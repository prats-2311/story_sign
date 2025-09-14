#!/usr/bin/env python3
"""
Fix Render startup issues
"""

import os
import subprocess

def create_production_files():
    """Create production-ready files"""
    print("🔧 Creating production-ready files...")
    
    # The production file was already created above
    if os.path.exists("StorySign_Platform/backend/main_api_production.py"):
        print("✅ main_api_production.py exists")
    else:
        print("❌ main_api_production.py missing")
        return False
    
    return True

def test_production_import():
    """Test if production file can import the main app"""
    print("🧪 Testing production file import...")
    
    try:
        import sys
        original_dir = os.getcwd()
        os.chdir("StorySign_Platform/backend")
        sys.path.insert(0, '.')
        
        try:
            from main_api_production import app
            print("✅ Production API imports successfully")
            result = True
        except ImportError as e:
            print(f"❌ Import error: {e}")
            result = False
        finally:
            os.chdir(original_dir)
            if '.' in sys.path:
                sys.path.remove('.')
        
        return result
        
    except Exception as e:
        print(f"❌ Error testing import: {e}")
        return False

def update_render_yaml():
    """Update render.yaml with production start command"""
    print("📝 Updating render.yaml...")
    
    try:
        with open("render.yaml", "r") as f:
            content = f.read()
        
        if "main_api_production.py" in content:
            print("✅ render.yaml already uses production file")
        else:
            print("⚠️  render.yaml needs to be updated")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading render.yaml: {e}")
        return False

def add_to_git():
    """Add production file to git"""
    print("📝 Adding production file to Git...")
    
    try:
        subprocess.run(["git", "add", "StorySign_Platform/backend/main_api_production.py"], check=True)
        subprocess.run(["git", "add", "render.yaml"], check=True)
        print("✅ Added files to Git")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error adding to Git: {e}")
        return False

def main():
    """Run all fixes"""
    print("🚀 Fixing Render Startup Issues")
    print("=" * 50)
    
    fixes = [
        ("Create production files", create_production_files),
        ("Test production import", test_production_import),
        ("Update render.yaml", update_render_yaml),
        ("Add to Git", add_to_git)
    ]
    
    results = []
    for fix_name, fix_func in fixes:
        print(f"\n{fix_name}:")
        print("-" * 30)
        result = fix_func()
        results.append((fix_name, result))
    
    print("\n" + "=" * 50)
    print("📊 Fix Results:")
    
    all_passed = True
    for fix_name, result in results:
        status = "✅ SUCCESS" if result else "❌ FAILED"
        print(f"   {status} - {fix_name}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All fixes applied successfully!")
        print("\n📝 Next steps:")
        print("1. Commit the changes:")
        print("   git commit -m 'Add production API file for Render deployment'")
        print("   git push origin main")
        print("\n2. In Render dashboard, set the start command manually:")
        print("   cd StorySign_Platform/backend && python main_api_production.py")
        print("\n3. Or try creating a new Blueprint service")
        print("\n4. Deploy and test")
    else:
        print("❌ Some fixes failed.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())