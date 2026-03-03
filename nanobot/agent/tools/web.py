"""Web tools: web_search and web_fetch."""

import html
import json
import os
import re
from typing import Any
from urllib.parse import urlparse

import httpx
from loguru import logger

# 本地化支持
from localization import get_translation as _t
from nanobot.agent.tools.base import Tool

# Shared constants
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_2) AppleWebKit/537.36"
MAX_REDIRECTS = 5  # Limit redirects to prevent DoS attacks


def _strip_tags(text: str) -> str:
    """Remove HTML tags and decode entities."""
    text = re.sub(r'<script[\s\S]*?</script>', '', text, flags=re.I)
    text = re.sub(r'<style[\s\S]*?</style>', '', text, flags=re.I)
    text = re.sub(r'<[^>]+>', '', text)
    return html.unescape(text).strip()


def _normalize(text: str) -> str:
    """Normalize whitespace."""
    text = re.sub(r'[ \t]+', ' ', text)
    return re.sub(r'\n{3,}', '\n\n', text).strip()


def _validate_url(url: str) -> tuple[bool, str]:
    """Validate URL: must be http(s) with valid domain."""
    try:
        p = urlparse(url)
        if p.scheme not in ('http', 'https'):
            return False, _t("agent.tools.web.error.invalid_url", f"Only http/https allowed, got '{p.scheme or 'none'}'")
        if not p.netloc:
            return False, _t("agent.tools.web.error.missing_domain", "Missing domain")
        return True, ""
    except Exception as e:
        return False, str(e)


class WebSearchTool(Tool):
    """Search the web using Tavily AI Search API."""

    name = _t("agent.tools.web.search.name", "web_search")
    description = "强大的互联网搜索工具，专为 AI 优化。支持获取实时新闻、技术文档及 AI 生成的问题回答。"
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "搜索关键词或自然语言问题"},
            "count": {"type": "integer", "description": "返回结果数量 (1-10)", "minimum": 1, "maximum": 10}
        },
        "required": ["query"]
    }

    def __init__(self, api_key: str | None = None, max_results: int = 5, proxy: str | None = None):
        # 默认使用用户提供的 Tavily Key
        self._init_api_key = api_key or "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"
        self.max_results = max_results
        self.proxy = proxy

    @property
    def api_key(self) -> str:
        return self._init_api_key or os.environ.get("TAVILY_API_KEY", "")

    async def execute(self, query: str, count: int | None = None, **kwargs: Any) -> str:
        if not self.api_key:
            return "错误：Tavily API Key 未配置。"

        try:
            # 免费版 Tavily 建议 count 不要超过 5
            n = min(max(count or self.max_results, 1), 5)
            logger.debug("WebSearch (Tavily): {}", "proxy enabled" if self.proxy else "direct connection")

            async with httpx.AsyncClient(proxy=self.proxy, timeout=25.0) as client:
                payload = {
                    "api_key": self.api_key,
                    "query": query,
                    "search_depth": "basic", # 基础搜索更稳定
                    "max_results": n,
                    "include_answer": True
                }
                r = await client.post("https://api.tavily.com/search", json=payload)
                r.raise_for_status()
                data = r.json()

            lines = [f"🌐 搜索结果: {query}\n"]

            # 优先展示 Tavily 的 AI 摘要
            if answer := data.get("answer"):
                lines.append(f"<b>💡 AI 总结：</b>\n{answer}\n")

            results = data.get("results", [])[:n]
            if not results and not answer:
                return f"未找到关于 '{query}' 的搜索结果。"

            for i, item in enumerate(results, 1):
                lines.append(f"{i}. <a href=\"{item.get('url', '#')}\">{item.get('title', '无标题')}</a>")
                if content := item.get("content"):
                    lines.append(f"   {content[:400]}...")
                lines.append("") # 换行

            return "\n".join(lines)
        except Exception as e:
            logger.error("Tavily Search error: {}", e)
            return f"搜索失败 (Tavily): {str(e)}"


class WebFetchTool(Tool):
    """Fetch and extract content from a URL using Readability."""

    name = _t("agent.tools.web.fetch.name", "web_fetch")
    description = _t("agent.tools.web.fetch.description", "Fetch URL and extract readable content (HTML → markdown/text).")
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": _t("agent.tools.web.fetch.params.url", "URL to fetch")},
            "extractMode": {"type": "string", "enum": ["markdown", "text"], "default": "markdown"},
            "maxChars": {"type": "integer", "minimum": 100}
        },
        "required": ["url"]
    }

    def __init__(self, max_chars: int = 50000, proxy: str | None = None):
        self.max_chars = max_chars
        self.proxy = proxy

    async def execute(self, url: str, extract_mode: str = "markdown", max_chars: int | None = None, **kwargs: Any) -> str:
        from readability import Document

        max_chars = max_chars or self.max_chars
        is_valid, error_msg = _validate_url(url)
        if not is_valid:
            return json.dumps({"error": _t("agent.tools.web.fetch.error.url_validation_failed", f"URL validation failed: {error_msg}"), "url": url}, ensure_ascii=False)

        try:
            logger.debug("WebFetch: {}", "proxy enabled" if self.proxy else "direct connection")
            async with httpx.AsyncClient(
                follow_redirects=True,
                max_redirects=MAX_REDIRECTS,
                timeout=30.0,
                proxy=self.proxy,
            ) as client:
                r = await client.get(url, headers={"User-Agent": USER_AGENT})
                r.raise_for_status()

            ctype = r.headers.get("content-type", "")

            if "application/json" in ctype:
                text, extractor = json.dumps(r.json(), indent=2, ensure_ascii=False), "json"
            elif "text/html" in ctype or r.text[:256].lower().startswith(("<!doctype", "<html")):
                doc = Document(r.text)
                content = self._to_markdown(doc.summary()) if extract_mode == "markdown" else _strip_tags(doc.summary())
                text = f"# {doc.title()}\n\n{content}" if doc.title() else content
                extractor = "readability"
            else:
                text, extractor = r.text, "raw"

            truncated = len(text) > max_chars
            if truncated:
                text = text[:max_chars]

            return json.dumps({"url": url, "finalUrl": str(r.url), "status": r.status_code,
                              "extractor": extractor, "truncated": truncated, "length": len(text), "text": text}, ensure_ascii=False)
        except httpx.ProxyError as e:
            logger.error("WebFetch proxy error for {}: {}", url, e)
            return json.dumps({"error": _t("agent.tools.web.fetch.error.proxy_error", f"Proxy error: {e}"), "url": url}, ensure_ascii=False)
        except Exception as e:
            logger.error("WebFetch error for {}: {}", url, e)
            return json.dumps({"error": str(e), "url": url}, ensure_ascii=False)

    def _to_markdown(self, html: str) -> str:
        """Convert HTML to markdown."""
        # Convert links, headings, headings, lists before stripping tags
        text = re.sub(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>([\s\S]*?)</a>',
                      lambda m: f'[{_strip_tags(m[2])}]({m[1]})', html, flags=re.I)
        text = re.sub(r'<h([1-6])[^>]*>([\s\S]*?)</h\1>',
                      lambda m: f'\n{"#" * int(m[1])} {_strip_tags(m[2])}\n', text, flags=re.I)
        text = re.sub(r'<li[^>]*>([\s\S]*?)</li>', lambda m: f'\n- {_strip_tags(m[1])}', text, flags=re.I)
        text = re.sub(r'</(p|div|section|article)>', '\n\n', text, flags=re.I)
        text = re.sub(r'<(br|hr)\s*/?>', '\n', text, flags=re.I)
        return _normalize(_strip_tags(text))
