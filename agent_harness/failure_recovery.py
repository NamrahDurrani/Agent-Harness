"""
agent_harness/failure_recovery.py

Sections 14-16 — classify WHY a step failed, then route to an appropriate
recovery action rather than blindly retrying the same thing or giving up.
This is what makes the harness's retry behavior different from
agent_box.py's own bounded same-args retry (which still runs underneath,
per-step, for transient errors) — this layer decides whether a
DIFFERENT capability should be tried after that's exhausted.
"""
from dataclasses import dataclass
from typing import Optional

from .task_state import PlanStep

# Failure classes (Section 15)
FACTUAL = "FACTUAL"
RETRIEVAL = "RETRIEVAL"
LAYOUT = "LAYOUT"          # reserved — no layout-generation capability exists yet in this registry
MISSING_CONTENT = "MISSING_CONTENT"
MISSING_SOURCE = "MISSING_SOURCE"
TOOL = "TOOL"
MODEL = "MODEL"
PDF_RENDER = "PDF_RENDER"


@dataclass
class RecoveryDecision:
    action: str                       # "retry_same" | "try_capability" | "skip_optional" | "give_up"
    capability: Optional[str] = None  # set when action == "try_capability"
    reason: str = ""


def classify_failure(step: PlanStep, exception: Optional[Exception] = None) -> str:
    """Section 15. Prefers the capability's own declared failure_class
    (set in default_capabilities.py) since that's the most reliable
    signal — a pdf_generate failure is a PDF_RENDER failure regardless of
    what Python exception type happened to be raised. Falls back to
    inspecting the exception/issues only when the capability didn't
    declare one."""
    if step.result and step.result.issues:
        issues_text = " ".join(step.result.issues).lower()
        if "source" in issues_text and "no sources" in issues_text:
            return MISSING_SOURCE
        if "empty answer" in issues_text or "no answer" in issues_text:
            return MISSING_CONTENT

    if exception is not None:
        msg = str(exception).lower()
        if "timeout" in msg or "connection" in msg or "rate limit" in msg:
            return TOOL
        if "pdf" in msg or "fitz" in msg:
            return PDF_RENDER

    return step.failure_class or TOOL


def decide_recovery(task_replans: int, max_replans: int, step: PlanStep,
                     failure_class: str) -> RecoveryDecision:
    """Section 15/16/17 — the routing table. Bounded by max_replans
    (Section 17: never infinite loops); once exhausted, an optional step
    is skipped rather than failing the whole task (Section 35 — goal-
    based completion), a required step gives up and the task fails.
    """
    if task_replans >= max_replans:
        if step.optional:
            return RecoveryDecision("skip_optional", reason="max_replans reached, step is optional")
        return RecoveryDecision("give_up", reason="max_replans reached, step is required")

    if failure_class == RETRIEVAL and step.capability == "agriculture_rag":
        # Section 15: retrieval failure -> alternative retrieval. The
        # registry's own agriculture_rag capability already tries
        # RAG-then-web internally (rag_pipeline.py's own retry loop) —
        # the harness-level fallback beyond that is a direct web_search,
        # which has a different query-shaping path than the RAG tool's
        # internal web fallback.
        return RecoveryDecision("try_capability", capability="web_search",
                                 reason="agriculture_rag exhausted its own internal retries")

    if failure_class == MISSING_SOURCE and step.capability == "agriculture_rag":
        return RecoveryDecision("try_capability", capability="web_search",
                                 reason="no sources from knowledge base — trying web")

    if failure_class == PDF_RENDER:
        # Section 15: PDF corruption/render failure -> regenerate, not
        # switch capability (there's only one PDF renderer).
        return RecoveryDecision("retry_same", reason="PDF render/validation failed — regenerating")

    if failure_class == TOOL:
        return RecoveryDecision("retry_same", reason="transient tool failure")

    if step.optional:
        return RecoveryDecision("skip_optional", reason=f"{failure_class} failure on an optional step")

    return RecoveryDecision("give_up", reason=f"no recovery strategy for {failure_class} on a required step")
