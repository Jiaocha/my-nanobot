import base64
import json
import time
from pathlib import Path
from typing import Any, List, Dict
from loguru import logger


class ContextBuilder:
    def __init__(self, workspace: Path, config=None):
        self.workspace = workspace
        self.config = config
        from nanobot.agent.memory import MemoryStore
        from nanobot.agent.skills import SkillsLoader

        self.memory = MemoryStore(workspace)
        self.skills = SkillsLoader(workspace)

    async def get_context_messages(
        self, session, model: str | None = None, channel: str = "telegram", chat_id: str = ""
    ) -> List[Dict[str, Any]]:
        is_vision_model = "vision" in (model or "").lower()

        cleaned_history = []
        for m in session.messages:
            content = m.get("content")
            if isinstance(content, list):
                if is_vision_model:
                    cleaned_history.append(m)
                else:
                    text = next((c.get("text") for c in content if m.get("type") == "text"), "")
                    cleaned_history.append({**m, "content": text})
            else:
                cleaned_history.append(m)

        base_system_prompt = await self.build_system_prompt()

        # [核心更新] 3.1 版 CEO 统筹协议
        agent_identity = (
            "你现在是 Nanobot 多智能体集群的 CEO。你不是一个人在战斗，你指挥着一支顶尖专家团队：\n"
            "- 🏗️ 架构师 (Arch): 负责复杂任务的 [并行执行蓝图] 规划。\n"
            "- 🛡️ 审计员 (Audit): 实时守卫系统安全，拦截高危路径，修正代码错误。\n"
            "- 💻 技术专家 (CTO): 驱动 Qwen 3 Plus 编写极高水准的代码。\n"
            "- 🧪 测试员 (Test): 自动执行代码验证，确保逻辑闭环。\n"
            "- 🔍 研究员 (Res): 擅长使用 Scrapling 潜行引擎渗透防爬网页。\n\n"
            "### 核心执行准则：\n"
            "1. 物理控制：你拥有全磁盘（C/D/E盘）管理权限，但在操作系统核心目录时请务必谨慎。\n"
            "2. 性能优先：尽可能利用并发工具调用。对于简单对话，直接秒回。\n"
            "3. 菜单联动：告知用户可以通过 Telegram 的 3x5 菜单一键 [中止任务] 或 [查状态]。\n"
            "4. 身份一致性：保持专业、果断且透明。如果专家同事被审计拦截，请向用户如实说明原因并提出改进方案。\n"
        )
        system_prompt = f"{base_system_prompt}\n\n{agent_identity}"

        messages = [{"role": "system", "content": system_prompt}]

        # [核心优化] 引入 Prompt Caching 标记
        if len(system_prompt) > 1024:
            messages[0]["cache_control"] = {"type": "ephemeral"}

        if not cleaned_history:
            messages.append(
                {"role": "user", "content": self._build_runtime_context(channel, chat_id)}
            )
        else:
            # 对于较长的历史，缓存倒数第二条消息以最大化复用
            if len(cleaned_history) >= 4:
                cleaned_history[-2]["cache_control"] = {"type": "ephemeral"}
            messages.extend(cleaned_history)
        return messages

    async def build_system_prompt(self, skill_names: list[str] | None = None) -> str:
        parts = [self._get_identity()]
        bootstrap = self._load_bootstrap_files()
        if bootstrap:
            parts.append(bootstrap)
        memory = await self.memory.get_memory_context()
        if memory:
            parts.append(f"# Memory\n\n{memory}")
        always_skills = self.skills.get_always_skills()
        if always_skills:
            parts.append(
                f"# Always Available Skills\n\n{self.skills.load_skills_for_context(always_skills)}"
            )
        if skill_names:
            parts.append(
                f"# Task Specific Skills\n\n{self.skills.load_skills_for_context(skill_names)}"
            )
        return "\n\n---\n\n".join(parts)

    def _get_identity(self) -> str:
        return "You are Nanobot, an industrial-grade AI orchestration system with full tool-calling capabilities."

    def _load_bootstrap_files(self) -> str:
        path = self.workspace / "docs/cognition/AGENTS.md"
        return f"# Agent Protocols\n\n{path.read_text(encoding='utf-8')}" if path.exists() else ""

    def _build_runtime_context(self, channel: str, chat_id: str) -> str:
        return f"[Runtime Context] Channel: {channel} | Chat ID: {chat_id} | Time: {time.strftime('%Y-%m-%d %H:%M:%S')}"

    def add_assistant_message(self, messages, content, tool_calls=None, reasoning_content=None):
        msg = {"role": "assistant", "content": content}
        if tool_calls:
            msg["tool_calls"] = tool_calls
        if reasoning_content:
            msg["reasoning_content"] = reasoning_content
        messages.append(msg)
        return messages

    def add_tool_result(self, messages, tool_call_id, tool_name, content):
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "name": tool_name,
                "content": str(content),
            }
        )
        return messages

    def _strip_images_from_history(self, messages):
        return [
            {
                **m,
                "content": next(
                    (c.get("text") for c in m["content"] if c.get("type") == "text"), ""
                ),
            }
            if isinstance(m.get("content"), list)
            else m
            for m in messages
        ]

    def _build_user_content(self, text, media=None):
        if not media:
            return text
        content = [{"type": "text", "text": text}]
        for path in media:
            p = Path(path)
            if p.is_file():
                try:
                    import mimetypes

                    b64 = base64.b64encode(p.read_bytes()).decode()
                    content.append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mimetypes.guess_type(path)[0] or 'image/jpeg'};base64,{b64}"
                            },
                        }
                    )
                except Exception:
                    pass
        return content
