"""AI Knowledge Transfer & SOP Builder - Streamlit application.

Run with:
    python -m streamlit run app.py

This app converts unstructured process notes into a structured knowledge-transfer
package (SOP, RACI, risks, action items, onboarding plan, and more) using local
Template Engine Mode. No API key or internet access is required.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src import db, exporters, providers
from src.sample_data import FIELD_LABELS, empty_inputs, get_sample_inputs
from src.template_engine import SECTION_ORDER
from src.utils import slugify, timestamp_slug
from src.validators import validate_inputs

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Knowledge Transfer & SOP Builder",
    page_icon="📘",
    layout="wide",
)

# Ensure the database exists before anything else.
db.init_db()

# Map maturity color names to Streamlit-friendly hex badges.
STATUS_COLORS = {"green": "#1a7f37", "yellow": "#b58900", "red": "#c0392b"}


# ---------------------------------------------------------------------------
# Session-state helpers
# ---------------------------------------------------------------------------
def _init_state() -> None:
    """Initialize session-state keys used across reruns."""
    if "form_values" not in st.session_state:
        st.session_state.form_values = empty_inputs()
    if "package" not in st.session_state:
        st.session_state.package = None
    if "saved_notice" not in st.session_state:
        st.session_state.saved_notice = ""


def _load_sample() -> None:
    """Populate the form with the generic sample process."""
    st.session_state.form_values = get_sample_inputs()
    st.session_state.package = None


def _clear_form() -> None:
    """Reset all form fields."""
    st.session_state.form_values = empty_inputs()
    st.session_state.package = None


def _status_badge(maturity: dict) -> str:
    """Return an HTML badge string for a maturity result."""
    color = STATUS_COLORS.get(maturity["color"], "#555")
    return (
        f"<span style='background:{color};color:white;padding:4px 12px;"
        f"border-radius:12px;font-weight:600;'>"
        f"{maturity['score']}/100 &middot; {maturity['status']}</span>"
    )


# ---------------------------------------------------------------------------
# UI sections
# ---------------------------------------------------------------------------
def render_sidebar() -> str:
    """Render the sidebar and return the selected generation mode."""
    with st.sidebar:
        st.header("⚙️ Settings")
        mode = st.selectbox(
            "Generation Mode",
            providers.AVAILABLE_MODES,
            index=0,
            help="Template Engine Mode runs fully offline using local rules and "
            "templates (no API key). LLM Enhanced Mode uses a language model "
            f"when the {providers.API_KEY_ENV_VAR} environment variable is set.",
        )

        # Show LLM availability so the active behavior is always clear.
        if mode == providers.LLM_MODE:
            if providers.llm_is_configured():
                st.success(
                    f"{providers.API_KEY_ENV_VAR} detected. LLM Enhanced Mode is "
                    "ready (falls back to templates on any error).",
                    icon="✅",
                )
            else:
                st.info(
                    f"No {providers.API_KEY_ENV_VAR} found. Generation will "
                    "automatically use Template Engine Mode.",
                    icon="ℹ️",
                )

        st.divider()
        st.subheader("Quick actions")
        st.button("Load sample process", use_container_width=True, on_click=_load_sample)
        st.button("Clear form", use_container_width=True, on_click=_clear_form)

        st.divider()
        st.caption(
            "Local-first · No API key required · Data stored in a local SQLite "
            "database."
        )
    return mode


def render_input_form() -> None:
    """Render the main process-input form."""
    values = st.session_state.form_values
    st.subheader("1. Enter Process Information")
    st.caption(
        "Paste rough notes as-is. Multi-item fields accept one item per line."
    )

    with st.form("process_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            values["process_name"] = st.text_input(
                FIELD_LABELS["process_name"], value=values["process_name"]
            )
            values["process_owner"] = st.text_input(
                FIELD_LABELS["process_owner"], value=values["process_owner"]
            )
            values["frequency"] = st.text_input(
                FIELD_LABELS["frequency"], value=values["frequency"]
            )
        with col2:
            values["backup_owner"] = st.text_input(
                FIELD_LABELS["backup_owner"], value=values["backup_owner"]
            )
            values["escalation_path"] = st.text_input(
                FIELD_LABELS["escalation_path"], value=values["escalation_path"]
            )
            values["success_criteria"] = st.text_input(
                FIELD_LABELS["success_criteria"], value=values["success_criteria"]
            )

        values["process_purpose"] = st.text_area(
            FIELD_LABELS["process_purpose"], value=values["process_purpose"], height=80
        )
        values["business_problem"] = st.text_area(
            FIELD_LABELS["business_problem"], value=values["business_problem"], height=80
        )
        values["current_notes"] = st.text_area(
            FIELD_LABELS["current_notes"], value=values["current_notes"], height=120
        )
        values["steps"] = st.text_area(
            FIELD_LABELS["steps"], value=values["steps"], height=140,
            help="One step per line.",
        )

        col3, col4 = st.columns(2)
        with col3:
            values["tools"] = st.text_area(
                FIELD_LABELS["tools"], value=values["tools"], height=100,
                help="One tool/system per line.",
            )
            values["inputs"] = st.text_area(
                FIELD_LABELS["inputs"], value=values["inputs"], height=100
            )
            values["risks"] = st.text_area(
                FIELD_LABELS["risks"], value=values["risks"], height=100
            )
            values["open_questions"] = st.text_area(
                FIELD_LABELS["open_questions"], value=values["open_questions"], height=100
            )
        with col4:
            values["stakeholders"] = st.text_area(
                FIELD_LABELS["stakeholders"], value=values["stakeholders"], height=100,
                help="One stakeholder per line.",
            )
            values["outputs"] = st.text_area(
                FIELD_LABELS["outputs"], value=values["outputs"], height=100
            )
            values["pain_points"] = st.text_area(
                FIELD_LABELS["pain_points"], value=values["pain_points"], height=100
            )
            values["additional_notes"] = st.text_area(
                FIELD_LABELS["additional_notes"], value=values["additional_notes"], height=100
            )

        submitted = st.form_submit_button(
            "🚀 Generate Knowledge Transfer Package",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        errors, warnings = validate_inputs(values)
        if errors:
            st.error("Please fix the following before generating:")
            for err in errors:
                st.markdown(f"- {err}")
        else:
            # Warnings do not block generation; they help improve quality.
            for warn in warnings:
                st.warning(warn, icon="⚠️")
            try:
                # Resolve the requested mode to a concrete provider. If LLM
                # Enhanced Mode is unavailable, this returns Template Engine Mode.
                provider = providers.get_provider(st.session_state.mode)
                st.session_state.package = provider.generate(values)
                st.session_state.saved_notice = ""
                st.success("Knowledge transfer package generated below.")
            except Exception as exc:  # pragma: no cover - defensive UI guard
                st.session_state.package = None
                st.error(
                    "Something went wrong while generating the package. "
                    f"Details: {exc}"
                )


def render_package(package: dict) -> None:
    """Render the generated package with tabs, metrics, and exports."""
    inputs = package["inputs"]
    maturity = package["maturity"]

    st.subheader("2. Generated Knowledge Transfer Package")
    st.caption(f"Generated with: **{package.get('mode', 'Template Engine Mode')}**")
    if package.get("mode_note"):
        st.info(package["mode_note"], icon="ℹ️")
    top1, top2, top3, top4 = st.columns(4)
    top1.markdown("**Maturity**")
    top1.markdown(_status_badge(maturity), unsafe_allow_html=True)
    top2.metric("Detected Gaps", len(package["gaps"]))
    top3.metric("Open Risks", len(package["risks"]))
    top4.metric("Action Items", len(package["action_items"]))

    # Save + export controls.
    save_col, md_col, ai_col, raci_col, risk_col = st.columns(5)
    with save_col:
        if st.button("💾 Save Package", use_container_width=True):
            try:
                new_id = db.save_package(package)
                st.session_state.saved_notice = f"Saved package #{new_id}."
            except Exception as exc:  # pragma: no cover - defensive UI guard
                st.session_state.saved_notice = ""
                st.error(f"Could not save the package to the database. Details: {exc}")
    with md_col:
        st.download_button(
            "⬇️ Markdown",
            data=exporters.to_markdown(package),
            file_name=f"{slugify(inputs.get('process_name'))}_{timestamp_slug()}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with ai_col:
        st.download_button(
            "⬇️ Action Items CSV",
            data=exporters.action_items_to_csv(package),
            file_name="action_items.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with raci_col:
        st.download_button(
            "⬇️ RACI CSV",
            data=exporters.raci_to_csv(package),
            file_name="raci_matrix.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with risk_col:
        st.download_button(
            "⬇️ Risks CSV",
            data=exporters.risks_to_csv(package),
            file_name="risks_and_gaps.csv",
            mime="text/csv",
            use_container_width=True,
        )

    if st.session_state.saved_notice:
        st.success(st.session_state.saved_notice)

    # Maturity breakdown chart.
    with st.expander("📊 Maturity score breakdown", expanded=False):
        st.caption(
            "Eight equally weighted dimensions (12.5 points each). The 'Why' "
            "column shows exactly how each score was derived."
        )
        breakdown_df = pd.DataFrame(maturity["breakdown"])
        breakdown_df["percent"] = (breakdown_df["fraction"] * 100).astype(int)
        breakdown_df = breakdown_df.rename(
            columns={
                "dimension": "Dimension",
                "percent": "Score %",
                "points": "Points",
                "detail": "Why",
            }
        )
        st.dataframe(
            breakdown_df[["Dimension", "Score %", "Points", "Why"]],
            use_container_width=True,
            hide_index=True,
        )

    # Structured data tabs.
    st.markdown("#### Structured views")
    tab_ai, tab_raci, tab_risk, tab_q, tab_auto = st.tabs(
        ["Action Items", "RACI Matrix", "Risks & Gaps", "Open Questions", "Automation"]
    )
    with tab_ai:
        st.dataframe(pd.DataFrame(package["action_items"]), use_container_width=True, hide_index=True)
    with tab_raci:
        st.dataframe(pd.DataFrame(package["raci"]), use_container_width=True, hide_index=True)
    with tab_risk:
        st.dataframe(pd.DataFrame(package["risks"]), use_container_width=True, hide_index=True)
    with tab_q:
        if package["open_questions"]:
            st.dataframe(pd.DataFrame(package["open_questions"]), use_container_width=True, hide_index=True)
        else:
            st.info("No open questions recorded.")
    with tab_auto:
        if package["automation"]:
            for suggestion in package["automation"]:
                st.markdown(f"- {suggestion}")
        else:
            st.info("No automation opportunities identified.")

    # Full narrative document.
    st.markdown("#### Full document")
    for idx, title in enumerate(SECTION_ORDER, start=1):
        with st.expander(f"{idx}. {title}", expanded=(idx <= 2)):
            st.markdown(package["sections"].get(title, "_Not available._"))


def render_saved_packages() -> None:
    """Render the saved-packages browser and delete controls."""
    st.subheader("Saved Packages")
    rows = db.list_packages()
    if not rows:
        st.info("No packages saved yet. Generate one and click **Save Package**.")
        return

    df = pd.DataFrame(rows)
    df = df.rename(
        columns={
            "id": "ID",
            "process_name": "Process",
            "process_owner": "Owner",
            "created_at": "Created",
            "maturity_score": "Score",
            "status": "Status",
            "open_risks": "Risks",
            "open_questions": "Questions",
            "action_items": "Actions",
        }
    )
    st.dataframe(df, use_container_width=True, hide_index=True)

    ids = [row["id"] for row in rows]
    col_view, col_delete = st.columns(2)
    with col_view:
        selected = st.selectbox("Select a package to view", ids, key="view_select")
        if st.button("Load selected package", use_container_width=True):
            loaded = db.get_package(int(selected))
            if loaded:
                st.session_state.package = loaded
                st.success(f"Loaded package #{selected}. See it in the Builder tab.")
    with col_delete:
        del_id = st.selectbox("Select a package to delete", ids, key="delete_select")
        if st.button("🗑️ Delete selected package", use_container_width=True):
            db.delete_package(int(del_id))
            st.warning(f"Deleted package #{del_id}.")
            st.rerun()


def render_dashboard() -> None:
    """Render aggregate dashboard metrics across all saved packages."""
    st.subheader("Dashboard")
    metrics = db.get_dashboard_metrics()
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Packages", metrics["total_packages"])
    c2.metric("Avg. Maturity", metrics["avg_score"])
    c3.metric("Open Risks", metrics["total_risks"])
    c4.metric("Open Questions", metrics["total_questions"])
    c5.metric("Action Items", metrics["total_actions"])

    rows = db.list_packages()
    if rows:
        st.markdown("#### Maturity by package")
        chart_df = pd.DataFrame(rows)[["process_name", "maturity_score"]]
        chart_df = chart_df.set_index("process_name")
        st.bar_chart(chart_df)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    _init_state()
    st.title("📘 AI Knowledge Transfer & SOP Builder")
    st.caption(
        "Transform unstructured process notes into structured SOPs, RACI "
        "matrices, risk logs, action trackers, and handoff checklists."
    )

    st.session_state.mode = render_sidebar()

    tab_builder, tab_saved, tab_dashboard = st.tabs(
        ["🛠️ Builder", "📂 Saved Packages", "📈 Dashboard"]
    )
    with tab_builder:
        render_input_form()
        if st.session_state.package:
            st.divider()
            render_package(st.session_state.package)
    with tab_saved:
        render_saved_packages()
    with tab_dashboard:
        render_dashboard()


if __name__ == "__main__":
    main()
