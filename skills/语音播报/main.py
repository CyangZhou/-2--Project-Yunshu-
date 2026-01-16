import pyttsx3
import sys

def speak(text, word_by_word=False):
    """
    将文本转换为语音进行播报
    
    参数:
        text: str - 要播报的文本内容
        word_by_word: bool - 是否逐字播报（默认False）
    """
    # 初始化语音引擎
    engine = pyttsx3.init()
    
    # 设置语音属性
    voices = engine.getProperty('voices')
    # 选择中文语音（通常索引为0或1，根据系统环境可能不同）
    for voice in voices:
        if 'Chinese' in voice.name or 'Chinese' in voice.id or 'zh' in voice.id:
            engine.setProperty('voice', voice.id)
            break
    
    # 设置语速（默认值为200）
    engine.setProperty('rate', 180)
    
    # 设置音量（0.0到1.0）
    engine.setProperty('volume', 1.0)
    
    # 播报文本
    if word_by_word:
        # 逐字播报，中间添加停顿
        for char in text:
            engine.say(char)
            engine.runAndWait()
    else:
        # 正常播报
        engine.say(text)
        engine.runAndWait()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # 从命令行参数获取要播报的文本
        text = ' '.join(sys.argv[1:])
        # 默认开启逐字播报
        speak(text, word_by_word=True)
    else:
        # 如果没有提供文本，使用默认欢迎语
        speak("语音播报技能已启动，您可以通过命令行参数传入要播报的文本")