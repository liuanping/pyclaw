"""
文件搜索工具
"""

import os
import re
from typing import Dict, Any, List
from pathlib import Path
from .base import Tool


class SearchFilesTool(Tool):
    """搜索文件工具"""

    @property
    def name(self) -> str:
        return "search_files"

    @property
    def description(self) -> str:
        return "按文件名搜索文件"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词"
                },
                "search_path": {
                    "type": "string",
                    "description": "搜索路径（可选，默认当前目录）"
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "是否区分大小写（默认false）"
                },
                "max_results": {
                    "type": "integer",
                    "description": "最大结果数（默认50）"
                }
            },
            "required": ["query"]
        }

    async def execute(
        self,
        query: str,
        search_path: str = None,
        case_sensitive: bool = False,
        max_results: int = 50
    ) -> str:
        try:
            search_path = search_path or os.getcwd()

            if not os.path.exists(search_path):
                return f"错误: 路径不存在: {search_path}"

            results = []
            flags = 0 if case_sensitive else re.IGNORECASE
            pattern = re.compile(re.escape(query), flags)

            for root, dirs, files in os.walk(search_path):
                # 跳过隐藏目录
                dirs[:] = [d for d in dirs if not d.startswith('.')]

                for file in files:
                    if pattern.search(file):
                        full_path = os.path.join(root, file)
                        results.append(full_path)
                        if len(results) >= max_results:
                            break
                if len(results) >= max_results:
                    break

            if results:
                return f"找到 {len(results)} 个文件:\n" + "\n".join(results)
            else:
                return f"未找到包含 '{query}' 的文件"
        except Exception as e:
            return f"搜索文件错误: {str(e)}"


class SearchInFilesTool(Tool):
    """在文件内容中搜索工具"""

    @property
    def name(self) -> str:
        return "search_in_files"

    @property
    def description(self) -> str:
        return "在文件内容中搜索文本"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索文本"
                },
                "search_path": {
                    "type": "string",
                    "description": "搜索路径（可选）"
                },
                "file_pattern": {
                    "type": "string",
                    "description": "文件匹配模式，例如 *.py（可选）"
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "是否区分大小写（默认false）"
                },
                "max_results": {
                    "type": "integer",
                    "description": "最大结果数（默认20）"
                }
            },
            "required": ["query"]
        }

    async def execute(
        self,
        query: str,
        search_path: str = None,
        file_pattern: str = None,
        case_sensitive: bool = False,
        max_results: int = 20
    ) -> str:
        try:
            search_path = search_path or os.getcwd()

            if not os.path.exists(search_path):
                return f"错误: 路径不存在: {search_path}"

            results = []
            flags = 0 if case_sensitive else re.IGNORECASE
            pattern = re.compile(re.escape(query), flags)

            for root, dirs, files in os.walk(search_path):
                dirs[:] = [d for d in dirs if not d.startswith('.')]

                for file in files:
                    # 文件过滤
                    if file_pattern:
                        from fnmatch import fnmatch
                        if not fnmatch(file, file_pattern):
                            continue

                    full_path = os.path.join(root, file)

                    # 跳过大文件
                    if os.path.getsize(full_path) > 5 * 1024 * 1024:  # 5MB
                        continue

                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                            for line_num, line in enumerate(f, 1):
                                if pattern.search(line):
                                    results.append(f"{full_path}:{line_num}: {line.strip()}")
                                    if len(results) >= max_results:
                                        break
                    except Exception:
                        pass

                    if len(results) >= max_results:
                        break
                if len(results) >= max_results:
                    break

            if results:
                return f"找到 {len(results)} 个匹配:\n" + "\n".join(results)
            else:
                return f"未找到包含 '{query}' 的内容"
        except Exception as e:
            return f"搜索内容错误: {str(e)}"
