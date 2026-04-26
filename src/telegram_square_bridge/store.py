from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional


class MessageStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._initialize()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _initialize(self) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS message_state (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    post_id TEXT,
                    post_url TEXT,
                    code TEXT,
                    error_message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(chat_id, message_id)
                );
                """
            )

    def try_reserve_message(self, chat_id: int, message_id: int) -> bool:
        with self._get_conn() as conn:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO message_state (chat_id, message_id, status)
                VALUES (?, ?, 'received');
                """,
                (chat_id, message_id),
            )
            return cursor.rowcount > 0

    def mark_posted(
        self,
        chat_id: int,
        message_id: int,
        post_id: Optional[str],
        post_url: Optional[str],
        code: str,
    ) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                UPDATE message_state
                SET status = 'posted', post_id = ?, post_url = ?, code = ?,
                    error_message = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE chat_id = ? AND message_id = ?;
                """,
                (post_id, post_url, code, chat_id, message_id),
            )

    def mark_failed(self, chat_id: int, message_id: int, code: str, error_message: str) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """
                UPDATE message_state
                SET status = 'failed', code = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
                WHERE chat_id = ? AND message_id = ?;
                """,
                (code, error_message, chat_id, message_id),
            )
