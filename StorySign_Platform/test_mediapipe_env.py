#!/usr/bin/env python3
"""
Test script to verify mediapipe_env has required packages
"""

import sys
import os

def test_imports():
    """Test critical imports for StorySign"""
    print("🧪 Testing MediaPipe Environment Dependencies")
    print("=" * 50)
    
    try:
        import numpy as np
        print(f"✅ NumPy {np.__version__}")
    except ImportError as e:
        print(f"❌ NumPy: {e}")
        return False
    
    try:
        import cv2
        print(f"✅ OpenCV {cv2.__version__}")
    except ImportError as e:
        print(f"❌ OpenCV: {e}")
        return False
    
    try:
        import mediapipe as mp
        print(f"✅ MediaPipe {mp.__version__}")
    except ImportError as e:
        print(f"❌ MediaPipe: {e}")
        return False
    
    try:
        import fastapi
        print(f"✅ FastAPI {fastapi.__version__}")
    except ImportError as e:
        print(f"❌ FastAPI: {e}")
        return False
    
    try:
        import uvicorn
        print(f"✅ Uvicorn {uvicorn.__version__}")
    except ImportError as e:
        print(f"❌ Uvicorn: {e}")
        return False
    
    try:
        import websockets
        print(f"✅ WebSockets {websockets.__version__}")
    except ImportError as e:
        print(f"❌ WebSockets: {e}")
        return False
    
    try:
        import pydantic
        print(f"✅ Pydantic {pydantic.__version__}")
    except ImportError as e:
        print(f"❌ Pydantic: {e}")
        return False
    
    # Test MediaPipe functionality
    try:
        mp_holistic = mp.solutions.holistic
        mp_drawing = mp.solutions.drawing_utils
        print("✅ MediaPipe Holistic and Drawing Utils")
    except Exception as e:
        print(f"❌ MediaPipe functionality: {e}")
        return False
    
    # Test backend imports
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
        from config import get_config
        print("✅ Backend config module")
        
        from video_processor import FrameProcessor
        print("✅ Backend video processor module")
        
    except Exception as e:
        print(f"❌ Backend modules: {e}")
        return False
    
    print("\n🎉 All dependencies are available!")
    print("✅ MediaPipe environment is ready for StorySign")
    return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)