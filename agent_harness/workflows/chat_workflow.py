"""
chat_workflow.py
=================
Runs the real per-step RAG agent tree through the harness box
(agent_box.AgentHarness), instead of the single flat "RunRAGPipeline"
node this file used to emit.

WHAT CHANGED AND WHY: rag_pipeline.py's _run_core() already had each
pipeline stage as a separately-callable method (_query_rewriter,
_orchestrator, _mcp_dispatch, _retrieve, _rerank, _evaluator,
_generate_grounded, _generate_from_web) — _run_core() itself now takes
optional harness/agent_id/loop params and wraps each of those calls via
self._call_step(...), which is a no-op passthrough when harness=None
(every other caller, unchanged) and dispatches through
AgentHarness.run_agent_blocking() when provided. See
rag_pipeline.py's _call_step() docstring and agent_box.py's
run_agent_blocking() docstring for the full cross-thread bridging
mechanism (mirrors api_server.py's own run_harness_workflow() bridge).

WHAT THIS DOES NOT DO: it does not touch rag_pipeline.py's control flow
(the retry while-loop, force_web branch, upload_chunks branch all stay
exactly where they are). It does not duplicate _execute_query's upload
file lookup logic. execute_fn (api_server._execute_query) is still the
single source of truth for how a chat query actually runs — this file
only adds harness/agent_id/loop as pass-through arguments so the SAME
call now emits real per-step events instead of one opaque node.

`execute_fn` is passed in by the caller (api_server.py) rather than
imported here, to avoid a circular import: api_server.py imports
agent_harness at module load time, so agent_harness must never import
anything back from api_server.py.
"""
import asyncio
import time
import uuid
from typing import Any, Callable, Dict, Tuple

from ..agent_box import AgentHarness, AgentError

EXPECTED_RAG_AGENTS = {
    "RAGSupervisorAgent",
    "QueryRewriterAgent", "OrchestratorAgent", "MCPDispatcherAgent",
    "RetrievalAgent", "RerankingAgent", "RelevanceEvaluatorAgent",
    "GroundedLLMAgent", "WebFallbackAgent", "RetryController",
}


async def _rag_supervisor(
    session_id: str, query: str, force_web: bool, scope_to_upload: bool, execute_fn: Callable,
    loop: "asyncio.AbstractEventLoop",
    harness: AgentHarness = None, agent_id: str = None,
) -> Tuple:
    """
    The single top-level agent wrapping the whole chat turn. Its own
    agent_id becomes the parent_agent_id every real pipeline step
    (QueryRewriterAgent, RetrievalAgent, etc.) nests under — this is what
    makes rag_pipeline.py's internal _call_step() calls show up as
    children of RAGSupervisorAgent in the tree, not as siblings.

    execute_fn (api_server._execute_query) is still synchronous/blocking
    — dispatched via asyncio.to_thread exactly as before. The difference
    is execute_fn now receives harness/agent_id/loop and threads them all
    the way down into rag_pipeline.py's _run_core(), instead of running
    as one opaque blocking call.
    """
    return await asyncio.to_thread(
        execute_fn, session_id, query,
        force_web=force_web, scope_to_upload=scope_to_upload,
        harness=harness, agent_id=agent_id, loop=loop,
    )


async def run_chat_workflow(
    execution_id: str,
    payload: Dict[str, Any],
    execute_fn: Callable[..., Tuple],
) -> Dict[str, Any]:
    """
    payload: {"session_id": str, "query": str, "force_web": bool}

    Replaces the old single node.start/node.end "RunRAGPipeline" pair
    with a real RAGSupervisorAgent tree: QueryRewriterAgent ->
    OrchestratorAgent -> MCPDispatcherAgent -> RetrievalAgent ->
    RerankingAgent -> RelevanceEvaluatorAgent (looping via
    RetryController on a retry, same MAX_RETRIES cap rag_pipeline.py
    already enforced) -> GroundedLLMAgent or WebFallbackAgent.

    This coroutine itself runs on the harness/main event loop (it got
    here via api_server.run_harness_workflow()'s
    run_coroutine_threadsafe bridge from the sync /api/chat endpoint) —
    asyncio.get_running_loop() inside it IS the loop SSE subscribers are
    on, so it's passed straight through as `loop` for
    run_agent_blocking() to bridge back to from the worker thread
    _run_core() executes on.
    """
    harness = AgentHarness(execution_id, session_id=payload.get("session_id"))
    loop = asyncio.get_running_loop()

    await harness.request_received(message="Chat request received")

    try:
        result = await harness.run_agent(
            "RAGSupervisorAgent", _rag_supervisor,
            payload["session_id"], payload["query"],
            payload.get("force_web", False), payload.get("scope_to_upload", False),
            execute_fn, loop,
            tools=["rag_pipeline"],
            input_summary={"query": payload["query"][:200]},
        )
    except AgentError as e:
        await harness.failed(f"{e.agent_name}: {e}")
        raise

    response, trace, used_rag, source_type, mcp_tool, sources = result

    await harness.completed(result_summary={"source_type": source_type, "used_rag": used_rag})

    return {
        "response": response,
        "trace": trace,
        "used_rag": used_rag,
        "source_type": source_type,
        "mcp_tool": mcp_tool,
        "sources": sources,
        "execution_id": execution_id,
    }