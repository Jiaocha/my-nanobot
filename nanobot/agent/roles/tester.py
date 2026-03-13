"""Tester role: Responsible for generating and running unit tests for generated code."""

import asyncio
import json
import httpx
from pathlib import Path
from loguru import logger
from nanobot.bus.events import OutboundMessage


class TesterRole:
    def __init__(self, provider, model: str | None, workspace: Path, bus, max_iterations: int):
        self.provider = provider
        self.model = model
        self.workspace = workspace
        self.bus = bus
        self.max_iterations = max_iterations

    async def verify_code(
        self, tool_name: str, arguments: dict, msg, current_iteration: int, task_start_time: float
    ) -> tuple[bool, str]:
        """Optionally generate and run tests for newly written code."""
        if not self.model or tool_name not in ["write_file", "edit_file"]:
            return True, ""

        file_content = arguments.get("content", "")
        file_path = arguments.get("path", "unknown.py")

        if not file_path.endswith(".py") or len(file_content) < 50:
            return True, ""

        logger.bind(cli_display=True).info(
            f"[{msg.channel}] 自动测试 -> [bold green]🧑‍🔬 代码测试[/bold green] ({self.model})"
        )
        await self.bus.publish_outbound(
            OutboundMessage(
                channel=msg.channel,
                chat_id=msg.chat_id,
                content=f"正在为 {Path(file_path).name} 生成单元测试...",
                metadata={
                    "_progress": True,
                    "step": current_iteration,
                    "total": self.max_iterations,
                    "task_start_time": task_start_time,
                    "model": self.model,
                },
            )
        )

        # [原生直连调用] 生成测试代码
        try:
            # 加载精细化模板
            template_path = self.workspace / "nanobot/templates/tester.txt"
            tester_instruction = (
                template_path.read_text(encoding="utf-8")
                if template_path.exists()
                else "你是一个专业的测试工程师。"
            )

            from nanobot.config.loader import load_config

            cfg = load_config()
            p = cfg.providers.qwen  # 假设使用 Qwen

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{p.api_base.rstrip('/')}/chat/completions",
                    headers={"Authorization": f"Bearer {p.api_key}"},
                    json={
                        "model": self.model.split("::")[-1],
                        "messages": [
                            {"role": "system", "content": tester_instruction},
                            {
                                "role": "user",
                                "content": f"文件名: {file_path}\n代码内容:\n{file_content}",
                            },
                        ],
                        "temperature": 0.0,
                    },
                )
                if resp.status_code == 200:
                    test_code = resp.json()["choices"][0]["message"]["content"]
                    # 去掉 Markdown 标记
                    test_code = test_code.replace("```python", "").replace("```", "").strip()
                    logger.success("✅ 测试用例已生成")

                    # [自愈合闭环] 自动运行测试
                    test_file_path = self.workspace / "tests" / f"test_{Path(file_path).stem}.py"
                    test_file_path.parent.mkdir(parents=True, exist_ok=True)
                    test_file_path.write_text(test_code, encoding="utf-8")

                    # 运行 pytest
                    import subprocess

                    try:
                        result = subprocess.run(
                            ["pytest", str(test_file_path), "-v"],
                            capture_output=True,
                            text=True,
                            cwd=str(self.workspace),
                            timeout=15,
                        )
                        if result.returncode == 0:
                            test_status = "✅ 测试通过"
                            test_output = result.stdout
                        else:
                            test_status = "❌ 测试失败"
                            test_output = result.stdout + "\n" + result.stderr
                    except subprocess.TimeoutExpired:
                        test_status = "⚠️ 测试超时"
                        test_output = "测试执行超过 15 秒限制"
                    except Exception as ex:
                        test_status = "⚠️ 测试执行异常"
                        test_output = str(ex)

                    return (
                        True,
                        f"[单元测试验证结果] {test_status}\n\n[测试执行输出]\n{test_output}",
                    )
                else:
                    return True, ""  # 失败则放行，不干扰主流程
        except Exception as e:
            logger.warning("测试生成失败: {}", e)
            return True, ""
