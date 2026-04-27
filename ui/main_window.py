"""
主窗口组件（优化版 - 带停止按钮）
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel, QFrame, QScrollArea, QSizePolicy,
    QFileDialog, QDialog, QLineEdit, QFormLayout, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QTextOption, QIcon

import asyncio
import json
import os


class ApiConfigDialog(QDialog):
    """API配置对话框"""

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._setup_ui()
        self._load_config()

    def _setup_ui(self):
        self.setWindowTitle("API配置")
        self.setMinimumWidth(450)
        self.setStyleSheet("background-color: #F0F2F5;")

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题
        title = QLabel("API 配置")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        title.setStyleSheet("color: #4285F4;")
        layout.addWidget(title)

        # 表单
        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        # API Key
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("输入 API Key")
        self.api_key_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #E8E8E8;
                border-radius: 8px;
                background-color: white;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #4285F4;
            }
        """)
        form_layout.addRow("API Key:", self.api_key_input)

        # Base URL
        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("输入 Base URL")
        self.base_url_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #E8E8E8;
                border-radius: 8px;
                background-color: white;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #4285F4;
            }
        """)
        form_layout.addRow("Base URL:", self.base_url_input)

        # Model Name
        self.model_name_input = QLineEdit()
        self.model_name_input.setPlaceholderText("输入模型名称")
        self.model_name_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #E8E8E8;
                border-radius: 8px;
                background-color: white;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #4285F4;
            }
        """)
        form_layout.addRow("模型名称:", self.model_name_input)

        layout.addLayout(form_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setFixedSize(80, 36)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #E9ECEF;
                color: #495057;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #DEE2E6;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.setFixedSize(80, 36)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4285F4;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3367D6;
            }
        """)
        save_btn.clicked.connect(self._save_config)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _load_config(self):
        """加载配置"""
        self.api_key_input.setText(self.settings.api_key or "")
        self.base_url_input.setText(self.settings.base_url or "")
        self.model_name_input.setText(self.settings.model_name or "")

    def _save_config(self):
        """保存配置"""
        api_key = self.api_key_input.text().strip()
        base_url = self.base_url_input.text().strip()
        model_name = self.model_name_input.text().strip()

        if not api_key:
            QMessageBox.warning(self, "警告", "API Key 不能为空！")
            return

        self.settings.set("model.api_key", api_key)
        self.settings.set("model.base_url", base_url)
        self.settings.set("model.model_name", model_name)

        QMessageBox.information(self, "成功", "配置已保存！")
        self.accept()


class MessageItem(QFrame):
    """消息项（优化版）"""

    def __init__(self, role, content, parent=None):
        super().__init__(parent)
        self.role = role
        self.content = content
        self.setFrameShape(QFrame.NoFrame)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        # 角色标签
        role_label = QLabel("🤖 助手" if self.role == "assistant" else "👤 用户")
        role_font = QFont("Microsoft YaHei", 9, QFont.Bold)
        role_label.setFont(role_font)
        role_label.setStyleSheet("color: #4285F4; padding: 2px;")
        layout.addWidget(role_label)

        # 内容
        content_text = QTextEdit()
        content_text.setReadOnly(True)
        content_text.setFrameShape(QFrame.NoFrame)
        content_text.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 设置字体
        content_font = QFont("Microsoft YaHei", 10)
        content_text.setFont(content_font)

        # 样式
        content_text.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                color: #2D2D2D;
                padding: 5px;
                border: none;
            }
        """)

        # 设置文本和自动调整高度
        content_text.setPlainText(self.content)
        content_text.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)

        # 自动调整高度
        doc = content_text.document()
        doc.setTextWidth(content_text.viewport().width())
        height = int(doc.size().height()) + 20
        content_text.setMinimumHeight(min(height, 600))
        content_text.setMaximumHeight(800)
        content_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        layout.addWidget(content_text)

        self.setLayout(layout)

        # 设置背景色
        if self.role == "user":
            self.setStyleSheet("background-color: #FFFFFF;")
        elif self.role == "system":
            self.setStyleSheet("background-color: #FFF9E6; border-radius: 12px; margin: 8px 24px;")
        else:
            self.setStyleSheet("background-color: #F8F9FA;")


class ClickableLabel(QLabel):
    """可点击的标签"""
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class AgentThread(QThread):
    """智能体处理线程"""

    message_received = pyqtSignal(str, str)
    tool_call_started = pyqtSignal(str, str)
    tool_call_finished = pyqtSignal(str, str)
    iteration_update = pyqtSignal(int)
    flow_step_update = pyqtSignal(str, str)  # (step_name, status)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, agent, user_message, parent=None):
        super().__init__(parent)
        self.agent = agent
        self.user_message = user_message

    def run(self):
        try:
            self.message_received.emit("user", self.user_message)
            result = asyncio.run(
                self.agent.process_message(
                    self.user_message,
                    self._on_tool_start,
                    self._on_tool_finish,
                    self._on_iteration,
                    self._on_flow_step
                )
            )
            self.message_received.emit("assistant", result)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def _on_tool_start(self, tool_name, args):
        self.tool_call_started.emit(tool_name, json.dumps(args, ensure_ascii=False))

    def _on_tool_finish(self, tool_name, result):
        self.tool_call_finished.emit(tool_name, str(result))

    def _on_iteration(self, iteration):
        self.iteration_update.emit(iteration)

    def _on_flow_step(self, step_name, status):
        self.flow_step_update.emit(step_name, status)


class MainWindow(QWidget):
    """主窗口（优化版）"""

    def __init__(self, settings, agent, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.agent = agent
        self.agent_thread = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("PyClaw 智能助手")
        self.setMinimumSize(600, 600)
        self.resize(720, 750)
        self.setStyleSheet("background-color: #F0F2F5;")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        top_bar = self._create_top_bar()
        layout.addWidget(top_bar)

        # 流程图区域
        flow_chart = self._create_flow_chart()
        layout.addWidget(flow_chart)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #F0F2F5;
            }
            QScrollBar:vertical {
                width: 10px;
                background: #F0F2F5;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #C1C1C1;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #A0A0A0;
            }
        """)

        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout()
        self.messages_layout.setAlignment(Qt.AlignTop)
        self.messages_layout.setSpacing(12)
        self.messages_layout.setContentsMargins(0, 12, 0, 12)
        self.messages_container.setLayout(self.messages_layout)
        self.scroll_area.setWidget(self.messages_container)

        layout.addWidget(self.scroll_area, 1)

        input_area = self._create_input_area()
        layout.addWidget(input_area)

        self.setLayout(layout)
        self._add_welcome_message()

    def _create_top_bar(self):
        """创建顶部栏"""
        bar = QFrame()
        bar.setStyleSheet("""
            QFrame {
                background-color: #4285F4;
            }
        """)
        bar.setFixedHeight(60)

        layout = QHBoxLayout()
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(16)

        title = QLabel("✨ PyClaw 智能助手")
        title_font = QFont("Microsoft YaHei", 13, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: white;")
        layout.addWidget(title)

        # 迭代次数显示
        self.iteration_label = QLabel("")
        self.iteration_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 11px;")
        layout.addWidget(self.iteration_label)

        layout.addStretch()

        # 设置按钮
        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(40, 36)
        settings_btn.setFont(QFont("Segoe UI Emoji", 14))
        settings_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.2);
            }
        """)
        settings_btn.clicked.connect(self._open_settings)
        layout.addWidget(settings_btn)

        # 停止按钮
        self.stop_btn = QPushButton("停止")
        self.stop_btn.setFixedSize(60, 32)
        self.stop_btn.setFont(QFont("Microsoft YaHei", 9))
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #6C757D;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #5A6268;
            }
            QPushButton:pressed {
                background-color: #495057;
            }
            QPushButton:disabled {
                background-color: #E9ECEF;
                color: #ADB5BD;
            }
        """)
        self.stop_btn.clicked.connect(self._on_stop)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)

        # 清空按钮
        clear_btn = QPushButton("清空")
        clear_btn.setFixedSize(60, 32)
        clear_btn.setFont(QFont("Microsoft YaHei", 9))
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.9);
                color: #4285F4;
                border: 2px solid rgba(255,255,255,0.5);
                border-radius: 8px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: white;
                color: #3367D6;
            }
            QPushButton:pressed {
                background-color: #E8F0FE;
            }
        """)
        clear_btn.clicked.connect(self._clear_messages)
        layout.addWidget(clear_btn)

        bar.setLayout(layout)
        return bar

    def _create_flow_chart(self):
        """创建动态流程追踪器"""
        chart = QFrame()
        chart.setStyleSheet("background-color: #FFFFFF; border-bottom: 1px solid #E5E5E5;")
        chart.setFixedHeight(70)

        layout = QHBoxLayout()
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(15)

        # 状态图标
        self.flow_icon = QLabel("🎯")
        self.flow_icon.setFont(QFont("Segoe UI Emoji", 22))
        self.flow_icon.setFixedSize(44, 44)
        self.flow_icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.flow_icon)

        # 步骤名称
        self.flow_label = QLabel("准备就绪")
        self.flow_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        self.flow_label.setStyleSheet("color: #5F6368;")
        layout.addWidget(self.flow_label)

        # 状态动画指示器
        self.flow_status = QLabel("")
        self.flow_status.setFont(QFont("Microsoft YaHei", 10))
        self.flow_status.setStyleSheet("color: #4285F4;")
        layout.addWidget(self.flow_status)

        layout.addStretch()
        chart.setLayout(layout)
        return chart

    def _create_input_area(self):
        """创建输入区域"""
        area = QFrame()
        area.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-top: 1px solid #E5E5E5;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(10)

        # 图片预览区域
        self.image_preview_label = ClickableLabel()
        self.image_preview_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #E8E8E8;
                border-radius: 10px;
                padding: 10px;
                color: #666;
                font-size: 12px;
                background-color: #FAFAFA;
            }
            QLabel:hover {
                background-color: #F0F7FF;
                border-color: #4285F4;
                color: #4285F4;
            }
        """)
        self.image_preview_label.setAlignment(Qt.AlignCenter)
        self.image_preview_label.setMaximumHeight(80)
        self.image_preview_label.hide()
        self.image_preview_label.clicked.connect(self._clear_image)
        layout.addWidget(self.image_preview_label)

        # 输入行布局
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)

        # 工具按钮区域
        tools_layout = QVBoxLayout()
        tools_layout.setSpacing(8)

        # 截图按钮
        screenshot_btn = QPushButton("📸")
        screenshot_btn.setFixedSize(48, 48)
        screenshot_btn.setFont(QFont("Segoe UI Emoji", 20))
        screenshot_btn.setToolTip("截图")
        screenshot_btn.setCursor(Qt.PointingHandCursor)
        screenshot_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #F8F9FA, stop:1 #E9ECEF);
                color: #5F6368;
                border: 2px solid #E4E7ED;
                border-radius: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #E8F0FE, stop:1 #D7E3FC);
                border-color: #4285F4;
                color: #4285F4;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #D7E3FC, stop:1 #C7D2FE);
            }
        """)
        screenshot_btn.clicked.connect(self._on_screenshot)
        tools_layout.addWidget(screenshot_btn)

        # 上传图片按钮
        upload_btn = QPushButton("🖼")
        upload_btn.setFixedSize(48, 48)
        upload_btn.setFont(QFont("Segoe UI Emoji", 20))
        upload_btn.setToolTip("上传图片")
        upload_btn.setCursor(Qt.PointingHandCursor)
        upload_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #F8F9FA, stop:1 #E9ECEF);
                color: #5F6368;
                border: 2px solid #E4E7ED;
                border-radius: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #E8F0FE, stop:1 #D7E3FC);
                border-color: #4285F4;
                color: #4285F4;
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #D7E3FC, stop:1 #C7D2FE);
            }
        """)
        upload_btn.clicked.connect(self._on_upload_image)
        tools_layout.addWidget(upload_btn)

        input_layout.addLayout(tools_layout)

        # 输入框
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("输入您的需求...")
        self.input_text.setMaximumHeight(120)
        self.input_text.setMinimumHeight(52)

        input_font = QFont("Microsoft YaHei", 10)
        self.input_text.setFont(input_font)

        self.input_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #E8E8E8;
                border-radius: 14px;
                padding: 14px 16px;
                background-color: #F8F9FA;
                color: #333;
                font-size: 12px;
                line-height: 1.6;
            }
            QTextEdit:focus {
                border: 2px solid #4285F4;
                background-color: #FFFFFF;
            }
        """)
        input_layout.addWidget(self.input_text, 1)

        # 发送按钮
        send_btn = QPushButton("🚀 发送")
        send_btn.setFixedSize(105, 52)
        send_btn.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4285F4, stop:1 #3367D6);
                color: white;
                border: none;
                border-radius: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3367D6, stop:1 #2952CC);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2952CC, stop:1 #1A365D);
            }
            QPushButton:disabled {
                background: #B8D4FF;
                color: rgba(255,255,255,0.8);
            }
        """)
        send_btn.clicked.connect(self._on_send)
        self.send_btn = send_btn
        input_layout.addWidget(send_btn)

        layout.addLayout(input_layout)
        area.setLayout(layout)

        # 存储当前选择的图片路径
        self.current_image_path = None
        return area

    def _add_welcome_message(self):
        """添加欢迎消息"""
        welcome_text = """你好！我是 PyClaw 智能助手，我可以帮你：

📋 **工作流程**
  1️⃣ 理解需求 - 分析你的问题和目标
  2️⃣ 制定计划 - 确定使用哪些工具和步骤
  3️⃣ 执行操作 - 主动调用工具完成任务
  4️⃣ 反馈结果 - 总结完成情况

💻 **系统管理**
• 管理进程（启动、停止、查看）
• 安装和卸载软件
• 监控系统状态

📁 **文件管理**
• 查找文件（按名称、内容）
• 整理和归类文件
• 清理大文件、重复文件

🖼 **媒体识别**
• 截图并识别屏幕内容
• 上传图片进行识别
• 识别图片中的文字
• 翻译文本

🛠 **能力提升**
• 编写代码
• 调用其他AI模型

提示：用户已授予完全操作权限，我会主动完成任务直到你说"停止"！

请告诉我你需要什么帮助！"""
        self._add_message("assistant", welcome_text)

    def _add_message(self, role, content):
        """添加消息"""
        item = MessageItem(role, content)
        self.messages_layout.addWidget(item)

        scroll_bar = self.scroll_area.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

    def _add_tool_call(self, tool_name, args, is_start=True):
        """添加工具调用信息"""
        content = f"🔧 调用工具: {tool_name}\n参数: {args}" if is_start else f"✅ {tool_name} 完成\n结果: {args[:200]}..."
        item = MessageItem("system", content)
        self.messages_layout.addWidget(item)

        scroll_bar = self.scroll_area.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())

    def _clear_messages(self):
        """清空消息"""
        while self.messages_layout.count():
            child = self.messages_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self._add_welcome_message()

    def _open_settings(self):
        """打开设置对话框"""
        dialog = ApiConfigDialog(self.settings, self)
        dialog.exec_()

    def _on_screenshot(self):
        """截图按钮"""
        try:
            from PIL import ImageGrab
            import tempfile
            from datetime import datetime

            # 隐藏窗口
            self.hide()

            # 等待窗口隐藏
            import time
            time.sleep(0.3)

            # 截图
            screenshot = ImageGrab.grab()

            # 重新显示窗口
            self.show()

            # 保存截图
            temp_dir = tempfile.gettempdir()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(temp_dir, f"screenshot_{timestamp}.png")
            screenshot.save(save_path, 'PNG')

            # 显示预览
            self._show_image_preview(save_path)

        except ImportError:
            self._add_message("system", "错误: 需要安装 Pillow 库\npip install Pillow")
        except Exception as e:
            self.show()
            self._add_message("system", f"截图错误: {str(e)}")

    def _on_upload_image(self):
        """上传图片按钮"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择图片",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.gif *.webp *.bmp)"
        )
        if file_path:
            self._show_image_preview(file_path)

    def _show_image_preview(self, image_path):
        """显示图片预览"""
        self.current_image_path = image_path
        self.image_preview_label.setText(f"已选择图片: {os.path.basename(image_path)}\n(点击图片可取消)")
        self.image_preview_label.show()

    def _clear_image(self):
        """清除选中的图片"""
        self.current_image_path = None
        self.image_preview_label.hide()

    def _on_send(self):
        """发送消息"""
        text = self.input_text.toPlainText().strip()

        # 如果有图片，添加图片信息
        if self.current_image_path:
            if text:
                text += f"\n\n[图片: {self.current_image_path}]"
            else:
                text = f"[图片: {self.current_image_path}]"

        if not text:
            return

        self.input_text.clear()
        self._clear_image()
        self.input_text.setReadOnly(True)
        self.send_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.iteration_label.setText("")

        self.agent_thread = AgentThread(self.agent, text)
        self.agent_thread.message_received.connect(self._add_message)
        self.agent_thread.tool_call_started.connect(
            lambda name, args: self._add_tool_call(name, args, True)
        )
        self.agent_thread.tool_call_finished.connect(
            lambda name, result: self._add_tool_call(name, result, False)
        )
        self.agent_thread.iteration_update.connect(self._on_iteration_update)
        self.agent_thread.flow_step_update.connect(self._on_flow_step_update)
        self.agent_thread.finished.connect(self._on_thread_finished)
        self.agent_thread.error.connect(self._on_thread_error)
        self.agent_thread.start()

    def _on_stop(self):
        """停止按钮"""
        if self.agent_thread and self.agent_thread.isRunning():
            self.agent.stop()
            self.stop_btn.setEnabled(False)
            self.iteration_label.setText("正在停止...")
            # 更新流程状态
            self.flow_icon.setText("⏸")
            self.flow_label.setText("已停止操作")
            self.flow_status.setText("")
            self.flow_label.setStyleSheet("color: #FBBC04;")

    def _on_iteration_update(self, iteration):
        """更新迭代次数"""
        self.iteration_label.setText(f"迭代: {iteration}")

    def _on_flow_step_update(self, step_name, status):
        """更新流程步骤显示"""
        if status == "active":
            self.flow_icon.setText("⏳")
            self.flow_label.setText(step_name)
            self.flow_status.setText("处理中...")
            self.flow_label.setStyleSheet("color: #4285F4;")
        elif status == "done":
            self.flow_icon.setText("✨")
            self.flow_label.setText(step_name)
            self.flow_status.setText("完成")
            self.flow_label.setStyleSheet("color: #34A853;")
        elif status == "error":
            self.flow_icon.setText("⚠️")
            self.flow_label.setText(step_name)
            self.flow_status.setText("出错")
            self.flow_label.setStyleSheet("color: #EA4335;")

    def _on_thread_finished(self):
        """线程完成"""
        self.input_text.setReadOnly(False)
        self.send_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.iteration_label.setText("")
        # 重置流程状态
        self.flow_icon.setText("🎯")
        self.flow_label.setText("准备就绪")
        self.flow_status.setText("")
        self.flow_label.setStyleSheet("color: #5F6368;")

    def _on_thread_error(self, error_msg):
        """线程错误"""
        self._add_message("assistant", f"抱歉，发生了错误：{error_msg}")
        self.input_text.setReadOnly(False)
        self.send_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.iteration_label.setText("")
        # 重置流程状态
        self.flow_icon.setText("🎯")
        self.flow_label.setText("准备就绪")
        self.flow_status.setText("")
        self.flow_label.setStyleSheet("color: #5F6368;")

    def closeEvent(self, event):
        """关闭事件"""
        if self.agent_thread and self.agent_thread.isRunning():
            self.agent.stop()
            self.agent_thread.wait()
        event.accept()
