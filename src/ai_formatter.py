"""AI Formatter — pluggable provider interface and registry.

Defines the :class:`AIProvider` protocol that all AI backends implement, a
registry to look them up by name, and a rule-based fallback formatter used
when no AI provider is available.
"""

from __future__ import annotations

import logging
from typing import Optional, Protocol, runtime_checkable

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared prompt template
# ---------------------------------------------------------------------------

DEFAULT_PROMPT = (
    "The following text was extracted from a PDF. Please verify it makes sense, "
    "fix any obvious artifacts, and format it as clean Markdown with proper "
    "headings and bullet points.\n\n---\n{text}\n---"
)

# ---------------------------------------------------------------------------
# Provider protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class AIProvider(Protocol):
    """Protocol that all AI formatter providers must satisfy."""

    name: str

    def format(self, extracted_text: str, prompt: str) -> str:
        """Send *extracted_text* + *prompt* to the AI and return formatted Markdown."""
        ...


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, type[AIProvider]] = {}


def register_provider(name: str, cls: type[AIProvider]) -> None:
    """Register a provider class under *name*."""
    _REGISTRY[name.lower()] = cls


def get_provider(name: str) -> AIProvider:
    """Instantiate and return the provider registered under *name*.

    Raises :class:`KeyError` if the name is not registered.
    """
    cls = _REGISTRY.get(name.lower())
    if cls is None:
        available = ", ".join(sorted(_REGISTRY)) or "(none)"
        raise KeyError(f"Unknown AI provider '{name}'. Available: {available}")
    return cls()


def list_providers() -> list[str]:
    """Return sorted list of registered provider names."""
    return sorted(_REGISTRY)


# ---------------------------------------------------------------------------
# Fallback (rule-based) formatter
# ---------------------------------------------------------------------------


def fallback_format(pages_text: str) -> str:
    """Produce basic Markdown without an AI provider.

    This is a simple pass-through that marks the output as non-AI-formatted
    so users know it has not been coherence-checked.
    """
    header = "<!-- Note: AI formatting was unavailable; this is raw extracted text. -->\n\n"
    return header + pages_text


# ---------------------------------------------------------------------------
# High-level helper
# ---------------------------------------------------------------------------


def format_with_ai(
    extracted_text: str,
    provider_name: Optional[str] = None,
    prompt_template: str = DEFAULT_PROMPT,
) -> str:
    """Format *extracted_text* using the named AI provider.

    Falls back to :func:`fallback_format` when the provider is unavailable or
    raises an exception.
    """
    if provider_name is None:
        logger.info("No AI provider specified — using fallback formatter.")
        return fallback_format(extracted_text)

    try:
        provider = get_provider(provider_name)
    except KeyError:
        logger.warning("Provider '%s' not found — using fallback.", provider_name)
        return fallback_format(extracted_text)

    prompt = prompt_template.format(text=extracted_text)
    try:
        result = provider.format(extracted_text, prompt)
        return result
    except Exception:
        logger.exception("AI provider '%s' failed — using fallback.", provider_name)
        return fallback_format(extracted_text)
