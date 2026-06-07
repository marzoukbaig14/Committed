"""
Committed — LLM-as-judge plumbing (Anthropic Claude).

SCAFFOLDING ONLY. This is the API / caching / cost-control / parsing / logging layer for the
LLM-as-judge. The judge's *wording* — the four-axis rubric, axis questions, pass/fail criteria,
reasoning steps — lives in `judge_prompt.py` and is authored from `docs/eval/judge_rubric.md`.
This file contains NO rubric content.

Why Claude instead of the free Gemini judge (supersedes ADR 0011): an API budget now exists,
and for a judge whose human-correlation is the headline trust number, a stronger reasoner is a
real upgrade. To preserve the free-infrastructure thesis (the ADR 0019 precedent: better
resources for quality, but the core stays free-reproducible), the Gemini judge is kept as the
documented free fallback in judge_gemini.py — the harness treats the backend as swappable.

Key design choices, and why:

- STRUCTURED OUTPUT via tool-use. Current Claude models dropped assistant prefilling; the
  documented way to force a schema is a tool with enum fields + forced tool_choice. The
  submit_judgment tool pins the labels (all four axes binary pass|fail) and puts rationale
  before label per axis, so the model reasons before it labels.
  diff_summary comes first so it characterizes the diff before any axis judgment.

- PROMPT CACHING on the rubric. The rubric system prompt is identical across every call, so it
  goes in a cached system block (cache_control ephemeral) and is billed at ~10% after the first
  write — the single biggest cost lever here. (Caching needs a ~1024+ token prefix to engage;
  the four-axis rubric clears that. Ephemeral TTL is ~5 min, so keep the batch flowing.)

- COST GUARDRAILS. (1) MAX_OUTPUT_TOKENS caps the most expensive dimension (output is 5x input).
  (2) A CostTracker accumulates real usage and STOPS the run at a USD ceiling. (3) Diffs are
  capped at 2048 tokens by the dataset, so inputs can't run away; a char check skips anomalies.
  (4) Resumability means you never re-pay for a judged example.

- REFERENCE-FREE. Judges a candidate message against the diff only; the gold message is never
  shown (plausibility design, ADR 0027). run_eval.py supplies model generations as candidates.

- RESUMABLE. Each result is appended to a JSONL log as it completes; a restart skips done ids.

SDK: the `anthropic` package. Reads ANTHROPIC_API_KEY from the environment (Codespaces secret).
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Iterable, Iterator

import anthropic

# Rubric wording lives here (Zook's to author from docs/eval/judge_rubric.md). Contract changed
# from the Gemini version to support caching: a fixed JUDGE_SYSTEM string (the rubric — cached)
# plus build_judge_user(diff, message) -> str for the variable per-call turn. Guarded so this
# module imports for inspection before judge_prompt.py exposes them.
try:
    from committed.eval.judge_prompt import JUDGE_SYSTEM, build_judge_user  # type: ignore
except Exception:  # pragma: no cover - scaffold guard
    JUDGE_SYSTEM = None  # type: ignore
    build_judge_user = None  # type: ignore


# --------------------------------------------------------------------------------------------
# Config (the only knobs)
# --------------------------------------------------------------------------------------------

# Default judge. Sonnet 4.6 is the price/quality sweet spot and almost certainly matches Opus on
# a task this bounded. Flip to "claude-opus-4-8" for the strongest reasoner (cost is negligible
# at this scale). Pin the exact id for reproducible eval.
JUDGE_MODEL = "claude-sonnet-4-6"

# Cap output (the 5x-priced dimension). The structured judgment is ~300-450 tokens; 800 is slack.
MAX_OUTPUT_TOKENS = 800

# Deterministic-as-possible judge for eval reproducibility.
TEMPERATURE = 0.0

# Hard spend ceiling for a single run. The run STOPS when cumulative cost crosses this; the
# resumable log lets you raise it and continue. Set low while developing the prompt.
BUDGET_CEILING_USD = 25.0

# Safety check on input size (dataset already caps diffs at 2048 tokens; this catches anomalies).
MAX_DIFF_CHARS = 24_000

# Modest throttle + 429/overloaded backoff. Paid-tier limits are high, so this is light.
THROTTLE_RPM = 60
MAX_RETRIES = 6
INITIAL_BACKOFF_S = 2.0

# Per-MTok prices (USD), current as of June 2026. Cache read ~10% of input; cache write ~125%.
PRICES = {
    "claude-sonnet-4-6": {"in": 3.0, "out": 15.0},
    "claude-opus-4-8": {"in": 5.0, "out": 25.0},
    "claude-haiku-4-5-20251001": {"in": 1.0, "out": 5.0},
}
CACHE_READ_MULT = 0.10
CACHE_WRITE_MULT = 1.25


# --------------------------------------------------------------------------------------------
# Structured-output tool (the contract the judge must fill)
#
# rationale precedes label per axis (reason-then-label); diff_summary is first (characterize the
# diff before judging). Label enums encode the locked scales.
# --------------------------------------------------------------------------------------------

def _axis(label_enum: list[str]) -> dict:
    return {
        "type": "object",
        "properties": {
            "rationale": {"type": "string", "description": "Reasoning for this axis, written before the label."},
            "label": {"type": "string", "enum": label_enum},
        },
        "required": ["rationale", "label"],
    }


JUDGMENT_TOOL = {
    "name": "submit_judgment",
    "description": "Submit the per-axis judgment for this commit message.",
    "input_schema": {
        "type": "object",
        "properties": {
            "diff_summary": {"type": "string", "description": "What the diff actually changes, in your own words."},
            "type_correctness": _axis(["pass", "fail"]),
            "faithfulness": _axis(["pass", "fail"]),
            "completeness": _axis(["pass", "fail"]),
            "specificity": _axis(["pass", "fail"]),
        },
        "required": ["diff_summary", "type_correctness", "faithfulness", "completeness", "specificity"],
    },
}


# --------------------------------------------------------------------------------------------
# Cost tracking
# --------------------------------------------------------------------------------------------

class BudgetExceeded(RuntimeError):
    """Raised when cumulative cost crosses BUDGET_CEILING_USD. The runner stops cleanly; rerun
    with a higher ceiling to continue (the log is resumable)."""


class CostTracker:
    """Accumulates real token usage and computes USD from PRICES. Accounts cached reads/writes
    separately so the caching discount is reflected honestly."""

    def __init__(self, model: str, ceiling_usd: float) -> None:
        self.model = model
        self.ceiling = ceiling_usd
        self.p = PRICES.get(model, {"in": 5.0, "out": 25.0})  # default to Opus rate if unknown
        self.in_tok = self.out_tok = self.cache_read = self.cache_write = 0

    def add(self, usage) -> None:
        # anthropic usage: input_tokens (non-cached), output_tokens, cache_read_input_tokens,
        # cache_creation_input_tokens. getattr guards across SDK versions.
        self.in_tok += getattr(usage, "input_tokens", 0) or 0
        self.out_tok += getattr(usage, "output_tokens", 0) or 0
        self.cache_read += getattr(usage, "cache_read_input_tokens", 0) or 0
        self.cache_write += getattr(usage, "cache_creation_input_tokens", 0) or 0

    @property
    def usd(self) -> float:
        return (
            self.in_tok * self.p["in"]
            + self.cache_read * self.p["in"] * CACHE_READ_MULT
            + self.cache_write * self.p["in"] * CACHE_WRITE_MULT
            + self.out_tok * self.p["out"]
        ) / 1_000_000

    def check(self) -> None:
        if self.usd >= self.ceiling:
            raise BudgetExceeded(f"cumulative ${self.usd:.2f} >= ceiling ${self.ceiling:.2f}")


class RateLimiter:
    def __init__(self, rpm: int) -> None:
        self.min_interval = 60.0 / rpm if rpm > 0 else 0.0
        self._last = 0.0

    def wait(self) -> None:
        if self.min_interval <= 0:
            return
        gap = self.min_interval - (time.monotonic() - self._last)
        if gap > 0:
            time.sleep(gap)
        self._last = time.monotonic()


# --------------------------------------------------------------------------------------------
# Single judgment
# --------------------------------------------------------------------------------------------

def judge_one(client: anthropic.Anthropic, diff: str, message: str, *, model: str = JUDGE_MODEL):
    """Score one (diff, candidate message) pair on all four axes. Returns (judgment_dict, usage).
    Retries rate-limit / overloaded errors with exponential backoff + jitter."""
    if JUDGE_SYSTEM is None or build_judge_user is None:
        raise RuntimeError(
            "judge_prompt must expose JUDGE_SYSTEM (str, the rubric) and "
            "build_judge_user(diff, message) -> str."
        )

    user_text = build_judge_user(diff=diff, message=message)
    delay = INITIAL_BACKOFF_S
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=MAX_OUTPUT_TOKENS,
                temperature=TEMPERATURE,
                # Cached rubric prefix -> ~10% input cost after the first call.
                system=[{"type": "text", "text": JUDGE_SYSTEM, "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": user_text}],
                tools=[JUDGMENT_TOOL],
                tool_choice={"type": "tool", "name": "submit_judgment"},
            )
            for block in resp.content:
                if block.type == "tool_use" and block.name == "submit_judgment":
                    return block.input, resp.usage
            raise RuntimeError("model did not return the submit_judgment tool call")
        except (anthropic.RateLimitError, anthropic.APIStatusError) as e:
            # 429 (rate limit) and 529 (overloaded) are transient — back off and retry.
            status = getattr(e, "status_code", None)
            if attempt < MAX_RETRIES and (isinstance(e, anthropic.RateLimitError) or status == 529):
                time.sleep(delay + random.uniform(0, delay * 0.25))
                delay *= 2
                continue
            raise


# --------------------------------------------------------------------------------------------
# Resumable batch over records
# --------------------------------------------------------------------------------------------

def _load_done_ids(out_path: Path) -> set[str]:
    done: set[str] = set()
    if not out_path.exists():
        return done
    with out_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                done.add(str(json.loads(line)["id"]))
            except (json.JSONDecodeError, KeyError):
                continue
    return done


def judge_records(
    records: Iterable[dict],
    out_path: str | Path,
    *,
    model: str = JUDGE_MODEL,
    rpm: int = THROTTLE_RPM,
    limit: int | None = None,
    ceiling_usd: float = BUDGET_CEILING_USD,
) -> int:
    """Judge an iterable of records, appending each result to a JSONL log.

    record = {'id', 'diff', 'message'} where 'message' is the CANDIDATE being judged (a model
    generation, not the gold reference). Returns count of NEW judgments written. Resumable;
    stops cleanly on BudgetExceeded.
    """
    out_path = Path(out_path)
    done = _load_done_ids(out_path)
    limiter = RateLimiter(rpm)
    cost = CostTracker(model, ceiling_usd)
    client = anthropic.Anthropic()  # ANTHROPIC_API_KEY from env

    written = 0
    with out_path.open("a") as f:
        for rec in records:
            if limit is not None and written >= limit:
                break
            ex_id = str(rec["id"])
            if ex_id in done:
                continue
            if len(rec["diff"]) > MAX_DIFF_CHARS:
                print(f"[judge] skipping {ex_id}: diff exceeds {MAX_DIFF_CHARS} chars", file=sys.stderr)
                continue

            limiter.wait()
            judgment, usage = judge_one(client, rec["diff"], rec["message"], model=model)
            cost.add(usage)

            row = {
                "id": ex_id,
                "diff": rec["diff"],
                "message": rec["message"],
                "model": model,
                "ts": time.time(),
                "judgment": judgment,
                "usage": {
                    "input_tokens": getattr(usage, "input_tokens", 0),
                    "output_tokens": getattr(usage, "output_tokens", 0),
                    "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", 0),
                    "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", 0),
                },
            }
            f.write(json.dumps(row) + "\n")
            f.flush()
            written += 1

            try:
                cost.check()
            except BudgetExceeded as e:
                print(f"[judge] stopping: {e}. Rerun with a higher ceiling to continue.", file=sys.stderr)
                break

    print(f"[judge] {written} new judgments, est. cost ${cost.usd:.2f} this run", file=sys.stderr)
    return written


def estimate_cost(n: int, model: str = JUDGE_MODEL) -> float:
    """Rough pre-flight estimate: assumes ~300 variable-input tokens, ~1500 cached rubric tokens,
    ~400 output tokens per call. Order-of-magnitude only."""
    p = PRICES.get(model, {"in": 5.0, "out": 25.0})
    per = (300 * p["in"] + 1500 * p["in"] * CACHE_READ_MULT + 400 * p["out"]) / 1_000_000
    return per * n


# --------------------------------------------------------------------------------------------
# CLI (standalone / smoke test). run_eval.py calls judge_records() directly with Hub rows.
# --------------------------------------------------------------------------------------------

def _read_input_records(path: Path) -> Iterator[dict]:
    with path.open() as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            rec.setdefault("id", str(i))
            yield rec


def main() -> None:
    ap = argparse.ArgumentParser(description="Run the Claude LLM-as-judge over a JSONL of (diff, message) records.")
    ap.add_argument("--input", required=True, help="JSONL with 'diff' and 'message' per line (message = candidate).")
    ap.add_argument("--out", required=True, help="JSONL log to append judgments to (resumable).")
    ap.add_argument("--model", default=JUDGE_MODEL, help="Claude model id (pin for reproducibility).")
    ap.add_argument("--rpm", type=int, default=THROTTLE_RPM, help="Requests/minute throttle.")
    ap.add_argument("--limit", type=int, default=None, help="Max NEW examples to judge this run.")
    ap.add_argument("--ceiling", type=float, default=BUDGET_CEILING_USD, help="Hard USD spend ceiling for this run.")
    args = ap.parse_args()

    print(f"[judge] est. cost ~${estimate_cost(args.limit or 1000, args.model):.2f} "
          f"for {args.limit or 1000} examples on {args.model}", file=sys.stderr)

    n = judge_records(
        _read_input_records(Path(args.input)),
        out_path=args.out,
        model=args.model,
        rpm=args.rpm,
        limit=args.limit,
        ceiling_usd=args.ceiling,
    )
    print(f"[judge] wrote {n} new judgments to {args.out}")

    os._exit(0)  # Codespaces streaming/shutdown quirk (STATUS.md note)


if __name__ == "__main__":
    main()