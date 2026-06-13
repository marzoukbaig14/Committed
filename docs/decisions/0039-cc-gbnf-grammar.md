---
id: 0039
title: Conventional Commits GBNF grammar for constrained decoding
date: 2026-06-11
status: accepted
supersedes: []
superseded_by: []
relates_to: [0009, 0017]
tags: [serving, eval]
---

## Context
ADR 0009 committed the project to constraining decoding with a GBNF grammar so
every generation is a well-formed Conventional Commits line. That decision did not
fix the concrete grammar. This record specifies it and the choices baked into it.
The grammar must match the normalized training targets (ADR 0017), or the constrained
output space would not align with what the model is trained to produce.

## Decision
The grammar lives at `src/committed/inference/grammar.gbnf` and constrains output to:

```
root        ::= type scope? ": " description
```

- **`type`** — the ten-code filter codebook:
  `feat | fix | refactor | docs | test | chore | perf | style | build | ci`.
  No `doc` alias (ADR 0017 normalizes `doc` → `docs`) and no `revert`.
- **`scope`** — optional; parentheses required when present; casing preserved
  (scopes are identifiers, per ADR 0017's normalization rules).
- **No breaking-change `!`** — ADR 0017 strips `!` from the normalized targets,
  so the grammar does not emit it.
- **`description`** — a single line with no leading or trailing whitespace and no
  trailing period; periods mid-description (e.g. `v2.0`) are allowed. Trailing
  punctuation is enforced here in the grammar, not in the prompt.

`revert` is excluded deliberately: a revert cannot be inferred from a diff alone
(it is git-history metadata), and ADR 0017 already drops revert commits from the
data, so the model never sees them as targets.

## Consequences
Every generation is valid-by-construction, which simplifies the prefix-classification
metric and all downstream parsing. Known limitation to carry forward: **the grammar
enforces format, not semantics.** It cannot catch thinking-mode leakage, hallucinated
or junk scopes, or a plausibly-shaped but wrong message — those are the judge's job
(ADRs 0027–0036). The grammar is versioned with the inference code; a change to the
type set or the description rule that alters behaviour is a new ADR, not an in-place edit.
