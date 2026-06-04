---
id: 0026
title: Simplify split stratification key to commit type only
date: 2026-06-04
status: accepted
supersedes: [0025]
superseded_by: []
relates_to: []
tags: [data]
---

## Context
ADR 0025 introduced a per-language cap (6,000), a floor (500), and a
stratification key of "commit type × language with automatic type-only fallback
when any cell has fewer than 3 rows." In practice the cap already brings every
kept language down to at most 6,000 rows, which means language volumes are
balanced before the split step. Under that cap the type × language grid
consistently produced thin cells for minority commit types (e.g. `perf`,
`revert`) within smaller languages, so the fallback fired almost universally —
making the two-dimensional key dead code that added complexity without changing
the output.

## Decision
The stratification key is commit type only. The type × language grid and its
3-row cell detector are removed from `make_split()`. Cap (6,000) and floor
(500) are unchanged.

## Consequences
Every kept language receives a proportional eval slice automatically — the cap
guarantees it. The split implementation is simpler and the fallback branch is
gone. No change to dataset size or the cap/floor parameters.
