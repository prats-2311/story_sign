#!/usr/bin/env python3
"""
Fix Render backend deployment issues
"""

import os
import subprocess
import sys
import yaml

def check_render_config():
    """Check render.yaml configuration"""
    print("🔧 Checking render.yaml configuration...")
    
    config_path = "render.yaml"
    
    if not os.path.exists(config_path):
        print("❌ render.yaml not found at repository root")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        service = config['services'][0]
        
        # Check build command
        build_cmd = service.get('buildCommand', '')
        if 'StorySign_Platform/backend' in build_cmd:
            print("✅ Build command has correct path")
        else:
            print(f"❌ Build command has wrong path: {build_cmd}")
            return False
        
        # Check start command
        start_cmd = service.get('startCommand', '')
        if 'StorySign_Platform/backend' in start_cmd:
            print("✅ Start command has correct path")
        else:
            print(f"❌ Start command has wrong path: {start_cmd}")
            return False
        
        # Check if using simplified API
        if 'main_api_simple:app' in start_cmd:
            print("✅ Using simplified API")
        else:
            print("❌ Not using simplified API")
            return False
        
        # Check if using minimal requirements
        if 'requirements_minimal.txt' in build_cmd:
            print("✅ Using minimal requirements")
        else:
            print("❌ Not using minimal requirements")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading render.yaml: {e}")
        return False

def check_backend_files():
    """Check if backend files exist"""
    print("📁 Checking backend files...")
    
    required_files = [
        "StorySign_Platform/backend/main_api_simple.py",
        "StorySign_Platform/backend/requirements_minimal.txt"
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

def check_duplicate_configs():
    """Check for duplicate configuration files"""
    print("🔍 Checking for duplicate configuration files...")
    
    duplicate_configs = [
        "StorySign_Platform/render.yaml",
        "StorySign_Platform/netlify.toml"
    ]
    
    found_duplicates = []
    for config_path in duplicate_configs:
        if os.path.exists(config_path):
            found_duplicates.append(config_path)
    
    if found_duplicates:
        print("⚠️  Found duplicate configuration files:")
        for config_path in found_duplicates:
            print(f"   - {config_path}")
        print("   These should be removed to avoid conflicts")
        return False
    else:
        print("✅ No duplicate configuration files found")
        return True

def test_backend_import():
    """Test if the simplified API can be imported"""
    print("🧪 Testing backend API import...")
    
    try:
        # Change to backend directory
        original_dir = os.getcwd()
        os.chdir("StorySign_Platform/backend")
        
        # Try to import the simplified API
        import sys
        sys.path.insert(0, '.')
        
        try:
            from main_api_simple import app
            print("✅ Simplified API imports successfully")
            result = True
        except ImportError as e:
            print(f"❌ Import error: {e}")
            result = False
        finally:
            # Restore directory and path
            os.chdir(original_dir)
            if '.' in sys.path:
                sys.path.remove('.')
        
        return result
        
    except Exception as e:
        print(f"❌ Error testing import: {e}")
        return False

def check_git_status():
    """Check if render.yaml is tracked by git"""
    print("📝 Checking Git status for render.yaml...")
    
    try:
        # Check if render.yaml is tracked
        result = subprocess.run(
            ["git", "ls-files", "render.yaml"],
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip():
            print("✅ render.yaml is tracked by Git")
        else:
            print("❌ render.yaml is not tracked by Git")
            return False
        
        # Check if there are uncommitted changes
        result = subprocess.run(
            ["git", "status", "--porcelain", "render.yaml"],
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip():
            print("⚠️  render.yaml has uncommitted changes")
            print("   Make sure to commit and push changes")
        else:
            print("✅ render.yaml is up to date in Git")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking Git status: {e}")
        return False

def create_render_troubleshooting_guide():
    """Create troubleshooting guide for Render deployment"""
    print("📋 Creating Render troubleshooting guide...")
    
    guide_content = """# Render Backend Deployment Troubleshooting

## Current Error Analysis

The error shows:
```
==> Running build command 'cd backend && pip install -r requirements.txt'...
bash: line 1: cd: backend: No such file or directory
```

This means Render is NOT using the render.yaml configuration file.

## Possible Causes & Solutions

### 1. Manual Configuration Override
**Problem**: Render dashboard has manual build/start commands that override render.yaml
**Solution**: 
1. Go to Render dashboard → Your service → Settings
2. Check "Build Command" and "Start Command" fields
3. If they contain manual commands, clear them to use render.yaml
4. Redeploy

### 2. Wrong Repository Root
**Problem**: Render is looking in wrong directory
**Solution**:
1. Verify render.yaml is at repository root (not inside StorySign_Platform/)
2. Ensure repository structure is correct

### 3. Render Not Finding render.yaml
**Problem**: Configuration file not detected
**Solution**:
1. Ensure render.yaml is committed and pushed to GitHub
2. Check file is at repository root
3. Verify YAML syntax is valid

### 4. Service Configuration Issue
**Problem**: Service was created with manual settings
**Solution**:
1. Delete current service in Render
2. Create new service using "Blueprint" option
3. Point to repository with render.yaml

## Correct Configuration

The render.yaml should contain:
```yaml
services:
  - type: web
    buildCommand: "cd StorySign_Platform/backend && pip install -r requirements_minimal.txt"
    startCommand: "cd StorySign_Platform/backend && gunicorn -w 4 -k uvicorn.workers.UvicornWorker main_api_simple:app --bind 0.0.0.0:$PORT"
```

## Verification Steps

1. Check render.yaml exists at repository root
2. Verify paths point to StorySign_Platform/backend
3. Confirm files exist: main_api_simple.py, requirements_minimal.txt
4. Ensure no duplicate render.yaml files
5. Check Render dashboard for manual overrides

## If Still Failing

Try creating the service as a "Blueprint" in Render:
1. Go to Render dashboard
2. Click "New +" → "Blueprint"
3. Connect to your GitHub repository
4. Render will automatically use render.yaml
"""
    
    with open("RENDER_TROUBLESHOOTING.md", "w") as f:
        f.write(guide_content)
    
    print("✅ Created RENDER_TROUBLESHOOTING.md")
    return True

def main():
    """Run all checks and fixes"""
    print("🚀 Fixing Render Backend Deployment")
    print("=" * 50)
    
    checks = [
        ("Check render.yaml config", check_render_config),
        ("Check backend files", check_backend_files),
        ("Check for duplicates", check_duplicate_configs),
        ("Test backend import", test_backend_import),
        ("Check Git status", check_git_status),
        ("Create troubleshooting guide", create_render_troubleshooting_guide)
    ]
    
    results = []
    for check_name, check_func in checks:
        print(f"\n{check_name}:")
        print("-" * 30)
        result = check_func()
        results.append((check_name, result))
    
    print("\n" + "=" * 50)
    print("📊 Check Results:")
    
    all_passed = True
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {check_name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All checks passed! Configuration looks correct.")
        print("\n📝 Next steps:")
        print("1. Commit any changes:")
        print("   git add render.yaml")
        print("   git commit -m 'Fix Render deployment: remove duplicate config'")
        print("   git push origin main")
        print("\n2. Check Render dashboard for manual overrides:")
        print("   - Go to your service → Settings")
        print("   - Clear any manual Build/Start commands")
        print("   - Let Render use render.yaml")
        print("\n3. Redeploy the service")
        print("\n4. If still failing, try creating a new 'Blueprint' service")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\n📋 See RENDER_TROUBLESHOOTING.md for detailed solutions")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())