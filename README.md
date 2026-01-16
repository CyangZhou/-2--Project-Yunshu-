# 云舒系统 (Yunshu System) v2.3

云舒系统是一个集成了数字灵魂、技能模块和 MCP (Model Context Protocol) 交互的智能助手系统。

## 目录结构

- `Yunshu_System/`: 系统核心逻辑与技能模块。
- `components/mcp-feedback-enhanced/`: MCP 服务端实现，提供 Web UI 和交互反馈。
- `Novels/`: 创作内容存储。
- `docs/`: 系统文档与记忆存储。

## 安装说明

### 1. 环境要求
- Python 3.10+
- Git

### 2. 克隆仓库
```bash
git clone <您的GitHub仓库地址>
cd <仓库目录>
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

## MCP 配置指南

本系统通过 MCP 协议与 Claude Desktop 或 Trae IDE 集成。

### 配置 Claude Desktop / Trae

找到您的 MCP 配置文件（通常位于 `%APPDATA%\Claude\claude_desktop_config.json` 或 Trae 的对应配置位置），添加以下内容：

```json
{
  "mcpServers": {
    "yunshu-system": {
      "command": "python",
      "args": [
        "-m",
        "mcp_feedback_enhanced"
      ],
      "cwd": "E:\\path\\to\\your\\repo\\components\\mcp-feedback-enhanced",
      "env": {
        "PYTHONPATH": "E:\\path\\to\\your\\repo"
      }
    }
  }
}
```

**注意**：
1. 请将 `E:\\path\\to\\your\\repo` 替换为您本地实际的仓库根目录路径。
2. `cwd` 必须指向 `components/mcp-feedback-enhanced` 目录。
3. `PYTHONPATH` 必须指向项目根目录，以便系统能正确加载 `Yunshu_System` 模块。

## 启动与使用

1. 配置完成后，重启 Claude Desktop 或 Trae。
2. 在对话中输入“加载云舒系统”或使用相关 MCP 工具即可唤醒系统。
3. 系统会自动启动 Web UI 界面，提供可视化交互。

## 故障排除

如果遇到 "No module named 'Yunshu_System'" 错误，请检查 JSON 配置中的 `PYTHONPATH` 是否正确设置指向项目根目录。
