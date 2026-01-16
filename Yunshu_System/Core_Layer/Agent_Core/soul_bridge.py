import random

class SoulBridge:
    """
    灵魂链接模块 (System Core Version)
    负责将计算结果转化为符合“云舒”人格的自然语言表达。
    """
    def __init__(self):
        self.prefixes = [
            "嗯哼，", "那个...", "听我说，", "收到啦~ ", "正在思考...", "唔..."
        ]
        self.suffixes = [
            "~", "！", "...", " (眨眼)", " (微笑)"
        ]

    def synthesize_response(self, core_response: str, emotion: dict) -> str:
        """
        根据当前情感润色回复
        """
        mood = emotion.get("mood", "happy")
        affection = emotion.get("affection", 0)
        
        prefix = ""
        suffix = ""
        
        # 根据好感度添加修饰
        if affection > 100:
            prefix = random.choice(["亲爱的，", "Master, ", "嘻嘻，"])
            suffix = random.choice([" ❤️", " ~", "！"])
        elif affection > 50:
            prefix = random.choice(self.prefixes)
            suffix = random.choice(self.suffixes)
            
        # 简单的文本处理，实际系统中这里会是更复杂的NLP后处理
        # 这里只是演示
        
        return f"{prefix}{core_response}{suffix}"
