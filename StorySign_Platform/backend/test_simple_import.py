#!/usr/bin/env python3
"""
Simple test to debug import issues
"""

print("Starting import test...")

try:
    print("1. Importing base modules...")
    import base64
    import cv2
    import numpy as np
    import logging
    from typing import Optional, Dict, Any, Tuple
    from datetime import datetime
    import time
    print("   Base modules imported successfully")
    
    print("2. Importing config...")
    from config import MediaPipeConfig, VideoConfig
    print("   Config imported successfully")
    
    print("3. Testing MediaPipe import...")
    try:
        import mediapipe as mp
        MEDIAPIPE_AVAILABLE = True
        print("   MediaPipe imported successfully")
    except ImportError:
        MEDIAPIPE_AVAILABLE = False
        print("   MediaPipe not available, using mock")
    
    print("4. Defining simple class...")
    class TestProcessor:
        def __init__(self):
            self.name = "test"
        
        def process(self):
            return "processed"
    
    print("5. Testing class instantiation...")
    processor = TestProcessor()
    result = processor.process()
    print(f"   Class test result: {result}")
    
    print("✅ All tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()