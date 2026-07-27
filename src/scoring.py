"""Process maturity scoring and readiness status.

The score is a transparent, rule-based model from 0-100 built from eight equally
weighted dimensions. Every dimension returns both a fraction (0-1) and a short,
human-readable explanation of *why* it scored that way, so the result is easy to
justify in interviews and easy to extend later.
"""

from __future__ import annotations

from .sample_data import FIELD_KEYS
from .utils import clean, is_blank, split_lines, word_count


# Each dimension contributes up to this many points. Eight dimensions * 12.5 = 100.
POINTS_PER_DIMENSION = 12.5

# Static description of what each dimension measures (shown in the UI/exports).
DIMENSION_HELP = {
    "Documentation completeness": "Share of all input fields that were filled in.",
    "Ownership clarity": "Whether a clear process owner is named.",
    "Step clarity": "How many discrete steps are documented (target: 6+).",
    "Risk coverage": "How many risks are documented (target: 3+).",
    "Backup coverage": "Whether a backup owner / support role is assigned.",
    "Escalation clarity": "Whether an escalation path is described in detail.",
    "Tooling & automation maturity": "How well tools/systems are documented and "
    "whether the process is systematized rather than fully manual.",
    "Open question resolution": "Fewer unresolved open questions scores higher.",
}


def _documentation_completeness(inputs: dict[str, str]) -> tuple[float, str]:
    """Fraction of all input fields that were filled in."""
    total = len(FIELD_KEYS)
    filled = sum(1 for key in FIELD_KEYS if not is_blank(inputs.get(key)))
    return filled / total, f"{filled} of {total} fields completed."


def _ownership_clarity(inputs: dict[str, str]) -> tuple[float, str]:
    """Reward a clearly named process owner."""
    if is_blank(inputs.get("process_owner")):
        return 0.0, "No process owner named."
    return 1.0, "Process owner is named."


def _step_clarity(inputs: dict[str, str]) -> tuple[float, str]:
    """Scale with the number of documented steps (caps at 6+ steps)."""
    steps = split_lines(inputs.get("steps", ""))
    count = len(steps)
    if count == 0:
        return 0.0, "No steps documented."
    fraction = min(count / 6.0, 1.0)
    return fraction, f"{count} step(s) documented (full credit at 6+)."


def _risk_coverage(inputs: dict[str, str]) -> tuple[float, str]:
    """Reward documented risks (caps at 3+ risks)."""
    risks = split_lines(inputs.get("risks", ""))
    count = len(risks)
    if count == 0:
        return 0.0, "No risks documented."
    fraction = min(count / 3.0, 1.0)
    return fraction, f"{count} risk(s) documented (full credit at 3+)."


def _backup_coverage(inputs: dict[str, str]) -> tuple[float, str]:
    """Full credit when a backup owner / support role exists."""
    if is_blank(inputs.get("backup_owner")):
        return 0.0, "No backup owner assigned."
    return 1.0, "Backup owner assigned."


def _escalation_clarity(inputs: dict[str, str]) -> tuple[float, str]:
    """Full credit when an escalation path is described in enough detail."""
    text = clean(inputs.get("escalation_path", ""))
    if not text:
        return 0.0, "No escalation path provided."
    if word_count(text) >= 3:
        return 1.0, "Escalation path described in detail."
    return 0.5, "Escalation path is present but very brief."


def _tooling_and_automation(inputs: dict[str, str]) -> tuple[float, str]:
    """Reward documented tooling and penalize heavy manual signals.

    A *mature* process leans on documented tools/systems rather than undocumented
    manual effort. This is intentionally the inverse of the "automation
    opportunity" idea: lots of manual work lowers maturity (and is surfaced
    separately as an improvement opportunity).
    """
    tools = split_lines(inputs.get("tools", ""))
    tool_score = min(len(tools) / 3.0, 1.0)  # full credit at 3+ documented tools

    # Detect manual-effort signals that reduce maturity.
    combined = " ".join(
        clean(inputs.get(key, "")).lower()
        for key in ("current_notes", "pain_points", "steps")
    )
    manual_signals = ["manual", "copy", "paste", "by hand", "re-type", "retype"]
    manual_hits = sum(1 for word in manual_signals if word in combined)
    manual_penalty = min(manual_hits * 0.2, 0.5)  # up to -0.5

    fraction = max(0.0, tool_score - manual_penalty)
    detail = f"{len(tools)} tool(s) documented"
    if manual_hits:
        detail += f"; {manual_hits} manual-effort signal(s) detected (penalty applied)"
    detail += "."
    return fraction, detail


def _open_question_resolution(inputs: dict[str, str]) -> tuple[float, str]:
    """Fewer open questions -> higher score (open questions reduce readiness)."""
    count = len(split_lines(inputs.get("open_questions", "")))
    if count == 0:
        return 1.0, "No open questions."
    if count <= 2:
        return 0.6, f"{count} open question(s) remaining."
    if count <= 4:
        return 0.3, f"{count} open questions remaining."
    return 0.0, f"{count} open questions remaining (too many for handoff)."


# Ordered list of (dimension label, scoring function). Each function returns
# (fraction, explanation).
_SCORERS = [
    ("Documentation completeness", _documentation_completeness),
    ("Ownership clarity", _ownership_clarity),
    ("Step clarity", _step_clarity),
    ("Risk coverage", _risk_coverage),
    ("Backup coverage", _backup_coverage),
    ("Escalation clarity", _escalation_clarity),
    ("Tooling & automation maturity", _tooling_and_automation),
    ("Open question resolution", _open_question_resolution),
]


def readiness_status(score: float) -> tuple[str, str]:
    """Map a numeric score to a (status label, color) tuple."""
    if score >= 80:
        return "Ready for Handoff", "green"
    if score >= 50:
        return "Needs Improvement", "yellow"
    return "Not Ready for Handoff", "red"


def compute_maturity(inputs: dict[str, str]) -> dict:
    """Compute the maturity score and a per-dimension breakdown.

    Returns a dict:
        {
            "score": int (0-100),
            "status": str,
            "color": str,
            "breakdown": [
                {"dimension", "fraction", "points", "measures", "detail"}, ...
            ],
        }
    """
    breakdown = []
    total = 0.0
    for label, scorer in _SCORERS:
        fraction, detail = scorer(inputs)
        fraction = max(0.0, min(1.0, fraction))
        points = fraction * POINTS_PER_DIMENSION
        total += points
        breakdown.append(
            {
                "dimension": label,
                "fraction": round(fraction, 2),
                "points": round(points, 1),
                "measures": DIMENSION_HELP.get(label, ""),
                "detail": detail,
            }
        )

    score = int(round(total))
    status, color = readiness_status(score)
    return {
        "score": score,
        "status": status,
        "color": color,
        "breakdown": breakdown,
    }
