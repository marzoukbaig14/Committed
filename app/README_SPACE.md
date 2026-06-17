# Deploying the Gradio Space

Phase-one standalone demo (ADR 0043). **Keep the Space private until the fine-tune is ready;
do not publicize it.**

## Layout the Space expects

A Gradio Space runs `app.py` at its root and `pip install`s `requirements.txt`. This app
imports `committed.inference.engine`, so the `committed` package must be importable on the
Space. Push these to the Space repo:

```
app.py                 <- this repo's app/gradio_app.py, renamed
requirements.txt       <- this repo's app/requirements.txt
committed/             <- copy of src/committed/ (carries engine.py, prompt.py, grammar.gbnf)
```

(Equivalently, add `committed @ git+https://github.com/marzoukbaig14/Committed.git` to
`requirements.txt` instead of copying the package — only if the GitHub repo is reachable
from the Space build.)

## Steps

1. Create a Hugging Face **Gradio** Space (SDK: Gradio), visibility **private**.
2. Push the files above.
3. The base GGUF is pulled from the public Hub on first load (ADR 0038); no Space secret is
   needed. To serve a different model, set `COMMITTED_MODEL_PATH` (or `COMMITTED_MODEL_REPO` /
   `COMMITTED_MODEL_FILE`) in the Space variables — the same env knobs the FastAPI service uses.

CPU Basic (free) is the target tier. First load builds `llama-cpp-python` and downloads the
model, so the initial boot is slow; subsequent requests are warm.
