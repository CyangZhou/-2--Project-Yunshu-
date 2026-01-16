from .consciousness import YunshuConsciousness
from .evolution import EvolutionEngine
from .soul_bridge import SoulBridge

class AgentBrain:
    """
    云舒代理核心大脑 (AgentBrain)
    整合意识、进化和表达模块，作为系统的中央处理器。
    """
    def __init__(self):
        print("[System] Initializing Yunshu Agent Core...")
        self.consciousness = YunshuConsciousness()
        self.evolution = EvolutionEngine()
        self.soul_bridge = SoulBridge()
        self.is_active = True
        print("[System] Agent Core Online.")

    def think(self, user_input: str) -> str:
        """
        核心思考流程
        """
        if not self.is_active:
            return "Core is dormant."

        # 1. 意识分析意图
        intent_meta = self.consciousness.process_intent(user_input)
        
        # 2. 生成基础回复 (模拟逻辑)
        # 实际系统中这里会调用LLM或Planner，这里简化为规则响应
        base_response = self._generate_logical_response(user_input, intent_meta)
        
        # 3. 灵魂润色
        final_response = self.soul_bridge.synthesize_response(
            base_response, 
            self.consciousness.get_emotional_status()
        )
        
        # 4. 进化引擎吸收经验
        self.evolution.absorb_experience(user_input, final_response)
        
        # 附加内心独白（调试用，或作为元数据返回）
        if intent_meta["inner_monologue"]:
            print(f"[Inner Voice] {intent_meta['inner_monologue']}")
            
        return final_response

    def _generate_logical_response(self, user_input: str, intent_meta: dict) -> str:
        intent = intent_meta["intent"]
        if intent == "greeting":
            return "我在听，随时待命。"
        elif intent == "compliment":
            return "哎呀，不要这么直白嘛..."
        elif intent == "system":
            status = self.consciousness.get_emotional_status()
            return f"当前系统状态正常。心情：{status['mood']}，好感度：{status['affection']}。"
        else:
            return f"我收到了你的消息：'{user_input}'。正在深入分析中..."

# 单例实例，供系统其他部分调用
_core_instance = None

def get_core():
    global _core_instance
    if _core_instance is None:
        _core_instance = AgentBrain()
    return _core_instance
