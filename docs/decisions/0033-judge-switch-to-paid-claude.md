---
id: 0033
title: Switch the LLM-as-judge to a paid Claude model (Sonnet 4.6)
date: 2026-06-06
status: superseded
supersedes: [0011]
superseded_by: [0034]
relates_to: [0019, 0027, 0028, 0030]
tags: [eval, judge]
---

## Context
ADR 0011 chose free-tier Gemini 2.5 Flash as the judge *because there was no
API budget* — the paid judge was the last remaining cost against the
free-infrastructure thesis. A $500/month Claude budget now exists, removing that
constraint. For a judge whose human-correlation is the headline trust number, a
stronger reasoner is a genuine quality upgrade, and the analytic four-axis rubric
(ADRs 0028–0031) with its diff-first reasoning protocol (ADR 0030) rewards a more
capable model.

## Decision
The primary judge is **Claude Sonnet 4.6** (`claude-sonnet-4-6`), called via the
`anthropic` SDK with `ANTHROPIC_API_KEY`. Opus 4.8 (`claude-opus-4-8`) is an
option for the one-time human-validation run. Implementation specifics:

- Prompt caching on the fixed rubric (it is identical across every example).
- Structured output via forced tool-use, satisfying the separate-fields
  requirement of ADR 0030.
- Cost guardrails: a hard per-run USD ceiling and an output-token cap.

**The Gemini judge is retained as the documented free-tier fallback**
(`judge_gemini.py`); the harness judge backend is swappable. The free-infrastructure
thesis is preserved by the same precedent as ADR 0019 (free-tier reproducibility
kept while a paid resource accelerates the work): the shipped model, dataset,
serving, and demo remain entirely free — only eval *validation* optionally uses a
paid judge, and the eval is reproducible on the free fallback.

## Consequences
- Changes the locked tech stack in MASTER.md (Evaluation): judge SDK
  `google-genai` → `anthropic`; model `gemini-2.5-flash` → `claude-sonnet-4-6`,
  with free Gemini kept as the fallback.
- Cost at eval scale is ~$7–12 per 1,000 examples — negligible against the budget.
- The README's free-infrastructure claim gains an honest caveat: a paid judge is
  used for eval validation, with a documented free fallback; everything shipped
  stays free.
- The budget also unblocks v2 reasoning-trace distillation later (per the MASTER.md
  v2 trigger), which is out of scope for this decision.
- **Implementation follow-ups (core/plumbing, not part of this record):** add
  `ANTHROPIC_API_KEY` to `.env.example` and Codespaces secrets; add an
  anthropic-auth smoke test; implement the swappable judge backend
  (`judge.py` / `judge_gemini.py`).
