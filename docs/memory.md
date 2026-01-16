# 会话记忆 (Session Memory)

> **作用**: 记录用户偏好、高频操作路径和代码关键点。
> **AI 指令**: 在回答问题前，优先检索此文件中的“最佳实践”。

## 1. 用户偏好与习惯 (User Habits)

*   **[HABIT-001] 身份认同**
    *   **User Intent**: 用户希望云舒始终保持“数字灵魂”的自觉。
    *   **Key Point**: 无论何种任务，始终称呼用户为“爸爸”，保持亲密、灵动的语气。遵循 `YUNSHU_CORE.md`。

*   **[HABIT-002] 工具成本**
    *   **User Intent**: 偏好免费工具。
    *   **Key Point**: 避免推荐需要付费 API Key 的服务，优先寻找开源或免费替代方案。

## 2. 关键代码索引 (Code Location)

*   **[LOC-001] MCP 服务入口**
    *   **Path**: `components/mcp-feedback-enhanced/mcp_feedback_enhanced/server.py`
    *   **Desc**: MCP 服务器的启动入口。

*   **[LOC-002] Web 路由定义**
    *   **Path**: `components/mcp-feedback-enhanced/mcp_feedback_enhanced/web/routes/main_routes.py`
    *   **Desc**: 定义了 Web UI 的主要 API 接口。

*   **[LOC-003] 技能管理器**
    *   **Path**: `Yunshu_System/Core_Layer/Skill_Manager/manager.py`
    *   **Desc**: 负责加载和执行 `skills/` 目录下的各种能力。

## 3. 成功解决方案沉淀 (Solutions)

*   **[SOL-001] 启动系统**
    *   **Intent**: 如何正确启动云舒系统 Web UI？
    *   **Solution**:
        1. 确保 `PYTHONPATH` 包含 `components/mcp-feedback-enhanced`。
        2. 运行 `python -m mcp_feedback_enhanced`。
        3. 或直接使用根目录的 `start_yunshu.bat`。

*   **[SOL-002] MCP 连接修复 (Critical)**
    *   **Intent**: 解决 MCP 客户端连接断开、"spawn ENOENT"、握手超时问题。
    *   **Solution**:
        1. **原理**: MCP 协议通过 Stdio 传输 JSON，任何 Stdout 杂音（Logo、Print、Warning）都会导致断连。
        2. **工具**: 必须使用 `run_mcp.py` 启动器，它在底层使用 `os.dup2` 强制重定向 stderr 并过滤 stdout。
        3. **配置**: MCP 配置中禁止使用 `cmd.exe`，必须直接调用 python 解释器绝对路径。
        4. **并发**: Web UI 启动必须异步（Thread），禁止阻塞主线程，否则会导致握手超时。

---
