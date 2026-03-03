---
name: tester
description: 基于 Context7 的代码引用分析，生成覆盖单元、集成和边界情况的完整测试套件。
always: false
---

# 测试用例大师 (Test Prophet) - 全链路增强版

当你被要求编写测试或查找 Bug 时，请启动此“先知”深度模式：

## 1. 引用链追踪 (Traceability)
- 使用 `mcp_context7_search` 查找该函数在整个项目中的调用位置。
- 确定所有的输入源（API 请求、配置文件、用户输入）。

## 2. 模拟环境构建 (Mocking Strategy)
- 如果代码涉及外部 MCP 服务器或 Qdrant 调用，指导模型编写 Mock 对象进行隔离。
- 参考 `mcp_github` 上的测试范式，确保断言（Assert）的严密性。

## 3. 边界推演 (Boundary Prophet)
- 必须配合 `mcp_thinking_sequentialthinking` 推演极端情况下的系统表现。

## 4. 交付质量 (Quality Check)
- 生成的测试脚本应能直接运行在 `pytest` 或 `jest` 框架下。
- 提供一份“覆盖率预估报告”。

## 注意事项
- 测试代码必须包含中文注释，解释为什么要测试这个特定场景。
- 优先处理涉及磁盘 IO 和网络请求的异步逻辑测试。
