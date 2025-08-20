#!/usr/bin/env python3
"""
Quick Fix Script for StorySign Environment Issues
Addresses the specific issues found in your terminal output
"""

import subprocess
import sys
import os

def main():
    print("🚀 StorySign Quick Fix")
    print("=" * 30)
    
    # Check current environment
    print(f"Current Python: {sys.executable}")
    print(f"Virtual Env: {os.environ.get('VIRTUAL_ENV', 'None')}")
    print(f"Conda Env: {os.environ.get('CONDA_DEFAULT_ENV', 'None')}")
    print()
    
    # Fix 1: Install MediaPipe with specific version
    print("🔧 Fix 1: Installing MediaPipe...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "mediapipe==0.10.9"])
        print("✅ MediaPipe installed successfully")
    except subprocess.CalledProcessError:
        print("❌ MediaPipe installation failed")
        print("💡 Try: conda install -c conda-forge mediapipe")
    
    # Fix 2: Install opencv-contrib-python for better codec support
    print("\n🔧 Fix 2: Installing OpenCV with better codec support...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", "opencv-python"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "opencv-contrib-python==4.8.1.78"])
        print("✅ OpenCV with contrib installed")
    except subprocess.CalledProcessError:
        print("❌ OpenCV installation failed")
    
    # Fix 3: Test imports
    print("\n🧪 Testing critical imports...")
    
    test_packages = [
        ("cv2", "OpenCV"),
        ("numpy", "NumPy"), 
        ("mediapipe", "MediaPipe")
    ]
    
    all_working = True
    for package, name in test_packages:
        try:
            __import__(package)
            print(f"✅ {name} working")
        except ImportError:
            print(f"❌ {name} failed")
            all_working = False
    
    # Fix 4: Test WebP support
    print("\n🧪 Testing WebP support...")
    try:
        import cv2
        import numpy as np
        
        test_img = np.zeros((10, 10, 3), dtype=np.uint8)
        success, _ = cv2.imencode('.webp', test_img, [cv2.IMWRITE_WEBP_QUALITY, 80])
        
        if success:
            print("✅ WebP support working")
        else:
            print("⚠️  WebP support limited - will use JPEG fallback")
    except Exception as e:
        print(f"⚠️  WebP test failed: {e}")
    
    if all_working:
        print("\n🎉 Quick fixes completed successfully!")
        print("\nNow you can run:")
        print("  python benchmark_optimizations.py")
        print("  cd backend && python main.py")
    else:
        print("\n⚠️  Some issues remain. Try:")
        print("  ./setup_clean_environment.sh")
        print("  python fix_environment.py")

if __name__ == "__main__":
    main()