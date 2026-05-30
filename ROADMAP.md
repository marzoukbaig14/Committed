# Committed — Roadmap

**Updated May 30, 2026.** Day 1 closed out yesterday covering everything originally planned for Days 1–3, plus a live decision cycle (ADR 0011, judge switch to Gemini free tier). The plan below reflects actual pace: infrastructure moves faster than projected because scaffolding is delegated to agents; core work (filter logic, judge prompt, training config) takes the full day it deserves and is never delegated. Days will still slip; the descope ladder in `MASTER.md` handles it.

---

## The next 7 days

### Day 1 — May 29 ✓ DONE

What was planned: repo skeleton and decision-log system. What actually happened: more.

- GitHub repo created. Decision-log system standing with 11 ADRs, generator script written and debugged (two real bugs caught and fixed: octal YAML parsing, filename-id derivation).
- Devcontainer, uv, ruff, pytest, lockfile. CPU dependency group (14 libraries). GPU `train` group declared but not installed. First live decision cycles: devcontainer `uv sync` (ADR 0010); judge switched from paid Anthropic Haiku to free Gemini 2.5 Flash (ADR 0011, superseding 0008).
- Planning docs (README, MASTER.md, ROADMAP.md) committed to the repo.
- **One task carried forward to today:** `CLAUDE.md`, `START_HERE.md`, and `handoffs/` not yet committed to the repo.

**You learned:** what ADRs are and why they are append-only; how the generator works and why it reads ids from filenames; the confirm-then-log protocol; the CPU/GPU dependency split and why it matters; what a devcontainer is and what problem it solves; how to use `git pull` to reconcile a Codespace that has fallen behind the remote.

---

### Day 2 — May 30 (today)

Goal: finish setup completely and get real eyes on the raw data.

**Setup finish (first ~1-2 hours):**
- Commit `CLAUDE.md`, `START_HERE.md`, and `handoffs/SETUP_AGENT.md` + `handoffs/DECISIONLOG_AGENT.md` to the repo. These were always meant to be there; five minutes to close it out.
- Get three tokens: Gemini API key from `aistudio.google.com` (free, no card needed); W&B key from `wandb.ai/authorize`; confirm your Hugging Face token has **write** scope (needed to push datasets and adapters later).
- Add all three as Codespaces secrets (`GEMINI_API_KEY`, `WANDB_API_KEY`, `HF_TOKEN`). Create `.env.example` documenting the variable names. Rebuild the Codespace so secrets inject. Verify with `echo ${VAR:+set}` — prints `set` without ever revealing the value.
- Write `tests/smoke_test.py`: import each major library, authenticate to HF, W&B, and Gemini. Run with `uv run pytest tests/smoke_test.py -v`. Commit the file. When this passes, setup is done.

**Data start (rest of the day):**
- Load CommitChronicle from the Hub in streaming mode. Read its schema, understand its columns, look at many real commit samples — not a skim, a real read.
- Check the dataset license for redistribution of a filtered derivative. Note what it says.
- Plot the token-length distribution of raw diffs and messages. This is not optional: the distribution is what sets your diff token cap, and that cap directly shapes training quality.

**You should understand by end of day:** how secrets flow through Codespaces and why tokens never go in files; what the smoke tests actually confirm; the `datasets` library (streaming vs. full load, and why you stream first on a dataset this large); and why you spend a full session looking at data before writing a single filter.

---

### Day 3 — May 31

Goal: write the filter logic. This is your core work — no agent writes it for you.

- Set the diff token cap from yesterday's distribution. Pick the value empirically, not arbitrarily.
- Write `src/committed/data/filter.py`: the Conventional Commits regex, message length bounds (5–200 chars), single-file changes only, Python commits only, drop merge commits, revert commits, and bot commits (Dependabot, GitHub Actions bot).
- Test the filters on a 5–10k sample. Read the outputs. If too aggressive (yield too low) or too loose (bad examples slipping through), adjust and re-test.
- Decide your stratification key for the 90/5/5 split (commit type is the natural choice).

**You should understand by end of day:** why you cap diffs by tokens not lines; how the regex maps to real Conventional Commits; what "stratified split" means in practice and why an unstratified split can silently mislead your eval.

---

### Day 4 — June 1

Goal: the first real artifact — a published, citable dataset on Hugging Face Hub.

- Run the filter pipeline over the full CommitChronicle (10.7M commits → target 30–50k pairs). This takes real time to execute; start it early.
- Build the 90/5/5 train/val/eval split, stratified by commit type.
- Push to the Hub as `<username>/committed-train`.
- Write the dataset card: what CommitChronicle is, what you filtered for and why, the schema, split sizes, and known limitations. Write the card you would want to find if you were using someone else's data.

**You should understand by end of day:** what a dataset card is and why it matters for reproducibility and trust; the Hub-as-registry pattern (push once, pull from anywhere); and what makes a split honest rather than leaky.

---

### Day 5 — June 2

Goal: a judge prompt that is validated, not just assumed good.

- Draft the Gemini judge prompt and rubric (your core work): type-correctness, specificity, scope-correctness, conciseness. This requires real thought — a vague rubric produces a misleading headline metric.
- Write the eval harness skeleton: `src/committed/eval/metrics.py` (BLEU, ROUGE-L, prefix-classification accuracy), `src/committed/eval/judge.py` (Gemini API call with free-tier throttling and 429 backoff), `src/committed/eval/run_eval.py` (ties it together).
- Hand-rate 20–30 examples yourself using the rubric you just wrote. Where does it feel wrong or ambiguous? Revise. Continue until your ratings and the rubric agree.

**You should understand by end of day:** why LLM-as-judge needs human validation to mean anything; what each of the five metrics measures and what it cannot; and why the judge-vs-human correlation is the number you will lead with in your README.

---

### Day 6 — June 3

Goal: baseline numbers in hand and a training run ready to fire.

- Finish the remaining human ratings to reach 50 total (20–30 done in Day 5). These 50 examples are load-bearing for the judge validation — take your time.
- Run the baseline: base Qwen3-1.7B (no fine-tune) on the eval set. Record all five metrics. This is your before number; every claim the fine-tune makes is measured against it.
- Write the training config in `configs/` (your core work): LoRA rank 16, alpha 32, learning rate 2e-4, sequence length informed by the token distribution from Day 2, batch size tuned to Colab T4 VRAM. Note what you chose and why.
- Set up the Colab environment: authenticate to HF and W&B, install the `train` dependency group, confirm the GPU is visible, and run a minimal import check before trusting the whole stack.

**You should understand by end of day:** what the baseline tells you about the starting point; the key hyperparameters in your QLoRA config and the reasoning behind each; and why checkpointing to the Hub during training is non-negotiable when the compute is ephemeral.

---

### Day 7 — June 4

Goal: first fine-tuned checkpoint on the Hub, W&B run attached.

- Fire the first QLoRA training run on Colab T4. Watch the loss curve live in W&B. Confirm it is descending rather than flat or spiking.
- Push checkpoints to the Hub every N steps. Colab disconnects; the Hub is the only persistent storage you trust.
- When the run finishes, pull the best checkpoint, run the eval harness, and compare against the Day 6 baseline.
- Buffer: use remaining time to close anything that slipped from Days 3–6 — a filter tweak, additional human ratings, a tighter judge prompt, a second training iteration.

**You should understand by end of day:** how to read a W&B training dashboard; what a healthy loss curve looks like versus overfitting; and what a first-run result tells you even when it is not great — a documented first result is honest engineering.

---

By the end of Day 7 you should have: a published filtered dataset on the Hub, a validated eval harness with a sanity-checked judge, baseline numbers, and a first fine-tuned adapter on the Hub with a W&B run attached. That is a strong and honest midpoint of v1.

---

## Phase map (the bigger picture)

| Phase | What happens | Status |
|-------|--------------|--------|
| Setup | Decision log, environment, accounts, secrets. | ✓ Done — smoke tests close it today |
| Data | Load, inspect, filter, split, publish. | Days 3–4 (starting today) |
| Eval design | Judge prompt, harness, 50 human ratings. | Days 5–6 |
| Baseline | Run base Qwen3-1.7B on the eval. | Day 6 |
| Train v1 | QLoRA on Colab, iterate, push adapters, log to W&B. | Day 7 onward |
| Final eval | Full eval, judge-vs-human correlation, stretch ablations if time. | After training |
| Serve | Merge, GGUF, GBNF grammar, FastAPI, Docker, benchmarks. | After eval |
| Ship | Gradio demo on Spaces, README, model and dataset cards. | End of v1 |
| v2 (later) | Reasoning-trace distillation, with-vs-without ablation. | After v1 ships |

Routine code commits go through git. Anything that changes the design, the stack, the scope, or the infrastructure goes through the decision-log flow.