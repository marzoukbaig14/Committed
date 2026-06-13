# Dockerfile for the Committed FastAPI inference service (HF Docker Space).
# Build from the REPO ROOT:  docker build -f src/committed/serving/Dockerfile -t committed-serve .
#
# llama-cpp-python compiles from source, so the image needs a C/C++ toolchain.
# The base GGUF and the tokenizer are public (ADR 0038), so they are baked into
# the image at build time — no Space secret needed, and cold starts skip the
# ~1.2 GB download (which would otherwise risk the Space's startup timeout).

FROM python:3.11-slim

# toolchain for building llama-cpp-python, plus git for any VCS deps.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential cmake git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# uv: reproducible installs from the committed lockfile (same tool CI uses).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# HF caches live inside the image so the model/tokenizer are present at runtime.
ENV HF_HOME=/app/.cache/huggingface \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PYTHONUNBUFFERED=1

# Install exactly what the lockfile pins (no dev, no GPU train group).
# Copy only what the build needs first, for layer caching.
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --locked --no-dev

# Warm the caches: pull the pinned public GGUF and the tokenizer at build time.
RUN uv run python -c "from huggingface_hub import hf_hub_download; hf_hub_download('ggml-org/Qwen3-1.7B-GGUF', 'Qwen3-1.7B-Q4_K_M.gguf')" \
    && uv run python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('Qwen/Qwen3-1.7B')"

# Comma-separated exact origins (prod + custom domain). *.vercel.app is matched by
# regex in api.py and need not be listed. Override at deploy time.
ENV COMMITTED_CORS_ORIGINS=""

# HF Spaces route to port 7860.
EXPOSE 7860
CMD ["uv", "run", "uvicorn", "committed.serving.api:app", "--host", "0.0.0.0", "--port", "7860"]
