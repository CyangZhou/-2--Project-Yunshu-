from typing import Dict, Any, List, Optional
import os
from pathlib import Path

class SkillFactory:
    """
    云舒系统技能工厂
    
    负责自动生成新的技能模组结构。
    """
    
    def __init__(self, workspace_root: str):
        """
        初始化
        Args:
            workspace_root: 指向 skills/ 目录 (因为 SKILL.md 中配置为 ../)
        """
        self.skills_dir = Path(workspace_root).resolve()
    
    def execute(self, params: Dict[str, Any]) -> str:
        """
        执行生成逻辑
        """
        skill_id = params.get("skill_id", "").strip()
        display_name = params.get("display_name", "").strip()
        description = params.get("description", "").strip()
        template_type = params.get("template_type", "basic")
        
        if not skill_id or not display_name:
            return "❌ 错误: 技能ID和显示名称不能为空。"
        
        # 简单的 ID 校验
        if not skill_id.replace("_", "").isalnum():
            return "❌ 错误: 技能ID只能包含字母、数字和下划线。"
        
        target_dir = self.skills_dir / skill_id
        
        if target_dir.exists():
            return f"❌ 错误: 技能目录 {skill_id} 已存在。"
        
        try:
            target_dir.mkdir(parents=True)
            
            # 0. Determine Template Config
            config = self._get_template_config(template_type)
            class_name = config["class_name"]
            
            # 1. 生成 SKILL.md
            self._create_skill_md(target_dir, skill_id, display_name, description, config)
            
            # 2. 生成 tools.py
            self._create_tools_py(target_dir, config)
            
            # 3. 生成 __init__.py
            self._create_init_py(target_dir, class_name)
            
            return f"✅ 技能 '{display_name}' ({skill_id}) 已成功创建！\n[模板: {template_type}]\n\n请刷新页面查看新卡片，并前往 {target_dir} 编写具体逻辑。"
        
        except Exception as e:
            return f"❌ 创建失败: {str(e)}"

    def _get_template_config(self, template_type: str) -> Dict:
        if template_type == "generator":
            return {
                "class_name": "ContentGenerator",
                "input_yaml": """  - name: topic
    type: text
    label: 主题
    required: true
    default: ""
  - name: filename
    type: text
    label: 文件名
    placeholder: "output.md"
    required: true""",
                "execute_code": """        topic = params.get("topic", "Unknown Topic")
        filename = params.get("filename", "output.md")
        
        # Generate content logic here
        content = f"# {topic}\\n\\nGenerated content..."
        
        output_path = self.workspace_root / filename
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return f"✅ 内容生成成功: {output_path}" """
            }
        elif template_type == "data_process":
            return {
                "class_name": "DataProcessor",
                "input_yaml": """  - name: input_file
    type: text
    label: 输入文件路径
    required: true
  - name: operation
    type: select
    label: 操作类型
    options: [{label: "分析", value: "analyze"}, {label: "清洗", value: "clean"}]
    default: "analyze" """,
                "execute_code": """        input_file = params.get("input_file", "")
        operation = params.get("operation", "analyze")
        
        if not input_file:
            return "❌ 请提供输入文件"
            
        # Process logic here
        return f"✅ 数据处理完成: {operation} on {input_file}" """
            }
        else: # basic
            return {
                "class_name": "SkillTools",
                "input_yaml": """  - name: instruction
    type: text
    label: 指令
    placeholder: "请输入您的指令..."
    required: true
    default: "" """,
                "execute_code": """        instruction = params.get("instruction", "")
        
        # 在这里编写您的业务逻辑
        # ...
        
        return f"技能执行成功: {instruction}" """
            }

    def _create_skill_md(self, target_dir: Path, skill_id: str, name: str, desc: str, config: Dict):
        content = f"""---
id: {skill_id}
name: {name}
version: 1.0.0
author: Yunshu
description: {desc}
icon: 🧩
color: "#4CAF50"
tags: [custom]
entry_point: tools.{config['class_name']}
workspace_root: ../../../Data
input:
{config['input_yaml']}
---

# {name}

{desc}

## 使用说明
在这里编写您的技能说明文档...
"""
        with open(target_dir / "SKILL.md", "w", encoding="utf-8") as f:
            f.write(content)

    def _create_tools_py(self, target_dir: Path, config: Dict):
        content = f"""from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

# Configure logger
logger = logging.getLogger(__name__)

class {config['class_name']}:
    \"\"\"
    技能实现类
    \"\"\"
    
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)
        self._ensure_workspace()

    def _ensure_workspace(self):
        if not self.workspace_root.exists():
            self.workspace_root.mkdir(parents=True, exist_ok=True)

    def execute(self, params: Dict[str, Any]) -> str:
        \"\"\"
        执行入口
        \"\"\"
        try:
{config['execute_code']}
        except Exception as e:
            logger.error(f"Execution failed: {{e}}")
            return f"❌ 执行出错: {{str(e)}}"
"""
        with open(target_dir / "tools.py", "w", encoding="utf-8") as f:
            f.write(content)

    def _create_init_py(self, target_dir: Path, class_name: str):
        content = f"""from .tools import {class_name}

__all__ = ["{class_name}"]
"""
        with open(target_dir / "__init__.py", "w", encoding="utf-8") as f:
            f.write(content)
