#!/usr/bin/env python3
"""
Startup verification script for StorySign Platform
Checks if all critical components can be imported and initialized
"""

import sys
import os
import subprocess
from pathlib import Path

def check_backend_imports():
    """Check if backend imports work correctly"""
    print("🔍 Checking backend imports...")
    
    try:
        # Change to backend directory
        backend_dir = Path(__file__).parent / "backend"
        os.chdir(backend_dir)
        
        # Test critical imports
        result = subprocess.run([
            sys.executable, "-c", 
            "import main; from core.database_service import get_database_service; from api.router import api_router; print('✅ Backend imports successful')"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Backend imports successful")
            return True
        else:
            print(f"❌ Backend import failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Backend import test timed out")
        return False
    except Exception as e:
        print(f"❌ Backend import test error: {e}")
        return False

def check_frontend_setup():
    """Check if frontend is properly set up"""
    print("🔍 Checking frontend setup...")
    
    try:
        frontend_dir = Path(__file__).parent / "frontend"
        
        # Check if package.json exists
        package_json = frontend_dir / "package.json"
        if not package_json.exists():
            print("❌ Frontend package.json not found")
            return False
        
        # Check if node_modules exists
        node_modules = frontend_dir / "node_modules"
        if not node_modules.exists():
            print("⚠️  Frontend dependencies not installed (run 'npm install' in frontend directory)")
            return False
        
        print("✅ Frontend setup looks good")
        return True
        
    except Exception as e:
        print(f"❌ Frontend check error: {e}")
        return False

def check_python_dependencies():
    """Check if required Python dependencies are available"""
    print("🔍 Checking Python dependencies...")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "numpy",
        "opencv-python",
        "pillow"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing Python packages: {', '.join(missing_packages)}")
        print(f"   Install with: pip install {' '.join(missing_packages)}")
        return False
    else:
        print("✅ All required Python packages are available")
        return True

def main():
    """Main verification function"""
    print("🚀 StorySign Platform Startup Verification")
    print("=" * 50)
    
    checks = [
        ("Python Dependencies", check_python_dependencies),
        ("Backend Imports", check_backend_imports),
        ("Frontend Setup", check_frontend_setup),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}")
        print("-" * 30)
        result = check_func()
        results.append((check_name, result))
    
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:.<30} {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All checks passed! The application should start successfully.")
        print("\nTo start the application:")
        print("  ./run_full_app.sh")
    else:
        print("⚠️  Some checks failed. Please fix the issues above before starting the application.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())