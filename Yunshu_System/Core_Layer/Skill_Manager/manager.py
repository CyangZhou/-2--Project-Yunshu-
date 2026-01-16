import os
import yaml
import importlib.util
import sys
import logging
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from Yunshu_System.Protocol_Layer.skill_interface import BaseSkill

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SkillManager")

class SkillManager:
    def __init__(self, skills_dir: str):
        self.skills_dir = skills_dir
        self.loaded_skills: Dict[str, BaseSkill] = {}
        self.skill_metadata: Dict[str, Any] = {}

    def scan_skills(self) -> List[Dict[str, Any]]:
        """
        Scan the skills directory for valid skill packages.
        """
        skills = []
        if not os.path.exists(self.skills_dir):
            os.makedirs(self.skills_dir)
            return []

        for item in os.listdir(self.skills_dir):
            skill_path = os.path.join(self.skills_dir, item)
            if os.path.isdir(skill_path):
                md_path = os.path.join(skill_path, "SKILL.md")
                yaml_path = os.path.join(skill_path, "skill.yaml")
                
                meta = None
                
                # 1. Try SKILL.md (Claude Standard)
                if os.path.exists(md_path):
                    try:
                        with open(md_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if content.startswith('---'):
                                parts = content.split('---', 2)
                                if len(parts) >= 3:
                                    meta = yaml.safe_load(parts[1])
                                    meta['instructions'] = parts[2].strip()
                                    meta['type'] = 'markdown'
                    except Exception as e:
                        logger.error(f"Failed to parse SKILL.md for {item}: {e}")
                
                # 2. Fallback to skill.yaml (Legacy)
                if not meta and os.path.exists(yaml_path):
                    try:
                        with open(yaml_path, 'r', encoding='utf-8') as f:
                            meta = yaml.safe_load(f)
                            meta['type'] = 'python' # Legacy assumption
                    except Exception as e:
                        logger.error(f"Failed to load skill metadata for {item}: {e}")

                if meta:
                    meta['id'] = item
                    meta['path'] = skill_path
                    skills.append(meta)
                    self.skill_metadata[item] = meta
        return skills

    def load_skill(self, skill_id: str) -> Optional[BaseSkill]:
        """
        Dynamically load a skill module and instantiate the class.
        Supports both Python-based skills (main.py) and Markdown-based skills (SKILL.md).
        """
        if skill_id in self.loaded_skills:
            return self.loaded_skills[skill_id]

        if skill_id not in self.skill_metadata:
            logger.error(f"Skill {skill_id} not found in metadata.")
            return None

        meta = self.skill_metadata[skill_id]
        skill_path = meta['path']
        
        # Check for main.py (Code Skill)
        module_path = os.path.join(skill_path, "main.py")
        if os.path.exists(module_path):
            try:
                spec = importlib.util.spec_from_file_location(f"skills.{skill_id}", module_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[f"skills.{skill_id}"] = module
                spec.loader.exec_module(module)

                # Find the subclass of BaseSkill
                skill_cls = None
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, BaseSkill) and attr is not BaseSkill:
                        skill_cls = attr
                        break
                
                if not skill_cls:
                    logger.error(f"No BaseSkill subclass found in {skill_id}")
                    return None

                instance = skill_cls(meta)
                if instance.init():
                    self.loaded_skills[skill_id] = instance
                    return instance
                else:
                    logger.error(f"Skill {skill_id} initialization failed.")
                    return None
            except Exception as e:
                logger.error(f"Failed to load skill {skill_id}: {e}")
                return None
        
        # If no main.py, check if it's a Markdown Skill
        elif meta.get('type') == 'markdown':
            # BaseSkill is already imported at module level
            
            class MarkdownSkill(BaseSkill):
                def init(self) -> bool:
                    return True
                def run(self, params: Dict[str, Any]) -> Dict[str, Any]:
                    # Return instructions as the primary content
                    return {
                        "status": "success",
                        "content": self.metadata.get('instructions', ''),
                        "meta": self.metadata
                    }
                def destroy(self):
                    pass
            
            instance = MarkdownSkill(meta)
            self.loaded_skills[skill_id] = instance
            return instance

        else:
            logger.error(f"main.py not found for skill {skill_id} and not a Markdown skill.")
            return None

    def run_skill(self, skill_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a skill.
        """
        skill = self.load_skill(skill_id)
        if not skill:
            return {"status": "error", "message": "Skill not loaded"}

        try:
            # Validate input (Basic check)
            # TODO: Add schema validation
            
            result = skill.run(params)
            return {"status": "success", "data": result}
        except Exception as e:
            logger.error(f"Error running skill {skill_id}: {e}")
            return {"status": "error", "message": str(e)}

    def unload_skill(self, skill_id: str):
        if skill_id in self.loaded_skills:
            try:
                self.loaded_skills[skill_id].destroy()
            except Exception as e:
                logger.error(f"Error destroying skill {skill_id}: {e}")
            del self.loaded_skills[skill_id]
