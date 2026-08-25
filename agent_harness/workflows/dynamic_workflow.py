"""
agent_harness/workflows/dynamic_workflow.py

Entry point for the dynamic, capability-driven harness (MASTER PROMPT
spec) — sits alongside chat_workflow.py and report_workflow.py, doesn't
replace either (Section 29/30: incremental, preserve existing behavior).
Like the LangGraph-based agentic_workflow.py it replaces, this is NOT
wired into api_server.py — that remains the one integration step left
for whenever it's wanted live.

CHANGE from the original: once dynamic.run(task) returns, every entry in
task.artifacts is registered in artifact_store.py (so a download/analysis
request can still find the file after this request/SSE stream ends) and
an "artifact.preview" event is emitted for each one — this is what
AgriBot.jsx's DocumentCard renders in the chat bubble. Everything else
in this file is unchanged.
"""
from typing import Any, Dict, Optional
import os

from ..agent_box import AgentHarness
from ..artifact_store import register_artifact
from ..default_capabilities import build_default_registry
from ..dynamic_harness import DynamicAgentHarness, ExecutionBudgets
from ..tools import ToolContext
from ..task_state import Task

# Fallback disk location for generated documents whose handler returned
# in-memory bytes instead of an already-saved path (see the loop below).
# Self-contained under agent_harness/ so this never collides with
# whatever directory your existing pdf export/report tooling already uses.
_GENERATED_DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "generated_documents")


async def run_dynamic_workflow(
    execution_id: str,
    payload: Dict[str, Any],
    pipeline: Any,
    llm: Any,
    get_upload_chunks_fn: Optional[Any] = None,
    budgets: ExecutionBudgets = ExecutionBudgets(),
) -> Dict[str, Any]:
    """
    payload: {"session_id": str, "query": str}
    pipeline / llm: the already-constructed AgenticRAGPipeline / LLMClient
        instances api_server.py already uses elsewhere — same injection
        pattern as chat_workflow.py's execute_fn / report_workflow.py's
        generate_fn.
    """
    session_id = payload["session_id"]
    query = payload["query"]

    harness = AgentHarness(execution_id, session_id=session_id)
    registry = build_default_registry()
    tool_ctx = ToolContext(pipeline=pipeline, get_upload_chunks_fn=get_upload_chunks_fn,
                           session_id=session_id, llm=llm)
    dynamic = DynamicAgentHarness(harness, registry, llm, tool_ctx, budgets)

    task = Task(execution_id=execution_id, session_id=session_id, user_request=query)
    task = await dynamic.run(task)

    # ── register + announce each generated file ────────────────────────
    # task.artifacts entries look like {"type": ..., "ref": filename,
    # "path": ..., "bytes": ...} (see dynamic_harness.py's _finalize()).
    #
    # FIX: this used to `continue` (silently drop the artifact) whenever
    # "path" was missing — which is exactly what happens if
    # document_render's real handler returns the file as in-memory bytes
    # rather than something already saved to disk. The document was
    # genuinely generated in that case, but nothing ever got registered
    # for /api/artifacts/.../download, so no card/link ever appeared —
    # even though the chat text correctly said the file was "ready to
    # download". Now: if bytes are available and no path was given, write
    # them out here as the fallback location, THEN register that.
    for art in task.artifacts:
        filename = art.get("ref")
        if not filename:
            continue
        file_type = art.get("type", "pdf")
        path = art.get("path")

        if not path:
            file_bytes = art.get("bytes")
            if not file_bytes:
                # Genuinely nothing to serve (handler didn't return a
                # path OR bytes) — skip this one artifact, don't crash
                # the whole response over it.
                continue
            os.makedirs(_GENERATED_DOCS_DIR, exist_ok=True)
            path = os.path.join(_GENERATED_DOCS_DIR, filename)
            mode = "wb" if isinstance(file_bytes, (bytes, bytearray)) else "w"
            with open(path, mode) as f:
                f.write(file_bytes)

        register_artifact(execution_id, session_id, filename, file_type, path)
        await harness._emit({
            "type": "artifact.preview", "event": "artifact.preview",
            "meta": {"execution_id": execution_id, "filename": filename, "file_type": file_type},
        })

    # FIX (UnicodeDecodeError): don't return task.artifacts as-is — some
    # entries can carry a raw "bytes" key (the actual PDF binary), which
    # is exactly what api_server.py was JSON-encoding, crashing with
    # "'utf-8' codec can't decode byte...". Bytes never need to leave the
    # server: the file is already written to disk by this point (either
    # because the handler saved it directly, or via the bytes-fallback
    # write above) — the frontend only ever needs filename/type to build
    # a download URL, matching the intended flow:
    #   PDF bytes -> saved to disk -> JSON response carries METADATA ONLY
    #   -> browser fetches the actual file from a separate file endpoint.
    sanitized_artifacts = [
        {"type": a.get("type"), "ref": a.get("ref")}
        for a in task.artifacts if a.get("ref")
    ]

    return {
        "response": task.final_output,
        "sources": task.sources,
        "artifacts": sanitized_artifacts,
        "plan": [{"capability": s.capability, "status": s.status} for s in task.plan],
        "status": task.status,
        "errors": task.errors,
        "execution_id": execution_id,
    }