#!/usr/bin/env python3
"""
测试 PyClaw 是否能够正常导入
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 50)
print("PyClaw 导入测试")
print("=" * 50)

tests = [
    ("配置模块", "from config import Settings"),
    ("工具基类", "from tools import Tool"),
    ("工具注册表", "from tools import ToolRegistry"),
    ("Shell工具", "from tools import ExecTool"),
    ("文件工具", "from tools import ReadFileTool, WriteFileTool, FilePatchTool"),
    ("进程工具", "from tools import ListProcessesTool"),
    ("搜索工具", "from tools import SearchFilesTool"),
    ("浏览器工具", "from tools import BrowserReadTool, BrowserScreenshotTool"),
    ("LLM提供者", "from llm import QwenProvider"),
    ("记忆存储", "from memory import MemoryStore"),
    ("会话管理", "from memory import SessionManager"),
    ("智能体", "from core import Agent"),
    ("Handler", "from core import PyClawHandler, StepOutcome"),
    ("LLM工具", "from llm import smart_format, trim_messages"),
]

all_passed = True

for name, import_stmt in tests:
    try:
        exec(import_stmt)
        print(f"✓ {name}: 通过")
    except Exception as e:
        print(f"✗ {name}: 失败 - {e}")
        all_passed = False

print("=" * 50)
if all_passed:
    print("所有测试通过！可以正常启动 PyClaw")
    print("运行: python main.py")
else:
    print("部分测试失败，请检查依赖是否正确安装")
    print("运行: pip install -r requirements.txt")
print("=" * 50)

# 检查依赖
print("\n依赖检查:")
try:
    import PyQt5
    print("✓ PyQt5: 已安装")
except ImportError:
    print("✗ PyQt5: 未安装")

try:
    import openai
    print("✓ openai: 已安装")
except ImportError:
    print("✗ openai: 未安装")

try:
    import psutil
    print("✓ psutil: 已安装")
except ImportError:
    print("✗ psutil: 未安装")

try:
    import PIL
    print("✓ Pillow: 已安装")
except ImportError:
    print("✗ Pillow: 未安装")
