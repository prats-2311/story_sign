#!/usr/bin/env python3
"""
Test script to verify the deployment directory structure is correct
"""

import os
import sys

def test_repository_structure():
    """Test if the repository structure matches deployment expectations"""
    print("📁 Testing repository structure...")
    
    # Check if we're at the repository root
    if not os.path.exists('StorySign_Platform'):
        print("❌ Not at repository root - StorySign_Platform directory not found")
        print("   Run this script from the repository root (story_sign/)")
        return False
    
    # Required files at repository root
    root_files = [
        'netlify.toml',
        'render.yaml'
    ]
    
    # Required directories and files
    required_paths = [
        'StorySign_Platform/frontend/package.json',
        'StorySign_Platform/frontend/src/App.js',
        'StorySign_Platform/frontend/public/index.html',
        'StorySign_Platform/backend/main_api_simple.py',
        'StorySign_Platform/backend/requirements_minimal.txt'
    ]
    
    # Check root configuration files
    missing_root_files = []
    for file_path in root_files:
        if not os.path.exists(file_path):
            missing_root_files.append(file_path)
        else:
            print(f"✅ Found at root: {file_path}")
    
    if missing_root_files:
        print("❌ Missing configuration files at repository root:")
        for file_path in missing_root_files:
            print(f"   - {file_path}")
        return False
    
    # Check required project files
    missing_files = []
    for file_path in required_paths:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✅ Found: {file_path}")
    
    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print("✅ Repository structure is correct")
    return True

def test_netlify_config():
    """Test netlify.toml configuration"""
    print("🔧 Testing netlify.toml configuration...")
    
    if not os.path.exists('netlify.toml'):
        print("❌ netlify.toml not found at repository root")
        return False
    
    try:
        with open('netlify.toml', 'r') as f:
            content = f.read()
        
        # Check for correct paths
        if 'base = "StorySign_Platform/frontend"' in content:
            print("✅ Correct base directory in netlify.toml")
        else:
            print("❌ Incorrect base directory in netlify.toml")
            return False
        
        if 'publish = "StorySign_Platform/frontend/build"' in content:
            print("✅ Correct publish directory in netlify.toml")
        else:
            print("❌ Incorrect publish directory in netlify.toml")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading netlify.toml: {e}")
        return False

def test_render_config():
    """Test render.yaml configuration"""
    print("🔧 Testing render.yaml configuration...")
    
    if not os.path.exists('render.yaml'):
        print("❌ render.yaml not found at repository root")
        return False
    
    try:
        with open('render.yaml', 'r') as f:
            content = f.read()
        
        # Check for correct paths
        if 'cd StorySign_Platform/backend' in content:
            print("✅ Correct backend paths in render.yaml")
        else:
            print("❌ Incorrect backend paths in render.yaml")
            return False
        
        if 'main_api_simple:app' in content:
            print("✅ Using simplified API in render.yaml")
        else:
            print("❌ Not using simplified API in render.yaml")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading render.yaml: {e}")
        return False

def test_build_commands():
    """Test if build commands would work"""
    print("🔨 Testing build commands...")
    
    # Test backend build command
    backend_path = 'StorySign_Platform/backend'
    if os.path.exists(f'{backend_path}/requirements_minimal.txt'):
        print("✅ Backend requirements file exists")
    else:
        print("❌ Backend requirements file missing")
        return False
    
    # Test frontend build command
    frontend_path = 'StorySign_Platform/frontend'
    if os.path.exists(f'{frontend_path}/package.json'):
        print("✅ Frontend package.json exists")
        
        # Check if build script exists
        try:
            import json
            with open(f'{frontend_path}/package.json', 'r') as f:
                package = json.load(f)
            
            if 'scripts' in package and 'build' in package['scripts']:
                print("✅ Frontend build script exists")
            else:
                print("❌ Frontend build script missing")
                return False
                
        except Exception as e:
            print(f"⚠️  Could not verify frontend build script: {e}")
    else:
        print("❌ Frontend package.json missing")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 Testing Deployment Directory Structure")
    print("=" * 50)
    
    tests = [
        ("Repository Structure", test_repository_structure),
        ("Netlify Configuration", test_netlify_config),
        ("Render Configuration", test_render_config),
        ("Build Commands", test_build_commands)
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
        print("🎉 All tests passed! Directory structure is correct for deployment.")
        print("\n📝 Next steps:")
        print("1. Commit and push the configuration files:")
        print("   git add netlify.toml render.yaml")
        print("   git commit -m 'Fix deployment: move config files to repository root'")
        print("   git push origin main")
        print("\n2. Trigger new deployments on Render and Netlify")
        print("3. Monitor build logs - should now succeed")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        print("\n🔧 Common fixes:")
        print("- Ensure you're running this from the repository root")
        print("- Check that netlify.toml and render.yaml are at the repository root")
        print("- Verify paths in config files point to StorySign_Platform/...")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())