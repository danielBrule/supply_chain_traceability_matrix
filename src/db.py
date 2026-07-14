"""SQLite persistence for product categories and question answers."""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

DB_PATH = Path(os.environ.get("SCTM_DB_PATH", "data/app.db"))


def init_db() -> None:
    """Create the local SQLite database and required tables if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                question_id TEXT NOT NULL,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE (category_id, question_id),
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


def create_category(name: str, description: str = "") -> int:
    """Create an active product category and return its ID."""
    now = _now()

    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO categories (name, description, is_active, created_at, updated_at)
            VALUES (?, ?, 1, ?, ?)
            """,
            (name.strip(), description.strip(), now, now),
        )
        return int(cursor.lastrowid)


def update_category(category_id: int, name: str, description: str = "") -> None:
    """Update a category's editable fields."""
    with _connect() as conn:
        conn.execute(
            """
            UPDATE categories
            SET name = ?, description = ?, updated_at = ?
            WHERE id = ?
            """,
            (name.strip(), description.strip(), _now(), category_id),
        )


def deactivate_category(category_id: int) -> None:
    """Soft-delete a category by marking it inactive."""
    with _connect() as conn:
        conn.execute(
            """
            UPDATE categories
            SET is_active = 0, updated_at = ?
            WHERE id = ?
            """,
            (_now(), category_id),
        )


def reactivate_category(category_id: int) -> None:
    """Restore an inactive category."""
    with _connect() as conn:
        conn.execute(
            """
            UPDATE categories
            SET is_active = 1, updated_at = ?
            WHERE id = ?
            """,
            (_now(), category_id),
        )


def delete_all_categories() -> None:
    """Permanently delete all categories and answers."""
    with _connect() as conn:
        conn.execute("DELETE FROM answers")
        conn.execute("DELETE FROM categories")


def get_active_categories() -> list[dict[str, Any]]:
    """Return active categories ordered by name."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, name, description, is_active, created_at, updated_at
            FROM categories
            WHERE is_active = 1
            ORDER BY name COLLATE NOCASE
            """
        ).fetchall()

    return [_row_to_dict(row) for row in rows]


def get_inactive_categories() -> list[dict[str, Any]]:
    """Return inactive categories ordered by name."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, name, description, is_active, created_at, updated_at
            FROM categories
            WHERE is_active = 0
            ORDER BY name COLLATE NOCASE
            """
        ).fetchall()

    return [_row_to_dict(row) for row in rows]


def get_answers(category_id: int) -> dict[str, Any]:
    """Return answers for a category keyed by question ID."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT question_id, value
            FROM answers
            WHERE category_id = ?
            ORDER BY question_id
            """,
            (category_id,),
        ).fetchall()

    return {row["question_id"]: _deserialize_value(row["value"]) for row in rows}


def save_answer(category_id: int, question_id: str, value: Any) -> None:
    """Insert or update one answer for a category/question pair."""
    now = _now()

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO answers (category_id, question_id, value, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(category_id, question_id)
            DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """,
            (category_id, question_id, _serialize_value(value), now),
        )


def get_setting(key: str, default: Any = None) -> Any:
    """Return one project setting value."""
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT value
            FROM settings
            WHERE key = ?
            """,
            (key,),
        ).fetchone()

    if row is None:
        return default

    return _deserialize_value(row["value"])


def save_setting(key: str, value: Any) -> None:
    """Insert or update one project setting."""
    now = _now()

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key)
            DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """,
            (key, _serialize_value(value), now),
        )


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def _serialize_value(value: Any) -> str:
    return json.dumps(value)


def _deserialize_value(value: str) -> Any:
    return json.loads(value)
