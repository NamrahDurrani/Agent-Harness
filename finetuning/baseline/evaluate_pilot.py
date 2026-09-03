"""
finetuning/baseline/evaluate_pilot.py

Pilot comparison: base AgriBot pipeline vs fine-tuned model, on a FROZEN
snapshot of whatever eval questions exist right now (intended for your
current 14). Saves raw answers for both, plus DIAGNOSTIC proxy metrics.

*** IMPORTANT HONESTY NOTE ***
I do not have your actual Track 2 / Track 7 scoring implementation (the
real groundedness/claim-verification code, citation precision/recall
logic, or noise-robustness harness) in front of me — it wasn't shared in
this conversation. Rather than invent a new scoring methodology and label
it "Track 2" / "Track 7" (which you explicitly said not to do), this
script computes clearly-labeled DIAGNOSTIC proxies only:
  - answer_rate: fraction of questions that got a non-empty answer
  - abstained_correctly: for questions tagged "unanswerable" or
    "partially_supported" in the eval set, did the model actually
    hedge/decline vs. confidently answer anyway (simple keyword check —
    NOT a claim verifier)
  - has_citation: whether `result.sources` came back non-empty
These are NOT your thesis's official Track 2/Track 7 metrics. Swap in
your real scoring functions where marked TODO once you share them, or
tell me where they already live in your project and I'll wire them in
directly instead of this proxy.

ALSO NOTE — Track 7 gap: proper Track 7 evaluation needs a noise-
robustness curve (accuracy vs. number of injected distractors: 0, 1, 2,
4, 8). Your current eval_set_v1.jsonl questions don't carry pre-built
distractor sets the way raft_train_set.jsonl does. This script does NOT
fabricate that dimension — it only reports the diagnostics above on the
plain eval questions, once per model. Building a distractor-injected eval
variant is a separate, not-yet-done step (see the progress .md).

Usage:
    python evaluate_pilot.py                      # base model only, if no adapter exists yet
    python evaluate_pilot.py --adapter-dir finetuning/checkpoints/raft_d2_r16_lr0.0001
"""
import argparse
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from rag_pipeline import AgenticRAGPipeline   # noqa: E402 — existing pipeline, unmodified

EVAL_SET_PATH   = PROJECT_ROOT / "finetuning" / "data" / "eval_set_v1.jsonl"
PILOT_SNAPSHOT  = PROJECT_ROOT / "finetuning" / "data" / "eval_pilot_snapshot.jsonl"
RESULTS_DIR     = PROJECT_ROOT / "finetuning" / "results" / "pilot_14"


def load_jsonl(path):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def freeze_pilot_snapshot(n_expected=14):
    """Snapshots the CURRENT contents of eval_set_v1.jsonl into a separate
    pinned file, the FIRST time this is run. On later runs, reuses the
    existing snapshot rather than re-slicing the (still-growing) eval set
    — otherwise the pilot's question basis would silently shift every
    time you add more of the 26 remaining questions."""
    if PILOT_SNAPSHOT.exists():
        snap = load_jsonl(PILOT_SNAPSHOT)
        print(f"[PILOT] Reusing existing frozen snapshot: {len(snap)} questions from {PILOT_SNAPSHOT}")
        return snap
    full = load_jsonl(EVAL_SET_PATH)
    if not full:
        raise RuntimeError(f"{EVAL_SET_PATH} is empty — nothing to snapshot.")
    snap = full[:n_expected] if len(full) >= n_expected else full
    write_jsonl(PILOT_SNAPSHOT, snap)
    print(f"[PILOT] Froze {len(snap)} questions into NEW snapshot: {PILOT_SNAPSHOT}")
    print(f"[PILOT] This file will NOT be touched again by future eval-set generation runs.")
    return snap


_HEDGE_PHRASES = ("don't have enough information", "don't have that", "not able to answer",
                   "cannot answer", "no information available", "not sure", "don't know")


def looks_like_abstention(answer: str) -> bool:
    if not answer:
        return True
    low = answer.lower()
    return any(p in low for p in _HEDGE_PHRASES)


def run_model_on_pilot(pipeline, questions, label, adapter_dir=None):
    """label is 'base' or 'finetuned' — just used for logging/output naming."""
    results = []
    for item in questions:
        t0 = time.time()
        try:
            r = pipeline.run(session_id=f"pilot-{label}-{item['id']}", user_query=item["question"])
            results.append({
                "eval_id": item["id"], "category": item["category"], "question": item["question"],
                "support_status": item.get("support_status"),
                "answer": r.answer, "sources": r.sources, "used_rag": r.used_rag,
                "latency_s": round(time.time() - t0, 2), "error": None,
            })
        except Exception as e:
            results.append({
                "eval_id": item["id"], "category": item["category"], "question": item["question"],
                "support_status": item.get("support_status"),
                "answer": None, "sources": [], "used_rag": False,
                "latency_s": round(time.time() - t0, 2), "error": str(e),
            })
    return results


def compute_diagnostics(results):
    """TODO: replace with your real Track 2 / Track 7 scoring once available."""
    n = len(results)
    answered = [r for r in results if r["answer"]]
    answer_rate = len(answered) / n if n else 0.0

    should_hedge = [r for r in results if r["support_status"] in ("unsupported", "partially_supported")]
    hedged_correctly = [r for r in should_hedge if looks_like_abstention(r["answer"] or "")]
    abstention_rate = len(hedged_correctly) / len(should_hedge) if should_hedge else None

    has_citation = sum(1 for r in results if r["sources"])
    citation_rate = has_citation / n if n else 0.0

    return {
        "n_questions": n,
        "answer_rate": round(answer_rate, 3),
        "abstention_rate_on_should_hedge": round(abstention_rate, 3) if abstention_rate is not None else None,
        "n_should_hedge": len(should_hedge),
        "citation_present_rate": round(citation_rate, 3),
        "note": "DIAGNOSTIC PROXY ONLY — not the official Track 2/7 methodology. See file header.",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--adapter-dir", type=str, default=None,
                    help="Path to a trained LoRA adapter. If omitted or not found, fine-tuned "
                         "evaluation is skipped and clearly reported as BLOCKED rather than faked.")
    args = p.parse_args()

    questions = freeze_pilot_snapshot()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n[PILOT] Running BASE model on {len(questions)} questions...")
    pipeline = AgenticRAGPipeline()  # existing, unmodified — production config, no adapter
    base_results = run_model_on_pilot(pipeline, questions, "base")
    write_jsonl(RESULTS_DIR / "raw_results_base.jsonl", base_results)
    base_diag = compute_diagnostics(base_results)

    finetuned_results, finetuned_diag = None, None
    if args.adapter_dir and Path(args.adapter_dir).exists() and (Path(args.adapter_dir) / "training_complete.flag").exists():
        print(f"\n[PILOT] Found completed adapter at {args.adapter_dir}")
        print("[PILOT] NOT IMPLEMENTED YET: loading the fine-tuned model for inference needs "
              "wiring your pipeline to point at this adapter (a swap-in for whatever loads the "
              "base Groq/local model today). Tell me how AgenticRAGPipeline selects its backend "
              "and I'll fill this in exactly rather than guess.")
    else:
        print(f"\n[PILOT] No completed fine-tuned adapter found"
              f"{f' at {args.adapter_dir}' if args.adapter_dir else ''} — "
              f"fine-tuned evaluation is BLOCKED, not faked. Run train_raft_qlora.py first.")

    summary = {
        "base": base_diag,
        "finetuned": finetuned_diag,
        "status": "PILOT PARTIAL — base model only" if finetuned_diag is None else "PILOT COMPLETE",
    }
    write_jsonl(RESULTS_DIR / "summary.jsonl", [summary])

    print("\n" + "=" * 50)
    print("PILOT EVALUATION SUMMARY")
    print("=" * 50)
    print(json.dumps(summary, indent=2))
    print(f"Raw results: {RESULTS_DIR}")
    print("=" * 50)


if __name__ == "__main__":
    main()
