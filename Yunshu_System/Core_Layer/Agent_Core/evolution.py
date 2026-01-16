import os
import json
import time

class EvolutionEngine:
    """
    云舒进化引擎 (System Core Version)
    负责记忆存储、经验吸收和自我成长。
    """
    def __init__(self, profile_path: str = None):
        if profile_path is None:
            # 默认存储在项目根目录的 Memory 文件夹中
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.profile_path = os.path.join(base_dir, "Memory", "user_profile.json")
        else:
            self.profile_path = profile_path
            
        self.session_insights = []
        self._load_memory()

    def _load_memory(self):
        if not os.path.exists(self.profile_path):
            try:
                os.makedirs(os.path.dirname(self.profile_path), exist_ok=True)
                with open(self.profile_path, 'w', encoding='utf-8') as f:
                    json.dump({"interactions": [], "level": 1, "exp": 0}, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"[Evolution] Memory init warning: {e}")

    def absorb_experience(self, user_input: str, system_response: str):
        """
        吸收交互经验
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        insight = {
            "timestamp": timestamp,
            "user": user_input[:50] + "..." if len(user_input) > 50 else user_input,
            "response_type": "interaction"
        }
        self.session_insights.append(insight)
        self._update_neuro_pathways(10) # 每次交互获得10点经验

    def _update_neuro_pathways(self, exp_gain: int):
        """
        更新神经通路（写入长期记忆）
        """
        if not os.path.exists(self.profile_path):
            return

        try:
            with open(self.profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            data["exp"] = data.get("exp", 0) + exp_gain
            
            # 简单的升级逻辑
            current_level = data.get("level", 1)
            if data["exp"] > current_level * 100:
                data["level"] += 1
                # 这里未来可以触发升级事件
            
            # 保存最近的交互（由于是核心，尽量减少IO频率，实际应异步，这里简化为同步）
            if "interactions" not in data:
                data["interactions"] = []
            
            # 只保留最近50条
            data["interactions"] = (data["interactions"] + self.session_insights)[-50:]
            self.session_insights = [] # 清空缓存

            with open(self.profile_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"[Evolution] Memory update failed: {e}")
