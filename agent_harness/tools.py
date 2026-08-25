"""
agent_harness/tools.py

The capability IMPLEMENTATIONS — plain async functions wrapping existing
project capabilities (rag_pipeline.py, mcp_weather_advisor.py,
mcp_pdf_export.py, mcp_tools.py, memory_store.py). Nothing here is
LangGraph-specific — no langchain import, no tool-call schema — this is
just the "how do I actually do X" layer. capability_registry.py wraps
each of these in a Capability, and dynamic_harness.py/planner.py decide
WHEN and WHETHER to call them. That split (implementation here, dynamic
routing decision elsewhere) is what changed from the earlier LangGraph
version of this file — TOOL_REGISTRY/ToolSpec/format_tool_manifest_for_prompt
were LangGraph-agent-facing and have been removed along with
langgraph_agent.py.

WIRING / WHAT THIS FILE DOES AND DOES NOT KNOW
------------------------------------------------
agent_harness must never import api_server.py (circular import — same
rule chat_workflow.py and report_workflow.py already document). Two
capabilities live behind that boundary and are NOT guessed at here:

  1. The already-constructed AgenticRAGPipeline instance (rag_pipeline.py)
     — needs API keys / Groq client / ChromaDB collection already wired
     up in api_server.py's startup.
  2. However uploaded-document chunks for a session actually get looked
     up today — the FUNCTION that turns a session_id into those chunks
     isn't in any file I've been given (known project bug: uploaded PDFs
     indexed into a collection never queried during chat).

Both are therefore injected via ToolContext at construction time — same
dependency-injection pattern chat_workflow.py already uses for execute_fn
and report_workflow.py already uses for generate_fn — rather than
fabricated.
"""
import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

# Existing, unchanged modules — same import style report_workflow.py /
# chat_workflow.py already use for their own dependencies.
import db_schema
from mcp_pdf_export import mcp_generate_pdf
import mcp_weather_advisor as weather_advisor
import mcp_tools  # existing unified MCP dispatcher (crop_calendar, unit_converter,
                   # tavily_search, docling_ingest) — folded in below, not reimplemented

from . import memory_store  # agent_harness-owned long-term memory (see memory_store.py)


@dataclass
class ToolContext:
    """Everything a capability handler needs that agent_harness can't
    reach on its own without importing api_server.py. Constructed once in
    workflows/dynamic_workflow.py from values api_server.py would pass in
    — mirrors execute_fn/generate_fn injection already used by
    chat_workflow.py / report_workflow.py.

    pipeline               — the already-constructed AgenticRAGPipeline
                              instance (same one api_server.py already
                              uses for normal chat).
    get_upload_chunks_fn    — callable(session_id) -> (upload_chunks,
                              upload_file_ids), or None if this project's
                              current upload lookup isn't available yet —
                              in that case search_uploaded_documents
                              reports a clear "not wired" error rather
                              than pretending to work.
    """
    pipeline: Any
    get_upload_chunks_fn: Optional[Callable[[str], Any]] = None
    session_id: str = ""
    llm: Any = None   # NEW — the project's LLMClient, needed by document-generation
                       # capabilities (topic_research/chart_generate) that don't go
                       # through the RAG pipeline at all.


# ═══════════════════════════════════════════════════════════════════════
# AGRICULTURE / RAG
# ═══════════════════════════════════════════════════════════════════════

async def run_search_agriculture_knowledge(ctx: ToolContext, query: str, harness=None,
                                            parent_agent_id: Optional[str] = None) -> Dict[str, Any]:
    """Calls the EXISTING AgenticRAGPipeline.run() end to end (query
    rewrite -> orchestrator -> MCP dispatch -> hybrid retrieval -> rerank
    -> evaluate -> retry-or-web-fallback -> grounded generation -> claim
    verification) — none of those internal steps are reimplemented or
    exposed to the caller. If a harness is provided, the call is threaded
    with harness=/agent_id=/loop= so the pipeline's OWN internal
    _call_step() wrapping still emits the existing per-step agent.*
    events as children of this capability call, exactly as it already
    does for normal chat via chat_workflow.py."""
    loop = asyncio.get_running_loop()
    result = await asyncio.to_thread(
        ctx.pipeline.run, ctx.session_id, query,
        harness=harness, agent_id=parent_agent_id, loop=loop,
    )
    return {
        "answer": result.answer,
        "sources": result.sources,
        "used_rag": result.used_rag,
        "source_type": result.source_type,
        "verification": getattr(result, "verification", None),
    }


# ═══════════════════════════════════════════════════════════════════════
# UPLOADED DOCUMENTS
# ═══════════════════════════════════════════════════════════════════════

async def run_search_uploaded_documents(ctx: ToolContext, query: str) -> Dict[str, Any]:
    if ctx.get_upload_chunks_fn is None:
        return {"ok": False, "error": "Uploaded-document lookup is not wired into ToolContext yet."}
    upload_chunks, upload_file_ids = await asyncio.to_thread(ctx.get_upload_chunks_fn, ctx.session_id)
    if not upload_chunks:
        return {"ok": True, "chunks": [], "note": "No uploaded documents for this session."}
    result = await asyncio.to_thread(
        ctx.pipeline.run, ctx.session_id, query,
        upload_chunks=upload_chunks, upload_file_ids=upload_file_ids,
        scope_to_upload=True,
    )
    return {"ok": True, "answer": result.answer, "sources": result.sources}


# ═══════════════════════════════════════════════════════════════════════
# WEATHER
# ═══════════════════════════════════════════════════════════════════════

async def run_get_weather_forecast(location: str) -> Dict[str, Any]:
    return await asyncio.to_thread(weather_advisor.get_weather_forecast, location)


async def run_get_sowing_advice(location: str, crop: str, target_day: str = "tomorrow") -> Dict[str, Any]:
    return await asyncio.to_thread(weather_advisor.get_sowing_advice, location, crop, target_day)


# ═══════════════════════════════════════════════════════════════════════
# PDF / REPORTS
# ═══════════════════════════════════════════════════════════════════════

def _generate_pdf_with_own_connection(session_id: str) -> dict:
    """Opens its own sqlite connection on whatever thread calls it — same
    cross-thread-safety pattern report_workflow.py's
    _fetch_with_own_connection / api_server.py's
    _generate_pdf_with_own_connection already use."""
    conn = db_schema.get_connection()
    try:
        return mcp_generate_pdf(session_id, conn)
    finally:
        conn.close()


async def run_create_pdf_report(session_id: str) -> Dict[str, Any]:
    return await asyncio.to_thread(_generate_pdf_with_own_connection, session_id)


async def run_validate_pdf(pdf_result: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic check — mirrors report_agents.py's
    _pdf_validation_agent exactly (same PyMuPDF-or-byte-length logic)."""
    if pdf_result.get("type") == "pdf":
        pdf_bytes = pdf_result.get("bytes", b"")
        ok = len(pdf_bytes) > 0
        page_count = None
        try:
            try:
                import pymupdf as fitz
            except ImportError:
                import fitz
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            page_count = doc.page_count
            ok = ok and page_count > 0
        except ImportError:
            pass
        return {"ok": ok, "type": "pdf", "size_bytes": len(pdf_bytes), "page_count": page_count}
    elif pdf_result.get("type") == "html":
        html = pdf_result.get("html", "")
        return {"ok": len(html) > 0, "type": "html_fallback", "size_bytes": len(html)}
    return {"ok": False, "type": pdf_result.get("type"), "error": "unexpected result type"}


# ═══════════════════════════════════════════════════════════════════════
# MCP TOOLS — folded in via the EXISTING mcp_tools.dispatch(tool_name,
# params) unified dispatcher. `weather`/`weather_sowing_advisor` are
# deliberately NOT re-added here — they'd duplicate
# get_weather_forecast/get_sowing_advice above.
# ═══════════════════════════════════════════════════════════════════════

async def run_mcp_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    return await asyncio.to_thread(mcp_tools.dispatch, tool_name, params)


# ═══════════════════════════════════════════════════════════════════════
# MEMORY — session-scoped long-term facts. See memory_store.py.
# ═══════════════════════════════════════════════════════════════════════

async def run_save_memory(ctx: ToolContext, key: str, value: str) -> Dict[str, Any]:
    await asyncio.to_thread(memory_store.save_memory, ctx.session_id, key, value)
    return {"ok": True, "saved": key}


async def run_retrieve_memory(ctx: ToolContext, query: str = "") -> Dict[str, Any]:
    rows = await asyncio.to_thread(memory_store.retrieve_memory, ctx.session_id, query or None)
    return {"ok": True, "memories": rows}