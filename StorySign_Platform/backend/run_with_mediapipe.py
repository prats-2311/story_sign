#!/usr/bin/env python3
"""
Run StorySign backend with real MediaPipe
"""

import uvicorn
from main import app
from config import get_config

if __name__ == "__main__":
    config = get_config()
    print("🚀 Starting StorySign Backend with MediaPipe...")
    print(f"📍 Server: {config.server.host}:{config.server.port}")
    print(f"🎥 Video: {config.video.width}x{config.video.height} @ {config.video.fps}fps")
    print(f"🤖 MediaPipe: complexity={config.mediapipe.model_complexity}")
    
    uvicorn.run(
        "main:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.server.reload,
        log_level=config.server.log_level
    )