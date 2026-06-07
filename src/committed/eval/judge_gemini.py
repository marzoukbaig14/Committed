"""
Committed — LLM-as-judge plumbing (Gemini 2.5 Flash).

SCAFFOLDING ONLY. This module is the API / throttling / parsing / logging layer for the
LLM-as-judge. The judge's *wording* — the four-axis rubric, axis questions, pass/fail
criteria, and per-axis reasoning steps — lives in `judge_prompt.py` and is authored from
`docs/eval/judge_rubric.md`. This file deliberately contains NO rubric content: it builds the
structured-output contract, calls the API, respects the free-tier limits, and writes a
resumable per-example log. (Working-norms split: rubric wording is hand-authored; plumbing is
scaffolded.)

Key design choices, and why:

- ONE call per message scores ALL FOUR axes. On the free tier this is 4x cheaper than one
  call per axis, and we always want the full per-axis vector (the composite never short-
  circuits on a gate failure — the vector is what diagnoses *which* capability regressed), so
  there is no benefit to splitting the call.

- The judge is REFERENCE-FREE. It scores a candidate message against the diff only; the
  dataset's gold `message` is never shown to it (plausibility design, ADR 0027). `run_eval.py`
  supplies the model's generated message as the candidate. The gold message is used elsewhere
  (BLEU / ROUGE-L in metrics.py), not here.

- Structured output enforces the reasoning protocol for free. Each axis field puts `rationale`
  before `label` in the schema, so the model must emit its reasoning before its verdict
  (reason-then-label). A shared `diff_summary` field comes first, so the model characterizes
  the diff before any axis judgment — the closest single-call approximation of "characterize
  the diff before reading the message." (True isolation would need two calls; not worth it on
  the free tier.)

- RESUMABLE by design. Gemini 2.5 Flash free tier is ~10 RPM with a LOW daily request cap
  (RPD), and Codespaces idle-suspends. The daily cap, not the per-minute rate, is usually the
  binding constraint for an eval of hundreds of examples. So results are appended to a JSONL
  log as each one completes, and on restart already-judged ids are skipped. A run can span
  multiple days and survive a suspend.

SDK: the `google-genai` package (`from google import genai`), ADR 0011. Reads `GEMINI_API_KEY`
from the environment (Codespaces secret; never hardcoded).
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Iterable, Iterator, Literal

from pydantic import BaseModel

# The google-genai SDK. `errors` carries APIError (with .code, e.g. 429 for rate/quota).
from google import genai
from google.genai import errors, types

# The rubric wording lives here (Zook's to author from docs/eval/judge_rubric.md). Shared
# interface with the Claude backend so the rubric is written ONCE: JUDGE_SYSTEM (the rubric text)
# + build_judge_user(diff, message) -> str (the per-call turn). The Claude backend uses them
# split (system cached / user variable); Gemini has no separate cached-system slot, so it just
# concatenates them into one prompt. Guarded so this module imports before judge_prompt.py exists.
try:
    from committed.eval.judge_prompt import JUDGE_SYSTEM, build_judge_user  # type: ignore
except Exception:  # pragma: no cover - scaffold guard
    JUDGE_SYSTEM = None  # type: ignore
    build_judge_user = None  # type: ignore


# --------------------------------------------------------------------------------------------
# Config (tune these; they are the only knobs)
# --------------------------------------------------------------------------------------------

# Pin a SPECIFIC Flash model id for reproducible eval (MASTER.md). "gemini-2.5-flash" tracks
# the current stable Flash; for byte-for-byte reproducibility, replace it with the dated
# snapshot id once confirmed in AI Studio (the eval is only reproducible against a fixed id).
JUDGE_MODEL = "gemini-2.5-flash"

# Free-tier rate limit for 2.5 Flash (2026): ~10 requests/minute. CHECK the live value in AI
# Studio — Google has been tightening free-tier quotas, and the DAILY cap (RPD) is usually the
# real constraint for a multi-hundred-example eval, not this per-minute number.
FREE_TIER_RPM = 10

# 429 backoff. A per-minute 429 clears within ~60s; a per-day 429 (quota exhausted) will not,
# so after MAX_RETRIES of 429 we treat it as daily-quota exhaustion and stop the batch
# gracefully (the resumable log lets you pick up tomorrow).
MAX_RETRIES = 5
INITIAL_BACKOFF_S = 2.0

# temperature=0 for a deterministic-as-possible judge (eval reproducibility).
TEMPERATURE = 0.0

# Fixed sampling seed -> more reproducible run-to-run output. Best-effort only: Gemini does not
# guarantee bit-identical results even at temp 0 + seed (server batching / routing), but this cuts
# most of the drift on borderline calls.
SEED = 7


# --------------------------------------------------------------------------------------------
# Structured-output schema (the contract the judge must fill)
#
# Field order matters: `rationale` precedes `label` so the model reasons before it labels, and
# `diff_summary` is first so the model characterizes the diff before judging any axis. The
# Literal types pin the allowed labels per the locked scales: all four axes are binary pass|fail.
# --------------------------------------------------------------------------------------------

class BinaryAxis(BaseModel):
    rationale: str
    label: Literal["pass", "fail"]


class JudgeResult(BaseModel):
    diff_summary: str          # "what the diff actually changes," in the judge's own words
    type_correctness: BinaryAxis
    faithfulness: BinaryAxis
    completeness: BinaryAxis
    specificity: BinaryAxis


class DailyQuotaExceeded(RuntimeError):
    """Raised when 429s persist past MAX_RETRIES — almost certainly the daily cap. The runner
    catches this and stops cleanly so the run can resume later."""


# --------------------------------------------------------------------------------------------
# Rate limiting
# --------------------------------------------------------------------------------------------

class RateLimiter:
    """Spaces calls at least 60/RPM seconds apart. Simple and good enough for a single-threaded
    eval loop; it does not model the daily cap (that surfaces as a persistent 429 instead)."""

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

# Per-MTok prices (USD) for cost logging. The numbers are tiny here, but logging them avoids surprises.
PRICES = {
    "gemini-2.5-flash": {"in": 0.30, "out": 2.50},
    "gemini-2.5-flash-lite": {"in": 0.10, "out": 0.40},
}


def _call_cost(model: str, usage) -> float:
    """USD for one call from Gemini usage_metadata. Returns 0.0 if usage is unavailable."""
    if usage is None:
        return 0.0
    p = PRICES.get(model, {"in": 0.30, "out": 2.50})
    pin = getattr(usage, "prompt_token_count", 0) or 0
    pout = getattr(usage, "candidates_token_count", 0) or 0
    return (pin * p["in"] + pout * p["out"]) / 1_000_000


def judge_one(client: genai.Client, diff: str, message: str, *, model: str = JUDGE_MODEL):
    """Score one (diff, candidate message) pair on all four axes. Returns (JudgeResult, usage).
    Retries 429s and transient 5xx (server overload) with exponential backoff + jitter; raises
    DailyQuotaExceeded if 429s persist (daily cap)."""
    if JUDGE_SYSTEM is None or build_judge_user is None:
        raise RuntimeError(
            "judge_prompt must expose JUDGE_SYSTEM (str, the rubric) and "
            "build_judge_user(diff, message) -> str."
        )

    # Gemini has no separate cached-system slot, so concatenate the shared rubric + per-call turn.
    prompt = JUDGE_SYSTEM + "\n\n" + build_judge_user(diff=diff, message=message)
    config = types.GenerateContentConfig(
        temperature=TEMPERATURE,
        seed=SEED,
        response_mime_type="application/json",
        response_schema=JudgeResult,  # forces valid JSON matching the schema above
    )

    delay = INITIAL_BACKOFF_S
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = client.models.generate_content(model=model, contents=prompt, config=config)
            # response.text is guaranteed valid JSON for the schema; validate into the model.
            return JudgeResult.model_validate_json(resp.text), getattr(resp, "usage_metadata", None)
        except errors.APIError as e:
            code = getattr(e, "code", None)
            # Retry two kinds of transient failure with the same backoff:
            #   429 = rate limit / RESOURCE_EXHAUSTED (per-minute throttle, or the daily cap)
            #   500/502/503/504 = server overload / "high demand" spikes — temporary
            transient_5xx = code in (500, 502, 503, 504)
            if (code == 429 or transient_5xx) and attempt < MAX_RETRIES:
                time.sleep(delay + random.uniform(0, delay * 0.25))
                delay *= 2
                continue
            if code == 429:
                # a 429 still failing past the backoff is almost certainly the daily cap
                raise DailyQuotaExceeded(str(e)) from e
            raise  # exhausted 5xx retries, or a genuinely non-transient error — surface it
    raise DailyQuotaExceeded("exhausted retries on 429")


# --------------------------------------------------------------------------------------------
# Resumable batch over records
# --------------------------------------------------------------------------------------------

def _load_done_ids(out_path: Path) -> set[str]:
    """Read ids already present in the JSONL log so a resumed run skips them."""
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
                continue  # tolerate a half-written trailing line
    return done


def judge_records(
    records: Iterable[dict],
    out_path: str | Path,
    *,
    model: str = JUDGE_MODEL,
    rpm: int = FREE_TIER_RPM,
    limit: int | None = None,
) -> int:
    """Judge an iterable of records, appending each result to a JSONL log.

    Each record is a dict with: 'id' (stable per-example id), 'diff', 'message' (the CANDIDATE
    message being judged — a model generation, not the gold reference). Returns the number of
    NEW judgments written this run. Resumable: already-logged ids are skipped; stops cleanly on
    DailyQuotaExceeded so it can be rerun to continue.
    """
    out_path = Path(out_path)
    done = _load_done_ids(out_path)
    limiter = RateLimiter(rpm)
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    written = 0
    total_cost = 0.0
    with out_path.open("a") as f:
        for rec in records:
            if limit is not None and written >= limit:
                break
            ex_id = str(rec["id"])
            if ex_id in done:
                continue

            limiter.wait()
            try:
                result, usage = judge_one(client, rec["diff"], rec["message"], model=model)
            except DailyQuotaExceeded:
                print(
                    f"[judge] daily quota likely exhausted after {written} new judgments; "
                    f"rerun to resume from the log at {out_path}",
                    file=sys.stderr,
                )
                break

            total_cost += _call_cost(model, usage)
            row = {
                "id": ex_id,
                "diff": rec["diff"],
                "message": rec["message"],
                "model": model,
                "ts": time.time(),
                "judgment": result.model_dump(),
                "usage": {
                    "prompt_tokens": getattr(usage, "prompt_token_count", None),
                    "output_tokens": getattr(usage, "candidates_token_count", None),
                } if usage is not None else None,
            }
            f.write(json.dumps(row) + "\n")
            f.flush()  # persist each result immediately so a suspend/crash loses nothing
            written += 1

    print(f"[judge] {written} new judgments this run, est. cost ${total_cost:.4f} ({model})",
          file=sys.stderr)
    return written


# --------------------------------------------------------------------------------------------
# CLI (standalone use / smoke testing). run_eval.py will call judge_records() directly with the
# Hub `test` split rows + model generations instead of reading a file.
# --------------------------------------------------------------------------------------------

def _read_input_records(path: Path) -> Iterator[dict]:
    """Read records from a JSONL file. Each line needs at least 'diff' and 'message'; if 'id'
    is missing it is assigned from the line index (stable for a fixed file)."""
    with path.open() as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            rec.setdefault("id", str(i))
            yield rec


def main() -> None:
    ap = argparse.ArgumentParser(description="Run the Gemini LLM-as-judge over a JSONL of (diff, message) records.")
    ap.add_argument("--input", required=True, help="JSONL with 'diff' and 'message' per line (message = candidate).")
    ap.add_argument("--out", required=True, help="JSONL log to append judgments to (resumable).")
    ap.add_argument("--model", default=JUDGE_MODEL, help="Gemini model id (pin a snapshot for reproducibility).")
    ap.add_argument("--rpm", type=int, default=FREE_TIER_RPM, help="Requests/minute throttle.")
    ap.add_argument("--limit", type=int, default=None, help="Max NEW examples to judge this run.")
    args = ap.parse_args()

    n = judge_records(
        _read_input_records(Path(args.input)),
        out_path=args.out,
        model=args.model,
        rpm=args.rpm,
        limit=args.limit,
    )
    print(f"[judge] wrote {n} new judgments to {args.out}")

    # Codespaces streaming/interpreter-shutdown quirk: guard the clean exit (STATUS.md note).
    os._exit(0)


if __name__ == "__main__":
    main()