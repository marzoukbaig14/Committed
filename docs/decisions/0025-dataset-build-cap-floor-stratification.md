---
id: 0025
title: Set per-language cap (6k), floor (500), and stratification key for dataset build
date: 2026-06-04
status: superseded
supersedes: []
superseded_by: [0026]
relates_to: [0023, 0022]
tags: [data]
---

## Context
The full collection pass produced a 189,330-row pool covering ~85–90% of the
CommitChronicle train split. The true language mix (no longer a biased sample) is
TypeScript 32.8% + JavaScript 31.3% = ~64% combined, Python 8.8%, Go 8.0%, then a
long tail reaching single digits (R: 3, Scala: 22, Perl: 27). The skew is genuine —
Conventional Commits is a JS-ecosystem-heavy convention. But the project goal is a
language-general local tool with a fair per-language eval: an uncapped 64% JS/TS
training set would bias the model toward JS idioms (the majority class dominates the
loss) and make the cross-language claim hollow. The thin tail cannot survive a
stratified 90/5/5 split — languages with only a few dozen rows cannot contribute to
three separate splits.

## Decision
Three reversible build-time parameters govern dataset composition (all in
`src/committed/data/build.py`):

1. **Per-language cap = 6,000 rows.** Languages above 6k are randomly downsampled to
   6k; smaller languages are kept in full. Result: approximately 59k balanced rows,
   JS+TS each ≤6k (~20% combined rather than 64%).
2. **Language floor = 500 pool rows.** Languages with fewer than 500 rows in the pool
   after the full collection pass are dropped entirely. This clears R (3), Scala (22),
   Perl (27), Lua, Groovy, and Objective-C — each too thin for reliable eval.
3. **Stratification key = commit type × language.** The 90/5/5 train/val/eval split is
   stratified on both commit type and language over the kept-language pool. If any cell
   in that 2-D grid has fewer than 3 rows (detected automatically in `make_split`), the
   split falls back to stratification on commit type only. The final sizes are confirmed
   by `uv run python src/committed/data/build.py --dry-run` before publishing.

Cap and floor are arguments to `apply_cap_and_floor()`; they are not embedded in
`filter.py` (which remains a stateless per-record pass). Commit-type skew
(fix ≈ 51%) is deliberately not downsampled — it is recorded for eval interpretation
(prefix-accuracy baseline ≈ 51%) and handled implicitly via stratification.

## Consequences
Balanced enough to support per-language eval and a credible language-general claim,
at the cost of discarding majority-class JS/TS data — accepted, since marginal
examples from the majority class add little incremental training signal. Cap and floor
are reversible: adjusting them requires only a re-run of `build.py` against the
existing pool, not a re-filter of the raw data. The exact post-cap row counts and
split sizes are confirmed by the `--dry-run` before any Hub push.
