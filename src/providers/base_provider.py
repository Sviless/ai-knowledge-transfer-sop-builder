"""Abstract base class for generation providers.

A *provider* is anything that can turn raw process inputs into a complete
knowledge-transfer package (the dict shape produced by
``template_engine.generate_package``). Keeping this interface small makes it easy
to add new backends (a local template engine, an LLM, etc.) without touching the
UI, storage, or exporters.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """Interface every generation provider must implement."""

    # Human-readable name shown in the UI and stored on the package.
    name: str = "Base Provider"

    @abstractmethod
    def is_available(self) -> bool:
        """Return True when this provider is ready to generate.

        For example, an LLM provider returns False when no API key is set. The
        application uses this to fall back to a provider that is always
        available (Template Engine Mode).
        """
        raise NotImplementedError

    @abstractmethod
    def generate(self, inputs: dict[str, str]) -> dict:
        """Generate and return a complete knowledge-transfer package dict.

        The returned dict must follow the same shape as
        ``template_engine.generate_package`` so exporters, storage, and the UI
        keep working unchanged.
        """
        raise NotImplementedError
