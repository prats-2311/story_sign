#!/usr/bin/env python3
"""
Local Development Startup Script
Runs the StorySign API with only working modules for local development
"""

import os
import sys
import subprocess

def main():
    print("🚀 StorySign Local Development Server")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("main_local.py"):
        print("❌ Error: Please run this from the backend directory")
        print("   cd StorySign_Platform/backend")
        sys.exit(1)
    
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: No virtual environment detected")
        print("   Consider activating your virtual environment first")
        print("   conda activate mediapipe_env")
        print()
    
    print("📋 Starting local development server...")
    print("   - Only working modules will be loaded")
    print("   - Broken modules will be skipped gracefully")
    print("   - API docs available at: http://127.0.0.1:8000/docs")
    print()
    
    try:
        # Run the local development server
        subprocess.run([
            sys.executable, "main_local.py",
            "--host", "127.0.0.1",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()