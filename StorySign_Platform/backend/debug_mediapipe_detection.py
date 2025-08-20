#!/usr/bin/env python3
"""
Debug MediaPipe detection in current environment
"""

import sys
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")

try:
    import mediapipe as mp
    print(f"✅ MediaPipe imported successfully - Version: {mp.__version__}")
    MEDIAPIPE_AVAILABLE = True
except ImportError as e:
    print(f"❌ MediaPipe import failed: {e}")
    MEDIAPIPE_AVAILABLE = False

print(f"MEDIAPIPE_AVAILABLE: {MEDIAPIPE_AVAILABLE}")

if MEDIAPIPE_AVAILABLE:
    # Test MediaPipe initialization
    try:
        mp_holistic = mp.solutions.holistic
        holistic = mp_holistic.Holistic(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1
        )
        print("✅ MediaPipe Holistic initialized successfully")
        holistic.close()
    except Exception as e:
        print(f"❌ MediaPipe initialization failed: {e}")