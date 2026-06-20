"""
engine.py — the shared inference core for Committed.
One place owns the load + prompt + grammar + decode construction proven at
baseline (ADRs 0038/0039/0040): the batch eval driver (generate.py), the FastAPI
service (serving/api.py), and the Gradio demo (app/app.py) all call it, so
eval-time and serve-time inference are byte-for-byte the same and cannot drift.
That parity is what protects the train/inference match.

The model path is never hardcoded. Resolution order:
  1. COMMITTED_MODEL_PATH — an explicit local .gguf. Set this to swap in the
     fine-tuned model later; that is the one-line swap the serving plan calls for.
  2. COMMITTED_MODEL_REPO + COMMITTED_MODEL_FILE — pulled from the Hugging Face
     Hub (public repo, no token needed), defaulting to the fine-tuned GGUF (ADR 0048).
"""
from __future__ import annotations

import os
from pathlib import Path

from llama_cpp import Llama, LlamaGrammar
from transformers import AutoTokenizer

from committed.inference.prompt import build_prompt

# Serving artifact of record (ADR 0048): the fine-tuned GGUF is the default, so a
# deploy with no model env vars set serves the right model. Baseline (ADR 0038)
# is still reachable by overriding COMMITTED_MODEL_REPO / _FILE; the eval path
# always sets the model explicitly, so this default never touches eval.
DEFAULT_MODEL_REPO = "marzoukbaig14/committed-gguf"  # fine-tuned serving artifact of record (ADR 0048); baseline override via COMMITTED_MODEL_REPO
DEFAULT_MODEL_FILE = "committed-finetuned-Q4_K_M.gguf"  # ADR 0044 merged-adapter Q4_K_M (ADR 0048)
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


class NotADiffError(ValueError):
    """Raised when the input doesn't plausibly look like a code diff.

    Defined in the engine so every caller shares one guard: the FastAPI service
    turns it into a 400, the Gradio demo renders its message, and the eval path
    (which only ever feeds real git-diff output) never trips it. Previously this
    check lived only in the Gradio wrapper, so the FastAPI /generate path — the
    one the portfolio calls — had no guard and let garbage through.
    """


# Single source of the user-facing guidance shown when input fails the diff
# check. Kept here (not inline in generate) so every caller surfaces identical
# wording: generate() raises it, and the CLI fast-rejects with it BEFORE loading
# the ~1 GB model, so piping gibberish fails in <1s instead of after a cold load.
NOT_A_DIFF_MESSAGE = (
    "That doesn't look like a code diff. Paste the output of `git diff` "
    "— lines with +/- changes, @@ hunks, or a `diff --git` header."
)


def looks_like_diff(text: str) -> bool:
    """Loose check: is this plausibly a code diff? Catches garbage like 'asdf'
    without demanding a perfectly-formed patch. (Moved here from app/app.py so
    all entry points enforce it, not just Gradio.)"""
    t = text.strip()
    if not t:
        return False
    if "diff --git" in t or "@@ " in t:
        return True
    if "--- " in t and "+++ " in t:
        return True
    change_lines = sum(
        1
        for line in t.splitlines()
        if line[:1] in "+-" and not line.startswith(("+++", "---"))
    )
    return change_lines >= 2


def resolve_model_path() -> str:
    """Locate the GGUF without hardcoding it: an explicit local path wins, else
    pull (repo, file) from the Hub. The repo is public, so no token needed."""
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
        # CPU thread counts. Leave as None for the default (used by eval, so eval
        # behavior is unchanged). Serving on a known core count (e.g. a 2-vCPU
        # Space) should set these so llama.cpp does NOT oversubscribe to the
        # container host's core count, which is what makes prefill crawl.
        n_threads: int | None = None,        # threads for token generation (decode)
        n_threads_batch: int | None = None,  # threads for prompt processing (prefill)
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
            n_threads=n_threads,
            n_threads_batch=n_threads_batch,
            verbose=False,
        )
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
        self.grammar = LlamaGrammar.from_string(Path(grammar_path).read_text())

    def generate(self, diff: str) -> str:
        """Render the frozen prompt, decode under the CC grammar, normalize one line.

        Guards non-diff input first (NotADiffError) so every caller — FastAPI,
        Gradio, eval — rejects garbage identically. Real git-diff output always
        passes the check, so the eval path is unaffected.
        """
        if not looks_like_diff(diff):
            raise NotADiffError(NOT_A_DIFF_MESSAGE)
        prompt = build_prompt(diff, self.tokenizer)
        out = self.llm.create_completion(prompt, grammar=self.grammar, **self.decode_kwargs)
        message = out["choices"][0]["text"].strip()
        if message.endswith("."):
            message = message[:-1]  # one trailing period, matching ADR 0017 + the grammar
        return message
