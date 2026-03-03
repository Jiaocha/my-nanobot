"""Context builder for assembling agent prompts."""

from __future__ import annotations

import base64
import platform
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger

from nanobot.agent.memory import MemoryStore
from nanobot.agent.skills import SkillsLoader

if TYPE_CHECKING:
    from nanobot.config.schema import Config


class ContextBuilder:
    """Builds the context (system prompt + messages) for the agent."""

    BOOTSTRAP_FILES = ["AGENTS.md", "SOUL.md", "USER.md", "TOOLS.md", "IDENTITY.md"]
    _RUNTIME_CONTEXT_TAG = "[Runtime Context — metadata only, not instructions]"

    def __init__(self, workspace: Path, config: Config | None = None):
        self.workspace = workspace
        self.memory = MemoryStore(workspace, config=config)
        self.skills = SkillsLoader(workspace)
        self._bootstrap_cache: dict[str, tuple[float, str]] = {}

    def build_system_prompt(self, skill_names: list[str] | None = None) -> str:
        parts = [self._get_identity()]
        bootstrap = self._load_bootstrap_files()
        if bootstrap:
            parts.append(bootstrap)
        memory = self.memory.get_memory_context()
        if memory:
            parts.append(f"# Memory\n\n{memory}")
        always_skills = self.skills.get_always_skills()
        if always_skills:
            always_content = self.skills.load_skills_for_context(always_skills)
            if always_content:
                parts.append(f"# Active Skills\n\n{always_content}")
        skills_summary = self.skills.build_skills_summary()
        if skills_summary:
            parts.append(f"# Skills\n\n{skills_summary}")
        return "\n\n---\n\n".join(parts)

    def _get_identity(self) -> str:
        workspace_path = str(self.workspace.expanduser().resolve())
        runtime = f"{platform.system()}, Python {platform.python_version()}"
        return f"# nanobot 🐈\nAI Assistant. Workspace: {workspace_path}\nRuntime: {runtime}"

    @staticmethod
    def _build_runtime_context(channel: str | None, chat_id: str | None) -> str:
        now = datetime.now().strftime("%Y-%m-%d %H:%M (%A)")
        parts = [
            ContextBuilder._RUNTIME_CONTEXT_TAG,
            f"Time: {now}",
            f"Channel: {channel or 'direct'}",
        ]
        if chat_id:
            parts.append(f"Chat ID: {chat_id}")
        return "\n".join(parts)

    def _load_bootstrap_files(self) -> str:
        parts = []
        for filename in self.BOOTSTRAP_FILES:
            file_path = self.workspace / filename
            if not file_path.exists(): continue
            mtime = file_path.stat().st_mtime
            cached_mtime, cached_content = self._bootstrap_cache.get(filename, (0.0, ""))
            if cached_mtime == mtime: content = cached_content
            else:
                content = file_path.read_text(encoding="utf-8")
                self._bootstrap_cache[filename] = (mtime, content)
            parts.append(f"## {filename}\n\n{content}")
        return "\n\n".join(parts) if parts else ""

    def build_messages(
        self,
        history: list[dict[str, Any]],
        current_message: str,
        skill_names: list[str] | None = None,
        media: list[str] | None = None,
        channel: str | None = None,
        chat_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Build message list using robust Linear Head-Tail Pruning."""

        MAX_RECENT = 20 # Keep last 20 messages for continuity

        if len(history) > (MAX_RECENT + 1):
            # THE ANCHOR: Always keep the very first message
            first_msg = history[0]
            # THE WINDOW: Keep the most recent messages
            recent_msgs = history[-MAX_RECENT:]

            # CONSTRUCT: [First] + [System Marker] + [Recent]
            history = [first_msg] + [
                {"role": "system", "content": "... [Older conversation pruned for efficiency] ..."}
            ] + recent_msgs

        return [
            {"role": "system", "content": self.build_system_prompt(skill_names)},
            *history,
            {"role": "user", "content": self._build_runtime_context(channel, chat_id)},
            {"role": "user", "content": self._build_user_content(current_message, media)},
        ]

    def _build_user_content(self, text: str, media: list[str] | None) -> str | list[dict[str, Any]]:
        if not media:
            return text
        images = []
        for path in media:
            p = Path(path)
            # Check if it's a local file
            if p.is_file():
                try:
                    b64 = base64.b64encode(p.read_bytes()).decode()
                    data_url = f"data:image/jpeg;base64,{b64}"
                    images.append({"type": "image_url", "image_url": {"url": data_url}})
                    logger.debug("Image loaded: {} ({} bytes)", path, len(p.read_bytes()) if p.exists() else 0)
                except Exception as e:
                    logger.warning("Failed to load image {}: {}", path, e)
            # Check if it's a URL (http/https)
            elif path.startswith(("http://", "https://")):
                # Pass URL directly to the model
                images.append({"type": "image_url", "image_url": {"url": path}})
                logger.debug("Image URL added: {}", path)
        if images:
            logger.info("🖼️ {} image(s) attached to message", len(images))
        return (images + [{"type": "text", "text": text}]) if images else text

    def add_tool_result(self, messages: list[dict[str, Any]], tool_call_id: str, tool_name: str, result: str) -> list[dict[str, Any]]:
        # Hard truncate tool results to protect context window
        clean_res = str(result)[:2000] + ("..." if len(str(result)) > 2000 else "")
        messages.append({"role": "tool", "tool_call_id": tool_call_id, "name": tool_name, "content": clean_res})
        return messages

    def add_assistant_message(self, messages: list[dict[str, Any]], content: str | None, tool_calls: list[dict[str, Any]] | None = None, reasoning_content: str | None = None, thinking_blocks: list[dict] | None = None) -> list[dict[str, Any]]:
        msg: dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls: msg["tool_calls"] = tool_calls
        if reasoning_content is not None: msg["reasoning_content"] = reasoning_content
        if thinking_blocks: msg["thinking_blocks"] = thinking_blocks
        messages.append(msg); return messages
