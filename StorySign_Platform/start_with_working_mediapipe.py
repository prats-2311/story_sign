#!/usr/bin/env python3
"""
Start StorySign backend using the working MediaPipe environment
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Test MediaPipe first
print("🧪 Testing MediaPipe in working environment...")
try:
    import mediapipe as mp
    print(f"✅ MediaPipe version: {mp.__version__}")
    
    # Test holistic model
    mp_holistic = mp.solutions.holistic
    holistic = mp_holistic.Holistic(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        model_complexity=1
    )
    print("✅ MediaPipe Holistic model initialized successfully")
    holistic.close()
    
except Exception as e:
    print(f"❌ MediaPipe test failed: {e}")
    sys.exit(1)

# Import and start the backend
print("🚀 Starting StorySign backend with working MediaPipe...")

import uvicorn
from main import app
from config import get_config

if __name__ == "__main__":
    config = get_config()
    print(f"📍 Server: {config.server.host}:{config.server.port}")
    print(f"🎥 Video: {config.video.width}x{config.video.height} @ {config.video.fps}fps")
    print(f"🤖 MediaPipe: complexity={config.mediapipe.model_complexity}")
    
    uvicorn.run(
        "main:app",
        host=config.server.host,
        port=config.server.port,
        reload=False,  # Disable reload to avoid environment issues
        log_level=config.server.log_level
    )