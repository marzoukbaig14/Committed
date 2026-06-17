from __future__ import annotations

import gradio as gr

from committed.inference.engine import CommitGenerator

# Free HF "CPU basic" Space = 2 vCPUs. Tell llama.cpp to use exactly those, so it
# doesn't spawn threads for the host's full core count and thrash. Speed only;
# the generated text is unchanged.
N_THREADS = 2

_generator: CommitGenerator | None = None


def _get_generator() -> CommitGenerator:
    global _generator
    if _generator is None:
        _generator = CommitGenerator(n_threads=N_THREADS, n_threads_batch=N_THREADS)
    return _generator


def _looks_like_diff(text: str) -> bool:
    """Loose check: is this plausibly a code diff? Catches garbage like 'asdf'
    without demanding a perfectly-formed patch."""
    t = text.strip()
    if not t:
        return False
    if "diff --git" in t or "@@ " in t:
        return True
    if "--- " in t and "+++ " in t:
        return True
    change_lines = sum(
        1
        for line in t.splitlines()
        if line[:1] in "+-" and not line.startswith(("+++", "---"))
    )
    return change_lines >= 2


def commit_message(diff: str) -> str:
    if not diff.strip():
        return "Paste a diff to get a commit message."
    if not _looks_like_diff(diff):
        return ("That doesn't look like a code diff. Paste the output of `git diff` "
                "— lines with +/- changes, @@ hunks, or a `diff --git` header.")
    return _get_generator().generate(diff)


# Warm up at container start so the first real click doesn't pay the model load.
# Wrapped so a hiccup never stops the UI from coming up.
try:
    _get_generator().generate(
        "diff --git a/x b/x\n--- a/x\n+++ b/x\n@@ -1 +1 @@\n-a\n+b\n"
    )
except Exception as e:  # noqa: BLE001
    print(f"[warmup] skipped: {e}")


with gr.Blocks(title="Committed") as demo:
    gr.Markdown(
        "# Committed\n"
        "Generate a Conventional Commits message from a code diff."
    )
    diff_in = gr.Textbox(label="Diff", lines=18, placeholder="diff --git a/... b/...")
    gr.Markdown(
        "_First request after the Space wakes loads the model (~30–60s). After that it's quick._"
    )
    out = gr.Textbox(label="Commit message", lines=2)
    gr.Button("Generate", variant="primary").click(commit_message, inputs=diff_in, outputs=out)

if __name__ == "__main__":
    demo.launch()
