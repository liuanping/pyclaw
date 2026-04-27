"""
LLM提供者模块 - 阿里云Qwen模型调用（增强版）

增强功能：
- 重试机制（指数退避，最多3次）
- 请求超时配置
- 异步调用（使用 asyncio.to_thread 避免阻塞事件循环）
- smart_format 智能截断过长输出
- 上下文长度估算与自动裁剪
"""

import json
import asyncio
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


def smart_format(data: str, max_str_len: int = 6000, omit_str: str = '\n\n[...输出过长，已截断...]\n\n') -> str:
    """智能截断过长的字符串，保留头尾"""
    if not isinstance(data, str):
        data = str(data)
    if len(data) < max_str_len + len(omit_str) * 2:
        return data
    return f"{data[:max_str_len // 2]}{omit_str}{data[-max_str_len // 2:]}"


def estimate_messages_chars(messages: List[Dict]) -> int:
    """估算消息列表的字符总数"""
    return sum(len(json.dumps(m, ensure_ascii=False)) for m in messages)


def trim_messages(messages: List[Dict], max_chars: int = 80000) -> List[Dict]:
    """裁剪消息列表，使其不超过最大字符数

    策略：保留 system 消息和最近的消息，从最老的非 system 消息开始删除
    """
    cost = estimate_messages_chars(messages)
    if cost <= max_chars:
        return messages

    print(f"[Context] 当前上下文 {cost} 字符，超过阈值 {max_chars}，开始裁剪...")

    # 分离 system 消息和其余消息
    system_msgs = []
    other_msgs = []
    for m in messages:
        if m.get("role") == "system":
            system_msgs.append(m)
        else:
            other_msgs.append(m)

    # 从最老的消息开始删除，但保持 user/assistant/tool 的成对关系
    while other_msgs and estimate_messages_chars(system_msgs + other_msgs) > max_chars * 0.6:
        # 找到第一个 user 消息并删除从它到下一个 user 消息之前的所有消息
        if other_msgs[0].get("role") == "user":
            other_msgs.pop(0)
            # 继续删除直到下一个 user 消息（或 tool 消息后面接 user）
            while other_msgs and other_msgs[0].get("role") in ("assistant", "tool"):
                other_msgs.pop(0)
        else:
            other_msgs.pop(0)

    result = system_msgs + other_msgs
    new_cost = estimate_messages_chars(result)
    print(f"[Context] 裁剪完成，{cost} -> {new_cost} 字符，{len(result)} 条消息")
    return result


@dataclass
class ToolCallRequest:
    """工具调用请求"""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class LLMResponse:
    """LLM响应"""
    content: Optional[str]
    tool_calls: List[ToolCallRequest]
    finish_reason: str

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


class LLMProvider:
    """LLM提供者基类"""

    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """调用LLM"""
        raise NotImplementedError()

    async def chat_with_image(
        self,
        image_base64: str,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """调用多模态LLM识别图片"""
        raise NotImplementedError()


# 可重试的HTTP状态码
RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}


class QwenProvider(LLMProvider):
    """阿里云Qwen模型提供者（增强版）

    增强功能：
    - 重试机制：遇到可重试错误时自动重试，指数退避
    - 超时配置：connect_timeout 和 read_timeout 可配置
    - 异步调用：使用 asyncio.to_thread 避免阻塞事件循环
    - 上下文裁剪：自动裁剪过长的消息历史
    """

    def __init__(self, api_key: str, base_url: str, model_name: str,
                 temperature: float = 0.7, max_tokens: int = 4000,
                 max_retries: int = 3, connect_timeout: int = 10,
                 read_timeout: int = 120, max_context_chars: int = 80000):
        if OpenAI is None:
            raise ImportError("需要安装 openai 库: pip install openai>=1.3.0")

        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.max_context_chars = max_context_chars

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=connect_timeout
        )

    def _calculate_delay(self, attempt: int) -> float:
        """计算重试延迟（指数退避）"""
        return min(30.0, 1.5 * (2 ** attempt))

    def _is_retryable_error(self, error: Exception) -> bool:
        """判断错误是否可重试"""
        error_str = str(error).lower()
        # 网络错误、超时、服务端错误
        retryable_keywords = [
            'timeout', 'timed out', 'connection error', 'connection reset',
            '502', '503', '504', '429', 'rate limit', 'server error',
            'internal error', 'overloaded', 'capacity'
        ]
        return any(kw in error_str for kw in retryable_keywords)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """调用Qwen模型（带重试和上下文裁剪）"""
        model = model or self.model_name
        temperature = temperature if temperature is not None else self.temperature
        max_tokens = max_tokens or self.max_tokens

        # 自动裁剪过长的上下文
        messages = trim_messages(messages, max_chars=self.max_context_chars)

        # 构建调用参数
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        if tools:
            kwargs["tools"] = tools

        # 带重试的调用
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                # 使用 asyncio.to_thread 避免阻塞事件循环
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    **kwargs
                )
                return self._parse_response(response)

            except Exception as e:
                last_error = e
                if self._is_retryable_error(e) and attempt < self.max_retries:
                    delay = self._calculate_delay(attempt)
                    print(f"[LLM Retry] 第{attempt + 1}次调用失败: {str(e)[:100]}，{delay:.1f}秒后重试...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    print(f"LLM调用错误: {e}")
                    raise

        # 理论上不会到达这里，但以防万一
        raise last_error

    async def chat_with_image(
        self,
        image_base64: str,
        prompt: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """调用Qwen多模态模型识别图片（带重试）"""
        model = model or self.model_name
        temperature = temperature if temperature is not None else self.temperature
        max_tokens = max_tokens or self.max_tokens

        # 构建多模态消息
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]

        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        # 带重试的调用
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    **kwargs
                )
                return response.choices[0].message.content or ""
            except Exception as e:
                last_error = e
                if self._is_retryable_error(e) and attempt < self.max_retries:
                    delay = self._calculate_delay(attempt)
                    print(f"[LLM Retry] 多模态调用第{attempt + 1}次失败: {str(e)[:100]}，{delay:.1f}秒后重试...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    print(f"多模态LLM调用错误: {e}")
                    raise

        raise last_error

    def _parse_response(self, response) -> LLMResponse:
        """解析LLM响应"""
        choice = response.choices[0]
        message = choice.message

        tool_calls = []
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tc in message.tool_calls:
                args = tc.function.arguments
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {"raw": args}

                tool_calls.append(ToolCallRequest(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=args
                ))

        return LLMResponse(
            content=message.content,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason
        )
