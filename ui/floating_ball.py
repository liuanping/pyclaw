"""
悬浮球组件
"""

from PyQt5.QtWidgets import QWidget, QLabel
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt5.QtGui import QPainter, QColor, QBrush, QRadialGradient, QFont


class FloatingBall(QWidget):
    """悬浮球组件"""

    clicked = pyqtSignal()  # 点击信号

    def __init__(self, settings, agent, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.agent = agent

        # 设置窗口属性
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 配置尺寸
        self.ball_size = settings.ball_size
        self.setFixedSize(self.ball_size, self.ball_size)

        # 拖动相关
        self.dragging = False
        self.drag_position = QPoint()

        # 动画相关
        self.hover_scale = 1.0
        self.pulse_opacity = 1.0

        # 初始化位置
        self._init_position()

        # 设置定时器用于脉冲动画
        self.pulse_direction = 1
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self._update_pulse)
        self.pulse_timer.start(50)

        # 显示欢迎提示
        self._show_welcome()

    def _init_position(self):
        """初始化位置"""
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.width() - self.ball_size - 20
        y = screen.height() - self.ball_size - 100
        self.move(x, y)

    def _show_welcome(self):
        """显示欢迎提示"""
        QTimer.singleShot(1000, self._show_tooltip)

    def _show_tooltip(self):
        """显示提示"""
        pass  # 可以实现气泡提示

    def _update_pulse(self):
        """更新脉冲动画"""
        self.pulse_opacity += 0.02 * self.pulse_direction
        if self.pulse_opacity >= 1.0:
            self.pulse_opacity = 1.0
            self.pulse_direction = -1
        elif self.pulse_opacity <= 0.6:
            self.pulse_opacity = 0.6
            self.pulse_direction = 1
        self.update()

    def paintEvent(self, event):
        """绘制悬浮球"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center_x = self.width() // 2
        center_y = self.height() // 2
        radius = int(self.ball_size // 2 * self.hover_scale)

        # 绘制光晕
        gradient = QRadialGradient(center_x, center_y, radius)
        gradient.setColorAt(0, QColor(66, 133, 244, int(200 * self.pulse_opacity)))
        gradient.setColorAt(0.5, QColor(66, 133, 244, int(100 * self.pulse_opacity)))
        gradient.setColorAt(1, QColor(66, 133, 244, 0))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)

        # 绘制主球
        main_gradient = QRadialGradient(
            center_x - radius // 3, center_y - radius // 3, radius
        )
        main_gradient.setColorAt(0, QColor(100, 160, 255))
        main_gradient.setColorAt(1, QColor(40, 100, 200))
        painter.setBrush(QBrush(main_gradient))
        painter.drawEllipse(center_x - radius + 5, center_y - radius + 5, radius * 2 - 10, radius * 2 - 10)

        # 绘制图标
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Segoe UI Emoji", int(radius * 0.8))
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, "🤖")

    def enterEvent(self, event):
        """鼠标进入事件"""
        self.hover_scale = 1.1
        self.update()
        self.setCursor(Qt.PointingHandCursor)

    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.hover_scale = 1.0
        self.update()
        self.setCursor(Qt.ArrowCursor)

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.dragging and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton and self.dragging:
            self.dragging = False
            # 检查是否是点击（移动距离很小）
            if (event.globalPos() - self.drag_position - self.frameGeometry().topLeft()).manhattanLength() < 5:
                self._on_click()

    def _on_click(self):
        """点击事件处理"""
        self.clicked.emit()
        # 创建并显示主窗口
        if not hasattr(self, 'main_window') or not self.main_window.isVisible():
            from ui.main_window import MainWindow
            self.main_window = MainWindow(self.settings, self.agent)
            # 定位到悬浮球附近
            ball_pos = self.geometry().topLeft()
            self.main_window.move(ball_pos.x() - 400, ball_pos.y() - 300)
            self.main_window.show()
            self.main_window.activateWindow()
