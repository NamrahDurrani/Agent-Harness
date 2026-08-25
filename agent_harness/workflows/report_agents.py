"""
agent_harness/workflows/report_agents.py

The real hierarchical PDF-generation agent tree. Every function below is
a "worker" that gets dispatched through AgentHarness.run_agent() (the box
in agent_box.py) — none of them touch events.py / execution_logger.py
directly, and the box auto-injects `harness=` / `agent_id=` into any
function that declares those parameters, which is how a parent agent
spawns children tagged with the correct parent_agent_id.

WHAT IS AND ISN'T REWRITTEN
----------------------------
- _fetch_session_data() (mcp_pdf_export.py) — UNCHANGED, called as-is by
  RetrievalAgent. This is where the session's already-retrieved RAG data
  (messages, sources, pipeline steps) lives — a PDF export summarizes a
  finished chat session, it does not re-run retrieval live.
- mcp_generate_pdf() (mcp_pdf_export.py) — UNCHANGED, called as-is by
  PDFRendererAgent via the same `generate_fn` api_server.py already
  passes in. Output is byte-for-byte identical to before this migration.
- Nothing here reimplements ChromaDB/BM25/RRF/weasyprint/_build_html.
  RerankingAgent's dedupe logic mirrors the key/count scheme
  _build_html() already uses internally (source_file|page_num), so the
  RAG Agent's reported source list matches what the renderer actually
  puts in the PDF — but it operates on the SQL rows RetrievalAgent
  already fetched, it doesn't touch the renderer.

WHY ReportWriterAgent has no LLM call
--------------------------------------
mcp_generate_pdf()/_build_html() already produce the full report (cover,
summary stats, conversation, extracted recommendations, sources, pipeline
trace) directly from the session data. Having ReportWriterAgent use Groq
to rephrase/re-author content that PDFRendererAgent is about to
independently re-render from the SAME underlying data would create two
sources of truth for one report — the Writer's summary could drift from
what actually ends up in the PDF. So today ReportWriterAgent
deterministically assembles the structured report_content object (title +
section list + counts) straight from RAG data — it does not invent
anything. If a true "AI-authored narrative" report type is added later
(distinct from the session-transcript export), that's the place to add a
real Groq call against state.user_query + the RAG summary.
"""
import asyncio
from typing import Any, Dict, Optional

from ..agent_box import AgentHarness
from ..agent_state import ReportAgentState


# ═══════════════════════════════════════════════════════════════════════
# LEVEL 2 — AgricultureRAGAgent (+ RetrievalAgent, RerankingAgent)
# ═══════════════════════════════════════════════════════════════════════

async def _retrieval_agent(state: ReportAgentState, fetch_fn, agent_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Calls the existing _fetch_session_data() (via the thread-safe
    fetch_fn wrapper) — no new retrieval happens here. Returns None if the
    session doesn't exist; the Supervisor decides what to do with that,
    this agent just reports what it found."""
    data = await asyncio.to_thread(fetch_fn, state.session_id)
    if data is not None:
        state.retrieved_documents = data.get("retrieved", [])
    return data


async def _reranking_agent(state: ReportAgentState, data: Optional[Dict[str, Any]], agent_id: Optional[str] = None) -> list:
    """Deterministic. Dedupes/ranks sources using the same
    source_file|page_num key and count the renderer already uses
    internally, so what the RAG Agent reports matches what lands in the
    PDF's 'Knowledge Sources Referenced' table."""
    if not data:
        return []
    all_sources: Dict[str, Dict[str, Any]] = {}
    for r_data in data.get("retrieved", []):
        for doc in r_data.get("docs", []):
            key = f"{doc['source_file']}|{doc['page_num']}"
            if key not in all_sources:
                all_sources[key] = {
                    "source_file": doc["source_file"],
                    "page_num": doc["page_num"],
                    "count": 0,
                    "rrf_score": doc["rrf_score"],
                }
            all_sources[key]["count"] += 1
    ranked = sorted(all_sources.values(), key=lambda s: -s["count"])
    state.ranked_documents = ranked
    state.sources = ranked
    return ranked


async def agriculture_rag_agent(
    state: ReportAgentState, fetch_fn, harness: AgentHarness = None, agent_id: Optional[str] = None
) -> Dict[str, Any]:
    data = await harness.run_agent(
        "RetrievalAgent", _retrieval_agent, state, fetch_fn,
        parent_agent_id=agent_id, tools=["sqlite:_fetch_session_data"],
        input_summary={"session_id": state.session_id},
    )
    ranked = await harness.run_agent(
        "RerankingAgent", _reranking_agent, state, data,
        parent_agent_id=agent_id, tools=["dedupe_rank"],
        input_summary={"query_groups": len(data.get("retrieved", [])) if data else 0},
    )
    rag_summary = {
        "documents": data.get("retrieved", []) if data else [],
        "sources": ranked,
        "retrieval_count": len(data.get("retrieved", [])) if data else 0,
        "confidence": "high" if ranked else "low",
    }
    return {"data": data, "rag_summary": rag_summary}


# ═══════════════════════════════════════════════════════════════════════
# LEVEL 3 — ReportWriterAgent
# ═══════════════════════════════════════════════════════════════════════

async def report_writer_agent(state: ReportAgentState, data: Dict[str, Any], agent_id: Optional[str] = None) -> Dict[str, Any]:
    session = data.get("session", {})
    messages = data.get("messages", [])
    title = session.get("title") or "Chat"

    sections = [
        {"title": "Session Summary", "content": f"{len(messages)} exchanges"},
        {"title": "Conversation", "content": f"{len(messages)} messages"},
        {"title": "Sources / References", "content": f"{len(state.sources)} sources cited"},
    ]

    report_content = {"title": title, "sections": sections, "sources": state.sources}
    state.report_content = report_content
    return report_content


# ═══════════════════════════════════════════════════════════════════════
# LEVEL 4 — PDFAgent (+ Structure, Layout, Renderer)
# ═══════════════════════════════════════════════════════════════════════

async def _pdf_structure_agent(state: ReportAgentState, data: Dict[str, Any], agent_id: Optional[str] = None) -> Dict[str, Any]:
    """Deterministic pre-flight check — confirms the shape of what
    PDFRendererAgent is about to produce (title present, message count,
    source count) WITHOUT reimplementing _build_html(). Catches an empty
    session before spending time on rendering."""
    if not data.get("messages"):
        raise RuntimeError("Session has no messages — nothing to render")
    structure = {
        "title": state.report_content["title"],
        "section_count": len(state.report_content["sections"]),
        "source_count": len(state.sources),
        "message_count": len(data["messages"]),
    }
    state.pdf_structure = structure
    return structure


async def _pdf_layout_agent(state: ReportAgentState, agent_id: Optional[str] = None) -> Dict[str, Any]:
    """Deterministic. Page size/margins/header-footer/typography are
    already fixed in mcp_pdf_export.py's _CSS — per spec, no agent chooses
    fonts here. This just records the fixed layout profile and estimates
    page count for the execution-tree UI."""
    est_pages = max(1, 1 + state.pdf_structure["message_count"] // 4)
    layout = {"page_size": "A4", "layout_profile": "agribot_default", "estimated_pages": est_pages}
    state.pdf_layout = layout
    return layout


async def _pdf_renderer_agent(state: ReportAgentState, generate_fn, agent_id: Optional[str] = None) -> Dict[str, Any]:
    """The ONLY place that produces PDF bytes — calls the existing,
    unchanged mcp_generate_pdf() via generate_fn (which opens its own
    sqlite connection on this worker thread, same as before)."""
    result = await asyncio.to_thread(generate_fn, state.session_id)
    state.pdf_path = result.get("filename")
    return result


async def pdf_agent(
    state: ReportAgentState, data: Dict[str, Any], generate_fn,
    harness: AgentHarness = None, agent_id: Optional[str] = None,
) -> Dict[str, Any]:
    await harness.run_agent("PDFStructureAgent", _pdf_structure_agent, state, data, parent_agent_id=agent_id)
    await harness.run_agent("PDFLayoutAgent", _pdf_layout_agent, state, parent_agent_id=agent_id)
    result = await harness.run_agent(
        "PDFRendererAgent", _pdf_renderer_agent, state, generate_fn,
        parent_agent_id=agent_id, tools=["mcp_pdf_export.mcp_generate_pdf"],
        max_retries=2,  # spec section 5: max 2 retries, each emits agent.retry
    )
    return result


# ═══════════════════════════════════════════════════════════════════════
# LEVEL 5 — ReportQAAgent (+ Source/Content/PDF validators)
# ═══════════════════════════════════════════════════════════════════════

async def _source_validation_agent(state: ReportAgentState, agent_id: Optional[str] = None) -> Dict[str, Any]:
    missing = [s for s in state.sources if not s.get("source_file")]
    return {"ok": len(missing) == 0, "checked": len(state.sources), "missing_source_file": len(missing)}


async def _content_validation_agent(state: ReportAgentState, agent_id: Optional[str] = None) -> Dict[str, Any]:
    sections = state.report_content.get("sections", []) if state.report_content else []
    empty = [s["title"] for s in sections if not s.get("content")]
    ok = bool(state.report_content and state.report_content.get("title")) and len(empty) == 0
    return {"ok": ok, "section_count": len(sections), "empty_sections": empty}


async def _pdf_validation_agent(state: ReportAgentState, pdf_result: Dict[str, Any], agent_id: Optional[str] = None) -> Dict[str, Any]:
    """Deterministic file-level checks via PyMuPDF when the result is a
    real PDF. Falls back to a byte-length check for the HTML fallback path
    (weasyprint not installed) — that's a valid degraded result, not a QA
    failure."""
    if pdf_result.get("type") == "pdf":
        pdf_bytes = pdf_result.get("bytes", b"")
        ok = len(pdf_bytes) > 0
        page_count = None
        try:
            try:
                import pymupdf as fitz  # new import name; falls back below on older installs
            except ImportError:
                import fitz  # PyMuPDF, pre-1.24 import name
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            page_count = doc.page_count
            ok = ok and page_count > 0
        except ImportError:
            pass  # PyMuPDF not installed — byte-length check still applies
        return {"ok": ok, "type": "pdf", "size_bytes": len(pdf_bytes), "page_count": page_count}
    elif pdf_result.get("type") == "html":
        html = pdf_result.get("html", "")
        return {"ok": len(html) > 0, "type": "html_fallback", "size_bytes": len(html)}
    return {"ok": False, "type": pdf_result.get("type"), "error": "unexpected result type"}


async def report_qa_agent(
    state: ReportAgentState, pdf_result: Dict[str, Any],
    harness: AgentHarness = None, agent_id: Optional[str] = None,
) -> Dict[str, Any]:
    source_check = await harness.run_agent("SourceValidationAgent", _source_validation_agent, state, parent_agent_id=agent_id)
    content_check = await harness.run_agent("ContentValidationAgent", _content_validation_agent, state, parent_agent_id=agent_id)
    pdf_check = await harness.run_agent(
        "PDFValidationAgent", _pdf_validation_agent, state, pdf_result,
        parent_agent_id=agent_id, tools=["pymupdf"],
    )
    validation = {
        "sources": source_check,
        "content": content_check,
        "pdf": pdf_check,
        "passed": source_check["ok"] and content_check["ok"] and pdf_check["ok"],
    }
    state.validation_results = validation
    return validation


# ═══════════════════════════════════════════════════════════════════════
# LEVEL 1 — ReportSupervisorAgent
# ═══════════════════════════════════════════════════════════════════════

async def report_supervisor_agent(
    state: ReportAgentState, fetch_fn, generate_fn,
    harness: AgentHarness = None, agent_id: Optional[str] = None,
) -> Dict[str, Any]:
    state.plan = ["AgricultureRAGAgent", "ReportWriterAgent", "PDFAgent", "ReportQAAgent"]

    rag_out = await harness.run_agent(
        "AgricultureRAGAgent", agriculture_rag_agent, state, fetch_fn,
        parent_agent_id=agent_id, tools=["sqlite"], max_retries=1,
    )
    data = rag_out["data"]

    # Preserves the EXACT original contract: a missing session returns
    # {"type": "error", "detail": ...} (-> HTTP 404 in api_server.py),
    # not an exception (-> HTTP 500). No Writer/PDF/QA work makes sense
    # for a session that doesn't exist.
    if data is None:
        state.status = "error"
        state.record_error("AgricultureRAGAgent", f"session '{state.session_id}' not found")
        return {"type": "error", "detail": f"Session '{state.session_id}' not found in database."}

    await harness.run_agent("ReportWriterAgent", report_writer_agent, state, data, parent_agent_id=agent_id)

    pdf_result = await harness.run_agent(
        "PDFAgent", pdf_agent, state, data, generate_fn, parent_agent_id=agent_id,
    )

    validation = await harness.run_agent(
        "ReportQAAgent", report_qa_agent, state, pdf_result, parent_agent_id=agent_id,
    )

    if not validation["passed"]:
        state.record_error("ReportQAAgent", "one or more QA checks failed")

    state.status = "completed"
    return pdf_result