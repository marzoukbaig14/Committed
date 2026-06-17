"""
test_serving.py — deterministic, offline tests for the serving API and the prompt
extraction. No model is loaded: the generator is faked and the tokenizer is a stub,
so these run on a tokenless, network-free runner. Run: uv run pytest tests/test_serving.py -v
"""

import pytest
from fastapi import HTTPException

from committed.inference import prompt
from committed.serving import api


class FakeGenerator:
    def __init__(self):
        self.seen = []

    def generate(self, diff: str) -> str:
        self.seen.append(diff)
        return "feat(api): add health endpoint"


def test_health_ok_when_loaded():
    api._state["generator"] = FakeGenerator()
    assert api.health() == {"status": "ok"}


def test_generate_returns_message_and_passes_diff_through():
    fake = FakeGenerator()
    api._state["generator"] = fake
    resp = api.generate(api.GenerateRequest(diff="diff --git a/x b/x\n+y"))
    assert resp == {"message": "feat(api): add health endpoint"}
    assert fake.seen == ["diff --git a/x b/x\n+y"]


def test_generate_rejects_empty_diff():
    api._state["generator"] = FakeGenerator()
    with pytest.raises(HTTPException) as exc:
        api.generate(api.GenerateRequest(diff="   "))
    assert exc.value.status_code == 400


def test_cors_middleware_installed():
    assert any("CORSMiddleware" in str(m.cls) for m in api.app.user_middleware), \
        "CORS middleware not installed"


class _FakeTokenizer:
    """Records exactly how build_prompt calls apply_chat_template."""

    def apply_chat_template(self, messages, **kwargs):
        self.messages = messages
        self.kwargs = kwargs
        return "RENDERED"


def test_build_prompt_is_a_faithful_extraction():
    tok = _FakeTokenizer()
    out = prompt.build_prompt("DIFF", tok)
    assert out == "RENDERED"
    # the exact construction the baseline froze (ADR 0040): messages from build_messages,
    # rendered with thinking suppressed at the template level.
    assert tok.messages == prompt.build_messages("DIFF")
    assert tok.kwargs == {
        "tokenize": False,
        "add_generation_prompt": True,
        "enable_thinking": False,
    }
