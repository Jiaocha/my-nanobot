"""Session management for conversation history."""

import json
import shutil
import tiktoken
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from nanobot.session.database import SessionDatabase
from nanobot.utils.helpers import ensure_dir, safe_filename


def count_message_tokens(messages: list[dict], model: str = "gpt-4") -> int:
    """Estimate token count for a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    tokens_per_message = 3
    tokens_per_name = 1
    total_tokens = 0

    for m in messages:
        total_tokens += tokens_per_message
        for key, value in m.items():
            if key == "content":
                if isinstance(value, str):
                    total_tokens += len(encoding.encode(value))
                elif isinstance(value, list):
                    # Multi-modal content
                    for item in value:
                        if item.get("type") == "text":
                            total_tokens += len(encoding.encode(item.get("text", "")))
                        elif item.get("type") == "image_url":
                            total_tokens += 1105  # Standard high-res image cost
            elif key == "role":
                total_tokens += len(encoding.encode(value))
            elif key == "name":
                total_tokens += tokens_per_name + len(encoding.encode(value))
            elif key == "tool_calls" and value:
                total_tokens += len(encoding.encode(json.dumps(value)))
            elif key == "tool_call_id":
                total_tokens += len(encoding.encode(value))

    total_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return total_tokens


@dataclass
class Session:
    """
    A conversation session.
    Important: Messages are append-only for LLM cache efficiency.
    """

    key: str  # channel:chat_id
    messages: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    last_consolidated: int = 0  # Number of messages already consolidated to files

    def add_message(self, role: str, content: str, **kwargs: Any) -> None:
        """Add a message to the session."""
        msg = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        self.messages.append(msg)
        self.updated_at = datetime.now()

    def get_history(self, max_tokens: int = 100000, model: str = "gpt-4") -> list[dict[str, Any]]:
        """Return unconsolidated messages for LLM input, respecting token budget."""
        unconsolidated = self.messages[self.last_consolidated:]
        
        # We process messages from NEWEST to OLDEST to stay within budget
        history_to_keep = []
        current_token_count = 0
        
        # Reserve some tokens for system prompt and safety (approx 3 tokens per msg overhead)
        budget = max_tokens - 1000 

        for m in reversed(unconsolidated):
            # Estimate tokens for this single message
            msg_tokens = count_message_tokens([m], model=model)
            if current_token_count + msg_tokens > budget:
                break
            
            history_to_keep.insert(0, m)
            current_token_count += msg_tokens

        # Drop leading non-user messages to avoid orphaned tool_result blocks
        for i, m in enumerate(history_to_keep):
            if m.get("role") == "user":
                history_to_keep = history_to_keep[i:]
                break

        out: list[dict[str, Any]] = []
        for m in history_to_keep:
            entry: dict[str, Any] = {"role": m["role"], "content": m.get("content", "")}
            for k in ("tool_calls", "tool_call_id", "name"):
                if k in m:
                    entry[k] = m[k]
            out.append(entry)
        return out

    def clear(self) -> None:
        """Clear all messages and reset session to initial state."""
        self.messages = []
        self.last_consolidated = 0
        self.updated_at = datetime.now()


class SessionManager:
    """
    Manages conversation sessions.
    Sessions are stored in an SQLite database.
    """

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.sessions_dir = ensure_dir(self.workspace / "sessions")
        self.db_path = self.sessions_dir / "sessions.db"
        self.db = SessionDatabase(self.db_path)
        self._cache: dict[str, Session] = {}
        
        # Trigger migration once
        self._migrate_legacy_jsonl()

    def get_or_create(self, key: str) -> Session:
        """Get an existing session or create a new one."""
        if key in self._cache:
            return self._cache[key]

        data = self.db.load_session(key)
        if data:
            session = Session(
                key=data["key"],
                messages=data["messages"],
                created_at=data["created_at"],
                updated_at=data["updated_at"],
                last_consolidated=data["last_consolidated"],
                metadata=data["metadata"]
            )
        else:
            session = Session(key=key)

        self._cache[key] = session
        return session

    def save(self, session: Session) -> None:
        """Save a session to the database."""
        self.db.save_session(
            key=session.key,
            created_at=session.created_at,
            updated_at=session.updated_at,
            last_consolidated=session.last_consolidated,
            metadata=session.metadata,
            messages=session.messages
        )
        self._cache[session.key] = session

    def invalidate(self, key: str) -> None:
        """Remove a session from the in-memory cache."""
        self._cache.pop(key, None)

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all sessions with summary info."""
        rows = self.db.list_sessions()
        return [
            {
                "key": r["key"],
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
                "last_consolidated": r["last_consolidated"]
            }
            for r in rows
        ]

    def _migrate_legacy_jsonl(self) -> None:
        """Import data from old .jsonl files into the SQLite database."""
        jsonl_files = list(self.sessions_dir.glob("*.jsonl"))
        
        # Check global legacy path as well (~/.nanobot/sessions)
        legacy_global = Path.home() / ".nanobot" / "sessions"
        if legacy_global.exists() and legacy_global != self.sessions_dir:
            jsonl_files.extend(list(legacy_global.glob("*.jsonl")))

        if not jsonl_files:
            return

        logger.info(f"Found {len(jsonl_files)} legacy session files. Migrating to SQLite...")
        
        for path in jsonl_files:
            try:
                messages = []
                metadata = {}
                created_at = None
                last_consolidated = 0
                key = None

                with open(path, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line: continue
                        data = json.loads(line)
                        if data.get("_type") == "metadata":
                            key = data.get("key")
                            metadata = data.get("metadata", {})
                            created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
                            last_consolidated = data.get("last_consolidated", 0)
                        else:
                            messages.append(data)

                # Use stem if key not found in metadata
                if not key:
                    key = path.stem.replace("_", ":", 1)

                # Only migrate if not already in DB
                if not self.db.load_session(key):
                    self.db.save_session(
                        key=key,
                        created_at=created_at or datetime.now(),
                        updated_at=datetime.now(),
                        last_consolidated=last_consolidated,
                        metadata=metadata,
                        messages=messages
                    )
                    logger.debug(f"Migrated session: {key}")

                # Rename to .jsonl.bak to avoid re-migration
                path.rename(path.with_suffix(".jsonl.bak"))
            except Exception as e:
                logger.error(f"Failed to migrate legacy file {path}: {e}")
