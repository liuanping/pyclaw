@echo off
chcp 65001 >nul
echo ====================================
echo PyClaw - 智能电脑助手
echo ====================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查虚拟环境
if not exist "venv" (
    echo [信息] 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 安装依赖
echo [信息] 检查依赖...
pip install -q -r requirements.txt

echo.
echo [信息] 启动 PyClaw...
echo.
python main.py

pause
