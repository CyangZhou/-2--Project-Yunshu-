import pyttsx3
import threading
from flask import Flask, request, jsonify

app = Flask(__name__)

# 定义语音播报函数（线程安全）
def speak_text(text, word_by_word=False):
    """
    线程安全的语音播报函数
    
    参数：
        text: str - 要播报的文本内容
        word_by_word: bool - 是否逐字播报（默认False）
    """
    # 每个线程单独初始化语音引擎
    engine = pyttsx3.init()
    
    # 设置语音属性
    voices = engine.getProperty('voices')
    # 选择中文语音
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

@app.route('/speak', methods=['POST'])
def speak():
    """
    语音播报API接口
    
    参数：
        text: str - 要播报的文本内容
        word_by_word: bool - 是否逐字播报（默认False）
    
    返回：
        JSON响应，包含操作结果
    """
    try:
        # 获取请求参数
        data = request.get_json()
        text = data.get('text', '')
        word_by_word = data.get('word_by_word', False)
        
        if not text:
            return jsonify({'code': 400, 'message': '缺少text参数'}), 400
        
        # 在新线程中播报文本，避免run loop already started错误
        t = threading.Thread(target=speak_text, args=(text, word_by_word))
        t.start()
        
        return jsonify({'code': 200, 'message': '语音播报成功'}), 200
    except Exception as e:
        return jsonify({'code': 500, 'message': f'语音播报失败：{str(e)}'}), 500

@app.route('/status', methods=['GET'])
def status():
    """
    检查语音播报服务状态
    
    返回：
        JSON响应，包含服务状态
    """
    return jsonify({'code': 200, 'message': '语音播报服务正常运行'}), 200

if __name__ == '__main__':
    # 启动Flask应用，监听所有IP地址的5000端口
    app.run(host='0.0.0.0', port=5000, debug=False)