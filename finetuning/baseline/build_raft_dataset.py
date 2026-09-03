"""
finetuning/baseline/build_raft_dataset.py

Builds a SEPARATE RAFT/SFT training dataset from your ChromaDB collection
— structurally identical in approach to build_eval_set.py (topic-weighted
sampling, budgeted/quota-safe LLM calls, resumable JSONL) but produces
TRAINING examples, not evaluation questions.

CONTAMINATION GUARD (the whole point of this being a separate script):
Before generating anything, this script loads finetuning/data/eval_set_v1.jsonl
and builds an exclusion set from it — every (oracle_source, oracle_page) pair
and every normalized question text already used as an EVAL question. Any
chunk or generated question matching that exclusion set is skipped. This is
checked on EVERY run, not just once, so re-running after eval_set_v1.jsonl
gains more questions (15-40) automatically extends the exclusion set too.

Each accepted example has this shape (Track 7 / RAFT format):
{
  "id": "raft-xxxxxxxx",
  "category": "raft_grounded" | "raft_abstain",
  "topic": "...",
  "question": "...",
  "oracle_source": "...", "oracle_page": N, "oracle_text": "...",
  "distractor_sources": [...], "distractor_texts": [...],
  "answer": "...",
  "citation": {"doc_id": "...", "span_hint": "first ~200 chars of oracle_text"}
}

Distractors are stored up to MAX_DISTRACTORS (4) per example. Ratio
ablations (1:0 / 1:2 / 1:4 from the brief) are done at TRAINING time by
slicing distractor_texts[:k] — this script only needs to run once to
support all three ablations, rather than building three separate files.

Usage (same conventions as build_eval_set.py):
    python build_raft_dataset.py --total 5                 # smoke test
    python build_raft_dataset.py                            # default: 200 examples
    python build_raft_dataset.py --total 200 --max-api-calls 150
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

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import vector_store                        # noqa: E402 — existing module, unmodified
from rag_pipeline import get_llm_client     # noqa: E402 — existing LLM client factory, unmodified

EVAL_SET_PATH = Path(__file__).resolve().parent.parent / "data" / "eval_set_v1.jsonl"
OUTPUT_PATH   = Path(__file__).resolve().parent.parent / "data" / "raft_train_set.jsonl"

DEFAULT_TOTAL = 200                 # training set is much bigger than the 40-question eval set
DEFAULT_ABSTAIN_PCT = 0.20          # 20% abstention examples, matching the brief's suggested composition
DEFAULT_MAX_API_CALLS = 150
MAX_DISTRACTORS = 4
RANDOM_SEED = 43                    # DIFFERENT seed from build_eval_set.py (42) on purpose —
                                     # using the same seed would let identical chunk draws recur
random.seed(RANDOM_SEED)

# ── Same topic buckets as build_eval_set.py, kept in sync intentionally ──
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


def mask_key(key: str) -> str:
    if not key or len(key) < 4:
        return "(not set)"
    return "*" * 8 + key[-4:]


def tag_chunks_by_topic(chunks):
    buckets = {topic: [] for topic in TOPIC_TARGET_PCT}
    buckets["general"] = chunks
    for chunk in chunks:
        low = chunk["text"].lower()
        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(kw in low for kw in keywords):
                buckets[topic].append(chunk)
    for topic in TOPIC_KEYWORDS:
        print(f"[BUILD_RAFT]   topic '{topic}': {len(buckets[topic])} matching chunks")
    return buckets


def pick_weighted_chunk(topic_buckets, exclude_keys, rng=random, max_tries=25):
    """Same weighted draw as build_eval_set.py, but skips anything whose
    (source_file, page_num) is in the eval-set exclusion set."""
    topics = list(TOPIC_TARGET_PCT.keys())
    weights = [TOPIC_TARGET_PCT[t] for t in topics]
    for _ in range(max_tries):
        topic = rng.choices(topics, weights=weights, k=1)[0]
        pool = topic_buckets[topic] or topic_buckets["general"]
        chunk = rng.choice(pool)
        key = (chunk["source_file"], chunk["page_num"])
        if key not in exclude_keys:
            return chunk, topic
    return None, None  # gave up — every draw in max_tries hit an excluded chunk


def pick_distractors(topic_buckets, oracle_topic, exclude_keys, k, rng=random):
    """Draws k distractor chunks from DIFFERENT topics than the oracle,
    so they're genuine distractors rather than more of the same evidence."""
    other_topics = [t for t in TOPIC_TARGET_PCT if t != oracle_topic]
    distractors = []
    tries = 0
    while len(distractors) < k and tries < k * 10:
        tries += 1
        topic = rng.choice(other_topics)
        pool = topic_buckets[topic] or topic_buckets["general"]
        chunk = rng.choice(pool)
        key = (chunk["source_file"], chunk["page_num"])
        if key in exclude_keys or chunk in distractors:
            continue
        distractors.append(chunk)
    return distractors


# ── Budgeted, safety-first LLM calling — IDENTICAL pattern to build_eval_set.py ──
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
        self.rejected_generation = 0


def call_llm_budgeted(llm, state, system_prompt, user_text, max_tokens=512, temperature=0.3):
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
                print(f"[BUILD_RAFT]   temporary-looking rate limit — waiting {wait_s}s "
                      f"(retry {attempt + 1}/{max_temp_retries})...")
                time.sleep(wait_s)
                continue
            raise QuotaStop(f"Repeated failures on what looked like a temporary rate limit. Raw: {e}")


def load_real_chunks():
    collection = vector_store._get_collection()
    count = collection.count()
    if count == 0:
        raise RuntimeError("Your ChromaDB collection is empty — ingest documents first.")
    results = collection.get(include=["documents", "metadatas"])
    chunks = []
    for text, meta in zip(results["documents"], results["metadatas"]):
        if text and len(text.strip()) > 200:
            chunks.append({
                "text": text,
                "source_file": (meta or {}).get("source_file", "unknown"),
                "page_num": (meta or {}).get("page_num", 0),
            })
    print(f"[BUILD_RAFT] {len(chunks)} usable chunks after filtering short/empty ones.")
    return chunks


def _normalize_for_dedup(question: str) -> str:
    q = question.strip().lower().rstrip("?").strip()
    q = re.sub(r"[^\w\s]", "", q)
    return re.sub(r"\s+", " ", q)


def load_eval_exclusion_set():
    """The contamination guard. Returns (excluded_chunk_keys, excluded_questions)
    built from whatever is CURRENTLY in eval_set_v1.jsonl — so re-running this
    script after the eval set grows (14 -> 40) automatically excludes more."""
    if not EVAL_SET_PATH.exists():
        print(f"[BUILD_RAFT]   WARNING: {EVAL_SET_PATH} not found — nothing to exclude. "
              f"Are you sure the eval set exists?")
        return set(), set()
    excluded_keys, excluded_questions = set(), set()
    with open(EVAL_SET_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            ex = json.loads(line)
            if ex.get("oracle_source") is not None:
                excluded_keys.add((ex["oracle_source"], ex.get("oracle_page")))
            excluded_questions.add(_normalize_for_dedup(ex["question"]))
    print(f"[BUILD_RAFT]   Contamination guard: excluding {len(excluded_keys)} eval-set source "
          f"chunk(s) and {len(excluded_questions)} eval-set question(s).")
    return excluded_keys, excluded_questions


# ── Grounded (answerable) RAFT examples ──────────────────────────────────
_QUESTION_SYSTEM = """You write ONE simple, realistic farmer-style question that this exact document chunk answers.
Keep it short and natural, like a farmer would type it — NOT academic or statistical.
Output ONLY the question, one sentence, ending in a question mark."""

_ANSWER_SYSTEM = """Answer the question using ONLY the information in the provided chunk. Be concise
(2-4 sentences). Do not add information not present in the chunk. Do not mention "the document"
or "the chunk" — answer directly as if speaking to the farmer who asked."""

_ABSTAIN_QUESTION_SYSTEM = """You write ONE simple, realistic farmer-style agriculture question that CANNOT
be answered from this document chunk, but is clearly on-topic for practical farming (e.g. asking for
today's exact price or this week's specific weather). Output ONLY the question."""

_ABSTAIN_ANSWERS = [
    "I don't have enough information in the provided context to answer that.",
    "That's not something I can answer from the material I have available — you may want to check a local source for current figures.",
    "I don't have that specific information on hand right now.",
]


def generate_grounded_examples(llm, state, topic_buckets, excluded_keys, excluded_questions, n, distractors_k, rng=random):
    examples = []
    attempts_budget = n * 3
    seen_questions = set(excluded_questions)
    for _ in range(attempts_budget):
        if len(examples) >= n:
            break
        chunk, topic = pick_weighted_chunk(topic_buckets, excluded_keys, rng)
        if chunk is None:
            print("[BUILD_RAFT]   couldn't find a non-excluded chunk after several tries — skipping this draw")
            continue
        question, _ = call_llm_budgeted(llm, state, _QUESTION_SYSTEM, chunk["text"][:2000])
        question = question.strip().strip('"')
        norm = _normalize_for_dedup(question)
        if len(question) < 15 or not question.endswith("?") or norm in seen_questions:
            state.rejected_generation += 1
            continue
        seen_questions.add(norm)
        answer, _ = call_llm_budgeted(llm, state, _ANSWER_SYSTEM,
                                       f"Question: {question}\n\nChunk:\n{chunk['text'][:2000]}")
        distractors = pick_distractors(topic_buckets, topic, excluded_keys, distractors_k, rng)
        ex = {
            "id": f"raft-{uuid.uuid4().hex[:8]}", "category": "raft_grounded", "topic": topic,
            "question": question,
            "oracle_source": chunk["source_file"], "oracle_page": chunk["page_num"], "oracle_text": chunk["text"][:2000],
            "distractor_sources": [d["source_file"] for d in distractors],
            "distractor_texts": [d["text"][:2000] for d in distractors],
            "answer": answer.strip(),
            "citation": {"doc_id": chunk["source_file"], "span_hint": chunk["text"][:200]},
        }
        _append_example(OUTPUT_PATH, ex)
        examples.append(ex)
    return examples


def generate_abstain_examples(llm, state, topic_buckets, excluded_keys, excluded_questions, n, distractors_k, rng=random):
    examples = []
    seen_questions = set(excluded_questions)
    for _ in range(n * 2):
        if len(examples) >= n:
            break
        chunk, topic = pick_weighted_chunk(topic_buckets, excluded_keys, rng)
        if chunk is None:
            continue
        question, _ = call_llm_budgeted(llm, state, _ABSTAIN_QUESTION_SYSTEM, chunk["text"][:2000])
        question = question.strip().strip('"')
        norm = _normalize_for_dedup(question)
        if len(question) < 15 or not question.endswith("?") or norm in seen_questions:
            state.rejected_generation += 1
            continue
        seen_questions.add(norm)
        distractors = pick_distractors(topic_buckets, topic, excluded_keys, distractors_k, rng)
        ex = {
            "id": f"raft-{uuid.uuid4().hex[:8]}", "category": "raft_abstain", "topic": topic,
            "question": question,
            "oracle_source": None, "oracle_page": None, "oracle_text": None,
            "distractor_sources": [chunk["source_file"]] + [d["source_file"] for d in distractors],
            "distractor_texts": [chunk["text"][:2000]] + [d["text"][:2000] for d in distractors],
            "answer": rng.choice(_ABSTAIN_ANSWERS),
            "citation": None,
        }
        _append_example(OUTPUT_PATH, ex)
        examples.append(ex)
    return examples


def _load_existing(path):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _append_example(path, ex):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")
        f.flush()


def parse_args():
    p = argparse.ArgumentParser(description="Build the RAFT/SFT training dataset (separate from the eval set).")
    p.add_argument("--total", type=int, default=DEFAULT_TOTAL)
    p.add_argument("--abstain-pct", type=float, default=DEFAULT_ABSTAIN_PCT)
    p.add_argument("--distractors", type=int, default=2, help="Distractors stored per example (max 4).")
    p.add_argument("--max-api-calls", type=int, default=DEFAULT_MAX_API_CALLS)
    return p.parse_args()


def main():
    args = parse_args()
    distractors_k = min(args.distractors, MAX_DISTRACTORS)
    n_abstain = round(args.total * args.abstain_pct)
    n_grounded = args.total - n_abstain

    api_key = os.environ.get("GROQ_API_KEY", "")
    model_name = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")

    existing = _load_existing(OUTPUT_PATH)
    completed_before = len(existing)
    grounded_before = sum(1 for e in existing if e["category"] == "raft_grounded")
    abstain_before = sum(1 for e in existing if e["category"] == "raft_abstain")

    print("=" * 50)
    print("RAFT TRAINING SET GENERATION")
    print("=" * 50)
    print(f"Model: {model_name}")
    print(f"API key: {mask_key(api_key)}")
    print(f"Target: {args.total} ({n_grounded} grounded / {n_abstain} abstain), {distractors_k} distractors each")
    print(f"Max API calls this run: {args.max_api_calls}")
    if existing:
        print(f"Resuming: {completed_before} already in file ({grounded_before} grounded / {abstain_before} abstain)")
    print("=" * 50)

    llm = get_llm_client()
    state = RunState(args.max_api_calls)
    stop_reason = None

    try:
        chunks = load_real_chunks()
        print("[BUILD_RAFT] Tagging chunks by topic...")
        topic_buckets = tag_chunks_by_topic(chunks)
        excluded_keys, excluded_questions = load_eval_exclusion_set()
        grounded = generate_grounded_examples(llm, state, topic_buckets, excluded_keys, excluded_questions,
                                               max(0, n_grounded - grounded_before), distractors_k)
        abstain = generate_abstain_examples(llm, state, topic_buckets, excluded_keys, excluded_questions,
                                             max(0, n_abstain - abstain_before), distractors_k)
        stop_reason = "TARGET REACHED" if (completed_before + len(grounded) + len(abstain)) >= args.total else "GENERATION LOOP FINISHED"
    except QuotaStop as e:
        stop_reason = f"SAFELY STOPPED — {e.reason}"

    final = _load_existing(OUTPUT_PATH)
    print("\n" + "=" * 50)
    print("RAFT TRAINING SET — RUN SUMMARY")
    print("=" * 50)
    print(f"Completed (total in file): {len(final)} / {args.total}")
    print(f"  grounded: {sum(1 for e in final if e['category'] == 'raft_grounded')}")
    print(f"  abstain:  {sum(1 for e in final if e['category'] == 'raft_abstain')}")
    print(f"API calls used this run: {state.api_calls_made}")
    print(f"Rejected generations: {state.rejected_generation}")
    print(f"Status: {stop_reason}")
    print(f"Output: {OUTPUT_PATH}")
    print("=" * 50)


if __name__ == "__main__":
    main()
