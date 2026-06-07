# Committed — LLM-as-Judge Rubric

**Status:** complete. Four axes authored & locked (`type_correctness`, `faithfulness`,
`completeness`, `specificity`); scales, reasoning protocol, and composite all decided. Anchors
are stated as general principles without illustrative instances by design.
**Architecture:** ADR 0027 (analytic per-axis rubric, plausibility-based type-correctness).
This revises 0027's original four dimensions — `scope_correctness` and `conciseness` are
dropped; `faithfulness` and `completeness` are added — so 0027 needs an amending/superseding
record (see the ADR handoff).

This document is the human-readable specification for the semantic half of the eval. The
deterministic metrics (BLEU, ROUGE-L, prefix-classification accuracy) live in `metrics.py`
and are out of scope here. `judge_prompt.py` encodes the wording below; this doc is the
source of truth for *what* it encodes and *why*.

---

## The four axes (final, orthogonal by design)

| Axis | The one question it asks | Scale | Status |
|------|--------------------------|-------|--------|
| `type_correctness` | Is the chosen type *defensible* for this diff? | binary | **locked** |
| `faithfulness` | Is what the message *states* **true** of the diff? | binary | **locked** |
| `completeness` | Is the primary + every material change *represented*? | 3-level | **locked** |
| `specificity` | Is the message *concrete* enough to be informative? | binary | **locked** |

Orthogonality is the point. Faithfulness catches over-claims (says more than the diff does);
completeness catches under-claims (omits material the diff does); specificity asks only
whether what it says is concrete; type asks only whether the label is defensible. Each axis
owns exactly one question so the same defect isn't scored twice.

---

## Decisions captured here

| Decision | Status |
|----------|--------|
| Analytic per-axis rubric; plausibility-based type-correctness | logged — ADR 0027 |
| Final four-axis set (revises 0027: drop scope/conciseness, add faithfulness/completeness) | **to log** |
| Scoring scales — mixed by axis shape | **to log** |
| Judge reasoning protocol (reason-then-label, structured fields, per-example logging) | **to log** |
| Axis anchors — all four axes authored | **to log** |
| Composite — gate-then-grade (no weights) | **to log** |

> Before assigning any ADR number for the "to log" rows, run `ls docs/decisions/` and read
> the live max id off the filenames. The directory listing is the only authority for
> sequencing.

---

## Scoring scales — mixed, by axis shape

Scale follows the shape of the underlying judgment, not a uniform default:

- **Binary** (`pass` / `fail`) where the judgment is genuinely two-valued — accept as-is or
  require a change. `type_correctness`, `specificity`, and `faithfulness`: a type is
  defensible or it isn't, a message is concrete or it's filler, a claim is supported or it
  isn't. A `partial` bucket on these is phantom resolution that the judge and human raters
  fill inconsistently, dragging down the judge-vs-human agreement that is the headline trust
  number for the eval.
- **3-level** (`fail` / `partial` / `pass`) where coverage is genuinely graded.
  `completeness` is like this: a message can capture the primary change but drop a material
  secondary one — a real, distinguishable middle state. Here `partial` earns its keep.

**Two consequences of mixing scales:**

1. **Composite normalization before any graded combination.** A binary `{0,1}` and a 3-level
   `{0,1,2}` are on different ranges. Normalize each axis to `[0,1]` (binary `0/1`; 3-level
   `0 / 0.5 / 1`) before combining. (The composite below uses gating, not averaging — but the
   graded headline still needs this mapping.)
2. **Validation statistic by axis.** Judge-vs-human agreement is not one number: the three
   binary axes use raw agreement / Cohen's kappa; `completeness` uses Spearman or weighted
   kappa. `run_eval.py` emits the right statistic per axis.

---

## Judge reasoning protocol (applies to every axis)

- **Characterize the diff first, in the judge's own words, before reading the candidate
  message** — stops the judge from anchoring on the model's own commit message.
- **Reason first, label second — never label first.** A label emitted before the reasoning
  gets rationalized backward. Reasoning-then-label lets the verdict follow the evidence.
- **Rationale and label are separate output fields** (e.g. JSON), so the harness parses the
  label deterministically and stores the rationale alongside it.
- **Every per-example judgment is logged** (rationale + label, per axis), which makes the
  human-validation correlation debuggable rather than a bare number.

---

## `type_correctness`  (binary, locked)

**Scale:** binary — `pass` / `fail`. **Basis:** plausibility. The diff is the only ground
truth; the gold/reference type is **never** consulted.

### Axis question

> Reviewing this commit the way an experienced maintainer would, is the chosen Conventional
> Commits type one they'd accept for the changes in this diff — or would they make you
> change it before merging?

### Decision rule

`pass` if **no strictly better type exists** for this diff; `fail` if a strictly better type
exists or the type is unsupported by the diff.

### `pass`

A competent reviewer would accept the chosen type as-is. This holds when the chosen type is
among the most defensible type(s) for what the diff actually does — no other type is
*strictly* better. If several types are equally defensible, the chosen one passes, because
"equally defensible" means no strictly better type exists. The reference/gold type carries no
weight.

### `fail`

A reviewer would require a change. Two cases:

- **(a) Unsupported or contradicted** — the type asserts a kind of change the diff does not
  contain, or nothing in the diff supports it.
- **(b) A strictly better type exists** — the type is not absurd, but a clearly better one
  exists that a reviewer would require. This includes cases where the better type carries a
  downstream consequence (such as the correct version bump) that the chosen type would
  suppress. *Equally-defensible* alternatives do not trigger (b); only a type that genuinely
  dominates the chosen one does.

**Backstop:** an out-of-codebook type, a missing type, or gibberish fail here too, though
grammar-constrained decoding should prevent these.

### Reasoning steps (logged; rationale first, label second)

1. In one line, state what the diff actually changes — in the judge's own words, from the
   diff, **not** the candidate message.
2. List the Conventional Commits types defensible for that change (often more than one).
3. Decide whether any single type is *strictly better* than the chosen one. Equally-defensible
   alternatives don't count; only a type a reviewer would actively prefer. Chosen type among
   the best (incl. tied) → no strictly better type exists.
4. Apply "would a reviewer make you change it?" → short rationale, then label.

---

## `faithfulness`  (binary, locked)

**Scale:** binary — `pass` / `fail`. **Basis:** accuracy. Everything the message asserts must
be true of the diff. Unlike specificity, this **requires reading the diff** to verify the
claims.

**Boundary:** `faithfulness` = is what's stated *true* (catches over-claims); `completeness`
= is the material change *represented at all* (catches under-claims). `specificity` stays
orthogonal: a concrete-but-false message *passes* specificity and is caught here.

### Axis question

> Is every claim the message makes about the change supported by the diff — i.e. does it
> describe what this commit really does, with nothing invented, mischaracterized, or
> overstated?

### `pass`

Every substantive claim is borne out by the diff. A reviewer reading the message then the
diff would not say "that's not what this does." The message may leave things out
(completeness's job) or be terse (specificity's job) — faithfulness only asks whether what it
*does* say is true.

### `fail`

The message asserts something the diff doesn't support: a change that isn't there, a wrong
characterization of what the change is, or an overstatement of its scope or impact. A
reviewer would correct the record.

### Reasoning steps (logged; rationale first, label second)

1. List what the diff actually changes, in your own words.
2. Take each claim the message makes and check it against that list.
3. Every claim supported → `pass`; any claim unsupported / wrong / overstated → `fail`.
4. Name the unsupported claim, then the label.

---

## `completeness`  (3-level, locked)

**Scale:** 3-level — `fail` / `partial` / `pass` (`complete`). Coverage is graded.

### Axis question

> Does the message represent the primary change and every material secondary change in the
> diff — where *material* = affects behavior, interface, semantics, or dependencies, and
> incidental edits (formatting, comments, local renames) don't count?

### `complete` (pass)

Captures the primary change and all material secondary changes. Incidental changes need not
be mentioned. A reviewer reading message-then-diff wouldn't say "you left out something that
matters."

### `partial`

Captures the primary change but omits at least one material secondary change, so the
message-only picture is missing something a reader would need.

### `fail`

Omits or misidentifies the primary change: a reader of the message alone wouldn't know what
the commit is fundamentally for. It describes only an incidental edit, or frames a secondary
change as the point.

### Reasoning steps (logged; rationale first, label second)

1. List what the diff changes, tagging each as primary / material-secondary / incidental.
2. Is the primary change represented? If not → `fail`.
3. Is each material secondary change represented?
4. Roll up: all material captured → `complete`; primary captured but ≥1 material change
   missing → `partial`; primary missing or misidentified → `fail`.
5. Name what's missing and whether it's primary or secondary, then the label.

---

## `specificity`  (binary, locked)

**Scale:** binary — `pass` / `fail`. The message must be concrete enough to be informative.

### Axis question

> Does the message name the specific behavior or mechanism that changed — something beyond
> what the type and the touched files already imply — rather than generic filler that could
> describe almost any commit?

### `pass`

Identifies the concrete thing changed at a resolution that distinguishes this commit from a
random one. It tells you something you couldn't infer from the type and file paths alone.

### `fail`

Generic boilerplate that could describe almost any commit, or names only the area touched
without naming the change. Judge concreteness only — don't penalize the message for being
wrong (faithfulness) or for omissions (completeness); a concrete-but-false message still
passes specificity.

### Reasoning steps (logged; rationale first, label second)

1. Read the message on its face.
2. Could this exact wording plausibly describe many unrelated commits? If yes → filler.
3. Does it name a concrete behavior or mechanism, not just an area?
4. Concrete and discriminating → `pass`; generic → `fail`. Then the label.

(No diff check needed — specificity is about the message's resolution, not its accuracy.)

---

## Composite — gate-then-grade (no weights)

Correctness is resolved before quality ever enters: if the message lies about the code, a
reviewer rejects it and never gets to "but is it specific enough?" That ordering is enforced
by gating, not by weighting — a weighted average would let high specificity buy back a
correctness failure, which is exactly the failure this structure exists to prevent.

**Hard gate — `faithfulness` (unconditional).** A `fail` fails the message outright,
regardless of every other axis. A tool whose entire value is trust cannot ship a false
message.

**Priority order for the rest (lexicographic):** `type_correctness` → `completeness` →
`specificity`. Correctness (type) before quality (completeness, specificity).

**Type-gate knob:** `type_correctness` is the **top of the quality tier, not a hard gate**
(default). For a tool whose output a human reviews before committing, a mistyped-but-truthful,
clear message is mis-filed, not dangerous. Promote `type` to an unconditional gate only if
Committed ever drives automated releases, where a wrong type causes a wrong version bump.

### Primary metric — conjunctive pass-rate

A message **passes** iff it clears all four axes; the pass-rate over the eval set is the
headline "is this shippable" number. One binary per message, one rate across the set, zero
weights. For this metric, **"clears `completeness`" = `complete`** — a `partial` does not
clear it, since a dropped material change isn't shippable-clean.

### Always report the per-axis vector

Report the four per-axis pass-rates alongside the conjunctive number. That is the whole
reason the axes were split: the single number says the model regressed, the vector says which
capability did.

### Optional graded headline (A/B and checkpoint ranking)

Built lexicographically, never by weighting:

```
score = 0                              if faithfulness fails  (and if type is gated, also 0 when type fails)
score = 1 + completeness + specificity otherwise
        completeness ∈ {0, 0.5, 1}     (fail / partial / complete)
        specificity  ∈ {0, 1}          (fail / pass)
→ score ∈ {0} ∪ [1, 3]  (1–3 in half-steps among correct messages)
```

Quality can never compensate for a correctness failure: a gate failure is 0, and graded
quality only exists above the gate.