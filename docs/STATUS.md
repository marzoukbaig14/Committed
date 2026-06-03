# Committed — Status

_Living status. Update in the same commit as the work._
_Plan lives in ROADMAP.md; design in MASTER.md + docs/decisions/._

**Phase:** Data — filter written and spot-checked; full build pass next
**Calendar:** Day ? (June 3, 2026)

## Done
- Setup: devcontainer + uv lockfile; CPU deps; 3 secrets injected; 15 smoke tests pass.
- Data inspection: CommitChronicle loaded/inspected; token distribution measured;
  exploration scripts in analysis/.
- Decision log: 24 ADRs total.
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
- Filter logic: CC regex + normalization (ADR 0017), subject-line length ceiling
  (ADR 0020), bot detection by message pattern (ADR 0021), language by file extension
  (ADR 0022), single-file only, drop merge/revert. Spot-checked in
  analysis/spotcheck_filter.py; results in analysis/results/spotcheck.txt.
- Package: installable src-layout package (ADR 0024); pyproject.toml + uv.lock updated.

## In progress
- Full filter build pass over all CommitChronicle languages (analysis/count_filtered.py);
  actual dataset size to be derived from results.

## Next
- Derive final dataset size from build pass.
- 90/5/5 split stratified by commit type and language, or capped per language (ADR 0023).
- Push committed-train dataset + dataset card to Hub.

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
