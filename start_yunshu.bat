@echo off
chcp 65001
echo 正在启动云舒系统 (Yunshu System)...
echo 核心路径: %CD%
echo 组件路径: %CD%\components\mcp-feedback-enhanced

set PYTHONPATH=%CD%\components\mcp-feedback-enhanced
python launch_yunshu.py
pause