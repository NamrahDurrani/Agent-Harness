"""
finetuning/baseline/run_baseline.py

Phase 3 (master prompt Sections 20/41): run the CURRENT, unmodified
AgriBot pipeline against the frozen evaluation set and save every raw
prediction. This is B0 — never overwritten once complete.

Uses AgenticRAGPipeline.run() exactly as your FastAPI app already calls
it — no new retrieval/generation code.

Same API-safety policy as build_eval_set.py:
  - No automatic model fallback, no key rotation — a genuine daily quota
    exhaustion stops the run cleanly and reports it.
  - Resumable: already-completed questions (no error recorded) are
    skipped on a rerun.
  - Note: we can't count AgriBot's INTERNAL API calls per question here
    without modifying rag_pipeline.py (each question may cost several —
    query rewrite, routing, retrieval evaluation, generation, etc.), so
    the safety limit here is expressed as a max NUMBER OF QUESTIONS
    processed per run, not a raw API-call count. Said plainly in the
    summary so it isn't confused with build_eval_set.py's exact call count.

REWRITE — FIX: Groq returns the identical "...usage limit..." phrase for
BOTH a short rolling-window rate limit (clears in minutes on its own) AND
a genuine full daily quota exhaustion (needs a real ~24h reset). A real
run hit this twice in one session — once with "try again in about 19
minute(s)", once with "about 2 minute(s)" — and both were being treated
as a hard daily-quota STOP, even though a short sleep would very likely
have let the run continue. The `_WAIT_RE` regex to extract that minute
count already existed in this file but was never actually used in
run_one() — that's the bug. Fixed by: extracting the wait hint, and if
it's short (<= --max-wait-minutes, default 30) and we haven't exceeded
--max-wait-retries (default 3) for THIS question, sleeping that long
(plus a small buffer) and retrying the SAME question in place, instead
of unwinding the whole run. Only a missing wait hint, an unreasonably
long one, or repeated short waits in a row now raises the real
QuotaStop. This intentionally avoids the alternative of "just rerun the
whole script by hand the moment it stops" — a blind immediate rerun
walks straight back into a quota that likely hasn't reset yet, and
re-pays each question's full internal pipeline cost (rewriter, retrieval,
evaluator retries, web fallback, verification) for nothing.

Usage:
    python run_baseline.py                          # process all remaining questions
    python run_baseline.py --max-questions 10        # process at most 10 this run
    python run_baseline.py --max-wait-minutes 15     # only auto-sleep through waits <= 15 min (default 30)
    python run_baseline.py --max-wait-retries 2       # give up sleeping after 2 short-wait retries per question (default 3)
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from rag_pipeline import AgenticRAGPipeline   # noqa: E402 — your existing pipeline class, unmodified

EVAL_SET_PATH = Path(__file__).resolve().parent.parent / "data" / "eval_set_v1.jsonl"
OUTPUT_PATH   = Path(__file__).resolve().parent.parent / "results" / "baseline_B0_results.jsonl"

_WAIT_RE             = re.compile(r"try again in about (\d+) minute", re.IGNORECASE)
_DAILY_QUOTA_MARKERS = ("usage limit", "daily limit", "daily quota", "insufficient quota")
_AUTH_MARKERS        = ("authentication", "invalid api key", "unauthorized", "401")


def mask_key(key: str) -> str:
    if not key or len(key) < 4:
        return "(not set)"
    return "*" * 8 + key[-4:]


class QuotaStop(Exception):
    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


def _load_existing_results(path):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _append_result(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()


def run_one(pipeline, item, max_wait_minutes=30, max_wait_retries=3):
    """One question through the real pipeline.

    Distinguishes:
      - a SHORT, transient Groq rate-limit window (the message has an
        extractable 'try again in about N minute(s)' hint, N is under
        max_wait_minutes, and we haven't already retried this same
        question max_wait_retries times) — sleeps it out and retries
        THIS question in place, rather than unwinding the whole run;
      - a genuine daily/account quota exhaustion (no wait hint, a long
        one, or repeated short waits that keep recurring) — raises
        QuotaStop, which unwinds the whole run cleanly, as before.
    Any OTHER error is recorded against this one question only; the
    run continues to the next question.
    """
    t0 = time.time()
    attempts = 0
    while True:
        attempts += 1
        try:
            result = pipeline.run(session_id=f"baseline-eval-{item['id']}", user_query=item["question"])
            return {
                "eval_id": item["id"], "category": item["category"], "question": item["question"],
                "answer": result.answer, "sources": result.sources, "used_rag": result.used_rag,
                "retry_count": result.retry_count, "source_type": result.source_type,
                "latency_s": round(time.time() - t0, 2), "error": None,
            }
        except Exception as e:
            msg = str(e).lower()
            if any(m in msg for m in _AUTH_MARKERS):
                raise QuotaStop(f"Authentication error — check your GROQ_API_KEY. Raw: {e}")

            if any(m in msg for m in _DAILY_QUOTA_MARKERS):
                wait_match = _WAIT_RE.search(msg)
                wait_minutes = int(wait_match.group(1)) if wait_match else None
                if wait_minutes is not None and wait_minutes <= max_wait_minutes and attempts <= max_wait_retries:
                    wait_s = wait_minutes * 60 + 10  # small buffer past the stated window
                    print(f"[RUN_BASELINE]   short rate-limit window ({wait_minutes} min) — "
                          f"sleeping {wait_s}s and retrying THIS question "
                          f"(attempt {attempts}/{max_wait_retries})...")
                    time.sleep(wait_s)
                    continue
                raise QuotaStop(
                    "Daily/account quota exhausted"
                    + (f" (wait hint was {wait_minutes} min — exceeds the {max_wait_minutes}-min "
                       f"short-limit cap, or this question already used its {max_wait_retries} "
                       f"wait-retries)" if wait_minutes is not None else " (no short-wait hint in message)")
                    + f". Raw: {e}"
                )
            # Anything else (a genuinely one-off failure on this question):
            # record it and keep going, matching the eval-run's need to see
            # every question's real outcome rather than stopping on the
            # first isolated error.
            return {
                "eval_id": item["id"], "category": item["category"], "question": item["question"],
                "answer": None, "sources": [], "used_rag": False, "retry_count": 0,
                "source_type": None, "latency_s": round(time.time() - t0, 2), "error": str(e),
            }


def parse_args():
    p = argparse.ArgumentParser(description="Run the frozen eval set through the current AgriBot baseline.")
    p.add_argument("--max-questions", type=int, default=None,
                    help="Stop after processing at most this many NEW questions this run (default: all remaining).")
    p.add_argument("--max-wait-minutes", type=int, default=30,
                    help="Auto-sleep-and-retry a question only if Groq's wait hint is at or under this many "
                         "minutes (default 30). Anything longer, or no hint at all, is treated as a real "
                         "daily quota exhaustion and stops the run.")
    p.add_argument("--max-wait-retries", type=int, default=3,
                    help="Give up sleeping and raise a real QuotaStop after this many short-wait retries "
                         "on the SAME question (default 3) — protects against a slow drip of short waits "
                         "that never actually clears.")
    return p.parse_args()


def main():
    args = parse_args()

    if not EVAL_SET_PATH.exists():
        raise RuntimeError(f"{EVAL_SET_PATH} not found — run build_eval_set.py first.")

    with open(EVAL_SET_PATH, "r", encoding="utf-8") as f:
        eval_items = [json.loads(line) for line in f if line.strip()]

    existing = _load_existing_results(OUTPUT_PATH)
    done_ids = {r["eval_id"] for r in existing if r["error"] is None}  # only CLEAN successes count as done
    remaining = [item for item in eval_items if item["id"] not in done_ids]

    if not remaining:
        raise RuntimeError(
            f"{OUTPUT_PATH} already has a clean result for every question in {EVAL_SET_PATH}. "
            f"B0 looks COMPLETE — delete the file manually first if you really intend to rerun it."
        )

    api_key = os.environ.get("GROQ_API_KEY", "")
    model_name = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")

    print("=" * 50)
    print("BASELINE EVALUATION (B0)")
    print("=" * 50)
    print(f"Model: {model_name}")
    print(f"API key: {mask_key(api_key)}")
    print(f"Total questions in eval set: {len(eval_items)}")
    print(f"Already completed (clean): {len(done_ids)}")
    print(f"Remaining this run: {len(remaining)}"
          + (f" (capped at {args.max_questions})" if args.max_questions else ""))
    print(f"Short-wait auto-retry: <= {args.max_wait_minutes} min, up to {args.max_wait_retries} retries/question")
    print("Note: this script limits QUESTIONS per run, not raw API calls — "
          "each question may cost several internal AgriBot calls "
          "(rewrite/route/retrieve/generate) that aren't separately counted here.")
    print("=" * 50)

    pipeline = AgenticRAGPipeline()
    processed = 0
    stop_reason = "ALL REMAINING QUESTIONS PROCESSED"

    for item in remaining:
        if args.max_questions and processed >= args.max_questions:
            stop_reason = f"--max-questions limit reached ({args.max_questions})"
            break
        print(f"[RUN_BASELINE] ({processed + 1}/{len(remaining)}) {item['question'][:70]!r}")
        try:
            record = run_one(pipeline, item,
                              max_wait_minutes=args.max_wait_minutes,
                              max_wait_retries=args.max_wait_retries)
        except QuotaStop as e:
            stop_reason = f"SAFELY STOPPED — {e.reason}"
            break
        _append_result(OUTPUT_PATH, record)
        if record["error"]:
            print(f"[RUN_BASELINE]   error recorded for this question: {record['error']}")
        processed += 1

    final = _load_existing_results(OUTPUT_PATH)
    final_clean = sum(1 for r in final if r["error"] is None)

    print("\n" + "=" * 50)
    print("BASELINE EVALUATION — RUN SUMMARY")
    print("=" * 50)
    print(f"Model: {model_name}")
    print(f"API key: {mask_key(api_key)}")
    print(f"Total questions in eval set: {len(eval_items)}")
    print(f"Processed this run: {processed}")
    print(f"Clean results (total in file): {final_clean}/{len(eval_items)}")
    print(f"Status: {stop_reason}")
    print(f"Output: {OUTPUT_PATH}")
    print("=" * 50)


if __name__ == "__main__":
    main()