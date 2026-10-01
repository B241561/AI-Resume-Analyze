from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

from config import DATABASE_PATH


_CREATE_ANALYSES_TABLE = """
    CREATE TABLE analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT NOT NULL,
        resume_text TEXT,
        job_description TEXT,
        analysis_json TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
"""


def initialize_database() -> None:
    with closing(sqlite3.connect(DATABASE_PATH)) as connection:
        connection.execute("BEGIN IMMEDIATE")
        try:
            columns = {
                row[1]: row
                for row in connection.execute("PRAGMA table_info(analyses)")
            }
            if not columns:
                connection.execute(_CREATE_ANALYSES_TABLE)
            elif any(columns[name][3] for name in ("resume_text", "job_description") if name in columns):
                connection.execute("ALTER TABLE analyses RENAME TO analyses_legacy")
                connection.execute(_CREATE_ANALYSES_TABLE)
                connection.execute(
                    """
                    INSERT INTO analyses (id, file_name, analysis_json, created_at)
                    SELECT id, file_name, analysis_json, created_at FROM analyses_legacy
                    """
                )
                connection.execute("DROP TABLE analyses_legacy")

            # History retains analysis metadata, never the source documents.
            connection.execute("UPDATE analyses SET resume_text = NULL, job_description = NULL")
            connection.commit()
        except Exception:
            connection.rollback()
            raise


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
        match_percentage = analysis.get("match_percentage")
        if (
            "match_available" not in analysis
            and "match_status" not in analysis
            and match_percentage == 0
            and not str(analysis.get("match_explanation", "")).strip()
        ):
            match_percentage = None
        history.append(
            {
                "id": row["id"],
                "file_name": row["file_name"],
                "ats_score": analysis.get("ats_score", 0),
                "match_percentage": match_percentage,
                "created_at": row["created_at"],
            }
        )
    return history
