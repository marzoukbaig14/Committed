---
id: 0021
title: Detect bot commits by message pattern, since the author field is anonymized
date: 2026-06-03
status: accepted
supersedes: []
superseded_by: []
relates_to: []
tags: [data, filter]
---

## Context
The data plan calls for dropping bot commits (Dependabot, GitHub Actions, and
similar). The original assumption was author-based detection. Inspecting
CommitChronicle showed the `author` field is an anonymized integer id — there are no
names or emails — so author-based detection is impossible. CommitChronicle also
deliberately avoids restrictive filtering and did not strip bots upstream, so
removing them is our responsibility.

## Decision
Detect bots with a high-precision message-template regex: the dependency-bump pattern
`bump .+ from .+ to .+`, case-insensitive, matched anywhere in the subject so it also
catches CC-prefixed bumps such as `build(deps): bump ...`. Precision is favored over
recall. A stray bot commit diluted across tens of thousands of examples is harmless,
whereas a broad keyword list (matching bare "bump", "automated", or "ci:") would drop
legitimate human commits — including an entire valid CC type in the case of "ci:".
The structural filters (single-file plus the CC regex) already remove most bot noise;
this is targeted mop-up.

## Consequences
Catches CC-formatted dependency bumps that would otherwise pass, while accepting that
rare bot survivors remain (judged acceptable on the spot-check). No dependence on the
author field. Updates MASTER's bot-filter description to message-pattern detection.
