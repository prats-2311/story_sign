#!/usr/bin/env python3
"""
Test script to check if backend starts without errors
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    print("Testing backend imports...")
    
    # Test config import
    from config import get_config
    print("✅ Config import successful")
    
    # Test video processor import
    from video_processor import FrameProcessor
    print("✅ Video processor import successful")
    
    # Test main imports
    import main
    print("✅ Main module import successful")
    
    print("\n🎉 All imports successful! Backend should start properly.")
    
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)