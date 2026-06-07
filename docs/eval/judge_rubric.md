# Committed — LLM-as-Judge Rubric

**Status:** complete and locked. Four axes authored (`type_correctness`, `faithfulness`,
`completeness`, `specificity`), **all four scored binary `pass | fail`**; reasoning protocol and
composite decided. Faithfulness is a decomposed, atomic-per-claim precision check. Anchors are
stated as general principles without illustrative instances by design.
**Architecture:** ADR 0027 established the analytic per-axis rubric with plausibility-based
type-correctness. ADR 0028 set the four orthogonal axes (revising 0027: `scope_correctness` and
`conciseness` dropped, `faithfulness` and `completeness` added). ADR 0035 finalized the rubric —
all axes binary and faithfulness decomposed — superseding the per-axis-scales decision (0029) and
the completeness/faithfulness anchor definitions (0031).

This document is the human-readable specification for the semantic half of the eval. The
deterministic metrics (BLEU, ROUGE-L, prefix-classification accuracy) live in `metrics.py` and are
out of scope here. `judge_prompt.py` encodes the axis wording below and is the **operative**
artifact; this doc is the source of truth for *what* it encodes and *why*. The composite
(gate-then-grade) is **not** in the prompt — the judge scores the four axes independently and the
gating/aggregation happen in `run_eval.py`, so the composite section below describes
`run_eval.py`'s behavior, not the prompt's.

---

## The four axes (final, orthogonal by design)

| Axis | The one question it asks | Scale | Status |
|------|--------------------------|-------|--------|
| `type_correctness` | Is the chosen type *defensible* for this diff? | binary | **locked** |
| `faithfulness` | Is every claim the message *makes* **true** of the diff? | binary | **locked** |
| `completeness` | Is the primary + every materially **distinct** change *referenced*? | binary | **locked** |
| `specificity` | Is the message *concrete* enough to be informative? | binary | **locked** |

Orthogonality is the point. Faithfulness is **precision** over the message's claims (catches
over-claims — saying more, or other, than the diff does); completeness is **coverage** of the
diff's materially distinct changes (catches under-claims — omitting something a reader needs);
specificity asks only whether what the message says is concrete; type asks only whether the label
is defensible. Each axis owns exactly one question so the same defect isn't scored twice.

---

## Decisions captured here

| Decision | Status |
|----------|--------|
| Analytic per-axis rubric; plausibility-based type-correctness | logged — ADR 0027 |
| Four orthogonal axes (drop scope/conciseness; add faithfulness/completeness) | logged — ADR 0028 |
| Judge reasoning protocol (reason-then-label, structured fields, per-example logging) | logged — ADR 0030 |
| Gate-then-grade composite (no weights) | logged — ADR 0032 |
| Backend-swappable judge, Gemini 2.5 Flash default (extends ADR 0011) | logged — ADR 0034 |
| Per-axis scales | logged — ADR 0029 (superseded by 0035) |
| Axis anchor definitions | logged — ADR 0031 (completeness + faithfulness anchors superseded by 0035) |
| **Rubric finalization: all axes binary; faithfulness decomposed** | logged — ADR 0035 (supersedes 0029, 0031) |

> ADR numbers above are reconstructed from the session handoff. Before relying on them, run
> `ls docs/decisions/` and read the live ids off the filenames — the directory listing is the
> only authority for sequencing.

---

## Scoring scales — uniform binary (ADR 0035)

Every axis is `pass` / `fail`. The judgment on each is genuinely two-valued — accept as-is or
require a change:

- `type_correctness`: a type is defensible or it isn't.
- `faithfulness`: every claim clears its test or at least one doesn't.
- `completeness`: every materially distinct change is referenced or one is missing.
- `specificity`: the message is concrete or it's filler.

A `partial` bucket is phantom resolution that the judge and human raters fill inconsistently,
dragging down the judge-vs-human agreement that is the headline trust number for the eval.
`completeness` previously carried a 3-level `fail/partial/complete` scale; ADR 0035 collapsed it to
binary because the materially-distinct test (below) makes the underlying judgment two-valued —
every distinct change is referenced or it isn't — and the middle bucket cost agreement without
adding signal. (ADR 0035 is the authoritative record for this change.)

**Two consequences of going uniform binary:**

1. **No cross-scale normalization.** All axes share the `{0,1}` range, so the composite combines
   them directly — no per-axis remapping before the graded headline.
2. **One validation statistic.** Judge-vs-human agreement is Cohen's kappa (and/or raw percent
   agreement) on each of the four binary axes; `run_eval.py` emits it per axis. Report a
   run-to-run stability number (e.g. Krippendorff's α or percent agreement on a re-judged subset)
   alongside it, so single-sample judge wobble is measured rather than hidden.

---

## Judge reasoning protocol (applies to every axis)

- **Characterize the diff first, in the judge's own words, before reading the candidate message** —
  stops the judge from anchoring on the model's own commit message.
- **Reason first, label second — never label first.** A label emitted before the reasoning gets
  rationalized backward. Reasoning-then-label lets the verdict follow the evidence.
- **Rationale and label are separate output fields** (structured output), so the harness parses the
  label deterministically and stores the rationale alongside it.
- **Every per-example judgment is logged** (rationale + label, per axis), which makes the
  human-validation correlation debuggable rather than a bare number.
- **Axes are scored independently.** The judge is not told that faithfulness is a hard gate;
  telling it so could bias how it scores that axis. Gating lives in `run_eval.py`.

---

## `type_correctness`  (binary, locked)

**Scale:** binary — `pass` / `fail`. **Basis:** plausibility. The diff is the only ground truth;
there is no gold/reference type to match against.

### Axis question

> Reviewing this commit the way an experienced maintainer would, is the chosen Conventional Commits
> type one they'd accept for the changes in this diff — or would they make you change it before
> merging?

### Decision rule

`pass` if **no strictly better type exists** for this diff; `fail` if a strictly better type exists
or the type is unsupported by the diff. **"Strictly better" means only that the chosen type
*misrepresents* the change** — a type a reviewer would merely *prefer* is not strictly better.

### `pass`

A competent reviewer would accept the chosen type as-is, because it is among the most defensible
type(s) for what the diff actually does (no other type is strictly better). If several types are
equally defensible, the chosen one passes — "equally defensible" means no strictly better type
exists. Matching some conventional default is neither necessary nor sufficient.

### `fail`

The chosen type **misrepresents** the change, in one of two ways:

- **(a) Names a category the diff doesn't perform** — the type asserts a kind of change the diff
  does not actually contain.
- **(b) Suppresses a real downstream consequence** that the correct type would carry — e.g. a
  change that should drive a version bump labeled so it wouldn't.

An out-of-codebook, missing, or gibberish type also fails (grammar-constrained decoding should
prevent these). Crucially: if the chosen type is a defensible reading of the change and a reviewer
would merely *prefer* a different label, that is **not** strictly better and the type **passes**.
Two equally-defensible types never make either one strictly better.

### Reasoning steps (logged; rationale first, label second)

1. In one line, state what the diff actually changes — the judge's own words, from the diff, not
   the candidate message.
2. List the Conventional Commits types defensible for that change (often more than one).
3. Decide whether the chosen type *misrepresents* the change — names a category the diff doesn't
   perform, or suppresses a downstream consequence the correct type carries. A type a reviewer
   would merely prefer is not strictly better; only misrepresentation is. A defensible reading means
   no strictly better type exists.
4. Apply "would a reviewer make you change it?" → short rationale, then label.

---

## `faithfulness`  (binary, decomposed, locked)

**Scale:** binary — `pass` / `fail`. **Basis:** accuracy of the description, checked **one atomic
claim at a time**. Judge only the description (the text after the type) — the type prefix is judged
under `type_correctness`, so a wrong or questionable type never counts against this axis.

**Boundary:** faithfulness is **precision** — is what the message *says* true? It is explicitly
**not** coverage of the diff (that is completeness; do not import it here). A concrete-but-false
message is caught here, not by specificity.

### Method — decompose, then verify each claim

Break the description into its **atomic claims** (the smallest standalone assertions it makes) and
sort each into one of two kinds:

- **(a) a what-changed claim** — an assertion about what the commit does / modifies / adds /
  removes. It must be **true of the diff**.
- **(b) a rationale claim** — the "why" or intended purpose behind the change. The diff is not
  needed to prove it; it **passes unless the diff actively contradicts it**.

Then test every claim against the diff individually. Faithfulness is the **conjunction**: the
message is faithful only if every claim clears its own test. This is a deliberate deviation from
the textbook definition — only *intrinsic* hallucination (a rationale the diff contradicts) fails a
rationale claim; an unprovable-but-not-contradicted "why" passes.

### `pass`

Every what-changed claim is supported by the diff (nothing invented, mischaracterized, or
overstated), and no claim — rationale included — is contradicted by the diff. The message may be
terse or leave things out; faithfulness only asks whether each thing it *does* assert is true.

### `fail`

At least one claim fails its test — a what-changed claim names a change that isn't in the diff,
mischaracterizes what changed, or overstates its scope/impact; or any claim (what-changed or
rationale) is directly contradicted by the diff. A wrong type is not a faithfulness failure, and a
rationale that is merely unprovable but not contradicted is not one either.

### Reasoning steps (logged; rationale first, label second)

1. List what the diff actually changes, in the judge's own words.
2. Enumerate the description's atomic claims (ignore the type prefix); tag each as what-changed or
   rationale.
3. Verify each claim against the diff on its own: what-changed → supported by the diff? rationale →
   not contradicted by the diff?
4. Conjunction: every claim clears → `pass`; any single claim fails → `fail`.
5. Name the specific failing claim and why (unsupported what-changed, mischaracterization,
   overstatement, or contradicted rationale), then the label.

---

## `completeness`  (binary, locked)

**Scale:** binary — `pass` / `fail`. Coverage is two-valued: either the message references
everything a reader needs, or it leaves out something that matters.

**What counts as material:** a change is material only if it is a **distinct** change — to
behavior, interface, semantics, or dependencies — that a reader would need to know about as a
separate thing. **Supporting detail does not count**: the new imports a change requires, the
internal mechanics of how a named change works, the plumbing of a refactor — these implement or
enable a change the message *already names*, so omitting them is not an omission. Incidental edits
(formatting, comments, local renames) never count.

This axis is about **coverage only** — whether each material change is referenced, not whether the
reference is accurate (faithfulness) and not whether it is concrete (specificity). Do not
double-count a flaw already charged to another axis.

### Axis question

> Reading the message alone, would a reviewer know the primary change AND every materially distinct
> change — or would they be missing something that matters?

### `pass`

References the primary change and every materially distinct secondary change. The message may be
terse, and need not spell out imports, internal mechanics, or refactor plumbing for a change it has
already named. A message that names the single change but names it **vaguely** (e.g. "fix flapping
test" for a one-change diff) still passes here — its lack of concrete detail is charged to
specificity, not completeness. A reviewer reading message-then-diff wouldn't say "you left out
something that matters."

### `fail`

Leaves a material change uncovered — either it never references the primary change (a reader of the
message alone wouldn't know what the commit is fundamentally for, e.g. it describes only an
incidental edit), or it omits a materially distinct secondary change a reader would need. Whether
what the message *does* say is true is faithfulness, not completeness.

### Reasoning steps (logged; rationale first, label second)

1. List what the diff changes, tagging each as primary / materially-distinct-secondary /
   supporting-detail / incidental.
2. Is the primary change referenced at all (not replaced by an incidental edit)? If not → `fail`.
3. Is every materially distinct secondary change referenced? Supporting detail and incidental edits
   do not count, and a vague-but-present reference still counts as referenced.
4. Primary referenced and all materially distinct changes referenced → `pass`; any materially
   distinct change uncovered → `fail`.
5. Name what's missing (primary, or which distinct secondary change), then the label.

---

## `specificity`  (binary, locked)

**Scale:** binary — `pass` / `fail`. The message must be concrete enough to be informative. Judge
concreteness **only** — not whether the message is true (faithfulness) and not whether it is
complete (completeness). A concrete-but-false message still passes specificity.

### Axis question

> Does the message name the specific behavior or mechanism that changed — something beyond what the
> type and the touched files already imply — rather than generic filler that could describe almost
> any commit?

### `pass`

Identifies the concrete thing changed at a resolution that distinguishes this commit from a random
one. It tells you something you couldn't infer from the type and file paths alone.

### `fail`

Generic boilerplate that could describe almost any commit, or names only the area touched without
naming the change.

### Reasoning steps (logged; rationale first, label second)

1. Read the message on its face.
2. Could this exact wording plausibly describe many unrelated commits? If yes → filler.
3. Does it name a concrete behavior or mechanism, not just an area?
4. Concrete and discriminating → `pass`; generic → `fail`. Then the label.

(No diff check needed — specificity is about the message's resolution, not its accuracy.)

---

## Composite — gate-then-grade (no weights)

> Computed in `run_eval.py` from the four independent axis labels, not in the judge prompt.
> Treat `run_eval.py` as the operative source if this section and the code ever disagree.

Correctness is resolved before quality ever enters: if the message lies about the code, a reviewer
rejects it and never gets to "but is it specific enough?" That ordering is enforced by gating, not
by weighting — a weighted average would let high specificity buy back a correctness failure, which
is exactly the failure this structure exists to prevent.

**Hard gate — `faithfulness` (unconditional).** A `fail` fails the message outright, regardless of
every other axis. A tool whose entire value is trust cannot ship a false message.

**Priority order for the rest (lexicographic):** `type_correctness` → `completeness` →
`specificity`. Correctness (type) before quality (completeness, specificity).

**Type-gate knob:** `type_correctness` is the **top of the quality tier, not a hard gate**
(default). For a tool whose output a human reviews before committing, a mistyped-but-truthful, clear
message is mis-filed, not dangerous. Promote `type` to an unconditional gate only if Committed ever
drives automated releases, where a wrong type causes a wrong version bump.

### Primary metric — conjunctive pass-rate

A message **passes** iff it clears all four axes; the pass-rate over the eval set is the headline
"is this shippable" number. One binary per message, one rate across the set, zero weights. Now that
completeness is binary, "clears completeness" is simply `completeness == pass`.

### Always report the per-axis vector

Report the four per-axis pass-rates alongside the conjunctive number. That is the whole reason the
axes were split: the single number says the model regressed, the vector says which capability did.

### Optional graded headline (A/B and checkpoint ranking)

Faithfulness-gated; built additively over the binary axes, never by weighting:

```
score = 0                              if faithfulness fails
score = 1 + completeness + specificity otherwise
        completeness ∈ {0, 1}   (fail / pass)
        specificity  ∈ {0, 1}   (fail / pass)
→ score ∈ {0, 1, 2, 3}
```

(If the type-gate knob is turned on, `type` failing also forces `score = 0`.) Quality can never
compensate for a correctness failure: a gate failure is 0, and graded quality only exists above the
gate. This graded score is the sensitive instrument for baseline-vs-fine-tuned comparison and
checkpoint ranking; the conjunctive pass-rate is the shippability bar.