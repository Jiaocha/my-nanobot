<div align="center">
  <img src="nanobot_logo.png" alt="nanobot" width="500">
  <h1>nanobot: 超轻量级个人 AI 助手</h1>
  <p>
    <a href="https://pypi.org/project/nanobot-ai/"><img src="https://img.shields.io/pypi/v/nanobot-ai" alt="PyPI"></a>
    <a href="https://pepy.tech/project/nanobot-ai"><img src="https://static.pepy.tech/badge/nanobot-ai" alt="Downloads"></a>
    <img src="https://img.shields.io/badge/python-≥3.11-blue" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
    <a href="./COMMUNICATION.md"><img src="https://img.shields.io/badge/Feishu-Group-E9DBFC?style=flat&logo=feishu&logoColor=white" alt="Feishu"></a>
    <a href="./COMMUNICATION.md"><img src="https://img.shields.io/badge/WeChat-Group-C5EAB4?style=flat&logo=wechat&logoColor=white" alt="WeChat"></a>
    <a href="https://discord.gg/MnCvHqpUGB"><img src="https://img.shields.io/badge/Discord-Community-5865F2?style=flat&logo=discord&logoColor=white" alt="Discord"></a>
  </p>
</div>

🐈 **nanobot** 是一款受 [OpenClaw](https://github.com/openclaw/openclaw) 启发的**超轻量级**个人 AI 助手。

⚡️ 核心智能体功能仅需 **~4,000** 行代码即可实现 —— 比 Clawdbot 的 43+ 万行代码缩小了 **99%**。

📏 实时代码统计：**4,150 行**（可随时运行 `bash core_agent_lines.sh` 进行验证）

## 📢 新闻

- **2026-03-03** 🚀 **重大架构更新** —— 引入全流式响应 (Streaming)、统一 SQLite 存储、基于 Token 的滑动窗口以及工具并发执行。
- **2026-02-28** 🚀 发布 **v0.1.4.post3** —— 更简洁的上下文、更稳健的会话历史以及更聪明的智能体。
- **2026-02-27** 🧠 实验性思考模式支持、钉钉富媒体消息、飞书和 QQ 频道修复。
- **2026-02-26** 🛡️ 会话投毒修复、WhatsApp 去重、Windows 路径保护、Mistral 兼容性。

<details>
<summary>早期新闻</summary>

- **2026-02-25** 🧹 新增 Matrix 频道、更简洁的会话上下文、自动工作区模板同步。
- **2026-02-24** 🚀 发布 **v0.1.4.post2** —— 一个侧重于可靠性的版本。
- **2026-02-17** 🎉 发布 **v0.1.4** —— MCP 支持、进度流式传输、新增 Provider。
- **2026-02-02** 🎉 nanobot 正式发布！

</details>

## nanobot 核心特性：

🪶 **超轻量级**：核心智能体代码仅约 4,000 行 —— 比 Clawdbot 缩小了 99%。

⚡️ **极速交互**：端到端流式响应 (Streaming)，实现零延迟的思考与进度反馈。

🚀 **高并发执行**：工具调用支持并行调度 (asyncio.gather)，复合任务响应速度提升 2-3 倍。

💾 **统一数据库存储**：会话历史与长期记忆全线迁移至 SQLite (WAL 模式)，告别文件锁隐患。

🧠 **精准上下文管理**：基于 Token 预算 (tiktoken) 的滑动窗口裁剪，确保长对话的极致稳定性。

🔬 **研究友好**：代码整洁易读，方便研究人员理解、修改和扩展。

## 🏗️ 架构图

<p align="center">
  <img src="nanobot_arch.png" alt="nanobot architecture" width="800">
</p>

## ✨ 功能亮点

<table align="center">
  <tr align="center">
    <th><p align="center">📈 24/7 实时市场分析</p></th>
    <th><p align="center">🚀 全栈软件工程师</p></th>
    <th><p align="center">📅 智能日常事务管理</p></th>
    <th><p align="center">📚 个人知识助手</p></th>
  </tr>
  <tr>
    <td align="center"><p align="center"><img src="case/search.gif" width="180" height="400"></p></td>
    <td align="center"><p align="center"><img src="case/code.gif" width="180" height="400"></p></td>
    <td align="center"><p align="center"><img src="case/scedule.gif" width="180" height="400"></p></td>
    <td align="center"><p align="center"><img src="case/memory.gif" width="180" height="400"></p></td>
  </tr>
  <tr>
    <td align="center">搜索 • 洞察 • 趋势</td>
    <td align="center">开发 • 部署 • 扩展</td>
    <td align="center">计划 • 自动化 • 组织</td>
    <td align="center">学习 • 记忆 • 推理</td>
  </tr>
</table>

## 📦 安装

**从源码安装**（包含最新功能，推荐开发使用）

```bash
git clone https://github.com/HKUDS/nanobot.git
cd nanobot
pip install -e .
```

## 🚀 快速开始

> [!TIP]
> 核心存储已全面升级至 SQLite。现有的 `.jsonl` 和 `MEMORY.md` 资料将在启动时自动无损迁移。

**1. 初始化**

```bash
nanobot onboard
```

**2. 配置** (`~/.nanobot/config.json`)

```json
{
  "providers": {
    "openai": { "apiKey": "sk-xxx" }
  }
}
```

**3. 对话**

```bash
nanobot agent
```

## 💬 聊天应用

将 nanobot 连接到你喜欢的聊天平台。目前全渠道已适配 **流式输出** 体验。

| 渠道 | 你需要准备 |
|---------|---------------|
| **Telegram** | Bot token |
| **Discord** | Bot token |
| **飞书 (Feishu)** | App ID + App Secret |
| **Mochat** | Claw token |
| **Slack** | Bot token + App-Level token |

## 📁 项目结构

```
nanobot/
├── agent/          # 🧠 核心智能体逻辑
│   ├── loop.py     #    流式 Agent 循环 (LLM ↔ 并发工具)
│   ├── context.py  #    Token 敏感型 Prompt 构建器
│   ├── memory.py   #    SQLite 长期记忆持久化
│   ├── skills.py   #    技能加载器
│   ├── subagent.py #    流式后台任务执行
│   └── tools/      #    内置工具集
├── session/        # 💬 基于 SQLite 的会话管理
├── providers/      # 🤖 LLM 服务商 (支持 Streaming 接口)
├── config/         # ⚙️ Pydantic 配置架构
└── cli/            # 🖥️ 命令行入口
```

## ⭐ Star History

<div align="center">
  <a href="https://star-history.com/#HKUDS/nanobot&Date">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=HKUDS/nanobot&type=Date&theme=dark" />
      <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=HKUDS/nanobot&type=Date" />
      <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=HKUDS/nanobot&type=Date" style="border-radius: 15px; box-shadow: 0 0 30px rgba(0, 217, 255, 0.3);" />
    </picture>
  </a>
</div>

<p align="center">
  <sub>nanobot 仅用于教育、研究和技术交流目的</sub>
</p>
