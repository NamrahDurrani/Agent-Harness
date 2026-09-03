"""
finetuning/baseline/clean_eval_set.py

Purely local cleanup — makes ZERO LLM API calls. Removes exact/near-
duplicate questions from eval_set_v1.jsonl (same detection logic as
build_eval_set.py's dedup fix) and, optionally, any question containing
a given substring (for manually flagging clearly off-topic ones, like
the WHO Child Growth Standards question found in a real run).

Keeps eval_set_v1.jsonl and baseline_B0_results.jsonl in sync: any
eval_id removed from the eval set also has its corresponding row removed
from the baseline results file, if present, so the two files never
reference mismatched questions.

This does NOT backfill removed questions. A smaller-than-40 final eval
set is completely fine — quality over question count, per the project's
own stated priority. If you DO want to backfill later (spending more
quota), just rerun build_eval_set.py after this — it resumes and
generates replacements for whatever's missing.

Usage:
    python clean_eval_set.py --dry-run                            # preview only, writes nothing
    python clean_eval_set.py                                      # dedup only
    python clean_eval_set.py --remove-containing "wasting in children"
    python clean_eval_set.py --remove-containing "Daycent model" --remove-containing "wasting in children"
"""
import argparse
import json
import re
from pathlib import Path

EVAL_SET_PATH = Path(__file__).resolve().parent.parent / "data" / "eval_set_v1.jsonl"
RESULTS_PATH  = Path(__file__).resolve().parent.parent / "results" / "baseline_B0_results.jsonl"


def _normalize_for_dedup(question: str) -> str:
    q = question.strip().lower().rstrip("?").strip()
    q = re.sub(r"[^\w\s]", "", q)
    return re.sub(r"\s+", " ", q)


def _is_near_duplicate(norm_question: str, seen_normalized: set, threshold: float = 0.7) -> bool:
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


def load_jsonl(path):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    p = argparse.ArgumentParser(description="Locally clean eval_set_v1.jsonl — no API calls.")
    p.add_argument("--remove-containing", action="append", default=[],
                    help="Substring (case-insensitive) — any question containing it is removed. Repeatable.")
    p.add_argument("--redo-empty-answers", action="store_true",
                    help="Also remove baseline result rows with a null/empty answer (e.g. ones that hit "
                         "a non-functional Tavily fallback before an API key was configured) — even "
                         "though error=None, so they get properly reprocessed on the next baseline run "
                         "instead of being treated as already complete.")
    p.add_argument("--dry-run", action="store_true", help="Preview what would be removed, write nothing.")
    args = p.parse_args()

    eval_items = load_jsonl(EVAL_SET_PATH)
    if not eval_items:
        print(f"[CLEAN] {EVAL_SET_PATH} not found or empty — nothing to do.")
        return

    kept = []
    removed_ids = []
    seen_normalized = set()

    for item in eval_items:
        q = item["question"]
        reason = None

        if any(kw.lower() in q.lower() for kw in args.remove_containing):
            reason = "matched --remove-containing filter"
        else:
            norm = _normalize_for_dedup(q)
            if norm in seen_normalized:
                reason = "exact duplicate"
            elif _is_near_duplicate(norm, seen_normalized):
                reason = "near-duplicate"

        if reason:
            print(f"[CLEAN] REMOVE ({reason}): {q!r}")
            removed_ids.append(item["id"])
        else:
            seen_normalized.add(_normalize_for_dedup(q))
            kept.append(item)

    print(f"\n[CLEAN] {len(eval_items)} -> {len(kept)} questions ({len(removed_ids)} removed).")

    results = load_jsonl(RESULTS_PATH)
    kept_results = [r for r in results if r["eval_id"] not in removed_ids]
    orphaned = len(results) - len(kept_results)
    if orphaned:
        print(f"[CLEAN] Also removing {orphaned} now-orphaned row(s) from baseline_B0_results.jsonl "
              f"(results for questions no longer in the eval set).")

    if args.redo_empty_answers:
        before = len(kept_results)
        empty_ids = [r["eval_id"] for r in kept_results if r["error"] is None and not r.get("answer")]
        kept_results = [r for r in kept_results if r["eval_id"] not in empty_ids]
        if empty_ids:
            print(f"[CLEAN] Removing {len(empty_ids)} result row(s) with a null/empty answer "
                  f"(error=None, but no real answer — e.g. a Tavily fallback that returned nothing) "
                  f"so they get reprocessed: {empty_ids}")

    if args.dry_run:
        print("[CLEAN] --dry-run set — nothing written.")
        return

    write_jsonl(EVAL_SET_PATH, kept)
    if results:
        write_jsonl(RESULTS_PATH, kept_results)
    print(f"[CLEAN] Wrote {len(kept)} questions to {EVAL_SET_PATH}"
          + (f" and {len(kept_results)} results to {RESULTS_PATH}" if results else ""))


if __name__ == "__main__":
    main()
