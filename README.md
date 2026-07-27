# 📘 AI Knowledge Transfer & SOP Builder

A local-first web application that transforms unstructured process notes,
handoff information, and operational knowledge into a **structured knowledge
transfer package** — complete with SOPs, a RACI matrix, risk and gap logs,
action trackers, onboarding plans, and handoff checklists.

Built with **Python + Streamlit + SQLite**. Runs entirely offline. **No API key
or internet connection required.**

---

## 1. Project Overview

Knowledge lives in people's heads, scattered spreadsheets, and email threads.
When someone leaves, changes roles, or goes on leave, that knowledge is at risk.
This tool captures rough process notes and instantly produces professional,
standardized documentation that a successor could actually follow — reducing
transition risk and improving business continuity.

The app ships with a modular, pluggable generation architecture and two modes:
**Template Engine Mode** (the default) is a transparent, rule-based engine that
interprets your notes, organizes them, detects missing information, scores
process maturity, and suggests automation opportunities — fully offline, no API
key. **LLM Enhanced Mode** is an optional provider that connects to a language
model via the `LLM_API_KEY` environment variable and gracefully falls back to
Template Engine Mode whenever a key is absent or an error occurs.

## 2. Problem This Tool Solves

- **Tribal knowledge**: critical processes depend on one person's memory.
- **Inconsistent documentation**: every handoff doc looks different (or doesn't exist).
- **Transition risk**: departures and role changes cause dropped balls.
- **No handoff readiness signal**: no objective way to tell if a process is ready to hand off.

This app standardizes documentation, quantifies readiness with a maturity score,
and surfaces the gaps that matter before they cause problems.

## 3. Key Features

- **18-section knowledge transfer package** generated from a single form.
- **Two generation modes**: default **Template Engine Mode** (offline, no key)
  and optional **LLM Enhanced Mode** (via `LLM_API_KEY`) behind a clean provider
  interface, with automatic fallback.
- **Process maturity score (0–100)** with a Green / Yellow / Red readiness status.
- **Automatic gap & risk detection** (missing backup owner, no escalation path, etc.).
- **Auto-generated RACI matrix** from your steps and stakeholders.
- **Realistic action-item tracker** built from gaps and open questions.
- **Automation opportunity suggestions** based on signals in your notes.
- **Exports**: full **Markdown** package, plus **CSV** for action items, RACI, and risks.
- **Local SQLite storage**: save, browse, reload, and delete packages.
- **Dashboard**: total packages, average maturity, open risks/questions, action items.
- **Sample data loader** for instant demos (generic, non-confidential).

## 4. Technology Stack

| Layer          | Technology            |
| -------------- | --------------------- |
| Language       | Python 3.9+           |
| UI             | Streamlit             |
| Storage        | SQLite (standard lib) |
| Data handling  | pandas                |
| Exports        | Markdown, CSV         |

## 5. Folder Structure

```
ai-knowledge-transfer-builder/
├── app.py                  # Streamlit UI: form, tabs, dashboard, exports
├── requirements.txt        # Dependencies (streamlit, pandas)
├── README.md               # This file
├── data/
│   └── knowledge_transfer.db   # SQLite DB (created automatically at runtime)
├── outputs/                # Saved Markdown exports land here
└── src/
    ├── __init__.py
    ├── template_engine.py  # Template Engine Mode generation logic
    ├── db.py               # SQLite create/save/retrieve/metrics
    ├── exporters.py        # Markdown + CSV exporters
    ├── scoring.py          # Process maturity scoring + readiness status
    ├── validators.py       # Input validation + missing-field detection
    ├── sample_data.py      # Generic sample process + field definitions
    ├── utils.py            # Shared helpers (paths, text parsing, formatting)
    └── providers/          # Pluggable generation backends
        ├── __init__.py         # Provider factory (get_provider) + mode list
        ├── base_provider.py    # Abstract provider interface
        ├── template_provider.py# Template Engine Mode (default, always available)
        └── llm_provider.py     # LLM Enhanced Mode (optional, uses LLM_API_KEY)
```

## 6. Setup Instructions

```bash
# 1. (Recommended) Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
```

> **Windows tip — avoid the most common "it won't run" issue:** always launch
> the app with `python -m streamlit run app.py` (see section 7). The short
> `streamlit run app.py` command only works if Python's `Scripts` folder is on
> your system `PATH`, which is often not the case on a fresh install. Using
> `python -m streamlit` sidesteps this entirely.

## 7. How to Run the App

```bash
python -m streamlit run app.py
```

Streamlit will open the app in your browser (typically at
`http://localhost:8501`). No API key, no configuration, no internet needed.

> **Note:** `python -m streamlit run app.py` is the most reliable command. The
> shorter `streamlit run app.py` only works if Python's `Scripts` folder is on
> your system `PATH`. If you see
> `'streamlit' is not recognized as ... a cmdlet ... or operable program`, use
> the `python -m streamlit` form above (or add the Scripts folder to PATH).

## 8. Example Use Case

An operations manager needs to hand off a **monthly vendor invoice
reconciliation** process before going on leave.

1. Click **Load sample process** in the sidebar (or type your own notes).
2. Click **Generate Knowledge Transfer Package**.
3. Review the maturity score (e.g., *Yellow — Needs Improvement*) and the
   detected gaps (e.g., *No backup owner defined*).
4. Explore the RACI matrix, risk log, and action items in the structured tabs.
5. Click **Save Package**, then export the full document to **Markdown** and the
   action items / RACI / risks to **CSV** for sharing.

Everything above is generic and contains no confidential information.

## 9. Portfolio Value

This project demonstrates a blend of skills that map directly to program/project
management, operations, and applied-AI roles:

- **AI workflow automation**: turning messy input into structured, useful output.
- **Process documentation & operational excellence**: SOPs, RACI, checklists.
- **Knowledge management & business continuity**: handoff readiness and risk reduction.
- **Software engineering**: clean modular architecture, local persistence, exports.
- **LLM-ready design**: a clear seam for adding an LLM Enhanced Mode later.

## 10. Possible Future Enhancements

- **Fully wired LLM Enhanced Mode** (add a provider SDK call in `llm_provider.py`).
- **Document upload** (paste-in files, meeting transcripts).
- **PDF and DOCX export** in addition to Markdown/CSV.
- **RAG-based document Q&A** over saved packages.
- **Source attribution** linking generated content back to input notes.
- **Multi-user support** and **authentication**.
- **Cloud deployment** with a shared database.

## 11. Resume Bullets

- Built a local-first AI Knowledge Transfer & SOP Builder using Python, Streamlit, and SQLite to convert unstructured notes into SOPs, RACI matrices, risk logs, action trackers, onboarding plans, and handoff checklists.
- Developed a template-driven knowledge management application that improves business continuity by standardizing process documentation, handoff readiness, and operational risk tracking.
- Designed an LLM-ready architecture with Template Engine Mode, structured exports, process maturity scoring, and dashboard metrics for AI-assisted workflow automation.

---

## Generation Modes

The app supports two generation modes, selectable from the sidebar. The active
mode is always shown above the generated package.

### 1. Template Engine Mode (default)

- Uses local Python templates, rules, the scoring model, and structured
  generation logic.
- Requires **no API key**, no network, and works fully offline.
- This is the default and guarantees the app is always functional.

### 2. LLM Enhanced Mode (optional)

- A clean provider interface (`src/providers/`) ready to connect to OpenAI,
  Azure OpenAI, Anthropic Claude, or another LLM.
- Reads its credential from the **`LLM_API_KEY`** environment variable. Keys are
  never hardcoded.
- **Not required to run the app.** If `LLM_API_KEY` is not set, the app
  automatically uses Template Engine Mode.
- Generation always starts from the local template baseline, then (optionally)
  enhances narrative sections via the LLM. Any error during enhancement falls
  back gracefully to the template output — the app never crashes.

**Enabling LLM Enhanced Mode (when you add a provider SDK):**

```powershell
# Windows (PowerShell) - set the key for the current session
$env:LLM_API_KEY = "your-key-here"
python -m streamlit run app.py
```

```bash
# macOS / Linux
export LLM_API_KEY="your-key-here"
python -m streamlit run app.py
```

The LLM integration point is clearly marked in
`src/providers/llm_provider.py` (`LLMProvider._enhance_with_llm`), with example
snippets for OpenAI, Azure OpenAI, and Claude. Add one SDK call there to enable
true LLM generation — no other files need to change.

## How Template Engine Mode Works

Template Engine Mode is a **transparent, rule-based** generation engine (no
external API, no model, fully offline):

1. **Parse** — multi-line fields are split into clean lists of items.
2. **Analyze** — `validators.py` detects gaps and `scoring.py` computes maturity.
3. **Build structured data** — action items, RACI rows, a combined risk log,
   open-question log, and automation suggestions are generated with simple,
   readable rules.
4. **Render narrative** — each of the 18 sections is produced from templates that
   weave your inputs and the analysis together into professional prose and tables.

Because every rule is explicit, the output is predictable and easy to explain —
and the section functions provide a clean seam where an LLM could later plug in.

## How the Maturity Score Is Calculated

The score (0–100) is the sum of **eight equally weighted dimensions** (12.5
points each):

1. **Documentation completeness** — fraction of all fields filled in.
2. **Ownership clarity** — is a process owner named?
3. **Step clarity** — number of documented steps (caps at 6+).
4. **Risk coverage** — number of documented risks (caps at 3+).
5. **Backup coverage** — is a backup owner assigned?
6. **Escalation clarity** — is an escalation path described in enough detail?
7. **Tooling & automation maturity** — rewards documented tools/systems and
   applies a small penalty for heavy manual-effort signals (a mature process is
   systematized, not fully manual). Note: automation *opportunities* are surfaced
   separately in the Automation Opportunity Suggestions section.
8. **Open question resolution** — fewer open questions scores higher.

Every dimension also reports a plain-language "Why" (e.g., *"4 of 18 fields
completed"*), shown in the Maturity score breakdown in the app and in the
Markdown export, so the score is fully transparent.

**Readiness status:**

| Score  | Status                    | Color  |
| ------ | ------------------------- | ------ |
| 80–100 | Ready for Handoff         | 🟢 Green  |
| 50–79  | Needs Improvement         | 🟡 Yellow |
| 0–49   | Not Ready for Handoff     | 🔴 Red    |

## How to Describe This on a Resume

Use any of the three bullets in section 11 above. In interviews, emphasize:
the **business problem** (transition risk / continuity), the **objective maturity
scoring model** you designed, the **clean modular architecture** with an
LLM-ready seam, and the **practical exports** (Markdown + CSV) that make the
output immediately usable by a real team.

---

*Portfolio-safe: all sample data is fictional and generic. This project does not
reference any real company, internal system, employee, or proprietary process.*
