#!/usr/bin/env python3
"""
Comprehensive fix for frontend deployment issues
"""

import os
import subprocess
import sys

def check_git_status():
    """Check if public files are tracked by git"""
    print("🔍 Checking Git status for public files...")
    
    try:
        # Check if public directory is tracked
        result = subprocess.run(
            ["git", "ls-files", "StorySign_Platform/frontend/public/"],
            capture_output=True,
            text=True
        )
        
        tracked_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
        
        print(f"📁 Tracked public files: {len(tracked_files)}")
        for file in tracked_files:
            if file:
                print(f"   ✅ {file}")
        
        # Check if files are untracked
        result = subprocess.run(
            ["git", "status", "--porcelain", "StorySign_Platform/frontend/public/"],
            capture_output=True,
            text=True
        )
        
        untracked_files = []
        for line in result.stdout.strip().split('\n'):
            if line.startswith('??'):
                untracked_files.append(line[3:])
        
        if untracked_files:
            print(f"⚠️  Untracked public files: {len(untracked_files)}")
            for file in untracked_files:
                print(f"   ❌ {file}")
            return False
        
        if not tracked_files:
            print("❌ No public files are tracked by Git!")
            return False
        
        print("✅ Public files are properly tracked by Git")
        return True
        
    except Exception as e:
        print(f"❌ Error checking Git status: {e}")
        return False

def fix_gitignore():
    """Fix gitignore to allow public directory"""
    print("🔧 Fixing .gitignore...")
    
    gitignore_path = "StorySign_Platform/.gitignore"
    
    try:
        with open(gitignore_path, 'r') as f:
            content = f.read()
        
        # Check if public is being ignored
        if '\npublic\n' in content or content.startswith('public\n'):
            print("⚠️  Found 'public' in .gitignore - this blocks frontend/public/")
            
            # Replace standalone 'public' with a comment
            content = content.replace('\npublic\n', '\n# public  # Commented out - we need frontend/public for React\n')
            content = content.replace('public\n', '# public  # Commented out - we need frontend/public for React\n')
            
            with open(gitignore_path, 'w') as f:
                f.write(content)
            
            print("✅ Fixed .gitignore to allow frontend/public directory")
            return True
        else:
            print("✅ .gitignore is not blocking public directory")
            return True
            
    except Exception as e:
        print(f"❌ Error fixing .gitignore: {e}")
        return False

def create_public_files():
    """Ensure all required public files exist"""
    print("📁 Creating/verifying public files...")
    
    public_dir = "StorySign_Platform/frontend/public"
    
    # Ensure directory exists
    os.makedirs(public_dir, exist_ok=True)
    
    # Create index.html
    index_html = f"{public_dir}/index.html"
    if not os.path.exists(index_html):
        with open(index_html, 'w') as f:
            f.write('''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta
      name="description"
      content="StorySign ASL Platform - Learn American Sign Language through interactive stories"
    />
    <link rel="manifest" href="%PUBLIC_URL%/manifest.json" />
    <title>StorySign ASL Platform</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>''')
        print("✅ Created index.html")
    else:
        print("✅ index.html exists")
    
    # Create manifest.json
    manifest_json = f"{public_dir}/manifest.json"
    if not os.path.exists(manifest_json):
        with open(manifest_json, 'w') as f:
            f.write('''{
  "short_name": "StorySign",
  "name": "StorySign ASL Platform",
  "start_url": ".",
  "display": "standalone",
  "theme_color": "#000000",
  "background_color": "#ffffff"
}''')
        print("✅ Created manifest.json")
    else:
        print("✅ manifest.json exists")
    
    return True

def test_netlify_config():
    """Test netlify.toml configuration"""
    print("🔧 Testing netlify.toml...")
    
    config_path = "netlify.toml"
    
    try:
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Check for correct paths
        if 'base = "StorySign_Platform/frontend"' in content:
            print("✅ Correct base directory")
        else:
            print("❌ Incorrect base directory")
            return False
        
        if 'publish = "build"' in content:
            print("✅ Correct publish directory (relative)")
        else:
            print("❌ Incorrect publish directory")
            return False
        
        if 'ESLINT_NO_DEV_ERRORS = "true"' in content:
            print("✅ ESLint errors disabled")
        else:
            print("❌ ESLint errors not disabled")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading netlify.toml: {e}")
        return False

def add_files_to_git():
    """Add public files to git"""
    print("📝 Adding files to Git...")
    
    try:
        # Add public directory
        subprocess.run(["git", "add", "StorySign_Platform/frontend/public/"], check=True)
        print("✅ Added public directory to Git")
        
        # Add netlify.toml
        subprocess.run(["git", "add", "netlify.toml"], check=True)
        print("✅ Added netlify.toml to Git")
        
        # Add fixed gitignore
        subprocess.run(["git", "add", "StorySign_Platform/.gitignore"], check=True)
        print("✅ Added fixed .gitignore to Git")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error adding files to Git: {e}")
        return False

def main():
    """Run all fixes"""
    print("🚀 Fixing Frontend Deployment Issues")
    print("=" * 50)
    
    fixes = [
        ("Fix .gitignore", fix_gitignore),
        ("Create public files", create_public_files),
        ("Test Netlify config", test_netlify_config),
        ("Add files to Git", add_files_to_git),
        ("Check Git status", check_git_status)
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
        print("   git commit -m 'Fix frontend deployment: unignore public dir, fix paths'")
        print("   git push origin main")
        print("\n2. Trigger new Netlify deployment")
        print("3. Monitor build logs - should now find index.html")
    else:
        print("❌ Some fixes failed. Please address the issues above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())