"""
文件系统工具
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from .base import Tool


class ReadFileTool(Tool):
    """读取文件工具"""

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "读取文件内容"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "文件路径"
                }
            },
            "required": ["path"]
        }

    async def execute(self, path: str) -> str:
        try:
            if not os.path.exists(path):
                return f"错误: 文件不存在: {path}"

            # 检查文件大小，避免读取超大文件
            if os.path.getsize(path) > 10 * 1024 * 1024:  # 10MB
                return f"错误: 文件过大 (超过10MB): {path}"

            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            return f"--- 文件: {path} ---\n{content}"
        except Exception as e:
            return f"读取文件错误: {str(e)}"


class WriteFileTool(Tool):
    """写入文件工具"""

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return "写入内容到文件，如果文件存在则覆盖"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "文件路径"
                },
                "content": {
                    "type": "string",
                    "description": "要写入的内容"
                }
            },
            "required": ["path", "content"]
        }

    async def execute(self, path: str, content: str) -> str:
        try:
            # 确保目录存在
            dir_path = os.path.dirname(path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)

            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

            return f"成功写入文件: {path} ({len(content)} 字符)"
        except Exception as e:
            return f"写入文件错误: {str(e)}"


class ListDirTool(Tool):
    """列出目录内容工具"""

    @property
    def name(self) -> str:
        return "list_dir"

    @property
    def description(self) -> str:
        return "列出目录内容"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "目录路径"
                }
            },
            "required": ["path"]
        }

    async def execute(self, path: str) -> str:
        try:
            if not os.path.exists(path):
                return f"错误: 目录不存在: {path}"

            if not os.path.isdir(path):
                return f"错误: 不是目录: {path}"

            items = os.listdir(path)
            items.sort()

            result = [f"--- 目录: {path} ---"]

            for item in items:
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    result.append(f"[DIR]  {item}/")
                else:
                    size = os.path.getsize(item_path)
                    result.append(f"[FILE] {item} ({size} 字节)")

            return "\n".join(result)
        except Exception as e:
            return f"列出目录错误: {str(e)}"


class DeleteFileTool(Tool):
    """删除文件工具"""

    @property
    def name(self) -> str:
        return "delete_file"

    @property
    def description(self) -> str:
        return "删除文件或目录（删除到回收站）"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "文件或目录路径"
                }
            },
            "required": ["path"]
        }

    async def execute(self, path: str) -> str:
        try:
            if not os.path.exists(path):
                return f"错误: 文件不存在: {path}"

            # 尝试使用send2trash，否则直接删除
            try:
                import send2trash
                send2trash.send2trash(path)
                return f"已移至回收站: {path}"
            except ImportError:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                return f"已永久删除: {path}"
        except Exception as e:
            return f"删除错误: {str(e)}"


class FilePatchTool(Tool):
    """文件局部修改工具 — 在文件中查找唯一的旧文本块并替换为新文本

    相比 write_file 的覆盖写入，file_patch 更安全精确：
    - 未找到匹配时返回错误，不会意外修改文件
    - 找到多处匹配时返回错误，要求提供更长的上下文确保唯一性
    """

    @property
    def name(self) -> str:
        return "file_patch"

    @property
    def description(self) -> str:
        return ("精确修改文件的一部分。在文件中查找唯一的 old_content 块并替换为 new_content。"
                "适合对已有文件做局部修改，比 write_file 更安全。"
                "如果未找到匹配或多处匹配会报错，请先用 read_file 确认当前内容。")

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "文件路径"
                },
                "old_content": {
                    "type": "string",
                    "description": "要替换的旧文本块（必须是文件中唯一匹配的）"
                },
                "new_content": {
                    "type": "string",
                    "description": "替换后的新文本"
                }
            },
            "required": ["path", "old_content", "new_content"]
        }

    async def execute(self, path: str, old_content: str, new_content: str) -> str:
        try:
            path = str(Path(path).resolve())

            if not os.path.exists(path):
                return f"错误: 文件不存在: {path}"

            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                full_text = f.read()

            if not old_content:
                return "错误: old_content 为空，请提供要替换的旧文本块"

            count = full_text.count(old_content)
            if count == 0:
                return ("错误: 未找到匹配的旧文本块。建议：先用 read_file 确认当前内容，"
                        "再使用 old_content 提供精确匹配的文本。注意缩进和空行。")
            if count > 1:
                return (f"错误: 找到 {count} 处匹配，无法确定唯一位置。"
                        f"请提供更长、更具体的旧文本块以确保唯一性。"
                        f"建议：包含上下文行来增强特征，或分小段逐个修改。")

            updated_text = full_text.replace(old_content, new_content)

            with open(path, 'w', encoding='utf-8') as f:
                f.write(updated_text)

            return f"文件局部修改成功: {path}"
        except Exception as e:
            return f"文件修改错误: {str(e)}"
