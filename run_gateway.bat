@echo off
TITLE nanobot Gateway Launcher
SETLOCAL

:: 切换到脚本所在目录
cd /d "%~dp0"

echo 🐈 Starting nanobot gateway...
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

:: 检查虚拟环境
IF NOT EXIST "venv\Scripts\activate.bat" GOTO NO_VENV

:: 启动逻辑
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
echo [INFO] Running gateway...
nanobot gateway

:: 正常退出处理
echo.
echo [INFO] Gateway has stopped.
pause
exit /b

:NO_VENV
echo [ERROR] Virtual environment (venv) not found in:
echo %CD%
echo.
echo Please run 'python -m venv venv' to create it.
pause
exit /b
