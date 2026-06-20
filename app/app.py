from __future__ import annotations

import gradio as gr

from committed.inference.engine import CommitGenerator, NotADiffError

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


def commit_message(diff: str) -> str:
    # The "looks like a diff" guard now lives in the engine (NotADiffError), so
    # this demo and the FastAPI service reject garbage identically — there is no
    # second copy of the heuristic here to drift out of sync.
    if not diff.strip():
        return "Paste a diff to get a commit message."
    try:
        return _get_generator().generate(diff)
    except NotADiffError as e:
        return str(e)


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
