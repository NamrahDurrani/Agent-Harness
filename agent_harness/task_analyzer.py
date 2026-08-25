"""
agent_harness/task_analyzer.py

Section 7 — turns the user's natural-language request into structured
requirements on the Task object. One LLM call, strict JSON contract (same
pattern used elsewhere in this project — e.g. rag_pipeline.py's
_orchestrator/_evaluator — rather than a new dependency).

UPDATED distinction paragraph: document_author replaces the old
topic_research+document_compose+document_render chain as the preferred
capability for "write me a document" requests — it's a single capability
that writes, executes, and self-corrects real Python code per request
(see document_author.py), not a fixed template. The older chain is still
registered for backward compatibility but shouldn't normally be selected
by name anymore.
"""
import json
import re
from typing import Any, Dict, Optional

from .task_state import Task

_SYSTEM_PROMPT = """You are a task analyzer for an agriculture AI assistant's execution harness.

Given a user's request, extract structured requirements. Do NOT answer the question — only analyze what KIND of task this is and what it will require.

Respond with ONLY this JSON, nothing else:
{{
  "goal": "<one sentence — what must be true for this request to be satisfied>",
  "output_type": "chat_answer" | "pdf",
  "required_content": ["<short items the response must cover, e.g. 'sowing timing', 'sources', 'comparison table', 'chart'>"],
  "constraints": {{"require_sources": true|false, "language": "<detected or 'en'>", "location": "<if mentioned, else null>", "crop": "<if mentioned, else null>", "doc_format": "pdf"|"docx"|null, "title": "<a short title for a NEW document being generated, else null>"}},
  "validation_requirements": ["<e.g. 'factual_accuracy', 'pdf_integrity', 'citations_present'>"],
  "candidate_capabilities": ["<capability names from AVAILABLE CAPABILITIES that are plausibly needed>"]
}}

AVAILABLE CAPABILITIES:
{capability_manifest}

Only include a capability in candidate_capabilities if the request plausibly needs it — do not include capabilities "just in case". A simple factual question needs ONE capability, not five.

IMPORTANT distinction: "export/save THIS conversation as a PDF" needs pdf_generate (+ pdf_validate). "Create/write/generate a report or document ABOUT A TOPIC" — with an introduction, tables, charts, images, references, or any real authored structure — needs document_author (it writes, executes, and self-corrects the actual document-generation code for this specific request; also include agriculture_rag first if the topic is agriculture-specific, so document_author has real research content to write from). Do not confuse these two. Anything the user explicitly asks the document to contain (a comparison table, a chart, images, a references section) belongs in required_content, verbatim enough that the document-writing step knows exactly what was asked for.
"""

_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = _JSON_RE.search(text)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


class TaskAnalyzer:
    def __init__(self, llm, capability_manifest: str):
        self.llm = llm
        self.capability_manifest = capability_manifest

    async def analyze(self, task: Task) -> Task:
        import asyncio
        system = _SYSTEM_PROMPT.format(capability_manifest=self.capability_manifest)
        user = f"USER REQUEST: {task.user_request}\n\nJSON:"
        try:
            raw, _usage = await asyncio.to_thread(self.llm.call, system, user, 500, 0.0, None)
        except Exception as e:
            # Fail toward the safest generic plan, not toward crashing —
            # a chat_answer with agriculture_rag as the sole candidate is
            # a reasonable default for "the analyzer itself broke".
            task.goal = task.user_request
            task.output_type = "chat_answer"
            task.constraints = {}
            task.errors.append({"stage": "task_analyzer", "error": str(e)})
            return task

        parsed = _extract_json(raw)
        if parsed is None:
            task.goal = task.user_request
            task.output_type = "chat_answer"
            task.errors.append({"stage": "task_analyzer", "error": "unparseable analysis output", "raw": raw[:300]})
            return task

        task.goal = parsed.get("goal") or task.user_request
        task.output_type = parsed.get("output_type") or "chat_answer"
        task.required_content = parsed.get("required_content") or []
        task.constraints = parsed.get("constraints") or {}
        task.validation_requirements = parsed.get("validation_requirements") or []
        task.constraints["_candidate_capabilities"] = parsed.get("candidate_capabilities") or []
        return task