---
name: summarize
description: 从 URL、播客和本地文件中总结或提取文本/转录内容（是“转录此 YouTube/视频”的绝佳备选方案）。
homepage: https://summarize.sh
metadata: {"nanobot":{"emoji":"🧾","requires":{"bins":["summarize"]},"install":[{"id":"brew","kind":"brew","formula":"steipete/tap/summarize","bins":["summarize"],"label":"安装 summarize (brew)"}]}}
---

# 总结 (Summarize)

快速 CLI 工具，用于总结 URL、本地文件和 YouTube 链接。

## 何时使用（触发词）

当用户询问以下内容时，请立即使用此技能：
- “使用 summarize.sh”
- “这个链接/视频讲了什么？”
- “总结这个 URL/文章”
- “转录这个 YouTube/视频”（尽力提取转录内容；不需要 `yt-dlp`）

## 快速入门

```bash
summarize "https://example.com" --model google/gemini-3-flash-preview
summarize "/path/to/file.pdf" --model google/gemini-3-flash-preview
summarize "https://youtu.be/dQw4w9WgXcQ" --youtube auto
```

## YouTube：总结 vs 转录

尽力提取转录内容（仅限 URL）：

```bash
summarize "https://youtu.be/dQw4w9WgXcQ" --youtube auto --extract-only
```

如果用户要求的转录内容非常庞大，请先返回一个精简的总结，然后询问需要展开哪个部分或时间段。

## 模型与密钥

为所选的提供商设置 API 密钥：
- OpenAI: `OPENAI_API_KEY`
- Anthropic: `ANTHROPIC_API_KEY`
- xAI: `XAI_API_KEY`
- Google: `GEMINI_API_KEY`（别名：`GOOGLE_GENERATIVE_AI_API_KEY`, `GOOGLE_API_KEY`）

如果未设置，默认模型为 `google/gemini-3-flash-preview`。

## 常用参数 (Flags)

- `--length short|medium|long|xl|xxl|<字符数>`
- `--max-output-tokens <数量>`
- `--extract-only`（仅限 URL）
- `--json`（机器可读格式）
- `--firecrawl auto|off|always`（备选提取方案）
- `--youtube auto`（如果设置了 `APIFY_API_TOKEN`，则使用 Apify 作为备选方案）

## 配置 (Config)

可选配置文件：`~/.summarize/config.json`

```json
{ "model": "openai/gpt-5.2" }
```

可选服务：
- `FIRECRAWL_API_KEY` 用于访问被拦截的网站
- `APIFY_API_TOKEN` 用于 YouTube 备选提取方案
