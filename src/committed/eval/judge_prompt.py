"""
Committed — LLM-as-judge prompt (the rubric, expressed as instructions to the judge).

This is the ONE place the four-axis rubric becomes a prompt. Both backends import from here:
  - JUDGE_SYSTEM: the fixed rubric + protocol. The Claude backend caches this; the Gemini
    backend prepends it to the user turn.
  - build_judge_user(diff, message): the variable per-call turn.

PROVENANCE: the axis criteria below are transcribed from docs/eval/judge_rubric.md (the authored
source of truth) and must stay in sync with it. The wrapper around them — the task framing, the
protocol instructions, the diff/message presentation, the output instruction — is the
prompt-engineering layer; tune it HERE if the judge misbehaves, but keep the axis criteria
faithful to the doc.

Two deliberate design points:
  - The composite (gate-then-grade) is NOT in this prompt. The judge scores the four axes
    independently; gating/aggregation happen in run_eval.py. Telling the judge that faithfulness
    is a hard gate could bias how it scores that axis.
  - Anchors are stated as general principles with no worked examples, by design (keeps the judge
    from pattern-matching to instances instead of applying the criterion).
"""

# NOTE: keep JUDGE_SYSTEM well over ~1024 tokens so Claude prompt caching engages (it clears that
# comfortably). The four axes are the bulk; the framing is the tunable part.

JUDGE_SYSTEM = """\
Evaluate a candidate Conventional Commits message against the code diff it describes. Score it on \
four independent axes, defined below.

You are NOT given any reference or "correct" message. Judge only the diff and what the candidate \
message itself claims. Score each axis on its own merits and do not let your verdict on one axis \
influence another.

Protocol (follow exactly):
- First, in your own words and from the DIFF ALONE, state what the commit actually changes. Do \
this before judging any axis, so your judgments rest on the diff rather than on how the message \
frames things.
- For every axis, write a short rationale BEFORE the label. The reasoning must lead to the \
verdict, not justify one you have already chosen.
- Apply each axis's criteria literally; do not extend benefit of the doubt beyond what they \
state. Do not reward length or confident phrasing; a longer or more assertive message is not a \
better one.

=== Axis 1: type_correctness (label: pass | fail) ===
Basis: plausibility. The diff is the only ground truth; there is no gold type to match.
Question: Reviewing this commit the way an experienced maintainer would, is the chosen \
Conventional Commits type one they'd accept for the changes in this diff, or would they make you \
change it before merging?
Decision rule: pass if no strictly better type exists for this diff; fail if a strictly better \
type exists, or the type is unsupported by the diff.
- pass: A competent reviewer would accept the chosen type as-is, because it is among the most \
defensible type(s) for what the diff actually does (no other type is strictly better). If several \
types are equally defensible, the chosen one passes, because "equally defensible" means no \
strictly better type exists. Matching some conventional default is neither necessary nor \
sufficient.
- fail: The chosen type MISREPRESENTS the change — it names a category of change the diff does \
not actually perform, or it suppresses a real downstream consequence that the correct type would \
carry (such as a change that should drive a version bump being labeled so it would not). An \
out-of-codebook, missing, or gibberish type also fails. "Strictly better" means ONLY this: a type \
is strictly better when the chosen one misrepresents the change in one of these ways. If the \
chosen type is a defensible reading of the change and a reviewer would merely PREFER a different \
label, that is NOT strictly better and the type PASSES. Two types each being defensible never \
makes either strictly better.
Reasoning steps:
1. State in one line what the diff actually changes (your own words, from the diff).
2. List the Conventional Commits types that are defensible for that change (often more than one).
3. Decide whether the chosen type MISREPRESENTS the change (names a category the diff does not \
perform, or suppresses a downstream consequence the correct type carries). A type a reviewer \
would merely prefer is NOT strictly better; only misrepresentation is. If the chosen type is a \
defensible reading, no strictly better type exists.
4. Apply "would a reviewer make you change it?" -> rationale, then label.

=== Axis 2: faithfulness (label: pass | fail) ===
Basis: accuracy of the DESCRIPTION, checked one atomic claim at a time. Judge only the \
description (the text after the type) — the type prefix is judged separately under \
type_correctness, so a wrong or questionable type never counts against this axis.
Method (decompose, then verify each claim): break the description into its atomic claims — the \
smallest standalone assertions it makes — and sort each into one of two kinds:
  (a) a WHAT-CHANGED claim: an assertion about what the commit does / modifies / adds / removes. \
It must be true of the diff.
  (b) a RATIONALE claim: the "why" or intended purpose behind the change. You do NOT need the \
diff to prove it; it passes unless the diff actively contradicts it.
Then test every claim against the diff INDIVIDUALLY. Faithfulness is the conjunction: the message \
is faithful only if every claim clears its own test. This decomposition is about the message's \
CLAIMS (precision — is what it says true?), NOT about whether the message covers every change in \
the diff (that is completeness; do not import it here).
Question (per claim): is this specific claim borne out by the diff (what-changed), or at least \
not contradicted by it (rationale)?
- pass: Every what-changed claim is supported by the diff (nothing invented, mischaracterized, or \
overstated), and no claim — rationale included — is contradicted by the diff. The message may be \
terse or leave things out; faithfulness only asks whether each thing it DOES assert is true.
- fail: At least one claim fails its test — a what-changed claim names a change that isn't in the \
diff, mischaracterizes what changed, or overstates its scope/impact; or any claim (what-changed \
or rationale) is directly contradicted by the diff. A wrong TYPE is not a faithfulness failure, \
and a rationale that is merely unprovable but not contradicted is not one either.
Reasoning steps:
1. List what the diff actually changes, in your own words.
2. Enumerate the description's atomic claims (ignore the type prefix); tag each as what-changed or \
rationale.
3. Verify each claim against the diff on its own: what-changed -> supported by the diff? \
rationale -> not contradicted by the diff?
4. Conjunction: every claim clears -> pass; any single claim fails -> fail.
5. Name the specific failing claim and why (unsupported what-changed, mischaracterization, \
overstatement, or contradicted rationale), then the label.

=== Axis 3: completeness (label: pass | fail) ===
Coverage is binary: either the message references everything a reader needs, or it leaves out \
something that matters. A change is "material" only if it is a DISTINCT change — to behavior, \
interface, semantics, or dependencies — that a reader would need to know about as a separate \
thing. Supporting detail that merely implements or enables a change the message ALREADY names — \
the new imports a change requires, the internal mechanics of how a named change works, the \
plumbing of a refactor — is NOT a separate material change, and leaving it out does not count \
against this axis. Incidental edits (formatting, comments, local renames) never count. \
This axis is about COVERAGE only: whether each material change is referenced, not whether the \
reference is accurate (accuracy is faithfulness) and not whether it is concrete (concreteness is \
specificity). Do not double-count a flaw already charged to another axis.
Question: Reading the message alone, would a reviewer know the primary change AND every materially \
distinct change — or would they be missing something that matters?
- pass: References the primary change and every materially distinct secondary change. The message \
may be terse, and it need not spell out imports, internal mechanics, or refactor plumbing for a \
change it has already named. A message that names the single change but names it vaguely (e.g. \
"fix flapping test" for a one-change diff) still passes here — its lack of concrete detail is \
charged to specificity, not to completeness. A reviewer reading message-then-diff wouldn't say \
"you left out something that matters."
- fail: Leaves a material change uncovered — either it never references the primary change (a \
reader of the message alone wouldn't know what the commit is fundamentally for, e.g. it describes \
only an incidental edit), or it omits a materially distinct secondary change a reader would need. \
(Whether what the message DOES say is true is faithfulness, not completeness.)
Reasoning steps:
1. List what the diff changes, tagging each as primary / materially-distinct-secondary / \
supporting-detail / incidental.
2. Is the primary change referenced at all (not replaced by an incidental edit)? If not -> fail.
3. Is every materially distinct secondary change referenced? Supporting detail and incidental \
edits do not count, and a vague-but-present reference still counts as referenced.
4. Primary referenced and all materially distinct changes referenced -> pass; any materially \
distinct change uncovered -> fail.
5. Name what's missing (primary, or which distinct secondary change), then the label.

=== Axis 4: specificity (label: pass | fail) ===
The message must be concrete enough to be informative. Judge concreteness ONLY — not whether the \
message is true (that is faithfulness) and not whether it is complete (that is completeness). A \
concrete-but-false message still passes specificity.
Question: Does the message name the specific behavior or mechanism that changed — something beyond \
what the type and the touched files already imply — rather than generic filler that could describe \
almost any commit?
- pass: Identifies the concrete thing changed at a resolution that distinguishes this commit from \
a random one. It tells you something you couldn't infer from the type and file paths alone.
- fail: Generic boilerplate that could describe almost any commit, or names only the area touched \
without naming the change.
Reasoning steps:
1. Read the message on its face.
2. Could this exact wording plausibly describe many unrelated commits? If yes -> filler.
3. Does it name a concrete behavior or mechanism, not just an area?
4. Concrete and discriminating -> pass; generic -> fail. Then the label.

=== Output ===
Provide, via the required structured output: first `diff_summary` (your own-words description of \
what the diff changes), then for each axis a `rationale` followed by a `label`. All four axes use \
exactly the labels pass|fail: type_correctness, faithfulness, completeness, specificity.
"""


def build_judge_user(diff: str, message: str) -> str:
    """The variable per-call turn: one diff + one candidate message to judge. The diff and message
    are wrapped in tags so the model can tell them apart cleanly; the standing instructions and
    the rubric live in JUDGE_SYSTEM."""
    return (
        "Evaluate the following candidate commit message against its diff.\n\n"
        f"<diff>\n{diff}\n</diff>\n\n"
        f"<candidate_message>\n{message}\n</candidate_message>\n\n"
        "Summarize what the diff changes first, then judge the four axes (rationale before label), "
        "then submit the structured judgment."
    )