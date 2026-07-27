"""Template Engine Mode provider.

Wraps the existing local, rule-based generation logic. This provider requires no
API key, no network, and is always available. It is the default and guarantees
the app is fully functional offline.
"""

from __future__ import annotations

from ..template_engine import generate_package
from .base_provider import BaseProvider

TEMPLATE_MODE = "Template Engine Mode"


class TemplateProvider(BaseProvider):
    """Generate packages using local Python templates, rules, and scoring."""

    name = TEMPLATE_MODE

    def is_available(self) -> bool:
        # Local generation is always available.
        return True

    def generate(self, inputs: dict[str, str]) -> dict:
        # Delegates to the well-tested local engine and stamps the mode name.
        return generate_package(inputs, mode=self.name)
