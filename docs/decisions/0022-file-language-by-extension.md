---
id: 0022
title: Identify a commit's file language by file extension, not the per-repo language column
date: 2026-06-03
status: accepted
supersedes: []
superseded_by: []
relates_to: []
tags: [data, filter]
---

## Context
CommitChronicle's `language` field is assigned per repository, not per file. Polyglot
repositories — for example a Python backend with a TypeScript frontend — carry a
single language label, so a `language == "Python"` filter admits non-Python file
changes (TypeScript, JSON, YAML) from Python-labeled repos. A hand review of a
Python-filtered sample found roughly 85% of it was non-Python, dominated by one
React/TypeScript monorepo that CommitChronicle labels Python.

## Decision
Determine a commit's file language from the changed file's extension, checked against
the single modified file's path (`new_path`, falling back to `old_path`), rather than
trusting the per-repo `language` column. For a Python scope this is a `.py` check; the
same mechanism generalizes to a language-to-extension map when the language scope
broadens (see 0023).

## Consequences
Eliminates cross-language contamination in the dataset. Correctly lowers the yield —
the prior count was inflated by mislabeled files — which in turn revealed that the
Python-only dataset is far smaller than projected and motivated 0023. Adds a small
per-file extension check to the structural filters.
