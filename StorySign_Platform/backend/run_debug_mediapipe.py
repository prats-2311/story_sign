#!/usr/bin/env python3
"""
Run StorySign backend with MediaPipe and debug logging
"""

import sys
print(f"🐍 Python executable: {sys.executable}")
print(f"🐍 Python version: {sys.version}")

# Test MediaPipe import before starting server
try:
    import mediapipe as mp
    print(f"✅ MediaPipe imported - Version: {mp.__version__}")
    MEDIAPIPE_AVAILABLE = True
except ImportError as e:
    print(f"❌ MediaPipe import failed: {e}")
    MEDIAPIPE_AVAILABLE = False

print(f"🤖 MEDIAPIPE_AVAILABLE: {MEDIAPIPE_AVAILABLE}")

# Import and start the server
import uvicorn
from main import app
from config import get_config

if __name__ == "__main__":
    config = get_config()
    print("🚀 Starting StorySign Backend with MediaPipe Debug...")
    print(f"📍 Server: {config.server.host}:{config.server.port}")
    print(f"🎥 Video: {config.video.width}x{config.video.height} @ {config.video.fps}fps")
    print(f"🤖 MediaPipe: complexity={config.mediapipe.model_complexity}")
    
    uvicorn.run(
        "main:app",
        host=config.server.host,
        port=config.server.port,
        reload=False,  # Disable reload to avoid issues
        log_level=config.server.log_level
    )