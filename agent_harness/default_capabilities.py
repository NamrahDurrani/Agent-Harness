"""
agent_harness/default_capabilities.py

Builds the concrete CapabilityRegistry (capability_registry.py) for this
project — one Capability per tools.py implementation, each with:
  - a handler that calls the real tools.run_* function and normalizes its
    result into task_state.AgentResult (Section 33)
  - a verify() function so the harness can check the result is actually
    good, not just that the call didn't raise (Section 34)
  - a failure_class for when the handler raises (Section 15)

This is the ONE place capability names are defined — planner.py only
ever sees names from registry.manifest_for_prompt(), and
dynamic_harness.py only ever calls registry.get(name).handler(...).
Neither hard-codes a capability list of its own.

ADDED: document_author — the write-code/execute/inspect/fix-loop
capability (document_author.py). This is the PREFERRED path for "write
me a document about X" requests now (see planner.py's safety net and
task_analyzer.py's updated prompt) — it doesn't use any fixed template,
the LLM writes fresh reportlab/matplotlib code per request. The older
topic_research/image_search/chart_generate/document_compose/
document_render/document_validate chain (document_capabilities.py) is
left registered and untouched for backward compatibility, but is no
longer the default route planner.py reaches for.
"""
from typing import Any, Dict

from . import tools, document_capabilities as doc_caps, document_author as doc_author
from .capability_registry import Capability, CapabilityRegistry
from .task_state import AgentResult


def _ok(output: Any, confidence: float = 1.0, evidence=None, metadata=None) -> AgentResult:
    return AgentResult(status="success", output=output, confidence=confidence,
                        evidence=evidence or [], metadata=metadata or {})


def _fail(issue: str, output: Any = None) -> AgentResult:
    return AgentResult(status="failure", output=output, confidence=0.0, issues=[issue])


# ═══════════════════════════════════════════════════════════════════════
# Handlers — adapt tools.run_*(...) into (ctx, harness, parent_agent_id, **args) -> AgentResult
# ═══════════════════════════════════════════════════════════════════════

async def _h_agriculture_rag(ctx, harness=None, parent_agent_id=None, **args) -> AgentResult:
    out = await tools.run_search_agriculture_knowledge(
        ctx, args["query"], harness=harness, parent_agent_id=parent_agent_id)
    if not out.get("answer"):
        return _fail("No answer produced", output=out)
    verification = out.get("verification")
    confidence = {"High": 1.0, "Medium": 0.6, "Low": 0.3}.get(
        getattr(verification, "confidence", None), 0.7)
    return _ok(out["answer"], confidence=confidence, evidence=out.get("sources", []),
               metadata={"source_type": out.get("source_type"), "used_rag": out.get("used_rag")})


def _verify_agriculture_rag(result: AgentResult, constraints: Dict[str, Any]) -> Dict[str, Any]:
    issues = []
    if not result.output or not str(result.output).strip():
        issues.append("empty answer")
    if constraints.get("require_sources") and not result.evidence:
        issues.append("no sources despite require_sources constraint")
    return {"ok": not issues, "issues": issues}


async def _h_document_search(ctx, **args) -> AgentResult:
    out = await tools.run_search_uploaded_documents(ctx, args["query"])
    if not out.get("ok"):
        return _fail(out.get("error", "document search failed"), output=out)
    return _ok(out.get("answer") or out.get("chunks"), evidence=out.get("sources", []))


async def _h_weather(ctx, **args) -> AgentResult:
    out = await tools.run_get_weather_forecast(args["location"])
    if not out:
        return _fail("no weather data returned")
    return _ok(out, confidence=0.9)


async def _h_sowing_advice(ctx, **args) -> AgentResult:
    out = await tools.run_get_sowing_advice(
        args["location"], args["crop"], args.get("target_day", "tomorrow"))
    if not out:
        return _fail("no sowing advice returned")
    return _ok(out, confidence=0.85)


async def _h_web_search(ctx, **args) -> AgentResult:
    out = await tools.run_mcp_tool("tavily_search", {"query": args["query"]})
    results = out.get("results") if isinstance(out, dict) else None
    if not results:
        return _fail("no web results", output=out)
    return _ok(out, confidence=0.5, evidence=results)   # web tier — lower confidence by default (Part 6, source authority)


async def _h_crop_calendar(ctx, **args) -> AgentResult:
    out = await tools.run_mcp_tool("crop_calendar", {"crop": args["crop"]})
    if not out:
        return _fail("no calendar data")
    return _ok(out, confidence=0.9)


async def _h_unit_converter(ctx, **args) -> AgentResult:
    out = await tools.run_mcp_tool("unit_converter", {
        "value": args["value"], "from_unit": args["from_unit"], "to_unit": args["to_unit"]})
    if out is None or (isinstance(out, dict) and out.get("error")):
        return _fail(str(out))
    return _ok(out, confidence=1.0)   # deterministic calculation — Section 33/34, this SHOULD be near-certain


async def _h_pdf_generate(ctx, **args) -> AgentResult:
    out = await tools.run_create_pdf_report(args.get("session_id") or ctx.session_id)
    if not out or out.get("type") not in ("pdf", "html"):
        return _fail("PDF generation returned an unexpected result", output=out)
    return _ok(out, confidence=1.0 if out.get("type") == "pdf" else 0.5)


def _verify_pdf_generate(result: AgentResult, constraints: Dict[str, Any]) -> Dict[str, Any]:
    if result.status != "success":
        return {"ok": False, "issues": ["generation failed"]}
    out = result.output or {}
    if out.get("type") == "html":
        return {"ok": True, "issues": ["fell back to HTML (weasyprint unavailable) — degraded but valid"]}
    return {"ok": bool(out.get("bytes")), "issues": [] if out.get("bytes") else ["no PDF bytes produced"]}


async def _h_pdf_validate(ctx, **args) -> AgentResult:
    out = await tools.run_validate_pdf(args["pdf_result"])
    if not out.get("ok"):
        return AgentResult(status="failure", output=out, confidence=0.0,
                            issues=[out.get("error", "PDF failed validation")])
    return _ok(out, confidence=1.0)


async def _h_save_memory(ctx, **args) -> AgentResult:
    out = await tools.run_save_memory(ctx, args["key"], args["value"])
    return _ok(out, confidence=1.0)


async def _h_retrieve_memory(ctx, **args) -> AgentResult:
    out = await tools.run_retrieve_memory(ctx, args.get("query", ""))
    return _ok(out.get("memories", []), confidence=1.0)


def build_default_registry() -> CapabilityRegistry:
    reg = CapabilityRegistry()

    reg.register(Capability(
        name="agriculture_rag", agent_name="AgricultureRAGAgent",
        purpose="Answer a factual agriculture question using the trusted knowledge base + web fallback + claim verification.",
        handler=_h_agriculture_rag, required_tools=["chromadb", "bm25", "groq"],
        verify=_verify_agriculture_rag, failure_class="RETRIEVAL",
        permissions=["read_knowledge_base", "read_web"],
    ))
    reg.register(Capability(
        name="document_search", agent_name="DocumentSearchAgent",
        purpose="Search the user's uploaded documents for this session.",
        handler=_h_document_search, required_tools=["upload_index"],
        depends_on_capabilities=[], optional_by_default=True, failure_class="RETRIEVAL",
        permissions=["read_uploads"],
    ))
    reg.register(Capability(
        name="weather", agent_name="WeatherAgent",
        purpose="Get the current weather forecast for a named location.",
        handler=_h_weather, required_tools=["open_meteo"], failure_class="TOOL",
        permissions=["read_external_api"],
    ))
    reg.register(Capability(
        name="sowing_advice", agent_name="SowingAdviceAgent",
        purpose="Get sowing/planting timing advice for a crop+location, combining weather with agronomic thresholds.",
        handler=_h_sowing_advice, required_tools=["open_meteo"],
        depends_on_capabilities=[], failure_class="TOOL",
        permissions=["read_external_api"],
    ))
    reg.register(Capability(
        name="web_search", agent_name="WebSearchAgent",
        purpose="Search the live web (Tavily) for information outside the indexed knowledge base — recent/time-sensitive topics.",
        handler=_h_web_search, required_tools=["tavily"], optional_by_default=True,
        failure_class="RETRIEVAL", permissions=["read_web"],
    ))
    reg.register(Capability(
        name="crop_calendar", agent_name="CropCalendarAgent",
        purpose="Look up the rule-based Pakistan sowing/harvest calendar for a named crop.",
        handler=_h_crop_calendar, required_tools=["mcp_tools"], failure_class="TOOL",
    ))
    reg.register(Capability(
        name="unit_converter", agent_name="CalculatorAgent",
        purpose="Deterministic unit conversion for agricultural units (acres/hectares, kg per acre/ha, etc).",
        handler=_h_unit_converter, required_tools=["mcp_tools"], failure_class="TOOL",
    ))
    reg.register(Capability(
        name="pdf_generate", agent_name="PDFRendererAgent",
        purpose="Export/summarize THIS CHAT SESSION as a PDF (conversation transcript, cited sources, retrieval trace). Use ONLY when the user wants a record of the conversation itself, e.g. 'export this chat', 'save this conversation as PDF'.",
        handler=_h_pdf_generate, required_tools=["mcp_pdf_export"],
        depends_on_capabilities=["agriculture_rag"], verify=_verify_pdf_generate,
        failure_class="PDF_RENDER", parallel_safe=False,
        permissions=["write_file"],
    ))
    reg.register(Capability(
        name="pdf_validate", agent_name="PDFValidationAgent",
        purpose="Validate a PDF produced by pdf_generate — checks it actually opens and has content.",
        handler=_h_pdf_validate, required_tools=["pymupdf"],
        depends_on_capabilities=["pdf_generate"], failure_class="PDF_RENDER",
    ))

    # ── Document generation — a FRESH document about a topic, not a chat
    # session export. document_author (below) is the preferred path —
    # see its own docstring. The older chain here is left registered,
    # untouched, for backward compatibility only. ─────────────────────

    reg.register(Capability(
        name="document_author", agent_name="DocumentAuthorAgent",
        purpose="Write, execute, and validate real Python code (reportlab + matplotlib) that builds a complete, professionally laid-out PDF for a NEW document about a topic — every section, table, and chart is generated fresh by the LLM for this specific request, never from a fixed template, with an automatic write/execute/inspect/fix loop. Use for 'generate/write/create a pdf/document/report about X' requests.",
        handler=doc_author.h_document_author, required_tools=["reportlab", "matplotlib", "pymupdf", "groq"],
        depends_on_capabilities=["topic_research"], failure_class="PDF_RENDER",
        parallel_safe=False, permissions=["write_file"],
    ))

    reg.register(Capability(
        name="topic_research", agent_name="ResearchAgent",
        purpose="Research a topic (web search + synthesis) and write organized content with headings, for building a NEW document. For agriculture-specific factual questions, prefer agriculture_rag instead (grounded + claim-verified).",
        handler=doc_caps.h_topic_research, required_tools=["tavily", "groq"],
        verify=doc_caps.verify_topic_research, failure_class="RETRIEVAL",
        permissions=["read_web"],
    ))
    reg.register(Capability(
        name="image_search", agent_name="ImageAgent",
        purpose="Find relevant images for a document topic. Optional — a document can be produced without images if none are found.",
        handler=doc_caps.h_image_search, required_tools=["tavily"],
        optional_by_default=True, failure_class="RETRIEVAL",
        permissions=["read_web"],
    ))
    reg.register(Capability(
        name="chart_generate", agent_name="ChartAgent",
        purpose="Generate ONE chart (bar/line/pie) from researched content, ONLY if the content actually contains comparable numeric data. Optional — skipped if nothing is genuinely chartable.",
        handler=doc_caps.h_chart_generate, required_tools=["matplotlib", "groq"],
        depends_on_capabilities=["topic_research"], optional_by_default=True,
        failure_class="TOOL",
    ))
    reg.register(Capability(
        name="document_compose", agent_name="DocumentComposeAgent",
        purpose="Assemble researched content, images, and a chart into one structured document (HTML). Runs after research/images/charts are gathered.",
        handler=doc_caps.h_document_compose,
        depends_on_capabilities=["topic_research"], verify=doc_caps.verify_document_compose,
        failure_class="MISSING_CONTENT",
    ))
    reg.register(Capability(
        name="document_render", agent_name="DocumentRenderAgent",
        purpose="Render a composed document into a real downloadable PDF or Word (.docx) file.",
        handler=doc_caps.h_document_render, required_tools=["weasyprint", "python-docx"],
        depends_on_capabilities=["document_compose"], verify=doc_caps.verify_document_render,
        failure_class="PDF_RENDER", parallel_safe=False,
        permissions=["write_file"],
    ))
    reg.register(Capability(
        name="document_validate", agent_name="DocumentValidationAgent",
        purpose="Validate the rendered document file — confirms it actually opens and has real content before calling the task done.",
        handler=doc_caps.h_document_validate, required_tools=["pymupdf"],
        depends_on_capabilities=["document_render"], failure_class="PDF_RENDER",
    ))
    reg.register(Capability(
        name="save_memory", agent_name="MemoryAgent",
        purpose="Save a durable fact about this session for future turns to retrieve.",
        handler=_h_save_memory, required_tools=["memory_store"], optional_by_default=True,
    ))
    reg.register(Capability(
        name="retrieve_memory", agent_name="MemoryAgent",
        purpose="Retrieve previously saved durable facts for this session.",
        handler=_h_retrieve_memory, required_tools=["memory_store"], optional_by_default=True,
    ))

    return reg