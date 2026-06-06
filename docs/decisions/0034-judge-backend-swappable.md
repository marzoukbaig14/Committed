---
id: 0034
title: Make judge harness backend-swappable; Gemini default, Claude optional upgrade
date: 2026-06-06
status: accepted
supersedes: [0033]
superseded_by: []
relates_to: [0011, 0028, 0030]
tags: [eval, judge]
---

## Context
ADR 0033 was written against a stale handoff that assumed an API budget was
already secured, and prematurely promoted Claude Sonnet 4.6 to the primary judge
while superseding ADR 0011 (Gemini 2.5 Flash). The actual position is:
- No API budget exists yet (Northeastern subsidised-credit application is pending).
- For this bounded rubric task Gemini 2.5 Flash is expected to be adequate.
- The judge's trustworthiness is established by human-validation regardless of
  backend, so the backend is a swappable implementation detail, not a load-bearing
  quality decision.

ADR 0033 is therefore superseded by this record. ADR 0011 (Gemini as default)
stands and is restored to `accepted`.

## Decision
Build the judge harness backend-agnostic, sharing one prompt source
(`JUDGE_SYSTEM` + `build_judge_user` in `judge_prompt.py`):

- **Default / current backend:** Gemini 2.5 Flash (free, ADR 0011) in
  `judge_gemini.py`. No change to the active judge.
- **Optional upgrade backend:** Claude Sonnet 4.6 (`claude-sonnet-4-6`) in
  `judge.py`, with prompt caching on the fixed rubric, forced tool-use for
  structured output, and a hard per-run USD ceiling + output-token cap as cost
  guardrails. Available once API credits are secured; `anthropic` is an optional
  dependency, not installed by default.

Whichever backend runs is validated against the 50 human ratings; if both are
run, the better-correlating one is reported. The free Gemini default keeps the
free-infrastructure thesis intact.

If Claude is later promoted to the default judge, that change is a follow-up ADR
superseding 0011 and the README gains the paid-judge caveat then.

## Consequences
- ADR 0011 is unchanged; Gemini 2.5 Flash remains the default judge.
- The `anthropic` SDK and `ANTHROPIC_API_KEY` are optional — added only when
  adopting the Claude backend.
- MASTER.md: Evaluation stack notes the backend-swappable architecture; default
  remains `google-genai` / `gemini-2.5-flash` (ADR 0011); Claude backend noted as
  optional upgrade.
- MASTER.md Thesis: unchanged — default judge is free, free-infrastructure story
  holds.
- A secured API budget would also unblock v2 reasoning-trace distillation (per
  MASTER.md trigger); out of scope here.
