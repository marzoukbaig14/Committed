"""
engine.py — the shared inference core for Committed.

One place owns the load + prompt + grammar + decode construction proven at
baseline (ADRs 0038/0039/0040): the batch eval driver (generate.py), the FastAPI
service (serving/api.py), and the Gradio demo (app/gradio_app.py) all call it, so
eval-time and serve-time inference are byte-for-byte the same and cannot drift.
That parity is what protects the train/inference match.

The model path is never hardcoded. Resolution order:
  1. COMMITTED_MODEL_PATH — an explicit local .gguf. Set this to swap in the
     fine-tuned model later; that is the one-line swap the serving plan calls for.
  2. COMMITTED_MODEL_REPO + COMMITTED_MODEL_FILE — pulled from the Hugging Face
     Hub (public repo, no token needed), defaulting to the pinned baseline GGUF.
"""

from __future__ import annotations

import os
from pathlib import Path

from llama_cpp import Llama, LlamaGrammar
from transformers import AutoTokenizer

from committed.inference.prompt import build_prompt

# Pinned baseline artifact (ADR 0038); the fine-tuned GGUF overrides via env var.
DEFAULT_MODEL_REPO = "ggml-org/Qwen3-1.7B-GGUF"
DEFAULT_MODEL_FILE = "Qwen3-1.7B-Q4_K_M.gguf"
DEFAULT_TOKENIZER = "Qwen/Qwen3-1.7B"
GRAMMAR_PATH = Path(__file__).parent / "grammar.gbnf"
N_CTX = 4096

# Decode settings reused verbatim from the baseline run. Do not change these
# without re-running the baseline, or the before/after delta stops being comparable.
DECODE_DEFAULTS: dict = {
    "temperature": 0.2,
    "max_tokens": 128,
    "seed": 7,
    "stop": ["</think>", "<think>"],  # backstop; enable_thinking=False is the real suppressor
}


def resolve_model_path() -> str:
    """Locate the GGUF without hardcoding it: an explicit local path wins, else
    pull (repo, file) from the Hub. The baseline repo is public, so no token needed."""
    explicit = os.environ.get("COMMITTED_MODEL_PATH")
    if explicit:
        return explicit
    from huggingface_hub import hf_hub_download

    repo = os.environ.get("COMMITTED_MODEL_REPO", DEFAULT_MODEL_REPO)
    filename = os.environ.get("COMMITTED_MODEL_FILE", DEFAULT_MODEL_FILE)
    return hf_hub_download(repo_id=repo, filename=filename)


class CommitGenerator:
    """Loads the model, tokenizer, and grammar once; turns a diff into one
    normalized Conventional Commits line."""

    def __init__(
        self,
        model_path: str | None = None,
        *,
        tokenizer_name: str | None = None,
        n_ctx: int = N_CTX,
        grammar_path: str | Path = GRAMMAR_PATH,
        **decode_kwargs,
    ) -> None:
        model_path = model_path or resolve_model_path()
        tokenizer_name = tokenizer_name or os.environ.get("COMMITTED_TOKENIZER", DEFAULT_TOKENIZER)
        self.decode_kwargs = {**DECODE_DEFAULTS, **decode_kwargs}
        # one seed drives both the model and decoding, exactly as the baseline did.
        self.llm = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            seed=self.decode_kwargs["seed"],
            verbose=False,
        )
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        self.grammar = LlamaGrammar.from_string(Path(grammar_path).read_text())

    def generate(self, diff: str) -> str:
        """Render the frozen prompt, decode under the CC grammar, normalize one line."""
        prompt = build_prompt(diff, self.tokenizer)
        out = self.llm.create_completion(prompt, grammar=self.grammar, **self.decode_kwargs)
        message = out["choices"][0]["text"].strip()
        if message.endswith("."):
            message = message[:-1]  # one trailing period, matching ADR 0017 + the grammar
        return message
