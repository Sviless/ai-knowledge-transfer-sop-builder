"""LLM Enhanced Mode provider (scaffold with graceful fallback).

This provider defines the seam where a real Large Language Model integration
(OpenAI, Azure OpenAI, Anthropic Claude, etc.) would be wired in. It reads its
credential from the ``LLM_API_KEY`` environment variable and never hardcodes a
key.

Behavior guarantees:
- If no API key is present, ``is_available()`` returns False and the app
  automatically uses Template Engine Mode.
- Even when a key is present, generation always starts from the local template
  baseline, so structured data, scoring, and exports keep working.
- Any error during LLM enhancement is caught and the app gracefully falls back
  to the template output (never crashes the user's session).
"""

from __future__ import annotations

import os

from ..template_engine import generate_package
from .base_provider import BaseProvider

LLM_MODE = "LLM Enhanced Mode"

# Name of the environment variable that holds the API key. Set it in your shell
# (e.g. ``setx LLM_API_KEY "sk-..."`` on Windows) before launching the app.
API_KEY_ENV_VAR = "LLM_API_KEY"

# Label used when LLM mode gracefully falls back to local generation.
TEMPLATE_MODE_FALLBACK = "Template Engine Mode (LLM fallback)"


class LLMProvider(BaseProvider):
    """Generate packages with optional LLM enhancement over a template baseline."""

    name = LLM_MODE

    def __init__(self) -> None:
        # Read the key from the environment only. Never hardcode secrets.
        self.api_key = os.getenv(API_KEY_ENV_VAR, "").strip()
        # Optional: allow choosing a provider/model via env without code changes.
        self.provider_name = os.getenv("LLM_PROVIDER", "openai").strip().lower()
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()

    def is_available(self) -> bool:
        """LLM mode is only available when an API key is configured."""
        return bool(self.api_key)

    def generate(self, inputs: dict[str, str]) -> dict:
        # 1. Always build the reliable local baseline first. This guarantees the
        #    package has valid structured data, scoring, and exportable content.
        package = generate_package(inputs, mode=self.name)

        # 2. If no key is configured, fall back cleanly to the template output.
        if not self.is_available():
            package["mode"] = f"{TEMPLATE_MODE_FALLBACK}"
            package["mode_note"] = (
                f"No {API_KEY_ENV_VAR} found; used Template Engine Mode instead."
            )
            return package

        # 3. Attempt LLM enhancement, but never let a failure break the app.
        try:
            package = self._enhance_with_llm(inputs, package)
            package["mode"] = self.name
        except Exception as exc:  # graceful fallback
            package["mode"] = f"{TEMPLATE_MODE_FALLBACK}"
            package["mode_note"] = (
                f"LLM enhancement unavailable, used Template Engine Mode. "
                f"Reason: {exc}"
            )
        return package

    # ------------------------------------------------------------------
    # LLM integration seam
    # ------------------------------------------------------------------
    def _enhance_with_llm(self, inputs: dict[str, str], package: dict) -> dict:
        """Enhance the template baseline using a real LLM.

        >>> THIS IS WHERE A REAL LLM API CALL WOULD BE ADDED. <<<

        The recommended pattern is to keep the template baseline as a safety net
        and ask the model to rewrite/enrich specific narrative sections (e.g.
        Executive Summary, Lessons Learned) while leaving the structured data
        (RACI, risks, action items, scoring) intact so exports stay valid.

        Example (OpenAI Python SDK — install `openai` and uncomment):

            # from openai import OpenAI
            # client = OpenAI(api_key=self.api_key)
            # prompt = _build_prompt(inputs, package)
            # response = client.chat.completions.create(
            #     model=self.model,
            #     messages=[
            #         {"role": "system", "content": "You are an expert "
            #          "operations and knowledge-transfer writer."},
            #         {"role": "user", "content": prompt},
            #     ],
            # )
            # improved_summary = response.choices[0].message.content
            # package["sections"]["Executive Summary"] = improved_summary

        Example (Azure OpenAI):

            # from openai import AzureOpenAI
            # client = AzureOpenAI(
            #     api_key=self.api_key,
            #     api_version="2024-06-01",
            #     azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            # )
            # ... same chat.completions.create call using your deployment name ...

        Example (Anthropic Claude):

            # import anthropic
            # client = anthropic.Anthropic(api_key=self.api_key)
            # msg = client.messages.create(
            #     model=self.model,
            #     max_tokens=1024,
            #     messages=[{"role": "user", "content": prompt}],
            # )
            # improved_summary = msg.content[0].text

        Because no LLM SDK is bundled in this offline-first build, we raise here
        to trigger the graceful fallback in ``generate``. Replace this line with
        one of the integrations above to enable true LLM Enhanced Mode.
        """
        raise NotImplementedError(
            "LLM integration is not configured in this build. Add a provider "
            "SDK call in LLMProvider._enhance_with_llm to enable it."
        )
