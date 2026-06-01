import os
import re
from collections import Counter
from datasets import load_dataset

# Stream the full dataset one row at a time (no full download into RAM).
ds = load_dataset("JetBrains-Research/commit-chronicle", "default", split="train", streaming=True)

# The Conventional Commits regex locked in MASTER.md. We apply it to the SUBJECT
# LINE (first line) of each message. This is the same regex you'll hand-write into
# filter.py later — here we're only using it to measure, not to build the filter.
CC = re.compile(r"^(feat|fix|refactor|docs|test|chore|perf|style|build|ci)(\(.+\))?: .+")

MAX_SCAN = 80_000          # how many commits to look at (bounds runtime on a 10.7M-row stream)
languages = Counter()      # tally of the commit-level `language` field across everything scanned
py_single = 0              # count of Python + single-file commits (our candidate pool)
cc_match = 0               # of those, how many match the CC regex on the first line
multiline_cc = 0           # of CC matches, how many have a body (message spans >1 line)
line_counts = Counter()    # distribution of line counts among CC-matching commits
examples = []              # a few multi-line CC messages to eyeball the body content

for i, row in enumerate(ds):
    if i >= MAX_SCAN:
        break
    if i and i % 20_000 == 0:        # lightweight heartbeat so we know it's alive on a slow stream
        print(f"...scanned {i}")

    languages[row["language"]] += 1  # build the language histogram for the notebook question

    # Gate 1 + 2: Python language AND exactly one file changed (single-file).
    if row["language"] != "Python" or len(row["mods"]) != 1:
        continue
    py_single += 1

    msg = row["message"]
    if not msg:
        continue
    lines = msg.splitlines()         # split on newlines; lines[0] is the subject line
    first_line = lines[0]

    # Apply the locked CC regex to the SUBJECT LINE only.
    if CC.match(first_line):
        cc_match += 1
        line_counts[len(lines)] += 1
        if len(lines) > 1:           # this commit has a body we'd be dropping if we take line 1
            multiline_cc += 1
            if len(examples) < 8:    # keep a few to inspect what the dropped body actually contains
                examples.append(msg)

# ---- Report ----
print(f"\nScanned {min(i, MAX_SCAN)} commits.\n")

print("Top 12 languages seen (does 'Jupyter Notebook' show up as its own bucket?):")
for lang, n in languages.most_common(12):
    print(f"  {lang:<20} {n}")

print(f"\nPython single-file commits: {py_single}  ({py_single / max(i,1):.1%} of scanned)")
print(f"  of those, match CC regex on first line: {cc_match}  ({cc_match / max(py_single,1):.1%}  <- this is the CC match rate)")
print(f"  of CC matches, multi-line (have a body): {multiline_cc}  ({multiline_cc / max(cc_match,1):.1%})")

print(f"\nLine-count distribution among CC matches: {dict(sorted(line_counts.items()))}")

print("\nA few multi-line CC examples (is the body diff-derivable, or context the diff can't give?):")
for m in examples:
    print(f"  {m!r}")

os._exit(0)   # clean exit; avoids the cosmetic streaming shutdown error