# Committed — Start Here

This is the map. If you (or an agent) are new to this project, read this first, then read `MASTER.md`.

Committed is a small language model fine-tuned to write Conventional Commits messages from code diffs. It runs locally, so your code never leaves your machine, and it is built and deployed end to end on free infrastructure. The point of the project is to demonstrate a complete, production-grade applied-ML pipeline: data curation, parameter-efficient fine-tuning, rigorous multi-metric evaluation, and a real serving and deployment layer.

## The documents and what each one is for

| File | What it is | Changes? |
|------|------------|----------|
| `START_HERE.md` | This map. | Rarely. |
| `CLAUDE.md` | The behavioral contract every agent follows. How agents work with the human: ask before assuming, teach as they go, stay on the plan, route decisions through the log. | **Frozen at project start.** Do not edit during the project. |
| `MASTER.md` | The single source of truth for the design: thesis, scope of v1/v2/v3, the full locked tech stack, architecture, data plan, training plan, serving plan, eval plan. | Yes, but only through the decision-log flow. |
| `ROADMAP.md` | The next seven days in detail, plus the broader phase map. | Yes, as work progresses. |
| `handoffs/SETUP_AGENT.md` | Brief for the agent that builds the dev environment and infrastructure. No application code. Its job ends when the environment is reproducible and every service authenticates. | Stable. |
| `handoffs/DECISIONLOG_AGENT.md` | Brief for the agent that runs the decision-logging system, plus the full design of that system (record format, generator script, the confirm-then-log protocol). | Stable. |
| `docs/decisions/*.md` | The decision records (ADRs). One file per significant design or dev decision. Append-only in spirit: you never delete a record, you supersede it. | Grows over time. |
| `docs/DECISION_LOG.md` | Human-readable table of all decisions. **Generated.** | Auto, never by hand. |
| `docs/decision-tree.md` | A Mermaid diagram showing how decisions relate and supersede each other. **Generated.** | Auto, never by hand. |

## The one rule that keeps this clean

**`CLAUDE.md` is frozen. Everything in `MASTER.md` and `ROADMAP.md` can change, but only through the decision-log flow:** an agent confirms the change with the human, logs a decision record, regenerates the log and tree, then updates the affected document. That way the repo always tells the true story of how the project evolved, and you can walk any decision back to understand what changed and why.

Code is versioned in git as usual. The decision log is for the design and dev choices that git does not capture well: why we picked this model, why we split the dependencies this way, why we reframed the project. Two different kinds of history, kept separately on purpose.

## Order of operations

1. Stand up the decision-logging system (so it captures everything from here on, including the environment setup itself).
2. Build the environment and infrastructure (the setup agent).
3. Start the data work.

See `ROADMAP.md` for the day-by-day version.