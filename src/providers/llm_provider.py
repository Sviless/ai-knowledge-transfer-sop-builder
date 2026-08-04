"""LLM Enhanced Mode provider (with a working Google Gemini backend).

This provider defines the seam where a real Large Language Model integration is
wired in. It ships a working **Google Gemini** backend (selected with
``LLM_PROVIDER=gemini``) and documents example seams for OpenAI, Azure OpenAI,
and Anthropic Claude. It reads its credential from the ``LLM_API_KEY``
environment variable and never hardcodes a key.

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
        # Pick a sensible default model for the selected provider.
        if self.provider_name in ("gemini", "google"):
            default_model = "gemini-2.0-flash"
        else:
            default_model = "gpt-4o-mini"
        self.model = os.getenv("LLM_MODEL", default_model).strip()

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

        The structured data (RACI, risks, action items, scoring) is always left
        intact so exports stay valid; only a narrative section (Executive
        Summary) is rewritten by the model. A working Google Gemini backend is
        included; OpenAI/Azure/Claude remain documented example seams.

        Select the backend with ``LLM_PROVIDER`` (default ``openai``):
            gemini | google  -> Google Gemini (implemented below)
            openai           -> OpenAI (example seam)
            azure            -> Azure OpenAI (example seam)
            anthropic        -> Anthropic Claude (example seam)
        """
        if self.provider_name in ("gemini", "google"):
            improved = self._call_gemini(self._build_prompt(inputs, package))
            if improved:
                package["sections"]["Executive Summary"] = improved
            return package

        # Example (OpenAI Python SDK — install `openai` and implement):
        #     from openai import OpenAI
        #     client = OpenAI(api_key=self.api_key)
        #     response = client.chat.completions.create(
        #         model=self.model,
        #         messages=[
        #             {"role": "system", "content": "You are an expert "
        #              "operations and knowledge-transfer writer."},
        #             {"role": "user", "content": self._build_prompt(inputs, package)},
        #         ],
        #     )
        #     package["sections"]["Executive Summary"] = (
        #         response.choices[0].message.content or "").strip()
        #     return package
        #
        # Example (Azure OpenAI): use `AzureOpenAI` with your deployment name.
        # Example (Anthropic Claude): use `anthropic.Anthropic(...).messages.create`.
        raise NotImplementedError(
            f"LLM_PROVIDER='{self.provider_name}' is an example-only seam in this "
            "build. Set LLM_PROVIDER=gemini for a working backend, or implement "
            "the SDK call for your provider in LLMProvider._enhance_with_llm."
        )

    # ------------------------------------------------------------------
    # Google Gemini backend
    # ------------------------------------------------------------------
    def _build_prompt(self, inputs: dict[str, str], package: dict) -> str:
        """Build the rewrite prompt from the current summary and process name."""
        current = package.get("sections", {}).get("Executive Summary", "")
        process = inputs.get("process_name") or inputs.get("title") or "this process"
        return (
            "Rewrite the following Executive Summary for a knowledge-transfer "
            "document so it reads clearly and professionally. Stay factual and "
            "do not invent details that are not present.\n\n"
            f"Process: {process}\n\n"
            f"Current Executive Summary:\n{current}"
        )

    def _call_gemini(self, prompt: str) -> str:
        """Call Google Gemini and return the improved text (lazy SDK import)."""
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:  # SDK not installed
            raise RuntimeError(
                "Google Gemini support requires the google-genai SDK. "
                "Install it with: pip install google-genai"
            ) from exc

        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are an expert operations and knowledge-transfer writer."
                ),
                temperature=0.4,
            ),
        )
        return (response.text or "").strip()

