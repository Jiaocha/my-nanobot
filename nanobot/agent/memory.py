"""Memory system for persistent agent memory."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from nanobot.utils.helpers import ensure_dir

if TYPE_CHECKING:
    from nanobot.config.schema import Config
    from nanobot.providers.base import LLMProvider
    from nanobot.session.manager import Session


_SAVE_MEMORY_TOOL = [
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": "Save the memory consolidation result to persistent storage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "history_entry": {
                        "type": "string",
                        "description": "A paragraph (2-5 sentences) summarizing key events/decisions/topics. "
                        "Start with [YYYY-MM-DD HH:MM]. Include detail useful for grep search.",
                    },
                    "memory_update": {
                        "type": "string",
                        "description": "Full updated long-term memory as markdown. Include all existing "
                        "facts plus new ones. Return unchanged if nothing new.",
                    },
                },
                "required": ["history_entry", "memory_update"],
            },
        },
    }
]


class MemoryStore:
    """Two-layer memory: MEMORY.md (long-term facts) + HISTORY.md (grep-searchable log).
    Optionally supports vector-based memory for semantic retrieval.
    """

    def __init__(self, workspace: Path, config: Config | None = None):
        self.workspace = workspace
        self.memory_dir = ensure_dir(workspace / "memory")
        self.memory_file = self.memory_dir / "MEMORY.md"
        self.history_file = self.memory_dir / "HISTORY.md"
        self.config = config
        self.vector_store = None
        
        # Database connection for facts
        from nanobot.session.database import SessionDatabase
        db_path = workspace / "sessions" / "sessions.db"
        self.db = SessionDatabase(db_path)

        if config and config.agents.defaults.memory_mode == "vector":
            from nanobot.agent.vector_memory import VectorMemoryStore
            self.vector_store = VectorMemoryStore(config.agents.defaults.vector_memory)
            
        # Initial migration
        self._migrate_md_to_db()

    def _migrate_md_to_db(self):
        """One-time migration from MEMORY.md to SQLite facts table."""
        if self.memory_file.exists():
            try:
                content = self.memory_file.read_text(encoding="utf-8")
                if content.strip():
                    self.db.save_fact("main_memory", content)
                    logger.info("Migrated MEMORY.md to SQLite database.")
                
                # Backup and remove to prevent re-migration
                self.memory_file.rename(self.memory_file.with_suffix(".md.bak"))
            except Exception as e:
                logger.error(f"Failed to migrate MEMORY.md: {e}")

    def read_long_term(self) -> str:
        facts = self.db.get_all_facts()
        return facts.get("main_memory", "")

    def write_long_term(self, content: str) -> None:
        self.db.save_fact("main_memory", content)

    def append_history(self, entry: str) -> None:
        # Keep HISTORY.md as a plain text log for now (it's append-only and huge)
        with open(self.history_file, "a", encoding="utf-8") as f:
            f.write(entry.rstrip() + "\n\n")

    def get_memory_context(self) -> str:
        long_term = self.read_long_term()
        context = f"## Long-term Memory\n{long_term}" if long_term else ""
        if self.vector_store:
            context += "\n\n(Vector memory is enabled. Relevant memories will be retrieved automatically if tools are used.)"
        return context

    async def prune(self, provider: LLMProvider, model: str) -> bool:
        """Audit the entire MEMORY.md file to resolve contradictions, merge duplicates, and re-organize."""
        current_memory = self.read_long_term()
        if not current_memory: return True

        system_prompt = (
            "You are a Senior Memory Auditor. Your mission is to clean and refine a long-term memory file (MEMORY.md).\n\n"
            "### AUDIT RULES:\n"
            "1. CONFLICTS: If two facts contradict (e.g., 'Prefers A' vs 'Changed to B'), keep only the LATEST one.\n"
            "2. DUPLICATES: Merge similar facts into a single, concise bullet point.\n"
            "3. CATEGORIZATION: Group facts into meaningful headers (e.g., [Project], [User Preference], [Resolved Issues]).\n"
            "4. PRESERVATION: DO NOT delete essential long-term facts (preferences, core project paths, established knowledge) unless they are strictly contradicted. "
            "A cleanup is NOT a factory reset. Keep the core identity and preferences intact.\n"
            "5. OUTPUT: Return the full, cleaned Markdown. Keep it extremely organized."
        )

        try:
            logger.info("Starting long-term memory audit and pruning...")
            response = await provider.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"## MEMORY.md Content\n\n{current_memory}"},
                ],
                model=model,
                temperature=0.0  # Be objective
            )

            cleaned = response.content.strip() if response.content else ""
            if cleaned and cleaned != current_memory:
                self.write_long_term(cleaned)
                logger.info("Long-term memory successfully pruned and organized.")
            return True
        except Exception:
            logger.exception("Memory pruning error")
            return False

    async def consolidate(
        self,
        session: Session,
        provider: LLMProvider,
        model: str,
        *,
        archive_all: bool = False,
        memory_window: int = 50,
    ) -> bool:
        """Consolidate old messages into MEMORY.md + HISTORY.md via LLM tool call.

        Returns True on success (including no-op), False on failure.
        """
        if archive_all:
            old_messages = session.messages
            keep_count = 0
            logger.info("Memory consolidation (archive_all): {} messages", len(session.messages))
        else:
            keep_count = memory_window // 2
            if len(session.messages) <= keep_count:
                return True
            if len(session.messages) - session.last_consolidated <= 0:
                return True
            old_messages = session.messages[session.last_consolidated:-keep_count]
            if not old_messages:
                return True
            logger.info("Memory consolidation: {} to consolidate, {} keep", len(old_messages), keep_count)

        lines = []
        for m in old_messages:
            if not m.get("content"):
                continue
            tools = f" [tools: {', '.join(m['tools_used'])}]" if m.get("tools_used") else ""
            lines.append(f"[{m.get('timestamp', '?')[:16]}] {m['role'].upper()}{tools}: {m['content']}")

        current_memory = self.read_long_term()
        # High-quality consolidation prompt with Few-Shot examples
        system_prompt = (
            "You are a Senior Memory Architect. Your goal is to distill conversations into high-value facts.\n\n"
            "### DISTILLATION GUIDELINES:\n"
            "1. EXTRACT: User preferences, project paths, key technical decisions, resolved bugs, and specific dates.\n"
            "2. IGNORE: Greetings, small talk, tool output noise, and transient process updates.\n"
            "3. FORMAT: Use '[Topic] Fact' style. Be extremely concise.\n\n"
            "### EXAMPLES:\n"
            "- Good: [Tech Preference] User prefers Python/Pytest for automation.\n"
            "- Good: [Path] Project 'nanobot' is at C:\\Users\\Administrator\\nanobot.\n"
            "- Good: [Bug Fix] Fixed Qdrant timeout by setting embedding_timeout=3.0.\n"
            "- Bad: User said hello and asked for weather.\n"
            "- Bad: Agent called web_search tool."
        )

        user_content = f"## Current Context\n{current_memory or '(None)'}\n\n## Conversation Segment\n{chr(10).join(lines)}"

        try:
            response = await provider.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                tools=_SAVE_MEMORY_TOOL,
                model=model,
            )

            args = None
            if response.tool_calls:
                raw_args = response.tool_calls[0].arguments
                if isinstance(raw_args, str):
                    try:
                        args = json.loads(raw_args)
                    except json.JSONDecodeError:
                        logger.debug("Failed to parse JSON string from tool_calls[0].arguments")
                else:
                    args = raw_args
            elif response.content:
                # Robust extraction of JSON from text
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    try:
                        args = json.loads(json_match.group(0))
                    except json.JSONDecodeError as e:
                        logger.debug("Failed to parse JSON from memory consolidation: {}", e)

            success = False
            if args and isinstance(args, dict):
                # Ensure memory directory exists before writing
                self.memory_dir.mkdir(parents=True, exist_ok=True)
                
                if entry := args.get("history_entry"):
                    summary_text = entry if isinstance(entry, str) else json.dumps(entry)
                    self.append_history(summary_text)
                    success = True
                    if self.vector_store:
                        # Deep indexing: Summary + raw segments
                        import asyncio
                        # Store summary
                        asyncio.create_task(self.vector_store.add_memory(f"[Summary] {summary_text}"))
                        # Store raw key segments (first and last parts often contain intent/conclusion)
                        if len(lines) > 2:
                            raw_context = "\n".join(lines[:3] + ["..."] + lines[-3:])
                            asyncio.create_task(self.vector_store.add_memory(f"[Context] {raw_context}"))

                if update := args.get("memory_update"):
                    new_val = update if isinstance(update, str) else json.dumps(update)
                    if new_val != current_memory:
                        self.write_long_term(new_val)
                        success = True
            else:
                logger.warning("Memory consolidation: LLM failed to provide structured summary.")

            # For archive_all, ALWAYS return True to unblock session reset, even if summary failed
            if archive_all:
                session.last_consolidated = 0
                return True

            if success:
                session.last_consolidated = len(session.messages) - keep_count
            return success
        except Exception:
            logger.exception("Memory consolidation error")
            # Unblock session clear even on error
            return True if archive_all else False
