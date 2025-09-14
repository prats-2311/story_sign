#!/usr/bin/env python3
"""
Test the production API locally to ensure it works before deploying
"""

import os
import sys
import subprocess
import time
import requests

def test_production_api():
    """Test if the production API starts and responds"""
    print("🧪 Testing production API locally...")
    
    # Change to backend directory
    backend_dir = "StorySign_Platform/backend"
    if not os.path.exists(backend_dir):
        print("❌ Backend directory not found")
        return False
    
    # Check if production file exists
    prod_file = f"{backend_dir}/main_api_production.py"
    if not os.path.exists(prod_file):
        print("❌ main_api_production.py not found")
        return False
    
    print("✅ Production file exists")
    
    # Test import
    try:
        original_dir = os.getcwd()
        os.chdir(backend_dir)
        sys.path.insert(0, '.')
        
        from main_api_production import app
        print("✅ Production API imports successfully")
        
        # Test if app has required endpoints
        if hasattr(app, 'routes'):
            routes = [route.path for route in app.routes]
            if '/health' in routes:
                print("✅ Health endpoint exists")
            else:
                print("⚠️  Health endpoint not found in routes")
        
        os.chdir(original_dir)
        if '.' in sys.path:
            sys.path.remove('.')
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        os.chdir(original_dir)
        if '.' in sys.path:
            sys.path.remove('.')
        return False

def test_requirements():
    """Test if requirements can be installed"""
    print("📦 Testing requirements installation...")
    
    req_file = "StorySign_Platform/backend/requirements_minimal.txt"
    if not os.path.exists(req_file):
        print("❌ requirements_minimal.txt not found")
        return False
    
    print("✅ Requirements file exists")
    
    # Read requirements
    try:
        with open(req_file, 'r') as f:
            requirements = f.read()
        
        print("📋 Requirements:")
        for line in requirements.split('\n'):
            if line.strip() and not line.startswith('#'):
                print(f"   - {line.strip()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading requirements: {e}")
        return False

def create_render_commands():
    """Create the exact commands for Render dashboard"""
    print("📝 Creating Render dashboard commands...")
    
    build_command = "cd StorySign_Platform/backend && pip install -r requirements_minimal.txt"
    start_command = "cd StorySign_Platform/backend && python main_api_production.py"
    
    print("\n" + "=" * 60)
    print("📋 COPY THESE COMMANDS TO RENDER DASHBOARD:")
    print("=" * 60)
    print("\n🔨 BUILD COMMAND:")
    print(f"   {build_command}")
    print("\n🚀 START COMMAND:")
    print(f"   {start_command}")
    print("\n💾 ENVIRONMENT VARIABLES (set these in Render):")
    print("   DATABASE_HOST=your-tidb-host")
    print("   DATABASE_USER=your-tidb-username")
    print("   DATABASE_PASSWORD=your-tidb-password")
    print("   JWT_SECRET=your-generated-secret")
    print("   ENVIRONMENT=production")
    print("   PORT=8000")
    print("=" * 60)
    
    return True

def main():
    """Run all tests"""
    print("🚀 Testing Production API for Render Deployment")
    print("=" * 50)
    
    tests = [
        ("Test production API", test_production_api),
        ("Test requirements", test_requirements),
        ("Create Render commands", create_render_commands)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 Production API is ready for deployment!")
        print("\n📝 Next steps:")
        print("1. Go to Render Dashboard → Your Service → Settings")
        print("2. Copy the BUILD COMMAND and START COMMAND from above")
        print("3. Set the ENVIRONMENT VARIABLES")
        print("4. Save Changes and Manual Deploy")
        print("5. Monitor logs for successful startup")
    else:
        print("❌ Some tests failed. Fix issues before deploying.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())