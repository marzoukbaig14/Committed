from __future__ import annotations

import gradio as gr

from committed.inference.engine import NotADiffError
# Reuse the ONE model registry + generator factory from the FastAPI serving layer, so the
# demo and the API expose exactly the same models with the same (repo, file, tokenizer) and
# the same 2-thread fix — no second registry to drift out of sync.
from committed.serving.api import MODEL_REGISTRY, DEFAULT_MODEL, build_generator

# Per-model generator cache for this (Gradio) process: default eager, others lazy.
_generators: dict = {}


def _get_generator(model_id: str):
    if model_id not in _generators:
        _generators[model_id] = build_generator(model_id)
    return _generators[model_id]


def commit_message(diff: str, model: str) -> str:
    # The "looks like a diff" guard lives in the engine (NotADiffError), so this demo and
    # the FastAPI service reject garbage identically — no second heuristic to drift.
    if not diff.strip():
        return "Paste a diff to get a commit message."
    model_id = model or DEFAULT_MODEL
    try:
        return _get_generator(model_id).generate(diff)  # lazy-loads 0.6b on first pick
    except NotADiffError as e:
        return str(e)


# Warm up the DEFAULT model at container start so the first real click doesn't pay its load.
# The other model loads lazily the first time it's picked. Wrapped so a hiccup never blocks UI.
try:
    _get_generator(DEFAULT_MODEL).generate(
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
    model_dd = gr.Dropdown(
        choices=list(MODEL_REGISTRY.keys()),
        value=DEFAULT_MODEL,
        label="Model",
        info="1.7b is the default (loaded at startup); 0.6b loads on first use.",
    )
    gr.Markdown(
        "_First request after the Space wakes loads the default model (~30–60s). "
        "The 0.6b loads the first time you pick it. After that it's quick._"
    )
    out = gr.Textbox(label="Commit message", lines=2)
    gr.Button("Generate", variant="primary").click(
        commit_message, inputs=[diff_in, model_dd], outputs=out
    )

if __name__ == "__main__":
    demo.launch()
