"""
网页搜索和浏览器工具

- WebSearchTool: 百度+Bing 双引擎搜索
- BrowserReadTool: Playwright 页面内容提取
- BrowserScreenshotTool: Playwright 网页截图
- OpenURLTool: 在用户浏览器中打开网页
"""

import os
import base64
import asyncio
import webbrowser
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from .base import Tool


# 通用请求头
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


# ── 搜索引擎解析 ──────────────────────────────────────────

def _search_baidu(query: str, num_results: int = 5) -> list:
    """百度搜索，返回 [{title, snippet, url}]"""
    url = f"https://www.baidu.com/s?wd={requests.utils.quote(query)}"
    resp = requests.get(url, headers=_HEADERS, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    results = []
    for container in soup.select("#content_left .c-container")[:num_results]:
        title_el = container.select_one("h3 a")
        # 摘要可能在 .c-abstract 或直接在容器文本中
        snippet_el = container.select_one(".c-abstract")
        if not snippet_el:
            # 部分百度结果的摘要不在 .c-abstract 中，取容器内首段长文本
            for p in container.select("span, p, div"):
                text = p.get_text(strip=True)
                if len(text) > 30:
                    snippet_el = p
                    break

        title = title_el.get_text(strip=True) if title_el else ""
        snippet = snippet_el.get_text(strip=True) if snippet_el else ""
        link = title_el.get("href", "") if title_el else ""

        if title:
            results.append({"title": title, "snippet": snippet, "url": link})

    return results


def _search_bing(query: str, num_results: int = 5) -> list:
    """Bing 搜索，返回 [{title, snippet, url}]"""
    url = f"https://cn.bing.com/search?q={requests.utils.quote(query)}"
    resp = requests.get(url, headers=_HEADERS, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    results = []
    for item in soup.select("li.b_algo")[:num_results]:
        title_el = item.select_one("h2 a")
        snippet_el = item.select_one(".b_caption p") or item.select_one("p")
        title = title_el.get_text(strip=True) if title_el else ""
        snippet = snippet_el.get_text(strip=True) if snippet_el else ""
        link = title_el.get("href", "") if title_el else ""

        if title:
            results.append({"title": title, "snippet": snippet, "url": link})

    return results


def _format_results(query: str, results: list, engine: str) -> str:
    """格式化搜索结果"""
    if not results:
        return f"使用 {engine} 未找到关于 '{query}' 的搜索结果。"
    lines = [f"搜索 '{query}' 的结果（{engine}）：\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. 【{r['title']}】")
        if r["snippet"]:
            lines.append(f"   {r['snippet']}")
        if r["url"]:
            lines.append(f"   链接：{r['url']}")
        lines.append("")
    return "\n".join(lines)


# ── WebSearchTool ──────────────────────────────────────────

class WebSearchTool(Tool):
    """网页搜索工具 — 百度 + Bing 双引擎 fallback"""

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return (
            "搜索互联网上的实时信息，包括新闻、股市、天气、最新数据等。"
            "当用户询问需要实时数据、最新信息、或者未知的事实时使用。"
            "搜索结果包含链接，可以用 browser_read 工具进一步阅读某个链接的详细内容。"
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词，比如 '今日上证指数'、'Python最新版本' 等"
                },
                "num_results": {
                    "type": "integer",
                    "description": "返回的搜索结果数量，默认5",
                    "default": 5
                },
                "search_engine": {
                    "type": "string",
                    "description": "搜索引擎选择：'baidu'（默认）或 'bing'",
                    "default": "baidu",
                    "enum": ["baidu", "bing"]
                }
            },
            "required": ["query"]
        }

    async def execute(self, query: str, num_results: int = 5,
                      search_engine: str = "baidu") -> str:
        """执行网页搜索 — 双引擎 fallback"""
        try:
            if search_engine == "bing":
                results = _search_bing(query, num_results)
                if results:
                    return _format_results(query, results, "Bing")
                # Bing 没结果，fallback 到百度
                results = _search_baidu(query, num_results)
                return _format_results(query, results, "百度")
            else:
                results = _search_baidu(query, num_results)
                if results:
                    return _format_results(query, results, "百度")
                # 百度没结果，fallback 到 Bing
                results = _search_bing(query, num_results)
                return _format_results(query, results, "Bing")
        except Exception as e:
            # 主引擎失败时尝试备选引擎
            try:
                if search_engine == "bing":
                    results = _search_baidu(query, num_results)
                    return _format_results(query, results, "百度")
                else:
                    results = _search_bing(query, num_results)
                    return _format_results(query, results, "Bing")
            except Exception as e2:
                return f"搜索失败：{str(e)}；备选引擎也失败：{str(e2)}"


# ── BrowserReadTool ────────────────────────────────────────

class BrowserReadTool(Tool):
    """浏览器页面内容提取工具 — 用 Playwright 打开 URL 并提取正文"""

    @property
    def name(self) -> str:
        return "browser_read"

    @property
    def description(self) -> str:
        return (
            "用浏览器打开指定 URL 并提取页面的文字内容。"
            "适合阅读网页的详细内容，如新闻全文、股票数据页、技术文档、博客文章等。"
            "当 web_search 返回了链接但你还需要更详细的内容时，用此工具阅读该链接。"
            "可选参数 selector 用于只提取页面中某个特定区域的内容。"
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "要阅读的网页 URL"
                },
                "selector": {
                    "type": "string",
                    "description": "可选，CSS 选择器，只提取页面中匹配该选择器的元素内容。"
                                   "例如 'article'、'.content'、'#main' 等。不填则提取整个页面正文。",
                    "default": ""
                },
                "max_length": {
                    "type": "integer",
                    "description": "返回内容的最大字符数，默认8000",
                    "default": 8000
                }
            },
            "required": ["url"]
        }

    async def execute(self, url: str, selector: str = "",
                      max_length: int = 8000) -> str:
        """用 Playwright 打开页面并提取内容"""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                try:
                    await page.goto(url, wait_until="commit", timeout=20000)
                    # 等待 domcontentloaded 或最多 5 秒
                    try:
                        await page.wait_for_load_state("domcontentloaded", timeout=5000)
                    except Exception:
                        pass
                    # 等待动态内容加载
                    await page.wait_for_timeout(2000)

                    # 提取内容
                    if selector:
                        el = await page.query_selector(selector)
                        if el:
                            text = await el.inner_text()
                        else:
                            text = await page.evaluate("() => document.body.innerText")
                            text = f"[警告: 未找到选择器 '{selector}'，已返回整页内容]\n\n{text}"
                    else:
                        text = await page.evaluate("() => document.body.innerText")

                    title = await page.title()

                    # 截断过长内容
                    if len(text) > max_length:
                        text = text[:max_length // 2] + \
                               "\n\n[...页面内容过长，已截断...]\n\n" + \
                               text[-max_length // 2:]

                    return f"--- 页面: {title} ---\nURL: {url}\n\n{text}"

                finally:
                    await browser.close()

        except ImportError:
            return "错误: 需要安装 playwright 库 (pip install playwright && playwright install chromium)"
        except Exception as e:
            error_str = str(e)
            if "Timeout" in error_str:
                return f"页面加载超时: {url}（{error_str[:100]}）"
            if "net::" in error_str:
                return f"网络错误，无法访问: {url}（{error_str[:100]}）"
            return f"读取页面失败: {error_str[:200]}"


# ── BrowserScreenshotTool ──────────────────────────────────

class BrowserScreenshotTool(Tool):
    """浏览器截图工具 — 用 Playwright 对网页截图"""

    def __init__(self, llm_provider=None):
        self._llm = llm_provider

    @property
    def name(self) -> str:
        return "browser_screenshot"

    @property
    def description(self) -> str:
        return (
            "用浏览器打开指定 URL 并截图。适合查看网页的视觉效果、图表、数据可视化等。"
            "截图会自动调用视觉模型分析图片内容。"
            "当你需要查看网页上的图表、表格、图片，或者想确认网页操作结果时使用。"
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "要截图的网页 URL"
                },
                "full_page": {
                    "type": "boolean",
                    "description": "是否截取整个页面（true）还是只截视口区域（false，默认）",
                    "default": False
                },
                "selector": {
                    "type": "string",
                    "description": "可选，CSS 选择器，只截取页面中匹配该选择器的元素",
                    "default": ""
                }
            },
            "required": ["url"]
        }

    async def execute(self, url: str, full_page: bool = False,
                      selector: str = "") -> str:
        """用 Playwright 截图并分析"""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(viewport={"width": 1920, "height": 1080})

                try:
                    await page.goto(url, wait_until="commit", timeout=20000)
                    try:
                        await page.wait_for_load_state("domcontentloaded", timeout=5000)
                    except Exception:
                        pass
                    await page.wait_for_timeout(2000)

                    # 截图
                    if selector:
                        el = await page.query_selector(selector)
                        if el:
                            screenshot_bytes = await el.screenshot()
                        else:
                            screenshot_bytes = await page.screenshot(full_page=full_page)
                    else:
                        screenshot_bytes = await page.screenshot(full_page=full_page)

                    title = await page.title()
                    screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")

                    # 如果有 LLM 提供者，自动分析截图
                    if self._llm:
                        analysis = await self._llm.chat_with_image(
                            image_base64=screenshot_b64,
                            prompt=(
                                "请描述这个网页截图中的关键信息，包括："
                                "1. 页面标题和主要内容；"
                                "2. 任何数据、数字、图表；"
                                "3. 重要的文字信息。"
                                "用中文回答，简洁明了。"
                            )
                        )
                        return f"--- 网页截图分析: {title} ---\nURL: {url}\n\n{analysis}"
                    else:
                        return (
                            f"已截取网页截图: {title}\n"
                            f"URL: {url}\n"
                            f"截图大小: {len(screenshot_bytes)} 字节\n"
                            f"提示: 截图已生成但未配置视觉模型，无法分析图片内容。"
                        )

                finally:
                    await browser.close()

        except ImportError:
            return "错误: 需要安装 playwright 库 (pip install playwright && playwright install chromium)"
        except Exception as e:
            return f"网页截图失败: {str(e)[:200]}"


# ── OpenURLTool ────────────────────────────────────────────

class OpenURLTool(Tool):
    """打开网页/URL工具 — 用用户的默认浏览器打开"""

    @property
    def name(self) -> str:
        return "open_url"

    @property
    def description(self) -> str:
        return (
            "用用户的默认浏览器打开指定的网页 URL。"
            "仅用于让用户在浏览器中查看网页，不会读取页面内容。"
            "如果你需要读取网页内容，请使用 browser_read 工具。"
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "要打开的网页 URL"
                }
            },
            "required": ["url"]
        }

    async def execute(self, url: str) -> str:
        """在默认浏览器中打开 URL"""
        try:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            webbrowser.open(url)
            return f"已在浏览器中打开: {url}"
        except Exception as e:
            return f"打开URL失败: {str(e)}"
