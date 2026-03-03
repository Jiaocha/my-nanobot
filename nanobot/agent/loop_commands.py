"""Agent loop command handlers - extracts command processing from loop.py."""

from __future__ import annotations

import re
import shutil
import time
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from nanobot.bus.events import OutboundMessage

if TYPE_CHECKING:
    from nanobot.agent.loop import AgentLoop
    from nanobot.bus.events import InboundMessage
    from nanobot.session.manager import Session


class CommandHandlers:
    """
    Command handlers for agent loop.

    Extracts command processing logic (/status, /weather, /memory, etc.)
    from AgentLoop to reduce file size and improve maintainability.
    """

    def __init__(self, loop: "AgentLoop"):
        self.loop = loop

    async def handle_status(self, msg: InboundMessage) -> OutboundMessage:
        """Handle /status command - show system status."""
        return OutboundMessage(
            channel=msg.channel,
            chat_id=msg.chat_id,
            content=await self.loop._get_system_status(),
        )

    async def handle_weather(self, msg: InboundMessage, args: list[str]) -> OutboundMessage:
        """Handle /weather command - query weather."""
        city = args[0] if args else "惠州"
        await self.loop.bus.publish_outbound(
            OutboundMessage(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content=f"正在查询 {city} 天气...",
                metadata={"_progress": True, "task_start_time": time.time()},
            )
        )
        return OutboundMessage(
            channel=msg.channel,
            chat_id=msg.chat_id,
            content=await self.loop.tools.execute("exec", {"command": f'python weather_cn.py "{city}"'}),
        )

    async def handle_memory(self, msg: InboundMessage, args: list[str]) -> OutboundMessage:
        """Handle /memory command - search memory."""
        query = " ".join(args) if args else "最近"
        await self.loop.bus.publish_outbound(
            OutboundMessage(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content=f"正在检索记忆：{query}...",
                metadata={"_progress": True, "task_start_time": time.time()},
            )
        )
        result = await self.loop.tools.execute("search_memory", {"query": query, "top_k": 3})
        return OutboundMessage(
            channel=msg.channel,
            chat_id=msg.chat_id,
            content=f"<b>🧠 相关记忆：</b>\n\n{result}",
        )

    async def handle_cleanup(self, msg: InboundMessage) -> OutboundMessage:
        """Handle /cleanup command - clean cache files."""
        cache_dir = Path.home() / ".nanobot" / "media"
        try:
            count = len(list(cache_dir.glob("*"))) if cache_dir.exists() else 0
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
            cache_dir.mkdir(parents=True, exist_ok=True)

            v_status = ""
            if hasattr(self.loop.context.memory, 'vector_store') and self.loop.context.memory.vector_store:
                await self.loop.context.memory.vector_store.cleanup_old_memories(days=14)
                v_status = "及过期向量记忆"

            return OutboundMessage(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content=f"🗑️ 已清理 {count} 个缓存文件{v_status}。",
            )
        except Exception as e:
            return OutboundMessage(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content=f"清理失败：{e}",
            )

    async def handle_new(self, msg: InboundMessage, session: Session) -> OutboundMessage:
        """Handle /new command - start new session."""
        async def _background_archive(snaps, skey):
            """Background task to archive old messages."""
            lock = self.loop._consolidation_locks.setdefault(skey, asyncio.Lock())
            self.loop._consolidating.add(skey)
            try:
                async with lock:
                    from nanobot.session.manager import Session as SessionClass
                    tmp = SessionClass(key=skey)
                    tmp.messages = list(snaps)
                    await self.loop._consolidate_memory(tmp, archive_all=True)
            except Exception:
                logger.exception("BG Archival failed")
            finally:
                self.loop._consolidating.discard(skey)

        import asyncio
        snapshots = list(session.messages[session.last_consolidated:])
        if snapshots:
            asyncio.create_task(_background_archive(snapshots, session.key))

        session.clear()
        self.loop.sessions.save(session)
        self.loop.sessions.invalidate(session.key)

        return OutboundMessage(
            channel=msg.channel,
            chat_id=msg.chat_id,
            content="新会话已开始。",
        )

    async def handle_help(self, msg: InboundMessage) -> OutboundMessage:
        """Handle /help command - show help message."""
        help_text = (
            "<b>🐈 nanobot 指南</b>\n"
            "━━━━━━━━━━━━━━\n"
            "🧹 <code>/new</code> - 开启新会话\n"
            "🌤️ <code>/weather</code> - 实时天气\n"
            "🧠 <code>/memory</code> - 搜索记忆\n"
            "📊 <code>/status</code> - 系统状态\n"
            "🗑️ <code>/cleanup</code> - 清理缓存\n"
            "⏹️ <code>/stop</code> - 停止任务\n"
            "━━━━━━━━━━━━━━\n"
            "✨ 请尽情体验！"
        )
        return OutboundMessage(
            channel=msg.channel,
            chat_id=msg.chat_id,
            content=help_text,
        )

    def add_path_hints(self, content: str) -> str:
        """Add path existence hints to message content."""
        path_matches = re.findall(r'[A-Za-z]:\\[^\\/:*?"<>|\r\n]+', content)
        for p in path_matches[:2]:
            try:
                po = Path(p.strip())
                exists = "存在" if po.exists() else "不存在"
                content += f"\n\n[SYSTEM HINT: '{p}' {exists}]"
            except (OSError, ValueError) as e:
                logger.debug("Path hint failed for '{}': {}", p, e)
        return content

    def can_handle(self, cmd: str) -> bool:
        """Check if this is a built-in command."""
        return cmd in {"/status", "/weather", "/memory", "/cleanup", "/new", "/help"}

    async def dispatch(
        self,
        msg: InboundMessage,
        cmd: str,
        args: list[str],
        session: Session,
    ) -> OutboundMessage | None:
        """Dispatch command to appropriate handler."""
        if cmd == "/status":
            return await self.handle_status(msg)
        elif cmd == "/weather":
            return await self.handle_weather(msg, args)
        elif cmd == "/memory":
            return await self.handle_memory(msg, args)
        elif cmd == "/cleanup":
            return await self.handle_cleanup(msg)
        elif cmd == "/new":
            return await self.handle_new(msg, session)
        elif cmd == "/help":
            return await self.handle_help(msg)
        return None
