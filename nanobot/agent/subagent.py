"""Subagent manager for background task execution."""

import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Any

from loguru import logger

from nanobot.agent.tools.filesystem import EditFileTool, ListDirTool, ReadFileTool, WriteFileTool
from nanobot.agent.tools.registry import ToolRegistry
from nanobot.agent.tools.shell import ExecTool
from nanobot.agent.tools.web import WebFetchTool, WebSearchTool
from nanobot.bus.events import InboundMessage, OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.config.schema import ExecToolConfig
from nanobot.providers.base import LLMProvider


class SubagentManager:
    """Manages background subagent execution with real-time reporting."""

    def __init__(
        self,
        provider: LLMProvider,
        workspace: Path,
        bus: MessageBus,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        reasoning_effort: str | None = None,
        brave_api_key: str | None = None,
        web_proxy: str | None = None,
        exec_config: "ExecToolConfig | None" = None,
        restrict_to_workspace: bool = False,
    ):
        from nanobot.config.schema import ExecToolConfig
        self.provider = provider
        self.workspace = workspace
        self.bus = bus
        self.model = model or provider.get_default_model()
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.reasoning_effort = reasoning_effort
        self.brave_api_key = brave_api_key
        self.web_proxy = web_proxy
        self.exec_config = exec_config or ExecToolConfig()
        self.restrict_to_workspace = restrict_to_workspace
        self._running_tasks: dict[str, asyncio.Task[None]] = {}
        self._session_tasks: dict[str, set[str]] = {}

    async def spawn(
        self,
        task: str,
        label: str | None = None,
        origin_channel: str = "cli",
        origin_chat_id: str = "direct",
        session_key: str | None = None,
    ) -> str:
        task_id = str(uuid.uuid4())[:8]
        display_label = label or task[:30] + ("..." if len(task) > 30 else "")
        origin = {"channel": origin_channel, "chat_id": origin_chat_id}

        bg_task = asyncio.create_task(
            self._run_subagent(task_id, task, display_label, origin)
        )
        self._running_tasks[task_id] = bg_task
        if session_key:
            self._session_tasks.setdefault(session_key, set()).add(task_id)

        def _cleanup(_: asyncio.Task) -> None:
            self._running_tasks.pop(task_id, None)
            if session_key and (ids := self._session_tasks.get(session_key)):
                ids.discard(task_id)
                if not ids: del self._session_tasks[session_key]

        bg_task.add_done_callback(_cleanup)
        return f"Subagent [{display_label}] 已启动 (ID: {task_id})。工作过程中我会实时为您更新进度。"

    async def _run_subagent(
        self,
        task_id: str,
        task: str,
        label: str,
        origin: dict[str, str],
    ) -> None:
        logger.info("Subagent [{}] starting task: {}", task_id, label)
        task_start_time = time.time()

        # LIVE: INITIAL ANNOUNCEMENT
        await self.bus.publish_outbound(OutboundMessage(
            channel=origin["channel"], chat_id=origin["chat_id"],
            content=f"🛠️ <b>{label}</b>: 正在初始化工作环境...",
            metadata={"_progress": True, "task_start_time": task_start_time, "subagent_id": task_id}
        ))

        try:
            tools = ToolRegistry()
            allowed_dir = self.workspace if self.restrict_to_workspace else None
            tools.register(ReadFileTool(workspace=self.workspace, allowed_dir=allowed_dir))
            tools.register(WriteFileTool(workspace=self.workspace, allowed_dir=allowed_dir))
            tools.register(EditFileTool(workspace=self.workspace, allowed_dir=allowed_dir))
            tools.register(ListDirTool(workspace=self.workspace, allowed_dir=allowed_dir))
            tools.register(ExecTool(working_dir=str(self.workspace), timeout=self.exec_config.timeout, restrict_to_workspace=self.restrict_to_workspace, path_append=self.exec_config.path_append))
            tools.register(WebSearchTool(api_key=self.brave_api_key, proxy=self.web_proxy))
            tools.register(WebFetchTool(proxy=self.web_proxy))

            system_prompt = self._build_subagent_prompt()
            messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}, {"role": "user", "content": task}]

            max_iterations = 15
            iteration = 0
            final_result: str | None = None

            while iteration < max_iterations:
                iteration += 1

                # LIVE: STEP UPDATE
                await self.bus.publish_outbound(OutboundMessage(
                    channel=origin["channel"], chat_id=origin["chat_id"],
                    content=f"🧠 <b>{label}</b>: 正在执行第 {iteration} 阶段任务...",
                    metadata={"_progress": True, "task_start_time": task_start_time, "subagent_id": task_id}
                ))

                full_content = ""
                tool_calls_map = {}
                
                async for chunk in self.provider.chat_stream(
                    messages=messages,
                    tools=tools.get_definitions(),
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    reasoning_effort=self.reasoning_effort,
                ):
                    if chunk.content:
                        full_content += chunk.content
                        # We don't stream raw subagent content to user yet to avoid noise,
                        # but we could update metadata or logs here.
                    
                    if chunk.tool_call_delta:
                        delta = chunk.tool_call_delta
                        idx = delta["index"]
                        if idx not in tool_calls_map:
                            tool_calls_map[idx] = {"id": delta.get("id"), "name": delta.get("name"), "arguments": ""}
                        if delta.get("name"): tool_calls_map[idx]["name"] = delta["name"]
                        if delta.get("id"): tool_calls_map[idx]["id"] = delta["id"]
                        if delta.get("arguments"): tool_calls_map[idx]["arguments"] += delta["arguments"]

                # Parse tool calls
                tool_calls = []
                for idx in sorted(tool_calls_map.keys()):
                    tc = tool_calls_map[idx]
                    import json_repair
                    try:
                        args = json_repair.loads(tc["arguments"]) if tc["arguments"] else {}
                    except Exception: args = {}
                    tool_calls.append(ToolCallRequest(id=tc["id"] or f"sub_{task_id}_{idx}", name=tc["name"] or "unknown", arguments=args))

                if tool_calls:
                    tool_call_dicts = [{"id": tc.id, "type": "function", "function": {"name": tc.name, "arguments": json.dumps(tc.arguments, ensure_ascii=False)}} for tc in tool_calls]
                    messages.append({"role": "assistant", "content": full_content, "tool_calls": tool_call_dicts})

                    # Parallel tool execution for subagent too!
                    async def _run_tool(tc):
                        await self.bus.publish_outbound(OutboundMessage(
                            channel=origin["channel"], chat_id=origin["chat_id"],
                            content=f"🔧 <b>{label}</b>: 正在使用工具 <code>{tc.name}</code>...",
                            metadata={"_progress": True, "task_start_time": task_start_time, "subagent_id": task_id}
                        ))
                        res = await tools.execute(tc.name, tc.arguments)
                        return tc.id, tc.name, res

                    tool_results = await asyncio.gather(*[_run_tool(tc) for tc in tool_calls])
                    for tid, tname, res in tool_results:
                        messages.append({"role": "tool", "tool_call_id": tid, "name": tname, "content": res})
                else:
                    final_result = full_content
                    break

            # LIVE: FINAL SUCCESS
            await self.bus.publish_outbound(OutboundMessage(
                channel=origin["channel"], chat_id=origin["chat_id"],
                content=f"✅ <b>{label}</b>: 任务执行完毕，结果已汇报给主控。",
                metadata={"_progress": False, "subagent_id": task_id}
            ))
            await self._announce_result(task_id, label, task, final_result or "Done.", origin, "ok")

        except Exception as e:
            logger.error("Subagent [{}] failed: {}", task_id, e)
            await self.bus.publish_outbound(OutboundMessage(
                channel=origin["channel"], chat_id=origin["chat_id"],
                content=f"❌ <b>{label}</b>: 执行出错: {str(e)}",
                metadata={"_progress": False, "subagent_id": task_id}
            ))
            await self._announce_result(task_id, label, task, str(e), origin, "error")

    async def _announce_result(self, task_id: str, label: str, task: str, result: str, origin: dict[str, str], status: str) -> None:
        """Announce result as an 'Employee' reporting to the 'CEO'."""
        status_text = "已圆满完成" if status == "ok" else "执行失败"

        # Format as a formal internal report
        report_content = (
            f"🔔 [内部汇报]\n"
            f"汇报人: {label} (ID: {task_id})\n"
            f"任务状态: {status_text}\n"
            f"任务内容: {task}\n"
            f"执行结果: \n{result}\n\n"
            f"请 CEO 查阅并进行下一步指示。"
        )

        # Inject as a USER message so the Agent knows it's an external report
        msg = InboundMessage(
            channel=origin['channel'],
            sender_id=f"Employee:{task_id}",
            chat_id=origin['chat_id'],
            content=report_content
        )
        await self.bus.publish_inbound(msg)
        logger.debug("Subagent [{}] submitted report to CEO", task_id)

    def _build_subagent_prompt(self) -> str:
        from nanobot.agent.context import ContextBuilder
        from nanobot.agent.skills import SkillsLoader
        time_ctx = ContextBuilder._build_runtime_context(None, None)
        parts = [f"# Subagent\n\n{time_ctx}\n\nYou are a specialized subagent. Complete the assigned task. Final response goes to main agent.\n\n## Workspace\n{self.workspace}"]
        skills_summary = SkillsLoader(self.workspace).build_skills_summary()
        if skills_summary: parts.append(f"## Skills\n\n{skills_summary}")
        return "\n\n".join(parts)

    async def cancel_by_session(self, session_key: str) -> int:
        tasks = [self._running_tasks[tid] for tid in self._session_tasks.get(session_key, []) if tid in self._running_tasks and not self._running_tasks[tid].done()]
        for t in tasks: t.cancel()
        if tasks: await asyncio.gather(*tasks, return_exceptions=True)
        return len(tasks)

    def get_running_count(self) -> int:
        return len(self._running_tasks)
