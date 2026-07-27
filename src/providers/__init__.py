"""Generation providers package.

Exposes a small factory that resolves a requested generation mode to a concrete
provider, always falling back to Template Engine Mode when a richer provider is
unavailable (for example, when no ``LLM_API_KEY`` is configured).
"""

from __future__ import annotations

from .base_provider import BaseProvider
from .llm_provider import API_KEY_ENV_VAR, LLM_MODE, LLMProvider
from .template_provider import TEMPLATE_MODE, TemplateProvider

# The list of modes offered in the UI. Template Engine Mode is first (default).
AVAILABLE_MODES = [TEMPLATE_MODE, LLM_MODE]


def get_provider(mode: str) -> BaseProvider:
    """Return a ready-to-use provider for the requested mode.

    If LLM Enhanced Mode is requested but not available (no API key), this
    returns the always-available TemplateProvider so the app keeps working.
    """
    if mode == LLM_MODE:
        llm = LLMProvider()
        if llm.is_available():
            return llm
        # Requested LLM but no key: fall back to local generation.
        return TemplateProvider()
    # Default: Template Engine Mode.
    return TemplateProvider()


def llm_is_configured() -> bool:
    """Return True when an LLM API key is present in the environment."""
    return LLMProvider().is_available()


__all__ = [
    "BaseProvider",
    "TemplateProvider",
    "LLMProvider",
    "TEMPLATE_MODE",
    "LLM_MODE",
    "API_KEY_ENV_VAR",
    "AVAILABLE_MODES",
    "get_provider",
    "llm_is_configured",
]
