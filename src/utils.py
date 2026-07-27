"""Helper utilities shared across the application.

This module keeps small, reusable helpers in one place so the rest of the
codebase stays focused on business logic.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
# Resolve important folders relative to the project root so the app works no
# matter which directory it is launched from.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
DB_PATH = DATA_DIR / "knowledge_transfer.db"


def ensure_directories() -> None:
    """Create the data and outputs folders if they do not already exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def now_iso() -> str:
    """Return the current timestamp as an ISO-8601 string (seconds precision)."""
    return datetime.now().replace(microsecond=0).isoformat(sep=" ")


def timestamp_slug() -> str:
    """Return a filesystem-friendly timestamp, e.g. 20260726_143001."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def slugify(text: str, default: str = "process") -> str:
    """Convert arbitrary text into a safe file name fragment.

    Example: "Monthly Vendor Onboarding" -> "monthly-vendor-onboarding".
    """
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text or default


def clean(text: str) -> str:
    """Trim whitespace from a string, tolerating None."""
    return (text or "").strip()


def is_blank(text: str) -> bool:
    """Return True when a value is missing or only whitespace."""
    return not clean(text)


def split_lines(text: str) -> list[str]:
    """Split a multi-line text block into a clean list of non-empty lines.

    Accepts newlines, semicolons, or bullet characters as separators so users
    can paste notes in whatever style they prefer.
    """
    if not text:
        return []
    # Normalize common separators to newlines first.
    normalized = re.sub(r"[;•]", "\n", text)
    items = []
    for raw in normalized.splitlines():
        line = raw.strip().lstrip("-*").strip()
        if line:
            items.append(line)
    return items


def word_count(text: str) -> int:
    """Return the number of words in a text block."""
    return len(clean(text).split())


def as_bullets(items: list[str], empty_message: str = "_None provided._") -> str:
    """Render a list of strings as a Markdown bullet list."""
    if not items:
        return empty_message
    return "\n".join(f"- {item}" for item in items)


def as_numbered(items: list[str], empty_message: str = "_None provided._") -> str:
    """Render a list of strings as a numbered Markdown list."""
    if not items:
        return empty_message
    return "\n".join(f"{idx}. {item}" for idx, item in enumerate(items, start=1))
