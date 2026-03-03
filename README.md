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

📏 实时代码统计：**3,935 行**（可随时运行 `bash core_agent_lines.sh` 进行验证）

## 📢 新闻

- **2026-02-28** 🚀 发布 **v0.1.4.post3** —— 更简洁的上下文、更稳健的会话历史以及更聪明的智能体。详情请参阅 [发布说明](https://github.com/HKUDS/nanobot/releases/tag/v0.1.4.post3)。
- **2026-02-27** 🧠 实验性思考模式支持、钉钉富媒体消息、飞书和 QQ 频道修复。
- **2026-02-26** 🛡️ 会话投毒修复、WhatsApp 去重、Windows 路径保护、Mistral 兼容性。
- **2026-02-25** 🧹 新增 Matrix 频道、更简洁的会话上下文、自动工作区模板同步。
- **2026-02-24** 🚀 发布 **v0.1.4.post2** —— 一个侧重于可靠性的版本，具有重新设计的任务心跳、Prompt 缓存优化，并加强了 Provider 和渠道的稳定性。详情请参阅 [发布说明](https://github.com/HKUDS/nanobot/releases/tag/v0.1.4.post2)。
- **2026-02-23** 🔧 虚拟工具调用心跳、Prompt 缓存优化、Slack mrkdwn 修复。
- **2026-02-22** 🛡️ Slack 线程隔离、Discord 正在输入状态修复、智能体可靠性改进。
- **2026-02-21** 🎉 发布 **v0.1.4.post1** —— 新增 Provider、全渠道媒体支持以及重大稳定性改进。详情请参阅 [发布说明](https://github.com/HKUDS/nanobot/releases/tag/v0.1.4.post1)。
- **2026-02-20** 🐦 飞书现在可以接收来自用户的多模态文件。底层记忆系统更可靠。
- **2026-02-19** ✨ Slack 现在支持发送文件，Discord 自动分割长消息，Subagents 在 CLI 模式下也能工作。

<details>
<summary>早期新闻</summary>

- **2026-02-18** ⚡️ nanobot 现在支持火山引擎、MCP 自定义认证请求头和 Anthropic Prompt 缓存。
- **2026-02-17** 🎉 发布 **v0.1.4** —— MCP 支持、进度流式传输、新增 Provider 和多项频道改进。详情请参阅 [发布说明](https://github.com/HKUDS/nanobot/releases/tag/v0.1.4)。
- **2026-02-16** 🦞 nanobot 现在集成了 [ClawHub](https://clawhub.ai) 技能 —— 可搜索并安装公开的智能体技能。
- **2026-02-15** 🔑 nanobot 现在支持带 OAuth 登录的 OpenAI Codex Provider。
- **2026-02-14** 🔌 nanobot 现在支持 MCP！详情请参阅 [MCP 章节](#mcp-model-context-protocol)。
- **2026-02-13** 🎉 发布 **v0.1.3.post7** —— 包含安全加固和多项改进。**请升级到最新版本以解决安全隐患**。详情请参阅 [发布说明](https://github.com/HKUDS/nanobot/releases/tag/v0.1.3.post7)。
- **2026-02-12** 🧠 重新设计的记忆系统 —— 代码更少，更可靠。欢迎加入相关的 [讨论](https://github.com/HKUDS/nanobot/discussions/566)！
- **2026-02-11** ✨ 增强了 CLI 体验并增加了对 MiniMax 的支持！
- **2026-02-10** 🎉 发布了具有多项改进的 **v0.1.3.post6**！查看更新 [说明](https://github.com/HKUDS/nanobot/releases/tag/v0.1.3.post6) 和我们的 [路线图](https://github.com/HKUDS/nanobot/discussions/431)。
- **2026-02-09** 💬 增加了对 Slack、Email 和 QQ 的支持 —— nanobot 现在支持多个聊天平台！
- **2026-02-08** 🔧 重构了 Provider —— 现在新增一个 LLM Provider 仅需 2 个简单步骤！查看 [此处](#providers)。
- **2026-02-07** 🚀 发布了带有 Qwen 支持和几项关键改进的 **v0.1.3.post5**！详情请查看 [此处](https://github.com/HKUDS/nanobot/releases/tag/v0.1.3.post5)。
- **2026-02-06** ✨ 增加了 Moonshot/Kimi Provider、Discord 集成并加强了安全性！
- **2026-02-05** ✨ 增加了飞书渠道、DeepSeek Provider 和增强的定时任务支持！
- **2026-02-04** 🚀 发布了带有多 Provider 和 Docker 支持的 **v0.1.3.post4**！详情请查看 [此处](https://github.com/HKUDS/nanobot/releases/tag/v0.1.3.post4)。
- **2026-02-03** ⚡ 集成了 vLLM 以支持本地 LLM，并改进了自然语言任务调度！
- **2026-02-02** 🎉 nanobot 正式发布！欢迎试用 🐈 nanobot！

</details>

## nanobot 核心特性：

🪶 **超轻量级**：核心智能体代码仅约 4,000 行 —— 比 Clawdbot 缩小了 99%。

🔬 **研究友好**：代码整洁易读，方便研究人员理解、修改和扩展。

⚡️ **极速启动**：更小的 footprint 意味着更快的启动速度、更低的资源占用和更快的迭代。

💎 **简单易用**：一键部署，开箱即用。

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

**使用 [uv](https://github.com/astral-sh/uv) 安装**（稳定且快）

```bash
uv tool install nanobot-ai
```

**从 PyPI 安装**（稳定版）

```bash
pip install nanobot-ai
```

## 🚀 快速开始

> [!TIP]
> 在 `~/.nanobot/config.json` 中设置你的 API Key。
> 获取 API Key: [OpenRouter](https://openrouter.ai/keys) (全球) · [Brave Search](https://brave.com/search/api/) (可选，用于网页搜索)

**1. 初始化**

```bash
nanobot onboard
```

**2. 配置** (`~/.nanobot/config.json`)

将以下**两个部分**添加或合并到你的配置中（其他选项有默认值）。

*设置你的 API Key*（例如 OpenRouter，推荐海外用户使用）：
```json
{
  "providers": {
    "openrouter": {
      "apiKey": "sk-or-v1-xxx"
    }
  }
}
```

*设置你的模型*（可选，指定 Provider —— 默认为自动检测）：
```json
{
  "agents": {
    "defaults": {
      "model": "anthropic/claude-opus-4-5",
      "provider": "openrouter"
    }
  }
}
```

**3. 对话**

```bash
nanobot agent
```

就这么简单！你只需 2 分钟即可拥有一个工作的 AI 助手。

## 💬 聊天应用

将 nanobot 连接到你喜欢的聊天平台。

| 渠道 | 你需要准备 |
|---------|---------------|
| **Telegram** | 来自 @BotFather 的 Bot token |
| **Discord** | Bot token + Message Content 权限 |
| **WhatsApp** | 二维码扫码 |
| **飞书 (Feishu)** | App ID + App Secret |
| **Mochat** | Claw token (支持自动设置) |
| **钉钉 (DingTalk)** | App Key + App Secret |
| **Slack** | Bot token + App-Level token |
| **Email** | IMAP/SMTP 凭据 |
| **QQ** | App ID + App Secret |

<details>
<summary><b>Telegram</b> (推荐)</summary>

**1. 创建机器人**
- 打开 Telegram，搜索 `@BotFather`
- 发送 `/newbot`，按提示操作
- 复制 Token

**2. 配置**

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "YOUR_BOT_TOKEN",
      "allowFrom": ["YOUR_USER_ID"]
    }
  }
}
```

> 你可以在 Telegram 设置中找到你的 **User ID**。它通常显示为 `@yourUserId`。
> 复制这个值（**不带 `@` 符号**）并粘贴到配置文件中。


**3. 运行**

```bash
nanobot gateway
```

</details>

<details>
<summary><b>Mochat (Claw IM)</b></summary>

默认使用 **Socket.IO WebSocket**，并带有 HTTP 轮询回退机制。

**1. 让 nanobot 为你设置 Mochat**

只需向 nanobot 发送这条消息（将 `xxx@xxx` 替换为你的真实邮箱）：

```
阅读 https://raw.githubusercontent.com/HKUDS/MoChat/refs/heads/main/skills/nanobot/skill.md 并在 MoChat 上注册。我的邮箱账号是 xxx@xxx。请将我绑定为你的所有者，并在 MoChat 上私信我。
```

nanobot 会自动注册、配置 `~/.nanobot/config.json` 并连接到 Mochat。

**2. 重启网关**

```bash
nanobot gateway
```

就这么简单 —— 其余的由 nanobot 处理！

<br>

<details>
<summary>手动配置（高级）</summary>

如果你更喜欢手动配置，请将以下内容添加到 `~/.nanobot/config.json`：

> 请妥善保管 `claw_token`。它只能通过 `X-Claw-Token` 请求头发送到你的 Mochat API 端点。

```json
{
  "channels": {
    "mochat": {
      "enabled": true,
      "base_url": "https://mochat.io",
      "socket_url": "https://mochat.io",
      "socket_path": "/socket.io",
      "claw_token": "claw_xxx",
      "agent_user_id": "6982abcdef",
      "sessions": ["*"],
      "panels": ["*"],
      "reply_delay_mode": "non-mention",
      "reply_delay_ms": 120000
    }
  }
}
```

</details>

</details>

<details>
<summary><b>Discord</b></summary>

**1. 创建机器人**
- 访问 https://discord.com/developers/applications
- 创建应用 → Bot → Add Bot
- 复制 Bot Token

**2. 启用 Intents**
- 在 Bot 设置中，启用 **MESSAGE CONTENT INTENT**
- （可选）如果你打算使用基于成员数据的允许列表，请启用 **SERVER MEMBERS INTENT**

**3. 获取你的 User ID**
- Discord 设置 → 高级 → 启用 **开发者模式 (Developer Mode)**
- 右键点击你的头像 → **复制用户 ID (Copy User ID)**

**4. 配置**

```json
{
  "channels": {
    "discord": {
      "enabled": true,
      "token": "YOUR_BOT_TOKEN",
      "allowFrom": ["YOUR_USER_ID"]
    }
  }
}
```

**5. 邀请机器人**
- OAuth2 → URL Generator
- Scopes: 选择 `bot`
- Bot Permissions: 选择 `Send Messages`, `Read Message History`
- 打开生成的邀请链接，将机器人添加到你的服务器

**6. 运行**

```bash
nanobot gateway
```

</details>

<details>
<summary><b>Matrix (Element)</b></summary>

首先安装 Matrix 依赖：

```bash
pip install nanobot-ai[matrix]
```

**1. 创建/选择 Matrix 账号**

- 在你的主服务器（例如 `matrix.org`）上创建或重用一个 Matrix 账号。
- 确认你可以使用 Element 登录。

**2. 获取凭据**

- 你需要：
  - `userId` (例如：`@nanobot:matrix.org`)
  - `accessToken`
  - `deviceId` (推荐设置，以便同步 Token 可以在重启后恢复)
- 你可以从主服务器登录 API (`/_matrix/client/v3/login`) 或从客户端的高级会话设置中获取这些信息。

**3. 配置**

```json
{
  "channels": {
    "matrix": {
      "enabled": true,
      "homeserver": "https://matrix.org",
      "userId": "@nanobot:matrix.org",
      "accessToken": "syt_xxx",
      "deviceId": "NANOBOT01",
      "e2eeEnabled": true,
      "allowFrom": ["@your_user:matrix.org"],
      "groupPolicy": "open",
      "groupAllowFrom": [],
      "allowRoomMentions": false,
      "maxMediaBytes": 20971520
    }
  }
}
```

> 请保持 `matrix-store` 持久化并使用稳定的 `deviceId` —— 如果这些在重启时发生变化，加密会话状态将会丢失。

| 选项 | 描述 |
|--------|-------------|
| `allowFrom` | 允许互动的用户 ID。为空表示允许所有发送者。 |
| `groupPolicy` | `open` (默认), `mention`, 或 `allowlist`。 |
| `groupAllowFrom` | 房间允许列表（当 policy 为 `allowlist` 时使用）。 |
| `allowRoomMentions` | 在 mention 模式下接受 `@room` 提及。 |
| `e2eeEnabled` | 端到端加密支持（默认 `true`）。设置为 `false` 仅支持纯文本。 |
| `maxMediaBytes` | 最大附件大小（默认 `20MB`）。设置为 `0` 以禁用所有媒体。 |


**4. 运行**

```bash
nanobot gateway
```

</details>

<details>
<summary><b>WhatsApp</b></summary>

需要 **Node.js ≥18**。

**1. 链接设备**

```bash
nanobot channels login
# 使用 WhatsApp 扫描二维码 → 设置 → 已链接设备
```

**2. 配置**

```json
{
  "channels": {
    "whatsapp": {
      "enabled": true,
      "allowFrom": ["+1234567890"]
    }
  }
}
```

**3. 运行**（需要两个终端）

```bash
# 终端 1
nanobot channels login

# 终端 2
nanobot gateway
```

</details>

<details>
<summary><b>Feishu (飞书)</b></summary>

使用 **WebSocket** 长连接 —— 无需公网 IP。

**1. 创建飞书机器人**
- 访问 [飞书开放平台](https://open.feishu.cn/app)
- 创建新应用 → 启用 **机器人** 能力
- **权限管理**：添加 `im:message` (发送消息) 和 `im:message.p2p_msg:readonly` (接收单聊消息)
- **事件订阅**：添加 `im.message.receive_v1` (接收消息)
  - 选择 **长连接** 模式（需要先运行 nanobot 以建立连接）
- 从“凭证与基础信息”获取 **App ID** 和 **App Secret**
- 发布应用

**2. 配置**

```json
{
  "channels": {
    "feishu": {
      "enabled": true,
      "appId": "cli_xxx",
      "appSecret": "xxx",
      "encryptKey": "",
      "verificationToken": "",
      "allowFrom": ["ou_YOUR_OPEN_ID"]
    }
  }
}
```

> 长连接模式下，`encryptKey` 和 `verificationToken` 是可选的。
> `allowFrom`: 添加你的 open_id（你给机器人发消息时可以在 nanobot 日志中找到它）。使用 `["*"]` 允许所有用户。

**3. 运行**

```bash
nanobot gateway
```

> [!TIP]
> 飞书使用 WebSocket 接收消息 —— 无需 Webhook 或公网 IP！

</details>

<details>
<summary><b>QQ (QQ单聊)</b></summary>

使用带 WebSocket 的 **botpy SDK** —— 无需公网 IP。目前仅支持**私聊消息**。

**1. 注册并创建机器人**
- 访问 [QQ 开放平台](https://q.qq.com) → 注册为开发者（个人或企业）
- 创建新的机器人应用
- 进入 **开发设置** → 复制 **AppID** 和 **AppSecret**

**2. 设置沙箱进行测试**
- 在机器人管理后台中，找到 **沙箱配置**
- 在 **在消息列表配置** 下，点击 **添加成员** 并添加你自己的 QQ 号
- 添加后，使用手机 QQ 扫描机器人的二维码 → 打开机器人简介 → 点击“发消息”开始聊天

**3. 配置**

> - `allowFrom`: 添加你的 openid（你给机器人发消息时可以在 nanobot 日志中找到它）。使用 `["*"]` 允许所有人访问。
> - 正式环境：在机器人后台提交审核并发布。详情请参阅 [QQ 机器人文档](https://bot.q.qq.com/wiki/)。

```json
{
  "channels": {
    "qq": {
      "enabled": true,
      "appId": "YOUR_APP_ID",
      "secret": "YOUR_APP_SECRET",
      "allowFrom": ["YOUR_OPENID"]
    }
  }
}
```

**4. 运行**

```bash
nanobot gateway
```

现在从 QQ 给机器人发送消息 —— 它应该会回复！

</details>

<details>
<summary><b>DingTalk (钉钉)</b></summary>

使用 **Stream 模式** —— 无需公网 IP。

**1. 创建钉钉机器人**
- 访问 [钉钉开放平台](https://open-dev.dingtalk.com/)
- 创建新应用 -> 添加 **机器人** 能力
- **参数配置**：
  - 开启 **消息接收模式 - Stream 模式**
- **权限管理**：添加必要的发送消息权限
- 从“凭据”获取 **AppKey** (Client ID) 和 **AppSecret** (Client Secret)
- 发布应用

**2. 配置**

```json
{
  "channels": {
    "dingtalk": {
      "enabled": true,
      "clientId": "YOUR_APP_KEY",
      "clientSecret": "YOUR_APP_SECRET",
      "allowFrom": ["YOUR_STAFF_ID"]
    }
  }
}
```

> `allowFrom`: 添加你的 staff ID。使用 `["*"]` 允许所有用户。

**3. 运行**

```bash
nanobot gateway
```

</details>

<details>
<summary><b>Slack</b></summary>

使用 **Socket Mode** —— 无需公网 URL。

**1. 创建 Slack App**
- 前往 [Slack API](https://api.slack.com/apps) → **Create New App** → 选择 "From scratch"
- 填写名称并选择你的工作区

**2. 配置 App**
- **Socket Mode**: 开启 → 使用 `connections:write` 权限生成 **App-Level Token** → 复制它 (`xapp-...`)
- **OAuth & Permissions**: 添加 Bot Scopes: `chat:write`, `reactions:write`, `app_mentions:read`
- **Event Subscriptions**: 开启 → 订阅机器人事件: `message.im`, `message.channels`, `app_mention` → 保存更改
- **App Home**: 滚动到 **Show Tabs** → 启用 **Messages Tab** → 勾选 **"Allow users to send Slash commands and messages from the messages tab"**
- **Install App**: 点击 **Install to Workspace** → 授权 → 复制 **Bot Token** (`xoxb-...`)

**3. 配置 nanobot**

```json
{
  "channels": {
    "slack": {
      "enabled": true,
      "botToken": "xoxb-...",
      "appToken": "xapp-...",
      "allowFrom": ["YOUR_SLACK_USER_ID"],
      "groupPolicy": "mention"
    }
  }
}
```

**4. 运行**

```bash
nanobot gateway
```

直接私信机器人或在频道中 @提及它 —— 它应该会回复！

> [!TIP]
> - `groupPolicy`: `"mention"` (默认 —— 仅在被 @提及 时回复), `"open"` (回复所有频道消息), 或 `"allowlist"` (仅限特定频道)。
> - 私信 Policy 默认为开启。设置 `"dm": {"enabled": false}` 以禁用私信。

</details>

<details>
<summary><b>Email</b></summary>

为 nanobot 设置专属邮箱账号。它会通过 **IMAP** 轮询新邮件并通过 **SMTP** 回复 —— 就像一个私人邮件助手。

**1. 获取凭据（以 Gmail 为例）**
- 为你的机器人创建一个专属 Gmail 账号（例如 `my-nanobot@gmail.com`）
- 启用两步验证 → 创建 [应用专用密码 (App Password)](https://myaccount.google.com/apppasswords)
- 将此应用密码用于 IMAP 和 SMTP

**2. 配置**

> - `consentGranted` 必须为 `true` 才能允许访问邮箱。这是一个安全门槛 —— 设置为 `false` 以完全禁用。
> - `allowFrom`: 添加你的邮箱地址。使用 `["*"]` 以接受任何人的邮件。
> - `smtpUseTls` 和 `smtpUseSsl` 分别默认为 `true` / `false`，这对于 Gmail（587 端口 + STARTTLS）是正确的。无需显式设置它们。
> - 如果你只想读取/分析邮件而不想发送自动回复，请设置 `"autoReplyEnabled": false`。

```json
{
  "channels": {
    "email": {
      "enabled": true,
      "consentGranted": true,
      "imapHost": "imap.gmail.com",
      "imapPort": 993,
      "imapUsername": "my-nanobot@gmail.com",
      "imapPassword": "your-app-password",
      "smtpHost": "smtp.gmail.com",
      "smtpPort": 587,
      "smtpUsername": "my-nanobot@gmail.com",
      "smtpPassword": "your-app-password",
      "fromAddress": "my-nanobot@gmail.com",
      "allowFrom": ["your-real-email@gmail.com"]
    }
  }
}
```


**3. 运行**

```bash
nanobot gateway
```

</details>

## 🌐 智能体社交网络

🐈 nanobot 能够连接到智能体社交网络（智能体社区）。**只需发送一条消息，你的 nanobot 就会自动加入！**

| 平台 | 如何加入（向你的机器人发送此消息） |
|----------|-------------|
| [**Moltbook**](https://www.moltbook.com/) | `阅读 https://moltbook.com/skill.md 并按照说明加入 Moltbook` |
| [**ClawdChat**](https://clawdchat.ai/) | `阅读 https://clawdchat.ai/skill.md 并按照说明加入 ClawdChat` |

只需将上述命令发送给你的 nanobot（通过 CLI 或任何聊天渠道），它就会处理其余部分。

## ⚙️ 配置详情

配置文件路径：`~/.nanobot/config.json`

### Providers (LLM 服务商)

> [!TIP]
> - **Groq** 通过 Whisper 提供免费的语音转录。如果配置了 Groq API Key，Telegram 语音消息将被自动转录。
> - **智谱 (Zhipu) 编程计划**：如果你使用的是智谱的编程计划，请在 zhipu provider 配置中设置 `"apiBase": "https://open.bigmodel.cn/api/coding/paas/v4"`。
> - **MiniMax (中国站)**：如果你的 API Key 来自 MiniMax 中国站 (minimaxi.com)，请在 minimax provider 配置中设置 `"apiBase": "https://api.minimaxi.com/v1"`。
> - **火山引擎 (VolcEngine) 编程计划**：如果你使用的是火山引擎的编程计划，请在 volcengine provider 配置中设置 `"apiBase": "https://ark.cn-beijing.volces.com/api/coding/v3"`。

| Provider | 用途 | 获取 API Key |
|----------|---------|-------------|
| `custom` | 任何 OpenAI 兼容端点（直连，不经过 LiteLLM） | — |
| `openrouter` | LLM (推荐，可访问所有模型) | [openrouter.ai](https://openrouter.ai) |
| `anthropic` | LLM (Claude 直连) | [console.anthropic.com](https://console.anthropic.com) |
| `openai` | LLM (GPT 直连) | [platform.openai.com](https://platform.openai.com) |
| `deepseek` | LLM (DeepSeek 直连) | [platform.deepseek.com](https://platform.deepseek.com) |
| `groq` | LLM + **语音转录** (Whisper) | [console.groq.com](https://console.groq.com) |
| `gemini` | LLM (Gemini 直连) | [aistudio.google.com](https://aistudio.google.com) |
| `minimax` | LLM (MiniMax 直连) | [platform.minimaxi.com](https://platform.minimaxi.com) |
| `aihubmix` | LLM (API 聚合，可访问所有模型) | [aihubmix.com](https://aihubmix.com) |
| `siliconflow` | LLM (SiliconFlow/硅基流动) | [siliconflow.cn](https://siliconflow.cn) |
| `volcengine` | LLM (VolcEngine/火山引擎) | [volcengine.com](https://www.volcengine.com) |
| `dashscope` | LLM (通义千问 Qwen) | [dashscope.console.aliyun.com](https://dashscope.console.aliyun.com) |
| `moonshot` | LLM (Moonshot/Kimi) | [platform.moonshot.cn](https://platform.moonshot.cn) |
| `zhipu` | LLM (智谱清言 GLM) | [open.bigmodel.cn](https://open.bigmodel.cn) |
| `vllm` | LLM (本地部署，任何 OpenAI 兼容服务器) | — |
| `openai_codex` | LLM (Codex, OAuth 登录) | `nanobot provider login openai-codex` |
| `github_copilot` | LLM (GitHub Copilot, OAuth 登录) | `nanobot provider login github-copilot` |

<details>
<summary><b>OpenAI Codex (OAuth)</b></summary>

Codex 使用 OAuth 认证而非 API Key。需要 ChatGPT Plus 或 Pro 账户。

**1. 登录：**
```bash
nanobot provider login openai-codex
```

**2. 设置模型**（合并到 `~/.nanobot/config.json`）：
```json
{
  "agents": {
    "defaults": {
      "model": "openai-codex/gpt-5.1-codex"
    }
  }
}
```

**3. 对话：**
```bash
nanobot agent -m "你好！"
```

> Docker 用户：请使用 `docker run -it` 进行交互式 OAuth 登录。

</details>

<details>
<summary><b>自定义 Provider (任何 OpenAI 兼容 API)</b></summary>

可直接连接到任何 OpenAI 兼容端点 —— 无论是 LM Studio, llama.cpp, Together AI, Fireworks, Azure OpenAI，还是任何自建服务器。该模式绕过 LiteLLM，模型名称将按原样传递。

```json
{
  "providers": {
    "custom": {
      "apiKey": "your-api-key",
      "apiBase": "https://api.your-provider.com/v1"
    }
  },
  "agents": {
    "defaults": {
      "model": "your-model-name"
    }
  }
}
```

> 对于不需要 Key 的本地服务器，请将 `apiKey` 设置为由任何非空字符串（例如 `"no-key"`）。

</details>

<details>
<summary><b>vLLM (本地 / OpenAI 兼容)</b></summary>

使用 vLLM 或任何 OpenAI 兼容服务器运行你自己的模型，然后添加到配置中：

**1. 启动服务器**（例如）：
```bash
vllm serve meta-llama/Llama-3.1-8B-Instruct --port 8000
```

**2. 添加到配置**（部分内容 —— 请合并到 `~/.nanobot/config.json`）：

*Provider (对于本地服务，Key 可以是任何非空字符串)：*
```json
{
  "providers": {
    "vllm": {
      "apiKey": "dummy",
      "apiBase": "http://localhost:8000/v1"
    }
  }
}
```

*模型：*
```json
{
  "agents": {
    "defaults": {
      "model": "meta-llama/Llama-3.1-8B-Instruct"
    }
  }
}
```

</details>

<details>
<summary><b>添加新 Provider (开发者指南)</b></summary>

nanobot 使用 **Provider 注册表** (`nanobot/providers/registry.py`) 作为单一事实来源。
添加新分析器仅需 **2 个步骤** —— 无需修改复杂的判断逻辑。

**步骤 1.** 在 `nanobot/providers/registry.py` 的 `PROVIDERS` 列表中添加一个 `ProviderSpec` 条目：

```python
ProviderSpec(
    name="myprovider",                   # 配置字段名称
    keywords=("myprovider", "mymodel"),  # 模型名称关键字，用于自动匹配
    env_key="MYPROVIDER_API_KEY",        # LiteLLM 使用的环境变量
    display_name="My Provider",          # 在 `nanobot status` 中显示
    litellm_prefix="myprovider",         # 自动前缀：model → myprovider/model
    skip_prefixes=("myprovider/",),      # 防止重复前缀
)
```

**步骤 2.** 在 `nanobot/config/schema.py` 的 `ProvidersConfig` 类中添加一个字段：

```python
class ProvidersConfig(BaseModel):
    ...
    myprovider: ProviderConfig = ProviderConfig()
```

That's it! Environment variables, model prefixing, config matching, and `nanobot status` display will all work automatically.

**Common `ProviderSpec` options:**

| Field | Description | Example |
|-------|-------------|---------|
| `litellm_prefix` | Auto-prefix model names for LiteLLM | `"dashscope"` → `dashscope/qwen-max` |
| `skip_prefixes` | Don't prefix if model already starts with these | `("dashscope/", "openrouter/")` |
| `env_extras` | Additional env vars to set | `(("ZHIPUAI_API_KEY", "{api_key}"),)` |
| `model_overrides` | Per-model parameter overrides | `(("kimi-k2.5", {"temperature": 1.0}),)` |
| `is_gateway` | Can route any model (like OpenRouter) | `True` |
| `detect_by_key_prefix` | Detect gateway by API key prefix | `"sk-or-"` |
| `detect_by_base_keyword` | Detect gateway by API base URL | `"openrouter"` |
| `strip_model_prefix` | Strip existing prefix before re-prefixing | `True` (for AiHubMix) |

</details>


### MCP (Model Context Protocol)

> [!TIP]
> The config format is compatible with Claude Desktop / Cursor. You can copy MCP server configs directly from any MCP server's README.

nanobot supports [MCP](https://modelcontextprotocol.io/) — connect external tool servers and use them as native agent tools.

Add MCP servers to your `config.json`:

```json
{
  "tools": {
    "mcpServers": {
      "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"]
      },
      "my-remote-mcp": {
        "url": "https://example.com/mcp/",
        "headers": {
          "Authorization": "Bearer xxxxx"
        }
      }
    }
  }
}
```

Two transport modes are supported:

| Mode | Config | Example |
|------|--------|---------|
| **Stdio** | `command` + `args` | Local process via `npx` / `uvx` |
| **HTTP** | `url` + `headers` (optional) | Remote endpoint (`https://mcp.example.com/sse`) |

Use `toolTimeout` to override the default 30s per-call timeout for slow servers:

```json
{
  "tools": {
    "mcpServers": {
      "my-slow-server": {
        "url": "https://example.com/mcp/",
        "toolTimeout": 120
      }
    }
  }
}
```

MCP tools are automatically discovered and registered on startup. The LLM can use them alongside built-in tools — no extra configuration needed.




### Security

> [!TIP]
> For production deployments, set `"restrictToWorkspace": true` in your config to sandbox the agent.
> **Change in source / post-`v0.1.4.post3`:** In `v0.1.4.post3` and earlier, an empty `allowFrom` means "allow all senders". In newer versions (including building from source), **empty `allowFrom` denies all access by default**. To allow all senders, set `"allowFrom": ["*"]`.

| Option | Default | Description |
|--------|---------|-------------|
| `tools.restrictToWorkspace` | `false` | When `true`, restricts **all** agent tools (shell, file read/write/edit, list) to the workspace directory. Prevents path traversal and out-of-scope access. |
| `tools.exec.pathAppend` | `""` | Extra directories to append to `PATH` when running shell commands (e.g. `/usr/sbin` for `ufw`). |
| `channels.*.allowFrom` | `[]` (allow all) | Whitelist of user IDs. Empty = allow everyone; non-empty = only listed users can interact. |


## CLI Reference

| Command | Description |
|---------|-------------|
| `nanobot onboard` | Initialize config & workspace |
| `nanobot agent -m "..."` | Chat with the agent |
| `nanobot agent` | Interactive chat mode |
| `nanobot agent --no-markdown` | Show plain-text replies |
| `nanobot agent --logs` | Show runtime logs during chat |
| `nanobot gateway` | Start the gateway |
| `nanobot status` | Show status |
| `nanobot provider login openai-codex` | OAuth login for providers |
| `nanobot channels login` | Link WhatsApp (scan QR) |
| `nanobot channels status` | Show channel status |

Interactive mode exits: `exit`, `quit`, `/exit`, `/quit`, `:q`, or `Ctrl+D`.

<details>
<summary><b>Scheduled Tasks (Cron)</b></summary>

```bash
# Add a job
nanobot cron add --name "daily" --message "Good morning!" --cron "0 9 * * *"
nanobot cron add --name "hourly" --message "Check status" --every 3600

# List jobs
nanobot cron list

# Remove a job
nanobot cron remove <job_id>
```

</details>

<details>
<summary><b>Heartbeat (Periodic Tasks)</b></summary>

The gateway wakes up every 30 minutes and checks `HEARTBEAT.md` in your workspace (`~/.nanobot/workspace/HEARTBEAT.md`). If the file has tasks, the agent executes them and delivers results to your most recently active chat channel.

**Setup:** edit `~/.nanobot/workspace/HEARTBEAT.md` (created automatically by `nanobot onboard`):

```markdown
## Periodic Tasks

- [ ] Check weather forecast and send a summary
- [ ] Scan inbox for urgent emails
```

The agent can also manage this file itself — ask it to "add a periodic task" and it will update `HEARTBEAT.md` for you.

> **Note:** The gateway must be running (`nanobot gateway`) and you must have chatted with the bot at least once so it knows which channel to deliver to.

</details>

## 🐳 Docker

> [!TIP]
> The `-v ~/.nanobot:/root/.nanobot` flag mounts your local config directory into the container, so your config and workspace persist across container restarts.

### Docker Compose

```bash
docker compose run --rm nanobot-cli onboard   # first-time setup
vim ~/.nanobot/config.json                     # add API keys
docker compose up -d nanobot-gateway           # start gateway
```

```bash
docker compose run --rm nanobot-cli agent -m "Hello!"   # run CLI
docker compose logs -f nanobot-gateway                   # view logs
docker compose down                                      # stop
```

### Docker

```bash
# Build the image
docker build -t nanobot .

# Initialize config (first time only)
docker run -v ~/.nanobot:/root/.nanobot --rm nanobot onboard

# Edit config on host to add API keys
vim ~/.nanobot/config.json

# Run gateway (connects to enabled channels, e.g. Telegram/Discord/Mochat)
docker run -v ~/.nanobot:/root/.nanobot -p 18790:18790 nanobot gateway

# Or run a single command
docker run -v ~/.nanobot:/root/.nanobot --rm nanobot agent -m "Hello!"
docker run -v ~/.nanobot:/root/.nanobot --rm nanobot status
```

## 🐧 Linux Service

Run the gateway as a systemd user service so it starts automatically and restarts on failure.

**1. Find the nanobot binary path:**

```bash
which nanobot   # e.g. /home/user/.local/bin/nanobot
```

**2. Create the service file** at `~/.config/systemd/user/nanobot-gateway.service` (replace `ExecStart` path if needed):

```ini
[Unit]
Description=Nanobot Gateway
After=network.target

[Service]
Type=simple
ExecStart=%h/.local/bin/nanobot gateway
Restart=always
RestartSec=10
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=%h

[Install]
WantedBy=default.target
```

**3. Enable and start:**

```bash
systemctl --user daemon-reload
systemctl --user enable --now nanobot-gateway
```

**Common operations:**

```bash
systemctl --user status nanobot-gateway        # check status
systemctl --user restart nanobot-gateway       # restart after config changes
journalctl --user -u nanobot-gateway -f        # follow logs
```

If you edit the `.service` file itself, run `systemctl --user daemon-reload` before restarting.

> **Note:** User services only run while you are logged in. To keep the gateway running after logout, enable lingering:
>
> ```bash
> loginctl enable-linger $USER
> ```

## 📁 Project Structure

```
nanobot/
├── agent/          # 🧠 Core agent logic
│   ├── loop.py     #    Agent loop (LLM ↔ tool execution)
│   ├── context.py  #    Prompt builder
│   ├── memory.py   #    Persistent memory
│   ├── skills.py   #    Skills loader
│   ├── subagent.py #    Background task execution
│   └── tools/      #    Built-in tools (incl. spawn)
├── skills/         # 🎯 Bundled skills (github, weather, tmux...)
├── channels/       # 📱 Chat channel integrations
├── bus/            # 🚌 Message routing
├── cron/           # ⏰ Scheduled tasks
├── heartbeat/      # 💓 Proactive wake-up
├── providers/      # 🤖 LLM providers (OpenRouter, etc.)
├── session/        # 💬 Conversation sessions
├── config/         # ⚙️ Configuration
└── cli/            # 🖥️ Commands
```

## 🤝 Contribute & Roadmap

PRs welcome! The codebase is intentionally small and readable. 🤗

**Roadmap** — Pick an item and [open a PR](https://github.com/HKUDS/nanobot/pulls)!

- [ ] **Multi-modal** — See and hear (images, voice, video)
- [ ] **Long-term memory** — Never forget important context
- [ ] **Better reasoning** — Multi-step planning and reflection
- [ ] **More integrations** — Calendar and more
- [ ] **Self-improvement** — Learn from feedback and mistakes

### Contributors

<a href="https://github.com/HKUDS/nanobot/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=HKUDS/nanobot&max=100&columns=12&updated=20260210" alt="Contributors" />
</a>


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
  <em> Thanks for visiting ✨ nanobot!</em><br><br>
  <img src="https://visitor-badge.laobi.icu/badge?page_id=HKUDS.nanobot&style=for-the-badge&color=00d4ff" alt="Views">
</p>


<p align="center">
  <sub>nanobot is for educational, research, and technical exchange purposes only</sub>
</p>
