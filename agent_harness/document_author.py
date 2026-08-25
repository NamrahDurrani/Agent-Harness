"""
agent_harness/document_author.py

The "Document Coding Agent -> Code Executor -> PDF Inspector -> fix loop"
architecture, as a single capability (document_author) registered in
default_capabilities.py. Nothing here is a fixed PDF template: the LLM
writes a fresh, self-contained Python script (reportlab + matplotlib)
for every single request, based on that request's own research content
and requirements. If the resulting PDF is missing something the request
asked for, the SAME loop hands the LLM its own script back along with
exactly what's wrong, and asks it to fix it — up to MAX_ATTEMPTS times.

This intentionally lives as ONE capability handler (not three separate
PlanSteps) so the write -> execute -> inspect -> fix -> re-execute cycle
can carry real context between attempts without fighting the harness's
step-level replan mechanism (which recreates a fresh step with the
SAME original args, not "here's what you did wrong last time"). Each
phase still gets its own node in the Agent Execution tree — see
_run_phase() below — via nested harness.run_agent() calls, matching how
your existing RAG sub-pipeline (QueryRewriterAgent, RetrievalAgent, etc.)
already nests under AgricultureRAGAgent.

ASSUMPTION FLAGGED: nested harness.run_agent() calls below pass
parent_agent_id explicitly (the id THIS capability itself was given).
If your actual AgentHarness.run_agent() signature doesn't accept a
parent_agent_id kwarg, this raises a clear TypeError immediately and
obviously — a one-line fix (drop the kwarg) if your harness instead
nests automatically via some internal "current agent" context.

SANDBOXING — WHAT THIS ACTUALLY DOES AND DOES NOT DO: generated code
runs as a separate OS subprocess (so a hang/infinite loop is killed by
a hard timeout instead of blocking your server), and is statically
scanned first for disallowed imports/attributes (os, sys, subprocess,
socket, shutil, eval/exec/__import__/open) before it's ever executed.
This is a meaningful safety NET against an LLM writing something
careless or broken, appropriate for "your own model generating code for
your own request on your own machine" — it is NOT a hardened, adversary-
proof sandbox (no container, no OS-level filesystem/network isolation).
If you need that bar, this is the one place to swap in a real sandbox
(e.g. run the subprocess inside a container or a restricted OS user).
"""
import ast
import asyncio
import io
import os
import re
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional

from .task_state import AgentResult

MAX_ATTEMPTS = 3
EXEC_TIMEOUT_S = 30

_GENERATED_DOCS_DIR = os.path.join(os.path.dirname(__file__), "generated_documents")

_ALLOWED_IMPORT_MODULES = {
    "reportlab", "reportlab.platypus", "reportlab.lib", "reportlab.lib.pagesizes",
    "reportlab.lib.styles", "reportlab.lib.units", "reportlab.lib.colors",
    "reportlab.lib.enums", "reportlab.pdfbase", "reportlab.pdfbase.ttfonts",
    "reportlab.pdfbase.pdfmetrics", "reportlab.graphics", "reportlab.graphics.shapes",
    "matplotlib", "matplotlib.pyplot", "matplotlib.figure", "matplotlib.ticker",
    "io", "os.path", "textwrap", "math", "datetime",
    # ADDED: the reusable visual-component helpers (report_components.py)
    # and the correct wrapped-table pattern (table_fix_example.py) live
    # in this SAME agent_harness/ directory. _execute_pdf_code below adds
    # that directory to the subprocess's PYTHONPATH so `import
    # report_components` / `from report_components import ...` resolves
    # exactly like any other top-level module — see the env= change.
    "report_components",
}
_FORBIDDEN_NAMES = {"eval", "exec", "__import__", "compile", "input", "open"}
_FORBIDDEN_ATTR_ROOTS = {"os", "sys", "subprocess", "socket", "shutil", "importlib", "ctypes"}


# ═══════════════════════════════════════════════════════════════════════
# Entry point — registered in default_capabilities.py as "document_author"
# ═══════════════════════════════════════════════════════════════════════

async def h_document_author(ctx, harness=None, parent_agent_id=None, **args) -> AgentResult:
    """
    args (wired by dynamic_harness._resolve_dependency_args's
    "document_author" branch):
      research_text: str  — factual content already gathered by
                             agriculture_rag/topic_research/document_search
      sources: list        — evidence entries, for a references section
      title: str
      requirements: list[str]  — task.required_content from task_analyzer.py
      user_request: str
    """
    llm = getattr(ctx, "llm", None)
    if llm is None:
        return AgentResult(status="failure", issues=["no LLM client available on ToolContext"])

    title = args.get("title") or "Document"
    research_text = args.get("research_text") or ""
    sources = args.get("sources") or []
    requirements = args.get("requirements") or []
    user_request = args.get("user_request") or title

    os.makedirs(_GENERATED_DOCS_DIR, exist_ok=True)
    filename = f"{_slugify(title)}_{os.urandom(4).hex()}.pdf"
    output_path = os.path.join(_GENERATED_DOCS_DIR, filename)

    missing = [m for m in ("reportlab", "matplotlib") if not _module_importable(m)]
    if missing:
        msg = (f"required package(s) not installed in this environment: "
               f"{', '.join(missing)} — run: pip install {' '.join(missing)}")
        print(f"[DOCUMENT_AUTHOR] {msg}")
        return AgentResult(status="failure", issues=[msg])

    previous_code: Optional[str] = None
    previous_issues: Optional[List[str]] = None
    last_inspection: Optional[Dict[str, Any]] = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        code = await _run_phase(
            harness, parent_agent_id, "CodingAgent",
            _write_pdf_code, llm, title, user_request, requirements,
            research_text, sources, previous_code, previous_issues, attempt,
            input_summary={"attempt": attempt, "title": title},
        )

        exec_result = await _run_phase(
            harness, parent_agent_id, "CodeExecutionAgent",
            _execute_pdf_code, code, output_path,
            input_summary={"attempt": attempt},
        )

        if not exec_result["ok"]:
            print(f"[DOCUMENT_AUTHOR] attempt {attempt} execution failed: {exec_result['error']}")
            previous_code = code
            previous_issues = [exec_result["error"]]
            continue

        inspection = await _run_phase(
            harness, parent_agent_id, "PDFInspectorAgent",
            _inspect_pdf, output_path, requirements,
            input_summary={"attempt": attempt},
        )
        last_inspection = inspection

        if inspection["ok"]:
            return AgentResult(
                status="success",
                output={"filename": filename, "path": output_path, "type": "pdf"},
                confidence=1.0,
                metadata={"attempts": attempt, "inspection": inspection},
            )

        print(f"[DOCUMENT_AUTHOR] attempt {attempt} inspection failed: {inspection['issues']}")
        previous_code = code
        previous_issues = inspection["issues"]

    # Exhausted attempts. If the last attempt at least produced a real
    # file, ship it (degraded, not perfect) rather than nothing — a
    # partially-complete document a user can look at beats a hard
    # failure when they explicitly asked for a document.
    if os.path.exists(output_path):
        return AgentResult(
            status="success",
            output={"filename": filename, "path": output_path, "type": "pdf"},
            confidence=0.4,
            issues=(last_inspection or {}).get("issues", []),
            metadata={"attempts": MAX_ATTEMPTS, "degraded": True},
        )
    return AgentResult(
        status="failure",
        issues=[f"could not produce a valid PDF after {MAX_ATTEMPTS} attempts"] +
               (previous_issues or []),
    )


async def _run_phase(harness, parent_agent_id, agent_name, fn, *fn_args, input_summary=None):
    """Runs one phase as its own nested Agent Execution tree node under
    this capability's own node, so the live panel shows
    DocumentAuthorAgent -> CodingAgent / CodeExecutionAgent /
    PDFInspectorAgent per attempt — matching the live-progress mockup."""
    if harness is None:
        # Defensive fallback if this ever runs without a harness (e.g. a
        # unit test) — just call the function directly, no tree node.
        result = fn(*fn_args)
        return await result if asyncio.iscoroutine(result) else result

    async def _call(agent_id=None):
        result = fn(*fn_args)
        return await result if asyncio.iscoroutine(result) else result

    return await harness.run_agent(agent_name, _call, parent_agent_id=parent_agent_id,
                                    input_summary=input_summary or {})


# ═══════════════════════════════════════════════════════════════════════
# Phase 1 — Document Coding Agent
# ═══════════════════════════════════════════════════════════════════════

_CODE_SYSTEM_PROMPT = """You are a Python engineer generating a COMPLETE, SELF-CONTAINED script that builds a professional PDF report using the reportlab library (reportlab.platypus) and, only if a chart is actually needed, matplotlib.

HARD RULES:
- Output ONLY raw Python code. No markdown fences, no explanation, no comments about what you're doing outside the code itself.
- A variable named OUTPUT_PATH (a string) is ALREADY DEFINED before your code runs. Build the document with:
    doc = SimpleDocTemplate(OUTPUT_PATH, pagesize=A4, ...)
  and end with doc.build(story).
- Do NOT read or write any other file. Do NOT call open() directly anywhere — only reportlab's own APIs, and for a chart,
  matplotlib saved to an in-memory io.BytesIO buffer (never to disk), then embedded via reportlab.platypus.Image(buffer, ...).
- Allowed imports ONLY: reportlab.* , matplotlib.* , io, math, textwrap, datetime, and report_components (see below).
  Nothing else — no os, sys, subprocess, socket, shutil, requests. Do not use eval, exec, __import__, compile, or input.
- The PDF must be genuinely well laid out: a clear title, section headings, real organized paragraphs of body text drawn
  from the RESEARCH CONTENT below (do not paste it verbatim — write clean, structured prose) — and ONLY the elements the
  REQUIREMENTS below actually ask for: a comparison table, a chart (matplotlib, embedded as an image), and/or a references
  section listing the SOURCES below. Don't invent extra sections the user didn't ask for, and don't skip ones they did.
- Use specific, real content grounded in the RESEARCH CONTENT — never placeholder text like "Lorem ipsum" or "[insert data
  here]". If the research content doesn't fully cover something requested, write the most accurate answer you can from
  general agricultural knowledge rather than leaving a section blank.

DESIGN SYSTEM — use these instead of freehanding your own styling (full guide: document_author_prompt.md):
- `from report_components import header_band, stat_cards, alert_box, badge, section_header` — these already exist in your
  environment. EXACT signatures — call them with EVERY argument shown, in this order, no keyword-skipping:
    header_band(title: str, subtitle: str, meta_line: str, width: float) -> Table
    stat_cards(items: list[tuple[str, str]], width: float) -> Table          # items = [("218 Bu/Ac", "Corn Target"), ...]
    section_header(number: int, title: str, width: float) -> Table
    alert_box(text: str, width: float) -> Table
    badge(text: str, kind: str) -> Paragraph   # kind is one of: deficit, balanced, warning, ok, high, medium, low
  Follow this EXACT pattern at the top of your script — copy it, then build your content into `story`:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from report_components import header_band, stat_cards, alert_box, badge, section_header
    PAGE_WIDTH, PAGE_HEIGHT = A4
    MARGIN = 40
    CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN
    styles = getSampleStyleSheet()
    story = []
    story.append(header_band("Report Title Here", "Report subtitle here", "Date: ... | Scope: ...", CONTENT_WIDTH))
    story.append(Spacer(1, 12))
    # only if the content has 3-5 genuine headline numbers:
    story.append(stat_cards([("218 Bu/Ac", "Corn Target"), ("64 Bu/Ac", "Soybean Target")], CONTENT_WIDTH))
    story.append(section_header(1, "Executive Summary", CONTENT_WIDTH))
    story.append(Paragraph("Body text here...", styles["BodyText"]))
    doc = SimpleDocTemplate(OUTPUT_PATH, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                             topMargin=MARGIN, bottomMargin=MARGIN)
    doc.build(story)
  ALWAYS pass CONTENT_WIDTH as the last argument to header_band/stat_cards/section_header/alert_box — never omit it, never
  guess a different variable name for it.
- EVERY table must build each cell as `Paragraph(str(cell), cell_style)` — NEVER a bare string — and must NOT set a fixed
  rowHeights list. A bare string doesn't wrap and silently overflows into the next row; a fixed rowHeight then draws the
  next row's content BEFORE the previous row's wrapped text finishes, so they visually overlap. Let reportlab compute row
  heights from the wrapped Paragraph content instead.
- Text content must be plain ASCII punctuation only: use a regular hyphen "-" (never en-dash "\u2013" or em-dash "\u2014"),
  spell out units instead of subscripts/superscripts (write "CO2" not "CO\u2082", "m2" not "m\u00b2"), and avoid symbols like
  "\u00b1", "\u00b0", "\u2122" (write "degrees", "plus/minus" instead). The base PDF font cannot render these and shows a
  black box in their place.
- CRITICAL: do NOT wrap doc.build(story) — or anything that leads up to it — in a try/except that swallows the exception.
  If something goes wrong, let it raise and crash loudly. A script that exits with status 0 but never actually wrote
  OUTPUT_PATH is the single hardest failure mode to diagnose or fix; a real traceback is far more useful than a silent
  no-op.

TITLE: {title}

USER'S ORIGINAL REQUEST: {user_request}

REQUIREMENTS TO INCLUDE (only what's listed here): {requirements}

RESEARCH CONTENT (factual basis for the document):
{research_text}

SOURCES (for a references section, only if requested):
{sources}
"""

_FIX_SUFFIX = """

YOUR PREVIOUS SCRIPT FAILED WITH THESE SPECIFIC PROBLEMS:
{issues}

YOUR PREVIOUS SCRIPT:
{previous_code}

Fix these exact problems and output the COMPLETE corrected script (the whole file, not a diff or a patch)."""

_FENCE_RE = re.compile(r"^```(?:python)?\s*|\s*```$", re.MULTILINE)


def _strip_code_fences(text: str) -> str:
    return _FENCE_RE.sub("", text.strip())


# FIX (the "■" tofu-box characters in your PDF): the prompt now asks the
# LLM to stick to ASCII punctuation, but an instruction is a request, not
# a guarantee — models still slip in an en-dash or a unicode subscript
# now and then. This is the deterministic backstop: a straight character
# substitution over the ENTIRE generated script text before it's ever
# executed, so the fix doesn't depend on the model remembering the rule
# every single time. Safe to apply to Python source too — none of these
# characters are meaningful in Python syntax, only inside the string
# literals that become PDF text.
_UNICODE_ASCII_MAP = {
    "\u2013": "-", "\u2014": "-", "\u2212": "-",       # en/em dash, minus sign
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',  # smart quotes
    "\u2026": "...",                                    # ellipsis
    "\u00b0": " degrees", "\u00b1": " +/-", "\u2122": "(TM)",
    "\u00b2": "2", "\u00b3": "3",                        # superscript 2/3 (m2, m3)
    "\u2080": "0", "\u2081": "1", "\u2082": "2", "\u2083": "3", "\u2084": "4",
    "\u2085": "5", "\u2086": "6", "\u2087": "7", "\u2088": "8", "\u2089": "9",  # subscripts (CO2)
}


def _sanitize_unicode(code: str) -> str:
    for uni, ascii_eq in _UNICODE_ASCII_MAP.items():
        code = code.replace(uni, ascii_eq)
    return code


async def _write_pdf_code(llm, title: str, user_request: str, requirements: List[str],
                           research_text: str, sources: List[Any],
                           previous_code: Optional[str], previous_issues: Optional[List[str]],
                           attempt: int) -> str:
    source_lines = "\n".join(
        f"- {s.get('label', s.get('source_file', str(s)))}" if isinstance(s, dict) else f"- {s}"
        for s in sources[:15]
    ) or "(none)"

    prompt = _CODE_SYSTEM_PROMPT.format(
        title=title, user_request=user_request,
        requirements=", ".join(requirements) or "(none explicitly stated — use good judgment)",
        research_text=(research_text or "(no research content available — use general agricultural knowledge)")[:6000],
        sources=source_lines,
    )
    if attempt > 1 and previous_code and previous_issues:
        prompt += _FIX_SUFFIX.format(
            issues="\n".join(f"- {i}" for i in previous_issues),
            previous_code=previous_code,
        )

    raw, _usage = await asyncio.to_thread(
        llm.call, prompt, "Write the script now.", 3500, 0.2)
    return _sanitize_unicode(_strip_code_fences(raw))


# ═══════════════════════════════════════════════════════════════════════
# Phase 2 — Code Execution Agent (static safety check + sandboxed subprocess)
# ═══════════════════════════════════════════════════════════════════════

def _module_allowed(name: str) -> bool:
    return any(name == m or name.startswith(m + ".") for m in _ALLOWED_IMPORT_MODULES)


def _attribute_root_name(node: ast.Attribute) -> Optional[str]:
    n = node
    while isinstance(n, ast.Attribute):
        n = n.value
    return n.id if isinstance(n, ast.Name) else None


def _static_safety_check(code: str) -> List[str]:
    issues = []
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [f"syntax error: {e}"]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if not _module_allowed(alias.name):
                    issues.append(f"disallowed import: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module and not _module_allowed(node.module):
                issues.append(f"disallowed import: {node.module}")
        elif isinstance(node, ast.Name) and node.id in _FORBIDDEN_NAMES:
            issues.append(f"disallowed name used: {node.id}")
        elif isinstance(node, ast.Attribute):
            root = _attribute_root_name(node)
            if root in _FORBIDDEN_ATTR_ROOTS:
                issues.append(f"disallowed attribute access: {root}.*")

    return issues


def _execute_pdf_code(code: str, output_path: str) -> Dict[str, Any]:
    safety_issues = _static_safety_check(code)
    if safety_issues:
        return {"ok": False, "error": "blocked by safety check: " + "; ".join(safety_issues)}

    full_script = f"OUTPUT_PATH = {output_path!r}\n" + code

    script_path = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(full_script)
            script_path = f.name

        # FIX: the temp script lives in the OS temp directory, not next
        # to report_components.py — a bare `import report_components` in
        # the generated code would fail with ModuleNotFoundError without
        # this. Prepending agent_harness/ (this file's own directory) to
        # PYTHONPATH makes it resolve exactly like importing any other
        # top-level module, without needing to relocate the temp file.
        env = os.environ.copy()
        agent_harness_dir = os.path.dirname(os.path.abspath(__file__))
        env["PYTHONPATH"] = agent_harness_dir + os.pathsep + env.get("PYTHONPATH", "")

        proc = subprocess.run(
            [sys.executable, script_path],
            capture_output=True, text=True, timeout=EXEC_TIMEOUT_S, env=env,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"execution timed out after {EXEC_TIMEOUT_S}s"}
    finally:
        if script_path:
            try:
                os.remove(script_path)
            except OSError:
                pass

    if proc.returncode != 0:
        return {"ok": False, "error": f"script exited {proc.returncode}: {proc.stderr[-1500:]}"}
    if not os.path.exists(output_path):
        return {"ok": False, "error": "script exited cleanly but did not create OUTPUT_PATH"}

    return {"ok": True}


# ═══════════════════════════════════════════════════════════════════════
# Phase 3 — PDF Inspector
# ═══════════════════════════════════════════════════════════════════════

def _inspect_pdf(path: str, requirements: List[str]) -> Dict[str, Any]:
    try:
        import fitz  # PyMuPDF — already a project dependency (pdf_validate/document_validate)
    except ImportError:
        return {"ok": True, "issues": ["PyMuPDF not available — skipped inspection"], "skipped": True}

    issues: List[str] = []
    try:
        doc = fitz.open(path)
    except Exception as e:
        return {"ok": False, "issues": [f"could not open generated PDF: {e}"]}

    page_count = doc.page_count
    if page_count < 1:
        issues.append("PDF has zero pages")

    full_text = ""
    image_count = 0
    for page in doc:
        full_text += page.get_text()
        image_count += len(page.get_images())
    doc.close()

    if len(full_text.strip()) < 200:
        issues.append("PDF has almost no extractable text — likely a near-empty document")

    req_lower = " ".join(requirements).lower()
    # Chart/image presence is reliably checkable — a chart embeds as a
    # raster image regardless of library, same for photos.
    if ("chart" in req_lower or "graph" in req_lower) and image_count == 0:
        issues.append("a chart/graph was requested but no embedded image was found in the PDF")
    if ("image" in req_lower or "picture" in req_lower or "photo" in req_lower) and image_count == 0:
        issues.append("images were requested but none were found embedded in the PDF")
    # NOTE: table presence is deliberately NOT hard-checked here — reportlab
    # Table cell text doesn't extract with reliable delimiters, so a
    # structural check would be guesswork. This inspector focuses on what
    # PyMuPDF can verify with confidence: real page/text/image content.

    return {"ok": len(issues) == 0, "issues": issues, "page_count": page_count, "image_count": image_count}


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")
    return (slug or "document")[:60]


def _module_importable(name: str) -> bool:
    import importlib.util
    return importlib.util.find_spec(name) is not None