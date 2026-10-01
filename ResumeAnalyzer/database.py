from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from config import DATABASE_PATH


def initialize_database() -> None:
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                resume_text TEXT,
                job_description TEXT,
                analysis_json TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Privacy-by-default migration: older versions stored source documents in plaintext.
        # History only needs metadata + analysis JSON, so erase legacy raw text on startup.
        connection.execute("UPDATE analyses SET resume_text = NULL, job_description = NULL")
        connection.commit()


def save_analysis(
    file_path: str | Path,
    resume_text: str,
    job_description: str,
    analysis: dict[str, Any],
) -> int:
    """Save analysis metadata/results without storing the original resume or job description."""
    del resume_text, job_description
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        cursor = connection.execute(
            """
            INSERT INTO analyses (file_name, resume_text, job_description, analysis_json)
            VALUES (?, NULL, NULL, ?)
            """,
            (Path(file_path).name, json.dumps(analysis)),
        )
        connection.commit()
        return int(cursor.lastrowid)


def list_recent_analyses(limit: int = 10) -> list[dict[str, Any]]:
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT id, file_name, analysis_json, created_at
            FROM analyses
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    history: list[dict[str, Any]] = []
    for row in rows:
        analysis = json.loads(row["analysis_json"])
        history.append(
            {
                "id": row["id"],
                "file_name": row["file_name"],
                "ats_score": analysis.get("ats_score", 0),
                "match_percentage": analysis.get("match_percentage", 0),
                "created_at": row["created_at"],
            }
        )
    return history
