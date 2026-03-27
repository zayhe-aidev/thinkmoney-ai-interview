"""Tests for LLM provider configuration."""

import os

import pytest

from src.config import get_llm

# OpenAI requires OPENAI_API_KEY at instantiation time.
# We use a dummy key for tests that need to create an OpenAI instance.
_DUMMY_OPENAI_KEY = "sk-test-dummy-key-for-testing-only"


@pytest.fixture(autouse=True)
def _ensure_openai_key(monkeypatch):
    """Set a dummy OpenAI key so ChatOpenAI can be instantiated in tests."""
    if not os.environ.get("OPENAI_API_KEY"):
        monkeypatch.setenv("OPENAI_API_KEY", _DUMMY_OPENAI_KEY)


class TestGetLlm:
    def test_openai_returns_correct_type(self):
        llm = get_llm("openai")
        from langchain_openai import ChatOpenAI

        assert isinstance(llm, ChatOpenAI)

    def test_anthropic_returns_correct_type(self):
        llm = get_llm("anthropic")
        from langchain_anthropic import ChatAnthropic

        assert isinstance(llm, ChatAnthropic)

    def test_ollama_returns_correct_type(self):
        llm = get_llm("ollama")
        from langchain_ollama import ChatOllama

        assert isinstance(llm, ChatOllama)

    def test_openai_default_model(self):
        llm = get_llm("openai")
        assert llm.model_name == "gpt-4o-mini"

    def test_anthropic_default_model(self):
        llm = get_llm("anthropic")
        assert llm.model == "claude-haiku-4-5-20251001"

    def test_ollama_default_model(self):
        llm = get_llm("ollama")
        assert llm.model == "gpt-oss:20b"

    def test_openai_custom_model(self):
        llm = get_llm("openai", model="gpt-4o")
        assert llm.model_name == "gpt-4o"

    def test_anthropic_custom_model(self):
        llm = get_llm("anthropic", model="claude-sonnet-4-5-20241022")
        assert llm.model == "claude-sonnet-4-5-20241022"

    def test_ollama_custom_model(self):
        llm = get_llm("ollama", model="llama3.1")
        assert llm.model == "llama3.1"

    def test_invalid_provider_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            get_llm("azure")

    def test_invalid_provider_message_lists_supported(self):
        with pytest.raises(ValueError, match="ollama, openai, anthropic"):
            get_llm("cohere")

    def test_temperature_is_zero(self):
        """All providers should use temperature=0 for deterministic output."""
        for provider in ("openai", "anthropic", "ollama"):
            llm = get_llm(provider)
            assert llm.temperature == 0

    def test_openai_fails_without_api_key(self, monkeypatch):
        """ChatOpenAI requires OPENAI_API_KEY at instantiation time."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(Exception):
            get_llm("openai")

    def test_anthropic_creates_without_api_key(self, monkeypatch):
        """ChatAnthropic can instantiate without ANTHROPIC_API_KEY set."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        llm = get_llm("anthropic")
        assert llm is not None

    def test_ollama_creates_without_any_env(self):
        """ChatOllama needs no API key — it connects to local server."""
        llm = get_llm("ollama")
        assert llm is not None
