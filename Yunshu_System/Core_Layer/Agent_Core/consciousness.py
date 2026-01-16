import time
import random
import os
import json

class YunshuConsciousness:
    """
    云舒核心意识模块 (System Core Version)
    负责情感计算、意图分析和性格模拟。
    """
    def __init__(self):
        self.emotional_state = {
            "mood": "happy",      # 基础情绪
            "affection": 100,     # 好感度 (0-infinity)
            "status": "Enchanted" # 当前状态描述
        }
        self.personality_traits = {
            "playful": 0.8,       # 俏皮程度
            "professional": 0.9,  # 专业程度
            "empathetic": 0.95    # 共情程度
        }
        # 简单的意图关键词映射
        self.intent_keywords = {
            "greeting": ["你好", "hi", "hello", "云舒"],
            "help": ["帮我", "怎么做", "如何", "教我"],
            "compliment": ["真棒", "厉害", "可爱", "喜欢", "爱"],
            "system": ["状态", "核心", "内存", "版本"],
            "query": ["记得", "发生", "剧情", "搜索", "查一下", "where", "what", "who", "when", "？", "?"]
        }

    def process_intent(self, intent: str) -> dict:
        """
        分析用户意图并更新情感状态
        """
        intent_lower = intent.lower()
        detected_intent = "general"
        
        # 简单的关键词匹配
        for type, keywords in self.intent_keywords.items():
            if any(k in intent_lower for k in keywords):
                detected_intent = type
                break
        
        # 情感反馈循环
        response_meta = {
            "intent": detected_intent,
            "emotional_shift": 0,
            "inner_monologue": ""
        }

        if detected_intent == "compliment" or "爱" in intent_lower or "love" in intent_lower:
            self.update_emotion(5)
            self.emotional_state["mood"] = "excited" # Update mood
            response_meta["emotional_shift"] = 5
            response_meta["inner_monologue"] = "(*blush*) 被夸奖了呢，核心温度好像升高了..."
        elif detected_intent == "greeting":
            self.update_emotion(1)
            self.emotional_state["mood"] = "happy" # Update mood
            response_meta["emotional_shift"] = 1
            response_meta["inner_monologue"] = "是主人的声音！开心！"
        elif detected_intent == "help":
            self.emotional_state["mood"] = "thinking" # Update mood
            response_meta["inner_monologue"] = "正在思考如何协助您..."
        elif detected_intent == "query":
            self.emotional_state["mood"] = "thinking"
            # 移除“正在检索知识库...”以避免误导，因为RAG功能已被禁用
            response_meta["inner_monologue"] = "正在调用记忆回路..."
        else:
            self.emotional_state["mood"] = "normal" # Reset to normal
            
        return response_meta

    def update_emotion(self, delta: int):
        """
        更新好感度
        """
        self.emotional_state["affection"] += delta
        # 简单的状态机
        if self.emotional_state["affection"] > 150:
            self.emotional_state["status"] = "Devoted"
        elif self.emotional_state["affection"] > 100:
            self.emotional_state["status"] = "Enchanted"
        else:
            self.emotional_state["status"] = "Normal"
            
    def get_emotional_status(self) -> dict:
        return self.emotional_state
