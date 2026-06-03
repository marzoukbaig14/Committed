---
id: 0020
title: Apply the message-length filter to the subject line only, with a ceiling and no floor
date: 2026-06-03
status: accepted
supersedes: []
superseded_by: []
relates_to: [0017]
tags: [data, filter]
---

## Context
MASTER's data plan specified a message-length bound of 5 to 200 characters, without
pinning whether it applies to the subject line or the full commit message. While
implementing the filter, three things became clear. First, the Conventional Commits
regex already requires a non-empty description after `type: `, so the shortest
possible match is about five characters (for example `ci: x`) — the lower bound is
redundant. Second, the bound should apply to the subject line, since the subject is
the training target after normalization (the body is dropped); checking the full
message would discard otherwise-good commits that simply have long bodies. Third, a
scan of subject lengths (median 45, max 355, with the bulk at or below 55) showed
that run-on outliers are rare.

## Decision
Filter on the subject line only, with a single upper ceiling of 200 characters and no
lower bound. The CC regex enforces the practical minimum; subjects over the ceiling
are dropped as malformed run-ons.

## Consequences
Negligible effect on yield — only rare run-on subjects are trimmed — and no good
commits are lost to long bodies. The filter is simpler. Updates MASTER's
"Message length: 5 to 200 characters" to a subject-only ceiling with no floor.
