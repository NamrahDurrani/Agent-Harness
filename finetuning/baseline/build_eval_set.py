"""
finetuning/baseline/build_eval_set.py

Phase 4 (master prompt Sections 19/41): build a FROZEN, AgriBot-specific
evaluation set from REAL documents already in your ChromaDB collection.

REWRITE 2 — question STYLE and TOPIC targeting, per explicit feedback that
the first real run generated academic/international-development-sounding
questions ("What barriers do women in Tanzania face...", "PoU 2011-2017")
instead of simple farmer-style questions, even though it was sampling
files literally named FAO_fertilizer_recommendations.pdf. Root cause,
confirmed from that run's own output: this KB's files are broad FAO
reports with heterogeneous content, not narrow single-topic guides — so
PURE RANDOM chunk sampling was always going to occasionally surface
unrelated development-statistics content. Two changes fix this:
  1. TOPIC-WEIGHTED sampling: chunks are tagged by keyword into topic
     buckets (crop cultivation, fertilizer, irrigation, pest, disease,
     soil, varieties, Pakistan/local, general) and drawn according to the
     target percentages below — instead of uniformly across all 27k+
     chunks regardless of what they're actually about.
  2. A much stricter question-generation PROMPT, with explicit simple-
     style few-shot examples AND explicit negative examples taken from
     the actual bad questions this script generated last run — so the
     model has a concrete contrast, not just an abstract instruction.

Everything else (API-call budget, daily-quota-vs-temporary-limit
handling, no model fallback, no key rotation, resumability, exact
logging format) is UNCHANGED from the previous version — this rewrite is
scoped to question generation strategy only, per the request.

REWRITE 3 — FIX: Windows console UnicodeEncodeError. A real run crashed
with `UnicodeEncodeError: 'charmap' codec can't encode character
'\\u2011'` when printing a rejected LLM-generated question that contained
a non-breaking hyphen. PowerShell's default console codepage (cp1252)
can't represent that character, so print() raised and took the whole
run down mid-loop. Fix is display-only — added a stdout/stderr UTF-8
reconfigure right after imports, on Windows only. No generation,
verification, sampling, or budget logic changed.

Usage unchanged:
    python build_eval_set.py --total 5                    # smoke test
    python build_eval_set.py                              # default: 40 (20/10/10)
    python build_eval_set.py --total 40 --max-api-calls 25
"""
import argparse
import json
import os
import random
import re
import sys
import time
import uuid
from pathlib import Path

# --- FIX: Windows console can't print non-ASCII characters (e.g. the
# non-breaking hyphen '\u2011' an LLM-generated question can contain)
# under the default cp1252 codepage, which crashed the run mid-loop.
# Force UTF-8 stdout/stderr on Windows so any such character is printed
# (or safely replaced) instead of raising UnicodeEncodeError. No effect
# on non-Windows platforms.
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import vector_store                        # noqa: E402 — your existing module, unmodified
from rag_pipeline import get_llm_client     # noqa: E402 — your existing LLM client factory, unmodified

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "eval_set_v1.jsonl"

DEFAULT_RATIO = (20, 10, 10)   # answerable, unanswerable, partial — sums to 40 (support-status split, UNCHANGED)
DEFAULT_MAX_API_CALLS = 60     # bumped 25 -> 60: real cost is >=2 calls per ACCEPTED question (generate +
                                # verify), and a verification rejection burns calls with nothing accepted —
                                # 25 was producing only ~3 accepted questions per run, meaning several reruns
                                # were needed just to rebuild from zero. Still a hard, configurable cap — not
                                # unlimited — just sized closer to what a full-from-scratch build actually costs.
RANDOM_SEED = 42

random.seed(RANDOM_SEED)


def mask_key(key: str) -> str:
    if not key or len(key) < 4:
        return "(not set)"
    return "*" * 8 + key[-4:]


# ── NEW: topic tagging + weighted sampling ──────────────────────────────
# Percentages from the requested question distribution (Section 12).
# "general" has no keyword filter — it's the catch-all pool, matching any
# chunk, used both for its own 5% share and as a fallback if a specific
# topic bucket runs short of real chunks.
TOPIC_KEYWORDS = {
    "crop_cultivation": ["sow", "sowing", "plant", "cultivat", "harvest", "crop rotation",
                          "wheat", "rice", "maize", "cotton", "sugarcane"],
    "fertilizer":       ["fertiliz", "fertilis", "npk", "nitrogen", "phosphorus", "potassium",
                          "urea", "dap ", "manure", "nutrient"],
    "irrigation":       ["irrigat", "water requirement", "water need", "drought", "rainfall",
                          "canal", "tube well", "tubewell"],
    "pest":             ["pest", "insect", "aphid", "borer", "weevil", "locust", "pesticide",
                          "integrated pest management"],
    "disease":          ["disease", "fungal", "fungus", "blight", "rust", "wilt", "pathogen"],
    "soil":             ["soil", "ph level", "loam", "salinity", "soil fertility", "soil test"],
    "varieties":        ["variety", "varieties", "cultivar", "hybrid seed", "seed variety"],
    "pakistan_local":   ["pakistan", "punjab", "sindh", "khyber pakhtunkhwa", "balochistan", " kpk"],
}
TOPIC_TARGET_PCT = {
    "crop_cultivation": 0.20, "fertilizer": 0.15, "irrigation": 0.10, "pest": 0.15,
    "disease": 0.10, "soil": 0.10, "varieties": 0.05, "pakistan_local": 0.10, "general": 0.05,
}


def tag_chunks_by_topic(chunks):
    """Buckets chunks by keyword match. A chunk can land in multiple
    buckets. 'general' always contains every chunk (it's the no-filter
    catch-all AND the fallback pool for underrepresented topics)."""
    buckets = {topic: [] for topic in TOPIC_TARGET_PCT}
    buckets["general"] = chunks
    for chunk in chunks:
        low = chunk["text"].lower()
        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(kw in low for kw in keywords):
                buckets[topic].append(chunk)
    for topic in TOPIC_KEYWORDS:
        print(f"[BUILD_EVAL]   topic '{topic}': {len(buckets[topic])} matching chunks")
    return buckets


def pick_weighted_chunk(topic_buckets, rng=random):
    """Draws ONE chunk, first picking a topic per TOPIC_TARGET_PCT, then a
    chunk uniformly within that topic's bucket. Falls back to 'general'
    if the chosen topic's bucket is empty (rather than erroring)."""
    topics = list(TOPIC_TARGET_PCT.keys())
    weights = [TOPIC_TARGET_PCT[t] for t in topics]
    topic = rng.choices(topics, weights=weights, k=1)[0]
    pool = topic_buckets[topic] or topic_buckets["general"]
    return rng.choice(pool), topic


def pick_weighted_pair(topic_buckets, rng=random):
    """Same idea as pick_weighted_chunk but returns two DIFFERENT chunks —
    used for the partially-supported generator, which needs chunk A
    (topic-weighted, real evidence) and chunk B (a genuinely different
    topic, so B is a real distractor rather than more of the same)."""
    a, topic_a = pick_weighted_chunk(topic_buckets, rng)
    other_topics = [t for t in TOPIC_TARGET_PCT if t != topic_a]
    topic_b = rng.choice(other_topics)
    pool_b = topic_buckets[topic_b] or topic_buckets["general"]
    b = rng.choice(pool_b)
    return a, b, topic_a


# ── Budgeted, safety-first LLM calling (UNCHANGED from previous version) ──
_WAIT_RE             = re.compile(r"try again in about (\d+) minute", re.IGNORECASE)
_DAILY_QUOTA_MARKERS = ("usage limit", "daily limit", "daily quota", "insufficient quota")
_AUTH_MARKERS        = ("authentication", "invalid api key", "unauthorized", "401")
_UNAVAILABLE_MARKERS = ("model unavailable", "model not found", "does not exist")


class QuotaStop(Exception):
    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


class RunState:
    def __init__(self, max_api_calls):
        self.api_calls_made = 0
        self.max_api_calls = max_api_calls
        self.failed_calls = 0
        self.retry_count = 0
        self.rejected_verification = 0   # NEW: tracks the "generated fine, chunk didn't support it" case
        self.rejected_incomplete = 0     # NEW: tracks empty/truncated/duplicate generations


def call_llm_budgeted(llm, state: RunState, system_prompt, user_text, max_tokens=512, temperature=0.3):
    if state.api_calls_made >= state.max_api_calls:
        raise QuotaStop(f"API call safety limit reached ({state.max_api_calls} calls this run).")
    max_temp_retries = 2
    for attempt in range(max_temp_retries + 1):
        if state.api_calls_made >= state.max_api_calls:
            raise QuotaStop(f"API call safety limit reached ({state.max_api_calls} calls this run).")
        state.api_calls_made += 1
        try:
            return llm.call(system_prompt, user_text, max_tokens=max_tokens, temperature=temperature)
        except Exception as e:
            msg = str(e).lower()
            state.failed_calls += 1
            if any(m in msg for m in _AUTH_MARKERS):
                raise QuotaStop(f"Authentication error — check your GROQ_API_KEY. Raw: {e}")
            if any(m in msg for m in _UNAVAILABLE_MARKERS):
                raise QuotaStop(f"Model unavailable. Raw: {e}")
            if any(m in msg for m in _DAILY_QUOTA_MARKERS):
                raise QuotaStop(f"Daily/account quota exhausted. Raw: {e}")
            if attempt < max_temp_retries:
                state.retry_count += 1
                m = _WAIT_RE.search(msg)
                wait_s = (int(m.group(1)) * 60 + 5) if m else 10
                print(f"[BUILD_EVAL]   temporary-looking rate limit — waiting {wait_s}s "
                      f"(retry {attempt + 1}/{max_temp_retries})...")
                time.sleep(wait_s)
                continue
            raise QuotaStop(f"Repeated failures on what looked like a temporary rate limit. Raw: {e}")


def load_real_chunks():
    collection = vector_store._get_collection()
    count = collection.count()
    if count == 0:
        raise RuntimeError("Your ChromaDB collection is empty — ingest documents first.")
    print(f"[BUILD_EVAL] Collection has {count} chunks.")
    results = collection.get(include=["documents", "metadatas"])
    chunks = []
    for text, meta in zip(results["documents"], results["metadatas"]):
        if text and len(text.strip()) > 200:
            chunks.append({
                "text": text,
                "source_file": (meta or {}).get("source_file", "unknown"),
                "page_num": (meta or {}).get("page_num", 0),
            })
    print(f"[BUILD_EVAL] {len(chunks)} usable chunks after filtering short/empty ones.")
    return chunks


# ── NEW: difficulty tiers (Section 3 — 60/25/15) ────────────────────────
_DIFFICULTY_INSTRUCTIONS = {
    "simple": "Write a SHORT, SIMPLE question (like 'What fertilizer is good for wheat?') — "
              "the kind a farmer would type in one breath.",
    "moderate": "Write a moderately specific question — e.g. naming a growth stage or a "
                "particular condition, like 'What fertilizer should I use during the early "
                "growth stage of wheat?' — still natural, not academic.",
    "challenging": "Write a slightly more involved but still realistic question — e.g. "
                   "describing a symptom and asking what to do, like 'My wheat crop has "
                   "yellow leaves and poor growth — what could be the cause?' — still "
                   "something a real farmer would actually type, NOT an academic or "
                   "statistical question.",
}


def _pick_difficulty(rng=random):
    return rng.choices(["simple", "moderate", "challenging"], weights=[0.60, 0.25, 0.15], k=1)[0]


# ── Type 1: fully supported ─────────────────────────────────────────────
# REWRITTEN prompt: explicit simple-farmer-question style, few-shot GOOD
# examples from the requested style guide, and explicit BAD examples
# taken directly from this script's own previous run — a concrete
# negative contrast, not just an abstract "be simple" instruction.
_QUESTION_GEN_SYSTEM = """You write ONE simple, realistic farmer-style question that this exact document chunk answers.

GOOD examples (this is the style to match):
- What fertilizer is good for wheat?
- When should I plant rice?
- What are common diseases of wheat?
- How much water does cotton need?
- Which crops are commonly grown in Punjab?

BAD examples (NEVER write questions like these — academic, statistical, or about unrelated countries/organizations, even if the chunk happens to contain this kind of content):
- What barriers do women in Tanzania still face in accessing agricultural resources?
- How much did the group invest in small-scale distillation equipment for star anise oil?
- What proportion of low- and middle-income countries increased their PoU between 2011 and 2017?

If the chunk you were given is ONLY about something in the BAD-example style (international development statistics, unrelated countries, organizational funding) and has no genuine simple farming angle, do not force a question — just write the most natural farming-relevant question you can that the chunk still actually supports.

{difficulty_instruction}

Output ONLY the question, nothing else. One complete sentence ending in a question mark. Do not reference "the document" or "the text"."""

_SUPPORT_CHECK_SYSTEM = (
    "Does the following document chunk contain enough information to "
    "fully answer the question? Answer with exactly one word: YES or NO."
)


def _looks_complete(question: str) -> bool:
    q = question.strip()
    return len(q) >= 15 and q.endswith("?") and len(q.split()) >= 4


def _normalize_for_dedup(question: str) -> str:
    """Case/whitespace/punctuation-insensitive form used to catch exact
    duplicates (e.g. two verbatim-identical generations) — a real bug
    found when a real run produced two identical questions from two
    different chunk draws on the same topic."""
    q = question.strip().lower().rstrip("?").strip()
    q = re.sub(r"[^\w\s]", "", q)
    return re.sub(r"\s+", " ", q)


def _is_near_duplicate(norm_question: str, seen_normalized: set, threshold: float = 0.7) -> bool:
    """Catches near-duplicates the exact check misses — e.g. 'which
    irrigation treatment HAD higher water productivity' vs '...GIVES
    higher water productivity', a real pair found in an actual run.
    Simple word-overlap (Jaccard) similarity — no extra dependency."""
    words = set(norm_question.split())
    if not words:
        return False
    for other in seen_normalized:
        other_words = set(other.split())
        if not other_words:
            continue
        overlap = len(words & other_words) / len(words | other_words)
        if overlap >= threshold:
            return True
    return False


def _generate_question_with_retry(llm, state, system_prompt, user_text, seen_questions, max_attempts=2):
    for attempt in range(1, max_attempts + 1):
        question, _ = call_llm_budgeted(llm, state, system_prompt, user_text,
                                         max_tokens=512, temperature=0.3)
        question = question.strip().strip('"')
        if not _looks_complete(question):
            state.rejected_incomplete += 1
            print(f"[BUILD_EVAL]   attempt {attempt}: rejected incomplete/empty generation "
                  f"({question!r})" + (" — retrying" if attempt < max_attempts else " — giving up on this chunk"))
            continue
        norm = _normalize_for_dedup(question)
        if norm in seen_questions or _is_near_duplicate(norm, seen_questions):
            state.rejected_incomplete += 1
            print(f"[BUILD_EVAL]   attempt {attempt}: rejected DUPLICATE/near-duplicate question "
                  f"({question!r})" + (" — retrying" if attempt < max_attempts else " — giving up on this chunk"))
            continue
        seen_questions.add(norm)
        return question
    return None


def _load_existing(output_path) -> list:
    if not output_path.exists():
        return []
    with open(output_path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _append_example(output_path, example):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(example, ensure_ascii=False) + "\n")
        f.flush()


def generate_fully_supported(llm, state, topic_buckets, n, already_have, seen_questions):
    examples = []
    need = max(0, n - already_have)
    if need == 0:
        return examples
    attempts_budget = need * 3  # oversample draws; some fail verification/validation
    for _ in range(attempts_budget):
        if len(examples) >= need:
            break
        chunk, topic = pick_weighted_chunk(topic_buckets)
        difficulty = _pick_difficulty()
        prompt = _QUESTION_GEN_SYSTEM.format(difficulty_instruction=_DIFFICULTY_INSTRUCTIONS[difficulty])
        question = _generate_question_with_retry(llm, state, prompt, chunk["text"][:2000], seen_questions)
        if question is None:
            continue
        verdict, _ = call_llm_budgeted(llm, state, _SUPPORT_CHECK_SYSTEM,
                                        f"Question: {question}\n\nChunk:\n{chunk['text'][:2000]}",
                                        max_tokens=256, temperature=0.0)
        if "YES" not in verdict.strip().upper():
            # VISIBILITY FIX: this was previously a silent `continue` — the
            # question generated fine, but the chunk doesn't actually
            # support it, so it's discarded. This (not just empty/duplicate
            # generations) is a major consumer of API calls with nothing
            # accepted — now logged so a low accept-rate run is explainable
            # instead of looking like calls are vanishing.
            print(f"[BUILD_EVAL]   rejected by verification (chunk doesn't fully support): {question!r}")
            state.rejected_verification += 1
            continue
        ex = {
            "id": f"fs-{uuid.uuid4().hex[:8]}", "category": "fully_answerable",
            "topic": topic, "difficulty": difficulty,
            "question": question, "oracle_source": chunk["source_file"],
            "oracle_page": chunk["page_num"], "oracle_text": chunk["text"][:2000],
            "support_status": "fully_supported",
        }
        _append_example(OUTPUT_PATH, ex)
        examples.append(ex)
    return examples


# ── Type 2: unanswerable ─────────────────────────────────────────────────
_UNANSWERABLE_SYSTEM = (
    "You write ONE simple, realistic farmer-style agriculture question "
    "that CANNOT be answered from this document chunk, but is clearly "
    "on-topic for practical farming — e.g. asking for today's exact "
    "price, this week's precise weather, or a specific current number "
    "the chunk does not contain. Keep it short and natural, like 'What "
    "is today's wheat price in Lahore?' — NOT an academic or statistical "
    "question. Output ONLY the question."
)


def generate_unanswerable(llm, state, topic_buckets, n, already_have, seen_questions):
    examples = []
    need = max(0, n - already_have)
    if need == 0:
        return examples
    for _ in range(need * 2):
        if len(examples) >= need:
            break
        chunk, topic = pick_weighted_chunk(topic_buckets)
        question = _generate_question_with_retry(llm, state, _UNANSWERABLE_SYSTEM, chunk["text"][:2000], seen_questions)
        if question is None:
            continue
        ex = {
            "id": f"ua-{uuid.uuid4().hex[:8]}", "category": "unanswerable",
            "topic": topic, "difficulty": "simple",
            "question": question, "oracle_source": None, "oracle_page": None,
            "oracle_text": None, "support_status": "unsupported",
            "note": f"Generated near (but not answered by): {chunk['source_file']}",
        }
        _append_example(OUTPUT_PATH, ex)
        examples.append(ex)
    return examples


# ── Type 3: partially supported ──────────────────────────────────────────
_PARTIAL_SYSTEM = (
    "You are given two unrelated document chunks (A and B). Write ONE "
    "simple, realistic farmer-style question that asks for TWO things: "
    "something chunk A actually answers, AND something plausible-"
    "sounding that NEITHER chunk answers (e.g. combine a real farming "
    "topic from A with a request for today's price or this week's "
    "forecast). Keep it short and natural — like 'What fertilizer should "
    "I use for wheat, and what will today's wheat price be?' — NOT "
    "academic or statistical. Output ONLY the question."
)


def generate_partially_supported(llm, state, topic_buckets, n, already_have, seen_questions):
    examples = []
    need = max(0, n - already_have)
    if need == 0:
        return examples
    for _ in range(need):
        a, b, topic = pick_weighted_pair(topic_buckets)
        user_text = f"Chunk A:\n{a['text'][:1200]}\n\nChunk B:\n{b['text'][:1200]}"
        question = _generate_question_with_retry(llm, state, _PARTIAL_SYSTEM, user_text, seen_questions)
        if question is None:
            continue
        ex = {
            "id": f"ps-{uuid.uuid4().hex[:8]}", "category": "partially_supported",
            "topic": topic, "difficulty": "moderate",
            "question": question, "oracle_source": a["source_file"],
            "oracle_page": a["page_num"], "oracle_text": a["text"][:2000],
            "support_status": "partially_supported",
        }
        _append_example(OUTPUT_PATH, ex)
        examples.append(ex)
    return examples


def compute_targets(args) -> tuple:
    if args.answerable is not None or args.unanswerable is not None or args.partial is not None:
        return (args.answerable or 0, args.unanswerable or 0, args.partial or 0)
    if args.total is None:
        return DEFAULT_RATIO
    scale = args.total / sum(DEFAULT_RATIO)
    return tuple(max(1, round(r * scale)) for r in DEFAULT_RATIO)


def parse_args():
    p = argparse.ArgumentParser(description="Build the frozen AgriBot evaluation set.")
    p.add_argument("--total", type=int, default=None)
    p.add_argument("--answerable", type=int, default=None)
    p.add_argument("--unanswerable", type=int, default=None)
    p.add_argument("--partial", type=int, default=None)
    p.add_argument("--max-api-calls", type=int, default=DEFAULT_MAX_API_CALLS)
    return p.parse_args()


def main():
    args = parse_args()
    n_answerable, n_unanswerable, n_partial = compute_targets(args)
    total_target = n_answerable + n_unanswerable + n_partial

    api_key = os.environ.get("GROQ_API_KEY", "")
    model_name = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")

    existing = _load_existing(OUTPUT_PATH)
    counts = {"fully_answerable": 0, "unanswerable": 0, "partially_supported": 0}
    for ex in existing:
        counts[ex["category"]] = counts.get(ex["category"], 0) + 1
    completed_before = sum(counts.values())

    if existing and completed_before >= total_target:
        raise RuntimeError(
            f"{OUTPUT_PATH} already has {completed_before} examples, which is >= "
            f"this run's target of {total_target}. This usually means you're running "
            f"a SMALLER --total against a file that already holds progress from a "
            f"LARGER, still-in-progress run — the file only tracks one target at a "
            f"time. Either:\n"
            f"  (a) continue the larger run instead (rerun with the SAME --total you "
            f"used before, or no --total flag at all for the default 40), or\n"
            f"  (b) if you really want an isolated smaller test, delete this file "
            f"first, or point --total at a different, separate output by editing "
            f"OUTPUT_PATH."
        )

    print("=" * 50)
    print("EVALUATION GENERATION")
    print("=" * 50)
    print(f"Model: {model_name}")
    print(f"API key: {mask_key(api_key)}")
    print(f"Target questions: {total_target} ({n_answerable} answerable / {n_unanswerable} unanswerable / {n_partial} partial)")
    print(f"Max API calls this run: {args.max_api_calls}")
    if existing:
        print(f"Resuming: {completed_before} already completed from a previous run — {counts}")
    print("=" * 50)

    llm = get_llm_client()
    state = RunState(args.max_api_calls)
    stop_reason = None

    try:
        chunks = load_real_chunks()
        print("[BUILD_EVAL] Tagging chunks by topic for weighted sampling...")
        topic_buckets = tag_chunks_by_topic(chunks)
        # BUGFIX: a real run produced verbatim-duplicate questions ("What
        # are the signs of salinity stress in crops?" generated twice from
        # two different chunk draws on the same topic). Seed the dedup set
        # from every question already in the file (including ones from a
        # previous, resumed run) so a rerun can't reintroduce a duplicate
        # of something already accepted.
        seen_questions = {_normalize_for_dedup(ex["question"]) for ex in existing}
        fully = generate_fully_supported(llm, state, topic_buckets, n_answerable, counts["fully_answerable"], seen_questions)
        unans = generate_unanswerable(llm, state, topic_buckets, n_unanswerable, counts["unanswerable"], seen_questions)
        partial = generate_partially_supported(llm, state, topic_buckets, n_partial, counts["partially_supported"], seen_questions)
        completed_after = completed_before + len(fully) + len(unans) + len(partial)
        stop_reason = "TARGET REACHED" if completed_after >= total_target else "GENERATION LOOP FINISHED (some chunks skipped)"
    except QuotaStop as e:
        stop_reason = f"SAFELY STOPPED — {e.reason}"

    final = _load_existing(OUTPUT_PATH)
    final_counts = {"fully_answerable": 0, "unanswerable": 0, "partially_supported": 0}
    topic_counts = {}
    for ex in final:
        final_counts[ex["category"]] = final_counts.get(ex["category"], 0) + 1
        t = ex.get("topic", "unknown")
        topic_counts[t] = topic_counts.get(t, 0) + 1

    print("\n" + "=" * 50)
    print("EVALUATION GENERATION — RUN SUMMARY")
    print("=" * 50)
    print(f"Model: {model_name}")
    print(f"API key: {mask_key(api_key)}")
    print(f"Target questions: {total_target}")
    print(f"Completed (total in file): {len(final)}")
    print(f"API calls used this run: {state.api_calls_made}")
    print(f"Failed calls: {state.failed_calls}")
    print(f"Retry count: {state.retry_count}")
    print(f"Rejected — incomplete/empty/duplicate generation: {state.rejected_incomplete}")
    print(f"Rejected — verification said chunk didn't support it: {state.rejected_verification}")
    print(f"Categories completed: {final_counts}")
    print(f"Topic distribution so far: {topic_counts}")
    print(f"Status: {stop_reason}")
    print(f"Output: {OUTPUT_PATH}")
    print("=" * 50)


if __name__ == "__main__":
    main()
