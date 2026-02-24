from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "dashboard.db"


def conn() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with conn() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                due_at TEXT,
                is_done INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS alarms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                time_of_day TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS timers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                seconds INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS quick_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )


def _to_list(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def get_counts() -> dict[str, int]:
    with conn() as connection:
        cursor = connection.cursor()
        notes_count = cursor.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
        reminders_open = cursor.execute("SELECT COUNT(*) FROM reminders WHERE is_done = 0").fetchone()[0]
        alarms_count = cursor.execute("SELECT COUNT(*) FROM alarms").fetchone()[0]
        timers_count = cursor.execute("SELECT COUNT(*) FROM timers").fetchone()[0]
        links_count = cursor.execute("SELECT COUNT(*) FROM quick_links").fetchone()[0]

    return {
        "notes": notes_count,
        "reminders": reminders_open,
        "alarms": alarms_count,
        "timers": timers_count,
        "quick_links": links_count,
    }


def list_notes(limit: int | None = None) -> list[dict[str, Any]]:
    sql = "SELECT * FROM notes ORDER BY id DESC"
    if limit:
        sql += f" LIMIT {int(limit)}"
    with conn() as connection:
        rows = connection.execute(sql).fetchall()
    return _to_list(rows)


def add_note(title: str, content: str) -> None:
    if not title:
        return
    with conn() as connection:
        connection.execute(
            "INSERT INTO notes (title, content, created_at) VALUES (?, ?, ?)",
            (title, content, datetime.now().isoformat(timespec="minutes")),
        )


def delete_note(note_id: int) -> None:
    with conn() as connection:
        connection.execute("DELETE FROM notes WHERE id = ?", (note_id,))


def list_reminders(limit: int | None = None) -> list[dict[str, Any]]:
    sql = "SELECT * FROM reminders ORDER BY is_done ASC, COALESCE(due_at, '9999') ASC, id DESC"
    if limit:
        sql += f" LIMIT {int(limit)}"
    with conn() as connection:
        rows = connection.execute(sql).fetchall()
    return _to_list(rows)


def add_reminder(text: str, due_at: str | None) -> None:
    if not text:
        return
    with conn() as connection:
        connection.execute(
            "INSERT INTO reminders (text, due_at, created_at) VALUES (?, ?, ?)",
            (text, due_at, datetime.now().isoformat(timespec="minutes")),
        )


def toggle_reminder(reminder_id: int) -> None:
    with conn() as connection:
        connection.execute(
            """
            UPDATE reminders
            SET is_done = CASE WHEN is_done = 1 THEN 0 ELSE 1 END
            WHERE id = ?
            """,
            (reminder_id,),
        )


def delete_reminder(reminder_id: int) -> None:
    with conn() as connection:
        connection.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))


def list_alarms() -> list[dict[str, Any]]:
    with conn() as connection:
        rows = connection.execute("SELECT * FROM alarms ORDER BY time_of_day ASC").fetchall()
    return _to_list(rows)


def add_alarm(label: str, time_of_day: str) -> None:
    if not label or not time_of_day:
        return
    with conn() as connection:
        connection.execute(
            "INSERT INTO alarms (label, time_of_day) VALUES (?, ?)",
            (label, time_of_day),
        )


def delete_alarm(alarm_id: int) -> None:
    with conn() as connection:
        connection.execute("DELETE FROM alarms WHERE id = ?", (alarm_id,))


def list_timers() -> list[dict[str, Any]]:
    with conn() as connection:
        rows = connection.execute("SELECT * FROM timers ORDER BY seconds ASC").fetchall()
    return _to_list(rows)


def add_timer(label: str, seconds: int) -> None:
    if not label or seconds <= 0:
        return
    with conn() as connection:
        connection.execute(
            "INSERT INTO timers (label, seconds) VALUES (?, ?)",
            (label, seconds),
        )


def delete_timer(timer_id: int) -> None:
    with conn() as connection:
        connection.execute("DELETE FROM timers WHERE id = ?", (timer_id,))


def list_quick_links(limit: int | None = None) -> list[dict[str, Any]]:
    sql = "SELECT * FROM quick_links ORDER BY id DESC"
    if limit:
        sql += f" LIMIT {int(limit)}"
    with conn() as connection:
        rows = connection.execute(sql).fetchall()
    return _to_list(rows)


def add_quick_link(title: str, url: str) -> None:
    if not title or not url:
        return
    with conn() as connection:
        connection.execute(
            "INSERT INTO quick_links (title, url) VALUES (?, ?)",
            (title, url),
        )


def delete_quick_link(link_id: int) -> None:
    with conn() as connection:
        connection.execute("DELETE FROM quick_links WHERE id = ?", (link_id,))


def set_setting(key: str, value: str) -> None:
    with conn() as connection:
        connection.execute(
            """
            INSERT INTO settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )


def get_settings(prefix: str | None = None) -> dict[str, str]:
    with conn() as connection:
        if prefix:
            rows = connection.execute(
                "SELECT key, value FROM settings WHERE key LIKE ?",
                (f"{prefix}%",),
            ).fetchall()
        else:
            rows = connection.execute("SELECT key, value FROM settings").fetchall()
    return {row["key"]: row["value"] for row in rows}
