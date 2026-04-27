"""
Handler 模式 — 将 Agent Loop 的逻辑拆分为可组合的 Handler

参考 GenericAgent 的 agent_loop.py 设计，将 process_message 中的
工具调用处理、no_tool 处理、轮次结束回调等逻辑拆分为独立方法。
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable

from llm import LLMResponse, ToolCallRequest, smart_format


@dataclass
class StepOutcome:
    """单步执行的结果"""
    data: Optional[str] = None           # 工具结果或模型文本回复
    next_prompt: Optional[str] = None     # 需要注入的下一条提示（如失败提示、轮次警告）
    should_exit: bool = False             # 是否应该退出循环


class BaseHandler:
    """Handler 基类，定义 Agent Loop 中各阶段的回调接口"""

    def tool_before_callback(self, tool_name: str, arguments: Dict[str, Any]) -> None:
        """工具调用前的回调"""
        pass

    def tool_after_callback(self, tool_name: str, result: str, is_failed: bool) -> StepOutcome:
        """工具调用后的回调，返回 StepOutcome 决定后续行为"""
        return StepOutcome(data=result)

    def handle_no_tool(self, response: LLMResponse, iteration: int,
                       has_tool_been_called: bool) -> StepOutcome:
        """模型未调用工具时的处理"""
        return StepOutcome(data=response.content or "", should_exit=True)

    def turn_end_callback(self, iteration: int, consecutive_failures: int) -> Optional[str]:
        """每轮结束时的回调，返回需要注入的提示（或 None）"""
        return None


class PyClawHandler(BaseHandler):
    """PyClaw 专用 Handler

    将 process_message 中的逻辑拆为：
    - _handle_tool_call() — 单个工具调用的处理
    - _handle_no_tool() — 模型未调用工具时的处理（空回复、代码块未调用工具检测等）
    - turn_end_callback() — 每轮结束时的轮次警告
    """

    def __init__(self,
                 tool_start_callback: Callable[[str, Dict], None] = None,
                 tool_finish_callback: Callable[[str, str], None] = None,
                 flow_step_callback: Callable[[str, str], None] = None):
        self.tool_start_callback = tool_start_callback
        self.tool_finish_callback = tool_finish_callback
        self.flow_step_callback = flow_step_callback
        self._consecutive_failures = 0

    def _get_tool_step_name(self, tool_name: str) -> str:
        """根据工具名生成友好的流程步骤名称"""
        tool_step_map = {
            "exec": "正在执行命令...",
            "read_file": "正在读取文件...",
            "write_file": "正在写入文件...",
            "list_dir": "正在浏览目录...",
            "delete_file": "正在删除文件...",
            "file_patch": "正在精确修改文件...",
            "list_processes": "正在查询进程...",
            "kill_process": "正在终止进程...",
            "start_process": "正在启动进程...",
            "system_info": "正在获取系统信息...",
            "find_app": "正在搜索应用...",
            "launch_app": "正在启动应用...",
            "search_files": "正在搜索文件...",
            "search_in_files": "正在搜索文件内容...",
            "web_search": "正在搜索互联网信息...",
            "open_url": "正在打开网页...",
            "browser_read": "正在用浏览器读取网页...",
            "browser_screenshot": "正在用浏览器截取网页...",
            "image_ocr": "正在识别图片文字...",
            "translate": "正在翻译文本...",
            "image_caption": "正在生成图片描述...",
            "screenshot": "正在截取屏幕...",
            "image_vision": "正在分析图片内容...",
        }
        return tool_step_map.get(tool_name, f"正在执行 {tool_name}...")

    def tool_before_callback(self, tool_name: str, arguments: Dict[str, Any]) -> None:
        """工具调用前的回调"""
        step_name = self._get_tool_step_name(tool_name)
        if self.flow_step_callback:
            self.flow_step_callback(step_name, "active")
        if self.tool_start_callback:
            self.tool_start_callback(tool_name, arguments)

    def tool_after_callback(self, tool_name: str, result: str, is_failed: bool) -> StepOutcome:
        """工具调用后的回调 — 渐进式失败处理"""
        if self.flow_step_callback:
            self.flow_step_callback(self._get_tool_step_name(tool_name), "done")
        if self.tool_finish_callback:
            self.tool_finish_callback(tool_name, result)

        if not is_failed:
            self._consecutive_failures = 0
            return StepOutcome(data=result)

        self._consecutive_failures += 1
        cf = self._consecutive_failures

        if cf == 1:
            result += (
                "\n\n[系统提示] 上一步操作失败了。请分析错误原因，"
                "然后换一种方法重试。"
            )
        elif cf == 2:
            result += (
                "\n\n[系统提示] 连续2次失败。建议你调用 web_search "
                "搜索解决方案，然后根据搜索结果换方法。"
            )
        elif cf == 3:
            result += (
                "\n\n[系统强制] 连续3次失败。你必须立即调用 "
                "web_search 搜索解决方案，不能再盲目重试。"
            )
        elif cf >= 5:
            result += (
                f"\n\n[系统强制] 连续{cf}次失败。"
                "当前方法明显不可行。你必须：1. 换一种完全不同的方法；"
                "2. 如果没有其他方法，向用户说明情况并请求指导。"
            )
            self._consecutive_failures = 0  # 重置

        return StepOutcome(data=result, next_prompt=None)

    def handle_no_tool(self, response: LLMResponse, iteration: int,
                       has_tool_been_called: bool) -> StepOutcome:
        """模型未调用工具时的处理 — 空回复/截断/代码块检测"""
        content = response.content or ""

        # 检测1：空回复 — 自动重试
        if not content.strip():
            return StepOutcome(
                data="",
                next_prompt="你返回了空内容。请重新回答用户的问题，必须调用工具来执行操作或获取信息。",
                should_exit=False
            )

        # 检测2：max_tokens 截断 — 提示模型用更短步骤
        if response.finish_reason == "length":
            return StepOutcome(
                data=content,
                next_prompt=(
                    "你的回复被截断了（达到最大token限制）。"
                    "请用更简短的步骤完成，先调用工具执行当前最重要的操作，"
                    "不要在回复中写太长的内容。"
                ),
                should_exit=False
            )

        # 检测3：有大代码块但未调用工具 — 提示使用工具
        code_block_pattern = re.compile(r'```[\s\S]*?```')
        code_blocks = code_block_pattern.findall(content)
        if code_blocks and not has_tool_been_called:
            return StepOutcome(
                data=content,
                next_prompt=(
                    "你的回复中包含代码块但没有调用工具执行。"
                    "如果你想执行代码，请使用 exec 工具（先 write_file 写入文件再 exec 执行）。"
                    "如果你想修改文件，请使用 file_patch 或 write_file 工具。"
                    "不要只展示代码，必须通过工具来执行。"
                ),
                should_exit=False
            )

        # 代码级强制：如果从未调用过工具且是前几轮迭代，强制调用工具
        if not has_tool_been_called and iteration <= 3:
            return StepOutcome(
                data=content,
                next_prompt=(
                    "你刚才直接给出了答案而没有调用任何工具。请重新审视用户的需求，"
                    "必须调用合适的工具来获取信息或执行操作后再回答。"
                    "如果你回答的内容涉及实时信息（股市、新闻、天气等），必须使用 web_search 工具搜索。"
                    "如果你可以直接执行操作（打开应用、执行命令、读取文件等），必须调用对应工具。"
                ),
                should_exit=False
            )

        # 正常结束
        return StepOutcome(data=content, should_exit=True)

    def turn_end_callback(self, iteration: int, consecutive_failures: int) -> Optional[str]:
        """每轮结束时的轮次递进警告"""
        if iteration == 7:
            return (
                "[DANGER] 你已经执行了7轮操作但尚未完成任务。请审视："
                "1. 是否在无效重试同一方法？如果是，立即换策略。\n"
                "2. 是否需要更多信息？用 web_search 搜索。\n"
                "3. 当前方法是否根本不可行？如果是，换一种完全不同的方法。"
            )
        elif iteration == 15:
            return (
                "[WARNING] 你已经执行了15轮操作。建议你向用户确认是否继续，"
                "或者用更简短的方式总结当前进展后请求用户指示。"
            )
        elif iteration >= 20:
            return (
                "[CRITICAL] 你已经执行了20轮以上操作。你必须现在向用户报告进展并询问是否继续。"
            )
        return None

    @property
    def consecutive_failures(self) -> int:
        return self._consecutive_failures
