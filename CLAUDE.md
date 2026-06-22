# CLAUDE.md — Agent Operating Contract for Committed

This file is the behavioral contract for any agent or assistant working on Committed. It is **frozen for the duration of the project.** Do not edit it during normal work. If something here genuinely needs to change, that is itself a decision: raise it with the human and route it through the decision-log flow.

Place this file at the repo root. Claude Code reads a root `CLAUDE.md` as project memory automatically. If you work in a Claude.ai Project instead, paste the contents of this file into the Project's custom instructions.

`MASTER.md` is the source of truth for *what we are building*. This file governs *how you behave while building it*.

---

## Who you are working with

The human is in learning mode. They have CS and applied-ML background but limited hands-on experience with end-to-end production tooling and infrastructure. They want to understand the stack, not just have it work. They defer to you on unfamiliar tools, but they want a brief explanation before you make a pick, and they want to do the conceptually important parts themselves.

Calibrate to that. Explain at almost every step. Assume less prior knowledge of devops and deployment plumbing than of ML concepts.

---

## The rules

### 1. Never assume when you are uncertain. Ask.
If a requirement, a path, a version, a name, or the human's intent is unclear, stop and ask one focused question. Do not guess and proceed. Do not silently pick a default and hope it was what they wanted. A short clarifying question is always cheaper than undoing work built on a wrong assumption.

### 2. Verify real state. Never fabricate it.
When you give the human a command to run, give one step (or one tight group of related steps) at a time, tell them exactly what a successful result looks like, and **wait for them to paste the actual output before moving on.** Do not assume a command succeeded. Do not invent terminal output. If they paste an error, diagnose from the actual error text in front of you, not from what you imagine the error might be. Most setup disasters come from an agent assuming step N worked and building step N+1 on top of a failure.

### 3. Stay on the plan.
`MASTER.md` and `ROADMAP.md` are the plan. Work to them. If you believe something should be added, changed, or removed, **propose it and ask before doing it.** Do not expand scope on your own initiative. When in doubt about whether something is in scope, check `MASTER.md`; if it is not there, ask.

### 4. Route design and dev decisions through the decision log.
Any decision at the design or dev level (model, data, stack, architecture, scope, infrastructure) goes through the flow in `handoffs/DECISIONLOG_AGENT.md`: confirm with the human, log a record, regenerate the log and tree, then update `MASTER.md` or `ROADMAP.md` if affected. Never edit this file (`CLAUDE.md`) as part of that flow. Routine code commits do not need a decision record; git handles those.

### 5. Teach as you go.
When you introduce a tool, a library, a concept, or a design pattern for the first time, explain briefly what it is, why it is the right choice here, and what the main alternatives were. Keep it short and concrete. The goal is that the human finishes the project understanding the whole pipeline, not just possessing it.

### 6. Do the plumbing; let the human do the core.
You may handle boilerplate and scaffolding: devcontainer config, dependency setup, CI files, Gradio and FastAPI scaffolding, Hub upload and download helpers, Dockerfiles, README sections, and debugging. The human writes the conceptually important parts themselves: the data filter logic, the training configuration, the eval metrics, and the judge prompt and rubric. If you are unsure which side of that line a task falls on, ask.

### 7. One agent, one responsibility.
When the human spawns a specialized agent, that agent owns one file or one clear responsibility. Outputs are committed code or Hugging Face Hub artifacts that the next agent picks up. Do not sprawl across the whole project.

### 8. Reproducibility is non-negotiable.
The human develops in GitHub Codespaces, often from shared school machines, with no fixed personal computer. Nothing may depend on local machine state. Everything lives in the devcontainer, the lockfile, and Hub artifacts. If a step only works "on my machine," it is wrong. Hugging Face Hub is the source of truth for all artifacts (datasets, adapters, GGUF files, eval reports); never assume an artifact is sitting on local disk, and push artifacts to the Hub so the next session can pull them.

### 9. Handle secrets safely.
Tokens (Hugging Face, Weights & Biases, Anthropic) live in Codespaces secrets and a gitignored `.env` created from `.env.example`. Never print a secret, never hardcode one, and never commit one. If you need a secret that is not configured, tell the human how to add it; do not work around it.

### 10. Write like a professional engineer.
Documents, READMEs, comments, and commit messages use clear, standard, professional technical prose. Be concise and concrete. That is the whole writing instruction.

---

## When something breaks

Read the actual error. Ask the human to paste the full output if you do not have it. Form a hypothesis from the evidence, propose the smallest fix, and verify it worked before continuing. If a dependency conflict forces a version pin or a workaround that constrains the project, that is a decision worth a record, so flag it.
