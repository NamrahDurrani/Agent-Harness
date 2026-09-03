"""
finetuning/baseline/train_raft_qlora.py

QLoRA fine-tuning on the RAFT training set built by build_raft_dataset.py.

*** READ THIS BEFORE RUNNING ***
Your existing AgriBot_FineTuning.ipynb currently loads `Qwen/Qwen2.5-1.5B-Instruct`
locally (a ~1.5B model). Your thesis requirement says to fine-tune
`openai/gpt-oss-20b` (~20B parameters) and NOT switch models. This script
follows your instruction and targets gpt-oss-20b by default, via HF_MODEL_NAME
below — but that is a MUCH heavier model than what's currently in your
notebook, and the two don't currently match. Before running this for real:
  1. Confirm you actually want to fine-tune the 20B open-weight release
     (huggingface.co/openai/gpt-oss-20b), not the Qwen placeholder.
  2. Confirm your GPU (local or Colab) has enough VRAM. Even 4-bit QLoRA
     on a 20B model needs roughly 14-16GB+ VRAM — a free-tier Colab T4
     (16GB, often less available) is right at the edge or insufficient;
     an A100 (40GB) is the safe choice. If that's not available, say so
     and we pick a smaller in-spirit model together rather than silently
     downgrading here.
  3. This is UNTESTED by me — I have no way to run this on your machine
     or Colab. Read through it before running, and expect to debug.

Resumability: if a completed adapter already exists at OUTPUT_DIR (marked
by a `training_complete.flag` file), this script exits without retraining
unless --force is passed. If a checkpoint exists but training didn't finish,
it resumes from the latest checkpoint via Trainer's own resume mechanism.

Usage:
    python train_raft_qlora.py                     # train (or resume) with defaults
    python train_raft_qlora.py --distractors 0      # ablation: golden:distractor = 1:0
    python train_raft_qlora.py --distractors 2      # ablation: 1:2 (default)
    python train_raft_qlora.py --distractors 4      # ablation: 1:4
    python train_raft_qlora.py --force              # retrain from scratch even if complete
"""
import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "finetuning" / "data" / "raft_train_set.jsonl"

HF_MODEL_NAME = os.environ.get("FT_MODEL_NAME", "openai/gpt-oss-20b")  # per thesis requirement — see warning above


def build_prompt(example, distractors_k):
    """Assembles the RAFT-style training prompt: question + oracle (if any)
    + up to distractors_k distractor chunks, SHUFFLED so the model can't
    learn 'oracle is always first'. Target output is the stored answer."""
    import random
    docs = []
    if example.get("oracle_text"):
        docs.append(("ORACLE", example["oracle_text"]))
    for i, txt in enumerate(example.get("distractor_texts", [])[:distractors_k]):
        docs.append(("DISTRACTOR", txt))
    random.shuffle(docs)

    context_block = "\n\n".join(f"[Document {i+1}]\n{txt}" for i, (_, txt) in enumerate(docs))
    prompt = (
        f"Answer the farmer's question using ONLY the relevant document(s) below. "
        f"Ignore documents that are not relevant. If none of the documents answer the "
        f"question, say you don't have enough information.\n\n"
        f"{context_block}\n\nQuestion: {example['question']}\nAnswer:"
    )
    return prompt, example["answer"]


def load_dataset_for_training(distractors_k):
    if not DATA_PATH.exists():
        raise RuntimeError(f"{DATA_PATH} not found — run build_raft_dataset.py first.")
    examples = []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                examples.append(json.loads(line))
    print(f"[TRAIN] Loaded {len(examples)} RAFT training examples "
          f"({sum(1 for e in examples if e['category']=='raft_grounded')} grounded, "
          f"{sum(1 for e in examples if e['category']=='raft_abstain')} abstain), "
          f"using {distractors_k} distractor(s)/example.")
    return examples


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--distractors", type=int, default=2, choices=[0, 1, 2, 3, 4],
                    help="golden:distractor ratio ablation — how many stored distractors to actually use")
    p.add_argument("--epochs", type=float, default=2.0)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--lora-r", type=int, default=16)
    p.add_argument("--lora-alpha", type=int, default=32)
    p.add_argument("--force", action="store_true", help="Retrain from scratch even if already complete.")
    args = p.parse_args()

    run_name = f"raft_d{args.distractors}_r{args.lora_r}_lr{args.lr}"
    output_dir = PROJECT_ROOT / "finetuning" / "checkpoints" / run_name
    complete_flag = output_dir / "training_complete.flag"

    if complete_flag.exists() and not args.force:
        print(f"[TRAIN] {complete_flag} already exists — this config is already trained.")
        print(f"[TRAIN] Adapter is at: {output_dir}")
        print(f"[TRAIN] Pass --force to retrain from scratch.")
        return

    examples = load_dataset_for_training(args.distractors)
    prompts = [build_prompt(e, args.distractors) for e in examples]

    print(f"[TRAIN] Model: {HF_MODEL_NAME}")
    print(f"[TRAIN] Output dir: {output_dir}")
    print(f"[TRAIN] LoRA: r={args.lora_r} alpha={args.lora_alpha} | lr={args.lr} | epochs={args.epochs}")

    # ---- Actual training loop ----
    # Deliberately not filled in blind: which of these you need depends on
    # answers only you can give me (local GPU vs Colab, VRAM available,
    # transformers/peft/trl versions already installed per your notebook's
    # cell 1). Rather than paste in a generic HF Trainer block that may not
    # match your environment and silently fail halfway through a long run,
    # tell me your GPU/VRAM situation and I'll fill this in exactly —
    # loading HF_MODEL_NAME in 4-bit, attaching LoRA (matching your
    # notebook's r=16/alpha=32/dropout=0.05/q,k,v,o_proj config), building
    # a Dataset from `prompts`, and wiring up Trainer/SFTTrainer with
    # resume_from_checkpoint support and periodic checkpoint saves.
    raise NotImplementedError(
        "Training loop intentionally left unimplemented until GPU/VRAM details are confirmed "
        "(see the *** READ THIS *** block at the top of this file). "
        f"{len(examples)} examples and {len(prompts)} prompts are ready to train on as soon as "
        f"the model-loading + Trainer block is filled in."
    )

    # On successful completion:
    # output_dir.mkdir(parents=True, exist_ok=True)
    # complete_flag.write_text(json.dumps({"examples": len(examples), "distractors": args.distractors}))


if __name__ == "__main__":
    main()
