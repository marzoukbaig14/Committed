# Committed — Status

_Living status. Update in the same commit as the work._
_Plan lives in ROADMAP.md; design in MASTER.md + docs/decisions/._

**Head:** ddb56d1
**Phase:** Data — inspection done, filter logic next
**Calendar:** Day 2 (May 30, 2026), running ahead of schedule

## Done
- Setup: devcontainer + uv lockfile; CPU deps; 3 secrets injected; 15 smoke tests pass.
- Decision log: 14 ADRs (0011 -> 0008 and 0013 -> 0014 supersedes; 0012 = license redistribution; 0014 = Project sync abandoned, org-blocked, manual STATUS continuity).
- Data inspection: CommitChronicle loaded/inspected; token distribution measured; exploration in notebooks/.
- Decision log: 16 ADRs (0011 -> 0008 and 0013 -> 0014 supersedes; 0012 = license redistribution; 0014 = Project sync abandoned, org-blocked; 0015 = adopt Claude Code as decision-log agent; 0016 = id-echo confirmation protocol for decision-log changes).

## In progress
- (nothing active)

## Next
- Day 3: write src/committed/data/filter.py — CC regex, message length 5-200, single-file only,
  Python only, drop merge/revert/bot commits, apply token cap. First measure the CC match rate
  on a 5-10k sample, then pick the cap.
- Day 4: full filter pass, 90/5/5 split stratified by commit type, push committed-train + dataset card.

## Key data findings (feed the filter)
- Cap is in Qwen3-1.7B tokens. Python single-file diffs: med 165, p90 601, p95 906, p99 2834.
  Cap candidate band ~600-900. Messages tiny (p99 38).
- Python single-file ~8% of commits -> ~600k candidates in train; 30-50k target feasible if CC rate holds.
- ADR 0012: filter MUST keep `repo` + `license` columns; cite CommitChronicle + paper (arXiv 2308.07655)
  in the dataset card; carry the sensitive-data note forward.

## Quirks
- W&B web UI blocked on school wifi (DNS/filter); training is cloud-to-cloud and fine; view via hotspot (maybe it was ethernet thing).
- Streaming + interpreter shutdown can throw a cosmetic exit crash; guard exploration scripts with os._exit(0).
- "PyTorch not found" from transformers is expected in the CPU Codespace (tokenizer-only).
- Org disables connectors/integrations (no Project GitHub sync) and blocks W&B UI; continuity is by pasting this file, not syncing (ADR 0014).