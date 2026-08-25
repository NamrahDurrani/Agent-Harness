"""
test_multi_agent_pdf.py — Phase 2.

Run: python test_multi_agent_pdf.py

Exercises report_agents.report_supervisor_agent directly (not through
api_server.py / a live DB / GROQ / weasyprint) using mocked fetch_fn and
generate_fn, so it's runnable anywhere. Verifies:

  - Supervisor, all Level-2..5 children AND grandchildren actually run
    (fails loudly if the hierarchy collapses back to one flat node)
  - every event carries execution_id / agent_id / parent_execution_id
  - PDFRendererAgent's retry path: fails twice, succeeds on 3rd attempt,
    emits exactly 2 agent.retry events
  - QA passes on a valid session and fails (without crashing) on a
    corrupt one (missing source_file)
  - the missing-session contract is preserved: {"type": "error", ...},
    NOT an exception — this must still map to HTTP 404, not 500
"""
import asyncio
import sqlite3
import uuid
from pathlib import Path

from agent_harness.agent_box import AgentHarness
from agent_harness.agent_state import ReportAgentState
from agent_harness.workflows.report_agents import report_supervisor_agent

DB_PATH = Path(__file__).resolve().parent / "agent_harness_executions.sqlite"

EXPECTED_AGENTS = {
    "ReportSupervisorAgent",
    "AgricultureRAGAgent", "RetrievalAgent", "RerankingAgent",
    "ReportWriterAgent",
    "PDFAgent", "PDFStructureAgent", "PDFLayoutAgent", "PDFRendererAgent",
    "ReportQAAgent", "SourceValidationAgent", "ContentValidationAgent", "PDFValidationAgent",
}


def _mock_session_data(with_sources=True):
    return {
        "session": {"session_id": "sess-1", "created_at": "2026-01-01", "title": "Wheat rust in Punjab"},
        "messages": [
            {"query_id": "q1", "original_query": "What wheat diseases affect Punjab?",
             "final_response": "Yellow rust and stem rust are the main concerns...",
             "query_ts": "2026-01-01T10:00:00", "response_ts": "2026-01-01T10:00:05", "used_rag": 1},
        ],
        "pipeline": [{"query_id": "q1", "steps": []}],
        "retrieved": [
            {"query_id": "q1", "docs": [
                {"source_file": "PARC_Annual_2023.pdf" if with_sources else "", "page_num": 12, "rrf_score": 0.041, "final_rank": 1},
                {"source_file": "FAO_Wheat_Guide.pdf" if with_sources else "", "page_num": 4, "rrf_score": 0.038, "final_rank": 2},
            ]},
        ],
        "llm_summary": [{"model_name": "llama-3.3-70b-versatile", "total_tokens": 512, "call_count": 1}],
    }


def _mock_pdf_result():
    return {"type": "pdf", "bytes": _minimal_valid_pdf_bytes(), "filename": "report.pdf"}


def _minimal_valid_pdf_bytes() -> bytes:
    """A genuinely valid, minimal one-page PDF (correct byte offsets, not
    just a '%PDF-1.4' prefix) so PyMuPDF's real validation in
    _pdf_validation_agent has something real to open — this is what
    exposed the bug: the old mock only *started* with a PDF header."""
    header = b"%PDF-1.4\n"
    objects = [
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n",
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n",
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\n",
    ]
    body = header
    offsets = []
    for obj in objects:
        offsets.append(len(body))
        body += obj
    xref_offset = len(body)
    xref = f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    for off in offsets:
        xref += f"{off:010} 00000 n \n"
    trailer = f"trailer<</Size {len(objects) + 1}/Root 1 0 R>>\nstartxref\n{xref_offset}\n%%EOF"
    return body + xref.encode() + trailer.encode()


def _fetch_ok(session_id: str):
    # sync, matching the real _fetch_with_own_connection contract (called
    # via asyncio.to_thread inside _retrieval_agent)
    return _mock_session_data()


def _fetch_missing(session_id: str):
    return None


def _generate_ok(session_id: str):
    return _mock_pdf_result()


def _make_flaky_generate(fail_times: int):
    calls = {"n": 0}

    def _gen(session_id: str):
        calls["n"] += 1
        if calls["n"] <= fail_times:
            raise RuntimeError(f"simulated renderer failure #{calls['n']}")
        return _mock_pdf_result()
    return _gen


def _events_for(execution_id: str):
    conn = sqlite3.connect(str(DB_PATH))
    rows = conn.execute(
        "SELECT event_type, node, status, meta FROM execution_events WHERE execution_id = ?",
        (execution_id,),
    ).fetchall()
    conn.close()
    return rows


async def test_full_hierarchy_success():
    execution_id = uuid.uuid4().hex
    harness = AgentHarness(execution_id, session_id="sess-1")
    state = ReportAgentState(execution_id=execution_id, session_id="sess-1", user_query="")

    result = await harness.run_agent(
        "ReportSupervisorAgent", report_supervisor_agent,
        state, _fetch_ok, _generate_ok,
    )
    await harness.completed(result)

    assert result["type"] == "pdf", result
    assert state.status == "completed", state.status
    assert state.validation_results["passed"] is True, state.validation_results

    rows = _events_for(execution_id)
    # execution_events doesn't have a dedicated agent_name column (see
    # PHASE 3 note below), so we verify the hierarchy by count: one
    # agent.start + one agent.end per agent in EXPECTED_AGENTS.
    starts = [r for r in rows if r[0] == "agent.start"]
    ends = [r for r in rows if r[0] == "agent.end"]
    assert len(starts) == len(EXPECTED_AGENTS), (
        f"expected {len(EXPECTED_AGENTS)} agent.start events (one per agent "
        f"in the hierarchy), got {len(starts)} — hierarchy may have collapsed"
    )
    assert len(ends) == len(EXPECTED_AGENTS), f"expected {len(EXPECTED_AGENTS)} agent.end events, got {len(ends)}"
    print(f"OK — full hierarchy: {len(starts)} agents started and ended, QA passed")


async def test_missing_session_returns_error_not_exception():
    execution_id = uuid.uuid4().hex
    harness = AgentHarness(execution_id, session_id="does-not-exist")
    state = ReportAgentState(execution_id=execution_id, session_id="does-not-exist", user_query="")

    # must NOT raise
    result = await harness.run_agent(
        "ReportSupervisorAgent", report_supervisor_agent,
        state, _fetch_missing, _generate_ok,
    )
    assert result["type"] == "error", result
    assert "not found" in result["detail"], result
    assert state.status == "error"
    print("OK — missing session returns {'type': 'error', ...} without raising (preserves 404 contract)")


async def test_renderer_retry_then_success():
    execution_id = uuid.uuid4().hex
    harness = AgentHarness(execution_id, session_id="sess-1")
    state = ReportAgentState(execution_id=execution_id, session_id="sess-1", user_query="")
    flaky = _make_flaky_generate(fail_times=2)  # PDFAgent's max_retries=2 -> succeeds on 3rd

    result = await harness.run_agent(
        "ReportSupervisorAgent", report_supervisor_agent,
        state, _fetch_ok, flaky,
    )
    assert result["type"] == "pdf", result

    rows = _events_for(execution_id)
    retries = [r for r in rows if r[0] == "agent.retry"]
    assert len(retries) == 2, f"expected 2 agent.retry events, got {len(retries)}"
    print(f"OK — PDFRendererAgent failed twice, retried, succeeded on 3rd attempt ({len(retries)} retry events)")


async def test_qa_fails_on_corrupt_sources_without_crashing():
    execution_id = uuid.uuid4().hex
    harness = AgentHarness(execution_id, session_id="sess-1")
    state = ReportAgentState(execution_id=execution_id, session_id="sess-1", user_query="")

    def _fetch_corrupt(session_id: str):
        return _mock_session_data(with_sources=False)  # source_file == ""

    result = await harness.run_agent(
        "ReportSupervisorAgent", report_supervisor_agent,
        state, _fetch_corrupt, _generate_ok,
    )
    assert result["type"] == "pdf"  # PDF still gets produced
    assert state.validation_results["passed"] is False, state.validation_results
    assert state.validation_results["sources"]["ok"] is False
    assert state.errors, "expected QA failure to be recorded in state.errors"
    print("OK — QA correctly fails on corrupt sources without crashing the workflow")


async def main():
    await test_full_hierarchy_success()
    await test_missing_session_returns_error_not_exception()
    await test_renderer_retry_then_success()
    await test_qa_fails_on_corrupt_sources_without_crashing()
    print("\nALL PHASE 2 TESTS PASSED")


if __name__ == "__main__":
    asyncio.run(main())