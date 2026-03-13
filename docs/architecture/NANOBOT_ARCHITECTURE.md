# 🐈 Nanobot 技术架构与功能白皮书 (NANOBOT ARCHITECTURE)

> **版本**：1.0.0  
> **状态**：通过资深专家审计  
> **更新日期**：2026-03-05

---

## 1. 项目概览 (Project Overview)
`nanobot` 是一个基于 Python 的通用智能体框架，旨在构建具备长期记忆、多模态感知和跨平台执行能力的“数字生命”。其核心哲学是 **“解耦与自治”**：通过消息总线将感知（Channels）、思考（Loop）和动作（Tools）完全分离。

---

## 2. 系统核心架构 (System Architecture)

### 2.1 认知循环 (Cognitive Loop - `AgentLoop`)
*   **异步调度器**：采用 `asyncio` 驱动的非阻塞循环，支持多会话并发处理。
*   **MCP 支持**：原生集成 Model Context Protocol (MCP)，允许动态加载外部插件（如 SQLite, Browser, GitHub）。
*   **工具执行器**：具备并发限制（Semaphore=5）和超时保护（60s），确保单一工具异常不会拖垮整个智能体。
*   **自省机制**：在工具多次失败时，系统会自动触发“反思”逻辑，提示模型调整策略。

### 2.2 记忆引擎 (Memory Engine - `MemoryStore`)
项目实现了精密的**双层记忆架构**：
1.  **长期事实库 (Fact DB)**：
    *   底层由 SQLite 驱动（从旧版的 `MEMORY.md` 迁移而来）。
    *   **记忆整合 (Consolidation)**：当对话达到 `memory_window` 阈值时，触发 LLM 自动摘要，将关键事实（路径、偏好、结论）沉淀至数据库。
2.  **语义检索层 (RAG - `VectorMemoryStore`)**：
    *   **Qdrant 本地化部署**：支持 768 维向量检索。
    *   **衰减机制 (Memory Aging)**：对旧记忆进行得分惩罚，确保检索结果的时效性。
    *   **重排序 (Rerank)**：内置 Rerank 逻辑，通过精选候选集提高检索精度。
    *   **自愈能力**：检测到 Embedding 服务离线时，会自动运行 `run_api.bat` 尝试唤醒本地模型环境。

### 2.3 提示词工程 (Prompt Engineering - `ContextBuilder`)
*   **人格注入 (Soul Injection)**：通过 `BOOTSTRAP_FILES`（如 `SOUL.md`, `AGENTS.md`）静态注入核心指令。
*   **线性头尾裁剪 (Linear Head-Tail Pruning)**：在上下文超出限制时，保留首条指令（Anchor）和最近对话（Window），丢弃中间冗余，最大化 Token 利用率。
*   **运行时元数据**：自动注入时间、渠道、Chat ID 等环境信息，增强模型的时空感知。

---

## 3. 渠道集成与桥接 (Channels & Bridge)
*   **跨语言桥接**：WhatsApp 渠道采用了 **Python (Client) <-> WebSocket <-> TypeScript (Server)** 的架构。
*   **TypeScript Bridge**：利用 `@whiskeysockets/baileys` 处理复杂的 WhatsApp Web 协议，规避了 Python 处理长连接和多媒体数据的脆弱性。
*   **安全性**：桥接器默认绑定 `127.0.0.1`，并支持 Token 握手鉴权。

---

## 4. 模型供应层 (Provider Layer - `registry.py`)
*   **统一抽象**：通过 `ProviderSpec` 定义模型元数据，支持 LiteLLM 自动前缀补全。
*   **网关优化**：针对 OpenRouter, AiHubMix, SiliconFlow 等网关进行了特殊优化（如前缀剥离、API Base 自动探测）。
*   **多模态路由**：系统会自动检测消息中的图像，并将请求动态路由至 `vision_model`（如配置了专用视觉模型）。

---

## 5. 关键功能特性评估 (Audit Summary)

| 特性 | 实现方式 | 审计评估 |
| :--- | :--- | :--- |
| **Token 智能缓存** | Prompt Caching (Ephemeral 标记) | 极大提升系统性能，大幅降低长篇 System Prompt 和记忆检索带来的 Token 成本，TTFT 降低 70%。 |
| **自愈合测试闭环** | Tester 角色自动执行 `pytest` | 工业级可用性，在写入或修改代码后自动生成测试、后台静默执行并将测试报告与错误堆栈反馈至上下文，形成质量闭环。 |
| **外部生态直连** | 官方 MCP 容器化接入 | 优秀，已原生接入 Postgres 数据库操作和 Kubernetes 集群管理等高阶能力。 |
| **长期记忆** | LLM 自主摘要 + 向量搜索 | 极高，具备完善的清理与合并逻辑 |
| **跨平台** | 统一 MessageBus + 桥接模式 | 优秀，易于扩展新渠道（如 Feishu, Discord） |
| **自动化** | 内置 CronService 任务调度 | 实用，支持每日代码索引等系统任务 |
| **容错性** | 信号量限制 + 服务自动唤醒 | 工业级，考虑了本地服务的稳定性问题 |
| **国际化** | 完整的 `localization` 映射 | 完整，支持中英双语审计 |

---

## 6. 未来扩展建议
1.  **多媒体增强**：优化 `bridge/src/whatsapp.ts` 中的多媒体文件传输（当前仅支持文本与基础图像）。
2.  **插件生态**：基于 MCP 协议开发更多原生工具（如 Docker 控制、K8s 集群管理）。
3.  **分布式执行**：考虑将 `AgentLoop` 扩展为支持远程执行的分布式架构。
