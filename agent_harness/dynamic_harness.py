"""
agent_harness/dynamic_harness.py

The controller (Section 4: "the harness controls execution, the agent
proposes"). Ties together task_analyzer.py, planner.py,
capability_registry.py, and failure_recovery.py, and drives everything
through the EXISTING agent_box.AgentHarness for every event
(agent.start/end/error/retry, validation.start/end, artifact.created) —
so the existing SQLite persistence, SSE stream, and React execution
panel all keep working unchanged (Section 2/22/29). This is plain
asyncio — no LangGraph (Section 28).

NOTE: this file lives directly in agent_harness/ (sibling to
agent_box.py, capability_registry.py, failure_recovery.py, planner.py,
task_analyzer.py, task_state.py) — every import below is a SINGLE dot.
Two dots ("..agent_box") tries to climb past agent_harness/ itself,
which is what "attempted relative import beyond top-level package" was
coming from.
"""
import asyncio
import time
from dataclasses import dataclass
from typing import Optional

from .agent_box import AgentHarness, AgentError
from .capability_registry import CapabilityRegistry
from .failure_recovery import classify_failure, decide_recovery
from .planner import Planner
from .task_analyzer import TaskAnalyzer
from .task_state import AgentResult, PlanStep, Task


@dataclass
class ExecutionBudgets:
    """Section 17 — enforced by the harness, not agent goodwill."""
    max_iterations: int = 20        # rounds of "dispatch whatever's ready" before giving up
    max_replans: int = 3            # Section 16, bounded
    max_tool_retries: int = 2       # per-step, same-args retry inside agent_box.run_agent
    timeout_s: float = 120.0        # wall-clock budget for the whole task


class DynamicAgentHarness:
    def __init__(self, harness: AgentHarness, registry: CapabilityRegistry, llm, tool_ctx,
                 budgets: ExecutionBudgets = ExecutionBudgets()):
        self.harness = harness
        self.registry = registry
        self.llm = llm
        self.tool_ctx = tool_ctx
        self.budgets = budgets
        self.analyzer = TaskAnalyzer(llm, registry.manifest_for_prompt())
        self.planner = Planner(registry)

    async def run(self, task: Task) -> Task:
        await self.harness.request_received(message="Dynamic harness request received")

        task = await self._call_analyzer(task)
        task = self.planner.plan(task)
        await self.harness._emit({
            "type": "plan.created", "event": "plan.created",
            "meta": {"steps": [{"id": s.id, "capability": s.capability, "depends_on": s.depends_on,
                                 "optional": s.optional} for s in task.plan]},
        })

        iterations = 0
        while iterations < self.budgets.max_iterations:
            if time.time() - task.started_at > self.budgets.timeout_s:
                task.errors.append({"stage": "dynamic_harness", "error": "execution timeout"})
                break

            if self._all_done(task):
                break

            dispatched = await self._dispatch_ready(task)
            if not dispatched:
                if task.is_stuck():
                    task.errors.append({"stage": "dynamic_harness", "error": "plan deadlocked — no ready steps remain"})
                break

            iterations += 1

        self._finalize(task)
        await self.harness.completed(result_summary={
            "status": task.status, "steps": len(task.plan), "replans": task.replans,
        })
        return task

    # ── analysis ─────────────────────────────────────────────────────

    async def _call_analyzer(self, task: Task) -> Task:
        async def _analyze(agent_id=None):
            return await self.analyzer.analyze(task)
        return await self.harness.run_agent("TaskAnalyzerAgent", _analyze,
                                            input_summary={"request": task.user_request[:200]})

    # ── dispatch ─────────────────────────────────────────────────────

    def _all_done(self, task: Task) -> bool:
        return all(s.status in ("success", "failed", "skipped") for s in task.plan)

    async def _dispatch_ready(self, task: Task) -> bool:
        ready = task.ready_steps()
        if not ready:
            return False

        # Section 10: parallel execution for independent steps, EXCEPT
        # capabilities marked parallel_safe=False (e.g. pdf_generate
        # writes one file — running two renders concurrently for the
        # same session is asking for a race, not a speedup).
        non_parallel = [s for s in ready
                        if not (self.registry.get(s.capability) or Capability_default()).parallel_safe]
        batch = [non_parallel[0]] if non_parallel else ready

        for s in batch:
            s.status = "running"
        await asyncio.gather(*[self._execute_step(task, s) for s in batch])
        return True

    # ── single step execution + observation + verification ────────────

    async def _execute_step(self, task: Task, step: PlanStep) -> None:
        cap = self.registry.get(step.capability)
        args = dict(step.args)
        args.update(self._resolve_dependency_args(task, step))

        async def _run(agent_id=None):
            return await cap.handler(self.tool_ctx, harness=self.harness,
                                     parent_agent_id=agent_id, **args)

        try:
            result: AgentResult = await self.harness.run_agent(
                cap.agent_name, _run,
                tools=cap.required_tools, input_summary=args,
                max_retries=self.budgets.max_tool_retries,
            )
        except AgentError as e:
            # agent_box's own bounded same-args retry is exhausted —
            # this is where cross-capability recovery decisions start.
            step.status = "failed"
            step.result = AgentResult(status="failure", issues=[str(e)])
            await self._observe_and_recover(task, step, exception=e)
            return

        step.result = result
        if result.status != "success":
            step.status = "failed"
            await self._observe_and_recover(task, step, exception=None)
            return

        # Section 34 — verify BEFORE trusting, not just "did it not raise"
        verification = await self._verify_step(task, step, cap)
        step.verification = verification
        if verification and not verification.get("ok", True):
            step.status = "failed"
            step.result.issues = step.result.issues + verification.get("issues", [])
            await self._observe_and_recover(task, step, exception=None)
            return

        step.status = "success"
        task.completed_step_ids.append(step.id)
        if result.evidence:
            task.sources.extend(result.evidence)
        if isinstance(result.output, dict) and result.output.get("filename"):
            await self.harness.artifact_created(
                result.output.get("type", "file"), result.output["filename"])

    async def _verify_step(self, task: Task, step: PlanStep, cap) -> Optional[dict]:
        if cap.verify is None:
            return None
        vid = await self.harness.validation_start(
            f"{cap.agent_name}Validation", input_summary={"step": step.id})
        try:
            verdict = cap.verify(step.result, task.constraints)
        except Exception as e:
            verdict = {"ok": False, "issues": [f"verify() itself raised: {e}"]}
        await self.harness.validation_end(vid, f"{cap.agent_name}Validation", verdict.get("ok", False),
                                          detail=verdict)
        return verdict

    def _resolve_dependency_args(self, task: Task, step: PlanStep) -> dict:
        """Wires a completed dependency's output into the next step's
        args — e.g. pdf_validate needs pdf_generate's actual output, not
        just "it ran". Only checks dep.status == "success" before using
        dep.result — a SKIPPED or FAILED optional dependency (e.g. no
        images found) satisfies the dependency for scheduling purposes
        (task_state.ready_steps) but contributes nothing here, which is
        exactly the "proceed without it" behavior Section 35 wants."""
        extra: dict = {}

        if step.capability == "pdf_validate":
            for dep_id in step.depends_on:
                dep = task.step(dep_id)
                if dep.capability == "pdf_generate" and dep.status == "success" and dep.result:
                    extra["pdf_result"] = dep.result.output

        elif step.capability == "chart_generate":
            for dep_id in step.depends_on:
                dep = task.step(dep_id)
                if dep.capability in ("topic_research", "agriculture_rag") and dep.status == "success" and dep.result:
                    extra["research_text"] = str(dep.result.output)

        elif step.capability == "document_compose":
            research_text_parts, sources, images, chart = [], [], [], None
            for dep_id in step.depends_on:
                dep = task.step(dep_id)
                if dep.status != "success" or not dep.result:
                    continue
                if dep.capability in ("topic_research", "agriculture_rag", "document_search"):
                    research_text_parts.append(str(dep.result.output))
                    sources.extend(dep.result.evidence or [])
                elif dep.capability == "image_search":
                    images = dep.result.output or []
                elif dep.capability == "chart_generate":
                    chart = dep.result.output
            extra.update({
                "research_text": "\n\n".join(research_text_parts),
                "sources": sources, "images": images, "chart": chart,
                "title": task.constraints.get("title") or task.goal or task.user_request[:80],
            })

        elif step.capability == "document_render":
            for dep_id in step.depends_on:
                dep = task.step(dep_id)
                if dep.capability == "document_compose" and dep.status == "success" and dep.result:
                    extra["html"] = dep.result.output
            extra["doc_format"] = task.constraints.get("doc_format", "pdf")
            extra["title"] = task.constraints.get("title") or task.goal or task.user_request[:80]

        elif step.capability == "document_validate":
            for dep_id in step.depends_on:
                dep = task.step(dep_id)
                if dep.capability == "document_render" and dep.status == "success" and dep.result:
                    extra["render_result"] = dep.result.output

        elif step.capability == "document_author":
            # Feeds the Document Coding Agent (document_author.py): the
            # factual research content + evidence it should write from,
            # plus the task-level requirements/original request that
            # only `task` (not a dependency step) actually carries.
            research_text_parts, sources = [], []
            for dep_id in step.depends_on:
                dep = task.step(dep_id)
                if dep.status == "success" and dep.result and \
                        dep.capability in ("topic_research", "agriculture_rag", "document_search"):
                    research_text_parts.append(str(dep.result.output))
                    sources.extend(dep.result.evidence or [])
            extra.update({
                "research_text": "\n\n".join(research_text_parts),
                "sources": sources,
                "title": task.constraints.get("title") or task.goal or task.user_request[:80],
                "requirements": task.required_content or [],
                "user_request": task.user_request,
            })

        return extra

    # ── failure classification + recovery + replanning ─────────────────

    async def _observe_and_recover(self, task: Task, step: PlanStep, exception) -> None:
        failure_class = classify_failure(step, exception)
        step.failure_class = failure_class
        task.failed_step_ids.append(step.id)
        task.errors.append({"stage": step.capability, "failure_class": failure_class,
                            "issues": step.result.issues if step.result else []})

        decision = decide_recovery(task.replans, self.budgets.max_replans, step, failure_class)
        await self.harness._emit({
            "type": "recovery.decision", "event": "recovery.decision",
            "meta": {"step": step.id, "capability": step.capability,
                     "failure_class": failure_class, "action": decision.action,
                     "reason": decision.reason},
        })

        if decision.action == "skip_optional":
            step.status = "skipped"
        elif decision.action == "give_up":
            pass  # stays "failed" — _finalize() decides task-level impact
        elif decision.action in ("retry_same", "try_capability"):
            new_cap = decision.capability or step.capability
            task = self.planner.replan(task, step, new_cap)

    # ── finalize ─────────────────────────────────────────────────────

    def _finalize(self, task: Task) -> None:
        """Section 35 — goal-based completion. A required (non-optional)
        step that never reached "success" fails the task; an optional
        one that got skipped does not."""
        required_unmet = [s for s in task.plan
                          if not s.optional and s.status not in ("success",)]
        task.status = "failed" if required_unmet else "completed"

        answer_parts = []
        for s in task.plan:
            if s.status == "success" and s.capability in ("agriculture_rag", "document_search", "web_search"):
                if s.result and s.result.output:
                    answer_parts.append(str(s.result.output))
            if s.status == "success" and s.capability == "pdf_generate" and s.result:
                out = s.result.output or {}
                if out.get("filename"):
                    task.artifacts.append({"type": "pdf", "ref": out["filename"]})
            if s.status == "success" and s.capability == "document_render" and s.result:
                out = s.result.output or {}
                if out.get("filename"):
                    # FIX: this used to only copy out.get("path") — if
                    # document_render's real handler returns the file as
                    # in-memory bytes (same "bytes" contract pdf_generate's
                    # own handler already uses — see
                    # default_capabilities._verify_pdf_generate checking
                    # out.get("bytes")) rather than a path already on
                    # disk, nothing here ever carried those bytes
                    # forward — dynamic_workflow.py's artifact
                    # registration had nothing to write to disk, so no
                    # download link was ever produced even though the
                    # document itself was generated successfully.
                    task.artifacts.append({"type": out.get("type", "pdf"), "ref": out["filename"],
                                           "path": out.get("path"), "bytes": out.get("bytes")})
                    answer_parts.append(
                        f"I've generated the document — **{out['filename']}** is ready to download.")
            # FIX: DocumentAuthorAgent (the CodingAgent/CodeExecutionAgent/
            # PDFInspectorAgent loop used for "generate a pdf of ..."
            # requests, per the terminal log) runs under the
            # "document_author" capability — a different capability name
            # from "pdf_generate"/"document_render" above. _finalize()
            # only checked those two names, so this path's result.output
            # (which DOES have a filename — see _execute_step's
            # harness.artifact_created() firing off the same output dict)
            # never got copied into task.artifacts. That's why the
            # terminal printed "artifacts=0" and /api/chat/dynamic
            # returned an empty artifacts list even though the PDF was
            # generated and saved to disk: dynamic_workflow.py's
            # register_artifact() loop (see artifact_store.py) had
            # nothing in task.artifacts to iterate over, so it never
            # wrote a row, never fired "artifact.preview", and
            # AgriBot.jsx — which already renders a DocumentCard + a
            # working /api/artifacts/{id}/download link the moment either
            # of those show up — had nothing to render. No frontend
            # change needed; this was the missing link.
            if s.status == "success" and s.capability == "document_author" and s.result:
                out = s.result.output or {}
                if out.get("filename"):
                    task.artifacts.append({"type": out.get("type", "pdf"), "ref": out["filename"],
                                           "path": out.get("path"), "bytes": out.get("bytes")})
                    answer_parts.append(
                        f"I've generated the document — **{out['filename']}** is ready to download.")

        task.final_output = "\n\n".join(answer_parts) if answer_parts else (
            None if task.status == "failed" else "Task completed with no text answer to display.")


def Capability_default():
    """Tiny fallback object so `.parallel_safe` access never explodes if
    a plan somehow references a capability name not in the registry
    (should be prevented by planner.py, but this keeps _dispatch_ready
    from crashing the whole task over a planning bug rather than failing
    that one step cleanly)."""
    class _D:
        parallel_safe = True
    return _D()