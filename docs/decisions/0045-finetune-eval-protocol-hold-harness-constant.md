---
id: 0045
title: "Fine-tune eval protocol: hold everything constant but the weights"
date: 2026-06-16
status: accepted
supersedes: []
superseded_by: []
relates_to: [0034, 0011, 0035, 0036, 0039, 0040, 0037]
tags: [eval]
---

## Context
A before/after comparison is only valid if the two runs differ in exactly one thing. The
fine-tune eval had to reuse the same sample, judge, rubric, grammar, and prompt as the
baseline run — any change to those would confound the comparison and make the delta
uninterpretable.

## Decision
The fine-tune eval holds the following identically to the baseline:

- **Sample** — same 442-row equal-allocation strata manifest (row indices from the test split).
- **Judge** — same Gemini 2.5 Flash backend (ADR 0034/0011).
- **Rubric** — same frozen rubric (ADR 0035/0036).
- **Grammar** — same GBNF grammar (ADR 0039).
- **Prompt** — same canonical zero-shot prompt (ADR 0040).
- **Weighting** — same deployment-reweighted headline metrics (ADR 0037).

Only the model weights differ between the two columns. Fine-tune candidates join baseline
refs by original test-split row index so paired comparisons are possible. Judge logs use
fresh output paths to avoid overwriting baseline evidence.

Any future model comparison (v1-i2, v2, etc.) must reuse this harness state unchanged
to remain a valid before/after against the same baseline.

## Consequences
- The comparison is interpretable: any delta in the metrics is attributable to fine-tuning
  and nothing else.
- The harness is now frozen as a protocol artifact, not just implementation. Changes to
  the judge, rubric, grammar, or prompt require a new baseline run before a new before/after
  can be claimed.
- The strata manifest is the canonical sample; resampling it for a future iteration would
  break comparability and requires a new ADR.
