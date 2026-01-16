import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import sys

# Add project root to sys.path to allow importing yunshu_speaker
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from yunshu_speaker.speaker import YunshuSpeaker

app = FastAPI(title="Yunshu Speaker Service")
speaker = YunshuSpeaker()

class SpeakRequest(BaseModel):
    text: str
    voice: str = "zh-CN-XiaoxiaoNeural"
    rate: str = "+0%"
    pitch: str = "+0Hz"

@app.post("/speak")
async def speak(request: SpeakRequest):
    try:
        # Update voice if needed
        if request.voice != speaker.voice:
            speaker.voice = request.voice
            
        output_path = await speaker.speak_to_file(
            text=request.text,
            rate=request.rate,
            pitch=request.pitch
        )
        return {"status": "success", "path": output_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.environ.get("YUNSHU_SPEAKER_PORT", 10001))
    print(f"Starting Yunshu Speaker Service on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
