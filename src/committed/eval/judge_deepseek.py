"""
Committed — LLM-as-judge plumbing (DeepSeek, OpenAI-compatible API).

SCAFFOLDING ONLY, same split as judge_gemini.py: this file is the API / throttling /
parsing / logging layer. The judge's *wording* — the four-axis rubric — lives in
`judge_prompt.py` (JUDGE_SYSTEM + build_judge_user) and is imported UNCHANGED, so the
DeepSeek judge applies the identical rubric the Gemini judge did. The only thing that
differs from judge_gemini.py is the model behind the call.

Why this backend exists (ADR 0050): the Gemini judge's prepaid credits were depleted
mid-eval (v2-i1 baseline arm stopped at 35/442). DeepSeek is pay-as-you-go and ~10-50x
cheaper, so the eval is re-run on DeepSeek. This breaks byte-for-byte comparability with
v1's Gemini-judged numbers, so ALL arms (0.6B + 1.7B) are re-judged on DeepSeek for an
internally consistent comparison; the Gemini numbers become a superseded reference.

Structured output: DeepSeek exposes OpenAI's `response_format={"type": "json_object"}`,
which guarantees syntactically valid JSON but does NOT enforce a schema (unlike Gemini's
response_schema). So we (a) keep the rubric frozen, (b) append a FORMAT envelope here that
restates the exact JSON shape and contains the literal word "json" (DeepSeek requires it
for json mode), and (c) validate the returned JSON into the same JudgeResult model. A
response that doesn't validate is retried, then surfaced.

SDK: the `openai` package pointed at https://api.deepseek.com. Reads DEEPSEEK_API_KEY from
the environment (never hardcoded).
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

from pydantic import BaseModel, ValidationError

# OpenAI-compatible client (DeepSeek). Imported at module top because run_eval.py imports
# this module lazily — only when --backend deepseek is selected — so it never burdens the
# Gemini/Claude paths.
from openai import OpenAI
from openai import APIError, APIStatusError, APIConnectionError, RateLimitError

# The rubric wording — imported UNCHANGED from the shared prompt module. Guarded so the
# module still imports if judge_prompt is absent (mirrors judge_gemini.py).
try:
    from committed.eval.judge_prompt import JUDGE_SYSTEM, build_judge_user  # type: ignore
except Exception:  # pragma: no cover - scaffold guard
    JUDGE_SYSTEM = None  # type: ignore
    build_judge_user = None  # type: ignore


# --------------------------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------------------------

# Pin the DeepSeek model. "deepseek-chat" is the stable non-reasoning chat model (DeepSeek-V3
# line). For byte-for-byte reproducibility, pin a dated snapshot if/when DeepSeek exposes one.
JUDGE_MODEL = "deepseek-chat"
BASE_URL = "https://api.deepseek.com"

# DeepSeek is generally lenient on rate; 60/min is a safe single-threaded default. Override
# via run_eval --rpm. (Kept as a knob to be polite, not because a low cap is expected.)
DEFAULT_RPM = 60

MAX_RETRIES = 5
INITIAL_BACKOFF_S = 2.0

# temperature=0 for a deterministic-as-possible judge (eval reproducibility). Same best-effort
# caveat as Gemini: the server does not guarantee bit-identical output even at temp 0.
TEMPERATURE = 0.0


# --------------------------------------------------------------------------------------------
# Structured-output schema — IDENTICAL to judge_gemini.py (redefined here, not imported, so
# this backend has no dependency on google-genai). Field order documents reason-before-label.
# --------------------------------------------------------------------------------------------

class BinaryAxis(BaseModel):
    rationale: str
    label: Literal["pass", "fail"]


class JudgeResult(BaseModel):
    diff_summary: str
    type_correctness: BinaryAxis
    faithfulness: BinaryAxis
    completeness: BinaryAxis
    specificity: BinaryAxis


class BalanceExhausted(RuntimeError):
    """Raised when DeepSeek reports an insufficient-balance (402) error. The runner catches
    this and stops cleanly so the run resumes after a top-up — the DeepSeek analogue of
    judge_gemini.DailyQuotaExceeded."""


# FORMAT envelope (plumbing, NOT rubric): restates the exact JSON contract for DeepSeek's
# json_object mode. Contains the literal word "json" as that mode requires. The field names,
# nesting, and labels match JudgeResult exactly.
FORMAT_INSTRUCTION = (
    "Return ONLY a single json object, no prose or code fences, with exactly this shape:\n"
    "{\n"
    '  "diff_summary": "<what the diff changes, in your own words>",\n'
    '  "type_correctness": {"rationale": "<reasoning>", "label": "pass" | "fail"},\n'
    '  "faithfulness":     {"rationale": "<reasoning>", "label": "pass" | "fail"},\n'
    '  "completeness":     {"rationale": "<reasoning>", "label": "pass" | "fail"},\n'
    '  "specificity":      {"rationale": "<reasoning>", "label": "pass" | "fail"}\n'
    "}\n"
    "Every label must be exactly \"pass\" or \"fail\"."
)


# --------------------------------------------------------------------------------------------
# Rate limiting (identical to judge_gemini.RateLimiter)
# --------------------------------------------------------------------------------------------

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
# Cost logging — DeepSeek prices (USD per MTok). deepseek-chat bills cache-hit vs cache-miss
# input separately, and the usage object reports both, so we cost them precisely. Prices as
# published 2026; update if DeepSeek changes them. Logged only, never authoritative billing.
# --------------------------------------------------------------------------------------------

PRICES = {
    "deepseek-chat": {"in_hit": 0.07, "in_miss": 0.27, "out": 1.10},
    "deepseek-reasoner": {"in_hit": 0.14, "in_miss": 0.55, "out": 2.19},
}


def _call_cost(model: str, usage) -> float:
    """USD for one call from the OpenAI-compatible usage object. Uses DeepSeek's
    prompt_cache_hit_tokens / prompt_cache_miss_tokens when present; falls back to charging
    all prompt tokens at the cache-miss rate."""
    if usage is None:
        return 0.0
    p = PRICES.get(model, PRICES["deepseek-chat"])
    out = getattr(usage, "completion_tokens", 0) or 0
    hit = getattr(usage, "prompt_cache_hit_tokens", None)
    miss = getattr(usage, "prompt_cache_miss_tokens", None)
    if hit is None and miss is None:
        prompt = getattr(usage, "prompt_tokens", 0) or 0
        return (prompt * p["in_miss"] + out * p["out"]) / 1_000_000
    return ((hit or 0) * p["in_hit"] + (miss or 0) * p["in_miss"] + out * p["out"]) / 1_000_000


# --------------------------------------------------------------------------------------------
# Single judgment
# --------------------------------------------------------------------------------------------

def _is_insufficient_balance(e: Exception) -> bool:
    """DeepSeek signals a depleted balance with HTTP 402 (Insufficient Balance)."""
    code = getattr(e, "status_code", None)
    if code == 402:
        return True
    return "insufficient balance" in str(e).lower()


def _strip_fences(text: str) -> str:
    """Defensive cleanup: some models wrap JSON in ```json ... ``` despite json_object mode."""
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[-1] if "\n" in t else t
        if t.endswith("```"):
            t = t[: t.rfind("```")]
    return t.strip()


def judge_one(client: OpenAI, diff: str, message: str, *, model: str = JUDGE_MODEL):
    """Score one (diff, candidate message) pair on all four axes. Returns (JudgeResult, usage).
    Retries transient errors (429/5xx/connection) and JSON-validation misses with exponential
    backoff; raises BalanceExhausted on a 402 so the runner can stop and resume after top-up.

    JSON-miss retries ESCALATE the temperature: at temperature=0 the model is deterministic, so a
    malformed generation would repeat identically on every retry. Bumping temperature lets a retry
    actually resample into valid JSON (the eval stays temp=0 for the first, normal attempt)."""
    if JUDGE_SYSTEM is None or build_judge_user is None:
        raise RuntimeError(
            "judge_prompt must expose JUDGE_SYSTEM (str, the rubric) and "
            "build_judge_user(diff, message) -> str."
        )

    # System = the frozen rubric (also the cache prefix DeepSeek dedupes across calls).
    # User = the per-call diff/message turn + the JSON FORMAT envelope (plumbing).
    user_turn = build_judge_user(diff=diff, message=message) + "\n\n" + FORMAT_INSTRUCTION
    messages = [
        {"role": "system", "content": JUDGE_SYSTEM},
        {"role": "user", "content": user_turn},
    ]

    delay = INITIAL_BACKOFF_S
    last_validation_err: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            temp = TEMPERATURE if attempt == 0 else min(0.2 * (attempt + 1), 0.8)
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temp,
                response_format={"type": "json_object"},
            )
            text = _strip_fences(resp.choices[0].message.content)
            try:
                return JudgeResult.model_validate_json(text), getattr(resp, "usage", None)
            except (ValidationError, ValueError) as ve:
                # json mode guarantees valid JSON but not our schema; retry a malformed shape.
                last_validation_err = ve
                if attempt < MAX_RETRIES:
                    time.sleep(delay + random.uniform(0, delay * 0.25))
                    delay *= 2
                    continue
                raise
        except (RateLimitError, APIConnectionError) as e:
            if attempt < MAX_RETRIES:
                time.sleep(delay + random.uniform(0, delay * 0.25))
                delay *= 2
                continue
            raise
        except APIStatusError as e:
            if _is_insufficient_balance(e):
                raise BalanceExhausted(str(e)) from e
            transient_5xx = getattr(e, "status_code", None) in (500, 502, 503, 504)
            if transient_5xx and attempt < MAX_RETRIES:
                time.sleep(delay + random.uniform(0, delay * 0.25))
                delay *= 2
                continue
            raise
    # only reached if the final retry was a validation miss
    raise last_validation_err if last_validation_err else RuntimeError("judge_one: retries exhausted")


# --------------------------------------------------------------------------------------------
# Resumable batch over records — identical contract/log format to judge_gemini.judge_records
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
    rpm: int = DEFAULT_RPM,
    limit: int | None = None,
) -> int:
    """Judge an iterable of records, appending each result to a JSONL log. Same record/log
    contract as judge_gemini.judge_records, so run_eval.py and the aggregation are unchanged.
    Resumable: already-logged ids are skipped; stops cleanly on BalanceExhausted."""
    out_path = Path(out_path)
    done = _load_done_ids(out_path)
    limiter = RateLimiter(rpm)
    client = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"], base_url=BASE_URL)

    written = 0
    skipped = 0
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
            except BalanceExhausted:
                print(
                    f"[judge:deepseek] insufficient balance after {written} new judgments; "
                    f"top up and rerun to resume from the log at {out_path}",
                    file=sys.stderr,
                )
                break
            except Exception as e:
                # One bad example (e.g. the model never returns schema-valid JSON even after
                # temperature-escalated retries) must not kill the batch. Log and skip; a rerun
                # retries skipped ids since they were never written to the log.
                skipped += 1
                print(f"[judge:deepseek] skipped id {ex_id} after retries: "
                      f"{type(e).__name__}: {str(e)[:120]}", file=sys.stderr)
                continue

            total_cost += _call_cost(model, usage)
            row = {
                "id": ex_id,
                "diff": rec["diff"],
                "message": rec["message"],
                "model": model,
                "ts": time.time(),
                "judgment": result.model_dump(),
                "usage": {
                    "prompt_tokens": getattr(usage, "prompt_tokens", None),
                    "output_tokens": getattr(usage, "completion_tokens", None),
                    "cache_hit_tokens": getattr(usage, "prompt_cache_hit_tokens", None),
                    "cache_miss_tokens": getattr(usage, "prompt_cache_miss_tokens", None),
                } if usage is not None else None,
            }
            f.write(json.dumps(row) + "\n")
            f.flush()
            written += 1

    print(f"[judge:deepseek] {written} new judgments this run "
          f"({skipped} skipped), est. cost ${total_cost:.4f} ({model})", file=sys.stderr)
    return written


# --------------------------------------------------------------------------------------------
# CLI (standalone smoke testing). run_eval.py calls judge_records() directly.
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
    ap = argparse.ArgumentParser(description="Run the DeepSeek LLM-as-judge over a JSONL of (diff, message) records.")
    ap.add_argument("--input", required=True, help="JSONL with 'diff' and 'message' per line (message = candidate).")
    ap.add_argument("--out", required=True, help="JSONL log to append judgments to (resumable).")
    ap.add_argument("--model", default=JUDGE_MODEL, help="DeepSeek model id.")
    ap.add_argument("--rpm", type=int, default=DEFAULT_RPM, help="Requests/minute throttle.")
    ap.add_argument("--limit", type=int, default=None, help="Max NEW examples to judge this run.")
    args = ap.parse_args()

    n = judge_records(
        _read_input_records(Path(args.input)),
        out_path=args.out,
        model=args.model,
        rpm=args.rpm,
        limit=args.limit,
    )
    print(f"[judge:deepseek] wrote {n} new judgments to {args.out}")
    os._exit(0)  # match judge_gemini: guard against interpreter-shutdown streaming quirk


if __name__ == "__main__":
    main()
