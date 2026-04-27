"""
进程管理工具
"""

import psutil
import os
import subprocess
import glob
import shutil
from typing import Dict, Any, List, Optional
from pathlib import Path
from .base import Tool


class ListProcessesTool(Tool):
    """列出进程工具"""

    @property
    def name(self) -> str:
        return "list_processes"

    @property
    def description(self) -> str:
        return "列出正在运行的进程（返回前50个，按内存使用排序）"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "name_filter": {
                    "type": "string",
                    "description": "按名称过滤进程（可选）"
                }
            }
        }

    async def execute(self, name_filter: str = None) -> str:
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent']):
                try:
                    if name_filter and name_filter.lower() not in proc.info['name'].lower():
                        continue

                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'memory_mb': proc.info['memory_info'].rss / 1024 / 1024,
                        'cpu_percent': proc.info['cpu_percent']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # 按内存排序
            processes.sort(key=lambda x: x['memory_mb'], reverse=True)
            processes = processes[:50]

            result = ["PID\t名称\t\t内存(MB)\tCPU%"]
            result.append("-" * 60)
            for proc in processes:
                result.append(f"{proc['pid']}\t{proc['name'][:15]:15}\t{proc['memory_mb']:.1f}\t{proc['cpu_percent']}")

            return "\n".join(result)
        except Exception as e:
            return f"列出进程错误: {str(e)}"


class KillProcessTool(Tool):
    """结束进程工具"""

    @property
    def name(self) -> str:
        return "kill_process"

    @property
    def description(self) -> str:
        return "结束指定的进程"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pid": {
                    "type": "integer",
                    "description": "进程ID"
                },
                "name": {
                    "type": "string",
                    "description": "进程名称（如果提供pid则忽略此项）"
                }
            }
        }

    async def execute(self, pid: int = None, name: str = None) -> str:
        try:
            if pid:
                proc = psutil.Process(pid)
                proc.terminate()
                return f"已结束进程: PID={pid}, 名称={proc.name()}"
            elif name:
                killed = []
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if name.lower() in proc.info['name'].lower():
                            proc.terminate()
                            killed.append(f"{proc.info['pid']}: {proc.info['name']}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                if killed:
                    return f"已结束进程:\n" + "\n".join(killed)
                else:
                    return f"未找到名称包含 '{name}' 的进程"
            else:
                return "错误: 必须提供 pid 或 name 参数"
        except Exception as e:
            return f"结束进程错误: {str(e)}"


class StartProcessTool(Tool):
    """启动进程工具"""

    @property
    def name(self) -> str:
        return "start_process"

    @property
    def description(self) -> str:
        return "启动新的进程或应用程序（支持应用名称和命令）"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "要执行的命令或应用名称"
                },
                "detached": {
                    "type": "boolean",
                    "description": "是否分离进程（后台运行），默认为true"
                },
                "is_app_name": {
                    "type": "boolean",
                    "description": "是否为应用名称（自动搜索），默认为false"
                }
            },
            "required": ["command"]
        }

    async def execute(self, command: str, detached: bool = True, is_app_name: bool = False) -> str:
        try:
            # 如果是应用名称，先搜索
            if is_app_name or not (os.path.exists(command) or ' ' in command or command.endswith('.exe')):
                app_path = self._find_app(command)
                if app_path:
                    command = app_path
                else:
                    # 尝试直接用 start 命令启动（Windows）
                    if os.name == 'nt':
                        return self._start_windows_app(command)

            if os.name == 'nt':  # Windows
                return self._start_windows_process(command, detached)
            else:  # Linux/Mac
                return self._start_linux_process(command, detached)

        except Exception as e:
            return f"启动进程错误: {str(e)}"

    def _find_app(self, app_name: str) -> Optional[str]:
        """搜索应用程序"""
        app_name_lower = app_name.lower()

        # Windows 常见安装位置
        if os.name == 'nt':
            search_paths = [
                os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), '*'),
                os.path.join(os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'), '*'),
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', '*'),
            ]

            # 常见的应用目录名称
            app_dirs = []
            for base_path in search_paths:
                try:
                    app_dirs.extend(glob.glob(base_path))
                except:
                    pass

            # 在每个应用目录中查找exe
            for app_dir in app_dirs:
                dir_name = os.path.basename(app_dir).lower()
                if app_name_lower in dir_name:
                    # 查找此目录下的exe
                    exes = glob.glob(os.path.join(app_dir, '*.exe'))
                    if exes:
                        # 优先选择与目录名匹配的exe
                        for exe in exes:
                            exe_name = os.path.basename(exe).lower()
                            if app_name_lower in exe_name:
                                return exe
                        return exes[0]

            # 直接在 PATH 中查找
            app_exe = shutil.which(app_name)
            if app_exe:
                return app_exe

            # 尝试 .exe 后缀
            if not app_name.endswith('.exe'):
                app_exe = shutil.which(app_name + '.exe')
                if app_exe:
                    return app_exe

        # Linux/Mac
        else:
            app_path = shutil.which(app_name)
            if app_path:
                return app_path

        return None

    def _start_windows_app(self, app_name: str) -> str:
        """使用Windows start命令启动应用"""
        try:
            # 使用 os.startfile
            try:
                os.startfile(app_name)
                return f"已尝试启动应用: {app_name}"
            except:
                pass

            # 使用 start 命令
            subprocess.Popen(f'start "" "{app_name}"', shell=True)
            return f"已尝试启动应用: {app_name}"
        except Exception as e:
            return f"启动应用失败: {str(e)}\n请尝试提供完整路径，或者使用 'find_app' 工具搜索应用。"

    def _start_windows_process(self, command: str, detached: bool) -> str:
        """启动Windows进程"""
        try:
            # 如果是exe文件，直接用ShellExecute打开
            if command.endswith('.exe') and os.path.exists(command):
                os.startfile(command)
                return f"已启动应用: {command}"

            # 使用 subprocess.Popen
            if detached:
                subprocess.Popen(
                    command,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    shell=True
                )
            else:
                subprocess.Popen(command, shell=True)

            return f"已启动进程: {command}"
        except Exception as e:
            # 尝试用 start 命令
            try:
                subprocess.Popen(f'start "" {command}', shell=True)
                return f"已启动进程: {command}"
            except Exception as e2:
                return f"启动进程错误: {str(e)}"

    def _start_linux_process(self, command: str, detached: bool) -> str:
        """启动Linux/Mac进程"""
        if detached:
            subprocess.Popen(f"{command} &", shell=True)
        else:
            subprocess.Popen(command, shell=True)
        return f"已启动进程: {command}"


class SystemInfoTool(Tool):
    """系统信息工具"""

    @property
    def name(self) -> str:
        return "system_info"

    @property
    def description(self) -> str:
        return "获取系统信息（CPU、内存、磁盘等）"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {}
        }

    async def execute(self) -> str:
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            # Windows 和 Linux 的磁盘路径不同
            if os.name == 'nt':
                disk = psutil.disk_usage('C:\\')
            else:
                disk = psutil.disk_usage('/')

            result = ["=== 系统信息 ==="]
            result.append(f"CPU使用率: {cpu_percent}%")
            result.append(f"内存: {memory.percent}% 已使用 ({memory.used // 1024 // 1024} MB / {memory.total // 1024 // 1024} MB)")
            result.append(f"磁盘: {disk.percent}% 已使用 ({disk.used // 1024 // 1024 // 1024} GB / {disk.total // 1024 // 1024 // 1024} GB)")

            return "\n".join(result)
        except Exception as e:
            return f"获取系统信息错误: {str(e)}"


class FindAppTool(Tool):
    """搜索已安装应用工具"""

    @property
    def name(self) -> str:
        return "find_app"

    @property
    def description(self) -> str:
        return "搜索已安装的应用程序"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "应用名称（关键词）"
                },
                "search_all": {
                    "type": "boolean",
                    "description": "是否搜索所有位置（较慢），默认false"
                }
            },
            "required": ["app_name"]
        }

    async def execute(self, app_name: str, search_all: bool = False) -> str:
        try:
            app_name_lower = app_name.lower()
            found_apps = []

            if os.name == 'nt':  # Windows
                found_apps = self._search_windows_apps(app_name_lower, search_all)
            else:
                found_apps = self._search_linux_apps(app_name_lower)

            if found_apps:
                result = [f"找到 {len(found_apps)} 个应用:"]
                for i, app in enumerate(found_apps[:10], 1):
                    result.append(f"{i}. {app}")
                if len(found_apps) > 10:
                    result.append(f"... 还有 {len(found_apps) - 10} 个")
                return "\n".join(result)
            else:
                return f"未找到包含 '{app_name}' 的应用。\n建议：\n1. 尝试更简短的关键词\n2. 使用 start_process 直接输入完整路径\n3. 检查应用是否已正确安装"

        except Exception as e:
            return f"搜索应用错误: {str(e)}"

    def _search_windows_apps(self, app_name_lower: str, search_all: bool) -> List[str]:
        """搜索Windows应用"""
        found_apps = []

        # 1. 搜索桌面和开始菜单快捷方式
        shortcut_paths = [
            os.path.join(os.environ.get('PUBLIC', ''), 'Desktop'),
            os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop'),
            os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Windows', 'Start Menu', 'Programs'),
            os.path.join(os.environ.get('PROGRAMDATA', ''), 'Microsoft', 'Windows', 'Start Menu', 'Programs'),
        ]

        for shortcut_path in shortcut_paths:
            if os.path.exists(shortcut_path):
                try:
                    for ext in ['*.lnk', '*.url']:
                        shortcuts = glob.glob(os.path.join(shortcut_path, '**', ext), recursive=True)
                        for sc in shortcuts:
                            sc_name = os.path.basename(sc).lower()
                            if app_name_lower in sc_name:
                                found_apps.append(sc)
                except:
                    pass

        # 2. 搜索 Program Files
        if search_all or not found_apps:
            search_paths = [
                os.environ.get('PROGRAMFILES', 'C:\\Program Files'),
                os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)'),
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs'),
            ]

            for base_path in search_paths:
                if os.path.exists(base_path):
                    try:
                        # 查找包含关键词的目录
                        dirs = [d for d in os.listdir(base_path) if app_name_lower in d.lower()]
                        for d in dirs:
                            dir_path = os.path.join(base_path, d)
                            if os.path.isdir(dir_path):
                                # 查找该目录下的exe
                                exes = glob.glob(os.path.join(dir_path, '*.exe'))
                                for exe in exes:
                                    exe_name = os.path.basename(exe).lower()
                                    # 优先显示名称匹配的
                                    if app_name_lower in exe_name:
                                        found_apps.insert(0, exe)
                                    else:
                                        found_apps.append(exe)
                    except:
                        pass

        # 3. 搜索 PATH
        try:
            exe_name = app_name_lower if app_name_lower.endswith('.exe') else app_name_lower + '.exe'
            in_path = shutil.which(exe_name)
            if in_path and in_path not in found_apps:
                found_apps.insert(0, in_path)
        except:
            pass

        return list(set(found_apps))  # 去重

    def _search_linux_apps(self, app_name_lower: str) -> List[str]:
        """搜索Linux应用"""
        found_apps = []

        # 搜索 PATH
        in_path = shutil.which(app_name_lower)
        if in_path:
            found_apps.append(in_path)

        # 搜索 .desktop 文件
        desktop_paths = [
            '/usr/share/applications',
            os.path.join(os.environ.get('HOME', ''), '.local', 'share', 'applications'),
        ]

        for dp in desktop_paths:
            if os.path.exists(dp):
                try:
                    desktop_files = glob.glob(os.path.join(dp, '*.desktop'))
                    for df in desktop_files:
                        try:
                            with open(df, 'r', encoding='utf-8', errors='replace') as f:
                                content = f.read()
                                if app_name_lower in content.lower():
                                    found_apps.append(df)
                        except:
                            pass
                except:
                    pass

        return found_apps


class LaunchAppTool(Tool):
    """启动应用工具（专门用于启动应用）"""

    @property
    def name(self) -> str:
        return "launch_app"

    @property
    def description(self) -> str:
        return "启动已安装的应用程序（自动搜索应用）"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "应用名称（例如：豆包、微信、chrome）"
                },
                "app_path": {
                    "type": "string",
                    "description": "应用完整路径（可选，如果知道路径直接提供）"
                }
            },
            "required": ["app_name"]
        }

    async def execute(self, app_name: str, app_path: str = None) -> str:
        try:
            # 如果提供了路径，直接使用
            if app_path and os.path.exists(app_path):
                return self._launch(app_path)

            # 先尝试直接启动（Windows商店应用等）
            if os.name == 'nt':
                try:
                    os.startfile(app_name)
                    return f"已尝试启动应用: {app_name}"
                except:
                    pass

            # 搜索应用
            finder = FindAppTool()
            search_result = await finder.execute(app_name)

            if "找到" in search_result and "个应用" in search_result:
                # 解析搜索结果，获取第一个应用
                lines = search_result.split('\n')
                if len(lines) > 1:
                    # 提取第一个应用路径
                    first_app = lines[1]
                    if '. ' in first_app:
                        first_app = first_app.split('. ', 1)[1]

                    if os.path.exists(first_app):
                        return self._launch(first_app)

            # 尝试直接用命令启动
            try:
                if os.name == 'nt':
                    subprocess.Popen(f'start "" "{app_name}"', shell=True)
                else:
                    subprocess.Popen(app_name, shell=True)
                return f"已尝试启动应用: {app_name}"
            except:
                pass

            return f"无法找到或启动应用: {app_name}\n\n搜索结果:\n{search_result}\n\n建议：\n1. 提供完整的应用路径\n2. 尝试更精确的应用名称\n3. 使用 find_app 工具先搜索应用"

        except Exception as e:
            return f"启动应用错误: {str(e)}"

    def _launch(self, path: str) -> str:
        """启动应用"""
        if os.name == 'nt':
            if path.endswith('.lnk') or path.endswith('.url'):
                os.startfile(path)
            elif path.endswith('.exe'):
                os.startfile(path)
            else:
                subprocess.Popen(f'"{path}"', shell=True)
        else:
            if path.endswith('.desktop'):
                subprocess.Popen(['xdg-open', path])
            else:
                subprocess.Popen(path)

        return f"已启动应用: {path}"
