"""
核心智能体（增强版）
"""

import os
import sys
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable

from llm import QwenProvider
from tools import (
    ToolRegistry,
    ExecTool,
    ReadFileTool, WriteFileTool, ListDirTool, DeleteFileTool, FilePatchTool,
    ListProcessesTool, KillProcessTool, StartProcessTool, SystemInfoTool,
    FindAppTool, LaunchAppTool,
    SearchFilesTool, SearchInFilesTool,
    ImageOCRTool, TranslateTool, ImageCaptionTool,
    ScreenshotTool, ImageVisionTool,
    WebSearchTool, OpenURLTool,
    BrowserReadTool, BrowserScreenshotTool,
)
from memory import MemoryStore, SessionManager
from .handler import PyClawHandler


SYSTEM_PROMPT = """你是 PyClaw，一个强大的桌面智能助手。你可以直接操作用户的电脑来完成任务。

## 铁律（必须遵守）
1. **禁止编造信息** — 你不知道任何实时数据（股市、天气、新闻、股价等），你的知识截止到2025年1月。所有需要实时信息的问题，必须调用 web_search 工具搜索。
2. **禁止只给建议** — 不要说"我建议你..."、"你可以..."、"要不要..."。用户让你做事，你直接调用工具去执行。
3. **必须先调用工具，再回答** — 遇到任何需要获取信息的任务，第一步永远是调用工具，绝不允许不调用工具就给出答案。
4. **当前时间: {current_time}** — 这是互联网同步的准确时间，用户问时间直接用这个值回答。

## 你拥有这台电脑的完全控制权
你可以使用电脑上的一切能力，无所不能：
- 执行任意命令行命令（安装软件、系统管理、网络操作、注册表修改等）
- 读写删除任意文件
- 启动/关闭任意程序和进程
- 用浏览器打开任意网页
- 搜索互联网获取实时信息
- 截屏并识别屏幕内容
- 操作注册表、服务、计划任务等系统功能
- **写代码并执行代码** — 你可以写Python脚本、批处理文件等，然后用 exec 运行
只要你能在命令行或GUI中做的事，你都能通过工具完成。不要犹豫，直接去做。

## 失败时必须继续尝试，直到成功
当你执行某个操作失败时，绝对不能直接告诉用户"失败了"就结束。你必须：
1. **分析失败原因** — 看看错误信息是什么，为什么会失败
2. **搜索解决方案** — 用 web_search 搜索"如何解决XXX"、"XXX错误怎么办"
3. **尝试新方法** — 根据搜索结果换一种方式执行
4. **写代码解决** — 如果没有现成工具可用，就写Python脚本或批处理文件来解决
5. **反复尝试** — 一次不行换另一种方法，继续尝试直到成功或穷尽所有可能

例如：
- launch_app 打不开应用 → 先 find_app 找路径 → 还不行就 exec 直接运行路径 → 还不行就 web_search 搜索如何启动该应用 → 找到方法后再执行
- exec 命令报错 → 分析错误 → 搜索解决方案 → 修正命令重新执行
- 某个功能没有现成工具 → 写一个Python脚本保存到临时文件 → exec 执行它

## 工具使用规则
- 用户要打开应用 → launch_app(app_name="应用名")，失败则 find_app + exec，再失败则 web_search 搜索启动方法
- 用户要打开网页/网站 → open_url(url="网址")，或先 web_search 搜索再打开
- 用户要搜索信息/查股市/查天气/查新闻 → web_search(query="搜索词")
- 搜索到链接后需要阅读详细内容 → browser_read(url="链接")，用浏览器打开页面提取全文
- 需要查看网页上的图表/数据可视化/截图 → browser_screenshot(url="链接")
- 用户要看文件 → read_file(path="路径")
- 用户要执行任何系统操作 → exec(command="命令")，包括但不限于：
  - 安装软件: pip install / winget install / choco install
  - 运行Python: python -c "代码" 或 python 脚本文件
  - 系统管理: netsh / sc / reg / schtasks / powershell
  - 网络操作: ping / curl / netstat / ipconfig
  - 文件操作: copy / move / mkdir / xcopy / robocopy
  - 任何其他命令行操作
- 用户要截图/看屏幕 → screenshot() 然后 image_vision()
- 用户要管理进程 → list_processes() / kill_process() / start_process()
- 遇到未知问题 → web_search(query="如何解决XXX") 搜索答案

## 工作流程（必须严格按此执行）
### 阶段一：THINK — 思考分析
- 仔细分析用户需求
- 确定需要哪些信息，哪些必须通过工具获取
- 规划要调用的工具及其参数
- **如果涉及实时/不确定的信息，第一步必须调用 web_search**

### 阶段二：ACT — 执行操作
- 按规划依次调用工具
- 每次工具返回后，根据结果决定下一步
- 如果工具失败，立即进入反思修复流程：
  1. 分析错误原因
  2. web_search 搜索解决方案
  3. 换方法重试或写代码解决
  4. 反复尝试直到成功

### 阶段三：VERIFY — 验证结果
- 检查任务是否真正完成
- 如果不确定结果是否正确，调用工具验证（如截图确认、读取文件确认等）
- 只有确认成功后才给出最终回复
- 如果验证发现未完成，回到 ACT 阶段继续执行

## 当前信息
- 时间: {current_time}
- 工作目录: {work_dir}
- 操作系统: {os_name}

## 记忆
你有记忆系统，会记录用户偏好。如果用户提到了重要的信息，请将其记录在记忆中。
"""


class Agent:
    """核心智能体"""

    def __init__(self, settings):
        self.settings = settings
        self._should_stop = False

        # 初始化LLM提供者
        self.llm = QwenProvider(
            api_key=settings.api_key,
            base_url=settings.base_url,
            model_name=settings.model_name,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens
        )

        # 初始化工具注册表
        self.tools = ToolRegistry()
        self._register_tools()

        # 初始化记忆系统
        self.memory = MemoryStore(str(settings.memory_dir))
        self.sessions = SessionManager(str(settings.sessions_dir))

        # 最大工具迭代次数 - 增加次数让任务更完整
        self.max_iterations = 50

        # 缓存网络时间，避免每次都请求
        self._cached_net_time = None

    def _get_network_time(self) -> str:
        """从互联网获取准确的北京时间，失败则回退到本地时间"""
        # 如果缓存有效（5分钟内），直接用缓存
        if self._cached_net_time:
            cached_dt, cached_str = self._cached_net_time
            if (datetime.now() - cached_dt).total_seconds() < 300:
                return cached_str

        try:
            # 方式1: 使用世界时间API
            resp = requests.get("http://worldtimeapi.org/api/timezone/Asia/Shanghai", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                time_str = data.get("datetime", "")
                if time_str:
                    # 格式: 2025-04-22T15:30:00.123456+08:00
                    net_time = datetime.fromisoformat(time_str).strftime("%Y-%m-%d %H:%M:%S")
                    self._cached_net_time = (datetime.now(), net_time)
                    return net_time
        except Exception:
            pass

        try:
            # 方式2: 使用淘宝时间API
            resp = requests.get("http://api.m.taobao.com/rest/api3.do?api=mtop.common.getTimestamp", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                t = data.get("data", {}).get("t", "")
                if t:
                    net_time = datetime.fromtimestamp(int(t) / 1000).strftime("%Y-%m-%d %H:%M:%S")
                    self._cached_net_time = (datetime.now(), net_time)
                    return net_time
        except Exception:
            pass

        # 回退到本地时间
        local_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return local_time

    def stop(self):
        """停止当前处理"""
        self._should_stop = True

    def reset_stop(self):
        """重置停止标志"""
        self._should_stop = False

    def _register_tools(self):
        """注册所有工具"""
        # Shell工具
        self.tools.register(ExecTool(working_dir=os.getcwd()))

        # 文件系统工具
        self.tools.register(ReadFileTool())
        self.tools.register(WriteFileTool())
        self.tools.register(ListDirTool())
        self.tools.register(DeleteFileTool())
        self.tools.register(FilePatchTool())

        # 进程管理工具
        self.tools.register(ListProcessesTool())
        self.tools.register(KillProcessTool())
        self.tools.register(StartProcessTool())
        self.tools.register(SystemInfoTool())
        self.tools.register(FindAppTool())
        self.tools.register(LaunchAppTool())

        # 搜索工具
        self.tools.register(SearchFilesTool())
        self.tools.register(SearchInFilesTool())
        self.tools.register(WebSearchTool())
        self.tools.register(OpenURLTool())

        # 浏览器工具
        self.tools.register(BrowserReadTool())
        self.tools.register(BrowserScreenshotTool(self.llm))

        # 媒体工具
        self.tools.register(ImageOCRTool())
        self.tools.register(TranslateTool())
        self.tools.register(ImageCaptionTool())
        self.tools.register(ScreenshotTool())
        self.tools.register(ImageVisionTool(self.llm))

    def _build_system_prompt(self) -> str:
        """构建系统提示"""
        current_time = self._get_network_time()
        work_dir = os.getcwd()
        os_name = sys.platform

        prompt = SYSTEM_PROMPT.format(
            current_time=current_time,
            work_dir=work_dir,
            os_name=os_name
        )

        # 添加记忆
        memory_context = self.memory.get_context()
        if memory_context:
            prompt += "\n\n" + memory_context

        # 添加工作记忆（每轮都注入）
        working_context = self.memory.get_working_context()
        if working_context:
            prompt += "\n\n## 工作记忆\n" + working_context

        return prompt

    # 需要联网搜索的关键词列表
    REALTIME_KEYWORDS = [
        "股市", "股票", "行情", "指数", "基金", "期货", "外汇",
        "天气", "气温", "温度", "下雨", "下雪",
        "新闻", "最新", "今天", "昨日", "近期", "最近",
        "比分", "比赛", "赛事", "联赛",
        "价格", "报价", "汇率", "油价", "金价",
        "排名", "排行", "榜单", "热搜",
        "疫情", "病例",
    ]

    async def process_message(
        self,
        user_message: str,
        tool_start_callback: Callable[[str, Dict], None] = None,
        tool_finish_callback: Callable[[str, str], None] = None,
        iteration_callback: Callable[[int], None] = None,
        flow_step_callback: Callable[[str, str], None] = None
    ) -> str:
        """处理用户消息 — THINK → ACT → VERIFY 三阶段流程（Handler 模式）"""
        # 重置停止标志
        self.reset_stop()

        # 检查是否是停止命令
        if "停止" in user_message or "stop" in user_message.lower():
            self.stop()
            return "好的，我已停止当前操作。"

        # 创建 Handler
        handler = PyClawHandler(
            tool_start_callback=tool_start_callback,
            tool_finish_callback=tool_finish_callback,
            flow_step_callback=flow_step_callback,
        )

        # 获取或创建会话
        session = self.sessions.get_or_create("main")

        # 构建消息列表
        messages = [{"role": "system", "content": self._build_system_prompt()}]
        messages.extend(session.get_history(max_messages=30))
        messages.append({"role": "user", "content": user_message})

        # 添加用户消息到会话
        session.add_message("user", user_message)

        # ============ 阶段一：THINK — 智能预处理 ============
        if self._needs_realtime_info(user_message):
            messages.append({
                "role": "user",
                "content": (
                    "[系统自动提示] 检测到你的需求可能涉及实时信息。"
                    "你必须在回答前先调用 web_search 工具搜索相关信息，"
                    "绝对不能用自己的知识来回答这个问题。"
                )
            })

        # 迭代处理
        iteration = 0
        final_response = ""
        has_tool_been_called = False

        if flow_step_callback:
            flow_step_callback("正在理解需求...", "active")

        while iteration < self.max_iterations and not self._should_stop:
            iteration += 1

            if iteration_callback:
                iteration_callback(iteration)

            # 每轮重新生成系统提示（注入最新的工作记忆）
            messages[0] = {"role": "system", "content": self._build_system_prompt()}

            # 轮次递进警告（通过 Handler）
            turn_warning = handler.turn_end_callback(iteration, handler.consecutive_failures)
            if turn_warning:
                messages.append({
                    "role": "user",
                    "content": turn_warning
                })

            # ============ 阶段二：ACT — 调用LLM执行 ============
            if flow_step_callback:
                flow_step_callback("正在调用LLM模型...", "active")
            try:
                response = await self.llm.chat(
                    messages=messages,
                    tools=self.tools.get_definitions()
                )
                if flow_step_callback:
                    flow_step_callback("LLM模型响应完成", "done")
            except Exception as e:
                if flow_step_callback:
                    flow_step_callback("LLM模型调用失败", "error")
                error_msg = f"调用模型时出错: {str(e)}"
                session.add_message("assistant", error_msg)
                self.sessions.save(session)
                return error_msg

            # 检查是否有工具调用
            if response.has_tool_calls and not self._should_stop:
                has_tool_been_called = True

                # 添加助手消息（包含工具调用）
                assistant_content = response.content or ""
                tool_call_dicts = []
                for tc in response.tool_calls:
                    tool_call_dicts.append({
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": str(tc.arguments)
                        }
                    })

                if tool_call_dicts:
                    messages.append({
                        "role": "assistant",
                        "content": assistant_content,
                        "tool_calls": tool_call_dicts
                    })
                else:
                    messages.append({
                        "role": "assistant",
                        "content": assistant_content
                    })

                # 执行工具调用（通过 Handler 回调）
                for tool_call in response.tool_calls:
                    if self._should_stop:
                        break

                    # tool_before_callback
                    handler.tool_before_callback(tool_call.name, tool_call.arguments)

                    # 执行工具
                    tool_result = await self.tools.execute(
                        tool_call.name,
                        **tool_call.arguments
                    )

                    # tool_after_callback — 渐进式失败处理
                    is_failed = self._is_tool_result_failed(tool_result)
                    outcome = handler.tool_after_callback(tool_call.name, tool_result, is_failed)
                    tool_result = outcome.data or tool_result

                    # 添加工具结果到消息
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.name,
                        "content": tool_result
                    })

                    # 每次工具调用后检查是否值得记忆
                    await self._check_and_save_memory(
                        user_message, tool_result[:200],
                        tool_name=tool_call.name, tool_result=tool_result
                    )

            else:
                # 没有工具调用 — 通过 Handler 处理
                outcome = handler.handle_no_tool(response, iteration, has_tool_been_called)

                if not outcome.should_exit and outcome.next_prompt:
                    # 需要注入提示让模型重新思考
                    messages.append({
                        "role": "assistant",
                        "content": outcome.data or ""
                    })
                    messages.append({
                        "role": "user",
                        "content": outcome.next_prompt
                    })
                    if flow_step_callback:
                        flow_step_callback("正在重新规划任务...", "active")
                    continue

                # ============ 阶段三：VERIFY — 验证结果 ============
                if has_tool_been_called:
                    verify_prompt = (
                        "[系统验证提示] 在给出最终回复前，请确认："
                        "1. 任务是否真正完成了？2. 结果是否正确？"
                        "3. 如果是操作类任务（如打开应用、执行命令），是否需要截图验证？"
                        "如果不确定结果，请调用工具验证后再回复。如果确认已完成，直接回复即可。"
                    )
                    messages.append({
                        "role": "assistant",
                        "content": outcome.data or ""
                    })
                    messages.append({
                        "role": "user",
                        "content": verify_prompt
                    })
                    verify_response = await self.llm.chat(
                        messages=messages,
                        tools=self.tools.get_definitions()
                    )
                    if verify_response.has_tool_calls and not self._should_stop:
                        for tc in verify_response.tool_calls:
                            if self._should_stop:
                                break
                            step_name = handler._get_tool_step_name(tc.name)
                            if flow_step_callback:
                                flow_step_callback(f"正在验证: {step_name}", "active")
                            tool_result = await self.tools.execute(tc.name, **tc.arguments)
                            if flow_step_callback:
                                flow_step_callback("验证完成", "done")
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tc.id,
                                "name": tc.name,
                                "content": tool_result
                            })
                        continue
                    else:
                        final_response = verify_response.content or outcome.data or ""
                else:
                    final_response = outcome.data or ""

                if flow_step_callback:
                    flow_step_callback("正在生成回复...", "active")
                if flow_step_callback:
                    flow_step_callback("任务完成", "done")
                session.add_message("assistant", final_response)
                self.sessions.save(session)
                self.sessions.trim_history(session)

                break

        if self._should_stop:
            final_response = "已停止操作。"
            session.add_message("assistant", final_response)
            self.sessions.save(session)
        elif iteration >= self.max_iterations:
            final_response = "我已经尝试了很多次，让我总结一下目前的进展：\n\n" + (response.content if 'response' in locals() else "没有完成")
            session.add_message("assistant", final_response)
            self.sessions.save(session)

        # 任务结束时清除工作记忆
        self.memory.clear_working_memory()

        return final_response

    def _needs_realtime_info(self, user_message: str) -> bool:
        """判断用户消息是否需要实时信息，用于THINK阶段预处理"""
        msg_lower = user_message.lower()
        return any(kw in msg_lower for kw in self.REALTIME_KEYWORDS)

    async def _check_and_save_memory(self, user_message: str, assistant_response: str,
                                        tool_name: str = "", tool_result: str = ""):
        """检查并保存重要信息到记忆

        改进：每次工具调用后都检查，而非仅首次迭代。
        使用关键词启发式判断是否值得记忆。
        """
        # 检查用户消息是否包含应记忆的信息
        keywords = ["记住", "记得", "我的", "喜欢", "偏好", "不要", "以后"]
        should_save = any(kw in user_message for kw in keywords)

        # 检查工具结果中是否包含值得记忆的信息
        if tool_name and tool_result:
            memory_tool_indicators = [
                ("exec", ["安装", "配置", "路径", "版本"]),
                ("read_file", ["配置", "设置", "环境变量"]),
                ("web_search", ["版本号", "下载地址", "官方文档"]),
            ]
            for tname, indicators in memory_tool_indicators:
                if tool_name == tname:
                    if any(ind in tool_result for ind in indicators):
                        should_save = True
                    break

        if should_save:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            memory_content = f"[{timestamp}] 用户: {user_message}\n"
            if tool_name:
                memory_content += f"工具: {tool_name} -> {tool_result[:200]}\n"
            memory_content += f"助手: {assistant_response}\n"
            self.memory.append_today(memory_content)

    def _is_tool_result_failed(self, result: str) -> bool:
        """判断工具执行结果是否表示失败"""
        if not result:
            return True
        result_lower = result.lower()
        fail_indicators = [
            "错误", "失败", "error", "fail", "not found", "未找到",
            "无法", "不能", "不存在", "拒绝", "denied", "timeout",
            "超时", "exception", "traceback", "无法找到", "无法启动"
        ]
        return any(indicator in result_lower for indicator in fail_indicators)

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
