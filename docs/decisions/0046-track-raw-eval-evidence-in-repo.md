---
id: 0046
title: Track raw eval evidence in the repo
date: 2026-06-16
status: accepted
supersedes: []
superseded_by: []
relates_to: [0045]
tags: [eval, infra]
---

## Context
The reported before/after numbers are produced by the judge from the strata candidate files
and judge logs. If those files are gitignored, the numbers in the findings doc are not
independently inspectable — a reader has to re-run the eval to verify them. Keeping the
evidence alongside the report makes the findings auditable without re-running anything.

## Decision
Un-ignore strata candidates and judge logs for both the baseline and fine-tune runs.
The `.gitignore` rule `analysis/results/*.jsonl` is amended with explicit `!` exceptions
for the four primary evidence files:

- `analysis/results/baseline_strata442.jsonl`
- `analysis/results/baseline_judge_log.jsonl`
- `analysis/results/finetune_strata442.jsonl`
- `analysis/results/finetune_judge_log.jsonl`

Implemented in commit `32b545b`. This ADR records the decision retroactively.

## Consequences
- The numbers in `docs/eval/FINDINGS_v1_i1.md` are directly auditable from the committed
  evidence without re-running the judge.
- The four jsonl files add modest size to the repo (a few MB); acceptable for evidence files.
- Future eval iterations must explicitly un-ignore their evidence files in `.gitignore` to
  maintain this convention; the default remains to ignore `*.jsonl` in `analysis/results/`.
