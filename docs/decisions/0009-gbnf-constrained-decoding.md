---
id: 0009
title: Constrain decoding to a Conventional Commits grammar (GBNF)
date: 2026-05-29
status: accepted
supersedes: []
superseded_by: []
relates_to: [0004, 0005]
tags: [serving, eval]
---

## Context
A small model frequently emits almost-valid output: the right idea in a malformed
shape. Guaranteeing well-formed Conventional Commits output is a strong, cheap
reliability signal.

## Decision
Constrain decoding with a GBNF grammar that encodes the Conventional Commits
format, run natively by llama.cpp, so every generation is valid by construction.

## Consequences
Output is always well-formed, which simplifies downstream parsing and the
prefix-classification metric. Cheap to run on llama.cpp (depends on the
GGUF/llama.cpp serving choice in 0005). Constrains the output space, which is
exactly right for this structured task.
