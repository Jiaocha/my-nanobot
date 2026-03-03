"""Agent loop: the core processing engine."""

from __future__ import annotations

import asyncio
import json
import re
import time
import weakref
from contextlib import AsyncExitStack
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Awaitable, Callable

from loguru import logger

from localization import get_translation as _t
from nanobot.agent.context import ContextBuilder
from nanobot.agent.loop_commands import CommandHandlers
from nanobot.agent.loop_status import StatusCollector
from nanobot.agent.subagent import SubagentManager
from nanobot.agent.tools.cron import CronTool
from nanobot.agent.tools.filesystem import EditFileTool, ListDirTool, ReadFileTool, WriteFileTool
from nanobot.agent.tools.memory import SearchMemoryTool
from nanobot.agent.tools.message import MessageTool
from nanobot.agent.tools.registry import ToolRegistry
from nanobot.agent.tools.shell import ExecTool
from nanobot.agent.tools.spawn import SpawnTool
from nanobot.agent.tools.web import WebFetchTool, WebSearchTool
from nanobot.bus.events import InboundMessage, OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.providers.base import LLMProvider
from nanobot.session.manager import Session, SessionManager

if TYPE_CHECKING:
    from nanobot.config.schema import ChannelsConfig, Config, ExecToolConfig
    from nanobot.cron.service import CronService


class AgentLoop:
    _TOOL_RESULT_MAX_CHARS = 2000
    _THINK_RE = re.compile(r"<think>[\s\S]*?</think>")

    def __init__(self, bus: MessageBus, provider: LLMProvider, workspace: Path, model: str | None = None, max_iterations: int = 40, temperature: float = 0.1, max_tokens: int = 4096, memory_window: int = 100, reasoning_effort: str | None = None, brave_api_key: str | None = None, web_proxy: str | None = None, exec_config: ExecToolConfig | None = None, cron_service: CronService | None = None, restrict_to_workspace: bool = False, session_manager: SessionManager | None = None, mcp_servers: dict | None = None, channels_config: ChannelsConfig | None = None, config: Config | None = None):
        import httpx

        from nanobot.config.schema import ExecToolConfig
        self.bus, self.channels_config, self.provider, self.workspace, self.model = bus, channels_config, provider, workspace, model or provider.get_default_model()
        self.max_iterations, self.temperature, self.max_tokens, self.memory_window, self.reasoning_effort = max_iterations, temperature, max_tokens, memory_window, reasoning_effort
        self.brave_api_key, self.web_proxy, self.exec_config, self.cron_service, self.restrict_to_workspace = brave_api_key, web_proxy, exec_config or ExecToolConfig(), cron_service, restrict_to_workspace
        # Vision model support
        self.vision_model = None
        self.memory_archival_model = None
        if config:
            try:
                if hasattr(config, 'agents') and hasattr(config.agents, 'defaults'):
                    self.vision_model = config.agents.defaults.vision_model
                    self.memory_archival_model = config.agents.defaults.memory_archival_model
                    if self.vision_model:
                        logger.info("👁️ Vision model configured: {}", self.vision_model)
                    if self.memory_archival_model:
                        logger.info("🧠 Dedicated memory archival model: {}", self.memory_archival_model)
            except Exception as e:
                logger.warning("Failed to load models from config: {}", e)
        self._http_client = httpx.AsyncClient(timeout=30.0, follow_redirects=True, limits=httpx.Limits(max_connections=20, max_keepalive_connections=10))
        self.context = ContextBuilder(workspace, config=config)
        if hasattr(self.context.memory, 'vector_store') and self.context.memory.vector_store: self.context.memory.vector_store.set_http_client(self._http_client)
        self.sessions = session_manager or SessionManager(workspace)
        self.tools = ToolRegistry()
        self.subagents = SubagentManager(provider=provider, workspace=workspace, bus=bus, model=self.model, temperature=self.temperature, max_tokens=self.max_tokens, reasoning_effort=reasoning_effort, brave_api_key=brave_api_key, web_proxy=web_proxy, exec_config=self.exec_config, restrict_to_workspace=restrict_to_workspace)
        self._running, self._mcp_servers, self._mcp_stack, self._mcp_connected, self._mcp_connecting = False, mcp_servers or {}, None, False, False
        self._consolidating, self._consolidation_tasks = set(), set()
        self._consolidation_locks = weakref.WeakValueDictionary()
        self._active_tasks, self._session_locks, self._recent_latencies, self._status_cache = {}, {}, [], {}
        self._token_usage = {"prompt": 0, "completion": 0}
        # Initialize helper modules
        self._cmd_handlers = CommandHandlers(self)
        self._status_collector = StatusCollector(self)
        self._register_default_tools()

    async def _get_system_status(self) -> str:
        """Get system status using StatusCollector."""
        return await self._status_collector.get_status()

    def _register_default_tools(self) -> None:
        allowed_dir = self.workspace if self.restrict_to_workspace else None
        for cls in (ReadFileTool, WriteFileTool, EditFileTool, ListDirTool): self.tools.register(cls(workspace=self.workspace, allowed_dir=allowed_dir))
        self.tools.register(ExecTool(working_dir=str(self.workspace), timeout=self.exec_config.timeout, restrict_to_workspace=self.restrict_to_workspace, path_append=self.exec_config.path_append))
        self.tools.register(WebSearchTool(api_key=self.brave_api_key, proxy=self.web_proxy))
        self.tools.register(WebFetchTool(proxy=self.web_proxy))
        self.tools.register(SearchMemoryTool(self.context.memory))
        self.tools.register(MessageTool(send_callback=self.bus.publish_outbound))
        self.tools.register(SpawnTool(manager=self.subagents))
        if self.cron_service: self.tools.register(CronTool(self.cron_service))

    async def _connect_mcp(self) -> None:
        if self._mcp_connected or self._mcp_connecting or not self._mcp_servers: return
        self._mcp_connecting = True
        from nanobot.agent.tools.mcp import connect_mcp_servers
        async def _bg():
            try:
                # 1. Warmup Vector DB in parallel
                if hasattr(self.context.memory, 'vector_store') and self.context.memory.vector_store:
                    asyncio.create_task(self.context.memory.vector_store.warmup())

                # 2. Connect MCP Servers
                self._mcp_stack = AsyncExitStack(); await self._mcp_stack.__aenter__()
                await connect_mcp_servers(self._mcp_servers, self.tools, self._mcp_stack)
                self._mcp_connected = True; logger.info("⚡ MCP Warming Complete ({} servers ready)", len(self._mcp_servers))
            except Exception as e: logger.error("MCP Warmup failed: {}", e)
            finally: self._mcp_connecting = False
        asyncio.create_task(_bg())

    def _set_tool_context(self, channel: str, chat_id: str, message_id: str | None = None) -> None:
        for name in ("message", "spawn", "cron"):
            if (tool := self.tools.get(name)) and hasattr(tool, "set_context"): tool.set_context(channel, chat_id, *([message_id] if name == "message" else []))

    @staticmethod
    def _strip_think(text: str | None) -> str | None:
        return AgentLoop._THINK_RE.sub("", text).strip() if text else None

    @staticmethod
    def _tool_hint(tool_calls: list) -> str:
        def _fmt(tc):
            args = (tc.arguments[0] if isinstance(tc.arguments, list) else tc.arguments) or {}
            val = next(iter(args.values()), None) if isinstance(args, dict) else None
            return f'{tc.name}("{str(val)[:40]}…")' if isinstance(val, str) and len(str(val)) > 40 else f'{tc.name}("{val}")' if val else tc.name
        return ", ".join(_fmt(tc) for tc in tool_calls)

    async def _run_agent_loop(self, initial_messages: list[dict], on_progress: Callable[..., Awaitable[None]] | None = None) -> tuple[str | None, list[str], list[dict]]:
        messages, iteration, final_content, tools_used = initial_messages, 0, None, []
        failure_tracker = {}

        # Check if messages contain images
        has_images = False
        for m in initial_messages:
            content = m.get("content")
            if isinstance(content, list):
                if any(c.get("type") == "image_url" for c in content):
                    has_images = True
                    break

        # Use vision model if images present and configured
        if has_images and self.vision_model:
            effective_model = self.vision_model
            logger.info("👁️ Vision model activated: {}", self.vision_model)
        else:
            effective_model = self.model

        while iteration < self.max_iterations:
            iteration += 1
            # Send progress hint on first iteration so user sees activity
            if iteration == 1 and on_progress:
                if has_images and self.vision_model:
                    await on_progress("🖼️ 正在分析图片...")
                else:
                    await on_progress("思考中...")
            import time; start_t = time.perf_counter()
            response = await self.provider.chat(
                messages=messages,
                tools=self.tools.get_definitions(),
                model=effective_model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                reasoning_effort=self.reasoning_effort
            )

            # (Token usage tracking...)
            if response.usage:
                self._token_usage["prompt"] += response.usage.get("prompt_tokens", 0)
                self._token_usage["completion"] += response.usage.get("completion_tokens", 0)

            self._recent_latencies.append(time.perf_counter() - start_t)
            if len(self._recent_latencies) > 5: self._recent_latencies.pop(0)

            if response.has_tool_calls:
                # (Lazy Wait for MCP...)
                if not self._mcp_connected and self._mcp_servers:
                    for _ in range(6):
                        if self._mcp_connected: break
                        logger.debug("⏱️ MCP Warming (Attempt {}/6)...", _+1); await asyncio.sleep(0.5)

                if on_progress:
                    clean = self._strip_think(response.content)
                    if clean: await on_progress(clean)
                    await on_progress(self._tool_hint(response.tool_calls), tool_hint=True)

                tool_call_dicts = [{"id": tc.id, "type": "function", "function": {"name": tc.name, "arguments": json.dumps(tc.arguments, ensure_ascii=False)}} for tc in response.tool_calls]
                messages = self.context.add_assistant_message(messages, response.content, tool_call_dicts, reasoning_content=response.reasoning_content, thinking_blocks=response.thinking_blocks)

                # Execute tools and track failures
                results = []
                for tc in response.tool_calls:
                    res = await self.tools.execute(tc.name, tc.arguments)
                    results.append(res)

                    # Reflection Logic: Check for persistent errors
                    if "error" in str(res).lower() or "failed" in str(res).lower():
                        failure_tracker[tc.name] = failure_tracker.get(tc.name, 0) + 1
                        if failure_tracker[tc.name] >= 2:
                            reflection_hint = (
                                f"\n\n[SYSTEM REFLECTION: Tool '{tc.name}' has failed {failure_tracker[tc.name]} times consecutively. "
                                "Your previous parameters are NOT WORKING. Stop repeating. "
                                "Re-analyze the environment (use list_dir/read_file) or try a completely different tool/strategy.]"
                            )
                            # Inject hint into the tool result to force LLM to see it
                            res = str(res) + reflection_hint
                    else:
                        failure_tracker[tc.name] = 0 # Reset on success

                for tool_call, result in zip(response.tool_calls, results):
                    messages = self.context.add_tool_result(messages, tool_call.id, tool_call.name, result)
            else:
                clean = self._strip_think(response.content)
                if response.finish_reason == "error":
                    final_content = clean or "Model error encountered."; break
                messages = self.context.add_assistant_message(messages, clean, reasoning_content=response.reasoning_content, thinking_blocks=response.thinking_blocks)
                final_content = clean; break
        # Post-loop reflection: Skill Mining
        skill_suggestion = self._mine_potential_skills(tools_used)
        if skill_suggestion:
            final_content += f"\n\n---\n💡 **技能挖掘建议**：\n{skill_suggestion}"

        return final_content, tools_used, messages

    def _mine_potential_skills(self, tools_used: list) -> str | None:
        """Analyze tool calls to suggest new permanent skills."""
        for tool_name, args, result in tools_used:
            if tool_name == "exec" and "command" in args:
                cmd = args["command"]
                # Heuristic for a 'complex' but successful command
                # 1. Long enough (> 50 chars)
                # 2. Contains some logic (&&, |, python, curl, grep)
                # 3. Was successful (result not empty and no error)
                if len(cmd) > 50 and any(kw in cmd for kw in ("&&", "|", "python", "curl", "grep", "docker")):
                    if result and "error" not in result.lower() and "failed" not in result.lower():
                        return (
                            f"我发现你刚才运行了一个复杂的命令：`{cmd[:60]}...`。\n"
                            "如果这是一个常用操作，你可以发送：`把它封装成一个叫 [名称] 的技能`，"
                            "我会帮你持久化到 skills 目录。"
                        )
        return None

    async def run(self) -> None:
        self._running = True; logger.info("智能体循环已启动")
        while self._running:
            try: msg = await asyncio.wait_for(self.bus.consume_inbound(), timeout=1.0)
            except asyncio.TimeoutError: continue
            if msg.content.strip().lower() == "/stop": await self._handle_stop(msg)
            else:
                task = asyncio.create_task(self._dispatch(msg))
                self._active_tasks.setdefault(msg.session_key, []).append(task)
                task.add_done_callback(lambda t, k=msg.session_key: self._active_tasks[k].remove(t) if k in self._active_tasks and t in self._active_tasks[k] else None)

    async def _handle_stop(self, msg: InboundMessage) -> None:
        tasks = self._active_tasks.pop(msg.session_key, [])
        cancelled = sum(1 for t in tasks if not t.done() and t.cancel())
        for t in tasks:
            try: await t
            except (asyncio.CancelledError, Exception): pass
        sub_cancelled = await self.subagents.cancel_by_session(msg.session_key)
        await self.bus.publish_outbound(OutboundMessage(channel=msg.channel, chat_id=msg.chat_id, content=f"⏹ 已停止 {cancelled + sub_cancelled} 个任务。"))

    async def _dispatch(self, msg: InboundMessage) -> None:
        lock = self._session_locks.setdefault(msg.session_key, asyncio.Lock())
        async with lock:
            try:
                response = await self._process_message(msg)
                if response: await self.bus.publish_outbound(response)
            except asyncio.CancelledError: logger.info("Task cancelled for {}", msg.session_key)
            except Exception:
                logger.exception("Error in dispatch for {}", msg.session_key)
                await self.bus.publish_outbound(OutboundMessage(channel=msg.channel, chat_id=msg.chat_id, content="系统遇到了一个错误。"))

    async def close_mcp(self) -> None:
        if self._mcp_stack:
            try: await self._mcp_stack.aclose()
            except Exception: pass
            self._mcp_stack = None

    def stop(self) -> None: self._running = False; logger.info("智能体循环停止")

    async def _process_message(self, msg: InboundMessage, session_key: str | None = None, on_progress: Callable[[str], Awaitable[None]] | None = None) -> OutboundMessage | None:
        if msg.channel == "system":
            c, cid = (msg.chat_id.split(":", 1) if ":" in msg.chat_id else ("cli", msg.chat_id))
            session = self.sessions.get_or_create(f"{c}:{cid}")
            self._set_tool_context(c, cid, msg.metadata.get("message_id"))
            # Trigger MCP warming for system-initiated tasks too
            if not self._mcp_connected and not self._mcp_connecting and self._mcp_servers:
                asyncio.create_task(self._connect_mcp())
            final, _, all_m = await self._run_agent_loop(self.context.build_messages(history=session.get_history(max_messages=self.memory_window), current_message=msg.content, channel=c, chat_id=cid))
            self._save_turn(session, all_m, 1 + len(session.messages)); self.sessions.save(session)
            return OutboundMessage(channel=c, chat_id=cid, content=final or "Task done.")

        # Ensure MCP is connected on first non-system message
        if not self._mcp_connected and not self._mcp_connecting and self._mcp_servers:
            asyncio.create_task(self._connect_mcp())

        key, task_start_time = session_key or msg.session_key, time.time()
        session = self.sessions.get_or_create(key); cmd_full = msg.content.strip()
        cmd = cmd_full.split()[0].lower() if cmd_full else ""
        args = cmd_full.split()[1:] if len(cmd_full.split()) > 1 else []

        if cmd == "/status":
            return OutboundMessage(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content=await self._get_system_status(),
            )
        if cmd == "/prune":
            await self.bus.publish_outbound(
                OutboundMessage(
                    channel=msg.channel,
                    chat_id=msg.chat_id,
                    content="正在进行记忆审计与冲突消解...",
                    metadata={"_progress": True, "task_start_time": task_start_time},
                )
            )
            ok = await self.context.memory.prune(self.provider, self.model)
            return OutboundMessage(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content="✅ 记忆审计完成！已去重并解决潜在冲突。" if ok else "❌ 记忆审计失败，请检查日志。",
            )
        if cmd == "/mcp":
            status = "<b>🛠️ MCP 服务器状态</b>\n" + "━" * 15 + "\n"
            if not self._mcp_servers:
                status += "未配置 MCP 服务器。"
            else:
                for name in self._mcp_servers:
                    icon = (
                        "🟢"
                        if self._mcp_connected
                        else ("🟡" if self._mcp_connecting else "⚪")
                    )
                    status += f"{icon} <code>{name}</code>\n"
                status += f"\n当前状态: {'已就绪' if self._mcp_connected else '待命 (首次调用激活)'}"
            return OutboundMessage(channel=msg.channel, chat_id=msg.chat_id, content=status)
        if cmd == "/tools":
            all_tools = self.tools.tool_names
            return OutboundMessage(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content=f"<b>🔧 当前可用工具 ({len(all_tools)})</b>\n\n<code>"
                + ", ".join(all_tools)
                + "</code>",
            )
        if cmd == "/config":
            cfg_info = "<b>⚙️ 当前配置摘要</b>\n" + "━" * 15 + "\n"
            cfg_info += f"模型: <code>{self.model}</code>\n"
            cfg_info += (
                f"Provider: <code>{self.provider.__class__.__name__.replace('Provider', '')}</code>\n"
            )
            cfg_info += f"工作区限制: {'开启' if self.restrict_to_workspace else '关闭'}\n"
            cfg_info += f"向量记忆: {'启用' if self.context.memory.vector_store else '禁用'}"
            return OutboundMessage(channel=msg.channel, chat_id=msg.chat_id, content=cfg_info)
        if cmd == "/weather":
            city = args[0] if args else "惠州"
            await self.bus.publish_outbound(
                OutboundMessage(
                    channel=msg.channel,
                    chat_id=msg.chat_id,
                    content=f"正在查询 {city} 天气...",
                    metadata={"_progress": True, "task_start_time": task_start_time},
                )
            )
            return OutboundMessage(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content=await self.tools.execute(
                    "exec", {"command": f"python weather_cn.py \"{city}\""}
                ),
            )
        if cmd == "/memory":
            q = " ".join(args) if args else "最近"
            await self.bus.publish_outbound(
                OutboundMessage(
                    channel=msg.channel,
                    chat_id=msg.chat_id,
                    content=f"正在检索记忆: {q}...",
                    metadata={"_progress": True, "task_start_time": task_start_time},
                )
            )
            return OutboundMessage(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content=f"<b>🧠 相关记忆：</b>\n\n{await self.tools.execute('search_memory', {'query': q, 'top_k': 3})}",
            )
        if cmd == "/cleanup":
            import shutil

            d = Path.home() / ".nanobot" / "media"
            try:
                count = len(list(d.glob("*"))) if d.exists() else 0
                if d.exists():
                    shutil.rmtree(d)
                d.mkdir(parents=True, exist_ok=True)
                v_status = ""
                if self.context.memory.vector_store:
                    await self.context.memory.vector_store.cleanup_old_memories(days=14)
                    v_status = "及过期向量记忆"
                return OutboundMessage(
                    channel=msg.channel,
                    chat_id=msg.chat_id,
                    content=f"🗑️ 已清理 {count} 个缓存文件{v_status}。",
                )
            except Exception as e:
                return OutboundMessage(
                    channel=msg.channel, chat_id=msg.chat_id, content=f"清理失败: {e}"
                )
        if cmd == "/new":
            async def _archive_logic(skey):
                lck = self._consolidation_locks.setdefault(skey, asyncio.Lock())
                self._consolidating.add(skey)
                try:
                    async with lck:
                        # Re-fetch session to get updated last_consolidated after waiting for lock
                        s = self.sessions.get_or_create(skey)
                        snaps = list(s.messages[s.last_consolidated:])
                        if not snaps:
                            return True
                        tmp = Session(key=skey)
                        tmp.messages = snaps
                        return await self._consolidate_memory(tmp, archive_all=True)
                except Exception:
                    logger.exception("BG Archival failed")
                    return False
                finally:
                    self._consolidating.discard(skey)

            # Synchronously wait for archival to finish for /new command
            t = asyncio.create_task(_archive_logic(session.key))
            self._consolidation_tasks.add(t)
            t.add_done_callback(self._consolidation_tasks.discard)
            
            ok = await t

            if not ok:
                return OutboundMessage(
                    channel=msg.channel,
                    chat_id=msg.chat_id,
                    content=_t("cli.error.archival_failed", "存档失败，会话未清除。"),
                )

            session.clear()
            self.sessions.save(session)
            self.sessions.invalidate(session.key)
            return OutboundMessage(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content=_t("cli.info.new_session_started", "新会话已开始。"),
            )
        if cmd == "/help":
            if args:
                skill_name = args[0].lower()
                skill_file = Path("nanobot/skills") / skill_name / "SKILL.md"
                if skill_file.exists():
                    try:
                        content = skill_file.read_text(encoding="utf-8")
                        # Basic cleanup: remove YAML frontmatter if present
                        if content.startswith("---"):
                            parts = content.split("---", 2)
                            if len(parts) > 2:
                                content = parts[2].strip()
                        return OutboundMessage(
                            channel=msg.channel,
                            chat_id=msg.chat_id,
                            content=f"<b>📖 {skill_name} 技能手册</b>\n━━━━━━━━━━━━━━\n{content[:4000]}",
                        )
                    except Exception as e:
                        return OutboundMessage(
                            channel=msg.channel,
                            chat_id=msg.chat_id,
                            content=f"读取技能文档失败: {e}",
                        )
                else:
                    return OutboundMessage(
                        channel=msg.channel,
                        chat_id=msg.chat_id,
                        content=f"❌ 未找到技能 <code>{skill_name}</code>。发送 <code>/tools</code> 查看可用工具集。",
                    )

            return OutboundMessage(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content="<b>🐈 nanobot 指南</b>\n━━━━━━━━━━━━━━\n🧹 <code>/prune</code> - 记忆审计与整理\n🛠️ <code>/mcp</code> - 检查外部工具状态\n🔧 <code>/tools</code> - 查看可用工具集\n⚙️ <code>/config</code> - 查看关键配置摘要\n✨ <code>/new</code> - 开启新会话\n🌤️ <code>/weather</code> - 实时天气\n🧠 <code>/memory</code> - 搜索历史/事实\n📊 <code>/status</code> - 运行状态\n🗑️ <code>/cleanup</code> - 清理媒体缓存\n━━━━━━━━━━━━━━\n💡 提示：发送 <code>/help 技能名</code> 查看详情（如：<code>/help weather</code>）",
            )

        path_matches = re.findall(r'[A-Za-z]:\\[^\\/:*?"<>|\r\n]+', msg.content)
        for p in path_matches[:2]:
            try:
                po = Path(p.strip())
                msg.content += f"\n\n[SYSTEM HINT: '{p}' {'存在' if po.exists() else '不存在'}]"
            except Exception:
                pass

        self._set_tool_context(msg.channel, msg.chat_id, msg.metadata.get("message_id"))
        if (mt := self.tools.get("message")) and isinstance(mt, MessageTool):
            mt.start_turn()

        history = session.get_history(max_messages=self.memory_window)

        async def _bp(c, *, tool_hint=False):
            await self.bus.publish_outbound(
                OutboundMessage(
                    channel=msg.channel,
                    chat_id=msg.chat_id,
                    content=c,
                    metadata={
                        "_progress": True,
                        "_tool_hint": tool_hint,
                        "task_start_time": task_start_time,
                    },
                )
            )

        final, _, all_msgs = await self._run_agent_loop(
            self.context.build_messages(
                history=history,
                current_message=msg.content,
                media=msg.media,
                channel=msg.channel,
                chat_id=msg.chat_id,
            ),
            on_progress=on_progress or _bp,
        )

        # Find where the new messages start (runtime context and user message)
        skip_idx = 0
        for i, m in enumerate(all_msgs):
            if (
                m.get("role") == "user"
                and isinstance(m.get("content"), str)
                and ContextBuilder._RUNTIME_CONTEXT_TAG in m.get("content")
            ):
                # Skip the metadata message itself to prevent history bloat
                skip_idx = i + 1
                break

        self._save_turn(session, all_msgs, skip_idx)

        # Trigger background memory consolidation if needed
        # We use a lock per session to prevent concurrent consolidation tasks
        if len(session.messages) - session.last_consolidated > self.memory_window:
            lck = self._consolidation_locks.setdefault(session.key, asyncio.Lock())

            async def _consolidate_task(s):
                if s.key in self._consolidating:
                    return
                self._consolidating.add(s.key)
                try:
                    async with lck:
                        # Re-check inside lock: maybe another task already consolidated it
                        if len(s.messages) - s.last_consolidated > self.memory_window:
                            await self._consolidate_memory(s)
                finally:
                    self._consolidating.discard(s.key)

            t = asyncio.create_task(_consolidate_task(session))
            self._consolidation_tasks.add(t)
            t.add_done_callback(self._consolidation_tasks.discard)

        self.sessions.save(session)

        if (mt := self.tools.get("message")) and isinstance(mt, MessageTool) and mt._sent_in_turn:
            return None
        return OutboundMessage(
            channel=msg.channel,
            chat_id=msg.chat_id,
            content=final or "Done.",
            metadata=msg.metadata or {},
        )

    def _save_turn(self, session: Session, messages: list[dict], skip: int) -> None:
        for m in messages[skip:]:
            entry = dict(m)
            role = entry.get("role")
            content = entry.get("content")

            if role == "assistant" and not content and not entry.get("tool_calls"):
                continue
            if role == "tool" and isinstance(content, str) and len(content) > self._TOOL_RESULT_MAX_CHARS:
                entry["content"] = content[: self._TOOL_RESULT_MAX_CHARS] + "\n..."
            elif role == "user" and isinstance(content, list):
                entry["content"] = [
                    (
                        {"type": "text", "text": "[image]"}
                        if (
                            c.get("type") == "image_url"
                            and c.get("image_url", {}).get("url", "").startswith("data:image/")
                        )
                        else c
                    )
                    for c in content
                ]
            entry.setdefault("timestamp", datetime.now().isoformat())
            session.messages.append(entry)
        session.updated_at = datetime.now()

    async def _consolidate_memory(self, session, archive_all: bool = False) -> bool:
        model = self.memory_archival_model or self.model
        return await self.context.memory.consolidate(
            session, self.provider, model, archive_all=archive_all, memory_window=self.memory_window
        )

    async def process_direct(
        self,
        content: str,
        session_key: str = "cli:direct",
        channel: str = "cli",
        chat_id: str = "direct",
        on_progress: Callable[[str], Awaitable[None]] | None = None,
    ) -> str:
        await self._connect_mcp()
        r = await self._process_message(
            InboundMessage(channel=channel, sender_id="user", chat_id=chat_id, content=content),
            session_key=session_key,
            on_progress=on_progress,
        )
        return r.content if r else ""
