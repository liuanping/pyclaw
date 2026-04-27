"""
Shell 执行工具
"""

import asyncio
import os
from typing import Dict, Any
from .base import Tool


class ExecTool(Tool):
    """执行Shell命令工具"""

    def __init__(self, working_dir: str = None):
        self.working_dir = working_dir or os.getcwd()

    @property
    def name(self) -> str:
        return "exec"

    @property
    def description(self) -> str:
        return "执行任意Shell命令，返回stdout、stderr和退出码。你可以执行任何命令，包括系统管理、网络操作、软件安装、文件操作等所有命令行操作。"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "要执行的Shell命令"
                },
                "working_dir": {
                    "type": "string",
                    "description": "工作目录（可选）"
                }
            },
            "required": ["command"]
        }

    async def execute(self, command: str, working_dir: str = None) -> str:
        """执行Shell命令"""
        cwd = working_dir or self.working_dir

        try:
            # 创建进程
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )

            # 等待完成，设置超时
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=60.0
                )
            except asyncio.TimeoutError:
                process.kill()
                return "错误: 命令执行超时（60秒）"

            # 解码输出
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')

            result = f"命令: {command}\n"
            result += f"退出码: {process.returncode}\n"
            if stdout_str:
                result += f"stdout:\n{stdout_str}\n"
            if stderr_str:
                result += f"stderr:\n{stderr_str}\n"

            return result

        except Exception as e:
            return f"执行错误: {str(e)}"
