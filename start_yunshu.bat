@echo off
:: =======================================================
:: 云舒系统 MCP 启动脚本 (Yunshu System Launcher)
:: =======================================================

:: 1. 设置控制台编码 (关键)
chcp 65001 >nul

:: 2. 设置项目根目录
set "PROJECT_ROOT=%~dp0"

:: 3. 设置 PYTHONPATH
set "PYTHONPATH=%PROJECT_ROOT%components\mcp-feedback-enhanced;%PYTHONPATH%"

:: 4. 强力屏蔽警告模式
:: 使用 -W ignore 命令行参数比环境变量更可靠
:: 2> mcp_stderr.log 将所有错误/日志输出重定向到文件，确保 stdout 只有纯净的 MCP JSON 数据
python -W ignore -m mcp_feedback_enhanced.server 2> "%PROJECT_ROOT%mcp_stderr.log"
