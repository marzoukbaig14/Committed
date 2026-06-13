# Serving

The FastAPI inference service for Committed. Wraps `committed.inference.engine.CommitGenerator`
behind the HTTP contract in [`docs/serving/HTTP_CONTRACT.md`](../../../docs/serving/HTTP_CONTRACT.md).

## Endpoints

| Method | Path        | Body                  | Returns                       |
|--------|-------------|-----------------------|-------------------------------|
| POST   | `/generate` | `{"diff": "..."}`     | `{"message": "<one CC line>"}`|
| GET    | `/health`   | —                     | `{"status": "ok"}` (200)      |

## Model selection (never hardcoded)

Resolution order, all via environment variables:

1. `COMMITTED_MODEL_PATH` — explicit local `.gguf`. **Set this to swap in the fine-tuned
   model** once it exists (the one-line swap).
2. `COMMITTED_MODEL_REPO` + `COMMITTED_MODEL_FILE` — pulled from the Hub (public; no token).
   Defaults to the pinned baseline `ggml-org/Qwen3-1.7B-GGUF / Qwen3-1.7B-Q4_K_M.gguf` (ADR 0038).

`COMMITTED_CORS_ORIGINS` is a comma-separated list of exact allowed origins (production and any
custom domain). Vercel preview domains (`https://*.vercel.app`) are allowed by regex in `api.py`.

## Run locally (Linux / a machine with a C++ toolchain)

```bash
uv sync                       # builds llama-cpp-python
uv run uvicorn committed.serving.api:app --reload --port 7860
# in another shell:
curl localhost:7860/health
curl -X POST localhost:7860/generate -H 'content-type: application/json' \
  -d '{"diff": "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-x = 1\n+x = 2\n"}'
```

> `llama-cpp-python` needs a C/C++ compiler and does not build on the human's bare Windows
> machine (ADR 0041). Run serving in Docker, on CI/Linux, or on the Space.

## Docker / HF Docker Space

```bash
docker build -f src/committed/serving/Dockerfile -t committed-serve .
docker run -p 7860:7860 -e COMMITTED_CORS_ORIGINS="https://your-portfolio.vercel.app" committed-serve
```

The base GGUF and tokenizer are baked in at build time, so the container starts without a
network pull. To deploy, the human creates a Hugging Face **Docker** Space and points it at this
Dockerfile (set `COMMITTED_CORS_ORIGINS` in the Space variables). The free Docker Space sleeps
after ~48 h idle; the frontend handles the cold-start wake via `/health` (ADR 0043).
