# PyClaw - 智能电脑助手

一个类似 OpenClaw 和 NanoClaw 的纯 Python 桌面智能助手。

## 功能特性

### 💻 系统管理
- 进程管理（启动、停止、查看进程
- 系统监控
- 安装和卸载软件

### 📁 文件管理
- 文件搜索（按名称、内容
- 文件整理和归类
- 大文件、重复文件管理

### 🛠️ 能力提升
- 图片内容识别（OCR）
- 文本翻译
- 代码编写
- 图片分析

### 🧠 智能特性
- Function Calling 工具调用
- 本地记忆系统
- 会话历史记录
- 阿里云 Qwen 模型集成

## 安装说明

### 1. 克隆或下载项目

```bash
cd pyclaw
```

### 2. 安装依赖

#### Windows (使用启动脚本（推荐）

双击 `start.bat` 文件，它会自动：
- 创建虚拟环境
- 安装依赖
- 启动程序

#### 手动安装

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动程序
python main.py
```

### 3. 可选依赖（可选功能

如果需要使用 OCR 图片识别功能：

1. 安装 Tesseract OCR 引擎：
   - 下载地址：https://github.com/UB-Mannheim/tesseract/wiki
   - 安装后将 Tesseract 目录添加到系统 PATH

## 使用说明

### 基本使用

1. 启动程序后，屏幕右下角会出现悬浮球
2. 拖动悬浮球可以移动位置
3. 点击悬浮球打开对话窗口
4. 在输入框中输入命令，点击发送

### 示例命令

```
帮我查看系统信息
```

```
搜索一下当前目录下的Python文件
```

```
帮我列出正在运行的进程
```

```
翻译这段文字成英文：你好世界
```

```
识别这张图片中的文字：C:\path\to\image.png
```

## 项目结构

```
pyclaw/
├── main.py              # 主程序入口
├── requirements.txt    # 依赖列表
├── start.bat          # Windows启动脚本
├── config/            # 配置模块
│   └── settings.py    # 设置管理
├── core/              # 核心模块
│   └── agent.py       # 智能体实现
├── ui/                # 界面模块
│   ├── floating_ball.py  # 悬浮球
│   └── main_window.py    # 主窗口
├── llm/               # 大模型模块
│   └── provider.py      # LLM提供者
├── tools/             # 工具模块
│   ├── base.py         # 工具基类
│   ├── registry.py     # 工具注册表
│   ├── shell.py        # Shell工具
│   ├── filesystem.py   # 文件系统工具
│   ├── process.py      # 进程管理工具
│   ├── search.py       # 搜索工具
│   └── media.py        # 媒体处理工具
└── memory/            # 记忆模块
    ├── store.py        # 记忆存储
    └── session.py     # 会话管理
```

## 配置说明

配置文件位于 `~/.pyclaw/config.json`，首次运行后自动生成。

主要配置项：

```json
{
  "model": {
    "api_key": "sk-xxx",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "model_name": "qwen3.5-27b",
    "temperature": 0.7,
    "max_tokens": 4000
  }
}
```

## 内置工具

| 工具名称 | 功能描述 |
|---------|---------|
| `exec` | 执行Shell命令 |
| `read_file` | 读取文件 |
| `write_file` | 写入文件 |
| `list_dir` | 列出目录 |
| `delete_file` | 删除文件 |
| `list_processes` | 列出进程 |
| `kill_process` | 结束进程 |
| `start_process` | 启动进程 |
| `system_info` | 系统信息 |
| `search_files` | 搜索文件 |
| `search_in_files` | 搜索文件内容 |
| `image_ocr` | 图片文字识别 |
| `translate` | 文本翻译 |
| `image_caption` | 图片分析 |

## 注意事项

1. **安全提示**：工具拥有执行Shell命令和操作文件的能力，请谨慎使用
2. **API Key**：请保管好你的API Key，不要分享给他人
3. **备份**：建议定期备份重要数据
4. **权限**：某些操作可能需要管理员权限

## 技术栈

- **GUI**: PyQt5
- **LLM**: OpenAI SDK (兼容阿里云百炼)
- **系统**: psutil, Pillow, pytesseract 等

## 许可证

MIT License

## 致谢

参考了 NanoBot 的架构设计理念。
