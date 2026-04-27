#!/usr/bin/env python3
"""
PyClaw 主程序入口
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.floating_ball import FloatingBall
from core.agent import Agent
from config.settings import Settings


def main():
    """主程序入口"""
    app = QApplication(sys.argv)
    app.setApplicationName("PyClaw")
    app.setApplicationVersion("1.0.0")

    # 设置应用字体
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)

    # 加载设置
    settings = Settings()

    # 创建智能体
    agent = Agent(settings)

    # 创建悬浮球
    floating_ball = FloatingBall(settings, agent)
    floating_ball.show()

    print("PyClaw 已启动！")
    print("悬浮球显示在屏幕右下角，可以拖动到任意位置")
    print("点击悬浮球打开对话窗口")

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
