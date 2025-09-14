#!/usr/bin/env python3
"""
Test script to validate Netlify configuration
"""

import os
import json
import subprocess
import sys

def test_netlify_toml():
    """Test if netlify.toml is valid"""
    print("📋 Testing netlify.toml configuration...")
    
    config_file = 'StorySign_Platform/netlify.toml'
    if not os.path.exists(config_file):
        print(f"❌ netlify.toml not found: {config_file}")
        return False
    
    try:
        # Try to parse TOML
        import toml
        with open(config_file, 'r') as f:
            config = toml.load(f)
        
        # Check required sections
        if 'build' not in config:
            print("❌ Missing [build] section in netlify.toml")
            return False
        
        build = config['build']
        required_keys = ['base', 'command', 'publish']
        
        for key in required_keys:
            if key not in build:
                print(f"❌ Missing required key in [build]: {key}")
                return False
        
        # Check paths
        if 'StorySign_Platform/frontend' not in build['base']:
            print(f"❌ Incorrect base directory: {build['base']}")
            return False
        
        print("✅ netlify.toml configuration is valid")
        print(f"   Base: {build['base']}")
        print(f"   Command: {build['command']}")
        print(f"   Publish: {build['publish']}")
        
        return True
        
    except ImportError:
        print("⚠️  toml package not available, skipping detailed validation")
        print("✅ netlify.toml file exists")
        return True
    except Exception as e:
        print(f"❌ Error parsing netlify.toml: {e}")
        return False

def test_frontend_structure():
    """Test if frontend directory structure is correct"""
    print("📁 Testing frontend directory structure...")
    
    base_dir = 'StorySign_Platform/frontend'
    required_files = [
        f'{base_dir}/package.json',
        f'{base_dir}/src/App.js',
        f'{base_dir}/public/index.html'
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
    
    print("✅ Frontend structure looks good")
    return True

def test_package_json():
    """Test if package.json has required scripts"""
    print("📦 Testing package.json...")
    
    package_file = 'StorySign_Platform/frontend/package.json'
    if not os.path.exists(package_file):
        print(f"❌ package.json not found: {package_file}")
        return False
    
    try:
        with open(package_file, 'r') as f:
            package = json.load(f)
        
        # Check required scripts
        if 'scripts' not in package:
            print("❌ No scripts section in package.json")
            return False
        
        scripts = package['scripts']
        required_scripts = ['build', 'start']
        
        for script in required_scripts:
            if script not in scripts:
                print(f"❌ Missing script: {script}")
                return False
        
        print("✅ package.json has required scripts")
        print(f"   Build: {scripts['build']}")
        print(f"   Start: {scripts['start']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading package.json: {e}")
        return False

def test_environment_files():
    """Test if environment files are properly configured"""
    print("🔧 Testing environment configuration...")
    
    env_files = [
        'StorySign_Platform/frontend/.env.production',
        'StorySign_Platform/frontend/.env.development'
    ]
    
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"✅ Found: {env_file}")
            
            # Check content
            try:
                with open(env_file, 'r') as f:
                    content = f.read()
                
                if 'REACT_APP_' in content:
                    print(f"   Contains React environment variables")
                else:
                    print(f"⚠️  No React environment variables found")
                    
            except Exception as e:
                print(f"⚠️  Could not read {env_file}: {e}")
        else:
            print(f"⚠️  Environment file not found: {env_file}")
    
    return True

def test_api_config():
    """Test if API configuration is properly set up"""
    print("🔗 Testing API configuration...")
    
    api_config_file = 'StorySign_Platform/frontend/src/config/api.js'
    if not os.path.exists(api_config_file):
        print(f"❌ API config not found: {api_config_file}")
        return False
    
    try:
        with open(api_config_file, 'r') as f:
            content = f.read()
        
        # Check if it uses environment variables
        if 'process.env.REACT_APP_API_URL' in content:
            print("✅ API config uses environment variables")
        else:
            print("⚠️  API config might be hardcoded")
        
        # Check if it has production logic
        if 'production' in content:
            print("✅ API config has production logic")
        else:
            print("⚠️  API config might not handle production properly")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading API config: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Netlify Deployment Configuration")
    print("=" * 50)
    
    tests = [
        ("Netlify TOML", test_netlify_toml),
        ("Frontend Structure", test_frontend_structure),
        ("Package JSON", test_package_json),
        ("Environment Files", test_environment_files),
        ("API Configuration", test_api_config)
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
        print("🎉 All tests passed! Ready for Netlify deployment.")
        print("\n📝 Next steps:")
        print("1. Deploy backend to Render first")
        print("2. Get backend URL from Render")
        print("3. Set environment variables in Netlify UI:")
        print("   - REACT_APP_API_URL=https://your-backend.onrender.com")
        print("   - REACT_APP_WS_URL=wss://your-backend.onrender.com")
        print("   - REACT_APP_ENVIRONMENT=production")
        print("4. Deploy frontend to Netlify")
        print("5. Test the deployment")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return 1
    
    return 0

if __name__ == "__main__":
    # Try to install toml if not available
    try:
        import toml
    except ImportError:
        print("Installing toml package for validation...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "toml"])
            import toml
        except:
            print("Could not install toml package, continuing without detailed validation...")
    
    exit(main())