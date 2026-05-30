---
id: 0013
title: Adopt STATUS.md, three-lane doc tracking, and GitHub-synced Project knowledge
date: 2026-05-30
status: accepted
supersedes: []
superseded_by: []
relates_to: [0001]
tags: [infra]
---

## Context
Project state was tracked by re-uploading governance docs (MASTER.md, DECISION_LOG.md)
into the Claude.ai Project knowledge by hand, plus a separate rolling state note pasted at
the start of each session. This kept two parallel copies of the truth — the git repo and
the Project snapshots — in manual sync, which was slow and error-prone.

## Decision
1. `docs/STATUS.md` is the living state (head, phase, done / in-progress / next, key
   findings, quirks), updated in the same commit as the work it describes. It replaces the
   separate rolling note.
2. `ROADMAP.md` is the forward plan; edited only when the plan itself changes, not to mark
   daily progress.
3. `MASTER.md` and ADRs change only through the decision-log flow.
4. Connect the GitHub repo to the Project's knowledge so a single "Sync now" replaces
   per-file uploads.
Alternative considered: using Claude Code to automate the ADR/log mechanics. Rejected
because it requires a paid subscription or API billing, which conflicts with the project's
free-infrastructure constraint.

## Consequences
Progress tracking becomes a one-line STATUS.md edit folded into each work commit; git
history plus STATUS carry progress instead of hand-maintained roadmap day-markers. Session
start drops to push plus one "Sync now." The repo stays the single source of truth and the
Project knowledge is a synced view of it. Trade-off: the Project sync is still manual (no
auto-sync on push), so a session can start stale if "Sync now" is skipped. Extends ADR 0001.