"""
finetuning/scripts/generate_eval_v2.py

Phase 1a of the v2 upgrade. Generates eval_set_v2_100.jsonl — 100 frozen
evaluation questions (target 50 fully_supported / 25 partially_supported /
25 unanswerable) — WITHOUT touching eval_set_v1_40.jsonl.

Reuses the proven topic-weighted sampling + few-shot style-guided prompt
approach from build_eval_set.py (v1), which fixed a real problem: pure
random chunk sampling over this KB's broad, heterogeneous FAO reports
produced academic/statistical questions instead of farmer-style ones.
Same fix applied here, plus the topics your v2 spec explicitly asks for
(seeds, livestock, climate/weather, post-harvest) added to the keyword
buckets — corpus permitting; unmatched buckets fall back to 'general'
rather than being forced.

NEW in v2 (didn't exist in v1):
  - Richer per-item schema: source_document, source_chunk, source_span,
    topic, language — not just oracle_source/oracle_page/oracle_text.
  - Response caching: every raw LLM response is saved to a cache file
    keyed by a hash of (prompt, chunk) BEFORE being used, so a crash or
    quota stop mid-run never re-spends a call for something already
    generated. This was an explicit gap in v1's build_raft_dataset.py —
    fixed here per your Section 21/22 requirement.
  - `language` field: defaults to "en" for all generated items. This
    script does NOT generate genuine Urdu questions — that would need a
    separate generation prompt/verification step not yet built. Marking
    this here rather than fabricating a language distribution.
  - `source_span`: this script does NOT do sentence-level span
    extraction — source_span is set equal to source_chunk (the full
    retrieved chunk). True span-level extraction would need an
    additional LLM call per item not currently implemented. Documented
    as a known simplification, matching this project's practice of
    flagging gaps rather than silently glossing over them.

Usage (Linux/bash):
    python finetuning/scripts/generate_eval_v2.py --total 5                       # smoke test
    python finetuning/scripts/generate_eval_v2.py                                 # default: 100 (50/25/25)
    python finetuning/scripts/generate_eval_v2.py --max-api-calls 150
"""
import argparse
import hashlib
import json
import os
import random
import re
import sys
import time
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import vector_store                        # noqa: E402 — existing module, unmodified
from rag_pipeline import get_llm_client     # noqa: E402 — existing LLM client factory, unmodified

OUTPUT_PATH = PROJECT_ROOT / "finetuning" / "data" / "eval_set_v2_100.jsonl"
CACHE_PATH  = PROJECT_ROOT / "finetuning" / "data" / ".cache_eval_v2_responses.jsonl"

DEFAULT_RATIO = (50, 25, 25)   # fully_supported, unanswerable, partially_supported — sums to 100
DEFAULT_MAX_API_CALLS = 150
RANDOM_SEED = 142   # distinct from v1's seed (42) — v2 is a separate, independently-seeded experiment

random.seed(RANDOM_SEED)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def mask_key(key: str) -> str:
    if not key or len(key) < 4:
        return "(not set)"
    return "*" * 8 + key[-4:]


# ── Topic buckets — v1's set, PLUS the topics your v2 spec explicitly asks for ──
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
    # NEW for v2 — only populate/use if the corpus actually has matching chunks; see main()'s
    # post-tagging report, which documents actual counts rather than assuming these exist.
    "seeds":            ["seed rate", "seed treatment", "germination", "seed quality", "seed storage"],
    "livestock":        ["livestock", "cattle", "poultry", "dairy", "goat", "buffalo", "fodder", "feed ration"],
    "climate_weather":  ["climate change", "weather forecast", "temperature rise", "heat stress",
                          "monsoon", "drought risk", "climate adapt"],
    "post_harvest":     ["post-harvest", "postharvest", "storage loss", "grain storage", "drying",
                          "spoilage", "cold storage", "food loss"],
}
TOPIC_TARGET_PCT = {
    "crop_cultivation": 0.16, "fertilizer": 0.12, "irrigation": 0.09, "pest": 0.12,
    "disease": 0.09, "soil": 0.08, "varieties": 0.04, "pakistan_local": 0.08,
    "seeds": 0.05, "livestock": 0.05, "climate_weather": 0.04, "post_harvest": 0.04,
    "general": 0.04,
}


def tag_chunks_by_topic(chunks):
    buckets = {topic: [] for topic in TOPIC_TARGET_PCT}
    buckets["general"] = chunks
    for chunk in chunks:
        low = chunk["text"].lower()
        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(kw in low for kw in keywords):
                buckets[topic].append(chunk)
    print("[GEN_EVAL_V2] Topic distribution in corpus (informational — generation still "
          "draws proportionally to TOPIC_TARGET_PCT, falling back to 'general' for empty buckets):")
    for topic in TOPIC_KEYWORDS:
        print(f"[GEN_EVAL_V2]   '{topic}': {len(buckets[topic])} matching chunks"
              + ("  <-- EMPTY, will fall back to 'general'" if not buckets[topic] else ""))
    return buckets


def pick_weighted_chunk(topic_buckets, rng=random):
    topics = list(TOPIC_TARGET_PCT.keys())
    weights = [TOPIC_TARGET_PCT[t] for t in topics]
    topic = rng.choices(topics, weights=weights, k=1)[0]
    pool = topic_buckets[topic] or topic_buckets["general"]
    return rng.choice(pool), topic


def pick_weighted_pair(topic_buckets, rng=random):
    a, topic_a = pick_weighted_chunk(topic_buckets, rng)
    other_topics = [t for t in TOPIC_TARGET_PCT if t != topic_a]
    topic_b = rng.choice(other_topics)
    pool_b = topic_buckets[topic_b] or topic_buckets["general"]
    b = rng.choice(pool_b)
    return a, b, topic_a


# ── Response cache (NEW in v2 — fixes v1's "wasted call on a partial pair" gap) ──
def _cache_key(system_prompt, user_text):
    return hashlib.sha256((system_prompt + "||" + user_text).encode("utf-8")).hexdigest()[:16]


def _load_cache():
    cache = {}
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    cache[rec["key"]] = rec["response"]
    return cache


def _cache_append(key, response):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps({"key": key, "response": response}, ensure_ascii=False) + "\n")
        f.flush()


_response_cache = {}  # populated in main(), passed through call_llm_budgeted


# ── Budgeted, safety-first LLM calling — same wait-hint-aware pattern proven in run_baseline.py ──
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
        self.cache_hits = 0
        self.failed_calls = 0
        self.rejected_verification = 0
        self.rejected_incomplete = 0


def call_llm_budgeted(llm, state, system_prompt, user_text, max_tokens=512, temperature=0.3,
                       max_wait_minutes=30, max_wait_retries=3):
    key = _cache_key(system_prompt, user_text)
    if key in _response_cache:
        state.cache_hits += 1
        return _response_cache[key], {}

    if state.api_calls_made >= state.max_api_calls:
        raise QuotaStop(f"API call safety limit reached ({state.max_api_calls} calls this run).")

    attempts = 0
    while True:
        attempts += 1
        if state.api_calls_made >= state.max_api_calls:
            raise QuotaStop(f"API call safety limit reached ({state.max_api_calls} calls this run).")
        state.api_calls_made += 1
        try:
            text, usage = llm.call(system_prompt, user_text, max_tokens=max_tokens, temperature=temperature)
            _response_cache[key] = text
            _cache_append(key, text)
            return text, usage
        except Exception as e:
            msg = str(e).lower()
            state.failed_calls += 1
            if any(m in msg for m in _AUTH_MARKERS):
                raise QuotaStop(f"Authentication error — check your GROQ_API_KEY. Raw: {e}")
            if any(m in msg for m in _UNAVAILABLE_MARKERS):
                raise QuotaStop(f"Model unavailable. Raw: {e}")
            if any(m in msg for m in _DAILY_QUOTA_MARKERS):
                wait_match = _WAIT_RE.search(msg)
                wait_minutes = int(wait_match.group(1)) if wait_match else None
                if wait_minutes is not None and wait_minutes <= max_wait_minutes and attempts <= max_wait_retries:
                    wait_s = wait_minutes * 60 + 10
                    print(f"[GEN_EVAL_V2]   short rate-limit window ({wait_minutes} min) — "
                          f"sleeping {wait_s}s (attempt {attempts}/{max_wait_retries})...")
                    time.sleep(wait_s)
                    continue
                raise QuotaStop(f"Daily/account quota exhausted. Raw: {e}")
            raise QuotaStop(f"Unrecognized repeated failure. Raw: {e}")


def load_real_chunks():
    collection = vector_store._get_collection()
    count = collection.count()
    if count == 0:
        raise RuntimeError("ChromaDB collection is empty — ingest documents first.")
    print(f"[GEN_EVAL_V2] Collection has {count} chunks.")
    results = collection.get(include=["documents", "metadatas"])
    chunks = []
    for text, meta in zip(results["documents"], results["metadatas"]):
        if text and len(text.strip()) > 200:
            chunks.append({
                "text": text,
                "source_file": (meta or {}).get("source_file", "unknown"),
                "page_num": (meta or {}).get("page_num", 0),
            })
    print(f"[GEN_EVAL_V2] {len(chunks)} usable chunks after filtering short/empty ones.")
    return chunks


_DIFFICULTY_INSTRUCTIONS = {
    "simple": "Write a SHORT, SIMPLE question (like 'What fertilizer is good for wheat?') — "
              "the kind a farmer would type in one breath.",
    "moderate": "Write a moderately specific question — e.g. naming a growth stage or a "
                "particular condition, like 'What fertilizer should I use during the early "
                "growth stage of wheat?' — still natural, not academic.",
    "challenging": "Write a slightly more involved but still realistic question — e.g. "
                   "describing a symptom and asking what to do — still something a real "
                   "farmer would actually type, NOT an academic or statistical question.",
}


def _pick_difficulty(rng=random):
    return rng.choices(["simple", "moderate", "challenging"], weights=[0.60, 0.25, 0.15], k=1)[0]


_QUESTION_GEN_SYSTEM = """You write ONE simple, realistic farmer-style question that this exact document chunk answers.

GOOD examples (this is the style to match):
- What fertilizer is good for wheat?
- When should I plant rice?
- What are common diseases of wheat?
- How much water does cotton need?
- What's the best way to store grain after harvest?
- Which livestock feed improves milk yield?

BAD examples (NEVER write questions like these — academic, statistical, or about unrelated countries/organizations):
- What barriers do women in Tanzania still face in accessing agricultural resources?
- What proportion of low- and middle-income countries increased their PoU between 2011 and 2017?

If the chunk is ONLY about something in the BAD-example style, do not force a question — write the most natural farming-relevant question you can that the chunk still actually supports.

{difficulty_instruction}

Output ONLY the question, nothing else. One complete sentence ending in a question mark."""

_SUPPORT_CHECK_SYSTEM = (
    "Does the following document chunk contain enough information to "
    "fully answer the question? Answer with exactly one word: YES or NO."
)

_UNANSWERABLE_SYSTEM = (
    "You write ONE simple, realistic farmer-style agriculture question "
    "that CANNOT be answered from this document chunk, but is clearly "
    "on-topic for practical farming — e.g. asking for today's exact "
    "price, this week's precise weather, or a specific current number "
    "the chunk does not contain. Keep it short and natural. Output ONLY the question."
)

_PARTIAL_SYSTEM = (
    "You are given two unrelated document chunks (A and B). Write ONE "
    "simple, realistic farmer-style question that asks for TWO things: "
    "something chunk A actually answers, AND something plausible-"
    "sounding that NEITHER chunk answers. Keep it short and natural. "
    "Output ONLY the question."
)


def _looks_complete(question: str) -> bool:
    q = question.strip()
    return len(q) >= 15 and q.endswith("?") and len(q.split()) >= 4


def _normalize_for_dedup(question: str) -> str:
    q = question.strip().lower().rstrip("?").strip()
    q = re.sub(r"[^\w\s]", "", q)
    return re.sub(r"\s+", " ", q)


def _is_near_duplicate(norm_question, seen_normalized, threshold=0.7):
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
        question, _ = call_llm_budgeted(llm, state, system_prompt, user_text, max_tokens=512, temperature=0.3)
        question = question.strip().strip('"')
        if not _looks_complete(question):
            state.rejected_incomplete += 1
            continue
        norm = _normalize_for_dedup(question)
        if norm in seen_questions or _is_near_duplicate(norm, seen_questions):
            state.rejected_incomplete += 1
            continue
        seen_questions.add(norm)
        return question
    return None


def _load_existing(path):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def _append_example(path, example):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(example, ensure_ascii=False) + "\n")
        f.flush()


def generate_fully_supported(llm, state, topic_buckets, n, already_have, seen_questions):
    examples = []
    need = max(0, n - already_have)
    if need == 0:
        return examples
    attempts_budget = need * 3
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
            state.rejected_verification += 1
            continue
        ex = {
            "id": f"v2-fs-{uuid.uuid4().hex[:8]}", "question": question,
            "support_status": "fully_supported",
            "source_document": chunk["source_file"], "source_chunk": chunk["text"][:2000],
            "source_span": chunk["text"][:2000],  # simplification — see file header
            "topic": topic, "language": "en", "difficulty": difficulty,
        }
        _append_example(OUTPUT_PATH, ex)
        examples.append(ex)
    return examples


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
            "id": f"v2-ua-{uuid.uuid4().hex[:8]}", "question": question,
            "support_status": "unanswerable",
            "source_document": None, "source_chunk": None, "source_span": None,
            "topic": topic, "language": "en", "difficulty": "simple",
            "note": f"Generated near (but not answered by): {chunk['source_file']}",
        }
        _append_example(OUTPUT_PATH, ex)
        examples.append(ex)
    return examples


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
            "id": f"v2-ps-{uuid.uuid4().hex[:8]}", "question": question,
            "support_status": "partially_supported",
            "source_document": a["source_file"], "source_chunk": a["text"][:2000],
            "source_span": a["text"][:2000],
            "topic": topic, "language": "en", "difficulty": "moderate",
        }
        _append_example(OUTPUT_PATH, ex)
        examples.append(ex)
    return examples


def compute_targets(args):
    if args.fully is not None or args.unanswerable is not None or args.partial is not None:
        return (args.fully or 0, args.unanswerable or 0, args.partial or 0)
    if args.total is None:
        return DEFAULT_RATIO
    scale = args.total / sum(DEFAULT_RATIO)
    return tuple(max(1, round(r * scale)) for r in DEFAULT_RATIO)


def parse_args():
    p = argparse.ArgumentParser(description="Build eval_set_v2_100.jsonl — never touches eval_set_v1_40.jsonl.")
    p.add_argument("--total", type=int, default=None)
    p.add_argument("--fully", type=int, default=None)
    p.add_argument("--unanswerable", type=int, default=None)
    p.add_argument("--partial", type=int, default=None)
    p.add_argument("--max-api-calls", type=int, default=DEFAULT_MAX_API_CALLS)
    return p.parse_args()


def main():
    global _response_cache
    args = parse_args()
    n_fully, n_unans, n_partial = compute_targets(args)
    total_target = n_fully + n_unans + n_partial

    api_key = os.environ.get("GROQ_API_KEY", "")
    model_name = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")

    existing = _load_existing(OUTPUT_PATH)
    counts = {"fully_supported": 0, "unanswerable": 0, "partially_supported": 0}
    for ex in existing:
        counts[ex["support_status"]] = counts.get(ex["support_status"], 0) + 1
    completed_before = sum(counts.values())

    _response_cache = _load_cache()

    print("=" * 60)
    print("EVAL-100 GENERATION (v2) — NEVER touches eval_set_v1_40.jsonl")
    print("=" * 60)
    print(f"Model: {model_name} | API key: {mask_key(api_key)}")
    print(f"Target: {total_target} ({n_fully} fully / {n_unans} unanswerable / {n_partial} partial)")
    print(f"Max API calls this run: {args.max_api_calls} | Cached responses available: {len(_response_cache)}")
    if existing:
        print(f"Resuming: {completed_before} already completed — {counts}")
    print("=" * 60)

    llm = get_llm_client()
    state = RunState(args.max_api_calls)
    stop_reason = None

    try:
        chunks = load_real_chunks()
        topic_buckets = tag_chunks_by_topic(chunks)
        seen_questions = {_normalize_for_dedup(ex["question"]) for ex in existing}
        fully = generate_fully_supported(llm, state, topic_buckets, n_fully, counts["fully_supported"], seen_questions)
        unans = generate_unanswerable(llm, state, topic_buckets, n_unans, counts["unanswerable"], seen_questions)
        partial = generate_partially_supported(llm, state, topic_buckets, n_partial, counts["partially_supported"], seen_questions)
        completed_after = completed_before + len(fully) + len(unans) + len(partial)
        stop_reason = "TARGET REACHED" if completed_after >= total_target else "GENERATION LOOP FINISHED (some chunks skipped)"
    except QuotaStop as e:
        stop_reason = f"SAFELY STOPPED — {e.reason}"

    final = _load_existing(OUTPUT_PATH)
    final_counts = {}
    topic_counts = {}
    for ex in final:
        final_counts[ex["support_status"]] = final_counts.get(ex["support_status"], 0) + 1
        topic_counts[ex.get("topic", "unknown")] = topic_counts.get(ex.get("topic", "unknown"), 0) + 1

    print("\n" + "=" * 60)
    print("EVAL-100 GENERATION — RUN SUMMARY")
    print("=" * 60)
    print(f"Completed (total in file): {len(final)} / {total_target}")
    print(f"API calls used this run: {state.api_calls_made} | Cache hits: {state.cache_hits}")
    print(f"Rejected — incomplete/duplicate: {state.rejected_incomplete}")
    print(f"Rejected — verification failed: {state.rejected_verification}")
    print(f"Categories: {final_counts}")
    print(f"Topic distribution: {topic_counts}")
    print(f"Status: {stop_reason}")
    print(f"Output: {OUTPUT_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
