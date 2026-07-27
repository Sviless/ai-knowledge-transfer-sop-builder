"""SQLite persistence for generated knowledge-transfer packages.

Each saved package is stored as a JSON blob alongside a few denormalized
columns (score, counts) that make dashboard queries fast and simple.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Optional

from .utils import DB_PATH, ensure_directories, now_iso


def _connect() -> sqlite3.Connection:
    """Open a SQLite connection with row access by column name."""
    ensure_directories()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the packages table if it does not already exist."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS packages (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                process_name    TEXT NOT NULL,
                process_owner   TEXT,
                created_at      TEXT NOT NULL,
                maturity_score  INTEGER NOT NULL,
                status          TEXT NOT NULL,
                open_risks      INTEGER NOT NULL DEFAULT 0,
                open_questions  INTEGER NOT NULL DEFAULT 0,
                action_items    INTEGER NOT NULL DEFAULT 0,
                package_json    TEXT NOT NULL
            )
            """
        )
        conn.commit()


def save_package(package: dict) -> int:
    """Persist a generated package and return its new row id."""
    init_db()
    inputs = package["inputs"]
    maturity = package["maturity"]
    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO packages (
                process_name, process_owner, created_at, maturity_score,
                status, open_risks, open_questions, action_items, package_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                inputs.get("process_name") or "Untitled Process",
                inputs.get("process_owner") or "",
                now_iso(),
                maturity["score"],
                maturity["status"],
                len(package.get("risks", [])),
                len(package.get("open_questions", [])),
                len(package.get("action_items", [])),
                json.dumps(package),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def list_packages() -> list[dict]:
    """Return metadata for all saved packages, newest first."""
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, process_name, process_owner, created_at, maturity_score,
                   status, open_risks, open_questions, action_items
            FROM packages
            ORDER BY id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_package(package_id: int) -> Optional[dict]:
    """Return the full stored package dict for a given id, or None."""
    init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT package_json FROM packages WHERE id = ?", (package_id,)
        ).fetchone()
    if not row:
        return None
    return json.loads(row["package_json"])


def delete_package(package_id: int) -> None:
    """Delete a saved package by id."""
    init_db()
    with _connect() as conn:
        conn.execute("DELETE FROM packages WHERE id = ?", (package_id,))
        conn.commit()


def get_dashboard_metrics() -> dict:
    """Aggregate metrics for the dashboard.

    Returns totals plus the average maturity score across all saved packages.
    """
    init_db()
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*)                     AS total_packages,
                COALESCE(AVG(maturity_score), 0) AS avg_score,
                COALESCE(SUM(open_risks), 0)     AS total_risks,
                COALESCE(SUM(open_questions), 0) AS total_questions,
                COALESCE(SUM(action_items), 0)   AS total_actions
            FROM packages
            """
        ).fetchone()
    return {
        "total_packages": int(row["total_packages"]),
        "avg_score": round(float(row["avg_score"]), 1),
        "total_risks": int(row["total_risks"]),
        "total_questions": int(row["total_questions"]),
        "total_actions": int(row["total_actions"]),
    }
