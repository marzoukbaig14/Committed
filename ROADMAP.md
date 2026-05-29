# Committed — Roadmap

This is the near-term plan. The broader phases live at the bottom. The next seven days are sequenced deliberately: stand up the decision-logging system first so it captures everything from here on (including the environment setup), then build a bulletproof environment, then start the data work.

Days will slip. That is expected. The point of the descope ladder in `MASTER.md` is to absorb slippage without panic. Each day below also says what the agent should teach you, since you are here to learn the stack, not just stand it up.

---

## The next 7 days

### Day 1 — Repo skeleton and the decision-logging system
Goal: a clean repo and a working, automated decision log that already captures what we have decided so far.
- Create the GitHub repo `committed`. Add `CLAUDE.md`, `MASTER.md`, `ROADMAP.md`, `START_HERE.md`, and the `handoffs/` directory.
- Stand up the decision-log system from `handoffs/DECISIONLOG_AGENT.md`: the `docs/decisions/` directory, the record template, the generator script, and the seed records capturing our locked decisions.
- Run the generator and confirm `docs/DECISION_LOG.md` and `docs/decision-tree.md` build correctly.
- **You should understand by end of day:** what ADRs are and why they are append-only, how the generator turns records into the log and tree, and the confirm-then-log protocol you will follow for the rest of the project.

### Day 2 — Environment, part 1: devcontainer and uv
Goal: a Codespace that builds itself the same way every time.
- Write `.devcontainer/devcontainer.json`. Open the repo in a Codespace and confirm it builds.
- Initialize the project with `uv`, pin Python 3.11, and add the base dev dependencies (`ruff`, `pytest`).
- Learn the workflow: `uv sync` to install from the lockfile, `uv run <command>` to run inside the managed environment without ever activating a venv by hand.
- Smoke test: `uv run ruff --version` and `uv run pytest --version` both succeed.
- **You should understand by end of day:** what a devcontainer is and why it solves the shared-machine problem, what `uv` does, and why a lockfile matters for reproducibility.

### Day 3 — Environment, part 2: ML deps, accounts, secrets, smoke tests
Goal: every tool installed in the right place, every service authenticating.
- Add the CPU/dev dependency group (datasets, pandas, transformers, llama-cpp-python, gradio, fastapi, the eval libraries, anthropic, wandb). Add the GPU `train` group (unsloth, bitsandbytes) but **do not install it in the Codespace.** Understand why the split exists.
- Set up Hugging Face, Weights & Biases, and Google AI Studio (Gemini, free tier) accounts and tokens. Store tokens as Codespaces secrets and create `.env` from `.env.example`.
- Write tiny smoke-test scripts that import each library and authenticate to each service, run via `uv run`.
- **You should understand by end of day:** why the training stack must not go in the CPU container, how secrets flow through Codespaces, and what "the environment is done" actually means (it builds clean and everything authenticates).

### Day 4 — Data, part 1: load and inspect CommitChronicle
Goal: real familiarity with the raw data before touching filters.
- Load CommitChronicle from the Hub. Explore its structure and look at many real samples.
- Check the dataset license terms for redistribution of a filtered derivative.
- Look at the token-length distribution of diffs and messages; this is what will set your diff cap.
- **You should understand by end of day:** the `datasets` library, streaming versus full download, and why you always inspect before you filter.

### Day 5 — Data, part 2: write the filter logic (your core work)
Goal: the filtering rules, written by you.
- Write the Conventional Commits regex and the heuristics (length bounds, single-file, drop merges and reverts and bots, Python only).
- Decide the diff token cap empirically from yesterday's distribution.
- Test the filters on a sample and eyeball the results.
- **You should understand by end of day:** why you cap by tokens rather than lines, and how stratifying by commit type keeps the split balanced.

### Day 6 — Data, part 3: filter, split, and push
Goal: a published dataset, the first real artifact.
- Run the filters over the full source, build the 90/5/5 split, and push the filtered dataset to the Hub.
- Write the dataset card.
- **You should understand by end of day:** what a dataset card is, why splits live with the artifact, and the Hub-as-registry idea.

### Day 7 — Eval design and buffer
Goal: the evaluation scaffolding and a sanity-checked rubric.
- Draft the judge prompt and rubric (your core work). Write the eval-harness skeleton.
- Hand-rate a handful of examples to sanity-check the rubric before committing to it.
- Use leftover time as buffer for anything that slipped.
- **You should understand by end of day:** why LLM-as-judge needs human validation, and what the five metrics each tell you.

By the end of the week you should have a reproducible environment, a working decision log, a published filtered dataset, and an eval design ready to run. That is a strong, honest seven days.

---

## Phase map (the bigger picture)

| Phase | What happens |
|-------|--------------|
| Setup | Decision log, environment, accounts, secrets. (Days 1 to 3 above.) |
| Data | Load, inspect, filter, split, publish. (Days 4 to 6.) |
| Eval design | Judge prompt, harness, 50 human ratings. (Day 7 and into the next week.) |
| Baseline | Run base Qwen3-1.7B on the eval, with and without a naive prompt. |
| Train v1 | QLoRA on Colab, iterate on hyperparameters, push adapters, log to W&B. |
| Final eval | Full eval, judge-versus-human correlation, the stretch ablations if time. |
| Serve | Merge, convert to GGUF, GBNF grammar, FastAPI, Docker, benchmarks. |
| Ship | Gradio demo on Spaces, README, model and dataset cards. |
| v2 (later) | Reasoning-trace distillation and the with-versus-without ablation. |

Routine code commits go through git. Anything that changes the design, the stack, the scope, or the infrastructure goes through the decision-log flow.