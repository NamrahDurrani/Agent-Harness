"""
agent_harness/planner.py

Section 7's Planner — turns TaskAnalyzer's candidate_capabilities
(stored on task.constraints["_candidate_capabilities"] — see your real
task_analyzer.py's `task.constraints["_candidate_capabilities"] =
parsed.get("candidate_capabilities") or []`) into a concrete,
dependency-wired List[PlanStep] on task.plan, plus best-effort per-step
args pulled from task.constraints / task.user_request.

WHAT THIS DOES NOT DO: it doesn't re-decide WHICH capabilities are
needed via any hardcoded document template — content, tables, charts,
and layout are still 100% produced live by each capability's own
handler in document_capabilities.py, every single run. This file only
decides WHICH agents get invoked and in what order — routing, not
authorship.

TWO SAFETY NETS beyond straightforward wiring, both added after finding
real gaps in practice, not speculatively:

1. DOCUMENT-INTENT FALLBACK (_wants_document / the block in plan()):
   task_analyzer.py's one LLM call sometimes decides a clearly
   document-shaped request ("generate a pdf about X...") only needs a
   factual answer, and never selects the document-authoring capability
   at all — nothing downstream can build a document if it's never asked
   to. If the request text obviously asks for a pdf/docx/document/report
   and the analyzer's candidate list omitted document_author, this adds
   it (plus a content-source capability to feed it, if none was already
   selected). document_author's own internal write/execute/inspect loop
   (document_author.py) decides on its own whether a chart/table/images
   belong in the result — no separate chart_generate/image_search
   injection is needed here anymore.

2. DEPENDENCY ALIASES (_DEPENDENCY_ALIASES): capability_registry.py
   declares document_compose's only "typical" prerequisite as
   topic_research, but dynamic_harness.py's OWN
   _resolve_dependency_args also accepts agriculture_rag (and
   document_search, for document_compose) as a valid content source —
   which is exactly what an agriculture-specific request like this one
   actually selects. Wiring depends_on off the registry's single
   declared hint alone would leave document_compose with NO dependency
   at all when only agriculture_rag was chosen, so it would run with no
   data. This maps each capability to every content-source capability
   dynamic_harness.py's resolver actually recognizes for it, and wires
   to whichever one is really in the plan.

AUTO-ADDED VALIDATION STEPS (_AUTO_VALIDATE): document_validate/
pdf_validate are appended automatically even if the analyzer's JSON
omitted them, per task_analyzer.py's own system prompt promise
("document_validate is added automatically").
"""
import re
from typing import Any, Dict, List

from .capability_registry import CapabilityRegistry
from .task_state import PlanStep, Task

_AUTO_VALIDATE = {
    "document_render": "document_validate",
    "pdf_generate": "pdf_validate",
}

# dynamic_harness._resolve_dependency_args accepts any of these as a
# valid content-source dependency for the given capability — wider than
# capability_registry.py's single declared depends_on_capabilities hint.
_DEPENDENCY_ALIASES = {
    "chart_generate": ["topic_research", "agriculture_rag"],
    "document_compose": ["topic_research", "agriculture_rag", "document_search"],
    "document_author": ["topic_research", "agriculture_rag", "document_search"],
}

_DOC_INTENT_RE = re.compile(r"\b(pdf|docx|document|report|word doc|generate a file)\b", re.IGNORECASE)
_CHART_INTENT_RE = re.compile(r"\b(chart|graph|plot)\b", re.IGNORECASE)
_IMAGE_INTENT_RE = re.compile(r"\b(image|picture|photo|illustration)\b", re.IGNORECASE)


# ═══════════════════════════════════════════════════════════════════════
# Per-capability arg builders — small pure functions so adding a new
# capability's arg contract later is a one-line addition to _ARG_BUILDERS,
# not a growing if/elif chain.
# ═══════════════════════════════════════════════════════════════════════

def _args_query(task: Task) -> Dict[str, Any]:
    return {"query": task.goal or task.user_request}


def _args_weather(task: Task) -> Dict[str, Any]:
    # ASSUMPTION: constraints.location is the only signal task_analyzer.py
    # gives us. If the LLM picked "weather" but didn't extract a
    # location, fall back to the raw request text so the tool call
    # attempts something instead of KeyError-ing on args["location"].
    return {"location": task.constraints.get("location") or task.user_request}


def _args_sowing_advice(task: Task) -> Dict[str, Any]:
    return {
        "location": task.constraints.get("location") or task.user_request,
        "crop": task.constraints.get("crop") or "",
        "target_day": task.constraints.get("target_day") or "tomorrow",
    }


def _args_crop_calendar(task: Task) -> Dict[str, Any]:
    return {"crop": task.constraints.get("crop") or task.user_request}


_UNIT_CONVERT_RE = re.compile(
    r"([\d.]+)\s*([a-zA-Z/]+)\s*(?:to|into|in)\s*([a-zA-Z/]+)", re.IGNORECASE)


def _args_unit_converter(task: Task) -> Dict[str, Any]:
    # ASSUMPTION: task_analyzer.py's JSON contract doesn't extract
    # numeric conversion details, so this is a best-effort regex over
    # the raw request. If it doesn't match, this returns {} and the
    # handler fails cleanly (AgentResult failure) rather than silently
    # guessing a value.
    m = _UNIT_CONVERT_RE.search(task.user_request)
    if not m:
        return {}
    return {"value": float(m.group(1)), "from_unit": m.group(2), "to_unit": m.group(3)}


def _args_pdf_generate(task: Task) -> Dict[str, Any]:
    return {"session_id": task.session_id}


def _args_empty(task: Task) -> Dict[str, Any]:
    # document_compose / document_render / document_validate /
    # chart_generate / pdf_validate get their REAL inputs wired by
    # dynamic_harness._resolve_dependency_args from completed dependency
    # steps at execution time — this deliberately seeds nothing, since
    # anything seeded here would just be overwritten there anyway.
    return {}


_ARG_BUILDERS = {
    "agriculture_rag": _args_query,
    "document_search": _args_query,
    "web_search": _args_query,
    "topic_research": _args_query,
    "image_search": _args_query,
    "retrieve_memory": _args_query,
    "weather": _args_weather,
    "sowing_advice": _args_sowing_advice,
    "crop_calendar": _args_crop_calendar,
    "unit_converter": _args_unit_converter,
    "pdf_generate": _args_pdf_generate,
    "pdf_validate": _args_empty,
    "chart_generate": _args_empty,
    "document_compose": _args_empty,
    "document_render": _args_empty,
    "document_validate": _args_empty,
    "save_memory": _args_empty,
}


def _wants_document(task: Task) -> bool:
    if (task.output_type or "").lower() == "pdf":
        return True
    return bool(_DOC_INTENT_RE.search(task.user_request or ""))


class Planner:
    def __init__(self, registry: CapabilityRegistry):
        self.registry = registry

    # ── initial plan ─────────────────────────────────────────────────

    def plan(self, task: Task) -> Task:
        requested = list(task.constraints.get("_candidate_capabilities") or [])

        if not requested:
            requested = ["agriculture_rag"]

        # Validate against the registry; unknown names are dropped, not
        # fatal — the router never routes to something the registry
        # didn't declare.
        valid: List[str] = []
        for name in requested:
            if self.registry.get(name) is not None:
                if name not in valid:
                    valid.append(name)
            else:
                task.errors.append({
                    "stage": "planner",
                    "error": f"unknown capability '{name}' from task analyzer — skipped",
                })

        # ── Safety net #1: document-intent fallback ──────────────────
        # If the request obviously wants a pdf/document/report and the
        # analyzer's own candidate list didn't include document_author
        # (the write/execute/inspect authoring capability) OR the older
        # document_compose/document_render chain, add document_author —
        # its own internal loop decides tables/charts/images on its own,
        # no separate injection needed. Prefers whatever content-source
        # capability is already selected (agriculture_rag is extremely
        # common for this project's requests) over adding a new one.
        authoring_chain = {"document_author", "document_compose", "document_render"}
        if _wants_document(task) and not (authoring_chain & set(valid)):
            content_source = "agriculture_rag" if "agriculture_rag" in valid else "topic_research"
            if content_source not in valid:
                valid.append(content_source)
            valid.append("document_author")
            task.errors.append({
                "stage": "planner", "level": "warning",
                "error": "task analyzer omitted the document-authoring capability for an "
                         "apparent document request — added document_author automatically "
                         f"(content source: {content_source})",
            })

        # ── Safety net #2: chart / image inference ────────────────────
        # Only relevant for the OLDER document_compose/document_render
        # chain, which has separate chart_generate/image_search steps.
        # document_author decides this internally, per-request.
        if "document_compose" in valid or "document_render" in valid:
            if _CHART_INTENT_RE.search(task.user_request or "") and "chart_generate" not in valid:
                valid.append("chart_generate")
            if _IMAGE_INTENT_RE.search(task.user_request or "") and "image_search" not in valid:
                valid.append("image_search")

        for trigger, auto_cap in _AUTO_VALIDATE.items():
            if trigger in valid and auto_cap not in valid:
                valid.append(auto_cap)

        if not valid:
            valid = ["agriculture_rag"]

        ordered = self._topological_order(valid)

        plan: List[PlanStep] = []
        step_id_by_capability: Dict[str, str] = {}
        for i, cap_name in enumerate(ordered, start=1):
            cap = self.registry.get(cap_name)
            step_id = f"s{i}"
            dep_candidates = _DEPENDENCY_ALIASES.get(cap_name, cap.depends_on_capabilities)
            depends_on = [step_id_by_capability[dep] for dep in dep_candidates
                          if dep in step_id_by_capability]
            args_builder = _ARG_BUILDERS.get(cap_name, _args_empty)
            plan.append(PlanStep(
                id=step_id, capability=cap_name, agent_name=cap.agent_name,
                args=args_builder(task), depends_on=depends_on,
                optional=cap.optional_by_default,
                # FIX: this was never set, so failure_recovery.classify_failure's
                # fallback (`step.failure_class or TOOL`) always saw None and
                # used the generic TOOL class instead of what the registry
                # actually declared (e.g. document_author -> PDF_RENDER) —
                # didn't change THIS bug's outcome (both route to retry_same),
                # but was silently wrong for any future failure_class-specific
                # recovery logic.
                failure_class=cap.failure_class,
            ))
            step_id_by_capability[cap_name] = step_id

        task.plan = plan
        return task

    # ── replanning ───────────────────────────────────────────────────

    def replan(self, task: Task, failed_step: PlanStep, new_capability: str) -> Task:
        task.replans += 1
        cap = self.registry.get(new_capability)
        new_id = f"{failed_step.id}-r{task.replans}"
        new_step = PlanStep(
            id=new_id, capability=new_capability,
            agent_name=cap.agent_name if cap else failed_step.agent_name,
            args=dict(failed_step.args), depends_on=list(failed_step.depends_on),
            optional=cap.optional_by_default if cap else failed_step.optional,
        )
        task.plan.append(new_step)

        # Reroute: anything that depended on the failed step now depends
        # on its replacement instead, so a downstream step reads the
        # RETRY's output rather than the permanently-failed original.
        for s in task.plan:
            if failed_step.id in s.depends_on:
                s.depends_on = [new_id if d == failed_step.id else d for d in s.depends_on]

        return task

    # ── topological ordering over depends_on_capabilities ───────────

    def _topological_order(self, capability_names: List[str]) -> List[str]:
        names = set(capability_names)
        visited: set = set()
        order: List[str] = []

        def visit(name: str, stack: frozenset):
            if name in visited or name not in names:
                return
            if name in stack:
                return  # cycle guard — shouldn't happen with this registry, don't hang if it does
            cap = self.registry.get(name)
            dep_candidates = _DEPENDENCY_ALIASES.get(name, cap.depends_on_capabilities if cap else [])
            next_stack = stack | {name}
            for dep in dep_candidates:
                visit(dep, next_stack)
            if name not in visited:
                visited.add(name)
                order.append(name)

        for name in capability_names:
            visit(name, frozenset())
        return order