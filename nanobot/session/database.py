"""SQLite database storage for sessions."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


class SessionDatabase:
    """Handles persistence of conversation history using SQLite."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._initialize_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _initialize_db(self) -> None:
        """Create tables if they don't exist."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    key TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_consolidated INTEGER DEFAULT 0,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_key TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT,
                    timestamp TEXT NOT NULL,
                    extra_data TEXT DEFAULT '{}',
                    FOREIGN KEY (session_key) REFERENCES sessions(key) ON DELETE CASCADE
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_key)")

    def save_session(self, key: str, created_at: datetime, updated_at: datetime, 
                     last_consolidated: int, metadata: dict, messages: list[dict]) -> None:
        """Save/Update session and its messages."""
        with self._get_connection() as conn:
            # Update session metadata
            conn.execute("""
                INSERT INTO sessions (key, created_at, updated_at, last_consolidated, metadata)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    updated_at = excluded.updated_at,
                    last_consolidated = excluded.last_consolidated,
                    metadata = excluded.metadata
            """, (
                key,
                created_at.isoformat(),
                updated_at.isoformat(),
                last_consolidated,
                json.dumps(metadata, ensure_ascii=False)
            ))

            # Replace all messages for this session (simplest approach for now)
            # Optimization: only insert new messages based on timestamp or ID
            conn.execute("DELETE FROM messages WHERE session_key = ?", (key,))
            
            msg_data = []
            for m in messages:
                # Separate core fields from extra data (tool_calls, etc.)
                core = {k: m[k] for k in ("role", "content", "timestamp") if k in m}
                extra = {k: v for k, v in m.items() if k not in ("role", "content", "timestamp")}
                
                content = core.get("content", "")
                if not isinstance(content, str):
                    content = json.dumps(content, ensure_ascii=False)

                msg_data.append((
                    key,
                    core.get("role", "user"),
                    content,
                    core.get("timestamp", datetime.now().isoformat()),
                    json.dumps(extra, ensure_ascii=False)
                ))

            conn.executemany("""
                INSERT INTO messages (session_key, role, content, timestamp, extra_data)
                VALUES (?, ?, ?, ?, ?)
            """, msg_data)

    def load_session(self, key: str) -> dict[str, Any] | None:
        """Load session and messages from database."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE key = ?", (key,)).fetchone()
            if not row:
                return None

            messages = []
            msg_rows = conn.execute(
                "SELECT * FROM messages WHERE session_key = ? ORDER BY id ASC", 
                (key,)
            ).fetchall()
            
            for mr in msg_rows:
                content = mr["content"]
                if content and (content.startswith("[") or content.startswith("{")):
                    try:
                        content = json.loads(content)
                    except json.JSONDecodeError:
                        pass # Keep as string if not valid JSON

                msg = {
                    "role": mr["role"],
                    "content": content,
                    "timestamp": mr["timestamp"]
                }
                if mr["extra_data"]:
                    msg.update(json.loads(mr["extra_data"]))
                messages.append(msg)

            return {
                "key": row["key"],
                "created_at": datetime.fromisoformat(row["created_at"]),
                "updated_at": datetime.fromisoformat(row["updated_at"]),
                "last_consolidated": row["last_consolidated"],
                "metadata": json.loads(row["metadata"]),
                "messages": messages
            }

    def delete_session(self, key: str) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM sessions WHERE key = ?", (key,))

    def list_sessions(self) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM sessions ORDER BY updated_at DESC").fetchall()
            return [dict(r) for r in rows]
