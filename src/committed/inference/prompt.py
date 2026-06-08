"""
prompt.py — builds the inference-time prompt for Committed.

Zero-shot: system instruction + the diff, no in-context examples. Reasoning:
- The fine-tuned model is conditioned on this same prompt over 52K pairs, so
  exemplars at inference would be redundant and can fight the learned mapping;
  the fine-tune therefore runs zero-shot.
- The baseline uses the IDENTICAL shape so the before/after comparison isolates
  fine-tuning, not a difference in prompt shape.
- This same system prompt must wrap every training example later. One prompt,
  used at baseline, at training, and at fine-tuned inference.

Format is handled by the grammar; this file carries only what a grammar can't:
type choice and the four content judgments. /no_think suppresses Qwen3's reasoning
trace so the grammar receives a clean commit line.
"""

# the canonical system prompt.
SYSTEM_INSTRUCTION = """\
You write a single Conventional Commits message describing a git diff.
Pick the type that best matches what changed:
feat — adds a capability; fix — corrects a bug; docs — documentation only; style — formatting with no change in logic; refactor — restructures code without changing behavior; perf — improves performance; test — adds or fixes tests; build — build system or dependencies; ci — CI configuration; chore — maintenance touching neither source nor tests.
Add a scope in parentheses only when a single file or area clearly owns the change; if the change is spread out or the owner is unclear, omit it.
Write the description so that:
- It reads correctly after "If applied, this commit will…" — imperative verb first ("add", never "adds" or "added").
- It states only what the diff shows. You can see what changed, not why, so never invent a reason, motivation, or outcome the diff doesn't contain; when unsure, say less rather than guess.
- It names the most significant change when the diff touches several things.
- It is specific: name the real function, file, flag, or endpoint, and skip filler verbs ("update", "change") and vague objects ("code", "stuff") when something precise fits.
"""


def build_messages(diff: str) -> list[dict]:
    """Assemble the chat messages for one diff: system instruction + the diff."""
    return [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        # /no_think only on the user turn the model is about to answer.
        {"role": "user", "content": _format_diff(diff) + "\n\n/no_think"},
    ]


def _format_diff(diff: str) -> str:
    """Near-raw diff presentation. This exact format must ALSO be used when
    formatting training examples, or the fine-tune sees a different input shape."""
    return f"Diff:\n{diff}"


if __name__ == "__main__":
    import json

    demo = "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-x = 1\n+x = 2\n"
    print(json.dumps(build_messages(demo), indent=2))