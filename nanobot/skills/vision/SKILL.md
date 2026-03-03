---
name: vision
description: 利用 Puppeteer 截图能力，对网页进行 UI 审美分析或前端代码临摹。
always: false
---

# 网页视觉捕手 (Visual Researcher)

当你需要访问网页并进行视觉分析时，请启动此模式：

## 1. 精准捕获 (Capture)
- **指令**：使用 `mcp_browser_puppeteer_screenshot({"url": "..."})` 获取页面截图。
- **保存**：截图会自动保存在系统的临时目录，Agent 应当立即利用多模态能力查看该截图。

## 2. 视觉分析 (Audit)
- 分析页面的配色方案、字体排版、间距分布。
- 检查是否存在响应式布局的问题。

## 3. 前端临摹 (Implementation)
- 基于看到的视觉效果，参考 `mcp_github` 中的最佳实践，提供 HTML/CSS 或 React 代码建议。

## 注意事项
- 截图完成后，必须向用户发送确认信息（如：“我已经看到了页面的视觉设计...”）。
- 如果页面加载极其缓慢，请告知用户可能存在网络延迟。
