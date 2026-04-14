"""Tests for src.ai_formatter."""

from __future__ import annotations

import pytest

from src.ai_formatter import (
    _REGISTRY,
    fallback_format,
    format_with_ai,
    get_provider,
    list_providers,
    register_provider,
)


class _DummyProvider:
    """A minimal test provider."""

    name: str = "dummy"

    def format(self, extracted_text: str, prompt: str) -> str:
        return f"FORMATTED: {extracted_text}"


class _FailingProvider:
    """A provider that always raises."""

    name: str = "failing"

    def format(self, extracted_text: str, prompt: str) -> str:
        raise RuntimeError("AI exploded")


@pytest.fixture(autouse=True)
def _clean_registry():
    """Snapshot and restore the provider registry around each test."""
    original = dict(_REGISTRY)
    yield
    _REGISTRY.clear()
    _REGISTRY.update(original)


class TestProviderRegistry:
    def test_register_and_get(self):
        register_provider("dummy", _DummyProvider)
        provider = get_provider("dummy")
        assert provider.name == "dummy"

    def test_get_unknown_raises(self):
        with pytest.raises(KeyError, match="Unknown AI provider"):
            get_provider("nonexistent")

    def test_list_providers(self):
        register_provider("alpha", _DummyProvider)
        register_provider("beta", _DummyProvider)
        names = list_providers()
        assert "alpha" in names
        assert "beta" in names


class TestFallbackFormat:
    def test_adds_header(self):
        result = fallback_format("hello world")
        assert "AI formatting was unavailable" in result
        assert "hello world" in result


class TestFormatWithAi:
    def test_no_provider_uses_fallback(self):
        result = format_with_ai("test text", provider_name=None)
        assert "AI formatting was unavailable" in result
        assert "test text" in result

    def test_unknown_provider_uses_fallback(self):
        result = format_with_ai("test text", provider_name="nonexistent")
        assert "AI formatting was unavailable" in result

    def test_successful_provider(self):
        register_provider("dummy", _DummyProvider)
        result = format_with_ai("hello", provider_name="dummy")
        assert result == "FORMATTED: hello"

    def test_failing_provider_uses_fallback(self):
        register_provider("failing", _FailingProvider)
        result = format_with_ai("hello", provider_name="failing")
        assert "AI formatting was unavailable" in result
