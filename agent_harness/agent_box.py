"""
agent_harness/agent_box.py

THE BOX.

This module is the single encapsulated entry point that every agent in the
hierarchical PDF workflow (Supervisor, RAG, Writer, PDF, QA and their
children) dispatches through. No agent module should import events.py,
execution_logger.py, or state.py directly — they call AgentHarness.run_agent()
instead, and the box handles:

  - structured agent.start / agent.end / agent.error / agent.retry events
  - execution_id / parent_execution_id / agent_id threading
  - SSE publishing via the existing EventBus (events.py — reused, untouched)
  - SQLite persistence via the existing execution_logger (reused, untouched)
  - bounded retries with explicit retry events

This does not replace router.py, events.py, execution_logger.py, tracer.py,
or state.py. It sits on top of them.

ADDITIVE CHANGE (LangGraph autonomous agent support): run_agent() now takes
an optional `event_kind` (default "agent", unchanged). The new
langgraph_agent.py loop calls the `run_tool()` sugar method below instead,
which is the same run_agent() machinery (same retry loop, same
persistence, same SSE publish) but emits tool.start/tool.end/tool.retry/
tool.error instead of agent.*, per the event-adapter requirement so the
existing React execution panel can tell "an agent (sub-workflow) ran" apart
from "a leaf tool/capability ran" without the frontend needing to change.
Nothing about the existing agent.* contract used by chat_workflow.py /
report_agents.py changes — event_kind defaults to "agent" everywhere it
isn't passed explicitly.
"""
import time
import uuid
import inspect
import asyncio
from typing import Any, Awaitable, Callable, Dict, Optional

from .events import get_bus
from .execution_logger import create_table_if_missing, persist_event
from .state import create_state, set_status

create_table_if_missing()


class AgentError(Exception):
    """Raised when an agent exhausts its retries. Carries the agent name and
    underlying cause so the Supervisor can decide what to do next."""

    def __init__(self, agent_name: str, message: str, cause: Optional[Exception] = None):
        super().__init__(message)
        self.agent_name = agent_name
        self.cause = cause


def _accepts_kwarg(fn: Callable, kw: str) -> bool:
    try:
        return kw in inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return False


def _safe_summary(obj: Any, limit: int = 500) -> Optional[str]:
    if obj is None:
        return None
    try:
        s = str(obj)
    except Exception:
        s = "<unrepresentable>"
    return s[:limit]


class AgentHarness:
    """
    One instance per top-level workflow run (e.g. one PDF-generation request).

    Usage from an agent module:

        harness = AgentHarness(execution_id, session_id="abc")
        await harness.request_received()

        result = await harness.run_agent(
            "AgricultureRAGAgent",
            some_async_fn,
            arg1, arg2,
            parent_agent_id=supervisor_agent_id,
            tools=["chromadb", "bm25"],
            max_retries=0,
        )

        await harness.completed(result)
    """

    def __init__(self, execution_id: str, session_id: Optional[str] = None):
        self.execution_id = execution_id
        self.session_id = session_id
        self.bus = get_bus()
        self._t0 = time.time()
        create_state(execution_id, workflow="report_generation", meta={"session_id": session_id})

    async def _emit(self, event: Dict[str, Any]):
        event.setdefault("event_id", uuid.uuid4().hex)
        event.setdefault("execution_id", self.execution_id)
        event.setdefault("timestamp", time.time())
        self._print(event)
        await self.bus.publish(self.execution_id, event)
        await persist_event(event)

    @staticmethod
    def _print(event: Dict[str, Any]) -> None:
        """Console line matching the existing [HARNESS] convention from
        chat_workflow.py / the old report_workflow.py — without this,
        agent activity is invisible in the terminal even though it's
        persisting to SQLite and publishing to SSE correctly."""
        evt_type = event.get("type", "")
        name = event.get("agent_name") or event.get("node", "")
        bits = []
        if event.get("status") and event["status"] not in ("running",):
            bits.append(event["status"])
        if event.get("duration_ms") is not None:
            bits.append(f"{event['duration_ms']:.0f}ms")
        if evt_type == "agent.retry":
            bits.append(f"attempt={event.get('attempt')} reason={event.get('reason')}")
        if evt_type == "agent.error":
            bits.append(f"error={event.get('error')}")
        detail = "  -> " + " ".join(str(b) for b in bits) if bits else ""
        print(f"  [HARNESS] {evt_type}{(' ' + name) if name else ''}{detail}")

    async def request_received(self, message: str = "Request received", meta: Optional[dict] = None):
        await self._emit({"type": "request.received", "message": message, "meta": meta or {}})

    async def completed(self, result_summary: Any = None):
        set_status(self.execution_id, "completed")
        await self._emit({
            "type": "completed",
            "status": "completed",
            "duration_ms": (time.time() - self._t0) * 1000.0,
            "result": _safe_summary(result_summary),
        })

    async def failed(self, error: Any):
        set_status(self.execution_id, "error")
        await self._emit({
            "type": "execution.error",
            "status": "error",
            "meta": {"error": _safe_summary(error, 1000)},
        })

    async def run_agent(
        self,
        agent_name: str,
        fn: Callable[..., Awaitable[Any]],
        *args,
        parent_agent_id: Optional[str] = None,
        tools: Optional[list] = None,
        input_summary: Any = None,
        max_retries: int = 0,
        retry_reason_fn: Optional[Callable[[Exception], str]] = None,
        event_kind: str = "agent",
        **kwargs,
    ) -> Any:
        """
        Run one agent (or, with event_kind="tool", one leaf tool call) under
        the box.

        fn is an async callable implementing the actual work (LLM call,
        deterministic transform, or a call into an existing implementation
        like rag_pipeline.py or mcp_pdf_export.py's renderer). If fn
        declares an `agent_id` and/or `harness` kwarg, the box injects this
        call's agent_id and itself so it can spawn children
        (harness.run_agent(...) again, with parent_agent_id=agent_id) —
        this is how the hierarchy nests.

        event_kind controls only the emitted event `type` prefix
        ("agent" -> agent.start/agent.end/agent.error/agent.retry, "tool"
        -> tool.start/tool.end/tool.error/tool.retry). It does not change
        any control flow, retry behavior, or persistence — same code path
        either way. Defaults to "agent", which is byte-for-byte the same
        event shape this method emitted before event_kind existed, so
        every existing caller (chat_workflow.py, report_agents.py) is
        unaffected. Prefer the run_tool() sugar method below over passing
        event_kind directly.

        Returns fn's result, or raises AgentError after max_retries is
        exhausted.
        """
        agent_id = uuid.uuid4().hex
        start_ts = time.time()
        k = event_kind

        await self._emit({
            "type": f"{k}.start",
            "event": f"{k}.start",
            "agent_id": agent_id,
            "parent_execution_id": parent_agent_id,
            "agent_name": agent_name,
            "status": "running",
            "tools": tools or [],
            "input_summary": _safe_summary(input_summary),
        })

        wants_agent_id = _accepts_kwarg(fn, "agent_id")
        wants_harness = _accepts_kwarg(fn, "harness")
        extra = {}
        if wants_agent_id:
            extra["agent_id"] = agent_id
        if wants_harness:
            extra["harness"] = self

        attempt = 0
        last_error: Optional[Exception] = None

        while attempt <= max_retries:
            attempt += 1
            try:
                result = await fn(*args, **kwargs, **extra)
                dur = (time.time() - start_ts) * 1000.0
                await self._emit({
                    "type": f"{k}.end",
                    "event": f"{k}.end",
                    "agent_id": agent_id,
                    "parent_execution_id": parent_agent_id,
                    "agent_name": agent_name,
                    "status": "completed",
                    "duration_ms": dur,
                    "output_summary": _safe_summary(result),
                })
                return result
            except Exception as e:
                last_error = e
                reason = retry_reason_fn(e) if retry_reason_fn else _safe_summary(e, 300)
                will_retry = attempt <= max_retries

                await self._emit({
                    "type": f"{k}.error",
                    "event": f"{k}.error",
                    "agent_id": agent_id,
                    "parent_execution_id": parent_agent_id,
                    "agent_name": agent_name,
                    "error": reason,
                    "retry_count": attempt - 1,
                    "status": "retrying" if will_retry else "failed",
                })

                if will_retry:
                    await self._emit({
                        "type": f"{k}.retry",
                        "event": f"{k}.retry",
                        "agent_id": agent_id,
                        "agent_name": agent_name,
                        "attempt": attempt + 1,
                        "reason": reason,
                    })
                    continue

                dur = (time.time() - start_ts) * 1000.0
                await self._emit({
                    "type": f"{k}.end",
                    "event": f"{k}.end",
                    "agent_id": agent_id,
                    "parent_execution_id": parent_agent_id,
                    "agent_name": agent_name,
                    "status": "failed",
                    "duration_ms": dur,
                })
                raise AgentError(agent_name, reason, cause=e)

        # unreachable, but keeps type checkers happy
        raise AgentError(agent_name, _safe_summary(last_error), cause=last_error)

    def run_agent_blocking(
        self,
        agent_name: str,
        fn: Callable[..., Any],
        *args,
        loop: "asyncio.AbstractEventLoop",
        parent_agent_id: Optional[str] = None,
        tools: Optional[list] = None,
        input_summary: Any = None,
        max_retries: int = 0,
        event_kind: str = "agent",
        **kwargs,
    ) -> Any:
        """
        Synchronous entry point for calling run_agent() from code that is
        NOT running on the harness's event loop — specifically,
        rag_pipeline.py's _run_core(), which executes on a worker thread
        spawned by asyncio.to_thread() from chat_workflow.py, not on the
        main loop api_server.py's SSE subscribers run on.

        `fn` is a plain SYNCHRONOUS callable (e.g. pipeline._query_rewriter)
        — not a coroutine function. It is dispatched onto its own worker
        thread via asyncio.to_thread from inside a coroutine that runs ON
        `loop`, so the actual blocking work (an LLM call, a ChromaDB
        query) never runs on the event loop thread itself — only event
        publishing does. This mirrors api_server.py's own
        run_harness_workflow()/run_coroutine_threadsafe() bridge exactly,
        reusing the same pattern rather than inventing a second one.

        `loop` MUST be the same loop SSE subscribers are running on
        (api_server._HARNESS_LOOP) — the caller passes it in explicitly;
        agent_box.py deliberately never imports api_server.py (would be
        circular).
        """
        async def _to_async_and_run():
            async def _wrapped(*a, **kw):
                return await asyncio.to_thread(fn, *a, **kw)

            return await self.run_agent(
                agent_name, _wrapped, *args,
                parent_agent_id=parent_agent_id, tools=tools,
                input_summary=input_summary, max_retries=max_retries,
                event_kind=event_kind,
                **kwargs,
            )

        future = asyncio.run_coroutine_threadsafe(_to_async_and_run(), loop)
        return future.result()

    # ────────────────────────────────────────────────────────────────
    # NEW — sugar for the LangGraph autonomous agent loop
    # (langgraph_agent.py). Same run_agent() machinery under the hood;
    # these just fix event_kind and give the frontend/event-log a
    # semantic difference between "an agent/sub-workflow ran" and
    # "one leaf tool/capability ran" (Part 25 of the harness spec).
    # ────────────────────────────────────────────────────────────────

    async def run_tool(
        self,
        tool_name: str,
        fn: Callable[..., Awaitable[Any]],
        *args,
        parent_agent_id: Optional[str] = None,
        input_summary: Any = None,
        max_retries: int = 0,
        retry_reason_fn: Optional[Callable[[Exception], str]] = None,
        **kwargs,
    ) -> Any:
        """Run one tool call under the box, emitting tool.start / tool.end /
        tool.error / tool.retry instead of agent.*. fn should be an async
        callable that already does its own thread-offloading if it wraps
        blocking work (see tools.py — every tool function there is async
        and internally uses asyncio.to_thread around the sync pipeline/MCP
        call, the same pattern _call_step()/run_agent_blocking() already
        established elsewhere in this codebase)."""
        return await self.run_agent(
            tool_name, fn, *args,
            parent_agent_id=parent_agent_id,
            input_summary=input_summary,
            max_retries=max_retries,
            retry_reason_fn=retry_reason_fn,
            event_kind="tool",
            **kwargs,
        )

    async def validation_start(self, name: str, parent_agent_id: Optional[str] = None,
                                input_summary: Any = None) -> str:
        """Emits validation.start and returns a validation_id to pass to
        validation_end(). Kept as two explicit calls (rather than wrapping
        a function like run_agent/run_tool do) because validation checks
        in this codebase are plain sync/async functions with structured
        {"ok": bool, ...} return values, not agent-shaped work with
        retries — see report_agents.py's _source_validation_agent /
        _content_validation_agent / _pdf_validation_agent for the existing
        pattern this mirrors."""
        validation_id = uuid.uuid4().hex
        await self._emit({
            "type": "validation.start",
            "event": "validation.start",
            "agent_id": validation_id,
            "parent_execution_id": parent_agent_id,
            "agent_name": name,
            "status": "running",
            "input_summary": _safe_summary(input_summary),
        })
        return validation_id

    async def validation_end(self, validation_id: str, name: str, passed: bool,
                              detail: Any = None, parent_agent_id: Optional[str] = None) -> None:
        await self._emit({
            "type": "validation.end",
            "event": "validation.end",
            "agent_id": validation_id,
            "parent_execution_id": parent_agent_id,
            "agent_name": name,
            "status": "completed" if passed else "failed",
            "output_summary": _safe_summary(detail),
        })

    async def artifact_created(self, artifact_type: str, ref: Any,
                                parent_agent_id: Optional[str] = None) -> None:
        """Emits artifact.created for a produced artifact (a PDF, a saved
        file, etc.) — ref is whatever the frontend needs to fetch/display
        it (a filename, a download path); kept generic since PDF export
        already returns a filename (mcp_pdf_export.mcp_generate_pdf) while
        other future artifact types may return something else."""
        await self._emit({
            "type": "artifact.created",
            "event": "artifact.created",
            "parent_execution_id": parent_agent_id,
            "artifact_type": artifact_type,
            "ref": _safe_summary(ref),
        })