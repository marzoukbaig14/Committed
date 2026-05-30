---
id: 0014
title: Abandon Project GitHub sync (org-blocked); manual STATUS.md continuity
date: 2026-05-30
status: accepted
supersedes: [0013]
superseded_by: []
relates_to: [0001]
tags: [infra]
---

## Context
ADR 0013 adopted STATUS.md + three-lane tracking and planned to connect the GitHub repo
to the Claude.ai Project knowledge for one-click "Sync now." On attempting it, the account
turned out to be inside a managed organization (public projects are disabled org-wide), and
the GitHub integration is disabled at the org level — a member cannot enable it. The sync
component of 0013 is therefore not implementable on this account.

0013 also recorded Claude Code as rejected because it "requires payment." That rationale was
imprecise: the org appears to provide a premium seat (a daily scheduled-runs quota, a Claude
Code feature, is visible), so Claude Code is likely available at no personal cost. It is
deferred by choice — manual work is preferred during the learning phase — not ruled out on cost.

## Decision
- Keep STATUS.md as the living state and the three-lane tracking rule (unchanged from 0013).
- Abandon the GitHub Project sync; it is blocked by org policy.
- Session continuity is by pasting STATUS.md at the start of a new chat; STATUS.md is kept
  short specifically so this is cheap.
- Claude Code is deferred, not rejected: available later for delegable plumbing once the
  learning phase ends, at no expected personal cost given the org seat.

## Consequences
Continuity depends only on what the org cannot switch off — the git repo, the Codespace, and
a short pasted status file — consistent with the project's reproducibility principle. No
connector, no payment, no admin action required. Trade-off: starting a fresh chat needs a
manual paste of a few seconds. Supersedes ADR 0013; extends ADR 0001.