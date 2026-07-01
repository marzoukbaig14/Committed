"""
api.py — FastAPI serving layer for Committed (dual-model).

Wraps the shared CommitGenerator behind the HTTP contract the frontend depends on
(ADR 0043), extended to serve two fine-tunes selectable per request (ADR 0049/0050):

    POST /generate  {"diff": "...", "model": "1.7b" | "0.6b"}  -> {"message": "<one CC line>"}
        - `model` is OPTIONAL and defaults to "1.7b". A request with no `model` field
          behaves exactly as the v1 single-model service — backward compatibility is a
          hard requirement (the live portfolio sends no `model`).
        - An unknown `model` value returns 400, never a crash.
    GET  /health  -> {"status": "ok", "model_loaded": <bool>,
                      "models_loaded": [...], "models_available": [...]}

Load strategy (ADR 0049 choice): the DEFAULT model (1.7b) is loaded EAGERLY at startup
(lifespan warm-up), so the common path keeps v1 cold-start behavior. The other model
(0.6b) is loaded LAZILY on the first request that asks for it, then cached — so cold
start never pays for both models.

Thread fix (carried from v1): the free HF "CPU basic" Space has 2 vCPUs, but llama.cpp
defaults to the host's full core count and thrashes (~60s generation). EVERY generator
instance is built with n_threads=2, n_threads_batch=2 → warm generation ~2-7s.

CORS allows the portfolio's origins: exact prod/custom domains via COMMITTED_CORS_ORIGINS
(comma separated), plus every Vercel preview domain (https://*.vercel.app) via regex.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from committed.inference.engine import CommitGenerator, NotADiffError

# The free CPU Space has 2 vCPUs; pin llama.cpp to exactly those on every instance so it
# doesn't oversubscribe to the host core count and thrash. Speed only; output unchanged.
THREADS = 2

# --- Model registry: the new source of truth for which models are servable -------------
# id -> the Hub GGUF (repo, file) and the tokenizer to render prompts with. The default
# (1.7b) is served through the engine's own resolver so the v1 COMMITTED_MODEL_* Space
# Variables keep overriding it unchanged; the 0.6b is pulled by its explicit (repo, file).
DEFAULT_MODEL = "1.7b"
MODEL_REGISTRY: dict[str, dict] = {
    "1.7b": {
        "repo": "marzoukbaig14/committed-gguf",
        "file": "committed-finetuned-Q4_K_M.gguf",
        "tokenizer": "Qwen/Qwen3-1.7B",
    },
    "0.6b": {
        "repo": "marzoukbaig14/committed-gguf-0.6b",
        "file": "committed-0.6b-finetuned-Q4_K_M.gguf",
        "tokenizer": "Qwen/Qwen3-0.6B",
    },
}

# process-wide state; populated at startup, read per request.
#   _state["generators"]: id -> CommitGenerator (the lazy cache)
#   _state["model_loaded"]: whether the DEFAULT model is warm (the field the portfolio reads)
_state: dict = {}


def build_generator(model_id: str) -> CommitGenerator:
    """Construct (does not cache) the generator for a model id. Raises KeyError on unknown.

    The default model is built with no explicit path, so engine.resolve_model_path() applies
    the v1 COMMITTED_MODEL_PATH / _REPO / _FILE overrides (Space Variables) exactly as before.
    Non-default models are pulled by their registered (repo, file)."""
    if model_id not in MODEL_REGISTRY:
        raise KeyError(model_id)
    spec = MODEL_REGISTRY[model_id]
    if model_id == DEFAULT_MODEL:
        return CommitGenerator(n_threads=THREADS, n_threads_batch=THREADS)
    from huggingface_hub import hf_hub_download

    path = hf_hub_download(repo_id=spec["repo"], filename=spec["file"])
    return CommitGenerator(
        model_path=path, tokenizer_name=spec["tokenizer"],
        n_threads=THREADS, n_threads_batch=THREADS,
    )


def get_generator(model_id: str) -> CommitGenerator:
    """Return the cached generator for model_id, constructing+caching it on first use
    (this is the lazy load for the non-default model). Raises KeyError on unknown id."""
    cache = _state.setdefault("generators", {})
    if model_id not in cache:
        cache[model_id] = build_generator(model_id)
    return cache[model_id]


class GenerateRequest(BaseModel):
    diff: str
    # OPTIONAL; None -> DEFAULT_MODEL. Kept as a free str (not an enum) so an unknown value
    # is a clean 400 we control, rather than a 422 pydantic schema error.
    model: str | None = None


class GenerateResponse(BaseModel):
    message: str


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # False until the default model is fully constructed, so a /health hit mid-startup
    # reports the truth. Eager-load ONLY the default; the 0.6b loads lazily on first use.
    _state["generators"] = {}
    _state["model_loaded"] = False
    get_generator(DEFAULT_MODEL)  # eager warm-up of the default (v1 cold-start behavior)
    _state["model_loaded"] = True
    yield
    _state.clear()


app = FastAPI(title="Committed", lifespan=lifespan)

_origins = [o.strip() for o in os.environ.get("COMMITTED_CORS_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    if not _state.get("generators"):
        raise HTTPException(status_code=503, detail="model not loaded")
    # model_loaded (default-model warm signal) is preserved for the portfolio's cold-start
    # check; models_loaded/available are additive for the dual-model UI.
    cache = _state.get("generators", {})
    return {
        "status": "ok",
        "model_loaded": bool(_state.get("model_loaded", False)),
        "models_loaded": sorted(cache.keys()),
        "models_available": list(MODEL_REGISTRY.keys()),
    }


@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest) -> dict:
    if not req.diff.strip():
        raise HTTPException(status_code=400, detail="empty diff")
    model_id = req.model or DEFAULT_MODEL
    if model_id not in MODEL_REGISTRY:
        raise HTTPException(
            status_code=400,
            detail=f"unknown model '{model_id}'; available: {list(MODEL_REGISTRY.keys())}",
        )
    try:
        gen = get_generator(model_id)  # lazy-loads the 0.6b on first request
        return {"message": gen.generate(req.diff)}
    except NotADiffError as e:
        # Non-diff input is a client error: 400 with the engine's explanatory message,
        # which the portfolio renders as its "doesn't look like a diff" guidance.
        raise HTTPException(status_code=400, detail=str(e))
