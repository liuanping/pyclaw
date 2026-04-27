"""
记忆系统
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional


class MemoryStore:
    """记忆存储"""

    def __init__(self, memory_dir: str):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self.long_term_file = self.memory_dir / "MEMORY.md"
        self._ensure_long_term_file()

        # 工作记忆：存放当前任务的关键信息
        self._working_memory: dict = {
            "key_info": "",      # 当前任务关键信息
            "related_sop": "",   # 相关的标准操作流程
        }

    def _ensure_long_term_file(self):
        """确保长期记忆文件存在"""
        if not self.long_term_file.exists():
            with open(self.long_term_file, 'w', encoding='utf-8') as f:
                f.write("# PyClaw 长期记忆\n\n")
                f.write("这是 PyClaw 的长期记忆文件，记录重要的用户偏好和信息。\n\n")

    def _get_today_file(self) -> Path:
        """获取今日记忆文件"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.memory_dir / f"{today}.md"

    def read_today(self) -> str:
        """读取今日记忆"""
        today_file = self._get_today_file()
        if today_file.exists():
            with open(today_file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def append_today(self, content: str) -> None:
        """追加到今日记忆"""
        today_file = self._get_today_file()
        timestamp = datetime.now().strftime("%H:%M:%S")
        with open(today_file, 'a', encoding='utf-8') as f:
            f.write(f"\n## {timestamp}\n\n{content}\n")

    def read_long_term(self) -> str:
        """读取长期记忆"""
        with open(self.long_term_file, 'r', encoding='utf-8') as f:
            return f.read()

    def write_long_term(self, content: str) -> None:
        """写入长期记忆"""
        with open(self.long_term_file, 'w', encoding='utf-8') as f:
            f.write(content)

    def append_long_term(self, content: str) -> None:
        """追加到长期记忆"""
        with open(self.long_term_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{content}\n")

    def get_recent_memories(self, days: int = 7) -> str:
        """获取最近N天的记忆"""
        memories = []

        # 长期记忆
        long_term = self.read_long_term()
        if long_term:
            memories.append("## 长期记忆\n\n" + long_term)

        # 最近N天的记忆
        for i in range(days):
            from datetime import timedelta
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            memory_file = self.memory_dir / f"{date_str}.md"
            if memory_file.exists():
                with open(memory_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content:
                        memories.append(f"## {date_str}\n\n" + content)

        return "\n".join(memories)

    def update_working_checkpoint(self, key_info: str = "", related_sop: str = "") -> None:
        """更新工作记忆检查点

        在每次工具调用后检查是否需要更新，存放当前任务的关键信息。
        """
        if key_info:
            self._working_memory["key_info"] = key_info
        if related_sop:
            self._working_memory["related_sop"] = related_sop

    def get_working_context(self) -> str:
        """获取工作记忆的格式化字符串，用于每轮注入系统提示"""
        parts = []
        if self._working_memory.get("key_info"):
            parts.append(f"当前任务关键信息: {self._working_memory['key_info']}")
        if self._working_memory.get("related_sop"):
            parts.append(f"相关操作流程: {self._working_memory['related_sop']}")
        if parts:
            return "\n".join(parts)
        return ""

    def clear_working_memory(self) -> None:
        """清除工作记忆（任务完成或切换时调用）"""
        self._working_memory = {"key_info": "", "related_sop": ""}

    def get_context(self) -> str:
        """获取用于LLM的记忆上下文"""
        recent = self.get_recent_memories(days=3)
        if recent:
            return f"""## 记忆系统

{recent}
"""
        return ""
