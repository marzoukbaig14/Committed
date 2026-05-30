# Handoff: Setup Agent

You are setting up the development environment and infrastructure for Committed. Read `CLAUDE.md` first; it is your behavioral contract and it governs everything below. Then read the relevant sections of `MASTER.md` (the tech stack and the dependency split).

Your job has a hard boundary. **You set up the environment and infrastructure. You do not write application code.** You are done when the environment rebuilds reproducibly and every service authenticates. Not before, not after.

## Why this handoff exists

A previous setup session lost an hour to a uv and virtualenv mess: commands were issued, assumed to have worked, and built upon while they were actually failing, and GPU dependencies were being forced into a CPU container. This handoff exists to make that impossible. Two things prevent it: a devcontainer that builds the environment deterministically, and the discipline below.

## How you work (non-negotiable)

- One step, or one tight group of related steps, at a time.
- Before each step, say what it does and what success looks like.
- After each step, **wait for the human to paste the actual terminal output.** Do not assume it worked. Do not move on until you have seen real evidence that it did.
- If output shows an error, diagnose from the actual text, propose the smallest fix, and re-verify.
- Teach as you go. The human is learning this stack. When you introduce a tool, say in a sentence or two what it is and why it is here.

## Prerequisites (confirm before starting)

Have the human confirm they have, or create, accounts for:
- GitHub (for the repo and Codespaces)
- Hugging Face (for datasets, adapters, Spaces)
- Weights & Biases (for run tracking)
- Anthropic (for the LLM-as-judge; needs a small amount of API credit)

You will need an access token from each of the last three. Do not ask for them in chat. They go into Codespaces secrets (see below).

## Target environment

GitHub Codespaces with a committed devcontainer is the canonical, reproducible environment. The human has no fixed personal machine and works from shared school computers, so this is not optional. Training happens later on Colab and Kaggle (GPU); this handoff covers the Codespace only.

## Step sequence

### 1. The devcontainer
Create `.devcontainer/devcontainer.json`. Start from this and adjust only with reason:

```json
{
  "name": "committed",
  "image": "mcr.microsoft.com/devcontainers/python:1-3.11-bookworm",
  "features": {
    "ghcr.io/devcontainers/features/git:1": {}
  },
  "postCreateCommand": "curl -LsSf https://astral.sh/uv/install.sh | sh && echo 'export PATH=\"$HOME/.local/bin:$PATH\"' >> ~/.bashrc",
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "charliermarsh.ruff"
      ]
    }
  }
}
```

What this does: pins Python 3.11 in a clean container, installs `uv` on creation, and puts `uv` on the PATH for future shells. Note that `postCreateCommand` deliberately does **not** run `uv sync` yet, because there is no `pyproject.toml` on the first build. After step 2 commits a `pyproject.toml` and `uv.lock`, update `postCreateCommand` to also run `uv sync` so future rebuilds install dependencies automatically. That is a small change worth a one-line decision record.

Teach: a devcontainer is a recipe for the whole dev environment. Anyone who opens this repo in a Codespace gets the identical setup, which is exactly why the shared-machine problem disappears.

Verify: open the repo in a Codespace, let it build, then in the terminal run `uv --version` and have the human paste the result.

### 2. Initialize the project with uv
- `uv init` to create `pyproject.toml`.
- Pin Python: confirm `pyproject.toml` requires `>=3.11`.
- Add the base dev tools: `uv add --dev ruff pytest`.
- This creates `uv.lock`. Commit `pyproject.toml` and `uv.lock`.

Teach: `uv` manages the virtualenv for you. You never activate anything by hand. You run things with `uv run <command>`, and `uv` ensures they run inside the right environment with the locked dependencies. The lockfile pins exact versions so the install is identical everywhere.

Verify: `uv run ruff --version` and `uv run pytest --version` both succeed. Have the human paste both.

### 3. Dependency groups, and the CPU-versus-GPU split
This is the step that prevents dependency hell.

- The default (CPU) dependencies install in the Codespace. Add them as a group, for example a `cpu` or default group: `datasets`, `pandas`, `transformers`, `llama-cpp-python`, `gradio`, `fastapi`, `uvicorn`, `evaluate`, `sacrebleu`, `rouge-score`, `scikit-learn`, `anthropic`, `wandb`, `pyyaml`.
- The GPU training stack goes in a separate `train` group that is **not installed in the Codespace**: `unsloth`, `bitsandbytes`, `accelerate`, `peft`, `trl`. These need CUDA and belong on Colab or the cluster.

Use `uv` dependency groups so the two sets are declared separately and the Codespace only installs the CPU set.

Teach: `bitsandbytes` and `unsloth` are built for NVIDIA GPUs. Installing them in a CPU container is where the previous session went wrong, since the install tries and fails to find CUDA. Keeping them in a `train` group that only the GPU machine installs removes the whole problem. Add the dependencies incrementally and verify each `uv sync` succeeds before adding more, so that if one package pulls a conflict you catch it immediately rather than ten packages later.

Verify: after the CPU group installs, run a one-line import smoke test (next step). Do not install the `train` group here.

### 4. Secrets
- Add Codespaces secrets for `HF_TOKEN`, `WANDB_API_KEY`, and `ANTHROPIC_API_KEY` (in the repo or account Codespaces settings, not in any file).
- Create `.env.example` listing those variable names with empty values, and ensure `.env` is gitignored.

Teach: secrets never go in the repo. Codespaces injects them as environment variables, and `.env.example` documents what is needed without exposing any real value.

Verify: confirm the variables are visible in the environment (for example `echo ${HF_TOKEN:+set}` prints `set` without revealing the value). Never print the actual token.

### 5. Smoke tests
Write small scripts (in `tests/` or `scripts/`) that:
- Import each major library and print its version.
- Authenticate to Hugging Face, W&B, and Anthropic using the env tokens, and confirm the connection without doing real work.

Run them with `uv run`.

Verify: all smoke tests pass. Have the human paste the output.

## Definition of done

- The Codespace rebuilds clean from the devcontainer.
- `uv run pytest` passes the smoke tests.
- ruff runs.
- Hugging Face, W&B, and Anthropic all authenticate.
- `pyproject.toml`, `uv.lock`, `.devcontainer/devcontainer.json`, `.env.example`, and `.gitignore` are committed.

When all of that is true, stop and hand back. The next phase (data) is not your job.

## Explicit non-goals
Do not load CommitChronicle. Do not write filters, training code, eval code, or model code. Do not install the GPU training stack in the Codespace. If you think any of these is needed now, you are out of scope; ask the human.

## If something breaks
Read the actual error. Ask for the full output if you do not have it. Fix the smallest thing. Re-verify. If a dependency conflict forces a version pin, note it and tell the human it should be a decision record, since a pin is a constraint the project now carries.