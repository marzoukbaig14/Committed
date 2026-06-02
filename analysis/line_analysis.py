import os
import re
import sys
import random
from collections import Counter
from datasets import load_dataset

import matplotlib
matplotlib.use("Agg")          # headless backend: render figures to a file, no display needed (Codespaces has none)
import matplotlib.pyplot as plt

# Where to save results (relative to repo root, where you run this). These runs are slow,
# so we persist both the numbers and the figure to re-read later without re-scanning.
RESULTS_DIR = "analysis/results"
os.makedirs(RESULTS_DIR, exist_ok=True)

# Stream the full dataset one row at a time (no full download into RAM).
ds = load_dataset("JetBrains-Research/commit-chronicle", "default", split="train", streaming=True)

# The format we filter for. CC types per the spec; 'update'/'add'/'remove' are NOT CC types.
TYPES = "feat|fix|refactor|docs|test|chore|perf|style|build|ci"
STRICT  = re.compile(rf"^({TYPES})(\([^)]+\))?: .+")                    # the originally locked regex
RELAXED = re.compile(rf"^({TYPES})(\([^)]+\))?!?: .+", re.IGNORECASE)   # case-insensitive + breaking-change '!'

MAX_SCAN = 1_000_000           # None = scan the FULL dataset.
K        = 25                  # how many non-matching subjects to sample for reading

languages      = Counter()
py_single      = 0
strict_hit     = 0
relaxed_hit    = 0
nonmatch_count = 0
short_nonmatch = 0             # non-matchers with a <15-char subject: a rough junk proxy
reservoir      = []            # representative sample of non-matching subjects (reservoir sampling)

random.seed(0)                 # fixed seed -> reproducible sample across re-runs
total_seen = 0
for row in ds:
    if MAX_SCAN is not None and total_seen >= MAX_SCAN:
        break
    total_seen += 1
    if total_seen % 500_000 == 0:                  # heartbeat so we know it's alive on the long stream
        print(f"...scanned {total_seen:,}")

    languages[row["language"]] += 1

    # Gate 1 + 2: Python language AND exactly one file changed.
    if row["language"] != "Python" or len(row["mods"]) != 1:
        continue
    py_single += 1

    msg = row["message"]
    if not msg:
        continue
    first_line = msg.splitlines()[0].lstrip()      # subject line; lstrip guards against stray leading whitespace

    is_relaxed = bool(RELAXED.match(first_line))
    strict_hit  += bool(STRICT.match(first_line))
    relaxed_hit += is_relaxed

    if not is_relaxed:                             # the "98%" we want to READ
        nonmatch_count += 1
        if len(first_line) < 15:
            short_nonmatch += 1
        # Reservoir sampling: K uniformly-random items from a stream of unknown length, in one pass.
        if len(reservoir) < K:
            reservoir.append(first_line)
        else:
            j = random.randint(0, nonmatch_count - 1)
            if j < K:
                reservoir[j] = first_line

# Build the report once, then both print it and write it to disk.
report = []
report.append(f"Scanned {total_seen:,} commits.\n")
report.append("Top 12 languages:")
for lang, n in languages.most_common(12):
    report.append(f"  {lang:<20} {n:,}")
report.append("")
report.append(f"Python single-file commits: {py_single:,}  ({py_single/total_seen:.1%} of scanned)")
report.append(f"  STRICT  CC match (as locked):            {strict_hit:,}  ({strict_hit/max(py_single,1):.2%})")
report.append(f"  RELAXED CC match (case-insensitive + !):  {relaxed_hit:,}  ({relaxed_hit/max(py_single,1):.2%})")
report.append(f"  recovery from relaxing:                   +{relaxed_hit - strict_hit:,}")
report.append("")
report.append(f"Non-matching Python single-file subjects: {nonmatch_count:,}")
report.append(f"  very short (<15 chars, likely junk):     {short_nonmatch:,}  ({short_nonmatch/max(nonmatch_count,1):.1%})")
report.append("")
report.append(f"{K} random non-matchers to READ -- good-but-unformatted, or junk?")
for s in reservoir:
    report.append(f"  {s!r}")

text = "\n".join(report)
print("\n" + text)

# Persist the text report so the numbers survive without re-scanning.
with open(f"{RESULTS_DIR}/scan_full.txt", "w") as f:
    f.write(text + "\n")

# Persist the language histogram as a figure (mirrors Day-2's token_distribution.png).
top    = languages.most_common(12)
names  = [t[0] for t in top][::-1]     # reverse so the largest bar sits at the top
counts = [t[1] for t in top][::-1]
plt.figure(figsize=(8, 5))
bars = plt.barh(names, counts)
for i, name in enumerate(names):
    if name == "Python":
        bars[i].set_color("#185FA5")   # highlight our target language
plt.xlabel("commits in sample")
plt.title("CommitChronicle language distribution")
plt.tight_layout()
plt.savefig(f"{RESULTS_DIR}/language_distribution.png", dpi=120)

print(f"\nSaved: {RESULTS_DIR}/scan_full.txt and {RESULTS_DIR}/language_distribution.png")

sys.stdout.flush()             # make sure the printed report lands before the hard exit
os._exit(0)                    # clean exit; avoids the cosmetic streaming shutdown error