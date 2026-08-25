"""
agent_harness/workflows/report_workflow.py

Runs the real hierarchical multi-agent PDF-generation workflow through the
harness box (agent_box.AgentHarness). The external signature this module
exposes is UNCHANGED from before this migration:

    run_report_workflow(execution_id, {"session_id": session_id}, generate_fn=...)

api_server.py's call site does not need to change at all.

Internally this now runs, instead of a single GenerateReport node:

    ReportSupervisorAgent
      -> AgricultureRAGAgent
           -> RetrievalAgent    (calls _fetch_session_data — unchanged)
           -> RerankingAgent    (dedupe/rank, same key scheme _build_html uses)
      -> ReportWriterAgent      (assembles report_content — no LLM call;
                                  see report_agents.py docstring for why)
      -> PDFAgent
           -> PDFStructureAgent (pre-flight structure check)
           -> PDFLayoutAgent    (records fixed layout profile)
           -> PDFRendererAgent  (calls mcp_generate_pdf() via generate_fn —
                                  UNCHANGED, same bytes as before)
      -> ReportQAAgent
           -> SourceValidationAgent
           -> ContentValidationAgent
           -> PDFValidationAgent

PDFRendererAgent is still the only place PDF bytes get produced. A missing
session still returns {"type": "error", "detail": ...} (-> HTTP 404), not
an exception (-> HTTP 500) — same behavior as before this migration.
"""
from typing import Any, Callable, Dict

import db_schema
from mcp_pdf_export import _fetch_session_data

from ..agent_box import AgentHarness, AgentError
from ..agent_state import ReportAgentState
from .report_agents import report_supervisor_agent


def _fetch_with_own_connection(session_id: str) -> dict:
    """Opens its own sqlite connection on whatever thread calls it — same
    cross-thread-safety pattern api_server.py's _generate_pdf_with_own_connection
    already uses for generate_fn (sqlite3 connections can't cross threads,
    and this runs inside asyncio.to_thread)."""
    conn = db_schema.get_connection()
    try:
        return _fetch_session_data(session_id, conn)
    finally:
        conn.close()


async def run_report_workflow(
    execution_id: str,
    payload: Dict[str, Any],
    generate_fn: Callable,
) -> Dict[str, Any]:
    """
    payload: {"session_id": str}
    generate_fn: UNCHANGED — the zero-extra-arg wrapper from api_server.py
        that opens its own db_schema connection, calls mcp_generate_pdf,
        and closes the connection. PDFRendererAgent runs it via
        asyncio.to_thread, same threading model as before.
    """
    session_id = payload["session_id"]
    harness = AgentHarness(execution_id, session_id=session_id)
    state = ReportAgentState(
        execution_id=execution_id,
        session_id=session_id,
        user_query="",  # PDF export has no live user_query — see report_agents.py
    )

    await harness.request_received(message="PDF report requested")

    try:
        result = await harness.run_agent(
            "ReportSupervisorAgent",
            report_supervisor_agent,
            state, _fetch_with_own_connection, generate_fn,
            tools=["sqlite", "mcp_pdf_export.mcp_generate_pdf"],
            input_summary={"session_id": session_id},
        )
    except AgentError as e:
        await harness.failed(f"{e.agent_name}: {e}")
        raise

    if result.get("type") == "error":
        state.status = "error"
    await harness.completed(result_summary={"type": result.get("type"), "status": state.status})
    return result
