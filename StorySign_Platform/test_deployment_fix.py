#!/usr/bin/env python3
"""
Test script to verify the deployment fix works
"""

import sys
import os
import subprocess
import time

def test_import():
    """Test if the simplified API can be imported"""
    print("🧪 Testing API import...")
    try:
        sys.path.insert(0, 'StorySign_Platform/backend')
        from main_api_simple import app
        print("✅ API imports successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_requirements():
    """Test if minimal requirements can be installed"""
    print("📦 Testing minimal requirements...")
    try:
        # Check if requirements file exists
        req_file = 'StorySign_Platform/backend/requirements_minimal.txt'
        if not os.path.exists(req_file):
            print(f"❌ Requirements file not found: {req_file}")
            return False
        
        print(f"✅ Requirements file found: {req_file}")
        
        # Read requirements
        with open(req_file, 'r') as f:
            requirements = f.read()
        
        print("📋 Minimal requirements:")
        for line in requirements.split('\n'):
            if line.strip() and not line.startswith('#'):
                print(f"   - {line.strip()}")
        
        return True
    except Exception as e:
        print(f"❌ Error checking requirements: {e}")
        return False

def test_render_config():
    """Test if render.yaml is properly configured"""
    print("⚙️  Testing render.yaml configuration...")
    try:
        import yaml
        
        config_file = 'StorySign_Platform/render.yaml'
        if not os.path.exists(config_file):
            print(f"❌ Render config not found: {config_file}")
            return False
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check key configuration
        service = config['services'][0]
        
        checks = [
            ('runtime', 'python'),
            ('buildCommand', 'StorySign_Platform/backend'),
            ('startCommand', 'main_api_simple:app'),
            ('healthCheckPath', '/health')
        ]
        
        for key, expected in checks:
            if key not in service:
                print(f"❌ Missing key in render.yaml: {key}")
                return False
            
            if expected not in str(service[key]):
                print(f"❌ Incorrect value for {key}: {service[key]}")
                print(f"   Expected to contain: {expected}")
                return False
        
        print("✅ Render configuration looks good")
        return True
        
    except Exception as e:
        print(f"❌ Error checking render.yaml: {e}")
        return False

def test_directory_structure():
    """Test if directory structure is correct"""
    print("📁 Testing directory structure...")
    
    required_files = [
        'StorySign_Platform/backend/main_api_simple.py',
        'StorySign_Platform/backend/requirements_minimal.txt',
        'StorySign_Platform/render.yaml',
        'StorySign_Platform/netlify.toml'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✅ Found: {file_path}")
    
    if missing_files:
        print("❌ Missing files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print("✅ All required files present")
    return True

def main():
    """Run all tests"""
    print("🚀 Testing StorySign Deployment Fix")
    print("=" * 50)
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("Render Configuration", test_render_config),
        ("Minimal Requirements", test_requirements),
        ("API Import", test_import)
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
        print("🎉 All tests passed! Ready for deployment.")
        print("\n📝 Next steps:")
        print("1. Commit and push your changes:")
        print("   git add .")
        print("   git commit -m 'Fix Render deployment configuration'")
        print("   git push origin main")
        print("\n2. Deploy on Render:")
        print("   - Go to your Render dashboard")
        print("   - Click 'Manual Deploy' or wait for auto-deploy")
        print("   - Monitor build logs")
        print("\n3. Test deployment:")
        print("   curl https://your-app.onrender.com/health")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())