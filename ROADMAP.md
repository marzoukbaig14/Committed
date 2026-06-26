# Committed — Roadmap

_Phase-based. Progress log reflects what actually happened (git-verified).
Future phases are projected from observed velocity. Update this file when a phase closes._

---

## Progress Log

### May 29 — Scaffolding ✓

First session. Covered more ground than planned.

- Repository created. Decision-log system bootstrapped: `scripts/build_decision_log.py`,
  `docs/decisions/TEMPLATE.md`, ADRs 0001–0009 (adopt ADR logging, positioning reframe,
  Qwen3-1.7B, production serving in v1, llama.cpp + GGUF, CPU/GPU dep split, devcontainer,
  judge selection, GBNF decoding).
- `devcontainer.json` created and updated; uv project initialized with ruff + pytest.
- CPU dependency group added (14 libraries, ADR 0006); GPU `train` group declared but not
  installed in the CPU container.
- ADR 0010: `uv sync` in devcontainer post-create. ADR 0011: judge switched from paid
  Anthropic Haiku to free Gemini 2.5 Flash.
- README, MASTER.md, ROADMAP.md committed. Two real bugs caught and fixed in the generator
  (YAML octal parsing, filename-to-id derivation).
- **Carried to next session:** CLAUDE.md, START_HERE.md, handoffs/ not yet committed.

---

### May 30 — Environment + Data Inspection ✓

- Committed CLAUDE.md, START_HERE.md, handoffs/SETUP_AGENT.md, handoffs/DECISIONLOG_AGENT.md.
  ROADMAP updated to reflect actual pace.
- `.env.example` added; 15 smoke tests written covering library imports + service auth
  (HF, W&B, Gemini). All pass.
- Token-length exploration of CommitChronicle: `diff_token_dist.py` and `explore_data.py`;
  token distribution plot produced. Confirmed Python single-file diffs: median 165 tokens,
  p90 601, p95 906, p99 2834.
- ADR 0012: redistribute filtered dataset under source license terms.
- ADR 0013: adopt STATUS.md + three-lane tracking. ADR 0014 supersedes it same session
  (GitHub Project sync blocked by org; continuity is manual STATUS paste).

---

### May 31 — Process Tooling ✓

Lighter session; process-layer decisions.

- ADR 0015: adopt Claude Code as the decision-log agent.
- ADR 0016: id-echo confirmation protocol (agent must echo id + decision statement and wait
  for `CONFIRM <id>` before writing any ADR). Handoff doc updated.
- STATUS.md housekeeping (drop churning Head field, fix calendar).

---

### June 1 — Exploration ✓

- Reorganized notebook scripts into `analysis/` with results subdirectory.
- `analysis/inspect_messages.py`: message-length and format distribution.
- `analysis/line_analysis.py`: diff line-count distributions; full-scan results and language
  distribution PNG produced and committed.

---

### June 2 — Filter Design ✓

Key architectural decisions for the filter, locking the dataset spec.

- ADR 0017: relax CC regex + define normalization spec (lowercase type, `doc→docs`, strip `!`,
  subject only, trim, strip one trailing period).
- ADR 0018: revised dataset size target (scope initially Python-only; 20–30k raw projected).
- ADR 0019: adopt HPC cluster as primary training compute (Colab as fallback only).
- Full CommitChronicle scan run: `analysis/results/scan_full.txt` shows per-language breakdown
  and actual yield. Language distribution plot committed.

---

### June 3 — Filter Implementation ✓

Core work: the filter is written, tested, and validated.

- ADRs 0020–0024 logged and MASTER.md propagated:
  - 0020: subject-line length ceiling (5–200 chars), no floor.
  - 0021: detect bots by message pattern (author field anonymized in CC data anyway).
  - 0022: language by file extension only — per-repo language attribute mislabels polyglot repos.
  - 0023: expand scope from Python-only to all CommitChronicle languages (scope expansion driven
    by ADR 0022 finding that Python-only yield was overprojected).
  - 0024: installable package, src-layout, hatchling build backend.
- `committed` installable package created: `src/committed/__init__.py`, `pyproject.toml` updated.
- `analysis/spotcheck_filter.py` written; 40 real examples eyeballed; results in
  `analysis/results/spotcheck.txt` (707 lines).
- `tests/test_filter.py` expanded to cover normalization, bot detection, CC matching,
  file-language mapping, structural filters, and `build_row()`.
- STATUS.md updated through ADR 0024.

---

### June 4 — Dataset Build + Publish ✓

Data phase closed. First Hub artifact live.

- ADR 0025: dataset build parameters — per-language cap 6,000, floor 500, 90/5/5 split
  stratified by commit type × language.
- ADR 0026 supersedes 0025 same session: stratification key simplified to commit type only.
  Per-language cap makes the type × language grid universally thin; type-only fallback was
  firing on every language, so the grid was removed.
- `src/committed/data/filter.py` committed to the package (was previously untracked).
- `src/committed/data/build.py`: applies cap/floor, produces 90/5/5 JSONL splits.
- `src/committed/data/push.py`: loads splits, auto-generates dataset card with composition
  tables, pushes to Hub.
- `analysis/collect_rows.py`: full streaming pass over CommitChronicle train split.
- `analysis/pool_stats.py`: read-only pool inspector (percentile tables, histograms).
- 49/49 tests pass (`test_filter.py` + `test_build.py`).
- **Build ran:**
  - Raw pool: 189,330 rows (from ~85–90% of CommitChronicle train split)
  - After cap 6,000 / floor 500: 57,969 rows, 16 languages
  - Final splits: train 52,173 · val 2,898 · eval 2,898
- **Dataset pushed:** `marzoukbaig14/committed-train` — train + validation + test splits
  with full dataset card.

---

## Velocity

| Session | Date | Phase output |
|---------|------|--------------|
| 1 | May 29 | ADR system + devcontainer + dependencies + planning docs |
| 2 | May 30 | Env complete + data inspected + smoke tests green |
| 3 | May 31 | Process ADRs |
| 4 | June 1 | Exploration scripts + reorganization |
| 5 | June 2 | Filter design decisions (3 ADRs) + full scan |
| 6 | June 3 | Filter written + tested + spotchecked + package |
| 7 | June 4 | Build pipeline + 49 tests + dataset on Hub |

**Observed rate:** 7 sessions → data phase complete (Setup through Publish).
**Slippage vs. original plan:** data took 7 sessions vs. 4 planned. Drivers: scope
expansion to all languages (ADR 0023), 26 design decisions instead of expected ~12,
package scaffolding overhead. Core coding sessions (June 3, June 4) hit ~1 major
deliverable each — consistent with original throughput estimate.

**Projection basis:** complex phases (Training, Evaluation) estimated at 2–3 sessions;
simpler wiring phases (Serving, Demo) at 1–2 sessions. Session = one focused working
block (~2–4 hours of active output).

---

## Remaining Phases

### Phase: Training

**Goal:** First fine-tuned adapter on the Hub with a W&B run attached.

Tasks (human-owned: config values and judgment calls):
- Write training config in `configs/`: LoRA rank, alpha, learning rate, sequence length
  (set from June 2 token distribution), batch size tuned to available GPU VRAM.
- Set up HPC cluster environment: authenticate to HF + W&B, install `train` dep group
  (`uv sync --group train`), confirm GPU visible, run minimal import check.
- Fire first QLoRA training run via vanilla `transformers` + PEFT + TRL `SFTTrainer` on
  `marzoukbaig14/committed-train`. Watch W&B loss curve live.
- Push adapter checkpoints to Hub every N steps (ephemeral compute — Hub is the only
  persistent storage).
- Pull best checkpoint; run quick sanity inference.

Inputs: `marzoukbaig14/committed-train` (done).
Outputs: `marzoukbaig14/committed-qwen3-1.7b-lora` adapter on Hub + W&B run URL.
**Estimated: 2–3 sessions (~June 5–7).**

---

### Phase: Evaluation

**Goal:** All five metrics on fine-tune vs. baseline, judge validated against 50 human ratings.

Tasks (human-owned: judge rubric, human ratings):
- Draft Gemini judge prompt + rubric: type-correctness, specificity, scope-correctness,
  conciseness. Rubric must be concrete enough to produce consistent scores.
- Write eval harness: `src/committed/eval/metrics.py` (BLEU, ROUGE-L, prefix-classification
  accuracy), `src/committed/eval/judge.py` (Gemini API + free-tier throttling + 429 backoff),
  `src/committed/eval/run_eval.py`.
- Run baseline: base Qwen3-1.7B (no fine-tune) on the eval split. Record all five metrics.
  This is the before number.
- Hand-rate 50 examples against your rubric. Compute judge-vs-human correlation.
  This correlation is the headline trust metric for the judge.
- Run fine-tune eval; compare all metrics against baseline.

Inputs: adapter checkpoint + `eval` split (2,898 rows).
Outputs: eval report pushed to Hub; judge-vs-human correlation documented.
**Estimated: 2–3 sessions (~June 8–10).**

---

### Phase: Serving

**Goal:** Docker image that runs the model offline with grammar-constrained output.

Tasks:
- Quantize adapter-merged checkpoint to GGUF (Q4_K_M and Q8_0).
- Write GBNF grammar file for valid Conventional Commits output (type, optional scope,
  optional `!`, `: `, subject — all validated by grammar at decode time).
- Wrap llama.cpp in a FastAPI endpoint: POST `{diff}` → `{message}`.
- Write Dockerfile; verify cold-start latency and tokens/sec on CPU.
- Run throughput benchmarks; document in README.

Inputs: GGUF file on Hub.
Outputs: Docker image + GGUF artifact on Hub + benchmark numbers.
**Estimated: 2–3 sessions (~June 11–13).**

---

### Phase: Demo + Ship

**Goal:** Live Gradio demo on HF Spaces; v1 complete.

Tasks:
- Build Gradio interface: diff text input → generated CC message output.
- Deploy to HF Spaces (CPU tier, calls the FastAPI endpoint or runs llama.cpp directly).
- Write final README sections: eval results table, demo link, how to reproduce.
- Final model card and dataset card review.

Inputs: serving layer done.
Outputs: live Spaces demo; v1 declared complete.
**Estimated: 1–2 sessions (~June 14–15).**

---

## v1 Completion Projection

Assuming ~1 session/day with current pace:

```
June 5-7   Training phase
June 8-10  Evaluation phase
June 11-13 Serving phase
June 14-15 Demo + Ship
```

**v1 projected complete: ~June 15, 2026.**
Original estimate was "2–3 weeks from May 29" → June 12–19. Projection is on the near
end of that range because data phase is done and the remaining phases have clearer scope.

---

## v2 (after v1 ships)

Reasoning-trace distillation: augment the dataset with synthetic `<think>` traces
generated by a capable LLM; fine-tune a second time on trace + message pairs; expose
reasoning in the Gradio demo. Requires a separate ADR and compute allocation.

---

## Phase Map

| Phase | What happens | Status |
|-------|--------------|--------|
| Setup | Decision log, environment, accounts, secrets. | ✓ Done (May 29–30) |
| Data | Load, inspect, filter, split, publish. | ✓ Done (June 1–4) |
| Eval design | Judge prompt + rubric, eval harness, 50 human ratings. | Researching — reviewing industry practices for eval criteria and hand-grading before writing rubric. |
| Baseline | Run base Qwen3-1.7B on the eval split; record all five metrics. | ⬜ After eval design |
| Train v1 | QLoRA via vanilla transformers + PEFT + TRL SFTTrainer on HPC, iterate, push adapters, log to W&B. | ⬜ After baseline |
| Final eval | Full eval on fine-tune vs. baseline; judge-vs-human correlation; stretch ablations if time. | ⬜ After training |
| Serve | Merge adapter, quantize to GGUF, GBNF grammar, FastAPI endpoint, Docker, benchmarks. | ⬜ After final eval |
| Ship | Gradio demo on Spaces, final README, model card + dataset card review. | ⬜ End of v1 (~June 15) |
| v2 (later) | Reasoning-trace distillation; with-vs-without ablation. | ⬜ After v1 ships |

_Routine code commits go through git.
Anything that changes design, stack, scope, or infrastructure goes through the decision-log flow._
