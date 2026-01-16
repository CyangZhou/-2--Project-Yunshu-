import re
import sys
import os
from typing import Dict, Any
from Yunshu_System.Protocol_Layer.skill_interface import BaseSkill

# Fix import issue for dynamic loading
try:
    from .tools import NovelWriterTools
except ImportError:
    sys.path.append(os.path.dirname(__file__))
    from tools import NovelWriterTools

class NovelWriterSkill(BaseSkill):
    def init(self) -> bool:
        self.tools = NovelWriterTools()
        return True

    def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Entry point for the Novel Writer Skill.
        Parses instruction, pre-loads context, and enforces workflow.
        """
        instruction = params.get("instruction", "")
        
        # 1. Parse Book Name
        book_match = re.search(r"《(.*?)》", instruction)
        book_name = book_match.group(1) if book_match else None
        
        # 2. Parse Volume (Optional, simplified)
        volume_match = re.search(r"(第[一二三四五六七八九十0-9]+卷)", instruction)
        volume = volume_match.group(1) if volume_match else None

        response = {
            "skill": "novel_writer",
            "version": "3.0.0",
            "actions_performed": [],
            "context": {}
        }

        if book_name:
            # --- Auto-Load Context (Step 1 of Workflow) ---
            profiles = self.tools.get_character_profiles(book_name, volume)
            outline = self.tools.get_outline(book_name, volume)
            
            response["context"]["character_profiles_snippet"] = profiles[:500] + "..." if len(profiles) > 500 else profiles
            response["context"]["outline_snippet"] = outline[:500] + "..." if len(outline) > 500 else outline
            response["actions_performed"].append(f"Loaded context for book: {book_name}")
            
            if volume:
                 response["actions_performed"].append(f"Loaded context for volume: {volume}")

            # --- Enforce Workflow (Prompt Injection) ---
            response["next_steps_required"] = [
                "1. WRITE: Generate content based on the loaded context.",
                f"2. AUDIT: Call `update_audit_log` for {book_name}.",
                f"3. SYNC: Call `update_status_sync_log` for {book_name}."
            ]
            
            anti_ai_guide = """
【反AI写作风格指南（强制执行）】
1. 极致微观感官：必须使用具体的感官描写（如“烟灰缸里的焦油味”、“指甲划过黑板的噪音”），拒绝空洞形容词。
2. 拒绝宏大叙事：专注于当下场景的细节，不要进行时间跨度大的总结。
3. 扩写策略：通过环境描写（光影、气味、材质）、心理独白（包含犹豫、吐槽）和细节互动来填充篇幅。
4. 禁用AI味词汇：禁止使用“心中一紧”、“嘴角上扬”、“神色复杂”等典型AI套话。
"""

            audit_checklist = """
【编辑审核清单（必须执行）】
1. 字数检查：正文是否超过 2000 字？（如果不足，请使用上述策略扩写，不要直接结束）。
2. 风格检查：是否包含了至少 5 处微观感官描写？
3. 逻辑检查：剧情是否符合大纲要求？
"""

            response["system_reminder"] = f"""
            CRITICAL WORKFLOW ENFORCEMENT:
            You are operating under the Novel Writer v3.0 Protocol.
            Context for 《{book_name}》 has been pre-loaded.
            
            {anti_ai_guide}
            
            {audit_checklist}

            AFTER generating the content, you MUST:
            1. Perform a self-audit using the `update_audit_log` tool based on the Checklist above.
            2. Record any character/plot changes using the `update_status_sync_log` tool.
            
            DO NOT skip these steps.
            """
        else:
            response["status"] = "awaiting_input"
            response["message"] = "Please specify a book name (e.g., 《BookName》) to initialize the workflow."

        return response

    def destroy(self):
        pass
