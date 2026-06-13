# Committed — Status

_Living status. Update in the same commit as the work._
_Plan lives in ROADMAP.md; design in MASTER.md + docs/decisions/._

**Phase:** Eval design decisions locked (ADRs 0027–0035); judge harness implementation pending. Training not yet started.
**Calendar:** Day 9 (June 7, 2026)

## Done
- Setup: devcontainer + uv lockfile; CPU deps; 3 secrets injected; 15 smoke tests pass.
- Data inspection: CommitChronicle loaded/inspected; token distribution measured;
  exploration scripts in analysis/.
- Decision log: 40 ADRs total.
  - 0008 superseded by 0011 (judge: Haiku → Gemini Flash); 0013 superseded by 0014
    (Project sync abandoned, org-blocked; manual STATUS continuity).
  - 0012 = license redistribution; 0015 = Claude Code as decision-log agent;
    0016 = id-echo confirmation protocol.
  - 0017 = relax CC regex + normalization spec; 0018 = revised size target
    (superseded by 0023); 0019 = HPC cluster as primary training compute.
  - 0020 = subject-line ceiling, no floor; 0021 = detect bots by message pattern
    (author field anonymized); 0022 = language by file extension not per-repo column;
    0023 = expand scope Python-only → all CommitChronicle languages; 0024 = installable
    package, src-layout, hatchling build backend. MASTER.md propagated for all.
  - 0025 = dataset build parameters: per-language cap 6,000, floor 500, stratification
    by type × language (superseded by 0026); 0026 = stratification key simplified to
    commit-type only (type × language cells universally thin after per-language cap).
  - Eval design (0027–0036): 0027 = analytic per-axis rubric architecture; 0028 = four
    orthogonal axes (type_correctness, faithfulness, completeness, specificity); 0029 =
    per-axis scales (superseded by 0035); 0030 = judge reasoning protocol (diff-first,
    reason-then-label, structured output, no persona); 0031 = per-axis anchors (superseded
    by 0035); 0032 = gate-then-grade composite (faithfulness hard gate, conjunctive
    pass-rate headline, graded 1–3 for ranking); 0033 = stale record superseded by 0034;
    0034 = judge harness backend-swappable (Gemini 2.5 Flash default, Claude Sonnet 4.6
    optional upgrade); 0035 = rubric finalization: all axes binary, faithfulness
    decomposed into atomic per-claim precision (supersedes 0029 + 0031); 0036 =
    type_correctness bar tightened — only misrepresentation fails (wrong category or
    suppressed semver consequence); a merely-preferred alternative passes; 0037 =
    deployment-reweighted headline metrics — per-type metrics from the equal-allocation
    strata sample reweighted to the true test-split type distribution (~49% fix); sample
    numbers retained as diagnostics.
  - Baseline/inference (0038–0040): 0038 = pin baseline GGUF to ggml-org/Qwen3-1.7B-GGUF
    Q4_K_M (matches serving quant so before/after isolates fine-tuning; models/ gitignored
    cache); 0039 = concrete CC GBNF grammar (ten-type codebook, optional scope, no !,
    single-line no-trailing-period; enforces format not semantics); 0040 = single canonical
    zero-shot prompt across baseline/training/inference, near-raw Diff:\n{diff} format,
    enable_thinking=False to stop Qwen3 thinking leak.
- Filter logic: CC regex + normalization (ADR 0017), subject-line length ceiling
  (ADR 0020), bot detection by message pattern (ADR 0021), language by file extension
  (ADR 0022), single-file only, drop merge/revert. Spot-checked in
  analysis/spotcheck_filter.py; results in analysis/results/spotcheck.txt.
- Package: installable src-layout package (ADR 0024); pyproject.toml + uv.lock updated.
- Filter module: `src/committed/data/filter.py` — CC regex + normalization, token cap
  2048 (Qwen3-1.7B), language by file extension, single-file, bot/merge/revert detection.
  49/49 tests pass (test_filter.py + test_build.py).
- Build pipeline ran: `src/committed/data/build.py --cap 6000`
  - Raw pool: 189,330 rows → 57,969 after cap 6,000 / floor 500 (16 languages kept).
  - 6 languages hit cap (JavaScript, TypeScript, Java, Python, Go, Rust at 6,000 each).
  - Remaining: Shell 4,215 · C++ 3,753 · PHP 2,708 · C 2,407 · C# 2,146 · Swift 2,129
    · Kotlin 1,812 · Dart 1,370 · Ruby 750 · Elixir 679.
  - Commit-type mix: fix 48.9% · feat 13.3% · chore 10.3% · test 9.0% · refactor 8.7%
    · docs 4.3% · ci 2.3% · style 1.5% · build 1.0% · perf 0.7%.
  - Final splits: train 52,173 / val 2,898 / eval 2,898 (90/5/5, stratified by type).
- Dataset pushed to Hub: `marzoukbaig14/committed-train` — train + validation + test
  splits with auto-generated dataset card (composition tables, provenance, limitations).
- Analysis scripts: `analysis/collect_rows.py` (streamed CommitChronicle → raw pool),
  `analysis/pool_stats.py` (read-only pool inspector).
- Inference + eval-harness code (on main): `src/committed/inference/prompt.py` (canonical
  zero-shot prompt, ADR 0040), `grammar.gbnf` (CC GBNF, ADR 0039), `generate.py` (GGUF
  baseline generation, Q4_K_M pin per ADR 0038, enable_thinking=False render),
  `src/committed/eval/run_eval.py` (orchestrator: deterministic metrics + judge + composite
  + deployment reweighting per ADR 0037).

## In progress
- Eval harness implementation: `judge_prompt.py` and `docs/eval/judge_rubric.md` not yet
  synced to final rubric (ADR 0035). Decisions are locked; prompt authoring is owed.

## Next
- Write `judge_prompt.py` + sync `docs/eval/judge_rubric.md` to ADR 0035 rubric (core
  work: anchors, decomposed faithfulness prompt, type-bar wording).
- Write QLoRA training config (model: Qwen3-1.7B, library: Unsloth + TRL SFTTrainer,
  compute: HPC cluster per ADR 0019).
- First training run; push checkpoints to Hub.
- Run eval harness on base-model baseline + fine-tuned checkpoint.

## Key data findings (feed the filter + training)
- Raw pool: 189,330 rows from ~85-90% of CommitChronicle train split (streaming pass,
  not exhaustive). Balanced dataset: 57,969 rows across 16 languages.
- Final training set: 52,173 rows. Commit types heavily skewed toward `fix` (48.9%);
  a trivial always-predict-`fix` baseline scores ~49% prefix-accuracy — read results
  against that floor.
- Cap is in Qwen3-1.7B tokens. Python single-file diffs: med 165, p90 601, p95 906,
  p99 2834. Token cap set at 2048 (over-cap diffs dropped, not truncated).
  Messages tiny (p99 38 chars).
- ADR 0012: `repo` + `license` columns kept in every row; CommitChronicle paper cited
  in dataset card (arXiv 2308.07655); sensitive-data caveat carried forward.

## Quirks
- W&B web UI blocked on school wifi (DNS/filter); training is cloud-to-cloud and fine;
  view via hotspot (maybe it was ethernet thing).
- Streaming + interpreter shutdown can throw a cosmetic exit crash; guard exploration
  scripts with os._exit(0).
- "PyTorch not found" from transformers is expected in the CPU Codespace (tokenizer-only).
- Org disables connectors/integrations (no Project GitHub sync) and blocks W&B UI;
  continuity is by pasting this file, not syncing (ADR 0014).
- collect_rows.py scan covered ~85-90% of CommitChronicle train split (not a full pass);
  language mix is near-complete rather than exhaustive.
