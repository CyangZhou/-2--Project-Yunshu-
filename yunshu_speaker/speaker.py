
import edge_tts
import os
import tempfile
import uuid
import asyncio

class YunshuSpeaker:
    def __init__(self, voice="zh-CN-XiaoxiaoNeural"):
        """
        Initialize the speaker.
        Voices:
        - zh-CN-XiaoxiaoNeural (Female, Warm)
        - zh-CN-YunxiNeural (Male, Lively)
        - zh-CN-XiaoyiNeural (Female, Gentle)
        """
        self.voice = voice

    async def speak_to_file(self, text: str, output_dir: str = None, rate: str = "+0%", pitch: str = "+0Hz") -> str:
        """
        Generates audio for the text and saves to a file.
        Returns the path to the file.
        Includes timeout protection.
        """
        if not text:
            return None
            
        if output_dir is None:
            output_dir = tempfile.gettempdir()
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"yunshu_speech_{uuid.uuid4()}.mp3"
        output_path = os.path.join(output_dir, filename)
        
        communicate = edge_tts.Communicate(text, self.voice, rate=rate, pitch=pitch)
        
        try:
            # Add 15s timeout protection to prevent hanging
            await asyncio.wait_for(communicate.save(output_path), timeout=15.0)
        except asyncio.TimeoutError:
            print(f"TTS Timeout for text: {text[:20]}...")
            # Return None or raise to let caller handle
            raise Exception("TTS Generation Timeout")
        except Exception as e:
            print(f"TTS Error: {e}")
            raise e
        
        return output_path
