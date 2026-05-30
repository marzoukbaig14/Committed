"""Smoke tests for the Committed development environment.

Verifies that all major dependencies import correctly and that the three
service credentials (Hugging Face, Weights & Biases, Google Gemini) are
present and authenticate. Run with: uv run pytest tests/smoke_test.py -v
"""
from __future__ import annotations

import os

import pytest


# --- Library imports ------------------------------------------------------
# Each test confirms that the library imports without error and exposes a
# version string. If any of these fail, the dependency is not installed and
# `uv sync` is the first thing to try.


def test_import_datasets():
    import datasets

    assert datasets.__version__


def test_import_transformers():
    import transformers

    assert transformers.__version__


def test_import_pandas():
    import pandas

    assert pandas.__version__


def test_import_sklearn():
    import sklearn

    assert sklearn.__version__


def test_import_evaluate():
    import evaluate  # noqa: F401


def test_import_sacrebleu():
    import sacrebleu  # noqa: F401


def test_import_rouge_score():
    from rouge_score import rouge_scorer  # noqa: F401


def test_import_llama_cpp():
    import llama_cpp

    assert llama_cpp.__version__


def test_import_gradio():
    import gradio

    assert gradio.__version__


def test_import_fastapi():
    import fastapi

    assert fastapi.__version__


def test_import_wandb():
    import wandb

    assert wandb.__version__


def test_import_google_genai():
    from google import genai  # noqa: F401


# --- Service authentication ----------------------------------------------
# Each of these makes one small authenticated call to confirm the
# corresponding env var is present and valid. Tests skip cleanly if the
# variable is unset, so the file can run anywhere even without secrets.


@pytest.mark.skipif(not os.environ.get("HF_TOKEN"), reason="HF_TOKEN not set")
def test_hf_auth():
    from huggingface_hub import HfApi

    api = HfApi(token=os.environ["HF_TOKEN"])
    info = api.whoami()
    assert "name" in info, f"unexpected whoami response: {info}"


@pytest.mark.skipif(
    not os.environ.get("WANDB_API_KEY"), reason="WANDB_API_KEY not set"
)
def test_wandb_auth():
    import wandb

    ok = wandb.login(key=os.environ["WANDB_API_KEY"], verify=True, relogin=True)
    assert ok, "wandb.login returned False"


@pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY"), reason="GEMINI_API_KEY not set"
)
def test_gemini_auth():
    from google import genai

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    models = list(client.models.list())
    assert len(models) > 0, "Gemini returned an empty model list"