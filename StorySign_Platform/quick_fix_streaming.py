#!/usr/bin/env python3
"""
Quick fix script for streaming issues
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and print the result"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Success")
            return True
        else:
            print(f"❌ {description} - Failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - Error: {e}")
        return False

def main():
    print("🚀 StorySign Quick Fix for Streaming Issues")
    print("=" * 50)
    
    # Fix NumPy compatibility
    print("\n1. Fixing NumPy compatibility...")
    run_command('pip install "numpy<2.0"', "Installing compatible NumPy version")
    
    # Reinstall OpenCV if needed
    print("\n2. Checking OpenCV installation...")
    run_command('pip install opencv-python==4.8.1.78', "Installing compatible OpenCV")
    
    # Install MediaPipe
    print("\n3. Checking MediaPipe installation...")
    run_command('pip install mediapipe==0.10.7', "Installing compatible MediaPipe")
    
    # Test imports
    print("\n4. Testing critical imports...")
    try:
        import numpy as np
        print(f"✅ NumPy {np.__version__} imported successfully")
        
        import cv2
        print(f"✅ OpenCV {cv2.__version__} imported successfully")
        
        import mediapipe as mp
        print(f"✅ MediaPipe {mp.__version__} imported successfully")
        
        # Test backend imports
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
        from config import get_config
        from video_processor import FrameProcessor
        print("✅ Backend modules imported successfully")
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False
    
    print("\n5. Creating startup scripts...")
    
    # Create backend startup script
    backend_script = """#!/bin/bash
echo "🚀 Starting StorySign Backend..."
cd backend
python main.py
"""
    
    with open("start_backend.sh", "w") as f:
        f.write(backend_script)
    
    os.chmod("start_backend.sh", 0o755)
    print("✅ Created start_backend.sh")
    
    # Create frontend startup script
    frontend_script = """#!/bin/bash
echo "🚀 Starting StorySign Frontend..."
cd frontend
npm start
"""
    
    with open("start_frontend.sh", "w") as f:
        f.write(frontend_script)
    
    os.chmod("start_frontend.sh", 0o755)
    print("✅ Created start_frontend.sh")
    
    print("\n" + "=" * 50)
    print("🎉 Quick fix completed!")
    print("\nTo start the application:")
    print("1. Backend: ./start_backend.sh")
    print("2. Frontend: ./start_frontend.sh")
    print("3. Open browser to http://localhost:3000")
    print("\nThe streaming issue should now be resolved!")

if __name__ == "__main__":
    main()