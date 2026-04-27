"""
配置管理模块
"""

import json
import os
from pathlib import Path


class Settings:
    """设置管理类"""

    def __init__(self):
        self.config_dir = Path.home() / ".pyclaw"
        self.config_file = self.config_dir / "config.json"
        self.workspace_dir = self.config_dir / "workspace"
        self.memory_dir = self.workspace_dir / "memory"
        self.sessions_dir = self.config_dir / "sessions"

        # 默认配置
        self.default_config = {
            "model": {
                "api_key": "sk-fa0c1234567891011cea123456",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "model_name": "qwen3.6-flash-2026-04-16",
                "temperature": 0.7,
                "max_tokens": 4000
            },
            "ui": {
                "ball_size": 50,
                "ball_position": "bottom_right",
                "theme": "dark"
            },
            "tools": {
                "shell_enabled": True,
                "file_enabled": True,
                "process_enabled": True,
                "max_tool_iterations": 15
            }
        }

        self._config = None
        self._ensure_directories()
        self._load_config()

    def _ensure_directories(self):
        """确保必要的目录存在"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self):
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except Exception:
                self._config = self.default_config.copy()
        else:
            self._config = self.default_config.copy()
            self._save_config()

    def _save_config(self):
        """保存配置文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, ensure_ascii=False, indent=2)

    def get(self, key_path, default=None):
        """获取配置值"""
        keys = key_path.split('.')
        value = self._config
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key_path, value):
        """设置配置值"""
        keys = key_path.split('.')
        config = self._config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
        self._save_config()

    @property
    def api_key(self):
        return self.get("model.api_key")

    @property
    def base_url(self):
        return self.get("model.base_url")

    @property
    def model_name(self):
        return self.get("model.model_name")

    @property
    def temperature(self):
        return self.get("model.temperature")

    @property
    def max_tokens(self):
        return self.get("model.max_tokens")

    @property
    def ball_size(self):
        return self.get("ui.ball_size", 50)

    @property
    def max_tool_iterations(self):
        return self.get("tools.max_tool_iterations", 15)
