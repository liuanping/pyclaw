"""
工具基类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class Tool(ABC):
    """工具基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """工具参数定义 (JSON Schema)"""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """执行工具"""
        pass

    def to_schema(self) -> Dict[str, Any]:
        """转换为OpenAI函数调用格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
