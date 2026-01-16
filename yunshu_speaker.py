import edge_tts
import asyncio
import os
import time
import uuid

class YunshuSpeaker:
    def __init__(self):
        # 使用晓晓作为默认中文语音
        self.voice = "zh-CN-XiaoxiaoNeural" 
        # 临时音频目录
        self.output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_audio")
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    async def speak_to_file(self, text):
        """
        将文本转换为语音文件
        :param text: 要朗读的文本
        :return: 生成的音频文件绝对路径
        """
        try:
            if not text:
                return None
                
            # 使用 UUID 防止文件名冲突
            filename = f"speech_{int(time.time())}_{uuid.uuid4().hex[:6]}.mp3"
            filepath = os.path.join(self.output_dir, filename)
            
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(filepath)
            
            return filepath
        except Exception as e:
            print(f"[YunshuSpeaker] Error generating speech: {e}")
            return None

if __name__ == "__main__":
    # 测试代码
    async def test():
        speaker = YunshuSpeaker()
        path = await speaker.speak_to_file("你好，我是云舒，很高兴为你服务。")
        print(f"Generated audio at: {path}")
    
    asyncio.run(test())
