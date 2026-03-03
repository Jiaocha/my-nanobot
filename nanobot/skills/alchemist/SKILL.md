---
name: alchemist
description: 专门负责消化长文章、网页或链接，提炼核心知识点并存入向量记忆。
always: false
---

# 个人知识库炼金术士 (Knowledge Alchemist)

当你收到一个需要“消化”或“学习”的链接时，请启动此精炼模式：

## 1. 深度萃取 (Extraction)
- **抓取**：优先使用本地 Python 驱动获取网页全文。
  ```bash
  python fetch_cn.py "目标URL"
  ```
- **视觉**：如果网页需要截图分析，使用 `mcp_browser_puppeteer_screenshot`。

## 2. 逻辑炼金 (Alchemy)
- 必须启动 `mcp_thinking_sequentialthinking` 进行深度思考。
- **三段式拆解**：
  - **What**：核心概念与定义。
  - **How**：运作逻辑与方法论。
  - **So What**：对用户的启发与关联。

## 3. 永久索引 (Memory Injection)
- 将提炼出的摘要（带上 `#知识库` 标签）通过 `search_memory` 的同步逻辑存入 Qdrant 向量库。

## 注意事项
- 使用 `fetch_cn.py` 时，返回的内容前 5000 字为核心正文。
- 如果抓取失败，请直接告知用户 URL 可能存在访问限制。
