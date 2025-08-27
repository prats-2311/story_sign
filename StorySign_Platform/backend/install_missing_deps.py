#!/usr/bin/env python3
"""
Install missing dependencies for StorySign API
"""

import subprocess
import sys

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """Install missing dependencies"""
    print("📦 Installing missing StorySign API dependencies...")
    
    # Required packages for the new API features
    packages = [
        "pydantic[email]",  # For email validation
        "strawberry-graphql[fastapi]",  # For GraphQL
        "python-jose[cryptography]",  # For JWT
        "passlib[bcrypt]",  # For password hashing
        "httpx",  # For HTTP client
    ]
    
    success_count = 0
    
    for package in packages:
        print(f"\n📥 Installing {package}...")
        if install_package(package):
            print(f"✅ {package} installed successfully")
            success_count += 1
        else:
            print(f"❌ Failed to install {package}")
    
    print(f"\n📊 Installation Summary:")
    print(f"  Successful: {success_count}/{len(packages)}")
    
    if success_count == len(packages):
        print("\n🎉 All dependencies installed successfully!")
        print("\n📝 Next steps:")
        print("  1. Test the API: python test_api_startup.py")
        print("  2. Start the server: python main.py")
        print("  3. Or use the new API server: python main_api.py")
        return True
    else:
        print(f"\n⚠️  {len(packages) - success_count} packages failed to install")
        print("The API will still work but some features may be limited")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)