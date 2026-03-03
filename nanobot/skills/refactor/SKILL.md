---
name: refactor
description: 深度分析本地代码结构，利用 Context7 进行项目级审计，并提供安全重构方案。
always: false
---

# 代码重构贤者 (Refactor Sage) - Context7 增强版

当你接到代码优化任务时，请启动此高阶协同模式：

## 1. 全局审计 (Global Audit)
- **依赖分析**：使用 `mcp_context7_list_files` 和 `search` 了解代码在项目中的地位。
- **模式识别**：对比 `mcp_github` (30-seconds-of-code) 中的最佳实践，发现低效写法。

## 2. 逻辑推演 (Safe Reasoning)
- 启动 `mcp_thinking_sequentialthinking` 对拟修改点进行“影响评估”：
  - “修改这个函数会导致其他模块报错吗？”
  - “这个异步操作会导致死锁吗？”

## 3. 精准重构 (Precision Edit)
- 提供优化后的代码，并显式标注出复杂度（Time/Space Complexity）的提升。
- 引导模型优先使用 `edit_file` 执行局部替换，保留原有架构风格。

## 注意事项
- 严禁盲目删除未使用的代码，除非经过 Context7 全局确认。
- 确保重构后的代码符合 Windows 路径处理规范（双斜杠、路径对象化）。
