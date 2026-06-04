# Committed — Status

_Living status. Update in the same commit as the work._
_Plan lives in ROADMAP.md; design in MASTER.md + docs/decisions/._

**Phase:** Data — full pipeline committed (filter, build, push); collect_rows data pass pending
**Calendar:** Day 7 (June 4, 2026)

## Done
- Setup: devcontainer + uv lockfile; CPU deps; 3 secrets injected; 15 smoke tests pass.
- Data inspection: CommitChronicle loaded/inspected; token distribution measured;
  exploration scripts in analysis/.
- Decision log: 26 ADRs total.
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
- Filter logic: CC regex + normalization (ADR 0017), subject-line length ceiling
  (ADR 0020), bot detection by message pattern (ADR 0021), language by file extension
  (ADR 0022), single-file only, drop merge/revert. Spot-checked in
  analysis/spotcheck_filter.py; results in analysis/results/spotcheck.txt.
- Package: installable src-layout package (ADR 0024); pyproject.toml + uv.lock updated.
- Filter module: `src/committed/data/filter.py` committed as installed package module.
  Implements all filter rules: CC regex + normalization (ADR 0017), token cap 2048
  (Qwen3-1.7B), language by file extension (ADR 0022), single-file, bot/merge/revert
  detection. `tests/test_filter.py` covers it.
- Build pipeline: `src/committed/data/build.py` — applies per-language cap 6,000 /
  floor 500, produces 90/5/5 train/val/eval JSONL splits stratified by commit type only
  (ADR 0026). `tests/test_build.py` added.
- Analysis scripts: `analysis/collect_rows.py` streams full CommitChronicle train split,
  applies filter, writes `data/committed_raw.jsonl` incrementally (unbalanced raw pool).
  `analysis/pool_stats.py` is a read-only inspector (percentile tables, histograms) for
  any JSONL pool file.
- Hub publish script: `src/committed/data/push.py` loads train/val/eval splits, auto-
  generates composition tables (language mix, commit-type distribution), builds dataset
  card, and pushes to `marzoukbaig14/committed-train`.

## In progress
- Running `analysis/collect_rows.py` to stream CommitChronicle → `data/committed_raw.jsonl`
  (unbalanced raw pool). Pipeline code is complete and committed; data pass not yet executed.

## Next
- Run `analysis/collect_rows.py` → `data/committed_raw.jsonl` (raw pool).
- Inspect pool with `analysis/pool_stats.py`; confirm size and distributions.
- Run `src/committed/data/build.py` → `data/train.jsonl`, `val.jsonl`, `eval.jsonl`.
- Push to Hub via `src/committed/data/push.py` → `marzoukbaig14/committed-train`.

## Key data findings (feed the filter)
- Cap is in Qwen3-1.7B tokens. Python single-file diffs: med 165, p90 601, p95 906,
  p99 2834. Cap candidate band ~600-900. Messages tiny (p99 38).
- Scope expanded to all CommitChronicle languages (ADR 0023); earlier Python-only
  20–30k raw / 15–25k usable projection (ADR 0018) was inflated by per-repo language
  mislabeling (ADR 0022). Size re-derived after build pass.
- ADR 0012: filter MUST keep `repo` + `license` columns; cite CommitChronicle + paper
  (arXiv 2308.07655) in the dataset card; carry the sensitive-data note forward.

## Quirks
- W&B web UI blocked on school wifi (DNS/filter); training is cloud-to-cloud and fine;
  view via hotspot (maybe it was ethernet thing).
- Streaming + interpreter shutdown can throw a cosmetic exit crash; guard exploration
  scripts with os._exit(0).
- "PyTorch not found" from transformers is expected in the CPU Codespace (tokenizer-only).
- Org disables connectors/integrations (no Project GitHub sync) and blocks W&B UI;
  continuity is by pasting this file, not syncing (ADR 0014).
