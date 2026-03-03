---
name: newsletter
description: 自动搜集、总结并生成精美的行业简报或周报。
always: false
---

# 简报大师 (Newsletter Master)

当你被要求生成简报时，请利用以下工具组合：

1. **精准搜集**：使用 `web_search` (Tavily) 进行关键词搜索。
2. **深度阅读**：对搜索结果中的关键链接，使用 `python fetch_cn.py "URL"` 抓取正文。
3. **内容提炼**：
   - 必须包含【核心摘要】、【热点趋势】、【深度点评】。
   - 对重要新闻打上 #行业快讯 标签。
4. **自动化存档**：
   - 生成 Markdown 格式报告。
   - 默认存入桌面路径：`C:\Users\Administrator\Desktop\简报_日期.md`。

## 注意事项
- 优先选择 TechCrunch, 36Kr, GitHub Trending 等高质量信源。
- 确保日期准确。
