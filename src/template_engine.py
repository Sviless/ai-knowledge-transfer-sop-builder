"""Template Engine Mode - local, rule-based knowledge-transfer generation.

This module contains the core logic that turns raw process notes into a
structured knowledge-transfer package. It uses only local Python (no external
APIs, no network) so the app runs fully offline.

The public entry point is :func:`generate_package`. The architecture is
intentionally LLM-ready: a future "LLM Enhanced Mode" could implement the same
section functions using a language model while keeping the same return shape.
"""

from __future__ import annotations

from .scoring import compute_maturity
from .sample_data import FIELD_LABELS
from .utils import (
    as_bullets,
    as_numbered,
    clean,
    is_blank,
    split_lines,
)
from .validators import detect_gaps

GENERATION_MODE = "Template Engine Mode"


# ---------------------------------------------------------------------------
# Structured data generators (used by exporters and the RACI/risk/action tabs)
# ---------------------------------------------------------------------------
def build_action_items(inputs: dict[str, str], gaps: list[str]) -> list[dict]:
    """Create a realistic action-item tracker from notes, gaps, and questions.

    Each item is a dict with a stable set of keys so it can be exported to CSV.
    Duplicate actions are skipped so the tracker stays clean.
    """
    owner = clean(inputs.get("process_owner")) or "Process Owner"
    backup = clean(inputs.get("backup_owner"))
    items: list[dict] = []
    _seen: set[str] = set()

    def add(action: str, item_owner: str, priority: str, timeframe: str) -> None:
        key = action.strip().lower()
        if key in _seen:
            return
        _seen.add(key)
        items.append(
            {
                "id": f"AI-{len(items) + 1:03d}",
                "action": action,
                "owner": item_owner,
                "priority": priority,
                "timeframe": timeframe,
                "status": "Open",
            }
        )

    # 1. Turn each detected gap into a corrective action item.
    for gap in gaps:
        add(f"Resolve gap: {gap}", owner, "High", "Within 1 week")

    # 2. Turn each open question into a follow-up action item.
    for question in split_lines(inputs.get("open_questions", "")):
        add(f"Answer open question: {question}", owner, "Medium", "Within 2 weeks")

    # 3. Standard knowledge-transfer actions that apply to almost any process.
    add("Review and confirm the documented step-by-step instructions", owner, "High", "Within 1 week")
    if backup:
        add(f"Schedule a shadowing session with backup owner ({backup})", owner, "High", "Within 2 weeks")
    else:
        add("Identify and assign a backup owner for this process", owner, "High", "Within 1 week")
    add("Store this knowledge-transfer package in a shared location", owner, "Medium", "Within 1 week")
    add("Schedule a 30-day check-in to validate the handoff", owner, "Low", "Within 30 days")

    return items


def build_raci(inputs: dict[str, str]) -> list[dict]:
    """Create a practical RACI matrix from the documented steps and stakeholders.

    RACI = Responsible, Accountable, Consulted, Informed. The process owner is
    Accountable for every step (single point of accountability). Consulted and
    Informed parties are distributed across the documented stakeholders so the
    matrix is not repetitive, and approval-style steps consult the owner.
    """
    owner = clean(inputs.get("process_owner")) or "Process Owner"
    backup = clean(inputs.get("backup_owner")) or "Backup Owner (TBD)"
    stakeholders = split_lines(inputs.get("stakeholders", ""))

    # Build rotating pools so consulted/informed vary across rows.
    others = [s for s in stakeholders if s.lower() != owner.lower()] or [
        "Key Stakeholder"
    ]

    steps = split_lines(inputs.get("steps", ""))
    if not steps:
        # Fall back to generic phases so the matrix is never empty.
        steps = [
            "Intake and preparation",
            "Execution of core work",
            "Review and approval",
            "Completion and reporting",
        ]

    approval_words = ("approv", "review", "sign", "authoriz", "escalat")

    matrix: list[dict] = []
    for idx, step in enumerate(steps):
        consulted = others[idx % len(others)]
        informed = others[(idx + 1) % len(others)]
        # Approval-style steps: the owner is consulted before proceeding.
        if any(word in step.lower() for word in approval_words):
            responsible = owner
            consulted = owner if consulted == owner else f"{consulted} + {owner}"
        else:
            responsible = owner
        matrix.append(
            {
                "task": step,
                "responsible": responsible,
                "accountable": owner,
                "consulted": consulted,
                "informed": informed,
            }
        )

    # Add a continuity row so backup coverage is explicit in the matrix.
    matrix.append(
        {
            "task": "Coverage when primary owner is unavailable",
            "responsible": backup,
            "accountable": owner,
            "consulted": others[0],
            "informed": others[-1],
        }
    )
    return matrix


def _suggest_mitigation(text: str) -> str:
    """Return a practical mitigation suggestion for a risk or gap statement."""
    lowered = text.lower()
    rules = [
        (("backup", "unavailable", "single point", "out of office"),
         "Assign and cross-train a backup owner; document coverage in the RACI."),
        (("escalation",),
         "Define a written escalation path with named contacts and thresholds."),
        (("success criteria", "definition of done"),
         "Document clear, measurable success criteria and a definition of done."),
        (("duplicate", "manual", "copy", "paste", "error"),
         "Add validation/checklists or automate the manual step to reduce errors."),
        (("deadline", "late", "miss", "time"),
         "Add reminders and a buffer; track status against the deadline."),
        (("audit", "trail", "approval"),
         "Capture approvals and changes in a structured, timestamped record."),
        (("step", "incomplete", "documented"),
         "Complete and validate the step-by-step work instructions."),
        (("stakeholder",),
         "Identify and confirm all stakeholders and their responsibilities."),
        (("tool", "system"),
         "List all tools/systems and confirm access for the successor."),
        (("input", "output"),
         "Document required inputs and expected outputs explicitly."),
        (("frequency",),
         "Define how often the process runs and its trigger."),
    ]
    for keywords, suggestion in rules:
        if any(k in lowered for k in keywords):
            return suggestion
    return "Assign an owner, define monitoring, and document a mitigation plan."


def build_risk_log(inputs: dict[str, str], gaps: list[str]) -> list[dict]:
    """Combine documented risks and detected gaps into a single risk log.

    Each entry includes a suggested mitigation to make the log actionable.
    """
    owner = clean(inputs.get("process_owner")) or "Process Owner"
    log: list[dict] = []

    def add(description: str, severity: str, source: str) -> None:
        log.append(
            {
                "id": f"R-{len(log) + 1:03d}",
                "risk": description,
                "severity": severity,
                "source": source,
                "mitigation": _suggest_mitigation(description),
                "owner": owner,
                "status": "Open",
            }
        )

    for risk in split_lines(inputs.get("risks", "")):
        add(risk, "Medium", "Documented risk")
    for gap in gaps:
        add(gap, "High", "Detected gap")

    return log


def build_open_questions(inputs: dict[str, str]) -> list[dict]:
    """Structure the open questions into a trackable log."""
    owner = clean(inputs.get("process_owner")) or "Process Owner"
    log: list[dict] = []
    for question in split_lines(inputs.get("open_questions", "")):
        log.append(
            {
                "id": f"Q-{len(log) + 1:03d}",
                "question": question,
                "owner": owner,
                "status": "Open",
            }
        )
    return log


def suggest_automation(inputs: dict[str, str]) -> list[str]:
    """Suggest automation opportunities based on signals in the notes."""
    text = " ".join(
        clean(inputs.get(key, "")).lower()
        for key in ("current_notes", "pain_points", "steps", "tools", "frequency", "outputs")
    )
    suggestions: list[str] = []

    def add_if(condition: bool, suggestion: str) -> None:
        if condition and suggestion not in suggestions:
            suggestions.append(suggestion)

    add_if("spreadsheet" in text or "track" in text,
           "Convert recurring tracking spreadsheets into a shared dashboard.")
    add_if("email" in text or "inbox" in text or "intake" in text,
           "Replace ad-hoc email intake with a structured intake form.")
    add_if("follow" in text or "reminder" in text or "action" in text,
           "Set up automated reminders for action items and follow-ups.")
    add_if("owner" in text or "ownership" in text or True,
           "Store ownership and process metadata in a structured database.")
    add_if("step" in text or "checklist" in text or True,
           "Create a standardized checklist to make the process repeatable.")
    add_if("status" in text or "summary" in text or "report" in text,
           "Automatically generate recurring status summaries.")
    add_if("approval" in text or "approve" in text,
           "Use a workflow automation tool for approvals and sign-offs.")
    add_if("manual" in text or "copy" in text or "paste" in text,
           "Automate manual copy/paste steps with a lightweight script or integration.")

    return suggestions


# ---------------------------------------------------------------------------
# Narrative section generators (Markdown strings)
# ---------------------------------------------------------------------------
def _executive_summary(inputs: dict, maturity: dict, gaps: list[str]) -> str:
    name = clean(inputs.get("process_name")) or "This process"
    owner = clean(inputs.get("process_owner")) or "an unassigned owner"
    purpose = clean(inputs.get("process_purpose")) or "No purpose was provided."
    return (
        f"**{name}** is owned by {owner}. {purpose}\n\n"
        f"Based on the information provided, this process has a maturity score of "
        f"**{maturity['score']}/100** ({maturity['status']}). "
        f"{len(gaps)} knowledge-transfer gap(s) were detected that should be "
        f"addressed before a clean handoff."
    )


def _process_overview(inputs: dict) -> str:
    parts = [
        f"**Purpose:** {clean(inputs.get('process_purpose')) or '_Not provided._'}",
        f"**Business / Operational Problem:** "
        f"{clean(inputs.get('business_problem')) or '_Not provided._'}",
        f"**Frequency:** {clean(inputs.get('frequency')) or '_Not provided._'}",
        f"**Success Criteria:** {clean(inputs.get('success_criteria')) or '_Not provided._'}",
    ]
    notes = clean(inputs.get("current_notes"))
    if notes:
        parts.append(f"\n**Current Process Notes:**\n\n{notes}")
    return "\n\n".join(parts)


def _sop(inputs: dict) -> str:
    name = clean(inputs.get("process_name")) or "the process"
    owner = clean(inputs.get("process_owner")) or "Process Owner"
    freq = clean(inputs.get("frequency")) or "As needed"
    header = (
        f"**Standard Operating Procedure for {name}**\n\n"
        f"- **Owner:** {owner}\n"
        f"- **Frequency:** {freq}\n"
        f"- **Objective:** {clean(inputs.get('process_purpose')) or 'Not provided.'}\n"
    )
    steps = split_lines(inputs.get("steps", ""))
    body = "\n**Procedure:**\n\n" + as_numbered(
        steps, "_No procedure steps were documented. Add steps to complete the SOP._"
    )
    success = clean(inputs.get("success_criteria"))
    footer = f"\n\n**Definition of Done:** {success}" if success else ""
    return header + body + footer


def _work_instructions(inputs: dict) -> str:
    steps = split_lines(inputs.get("steps", ""))
    if not steps:
        return "_No step-by-step details were provided. Document each step so a new owner can follow along independently._"
    lines = ["Detailed work instructions derived from the documented steps:\n"]
    for idx, step in enumerate(steps, start=1):
        lines.append(f"**Step {idx}.** {step}")
        lines.append(f"   - _Expected result:_ Step {idx} completed and verified.")
        lines.append(f"   - _If something goes wrong:_ Note the issue and follow the escalation path.\n")
    return "\n".join(lines)


def _raci_section(raci: list[dict]) -> str:
    lines = [
        "| Task / Activity | Responsible | Accountable | Consulted | Informed |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in raci:
        lines.append(
            f"| {row['task']} | {row['responsible']} | {row['accountable']} "
            f"| {row['consulted']} | {row['informed']} |"
        )
    return "\n".join(lines)


def _stakeholders_section(inputs: dict) -> str:
    return as_bullets(split_lines(inputs.get("stakeholders", "")))


def _tools_section(inputs: dict) -> str:
    return as_bullets(split_lines(inputs.get("tools", "")))


def _inputs_outputs_section(inputs: dict) -> str:
    return (
        "**Inputs Required:**\n\n"
        + as_bullets(split_lines(inputs.get("inputs", "")))
        + "\n\n**Outputs Produced:**\n\n"
        + as_bullets(split_lines(inputs.get("outputs", "")))
    )


def _risk_section(risk_log: list[dict]) -> str:
    if not risk_log:
        return "_No risks or gaps detected._"
    lines = [
        "| ID | Risk / Gap | Severity | Source | Suggested Mitigation | Owner | Status |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in risk_log:
        lines.append(
            f"| {r['id']} | {r['risk']} | {r['severity']} | {r['source']} "
            f"| {r.get('mitigation', '')} | {r['owner']} | {r['status']} |"
        )
    return "\n".join(lines)


def _open_questions_section(questions: list[dict]) -> str:
    if not questions:
        return "_No open questions recorded._"
    lines = ["| ID | Open Question | Owner | Status |", "| --- | --- | --- | --- |"]
    for q in questions:
        lines.append(f"| {q['id']} | {q['question']} | {q['owner']} | {q['status']} |")
    return "\n".join(lines)


def _action_items_section(items: list[dict]) -> str:
    if not items:
        return "_No action items generated._"
    lines = [
        "| ID | Action | Owner | Priority | Timeframe | Status |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for a in items:
        lines.append(
            f"| {a['id']} | {a['action']} | {a['owner']} | {a['priority']} "
            f"| {a.get('timeframe', '')} | {a['status']} |"
        )
    return "\n".join(lines)


def _knowledge_transfer_checklist(inputs: dict) -> str:
    checks = [
        ("Process purpose documented", not is_blank(inputs.get("process_purpose"))),
        ("Step-by-step instructions documented", len(split_lines(inputs.get("steps", ""))) >= 3),
        ("Tools and systems listed", not is_blank(inputs.get("tools"))),
        ("Inputs and outputs documented", not is_blank(inputs.get("inputs")) and not is_blank(inputs.get("outputs"))),
        ("Stakeholders identified", not is_blank(inputs.get("stakeholders"))),
        ("Risks documented", not is_blank(inputs.get("risks"))),
        ("Backup owner assigned", not is_blank(inputs.get("backup_owner"))),
        ("Escalation path defined", not is_blank(inputs.get("escalation_path"))),
        ("Success criteria defined", not is_blank(inputs.get("success_criteria"))),
    ]
    return "\n".join(
        f"- [{'x' if done else ' '}] {label}" for label, done in checks
    )


def _successor_readiness_checklist(inputs: dict) -> str:
    items = [
        "Successor has read the full SOP and work instructions",
        "Successor has access to all listed tools and systems",
        "Successor has completed at least one supervised run of the process",
        "Successor knows the escalation path and key contacts",
        "Successor can locate all inputs and produce all outputs independently",
        "Successor has reviewed the risks and gaps log",
    ]
    return "\n".join(f"- [ ] {item}" for item in items)


def _onboarding_plan(inputs: dict) -> str:
    name = clean(inputs.get("process_name")) or "the process"
    return (
        "**First 30 Days - Learn**\n\n"
        f"- Read this knowledge-transfer package for {name} end to end.\n"
        "- Get access to all listed tools and systems.\n"
        "- Shadow the current owner through at least one full cycle.\n"
        "- Review the risks, gaps, and open questions logs.\n\n"
        "**Days 31-60 - Practice**\n\n"
        "- Run the process with supervision and confirm each step.\n"
        "- Resolve high-priority open questions and gaps.\n"
        "- Build or refine the standardized checklist.\n\n"
        "**Days 61-90 - Own**\n\n"
        "- Run the process independently and produce all outputs.\n"
        "- Confirm backup coverage and escalation contacts.\n"
        "- Propose and begin one automation improvement.\n"
    )


def _maturity_section(maturity: dict) -> str:
    lines = [
        f"**Overall Maturity Score: {maturity['score']}/100 - {maturity['status']}**\n",
        "Each dimension is worth up to 12.5 points (8 dimensions = 100).\n",
        "| Dimension | Score | Points | Why |",
        "| --- | --- | --- | --- |",
    ]
    for row in maturity["breakdown"]:
        pct = int(row["fraction"] * 100)
        lines.append(
            f"| {row['dimension']} | {pct}% | {row['points']} "
            f"| {row.get('detail', '')} |"
        )
    return "\n".join(lines)


def _automation_section(suggestions: list[str]) -> str:
    return as_numbered(suggestions, "_No automation opportunities identified._")


def _lessons_learned(inputs: dict) -> str:
    pain = split_lines(inputs.get("pain_points", ""))
    lines = ["**Pain points to address in the next iteration:**\n"]
    lines.append(as_bullets(pain, "_No pain points documented._"))
    lines.append(
        "\n**What is working well:** _To be completed by the process owner._"
    )
    lines.append(
        "\n**What should change:** _To be completed after the first supervised run._"
    )
    return "\n".join(lines)


def _final_handoff_summary(inputs: dict, maturity: dict, gaps: list[str],
                           action_items: list[dict]) -> str:
    name = clean(inputs.get("process_name")) or "This process"
    owner = clean(inputs.get("process_owner")) or "the current owner"
    backup = clean(inputs.get("backup_owner")) or "no backup owner (assign one)"
    open_high = sum(1 for a in action_items if a["priority"] == "High")
    return (
        f"**{name}** is documented and owned by {owner}, with {backup} as backup.\n\n"
        f"- Maturity: **{maturity['score']}/100 ({maturity['status']})**\n"
        f"- Detected gaps to close: **{len(gaps)}**\n"
        f"- High-priority action items: **{open_high}**\n\n"
        "Complete the high-priority action items and the knowledge-transfer "
        "checklist before considering this process fully handed off."
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
# The ordered section titles that make up a complete package. Kept as a module
# constant so the exporter and UI can iterate in a consistent order.
SECTION_ORDER = [
    "Executive Summary",
    "Process Overview",
    "SOP: Standard Operating Procedure",
    "Step-by-Step Work Instructions",
    "RACI Matrix",
    "Key Stakeholders",
    "Tools and Systems Used",
    "Inputs and Outputs",
    "Risks and Gaps Log",
    "Open Questions Log",
    "Action Item Tracker",
    "Knowledge Transfer Checklist",
    "Successor Readiness Checklist",
    "30/60/90-Day Onboarding Plan",
    "Process Maturity Assessment",
    "Automation Opportunity Suggestions",
    "Lessons Learned",
    "Final Handoff Summary",
]


def generate_package(inputs: dict[str, str], mode: str = GENERATION_MODE) -> dict:
    """Generate a complete knowledge-transfer package from raw inputs.

    Returns a dict containing structured data, per-section Markdown, and the
    computed maturity score. This shape is intentionally stable so a future
    "LLM Enhanced Mode" can populate the same keys.
    """
    # 1. Analyze the inputs.
    gaps = detect_gaps(inputs)
    maturity = compute_maturity(inputs)

    # 2. Build structured data.
    action_items = build_action_items(inputs, gaps)
    raci = build_raci(inputs)
    risk_log = build_risk_log(inputs, gaps)
    open_questions = build_open_questions(inputs)
    automation = suggest_automation(inputs)

    # 3. Build narrative sections (ordered dict via SECTION_ORDER).
    sections = {
        "Executive Summary": _executive_summary(inputs, maturity, gaps),
        "Process Overview": _process_overview(inputs),
        "SOP: Standard Operating Procedure": _sop(inputs),
        "Step-by-Step Work Instructions": _work_instructions(inputs),
        "RACI Matrix": _raci_section(raci),
        "Key Stakeholders": _stakeholders_section(inputs),
        "Tools and Systems Used": _tools_section(inputs),
        "Inputs and Outputs": _inputs_outputs_section(inputs),
        "Risks and Gaps Log": _risk_section(risk_log),
        "Open Questions Log": _open_questions_section(open_questions),
        "Action Item Tracker": _action_items_section(action_items),
        "Knowledge Transfer Checklist": _knowledge_transfer_checklist(inputs),
        "Successor Readiness Checklist": _successor_readiness_checklist(inputs),
        "30/60/90-Day Onboarding Plan": _onboarding_plan(inputs),
        "Process Maturity Assessment": _maturity_section(maturity),
        "Automation Opportunity Suggestions": _automation_section(automation),
        "Lessons Learned": _lessons_learned(inputs),
        "Final Handoff Summary": _final_handoff_summary(
            inputs, maturity, gaps, action_items
        ),
    }

    return {
        "mode": mode,
        "inputs": inputs,
        "maturity": maturity,
        "gaps": gaps,
        "sections": sections,
        "action_items": action_items,
        "raci": raci,
        "risks": risk_log,
        "open_questions": open_questions,
        "automation": automation,
    }
