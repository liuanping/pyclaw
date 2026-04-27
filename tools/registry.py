"""
工具注册表
"""

from typing import Dict, List, Any, Optional
from .base import Tool
from llm import smart_format


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """注册工具"""
        self._tools[tool.name] = tool

    def unregister(self, tool_name: str) -> None:
        """注销工具"""
        if tool_name in self._tools:
            del self._tools[tool_name]

    def get(self, tool_name: str) -> Optional[Tool]:
        """获取工具"""
        return self._tools.get(tool_name)

    def get_definitions(self) -> List[Dict[str, Any]]:
        """获取所有工具的定义"""
        return [tool.to_schema() for tool in self._tools.values()]

    async def execute(self, tool_name: str, **kwargs) -> str:
        """执行工具"""
        tool = self._tools.get(tool_name)
        if not tool:
            return f"错误: 找不到工具 '{tool_name}'"
        try:
            result = await tool.execute(**kwargs)
            # 对过长的工具结果进行智能截断，避免消耗过多上下文 token
            return smart_format(result, max_str_len=6000)
        except Exception as e:
            return f"工具 '{tool_name}' 执行错误: {str(e)}"

    def list_tools(self) -> List[str]:
        """列出所有工具名称"""
        return list(self._tools.keys())
