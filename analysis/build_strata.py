"""
build_strata.py — Stratified eval sampler for the Committed baseline.

Draws a type-stratified ~442-row eval set from the committed-train test split:
  - any type with > FLOOR available is capped at FLOOR (fix/feat/chore/test/refactor/docs/ci -> 50)
  - any type at or below FLOOR is taken whole (style 43, build 28, perf 21)
Within a capped cell, rows are spread across languages (round-robin over the
extension-derived `language` column, ADR 0022) so no cell is single-language.

id = ORIGINAL test-split row index (the run_eval join key). The dataset is never
shuffled or re-indexed; only within-cell candidate order is shuffled (seeded).

Out:
  data/strata_ids.txt        one original-index id per line  -> generate.py --ids-file
  data/strata_manifest.json  per-cell counts, id->type/lang, + true full-split type counts
"""

import json, os, random, re
from collections import defaultdict, Counter
from datasets import load_dataset

SEED = 0
FLOOR = 50

def cc_type(msg):
    return msg.split("(")[0].split(":")[0]   # exact same as collect_rows.py

ds = load_dataset("marzoukbaig14/committed-train", split="test")
rng = random.Random(SEED)

# Bucket original indices by type. id = enumeration index = original row index.
by_type = defaultdict(list)               # type -> [(id, language), ...]
for idx, row in enumerate(ds):
    by_type[cc_type(row["message"])].append((idx, row["language"]))

def round_robin_by_language(rows, k):
    buckets = defaultdict(list)
    for idx, lang in rows:
        buckets[lang].append(idx)
    langs = sorted(buckets)               # deterministic order
    for lang in langs:
        rng.shuffle(buckets[lang])
    picked = []
    while len(picked) < k:
        progressed = False
        for lang in langs:
            if buckets[lang]:
                picked.append(buckets[lang].pop())
                progressed = True
                if len(picked) == k:
                    break
        if not progressed:
            break
    return picked

selected = []
manifest = {"seed": SEED, "floor": FLOOR,
            "true_type_counts": {t: len(v) for t, v in by_type.items()},
            "cells": {}, "rows": {}}

for t in sorted(by_type):
    rows = by_type[t]
    ids = round_robin_by_language(rows, FLOOR) if len(rows) > FLOOR else [i for i, _ in rows]
    selected.extend(ids)
    lang_of = {i: lang for i, lang in rows}
    manifest["cells"][t] = {"n": len(ids), "languages": dict(Counter(lang_of[i] for i in ids))}
    for i in ids:
        manifest["rows"][str(i)] = {"type": t, "language": lang_of[i]}

selected.sort()
os.makedirs("data", exist_ok=True)
with open("data/strata_ids.txt", "w") as f:
    f.write("\n".join(map(str, selected)) + "\n")
with open("data/strata_manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)

print(f"selected {len(selected)} rows (seed={SEED}, floor={FLOOR})\n")
print(f"{'type':10} {'n':>4}   languages")
for t in sorted(manifest["cells"], key=lambda x: -manifest["cells"][x]["n"]):
    c = manifest["cells"][t]
    mix = ", ".join(f"{k}:{v}" for k, v in sorted(c["languages"].items(), key=lambda kv: -kv[1]))
    print(f"{t:10} {c['n']:>4}   {mix}")
print("\nwrote data/strata_ids.txt and data/strata_manifest.json")