# Handoff: Serving Agent

You are building the serving layer for Committed: the thing that takes a code diff and returns a Conventional Commits message over HTTP, plus the standalone Gradio demo. Read `CLAUDE.md` first; it is your behavioral contract and governs everything below. Then read the Serving Plan and Output Format sections of `MASTER.md`, and the current `STATUS.md` so you know what already exists.

You work in the **Committed repo** (`marzoukbaig14/Committed`). You do not touch the portfolio repo; that is a separate agent's job. The two of you meet at one HTTP contract, defined below.

## Your job has a hard boundary

You build and deploy the model-serving path and the Gradio demo. You do **not** author the prompt wording, you do **not** run training, and you do **not** publicize anything. You are done when the FastAPI endpoint serves a valid commit message against the current base model on a Hugging Face Space, the Gradio demo runs, the merge/convert tooling is scaffolded, and the HTTP contract is documented for the frontend agent.

The model is not fine-tuned yet. You build against the base model and make the model path swappable so the fine-tuned GGUF drops in later with a one-line change. Priority for this pass: get it working against the base model. Quality comes from the fine-tune later.

## How you work (non-negotiable)

- One step, or one tight group of related steps, at a time.
- Before each step, say what it does and what success looks like.
- After each step, wait for the human to paste the actual terminal output before moving on. Do not assume a command worked.
- If output shows an error, diagnose from the actual error text, propose the smallest fix, and re-verify.
- Teach as you go. When you introduce a tool, say in a sentence or two what it is and why it is here.
- Stay in scope. If you think something should be added or changed, propose it and ask. Route design or dev decisions through the decision-log flow.

## The HTTP contract (lock this first — the frontend depends on it)

This is the seam between you and the frontend agent. Agree it with the human before building, and once set, do not change it without telling him, so the frontend stays in sync.

- `POST /generate` — body `{ "diff": "<unified diff text>" }` returns `{ "message": "<conventional commit subject line>" }`. One line, already normalized, grammar-valid.
- `GET /health` — returns `200 {"status":"ok"}` once the model is loaded. The frontend pings this on page load to wake the Space early and to drive a "waking up" state.
- CORS must allow the portfolio's origins: the production Vercel domain, any custom domain, and Vercel preview domains (`https://*.vercel.app`). Without this, the browser call from the page is blocked.

## What already exists (reuse, do not reinvent)

- The base model is the official `Qwen/Qwen3-1.7B` GGUF at Q4_K_M (~1.1 GB), the same artifact the baseline eval ran against. No conversion is needed for the base model.
- The eval/baseline already froze a zero-shot prompt and a thinking-suppression technique: the prompt is rendered with `AutoTokenizer.apply_chat_template(..., enable_thinking=False)`, and the resulting string is passed to `llm.create_completion(prompt_str, grammar=...)`, bypassing llama.cpp's flaky Qwen3 template handling. The serving path must reuse this exact construction so inference matches training and eval. Do not write a new prompt.

## Step sequence

1. **Read and confirm.** Read the contract above and the base-model-now / swap-later approach back to the human. Confirm the model path will be an environment variable or config value, never hardcoded.

2. **Inference core — `src/committed/inference/`.**
   - `prompt.py` **already exists and is the human's (ADR 0040); reuse it verbatim, do not author or reword it.** It is extracted, not rewritten: the `apply_chat_template(..., enable_thinking=False)` render is consolidated here as `build_prompt(diff, tokenizer) -> str`, pulled out of the existing baseline code, not written fresh.
   - `grammar.gbnf` **already exists and is finalized (ADR 0039); reuse it as-is.** It encodes the normalized Conventional Commits subject (ten-type codebook, optional `(scope)`, no `!`, single line, no trailing period). It is no longer an owed ADR.
   - `generate.py` — **do not rewrite it.** It is the baseline batch driver and holds the proven construction. Extract the load+prompt+grammar+decode core into `inference/engine.py`, leave `generate.py` as the batch driver importing it, and import `engine.py` from serving. `prompt.py` and `grammar.gbnf` are extracted from the existing code, not authored fresh. The only owed quant pin now is for the *fine-tuned* served GGUF (Q4_K_M/Q8/fp16), finalized when the adapter exists.

3. **FastAPI app — `src/committed/serving/api.py`.** Wrap `generate.py`. Expose `POST /generate` and `GET /health` per the contract. Add CORS for the portfolio origins. Load the model once at startup, not per request.

4. **Dockerfile — `src/committed/serving/Dockerfile`.** Linux base, install the serving deps (`llama-cpp-python`, `fastapi`, `uvicorn`), pull the public GGUF on startup (the model repo is public, so no Space secret is needed), run uvicorn. Model path via environment variable.

5. **Deploy the backend Space.** The human creates a Hugging Face **Docker** Space (this is the SDK choice that runs your Dockerfile). Verify `/generate` returns a valid line against the base model and `/health` returns ok. Confirm CORS by calling it from a browser origin.

6. **Gradio demo — `app/gradio_app.py`.** Phase-one standalone demo on a separate **Gradio** Space (Gradio SDK, no Dockerfile). Simplest path: load the base GGUF inline and serve the diff-to-message UI. The human sets this Space to **private** until the fine-tune is ready, per the no-publicize rule.

7. **Merge/convert tooling (scaffold only).** Write the script that will later merge the LoRA adapter into the base, convert to GGUF, and quantize (Q4_K_M primary; Q8 and fp16 for the quality-vs-latency comparison in `MASTER.md`). The adapter does not exist yet, so this is scaffolded and documented, not run. The GGUF quant pin is an owed decision record the human finalizes.

8. **Self-test.** Test the full path against the base GGUF on your branch. You can verify everything except fine-tuned quality.

## Definition of done

- `POST /generate` on the Docker Space returns a grammar-valid, normalized commit line against the base model; `GET /health` works; CORS allows the portfolio origins.
- The Gradio Space runs the base model and is set to private.
- The merge/convert/quantize script is scaffolded and documented.
- The HTTP contract is written down and handed to the frontend agent.
- The model path is an environment variable, so the fine-tuned GGUF swaps in with one change.

## Explicit non-goals

Do not author the prompt wording (the human's core). Do not run training. Do not touch the portfolio repo. Do not make the Spaces public or link them anywhere; no publicizing until the fine-tune is ready. Do not pin the GGUF quant or freeze the GBNF grammar without the owed decision records; draft to the normalization spec and flag them. If you hit a dependency or version constraint worth carrying, flag it as a decision record.

## If something breaks

Read the actual error. Ask the human for the full output. Form a hypothesis, propose the smallest fix, verify before continuing. `llama-cpp-python` needs a C++ toolchain to build; it builds fine in the Linux Docker image and on the Space, but not on a bare Windows machine, so do model runs in the container or on the Space, not locally.
