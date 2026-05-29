---
id: 0001
title: Adopt ADR-based decision logging with a generator
date: 2026-05-29
status: accepted
supersedes: []
superseded_by: []
relates_to: []
tags: [infra, process]
---

## Context
The project will make many design and dev decisions over several weeks, often
across different sessions and agents. Git versions code well but does not capture
why a design choice was made, and those reasons are easy to lose. A prior project
used an append-only decision file and it made the work much easier to track.

## Decision
Adopt Architecture Decision Records: one markdown file per decision in
docs/decisions/, with YAML frontmatter. A script regenerates a human-readable log
and a Mermaid relationship tree from the records. Records are append-only; a
decision is changed by superseding it, not by deleting it.

## Consequences
Every significant decision is now traceable, and the tree shows how decisions
relate and evolve. It costs a small amount of bookkeeping per decision. It also
doubles as a portfolio signal of professional practice, and as a seed for a
possible standalone "decision control" tool later.
