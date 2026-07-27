"""Generic sample data for demos and quick testing.

IMPORTANT (portfolio-safe): every value below is fictional and generic. It does
not reference any real company, system, employee, or proprietary process.
"""

from __future__ import annotations


# The canonical list of input field keys used across the whole application.
# Keeping this in one place avoids typos and keeps modules in sync.
FIELD_KEYS: list[str] = [
    "process_name",
    "process_owner",
    "process_purpose",
    "business_problem",
    "current_notes",
    "steps",
    "tools",
    "stakeholders",
    "inputs",
    "outputs",
    "risks",
    "pain_points",
    "open_questions",
    "frequency",
    "success_criteria",
    "backup_owner",
    "escalation_path",
    "additional_notes",
]

# Human-friendly labels for each field (used in the UI and exports).
FIELD_LABELS: dict[str, str] = {
    "process_name": "Process Name",
    "process_owner": "Process Owner",
    "process_purpose": "Process Purpose",
    "business_problem": "Business / Operational Problem",
    "current_notes": "Current Process Notes",
    "steps": "Step-by-Step Details Known Today",
    "tools": "Tools or Systems Used",
    "stakeholders": "Stakeholders",
    "inputs": "Inputs Required",
    "outputs": "Outputs Produced",
    "risks": "Known Risks",
    "pain_points": "Pain Points",
    "open_questions": "Open Questions",
    "frequency": "Frequency of the Process",
    "success_criteria": "Success Criteria",
    "backup_owner": "Backup Owner / Support Role",
    "escalation_path": "Escalation Path",
    "additional_notes": "Additional Notes",
}


def empty_inputs() -> dict[str, str]:
    """Return a dictionary with every field key mapped to an empty string."""
    return {key: "" for key in FIELD_KEYS}


def get_sample_inputs() -> dict[str, str]:
    """Return a fully populated, generic example process.

    Scenario: a fictional monthly vendor invoice reconciliation process for a
    generic operations team. Nothing here is real or confidential.
    """
    return {
        "process_name": "Monthly Vendor Invoice Reconciliation",
        "process_owner": "Operations Analyst (Sample Role)",
        "process_purpose": (
            "Ensure all vendor invoices for the month are matched to approved "
            "purchase orders, reconciled against the budget, and submitted for "
            "payment accurately and on time."
        ),
        "business_problem": (
            "Invoices are currently tracked across scattered spreadsheets and "
            "email threads, which leads to late payments, duplicate entries, and "
            "no clear audit trail when someone is out of office."
        ),
        "current_notes": (
            "Invoices arrive by email throughout the month. The analyst manually "
            "downloads each one, logs it in a spreadsheet, and checks it against "
            "the purchase order list. Approvals are requested over chat. At month "
            "end, a summary is emailed to the finance lead. Most of the work is "
            "manual and depends heavily on one person's tribal knowledge."
        ),
        "steps": (
            "1. Collect incoming vendor invoices from the shared inbox\n"
            "2. Log each invoice in the tracking spreadsheet\n"
            "3. Match each invoice to an approved purchase order\n"
            "4. Flag mismatches or missing purchase orders\n"
            "5. Request approval from the budget owner\n"
            "6. Submit approved invoices to the payment system\n"
            "7. Prepare and send the month-end reconciliation summary"
        ),
        "tools": (
            "Shared email inbox\n"
            "Spreadsheet tracker\n"
            "Team chat tool\n"
            "Generic accounts-payable system\n"
            "Cloud file storage"
        ),
        "stakeholders": (
            "Operations Analyst\n"
            "Finance Lead\n"
            "Budget Owner\n"
            "Vendors\n"
            "Procurement Coordinator"
        ),
        "inputs": (
            "Vendor invoices\n"
            "Approved purchase order list\n"
            "Monthly budget figures"
        ),
        "outputs": (
            "Reconciled invoice tracker\n"
            "Approved payment batch\n"
            "Month-end reconciliation summary"
        ),
        "risks": (
            "Single point of failure if the analyst is unavailable\n"
            "Duplicate payments due to manual entry\n"
            "Missed month-end deadline\n"
            "No clear audit trail for approvals"
        ),
        "pain_points": (
            "Too much manual copy-paste\n"
            "Approvals get lost in chat\n"
            "Hard to know current status mid-month"
        ),
        "open_questions": (
            "Who approves invoices when the budget owner is on leave?\n"
            "What is the threshold for escalating a mismatch?\n"
            "How long should reconciliation records be retained?"
        ),
        "frequency": "Monthly (with weekly check-ins)",
        "success_criteria": (
            "All invoices reconciled and submitted before the month-end deadline "
            "with zero duplicate payments and a complete approval trail."
        ),
        "backup_owner": "",  # Intentionally blank to demonstrate gap detection.
        "escalation_path": (
            "Analyst -> Finance Lead -> Operations Manager for unresolved "
            "mismatches over the defined threshold."
        ),
        "additional_notes": (
            "The team would like to reduce manual effort and create a repeatable, "
            "documented process that a new team member could follow independently."
        ),
    }
