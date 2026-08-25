"""
claim_verification.py

Phase 8 of the knowledge-system upgrade: a claim-level evidence gate that
runs AFTER answer generation (rag_pipeline.py's _generate_grounded /
_generate_from_web) and BEFORE the answer is returned to the user.

WHY THIS IS NEEDED (found during the audit, not assumed)
-----------------------------------------------------------
The existing citation mechanism — rag_pipeline._inject_inline_citations()
— is pure keyword overlap: it tags a sentence with "[N]" if source N's
top keywords appear in that sentence. It never checks whether source N's
actual text *supports* the claim in that sentence. That's exactly what
Part 20 of the spec warns against ("Do not cite a document merely
because it appeared in retrieval — the cited evidence must actually
support the claim"). This module doesn't touch _inject_inline_citations
(citations still render exactly as before) — it adds a SEPARATE,
independent check on top: does the evidence actually say what the
answer claims it says.

WHAT THIS DOES
--------------
1. Extracts the discrete factual claims from the generated answer (one
   LLM call, not one call per claim — Part 31: don't sacrifice latency).
2. For each claim, checks it against the snippet text of the source(s)
   it's tagged to (or, if untagged, against ALL source snippets) and
   assigns one of: SUPPORTED / PARTIALLY_SUPPORTED / INSUFFICIENT_EVIDENCE
   / CONFLICTING_EVIDENCE.
3. Flags high-risk claims (pesticide/chemical dosage, fertilizer rate,
   veterinary treatment — Part 32) that need a stricter bar: these are
   only left standing if SUPPORTED, not PARTIALLY_SUPPORTED.
4. Produces an overall status + a plain-language confidence label (High
   / Medium / Low — never fake precision like "97.34%", per Part 22).
5. If the overall evidence is insufficient, or a high-risk claim isn't
   properly supported, appends an explicit, honest qualifier to the
   answer — it does NOT silently delete or rewrite the model's prose
   (Part 19: "removed or explicitly qualified" — qualifying is the safer
   of the two; surgical deletion risks garbling a sentence's grammar).

WHAT THIS DELIBERATELY DOES NOT DO
------------------------------------
It does not second-guess the existing decision (already made deliberately
in _generate_grounded's system prompt) to let the model supplement
retrieved context with well-established general agricultural knowledge
when context is only partial. That's an existing, intentional product
choice — Part 3 of this spec is in real tension with it (Part 3 says the
LLM must never be the source of truth), and resolving that tension is a
product decision, not something to silently overrule here. What this
module DOES do is make the gap visible: a claim that came from the
model's general knowledge rather than the cited evidence gets tagged
INSUFFICIENT_EVIDENCE rather than waved through — the caller decides
what to do with that (currently: qualify it, not strip it).
"""
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Terms that trigger the stricter "must be SUPPORTED, not just
# PARTIALLY_SUPPORTED" bar (Part 32). Deliberately broad/cheap
# (substring match) rather than a full NER model — false positives here
# just mean an extra claim gets held to a higher bar, which is the safe
# direction to err in for this category.
HIGH_RISK_TERMS = [
    "dosage", "dose", "ml/l", "g/l", "kg/acre", "kg/ha", "liters per",
    "mix ratio", "application rate", "pesticide", "fungicide",
    "insecticide", "herbicide", "spray concentration", "withdrawal period",
    "veterinary", "vaccination schedule", "drug", "antibiotic",
]


@dataclass
class ClaimVerdict:
    claim: str
    status: str                     # SUPPORTED | PARTIALLY_SUPPORTED | INSUFFICIENT_EVIDENCE | CONFLICTING_EVIDENCE
    cited_sources: List[int]        # source "num"s this claim was checked against
    high_risk: bool
    note: str = ""


@dataclass
class VerificationResult:
    overall_status: str             # SUPPORTED | PARTIALLY_SUPPORTED | INSUFFICIENT_EVIDENCE | CONFLICTING_EVIDENCE | OUT_OF_SCOPE
    confidence: str                 # High | Medium | Low
    claims: List[ClaimVerdict] = field(default_factory=list)
    unresolved_high_risk: List[str] = field(default_factory=list)
    raw_llm_output: str = ""


def _is_high_risk(claim_text: str) -> bool:
    low = claim_text.lower()
    return any(term in low for term in HIGH_RISK_TERMS)


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()
    # Strip ```json ... ``` / ``` ... ``` fences — models frequently wrap
    # JSON in these despite being told not to; stripping first means the
    # plain json.loads() below succeeds instead of falling through to the
    # regex scan (which also works, but this is the common case).
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return _salvage_claims(text)


_CLAIM_OBJ_RE = re.compile(r'\{\s*"claim"\s*:.*?\}(?=\s*[,\]])', re.DOTALL)


def _salvage_claims(text: str) -> Optional[Dict[str, Any]]:
    """
    Last-resort recovery for a response that got cut off mid-JSON (the
    observed failure mode: a big variance in verify_answer()'s own
    duration — some calls taking 10x longer than others — is consistent
    with the model running long and hitting max_tokens mid-object,
    producing syntactically invalid JSON that a whole-document parse
    will always reject).

    Rather than throwing the whole response away, pull out each
    INDIVIDUAL claim object that completed before the cutoff — a claim
    object is well-formed even if the array/outer object around it
    wasn't closed. Whatever's recoverable is still more useful than
    "0 claims checked" on every single answer.
    """
    found = []
    for m in _CLAIM_OBJ_RE.finditer(text):
        candidate = m.group(0).rstrip(",")
        try:
            found.append(json.loads(candidate))
        except json.JSONDecodeError:
            continue
    if not found:
        return None
    return {"claims": found}


_SYSTEM_PROMPT = """You are a strict factual-claim verifier for an agriculture knowledge system.

You will be given a QUESTION, an ANSWER (with inline [N] citation tags), and the SOURCE SNIPPETS those numbers refer to.

Do this:
1. Break the ANSWER into its distinct factual claims (skip filler/transition sentences that assert nothing checkable).
2. For each claim, check it against the source snippet(s) its [N] tag(s) point to (if a claim has no [N] tag, check it against ALL snippets).
3. Classify each claim as exactly one of:
   - "SUPPORTED" — the cited snippet(s) clearly state this
   - "PARTIALLY_SUPPORTED" — the snippet(s) are topically related but don't fully confirm the specific claim (e.g. general knowledge, not explicitly in the evidence)
   - "INSUFFICIENT_EVIDENCE" — nothing in the snippets supports this claim at all
   - "CONFLICTING_EVIDENCE" — two or more snippets disagree with each other on this claim

Respond with ONLY this JSON, nothing else. Keep "claim" paraphrases SHORT (<=12 words) and only include "note" when status is not SUPPORTED — this keeps the response compact enough to complete within the token budget:
{
  "claims": [
    {"claim": "<short paraphrase>", "status": "SUPPORTED|PARTIALLY_SUPPORTED|INSUFFICIENT_EVIDENCE|CONFLICTING_EVIDENCE", "cited_sources": [<ints>], "note": "<<=15 words, only if not SUPPORTED>"}
  ]
}
"""


def verify_answer(llm, query: str, answer: str, sources: List[Dict[str, Any]]) -> VerificationResult:
    """
    llm: the project's existing LLMClient (rag_pipeline.LLMClient) — same
        instance already used for generation, no second client needed.
    sources: the SAME structured sources list _build_sources_from_docs /
        _build_sources_from_web already produce, with one addition this
        module's caller (rag_pipeline.py) makes to both: a "snippet"
        field carrying a text excerpt (not just keywords) — see the
        rag_pipeline.py edit alongside this file.

    Runs ONE LLM call regardless of how many claims/sources there are —
    Part 31 (performance): claim extraction + verification is a single
    pass, not N calls.
    """
    if not answer or not answer.strip():
        return VerificationResult(overall_status="OUT_OF_SCOPE", confidence="Low")

    if not sources:
        # No evidence was retrieved at all — can't verify anything, and
        # per Part 18 that itself IS the finding, not a reason to skip
        # the check.
        return VerificationResult(
            overall_status="INSUFFICIENT_EVIDENCE", confidence="Low",
            claims=[ClaimVerdict(claim=answer[:120], status="INSUFFICIENT_EVIDENCE",
                                  cited_sources=[], high_risk=_is_high_risk(answer),
                                  note="No sources were retrieved for this answer.")],
        )

    snippet_block = "\n\n".join(
        f"[{s['num']}] {s.get('label', s.get('source_file', ''))}\n{s.get('snippet', '')[:600]}"
        for s in sources
    )
    user_prompt = f"QUESTION: {query}\n\nANSWER:\n{answer}\n\nSOURCE SNIPPETS:\n{snippet_block}\n\nJSON:"

    try:
        raw, _usage = llm.call(_SYSTEM_PROMPT, user_prompt, max_tokens=1600, temperature=0.0)
    except Exception as e:
        # Fail safe, not fail open: an unrunnable verification step means
        # we genuinely don't know — treat as insufficient rather than
        # silently skipping the gate.
        return VerificationResult(
            overall_status="INSUFFICIENT_EVIDENCE", confidence="Low",
            claims=[], raw_llm_output=f"verification call failed: {e}",
        )

    parsed = _extract_json(raw)
    if parsed is None or "claims" not in parsed:
        return VerificationResult(
            overall_status="INSUFFICIENT_EVIDENCE", confidence="Low",
            claims=[], raw_llm_output=raw,
        )

    claims: List[ClaimVerdict] = []
    unresolved_high_risk: List[str] = []
    for c in parsed.get("claims", []):
        claim_text = str(c.get("claim", "")).strip()
        status = str(c.get("status", "INSUFFICIENT_EVIDENCE")).upper()
        if status not in ("SUPPORTED", "PARTIALLY_SUPPORTED", "INSUFFICIENT_EVIDENCE", "CONFLICTING_EVIDENCE"):
            status = "INSUFFICIENT_EVIDENCE"
        cited = [int(n) for n in c.get("cited_sources", []) if isinstance(n, (int, float, str)) and str(n).isdigit()]
        high_risk = _is_high_risk(claim_text)
        note = str(c.get("note", ""))[:200]

        if high_risk and status != "SUPPORTED":
            # Part 32: high-risk claims need the SUPPORTED bar specifically —
            # PARTIALLY_SUPPORTED isn't good enough for a dosage/treatment claim.
            unresolved_high_risk.append(claim_text)

        claims.append(ClaimVerdict(claim=claim_text, status=status, cited_sources=cited,
                                    high_risk=high_risk, note=note))

    # ── aggregate overall status ──────────────────────────────────────
    statuses = [c.status for c in claims]
    if unresolved_high_risk:
        overall = "INSUFFICIENT_EVIDENCE"
    elif "CONFLICTING_EVIDENCE" in statuses:
        overall = "CONFLICTING_EVIDENCE"
    elif not claims:
        overall = "OUT_OF_SCOPE"
    elif all(s == "SUPPORTED" for s in statuses):
        overall = "SUPPORTED"
    elif any(s == "INSUFFICIENT_EVIDENCE" for s in statuses) and \
            all(s in ("SUPPORTED", "INSUFFICIENT_EVIDENCE") for s in statuses):
        # mix of solid and ungrounded claims — meaningfully worse than
        # "partially supported everywhere", surface it distinctly
        overall = "PARTIALLY_SUPPORTED" if any(s == "SUPPORTED" for s in statuses) else "INSUFFICIENT_EVIDENCE"
    else:
        overall = "PARTIALLY_SUPPORTED"

    confidence = {
        "SUPPORTED": "High",
        "PARTIALLY_SUPPORTED": "Medium",
        "CONFLICTING_EVIDENCE": "Low",
        "INSUFFICIENT_EVIDENCE": "Low",
        "OUT_OF_SCOPE": "Low",
    }[overall]

    return VerificationResult(
        overall_status=overall, confidence=confidence, claims=claims,
        unresolved_high_risk=unresolved_high_risk, raw_llm_output=raw,
    )


def apply_qualifier(answer: str, result: VerificationResult) -> str:
    """Appends an honest, visible qualifier when warranted — never
    silently deletes or rewrites the model's prose (Part 19). Returns
    the answer UNCHANGED when overall_status is SUPPORTED or
    PARTIALLY_SUPPORTED with no unresolved high-risk claims."""
    if result.overall_status == "SUPPORTED" and not result.unresolved_high_risk:
        return answer

    if result.unresolved_high_risk:
        items = "; ".join(result.unresolved_high_risk[:3])
        return (
            f"{answer}\n\n"
            f"⚠️ Note: this answer includes specific recommendation(s) "
            f"({items}) that aren't clearly confirmed by the retrieved "
            f"sources — verify with a local agricultural extension office "
            f"or authoritative source before acting on them."
        )

    if result.overall_status == "INSUFFICIENT_EVIDENCE":
        return (
            f"{answer}\n\n"
            f"⚠️ Note: I couldn't find sufficient authoritative evidence "
            f"to fully confirm this answer — treat it as general "
            f"information rather than a verified recommendation."
        )

    if result.overall_status == "CONFLICTING_EVIDENCE":
        return (
            f"{answer}\n\n"
            f"⚠️ Note: the sources I found don't fully agree with each "
            f"other on this — the answer above reflects the most "
            f"authoritative/relevant source, but you may want to check "
            f"the specific context (region, season, variety) that applies to you."
        )

    return answer