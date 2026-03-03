import asyncio
import re
import sys

import httpx


class SmartContentScraper:
    """Advanced Python Scraper with Noise Reduction and Density Analysis."""

    @staticmethod
    def _clean_html(html: str) -> str:
        # 1. 强力移除无关标签
        noise_tags = [
            r'<script.*?>.*?</script>', r'<style.*?>.*?</style>',
            r'<nav.*?>.*?</nav>', r'<footer.*?>.*?</footer>',
            r'<header.*?>.*?</header>', r'<select.*?>.*?</select>',
            r'<form.*?>.*?</form>', r'<iframe.*?>.*?</iframe>',
            r'<aside.*?>.*?</aside>', r'<button.*?>.*?</button>'
        ]
        for tag in noise_tags:
            html = re.sub(tag, '', html, flags=re.S|re.I)

        # 2. 提取标题
        title = "No Title"
        tm = re.search(r'<title>(.*?)</title>', html, re.I)
        if tm: title = tm.group(1).strip()

        # 3. 提取主体内容（寻找 <div> 或 <main> 标签中包含最多 <p> 的区域）
        # 简单实现：将所有块级标签转换为换行，保留文本
        text = re.sub(r'<(h[1-6]|p|div|section|article|li).*?>', r'\n', html, flags=re.I)
        text = re.sub(r'<.*?>', '', text, flags=re.S)

        # 4. 行过滤：剔除字数过少或包含过多特殊符号的行（通常是导航或菜单）
        clean_lines = []
        for line in text.splitlines():
            line = line.strip()
            if len(line) < 15: continue # 过滤短行
            if line.count('|') > 3 or line.count('{') > 1: continue # 过滤菜单/代码碎片
            clean_lines.append(line)

        return f"# {title}\n\n" + "\n\n".join(clean_lines[:100]) # 取前 100 段

    async def scrape(self, url: str):
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        try:
            async with httpx.AsyncClient(timeout=25.0, follow_redirects=True, verify=False) as client:
                r = await client.get(url, headers=headers)
                r.raise_for_status()
                return self._clean_html(r.text)
        except Exception as e:
            return f"抓取错误: {str(e)}"

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://github.com/trending"
    scraper = SmartContentScraper()
    print(asyncio.run(scraper.scrape(url)))
