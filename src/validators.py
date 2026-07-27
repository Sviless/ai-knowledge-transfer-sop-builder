"""Input validation and missing-information detection.

These helpers keep the UI honest: they block truly empty submissions and surface
the gaps that matter most for a clean knowledge transfer.
"""

from __future__ import annotations

from .utils import clean, is_blank, split_lines


# Fields that must be present for a submission to be considered valid at all.
REQUIRED_FIELDS: list[str] = ["process_name", "process_purpose"]

# Fields whose absence should be surfaced as a knowledge-transfer gap. Each maps
# to a friendly message shown in the risks / gaps log.
GAP_CHECKS: dict[str, str] = {
    "process_owner": "No process owner is clearly defined.",
    "backup_owner": "No backup owner or support role is defined.",
    "escalation_path": "No escalation path is provided.",
    "success_criteria": "No clear success criteria are defined.",
    "frequency": "No process frequency is defined.",
    "inputs": "No inputs are documented.",
    "outputs": "No outputs are documented.",
    "stakeholders": "Stakeholders are unclear or missing.",
    "tools": "Tools or systems used are missing.",
    "risks": "No known risks have been documented.",
}


def validate_required(inputs: dict[str, str]) -> list[str]:
    """Return a list of error messages for missing required fields.

    An empty list means the submission passes the minimum bar for generation.
    """
    errors: list[str] = []
    if is_blank(inputs.get("process_name")):
        errors.append("Process Name is required.")
    if is_blank(inputs.get("process_purpose")):
        errors.append("Process Purpose is required.")
    return errors


def validate_inputs(inputs: dict[str, str]) -> tuple[list[str], list[str]]:
    """Validate a submission and return (errors, warnings).

    - Errors block generation (missing required fields).
    - Warnings do not block generation but tell the user how to improve quality.
    """
    errors = validate_required(inputs)

    warnings: list[str] = []
    if len(clean(inputs.get("process_purpose"))) < 15 and not is_blank(
        inputs.get("process_purpose")
    ):
        warnings.append(
            "Process Purpose is very short. Add a sentence or two for a stronger summary."
        )
    if len(split_lines(inputs.get("steps", ""))) < 3:
        warnings.append(
            "Fewer than three steps documented. More steps produce a clearer SOP."
        )
    if is_blank(inputs.get("backup_owner")):
        warnings.append(
            "No backup owner provided. This lowers the maturity score and handoff readiness."
        )
    if is_blank(inputs.get("tools")):
        warnings.append("No tools/systems listed. Add them so the successor can get access.")

    return errors, warnings


def detect_gaps(inputs: dict[str, str]) -> list[str]:
    """Detect likely knowledge-transfer gaps based on missing information.

    Returns a list of plain-language gap statements. The scoring and risk
    modules reuse this to keep everything consistent.
    """
    gaps: list[str] = []

    # Simple presence checks for individual fields.
    for field, message in GAP_CHECKS.items():
        if is_blank(inputs.get(field)):
            gaps.append(message)

    # Steps need to be more than a single line to be considered complete.
    steps = split_lines(inputs.get("steps", ""))
    if len(steps) == 0:
        gaps.append("No step-by-step details have been documented.")
    elif len(steps) < 3:
        gaps.append("Process steps appear incomplete (fewer than three steps).")

    # A process with risks but no backup owner is a classic continuity gap.
    if not is_blank(inputs.get("risks")) and is_blank(inputs.get("backup_owner")):
        gaps.append("Risks are documented but no backup owner is assigned to them.")

    return gaps


def field_completeness(inputs: dict[str, str]) -> dict[str, bool]:
    """Return a map of {field_key: is_filled} for all provided fields."""
    return {key: not is_blank(value) for key, value in inputs.items()}
