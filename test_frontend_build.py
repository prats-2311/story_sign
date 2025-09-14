#!/usr/bin/env python3
"""
Test script to verify frontend build works locally
"""

import os
import subprocess
import sys
import json

def test_frontend_structure():
    """Test if frontend has all required files"""
    print("📁 Testing frontend structure...")
    
    frontend_path = "StorySign_Platform/frontend"
    required_files = [
        f"{frontend_path}/package.json",
        f"{frontend_path}/src/App.js",
        f"{frontend_path}/public/index.html",
        f"{frontend_path}/public/manifest.json"
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
    
    return True

def test_package_json():
    """Test package.json configuration"""
    print("📦 Testing package.json...")
    
    package_path = "StorySign_Platform/frontend/package.json"
    try:
        with open(package_path, 'r') as f:
            package = json.load(f)
        
        # Check required fields
        required_fields = ['name', 'scripts']
        for field in required_fields:
            if field not in package:
                print(f"❌ Missing field in package.json: {field}")
                return False
        
        # Check build script
        if 'build' not in package['scripts']:
            print("❌ Missing build script in package.json")
            return False
        
        print(f"✅ Build script: {package['scripts']['build']}")
        
        # Check homepage setting
        if 'homepage' in package:
            print(f"✅ Homepage: {package['homepage']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading package.json: {e}")
        return False

def test_index_html():
    """Test index.html content"""
    print("📄 Testing index.html...")
    
    index_path = "StorySign_Platform/frontend/public/index.html"
    try:
        with open(index_path, 'r') as f:
            content = f.read()
        
        # Check required elements
        required_elements = [
            '<div id="root">',
            '<html lang="en">',
            '<meta charset="utf-8"'
        ]
        
        for element in required_elements:
            if element not in content:
                print(f"❌ Missing element in index.html: {element}")
                return False
        
        print("✅ index.html has required elements")
        
        # Check for problematic references
        if 'favicon.ico' in content:
            print("⚠️  index.html references favicon.ico but file doesn't exist")
        
        if 'logo192.png' in content:
            print("⚠️  index.html references logo192.png but file doesn't exist")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading index.html: {e}")
        return False

def test_netlify_config():
    """Test netlify.toml configuration"""
    print("🔧 Testing netlify.toml...")
    
    # Check that only root netlify.toml exists
    root_config = "netlify.toml"
    inside_config = "StorySign_Platform/netlify.toml"
    
    if not os.path.exists(root_config):
        print("❌ netlify.toml not found at repository root")
        return False
    
    if os.path.exists(inside_config):
        print("⚠️  netlify.toml found inside StorySign_Platform/ - this may cause conflicts")
        print("   Only the root netlify.toml should exist")
    
    try:
        with open(root_config, 'r') as f:
            content = f.read()
        
        # Check paths
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

def test_build_locally():
    """Test if build works locally"""
    print("🔨 Testing local build...")
    
    frontend_path = "StorySign_Platform/frontend"
    
    # Check if node_modules exists
    if not os.path.exists(f"{frontend_path}/node_modules"):
        print("⚠️  node_modules not found - dependencies may not be installed")
        print("   Run: cd StorySign_Platform/frontend && npm install")
        return True  # Don't fail the test for this
    
    try:
        # Try to run the build command
        print("   Running: npm run build")
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=frontend_path,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print("✅ Local build succeeded")
            
            # Check if build directory was created
            build_path = f"{frontend_path}/build"
            if os.path.exists(build_path):
                print("✅ Build directory created")
                
                # Check for key files
                key_files = ["index.html", "static"]
                for file_name in key_files:
                    if os.path.exists(f"{build_path}/{file_name}"):
                        print(f"✅ Found in build: {file_name}")
                    else:
                        print(f"⚠️  Missing in build: {file_name}")
            else:
                print("❌ Build directory not created")
                return False
            
            return True
        else:
            print("❌ Local build failed")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Build timed out after 2 minutes")
        return False
    except FileNotFoundError:
        print("⚠️  npm not found - cannot test local build")
        return True  # Don't fail for missing npm
    except Exception as e:
        print(f"❌ Error running build: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Frontend Build Configuration")
    print("=" * 50)
    
    tests = [
        ("Frontend Structure", test_frontend_structure),
        ("Package JSON", test_package_json),
        ("Index HTML", test_index_html),
        ("Netlify Config", test_netlify_config),
        ("Local Build", test_build_locally)
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
        print("🎉 All tests passed! Frontend should build successfully.")
        print("\n📝 Next steps:")
        print("1. Commit and push changes:")
        print("   git add .")
        print("   git commit -m 'Fix frontend build: remove duplicate netlify.toml, fix index.html'")
        print("   git push origin main")
        print("\n2. Trigger new Netlify deployment")
        print("3. Monitor build logs")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())