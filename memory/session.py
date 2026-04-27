"""
会话管理
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


class Session:
    """会话"""

    def __init__(self, key: str):
        self.key = key
        self.messages: List[Dict[str, Any]] = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """添加消息"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        if metadata:
            message["metadata"] = metadata
        self.messages.append(message)
        self.updated_at = datetime.now()

    def get_history(self, max_messages: int = 50, max_chars: int = 40000) -> List[Dict[str, str]]:
        """获取对话历史（LLM格式），自动裁剪过长内容"""
        history = []
        total_chars = 0
        # 从最新的消息开始取，直到达到限制
        messages = self.messages[-max_messages:]
        for msg in reversed(messages):
            content = msg["content"]
            total_chars += len(content) if isinstance(content, str) else len(str(content))
            if total_chars > max_chars and history:
                # 对最老的消息进行内容压缩
                if len(content) > 500:
                    content = content[:250] + "\n...[历史消息已压缩]...\n" + content[-250:]
                else:
                    break  # 消息本身就短，不再添加更老的消息
            history.append({
                "role": msg["role"],
                "content": content
            })
        history.reverse()
        return history

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "key": self.key,
            "messages": self.messages,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """从字典创建"""
        session = cls(data["key"])
        session.messages = data.get("messages", [])
        session.created_at = datetime.fromisoformat(data["created_at"])
        session.updated_at = datetime.fromisoformat(data["updated_at"])
        return session


class SessionManager:
    """会话管理器"""

    def __init__(self, sessions_dir: str):
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self._sessions: Dict[str, Session] = {}

    def get_or_create(self, key: str) -> Session:
        """获取或创建会话"""
        if key in self._sessions:
            return self._sessions[key]

        # 尝试从磁盘加载
        session = self._load(key)
        if not session:
            session = Session(key)

        self._sessions[key] = session
        return session

    def save(self, session: Session) -> None:
        """保存会话到磁盘"""
        session_file = self._get_session_file(session.key)
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)

    def trim_history(self, session: Session, max_chars: int = 60000) -> None:
        """裁剪会话历史，压缩最老消息中的长内容

        策略：
        1. 估算当前历史消息的字符总数
        2. 超过阈值时，压缩最老消息中的长内容（保留摘要，裁剪细节）
        3. 极端情况直接移除最老的 user-assistant 对
        """
        total_chars = sum(
            len(msg["content"]) if isinstance(msg["content"], str) else len(str(msg["content"]))
            for msg in session.messages
        )
        if total_chars <= max_chars:
            return

        print(f"[Session] 历史消息 {total_chars} 字符，超过阈值 {max_chars}，开始裁剪...")

        # 第一轮：压缩最老的长消息（保留首尾各200字符）
        for i, msg in enumerate(session.messages):
            content = msg["content"] if isinstance(msg["content"], str) else str(msg["content"])
            if len(content) > 1000:
                compressed = content[:200] + "\n...[历史消息已压缩]...\n" + content[-200:]
                session.messages[i]["content"] = compressed

        # 检查压缩后是否仍在阈值内
        total_chars = sum(
            len(msg["content"]) if isinstance(msg["content"], str) else len(str(msg["content"]))
            for msg in session.messages
        )
        if total_chars <= max_chars:
            print(f"[Session] 压缩完成，{len(session.messages)} 条消息")
            return

        # 第二轮：移除最老的 user-assistant 对，直到低于阈值
        while total_chars > max_chars * 0.6 and len(session.messages) > 2:
            # 找到第一个 user 消息并删除从它到下一个 user 消息之前的所有消息
            if session.messages[0]["role"] == "user":
                session.messages.pop(0)
                while session.messages and session.messages[0]["role"] in ("assistant", "tool"):
                    session.messages.pop(0)
            else:
                session.messages.pop(0)

            total_chars = sum(
                len(msg["content"]) if isinstance(msg["content"], str) else len(str(msg["content"]))
                for msg in session.messages
            )

        print(f"[Session] 裁剪完成，剩余 {len(session.messages)} 条消息，{total_chars} 字符")

    def _load(self, key: str) -> Optional[Session]:
        """从磁盘加载会话"""
        session_file = self._get_session_file(key)
        if session_file.exists():
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return Session.from_dict(data)
            except Exception:
                pass
        return None

    def _get_session_file(self, key: str) -> Path:
        """获取会话文件路径"""
        # 安全的文件名
        safe_key = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in key)
        return self.sessions_dir / f"{safe_key}.json"

    def list_sessions(self) -> List[str]:
        """列出所有会话"""
        sessions = []
        for file in self.sessions_dir.glob("*.json"):
            sessions.append(file.stem)
        return sessions

    def delete_session(self, key: str) -> bool:
        """删除会话"""
        if key in self._sessions:
            del self._sessions[key]

        session_file = self._get_session_file(key)
        if session_file.exists():
            session_file.unlink()
            return True
        return False
