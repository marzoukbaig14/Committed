"""
cli.py — the `committed` command-line entry point.

Headline local path for the project: `git diff | committed` reads a unified diff
from stdin and prints one Conventional Commits line to stdout. This file is thin
plumbing only — all real inference logic (prompt, grammar, decode, the not-a-diff
guard) lives in engine.CommitGenerator, so the CLI, the FastAPI service, the
Gradio demo, and the eval driver all run byte-for-byte the same generation path.

Contract that makes it pipe-friendly:
  - stdout carries ONLY the generated message (so `git diff | committed` composes).
  - all progress/diagnostics ("loading model…", "downloading…") go to stderr.
  - non-diff input is rejected on stderr with a non-zero exit.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from committed.inference.engine import (
    DEFAULT_MODEL_FILE,
    DEFAULT_MODEL_REPO,
    NOT_A_DIFF_MESSAGE,
    CommitGenerator,
    NotADiffError,
    looks_like_diff,
)

# ~1.03 GB on the Hub (committed-finetuned-Q4_K_M.gguf). Hardcoded only for the
# one-line "first run downloads ~N" notice; the real size is whatever the Hub has.
_MODEL_SIZE_HINT = "~1.0 GB"


def _eprint(msg: str) -> None:
    """Everything that isn't the result goes to stderr, keeping stdout clean."""
    print(msg, file=sys.stderr, flush=True)


def _read_diff(diff_file: str | None) -> str:
    """Diff text comes from a file argument if given, else stdin (the default)."""
    if diff_file:
        return Path(diff_file).read_text(encoding="utf-8")
    if sys.stdin.isatty():
        # Run interactively with nothing piped in: there's no diff to read, so
        # guide the user instead of blocking forever on an empty stdin.
        _eprint("No diff on stdin. Try:  git diff | committed   (or: committed path/to/file.diff)")
        sys.exit(2)
    return sys.stdin.read()


def _resolve_model_path(cli_path: str | None) -> str:
    """Mirror engine.resolve_model_path's resolution order, but add a one-line
    download notice when the GGUF isn't cached yet (a ~1 GB silent hang is bad
    UX). An explicit path — CLI flag or COMMITTED_MODEL_PATH — skips the Hub."""
    explicit = cli_path or os.environ.get("COMMITTED_MODEL_PATH")
    if explicit:
        return explicit

    repo = os.environ.get("COMMITTED_MODEL_REPO", DEFAULT_MODEL_REPO)
    filename = os.environ.get("COMMITTED_MODEL_FILE", DEFAULT_MODEL_FILE)

    from huggingface_hub import hf_hub_download, try_to_load_from_cache

    # try_to_load_from_cache returns a str path only on a cache hit; otherwise a
    # sentinel or None. Anything but a str means we're about to download.
    if not isinstance(try_to_load_from_cache(repo, filename), str):
        _eprint(f"downloading model {repo}/{filename} ({_MODEL_SIZE_HINT}, first run only; cached afterward)…")
    # The repo is public, so no token is needed. Caches under the standard HF dir.
    return hf_hub_download(repo_id=repo, filename=filename)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="committed",
        description="Generate a Conventional Commits message from a git diff. "
        "Reads the diff from stdin by default: `git diff | committed`.",
    )
    parser.add_argument(
        "diff_file",
        nargs="?",
        help="Path to a file containing a unified diff. Omit to read from stdin.",
    )
    parser.add_argument(
        "--model-path",
        help="Path to a local .gguf to use instead of auto-downloading from the Hub.",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        help="Cap on generated tokens (default: the engine's tuned value).",
    )
    args = parser.parse_args()

    diff_text = _read_diff(args.diff_file)

    # Fast guard: reject empty / non-diff input BEFORE loading the model, so bad
    # input fails in milliseconds rather than after a cold ~1 GB load. Same guard
    # and same wording the engine uses, so every entry point rejects identically.
    if not diff_text.strip():
        _eprint("Empty input — nothing to summarize. Pipe a real diff: git diff | committed")
        sys.exit(2)
    if not looks_like_diff(diff_text):
        _eprint(NOT_A_DIFF_MESSAGE)
        sys.exit(1)

    model_path = _resolve_model_path(args.model_path)

    # Each CLI run is a fresh process, so it always pays a one-time model load
    # (~18s cold). Announce it so the user isn't staring at a frozen terminal.
    _eprint("loading model…")
    decode_overrides = {"max_tokens": args.max_tokens} if args.max_tokens else {}
    generator = CommitGenerator(model_path=model_path, **decode_overrides)

    try:
        message = generator.generate(diff_text)
    except NotADiffError as e:
        # Defensive: the pre-check above should already have caught this, but the
        # engine owns the guard, so honor it if it ever rejects something we let through.
        _eprint(str(e))
        sys.exit(1)

    # The result — and only the result — on stdout.
    print(message)


if __name__ == "__main__":
    main()
