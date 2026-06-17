"""
gradio_app.py — standalone Gradio demo for Committed (HF Spaces, Gradio SDK).

Loads the base GGUF inline via the shared CommitGenerator (same construction as
eval and the FastAPI service) and serves a diff -> Conventional Commits message UI.

Kept PRIVATE until the fine-tuned model is ready and not publicized before then
(ADR 0043). The model path comes from the environment; see committed.inference.engine.
"""

from __future__ import annotations

import gradio as gr

from committed.inference.engine import CommitGenerator

_generator: CommitGenerator | None = None


def _get_generator() -> CommitGenerator:
    """Lazy singleton: load the model once, on first request."""
    global _generator
    if _generator is None:
        _generator = CommitGenerator()
    return _generator


def commit_message(diff: str) -> str:
    if not diff.strip():
        return "Paste a diff to get a commit message."
    return _get_generator().generate(diff)


with gr.Blocks(title="Committed") as demo:
    gr.Markdown(
        "# Committed\n"
        "Generate a Conventional Commits message from a code diff. Runs a small "
        "model locally, so your diff never leaves the server."
    )
    diff_in = gr.Textbox(label="Diff", lines=18, placeholder="diff --git a/... b/...")
    out = gr.Textbox(label="Commit message", lines=2)
    gr.Button("Generate", variant="primary").click(commit_message, inputs=diff_in, outputs=out)


if __name__ == "__main__":
    demo.launch()
