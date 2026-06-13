"""
api.py — FastAPI serving layer for Committed.

Wraps the shared CommitGenerator behind the HTTP contract the frontend depends on
(ADR 0043):

    POST /generate  {"diff": "..."}  -> {"message": "<one CC line>"}
    GET  /health                     -> {"status": "ok"}  (200 once the model is loaded)

The model is loaded once at startup (lifespan), never per request. CORS allows the
portfolio's origins: exact prod/custom domains via COMMITTED_CORS_ORIGINS (comma
separated), plus every Vercel preview domain (https://*.vercel.app) via regex.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from committed.inference.engine import CommitGenerator

# process-wide model handle; populated at startup, read per request.
_state: dict = {}


class GenerateRequest(BaseModel):
    diff: str


class GenerateResponse(BaseModel):
    message: str


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # one model instance for the process; path resolved from the environment.
    _state["generator"] = CommitGenerator()
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
    if "generator" not in _state:
        raise HTTPException(status_code=503, detail="model not loaded")
    return {"status": "ok"}


@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest) -> dict:
    if not req.diff.strip():
        raise HTTPException(status_code=400, detail="empty diff")
    return {"message": _state["generator"].generate(req.diff)}
