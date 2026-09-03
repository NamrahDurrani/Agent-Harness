# AgriBot Fine-Tuning Project — Progress Log (Updated)

**Project:** Agentic RAG platform for agricultural knowledge (AgriBot)
**Tracks:** Track 2 (Groundedness & Factuality) + Track 7 (RAG-Adapted Fine-Tuning / RAFT)
**Status:** Eval-set generation ongoing (14/40). Training dataset builder, training script, and
pilot evaluation script written this turn but **none have been run** — I have no execution access
to your machine, so everything below marked "written" is unexecuted code, not a completed step.

---

## 0. Important limitation, stated plainly

I don't have live access to your project, your Groq key, your ChromaDB, or a GPU. I can only
read what you paste/upload into this chat and hand back files for you to run yourself. So
"progress" in this log means one of two things, and they're clearly separated below:
- **Confirmed done** — you ran it and pasted me the real output.
- **Written, not run** — I wrote code following your existing patterns, but it has not executed
  against your real data, model, or GPU, and may need debugging once you actually run it.

---

## 1. Confirmed done (you ran these, I saw the output)

- **Eval-set generation pipeline** (`build_eval_set.py`) — topic-weighted sampling from your real
  27,734-chunk ChromaDB collection, chunk-support verification before accepting a question,
  dedup, budgeted/quota-safe Groq calls, resumable JSONL output.
- **Auto-resume wrapper** (`run_until_target.ps1`) — reruns `build_eval_set.py` automatically,
  distinguishing the script's own artificial call cap from a real Groq quota/auth failure, and
  stopping cleanly (not looping) on the latter.
- **Eval-set progress:** 3 → 11 → 13 → **14 / 40 questions**, all currently `fully_answerable`
  (0 unanswerable, 0 partially_supported so far — target distribution is 20/10/10, current
  distribution is skewed and will need correcting as more are generated).
- **Root cause of "why it keeps stopping" identified:** Groq's free-tier daily quota for
  `openai/gpt-oss-20b` is small relative to this workload (as few as 5-8 accepted API calls before
  exhaustion in recent runs). The "try again in N minutes" text in Groq's error has been unreliable
  — a run that said "~2 minutes" was still blocked after 10 minutes, confirming this is a genuine
  daily cap, not a short cooldown. **Action needed from you:** check the real reset time/remaining
  quota at console.groq.com rather than trusting the in-message estimate.
- **B0 baseline** (`run_baseline.py`) — partially run in an earlier session (~20+ clean results),
  stopped by a real Groq daily-quota exhaustion, not a bug. Not yet finished for all 40 questions
  (currently blocked on the eval set itself not being at 40 yet).
- **Local cleanup tooling** (`clean_eval_set.py`) — dedup and manual filtering, zero API calls,
  keeps eval set and baseline results in sync.

---

## 2. Written this turn, NOT yet run — what's actually changing right now

Three new files, none executed:

### `build_raft_dataset.py`
- Builds a **separate** training dataset at `finetuning/data/raft_train_set.jsonl`, structurally
  parallel to `build_eval_set.py` (same topic buckets, same budgeted/resumable Groq-call pattern).
- **Contamination guard:** on every run, it loads whatever is currently in `eval_set_v1.jsonl` and
  builds an exclusion set from it (by source+page AND by normalized question text). Any chunk or
  generated question overlapping the eval set is skipped. This re-checks fresh each run, so it
  stays correct as the eval set grows from 14 to 40.
- Produces RAFT-format records: question, oracle chunk, up to 4 stored distractor chunks (from
  different topics), a grounded answer, and a citation hint. Also generates a smaller share of
  abstention examples (default 20%, matching the master brief's suggested composition).
- Distractor **ratio ablations (1:0 / 1:2 / 1:4)** are handled at training time by slicing
  `distractor_texts[:k]` — one dataset build supports all three ablation runs, per the brief's
  requirement to change only one variable at a time.

### `train_raft_qlora.py`
- **Flags a real conflict rather than silently resolving it:** your thesis instruction says fine-tune
  `openai/gpt-oss-20b` and don't switch models. Your existing `AgriBot_FineTuning.ipynb` currently
  loads `Qwen/Qwen2.5-1.5B-Instruct` instead — a much smaller model. This script targets
  `openai/gpt-oss-20b` per your explicit instruction, but that needs real GPU/VRAM headroom
  (roughly 14-16GB+ even at 4-bit QLoRA) that a free Colab T4 may not reliably have. **This needs
  your decision, not mine**, before any training actually runs.
- Idempotent/resumable by design: checks for a `training_complete.flag` in the target checkpoint
  dir before doing anything, so rerunning doesn't retrain a config that's already done. Distinct
  checkpoint dirs per ablation config (e.g. `raft_d2_r16_lr0.0001/`) so the three distractor
  ablations don't collide.
- **The actual model-loading + Trainer loop is deliberately left as `NotImplementedError`.** I did
  not paste in a generic HF Trainer block, because it needs to match your real environment
  (installed `transformers`/`peft`/`trl` versions, local GPU vs. Colab, available VRAM) and a
  mismatched block could fail silently partway through a long run. Tell me your actual GPU
  situation and I'll fill this in precisely.

### `evaluate_pilot.py`
- Freezes whatever is currently in `eval_set_v1.jsonl` into a pinned `eval_pilot_snapshot.jsonl`
  the first time it's run, so the pilot's question basis doesn't silently shift as the eval set
  grows toward 40 later.
- Runs the **base**, unmodified AgriBot pipeline on that snapshot and saves raw answers/sources.
- Checks for a completed fine-tuned adapter; if none exists (true right now, since training hasn't
  run), it reports the fine-tuned side as **BLOCKED**, not fabricated or skipped silently.
- **Honesty flag on scoring:** I do not have your actual Track 2 / Track 7 scoring implementation
  (claim verification, citation precision/recall, noise-robustness harness) — it wasn't shared in
  this conversation. Rather than invent new metrics and label them "Track 2"/"Track 7" (which
  you explicitly said not to do), this script computes clearly-labeled **diagnostic proxies only**
  (answer rate, keyword-based abstention check, citation-presence rate) and marks them as such in
  the output. If real Track 2/7 scoring code exists elsewhere in your project, point me to it and
  I'll wire it in directly instead of the proxy.

---

## 3. Issues / gaps identified this turn

1. **Training dataset never existed** — confirmed via your own message; `build_raft_dataset.py`
   above is the first attempt at it, unexecuted.
2. **Fine-tuning notebook has no training loop** — 5 cells of setup only (GPU check, installs,
   4-bit model load, LoRA config attach). No dataset loading, no `Trainer`, no saved checkpoint.
3. **Model mismatch** — notebook loads `Qwen/Qwen2.5-1.5B-Instruct`; thesis requirement is
   `openai/gpt-oss-20b`. Not resolved; needs your decision on GPU capacity first.
4. **Track 2/7 scoring methodology not available to me** — I only have the *plan* for what these
   should measure (from the master brief), not your actual scoring code, if it exists.
5. **Track 7 noise-robustness curve has no eval-side support yet** — `eval_set_v1.jsonl` questions
   don't carry distractor sets the way the new RAFT training records do. A distractor-injected
   eval variant (0/1/2/4/8 distractors, per question) still needs to be built separately before a
   real noise-robustness comparison is possible.
6. **Groq daily quota is the binding constraint** on eval-set completion — expect this to take
   multiple short sessions across days, not one sitting, unless the Groq plan is upgraded.
7. **Eval-set category imbalance** — all 14 accepted questions so far are `fully_answerable`; the
   `unanswerable` and `partially_supported` generators haven't produced any accepted examples yet
   in the runs seen. Worth checking directly once more quota is available.

---

## 4. Honest current state block

```
Base model (production/eval-set generation): openai/gpt-oss-20b (via Groq)
Notebook's currently loaded model:            Qwen/Qwen2.5-1.5B-Instruct (MISMATCH — unresolved)

Evaluation questions:        14 / 40  (all fully_answerable so far)
RAFT training dataset:       NOT YET BUILT (script written, not run)
Fine-tuning:                 NOT STARTED (training loop not implemented, model choice unresolved)
Base model pilot evaluation: NOT YET RUN (script written, not run)
Fine-tuned model evaluation: BLOCKED (no adapter exists)
Track 2 scoring:             Diagnostic proxy only — real methodology not shared with me
Track 7 scoring:             Not implementable yet — needs distractor-injected eval variant

Next action: decide GPU/VRAM plan for openai/gpt-oss-20b QLoRA (or confirm downgrading the
             fine-tuning target), then run build_raft_dataset.py once quota allows.
```
