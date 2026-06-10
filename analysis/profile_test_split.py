from datasets import load_dataset
from collections import Counter
import re

ds = load_dataset("marzoukbaig14/committed-train", split="test")
print("n =", len(ds))
print("columns:", ds.column_names)
print("sample row:", ds[0])

type_re = re.compile(r"^([a-zA-Z]+)(\([^)]*\))?!?:")
def cc_type(msg):
    m = type_re.match(msg.strip())
    return m.group(1).lower() if m else "<unparsed>"

types = Counter(cc_type(r["message"]) for r in ds)
print("\ntype counts:")
for t, c in types.most_common():
    print(f"  {t:10s} {c:5d}  {c/len(ds)*100:4.1f}%")

lang_col = next((c for c in ds.column_names if "lang" in c.lower()), None)
if lang_col:
    langs = Counter(r[lang_col] for r in ds)
    print(f"\nlanguage ({lang_col}):")
    for l, c in langs.most_common(20):
        print(f"  {str(l):15s} {c:5d}  {c/len(ds)*100:4.1f}%")
else:
    print("\nno language column; columns:", ds.column_names)