#!/usr/bin/env python3
"""
StorySign Full Application Launcher
Runs both backend (with MediaPipe) and frontend simultaneously
"""

import subprocess
import time
import signal
import sys
import os
import requests
from pathlib import Path

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

class StorySignLauncher:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        
    def print_colored(self, message, color=Colors.NC):
        print(f"{color}{message}{Colors.NC}")
        
    def cleanup(self):
        """Clean up processes and ports"""
        self.print_colored("🛑 Shutting down StorySign application...", Colors.YELLOW)
        
        # Kill backend process
        if self.backend_process:
            self.print_colored(f"📱 Stopping backend (PID: {self.backend_process.pid})...", Colors.YELLOW)
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
            except:
                self.backend_process.kill()
        
        # Kill frontend process
        if self.frontend_process:
            self.print_colored(f"🌐 Stopping frontend (PID: {self.frontend_process.pid})...", Colors.YELLOW)
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=5)
            except:
                self.frontend_process.kill()
        
        # Kill any remaining processes on ports
        self.print_colored("🧹 Cleaning up ports...", Colors.YELLOW)
        try:
            subprocess.run(["pkill", "-f", "python.*main.py"], check=False)
            subprocess.run(["pkill", "-f", "npm.*start"], check=False)
        except:
            pass
            
        self.print_colored("✅ Cleanup complete", Colors.GREEN)
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.cleanup()
        sys.exit(0)
        
    def check_conda_env(self):
        """Check if mediapipe_env conda environment exists"""
        try:
            result = subprocess.run(["conda", "env", "list"], 
                                  capture_output=True, text=True, check=True)
            if "mediapipe_env" not in result.stdout:
                self.print_colored("❌ Error: mediapipe_env conda environment not found", Colors.RED)
                self.print_colored("💡 Please create the environment first:", Colors.YELLOW)
                self.print_colored("   conda create -n mediapipe_env python=3.9", Colors.NC)
                self.print_colored("   conda activate mediapipe_env", Colors.NC)
                self.print_colored("   pip install mediapipe fastapi uvicorn websockets opencv-python numpy", Colors.NC)
                return False
            return True
        except subprocess.CalledProcessError:
            self.print_colored("❌ Error: conda is not installed or not in PATH", Colors.RED)
            return False
            
    def check_npm(self):
        """Check if npm is available"""
        try:
            subprocess.run(["npm", "--version"], 
                          capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            self.print_colored("❌ Error: npm is not installed or not in PATH", Colors.RED)
            return False
            
    def check_directories(self):
        """Check if we're in the right directory"""
        if not (Path("backend").exists() and Path("frontend").exists()):
            self.print_colored("❌ Error: Please run this script from the StorySign_Platform directory", Colors.RED)
            self.print_colored("💡 Current directory should contain 'backend' and 'frontend' folders", Colors.YELLOW)
            return False
        return True
        
    def kill_existing_processes(self):
        """Kill any existing processes on ports 8000 and 3000"""
        self.print_colored("🧹 Cleaning up existing processes...", Colors.YELLOW)
        try:
            subprocess.run(["pkill", "-f", "python.*main.py"], check=False)
            subprocess.run(["pkill", "-f", "npm.*start"], check=False)
            time.sleep(2)
        except:
            pass
            
    def start_backend(self):
        """Start backend with MediaPipe environment"""
        self.print_colored("🔧 Starting backend with MediaPipe...", Colors.BLUE)
        
        try:
            # Change to backend directory and start with conda
            backend_cmd = [
                "conda", "run", "-n", "mediapipe_env", 
                "python", "main.py"
            ]
            
            self.backend_process = subprocess.Popen(
                backend_cmd,
                cwd="backend",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            return True
        except Exception as e:
            self.print_colored(f"❌ Failed to start backend: {e}", Colors.RED)
            return False
            
    def wait_for_backend(self):
        """Wait for backend to be ready"""
        self.print_colored("⏳ Waiting for backend to start...", Colors.YELLOW)
        
        for i in range(30):  # Wait up to 30 seconds
            try:
                response = requests.get("http://localhost:8000/", timeout=2)
                if response.status_code == 200:
                    self.print_colored("✅ Backend is running on http://localhost:8000", Colors.GREEN)
                    return True
            except:
                pass
            time.sleep(1)
            
        self.print_colored("❌ Backend failed to start within 30 seconds", Colors.RED)
        return False
        
    def install_frontend_deps(self):
        """Install frontend dependencies if needed"""
        self.print_colored("📦 Checking frontend dependencies...", Colors.BLUE)
        
        if not Path("frontend/node_modules").exists():
            self.print_colored("📥 Installing frontend dependencies...", Colors.YELLOW)
            try:
                subprocess.run(["npm", "install"], 
                             cwd="frontend", check=True)
                return True
            except subprocess.CalledProcessError:
                self.print_colored("❌ Failed to install frontend dependencies", Colors.RED)
                return False
        return True
        
    def start_frontend(self):
        """Start frontend"""
        self.print_colored("🌐 Starting frontend...", Colors.BLUE)
        
        try:
            self.frontend_process = subprocess.Popen(
                ["npm", "start"],
                cwd="frontend",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return True
        except Exception as e:
            self.print_colored(f"❌ Failed to start frontend: {e}", Colors.RED)
            return False
            
    def run(self):
        """Main run method"""
        # Set up signal handler
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.print_colored("🚀 Starting StorySign Full Application...", Colors.GREEN)
        self.print_colored("📍 Using mediapipe_env conda environment for backend", Colors.NC)
        self.print_colored("📍 Using npm for frontend", Colors.NC)
        
        # Pre-flight checks
        if not self.check_conda_env():
            return 1
        if not self.check_npm():
            return 1
        if not self.check_directories():
            return 1
            
        # Clean up existing processes
        self.kill_existing_processes()
        
        # Start backend
        if not self.start_backend():
            return 1
            
        # Wait for backend to be ready
        if not self.wait_for_backend():
            self.cleanup()
            return 1
            
        # Install frontend dependencies
        if not self.install_frontend_deps():
            self.cleanup()
            return 1
            
        # Start frontend
        if not self.start_frontend():
            self.cleanup()
            return 1
            
        # Wait for frontend to start
        self.print_colored("⏳ Waiting for frontend to start...", Colors.YELLOW)
        time.sleep(10)
        
        # Success message
        self.print_colored("🎉 StorySign application is running!", Colors.GREEN)
        self.print_colored("📱 Backend: http://localhost:8000", Colors.GREEN)
        self.print_colored("🌐 Frontend: http://localhost:3000", Colors.GREEN)
        self.print_colored(f"📋 Backend PID: {self.backend_process.pid}", Colors.YELLOW)
        self.print_colored(f"📋 Frontend PID: {self.frontend_process.pid}", Colors.YELLOW)
        print()
        self.print_colored("🎯 Instructions:", Colors.BLUE)
        self.print_colored("   1. Open http://localhost:3000 in your browser", Colors.NC)
        self.print_colored("   2. Click 'Test Backend' to verify connectivity", Colors.NC)
        self.print_colored("   3. Click 'Start Webcam' to enable camera", Colors.NC)
        self.print_colored("   4. Click 'Start Streaming' to see MediaPipe skeleton", Colors.NC)
        print()
        self.print_colored("⚠️  Press Ctrl+C to stop both services", Colors.YELLOW)
        
        # Keep running until interrupted
        try:
            while True:
                time.sleep(1)
                # Check if processes are still running
                if self.backend_process.poll() is not None:
                    self.print_colored("❌ Backend process died", Colors.RED)
                    break
                if self.frontend_process.poll() is not None:
                    self.print_colored("❌ Frontend process died", Colors.RED)
                    break
        except KeyboardInterrupt:
            pass
            
        self.cleanup()
        return 0

if __name__ == "__main__":
    launcher = StorySignLauncher()
    sys.exit(launcher.run())