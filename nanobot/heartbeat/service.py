"""Heartbeat service - periodic agent wake-up to check for tasks."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Coroutine

from loguru import logger

# 本地化支持

if TYPE_CHECKING:
    from nanobot.providers.base import LLMProvider

_HEARTBEAT_TOOL = [
    {
        "type": "function",
        "function": {
            "name": "heartbeat",
            "description": "在查看任务后报告心跳决策结果。",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["skip", "run"],
                        "description": "skip = 无需操作, run = 有活跃任务需要执行",
                    },
                    "tasks": {
                        "type": "string",
                        "description": "活跃任务的自然语言摘要（当 action 为 run 时必填）",
                    },
                },
                "required": ["action"],
            },
        },
    }
]


class HeartbeatService:
    """
    Periodic heartbeat service that wakes the agent to check for tasks.

    Phase 1 (decision): reads HEARTBEAT.md and asks the LLM — via a virtual
    tool call — whether there are active tasks.  This avoids free-text parsing
    and the unreliable HEARTBEAT_OK token.

    Phase 2 (execution): only triggered when Phase 1 returns ``run``.  The
    ``on_execute`` callback runs the task through the full agent loop and
    returns the result to deliver.
    """

    def __init__(
        self,
        workspace: Path,
        provider: LLMProvider,
        model: str,
        on_execute: Callable[[str], Coroutine[Any, Any, str]] | None = None,
        on_notify: Callable[[str], Coroutine[Any, Any, None]] | None = None,
        interval_s: int = 30 * 60,
        enabled: bool = True,
    ):
        self.workspace = workspace
        self.provider = provider
        self.model = model
        self.on_execute = on_execute
        self.on_notify = on_notify
        self.interval_s = interval_s
        self.enabled = enabled
        self._running = False
        self._task: asyncio.Task | None = None

    @property
    def heartbeat_file(self) -> Path:
        return self.workspace / "HEARTBEAT.md"

    def _read_heartbeat_file(self) -> str | None:
        if self.heartbeat_file.exists():
            try:
                return self.heartbeat_file.read_text(encoding="utf-8")
            except Exception:
                return None
        return None

    async def _decide(self, content: str) -> tuple[str, str]:
        """Phase 1: ask LLM to decide skip/run via virtual tool call.

        Returns (action, tasks) where action is 'skip' or 'run'.
        """
        system_prompt = (
            "你是一个高度专业的心跳任务审计智能体。你的职责是阅读 HEARTBEAT.md 文件并判定是否确实存在需要【立即执行】的活跃任务。\n\n"
            "### 严格规则：\n"
            "1. 忽略自身：请无视所有描述“心跳运行正常”、“心跳监控”、“系统健康状况 OK”等描述心跳服务自身存活或频率的信息。这些信息不需要你报告或确认。\n"
            "2. 仅业务：只有当存在明确的、由用户提出的业务逻辑任务（例如：总结代码、提醒、生成报告、查询数据等）且该任务未标记为【已完成】时，才返回 action='run'。\n"
            "3. 状态：如果文件仅包含说明、标题或描述心跳系统本身的任务，请务必返回 action='skip'。\n"
            "4. 绝不闲聊：不要在 heartbeat 工具调用之外回复任何内容。"
        )

        response = await self.provider.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": (
                    "请查看下方的 HEARTBEAT.md 内容，是否存在真正的活跃业务任务？\n\n"
                    f"```markdown\n{content}\n```"
                )},
            ],
            tools=_HEARTBEAT_TOOL,
            model=self.model,
        )

        if not response.has_tool_calls:
            return "skip", ""

        args = response.tool_calls[0].arguments
        action = args.get("action", "skip")
        tasks = args.get("tasks", "")

        # Prevent the heartbeat status line itself from being treated as a task
        status_keywords = ["运行正常", "状态", "OK", "心跳监控", "正常运行", "一切正常"]
        if action == "run" and tasks:
            if any(kw in tasks for kw in status_keywords) and len(tasks) < 200:
                logger.debug("Filtered out self-monitoring heartbeat message: {}", tasks)
                return "skip", ""

        return action, tasks

    async def start(self) -> None:
        """Start the heartbeat service."""
        if not self.enabled:
            logger.info("心跳功能已禁用")
            return
        if self._running:
            logger.debug("心跳功能已在运行中")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.debug("心跳功能已启动（每 {} 秒检查一次）", self.interval_s)

    def stop(self) -> None:
        """Stop the heartbeat service."""
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    async def _run_loop(self) -> None:
        """Main heartbeat loop."""
        while self._running:
            try:
                await asyncio.sleep(self.interval_s)
                if self._running:
                    await self._tick()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Heartbeat error: {}", e)

    async def _tick(self) -> None:
        """Execute a single heartbeat tick (silent mode)."""
        content = self._read_heartbeat_file()
        if not content:
            return

        try:
            action, tasks = await self._decide(content)

            if action != "run":
                return

            if self.on_execute:
                response = await self.on_execute(tasks)
                if response and self.on_notify:
                    await self.on_notify(response)
        except Exception:
            logger.exception("Heartbeat task failed")

    async def trigger_now(self) -> str | None:
        """Manually trigger a heartbeat."""
        content = self._read_heartbeat_file()
        if not content:
            return None
        action, tasks = await self._decide(content)
        if action != "run" or not self.on_execute:
            return None
        return await self.on_execute(tasks)
