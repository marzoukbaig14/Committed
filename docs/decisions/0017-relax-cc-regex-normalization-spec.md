---
id: 0017
title: Relax the Conventional Commits filter regex and define the normalization spec
date: 2026-06-02
status: accepted
supersedes: []
superseded_by: []
relates_to: [0009]
tags: [data]
---

## Context
The data plan specified a strict, case-sensitive Conventional Commits regex. A
full-scale scan (1,000,000 commits) showed it dropped valid commits over
capitalization and breaking-change markers (e.g. `Fix:`, `feat!:`) and the common
singular `doc:` variant. Separately, the normalizations used to build the training
target from a matched commit had never been formally specified, which is a
reproducibility gap.

## Decision
Matching: a commit qualifies if its subject line (first line) matches the
Conventional Commits types `feat|fix|refactor|docs|test|chore|perf|style|build|ci`
plus `doc` (treated as a `docs` alias), case-insensitively, with an optional
`(scope)`, an optional breaking-change `!`, and a required `: ` separator.
Deliberately excluded: `revert` (revert commits are dropped), non-standard types
(`deps`, `wip`, `release`), bracketed-type styles (`[Chore]`, deferred), and
subjects with no colon or a path prefix (left to a possible future classifier-based
harvest).

Normalizations applied to build the target from the matched subject line:
1. lowercase the type (`Fix:` -> `fix:`);
2. map `doc` -> `docs`;
3. strip the breaking-change `!` (`feat!:` -> `feat:`);
4. keep only the subject line (multi-line commits retained, body dropped);
5. strip surrounding whitespace;
6. strip a single trailing period;
7. leave scope casing unchanged;
8. leave description casing unchanged.

## Consequences
Recovers ~10% more matches than the strict regex without leaving the CC spec. All
targets stay consistent with the lowercase GBNF grammar, so ADR 0009 is unchanged:
the `!` is stripped rather than preserved, and breaking-change support is deferred.
Scope and description casing are left as-is to avoid mangling identifiers and
acronyms; the resulting description-casing inconsistency is an accepted v1
limitation, to be revisited if evaluation shows it matters. MASTER's Data Plan must
be updated to replace the regex and document this normalization spec.
