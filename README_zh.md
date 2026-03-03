<div align="center">
  <img src="nanobot_logo.png" alt="nanobot" width="500">
  <h1>nanobot: 超轻量级个人 AI 助手</h1>
  <p>
    <a href="https://pypi.org/project/nanobot-ai/"><img src="https://img.shields.io/pypi/v/nanobot-ai" alt="PyPI 版本"></a>
    <a href="https://pepy.tech/project/nanobot-ai"><img src="https://static.pepy.tech/badge/nanobot-ai" alt="下载次数"></a>
    <img src="https://img.shields.io/badge/python-≥3.11-blue" alt="Python 版本">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="许可证">
    <a href="./COMMUNICATION.md"><img src="https://img.shields.io/badge/飞书群组-E9DBFC?style=flat&logo=feishu&logoColor=white" alt="飞书"></a>
    <a href="./COMMUNICATION.md"><img src="https://img.shields.io/badge/微信群组-C5EAB4?style=flat&logo=wechat&logoColor=white" alt="微信"></a>
    <a href="https://discord.gg/MnCvHqpUGB"><img src="https://img.shields.io/badge/Discord 社区 -5865F2?style=flat&logo=discord&logoColor=white" alt="Discord"></a>
  </p>
</div>

---

🐈 **nanobot** 是一款受 [OpenClaw](https://github.com/openclaw/openclaw) 启发的**超轻量级**个人 AI 助手。

⚡️ 核心智能体功能仅需 **~4,000 行**代码即可实现 —— 比 Clawdbot 的 43 万 + 行代码缩小了 **99%**。

📏 实时代码统计：**3,935 行**（可随时运行 `bash core_agent_lines.sh` 进行验证）

## 🎯 核心特性

| 特性 | 说明 |
|------|------|
| 🪶 **超轻量级** | 核心智能体代码仅约 4,000 行，比 Clawdbot 缩小 99% |
| 🔬 **研究友好** | 代码整洁易读，方便理解、修改和扩展 |
| ⚡️ **极速启动** | 更小的资源占用，更快的启动和迭代速度 |
| 💎 **简单易用** | 一键部署，开箱即用，2 分钟即可拥有 AI 助手 |
| 🔌 **多平台支持** | 支持 Telegram、Discord、飞书、钉钉、Slack 等 10+ 聊天平台 |
| 🧠 **强大智能** | 支持文件操作、网页搜索、定时任务、记忆系统等高级功能 |

## 🏗️ 架构图

<p align="center">
  <img src="nanobot_arch.png" alt="nanobot 架构图" width="800">
</p>

## ✨ 使用场景

<table align="center">
  <tr align="center">
    <th>📈 24/7 实时市场分析</th>
    <th>🚀 全栈软件工程师</th>
    <th>📅 智能日常事务管理</th>
    <th>📚 个人知识助手</th>
  </tr>
  <tr>
    <td align="center"><img src="case/search.gif" width="150"></td>
    <td align="center"><img src="case/code.gif" width="150"></td>
    <td align="center"><img src="case/scedule.gif" width="150"></td>
    <td align="center"><img src="case/memory.gif" width="150"></td>
  </tr>
  <tr>
    <td>搜索 • 洞察 • 趋势</td>
    <td>开发 • 部署 • 扩展</td>
    <td>计划 • 自动化 • 组织</td>
    <td>学习 • 记忆 • 推理</td>
  </tr>
</table>

## 📦 快速安装

### 方式一：从 PyPI 安装（推荐，稳定版）

```bash
pip install nanobot-ai
```

### 方式二：使用 uv 安装（更快）

```bash
uv tool install nanobot-ai
```

### 方式三：从源码安装（开发使用）

```bash
git clone https://github.com/HKUDS/nanobot.git
cd nanobot
pip install -e .
```

## 🚀 5 分钟快速开始

### 第一步：初始化配置

```bash
nanobot onboard
```

这会在 `~/.nanobot/` 目录下创建配置文件和工作空间。

### 第二步：配置 API Key

编辑配置文件 `~/.nanobot/config.json`，添加你的 API Key：

```json
{
  "providers": {
    "openrouter": {
      "apiKey": "sk-or-v1-你的 API 密钥"
    }
  },
  "agents": {
    "defaults": {
      "model": "anthropic/claude-opus-4-5",
      "provider": "openrouter"
    }
  }
}
```

> 💡 **提示**：
> - 海外用户推荐使用 [OpenRouter](https://openrouter.ai/keys)
> - 国内用户可使用 [SiliconFlow](https://siliconflow.cn)、[DeepSeek](https://platform.deepseek.com) 等
> - 更多 Provider 配置见下文

### 第三步：开始对话

```bash
nanobot agent -m "你好，请介绍一下自己"
```

或者进入交互模式：

```bash
nanobot agent
```

就这么简单！你现在拥有了一个工作的 AI 助手！🎉

## 💬 连接聊天平台

nanobot 支持多种聊天平台，让你的 AI 助手 24 小时在线服务。

| 平台 | 难度 | 特点 |
|------|------|------|
| **Telegram** | ⭐ | 推荐！配置简单，隐私保护好 |
| **飞书** | ⭐⭐ | 国内可用，WebSocket 长连接 |
| **钉钉** | ⭐⭐ | 企业用户友好 |
| **Discord** | ⭐⭐⭐ | 功能强大，配置稍复杂 |
| **Slack** | ⭐⭐⭐ | 企业协作首选 |
| **WhatsApp** | ⭐⭐⭐ | 全球最流行，需 Node.js |
| **QQ** | ⭐⭐ | 国内用户友好，仅支持私聊 |
| **Email** | ⭐⭐ | 邮件助手，IMAP/SMTP |

### 示例：配置 Telegram

**1. 创建机器人**
- 打开 Telegram，搜索 `@BotFather`
- 发送 `/newbot`，按提示设置名称
- 复制获得的 Token

**2. 获取你的 User ID**
- 在 Telegram 中搜索 `@userinfobot`
- 发送任意消息，获取你的 User ID

**3. 配置 nanobot**

在 `~/.nanobot/config.json` 中添加：

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "你的 BOT_TOKEN",
      "allowFrom": ["你的 USER_ID"]
    }
  }
}
```

**4. 启动网关**

```bash
nanobot gateway
```

现在你可以在 Telegram 中与你的 AI 助手对话了！

## 🔌 支持的 LLM Provider

nanobot 支持 20+ 个 LLM Provider，满足各种需求。

### 国际 Provider

| Provider | 用途 | API Key 获取 |
|----------|------|-------------|
| `openrouter` | 聚合平台（推荐） | [openrouter.ai](https://openrouter.ai) |
| `anthropic` | Claude 系列 | [console.anthropic.com](https://console.anthropic.com) |
| `openai` | GPT 系列 | [platform.openai.com](https://platform.openai.com) |
| `gemini` | Gemini 系列 | [aistudio.google.com](https://aistudio.google.com) |
| `groq` | 高速推理 + 语音转录 | [console.groq.com](https://console.groq.com) |

### 国内 Provider

| Provider | 用途 | API Key 获取 |
|----------|------|-------------|
| `siliconflow` | 硅基流动（聚合） | [siliconflow.cn](https://siliconflow.cn) |
| `deepseek` | DeepSeek | [platform.deepseek.com](https://platform.deepseek.com) |
| `dashscope` | 通义千问 | [dashscope.console.aliyun.com](https://dashscope.console.aliyun.com) |
| `moonshot` | Kimi | [platform.moonshot.cn](https://platform.moonshot.cn) |
| `zhipu` | 智谱清言 | [open.bigmodel.cn](https://open.bigmodel.cn) |
| `volcengine` | 火山引擎 | [volcengine.com](https://www.volcengine.com) |
| `minimax` | MiniMax | [platform.minimaxi.com](https://platform.minimaxi.com) |

### 本地部署

| Provider | 用途 |
|----------|------|
| `vllm` | 本地 vLLM 服务器 |
| `custom` | 任何 OpenAI 兼容接口 |

### 配置示例

```json
{
  "providers": {
    "deepseek": {
      "apiKey": "你的 DeepSeek API Key"
    },
    "siliconflow": {
      "apiKey": "你的 SiliconFlow API Key"
    }
  },
  "agents": {
    "defaults": {
      "model": "deepseek-chat",
      "provider": "deepseek"
    }
  }
}
```

## 🛠️ 核心功能

### 1. 文件操作

AI 助手可以读取、编辑、创建文件：

```
请帮我创建一个 Python 脚本，实现简单的计算器功能
```

### 2. 网页搜索

支持网页搜索和内容抓取：

```
搜索一下最新的 AI 发展趋势，并总结要点
```

### 3. 定时任务

支持 Cron 表达式和周期性任务：

```bash
# 添加定时任务
nanobot cron add --name "早安" --message "早上好！今天也要加油哦！" --cron "0 8 * * *"

# 查看任务列表
nanobot cron list
```

### 4. 记忆系统

nanobot 拥有长期记忆能力：

- **MEMORY.md**: 存储长期事实和知识
- **HISTORY.md**: 可搜索的对话历史日志

```
记住我喜欢喝咖啡，每天早上 8 点提醒我
```

### 5. MCP (Model Context Protocol)

支持连接外部 MCP 服务器，扩展 AI 能力：

```json
{
  "tools": {
    "mcpServers": {
      "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"]
      }
    }
  }
}
```

### 6. 子智能体

支持创建和管理多个子智能体，并行处理复杂任务：

```
创建一个数据分析子智能体，帮我分析这个 CSV 文件
```

## 📁 工作空间结构

```
~/.nanobot/
├── config.json          # 主配置文件
├── workspace/           # 工作空间
│   ├── AGENTS.md        # 智能体配置
│   ├── SOUL.md          # 智能体人格设定
│   ├── USER.md          # 用户偏好设置
│   ├── TOOLS.md         # 工具说明
│   ├── HEARTBEAT.md     # 心跳任务文件
│   └── skills/          # 自定义技能
├── memory/
│   ├── MEMORY.md        # 长期记忆
│   └── HISTORY.md       # 历史日志
└── logs/                # 日志文件
```

## 🐳 Docker 部署

### Docker Compose（推荐）

```bash
# 首次初始化
docker compose run --rm nanobot-cli onboard

# 编辑配置
vim ~/.nanobot/config.json

# 启动网关
docker compose up -d nanobot-gateway

# 使用 CLI
docker compose run --rm nanobot-cli agent -m "你好"

# 查看日志
docker compose logs -f nanobot-gateway
```

### 直接 Docker 运行

```bash
docker run -it -v ~/.nanobot:/root/.nanobot ghcr.io/hkuds/nanobot agent
```

## 🔒 安全建议

### 配置文件权限

```bash
chmod 700 ~/.nanobot
chmod 600 ~/.nanobot/config.json
```

### 访问控制

在配置中设置 `allowFrom` 白名单：

```json
{
  "channels": {
    "telegram": {
      "allowFrom": ["你的 USER_ID"]
    }
  }
}
```

### 工作空间限制

启用工作空间限制，防止 AI 访问敏感文件：

```json
{
  "tools": {
    "restrictToWorkspace": true
  }
}
```

### 生产环境部署

1. **使用专用用户运行**
   ```bash
   sudo useradd -m nanobot
   sudo -u nanobot nanobot gateway
   ```

2. **使用防火墙限制出站连接**

3. **定期更新依赖**
   ```bash
   pip install --upgrade nanobot-ai
   ```

## 📊 CLI 命令参考

| 命令 | 说明 |
|------|------|
| `nanobot onboard` | 初始化配置和工作空间 |
| `nanobot agent -m "消息"` | 与智能体对话 |
| `nanobot agent` | 交互模式 |
| `nanobot gateway` | 启动聊天网关 |
| `nanobot status` | 查看状态 |
| `nanobot cron add/list/remove` | 定时任务管理 |
| `nanobot provider login <provider>` | OAuth 登录 Provider |
| `nanobot channels login` | WhatsApp 扫码登录 |

### 交互模式退出命令

输入以下任一命令退出交互模式：
- `exit` / `quit`
- `/exit` / `/quit`
- `:q`
- `Ctrl+D`

## 🤝 加入社区

- 💬 [飞书交流群](./COMMUNICATION.md)
- 💬 [微信群](./COMMUNICATION.md)
- 🌐 [Discord 社区](https://discord.gg/MnCvHqpUGB)
- 📋 [GitHub 讨论区](https://github.com/HKUDS/nanobot/discussions)

## 📰 更新日志

### v0.1.4.post3 (2026-02-28)

- ✨ 更简洁的上下文管理
- 🛡️ 更稳健的会话历史
- 🧠 更聪明的智能体

[查看完整发布说明](https://github.com/HKUDS/nanobot/releases/tag/v0.1.4.post3)

### v0.1.4.post2 (2026-02-24)

- 🔧 重新设计的任务心跳系统
- ⚡️ Prompt 缓存优化
- 🛡️ Provider 和渠道稳定性增强

[查看完整发布说明](https://github.com/HKUDS/nanobot/releases/tag/v0.1.4.post2)

<details>
<summary>查看更多历史版本</summary>

- **v0.1.4.post1**: 新增 Provider、全渠道媒体支持
- **v0.1.4**: MCP 支持、进度流式传输
- **v0.1.3.post7**: 安全加固和多项改进

[查看所有版本](https://github.com/HKUDS/nanobot/releases)

</details>

## 🙏 致谢

- 灵感来源于 [OpenClaw](https://github.com/openclaw/openclaw)
- 感谢所有贡献者和社区成员

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

<div align="center">

**🐈 享受你的超轻量级 AI 助手！**

[文档](https://github.com/HKUDS/nanobot/wiki) · [问题反馈](https://github.com/HKUDS/nanobot/issues) · [功能建议](https://github.com/HKUDS/nanobot/discussions)

</div>
