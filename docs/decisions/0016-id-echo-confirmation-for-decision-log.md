---
id: 0016
title: Require id-echo confirmation before agent decision-log changes
date: 2026-05-31
status: accepted
supersedes: []
superseded_by: []
relates_to: [0001, 0015]
tags: [infra]
---

## Context
ADR 0015 adopted Claude Code as the decision-log agent. To stop the agent from acting on a
misunderstanding and creating or editing the wrong record, decision-log changes need an explicit
human confirmation gate. A static password or initials would be typed reflexively and would not
verify the specific change is correct; echoing the ADR id forces the human to check which record
is being touched.

## Decision
Before creating, editing, or committing any decision-log change, the agent must (1) present a
change preview (id, title, status, supersedes/relates_to, one-line decision; for an edit the exact
file and field changes; and the commit message), (2) write nothing and run no git until the human
replies "CONFIRM <id>" matching the preview's id, treating any reply without the matching id as not
confirmed, and (3) ask one clarifying question if anything is ambiguous rather than guessing. The
protocol is recorded in handoffs/DECISIONLOG_AGENT.md and layers on top of Claude Code's built-in
per-edit diff approval.

## Consequences
Decision-log changes now require an id-matched confirmation, making a wrong-record change hard to
trigger by accident and easy to catch. Adds a small deliberate step to each ADR action. Does not
affect CLAUDE.md (frozen; rules 1 and 4 already require confirm-before-acting) or MASTER (product
design). Relates to ADR 0015 (the agent it governs) and ADR 0001.
