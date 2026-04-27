# PyClaw 项目文件结构

```
pyclaw/
│
├── __init__.py                 # 包初始化
├── main.py                     # 主程序入口
├── test_imports.py             # 导入测试脚本
├── requirements.txt            # Python依赖
├── start.bat                   # Windows启动脚本
└── README.md                   # 项目说明
│
├── config/                     # 配置模块
│   ├── __init__.py
│   └── settings.py             # 设置管理类
│
├── core/                       # 核心模块
│   ├── __init__.py
│   └── agent.py                # 智能体核心逻辑
│
├── ui/                         # 界面模块
│   ├── __init__.py
│   ├── floating_ball.py        # 悬浮球组件
│   └── main_window.py          # 主对话窗口
│
├── llm/                        # 大模型模块
│   ├── __init__.py
│   └── provider.py             # LLM提供者 (阿里云Qwen)
│
├── tools/                      # 工具模块
│   ├── __init__.py
│   ├── base.py                 # 工具基类
│   ├── registry.py             # 工具注册表
│   ├── shell.py                # Shell执行工具
│   ├── filesystem.py           # 文件系统工具
│   ├── process.py              # 进程管理工具
│   ├── search.py               # 文件搜索工具
│   └── media.py                # 媒体处理工具
│
└── memory/                     # 记忆模块
    ├── __init__.py
    ├── store.py                # 记忆存储
    └── session.py              # 会话管理
```

## 核心架构

### 1. Agent (智能体核心)
- 协调 LLM 和工具的交互
- 管理对话上下文
- 实现工具调用循环

### 2. Tools (工具系统)
- 基础工具类 (Tool)
- 工具注册表 (ToolRegistry)
- 各类具体工具实现

### 3. LLM (大模型)
- QwenProvider - 阿里云Qwen模型
- 支持 Function Calling

### 4. Memory (记忆系统)
- MemoryStore - 长期/短期记忆
- SessionManager - 会话管理

### 5. UI (用户界面)
- FloatingBall - 悬浮球
- MainWindow - 对话窗口

## 快速开始

1. 双击 `start.bat` (Windows)
2. 或运行: `python main.py`

首次启动会在 `~/.pyclaw/` 创建配置和数据目录。
