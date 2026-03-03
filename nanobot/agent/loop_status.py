"""System status utilities for agent loop."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from nanobot.agent.loop import AgentLoop


class StatusCollector:
    """
    Collects and formats system status information.

    Extracted from AgentLoop to reduce file size and improve testability.
    """

    def __init__(self, loop: "AgentLoop"):
        self.loop = loop

    def _get_dir_size(self, path: Path) -> str:
        """Get directory size in human-readable format."""
        if not path.exists():
            return "0 B"
        try:
            total = 0
            for entry in os.scandir(path):
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    try:
                        for sub in os.scandir(entry.path):
                            if sub.is_file():
                                total += sub.stat().st_size
                    except OSError as e:
                        logger.debug("Directory scan error: {}", e)

            for unit in ['B', 'KB', 'MB', 'GB']:
                if total < 1024:
                    return f"{total:.1f} {unit}"
                total /= 1024
            return f"{total:.2f} GB"
        except OSError as e:
            logger.warning("Size calculation failed: {}", e)
            return "..."

    async def get_status(self) -> str:
        """
        Get comprehensive system status.

        Returns formatted status string with:
        - Memory count
        - Workspace size
        - Database size
        - Average latency
        - Token usage
        """
        now = time.time()

        # Check cache (60 seconds)
        if "data" in self.loop._status_cache and (now - self.loop._status_cache.get("ts", 0) < 60):
            return self.loop._status_cache["data"]

        # Memory count
        mem_count = "就绪"
        if hasattr(self.loop.context.memory, 'vector_store') and self.loop.context.memory.vector_store:
            try:
                info = self.loop.context.memory.vector_store.client.get_collection(
                    collection_name=self.loop.context.memory.vector_store.collection_name
                )
                points_count = getattr(info, 'points_count', 0) or 0
                mem_count = f"{points_count} 条"
            except Exception as e:
                logger.debug("Vector DB status check failed: {}", e)
                mem_count = "已连接"

        # Directory sizes
        home = Path.home() / ".nanobot"
        workspace_size = self._get_dir_size(home / "workspace")
        db_size = self._get_dir_size(home / "qdrant_db")

        # Average latency
        if self.loop._recent_latencies:
            avg_latency = f"{sum(self.loop._recent_latencies) / len(self.loop._recent_latencies):.2f}s"
        else:
            avg_latency = "N/A"

        # Token usage
        total_tokens = self.loop._token_usage['prompt'] + self.loop._token_usage['completion']
        prompt_tokens = self.loop._token_usage['prompt']
        completion_tokens = self.loop._token_usage['completion']
        tokens = f"{total_tokens} (↑{prompt_tokens} ↓{completion_tokens})"

        # Active tasks
        active = sum(1 for tasks in self.loop._active_tasks.values() for _ in tasks)
        subagents = self.loop.subagents.get_running_count()

        # Build status message
        status = f"""📊 **系统状态**

🧠 **记忆**: {mem_count}
💾 **工作区**: {workspace_size}
🗄️ **数据库**: {db_size}
⏱️ **平均延迟**: {avg_latency}
🎫 **Token 使用**: {tokens}
📌 **活动任务**: {active}
🤖 **子智能体**: {subagents}
"""

        # Cache for 60 seconds
        self.loop._status_cache["data"] = status
        self.loop._status_cache["ts"] = now

        return status
