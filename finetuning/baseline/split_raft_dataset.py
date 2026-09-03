"""
finetuning/baseline/split_raft_dataset.py

Step 9: splits raft_train_set.jsonl into train/validation files, 90/10,
STRATIFIED by category (raft_grounded / raft_abstain) so both splits
contain a representative mix rather than validation accidentally being
all-abstain or all-grounded on a small dataset. Deterministic (fixed
seed) so reruns don't reshuffle the split.

This is a NEW step, not present in train_raft_qlora.py as written (it
currently loads the whole raft_train_set.jsonl with no split) — added
because a held-out validation slice is standard practice for judging
overfitting during QLoRA training, and costs nothing to produce.

Usage:
    python split_raft_dataset.py                    # default 90/10
    python split_raft_dataset.py --val-frac 0.15     # custom split
"""
import argparse
import json
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = PROJECT_ROOT / "finetuning" / "data" / "raft_train_set.jsonl"
TRAIN_OUT   = PROJECT_ROOT / "finetuning" / "data" / "raft_train_split.jsonl"
VAL_OUT     = PROJECT_ROOT / "finetuning" / "data" / "raft_validation_split.jsonl"

SPLIT_SEED = 44  # different from build_eval_set.py (42) and build_raft_dataset.py (43)


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--val-frac", type=float, default=0.10)
    args = p.parse_args()

    if not SOURCE_PATH.exists():
        raise RuntimeError(f"{SOURCE_PATH} not found — run build_raft_dataset.py first.")

    with open(SOURCE_PATH, "r", encoding="utf-8") as f:
        examples = [json.loads(line) for line in f if line.strip()]

    rng = random.Random(SPLIT_SEED)
    train, val = [], []
    for category in ("raft_grounded", "raft_abstain"):
        subset = [e for e in examples if e["category"] == category]
        rng.shuffle(subset)
        n_val = max(1, round(len(subset) * args.val_frac)) if subset else 0
        val.extend(subset[:n_val])
        train.extend(subset[n_val:])

    rng.shuffle(train)
    rng.shuffle(val)

    write_jsonl(TRAIN_OUT, train)
    write_jsonl(VAL_OUT, val)

    print("=" * 50)
    print("RAFT DATASET SPLIT")
    print("=" * 50)
    print(f"Source: {SOURCE_PATH} ({len(examples)} total)")
    print(f"Train:      {len(train)}  -> {TRAIN_OUT}")
    print(f"Validation: {len(val)}  -> {VAL_OUT}")
    print(f"  train grounded/abstain: "
          f"{sum(1 for e in train if e['category']=='raft_grounded')}/"
          f"{sum(1 for e in train if e['category']=='raft_abstain')}")
    print(f"  val grounded/abstain:   "
          f"{sum(1 for e in val if e['category']=='raft_grounded')}/"
          f"{sum(1 for e in val if e['category']=='raft_abstain')}")
    print("=" * 50)


if __name__ == "__main__":
    main()
