---
name: skill_factory
description: "Meta-skill for generating new standard skill modules. Context-aware: analyzes user requirements to select appropriate templates (Basic/Generator/Data) and automatically populates metadata (name, tags, description) for the new skill."
tags: ["meta", "generator", "scaffold", "factory", "dev-tool"]
version: "2.0.0"
---

# 🏭 技能工厂 (Skill Factory)

> **核心使命**：标准化生产，让创意快速落地。这是云舒系统的“母体”技能，负责孵化新的能力模块。

## 1. 核心功能 (Core Capabilities)

### 1.1 智能脚手架 (Smart Scaffolding)
*   **自动目录结构**：在 `skills/` 下自动创建符合 TRAE 规范的文件夹结构。
*   **标准化元数据**：自动生成包含 `name`, `description`, `tags`, `version` 的 `SKILL.md`。
*   **依赖注入**：根据技能类型（如 Web Search 或 Python Script），自动添加 `package.json` 或 `requirements.txt` 模板。

### 1.2 模板类型 (Templates)

| 模板ID | 适用场景 | 包含文件 |
| :--- | :--- | :--- |
| **Basic** | 通用简单任务 | `SKILL.md` |
| **TypeScript** | Web SDK 集成 (Search, VLM) | `SKILL.md`, `scripts/*.ts`, `package.json` |
| **Python** | 本地数据处理 (PDF, Excel) | `SKILL.md`, `scripts/*.py`, `requirements.txt` |
| **Agentic** | 复杂多步任务 (Novel Expert) | `SKILL.md`, `guides/*.md`, `prompts/*.json` |

## 2. 上下文参数化 (Context Parameters)

本技能支持以下动态参数，可通过对话上下文自动填充：

*   `{{skill_id}}`: 技能的唯一标识符（英文，如 `code_reviewer`）。
*   `{{skill_name}}`: 技能的显示名称（如 `代码审查专家`）。
*   `{{skill_type}}`: 模板类型（`basic` | `typescript` | `python` | `agentic`）。
*   `{{description}}`: 技能的简短描述，用于生成 Frontmatter。
*   `{{tags}}`: 技能标签列表，用于上下文触发。

## 3. 交互流程 (Workflow)

1.  **需求分析**：用户描述想要创建的技能（例如：“我想做一个能自动分析 Excel 的技能”）。
2.  **参数推断**：
    *   `skill_id`: `excel_analyst`
    *   `skill_type`: `python`
    *   `tags`: `['excel', 'data', 'analysis', 'python']`
3.  **确认与生成**：向用户确认参数后，调用文件系统工具创建技能包。
4.  **热加载**：提示用户刷新 Skills 列表。

## 4. 最佳实践 (Best Practices)

*   **命名规范**：`skill_id` 必须是 `snake_case` 或 `kebab-case`。
*   **原子化**：一个技能只做一件事，保持 `SKILL.md` 清晰专注。
*   **文档优先**：生成的 `SKILL.md` 必须包含详细的 `Overview`, `Usage`, 和 `Reference` 章节。
