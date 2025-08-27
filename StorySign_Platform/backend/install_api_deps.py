#!/usr/bin/env python3
"""
Install API dependencies for StorySign ASL Platform
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {command}")
        print(f"   Error: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True


def install_dependencies():
    """Install all required dependencies"""
    backend_dir = Path(__file__).parent
    requirements_file = backend_dir / "requirements_api.txt"
    
    if not requirements_file.exists():
        print(f"❌ Requirements file not found: {requirements_file}")
        return False
    
    print("🚀 Installing StorySign API dependencies...")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Upgrade pip first
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install wheel for better package building
    if not run_command(f"{sys.executable} -m pip install wheel", "Installing wheel"):
        return False
    
    # Install main requirements
    if not run_command(
        f"{sys.executable} -m pip install -r {requirements_file}",
        "Installing API requirements"
    ):
        return False
    
    # Install additional development tools
    dev_packages = [
        "strawberry-graphql[fastapi]",  # Ensure GraphQL support
        "python-jose[cryptography]",    # JWT support
        "passlib[bcrypt]",              # Password hashing
        "httpx",                        # HTTP client for testing
        "pytest-asyncio",               # Async testing
    ]
    
    for package in dev_packages:
        if not run_command(
            f"{sys.executable} -m pip install {package}",
            f"Installing {package}"
        ):
            print(f"⚠️  Warning: Failed to install {package}, continuing...")
    
    print("=" * 60)
    print("✅ All dependencies installed successfully!")
    
    # Verify key imports
    print("\n🔍 Verifying key imports...")
    
    imports_to_test = [
        ("fastapi", "FastAPI"),
        ("strawberry", "GraphQL support"),
        ("jose", "JWT support"),
        ("passlib", "Password hashing"),
        ("httpx", "HTTP client"),
        ("sqlalchemy", "Database ORM"),
    ]
    
    all_imports_ok = True
    for module, description in imports_to_test:
        try:
            __import__(module)
            print(f"✅ {description} - OK")
        except ImportError as e:
            print(f"❌ {description} - FAILED: {e}")
            all_imports_ok = False
    
    if all_imports_ok:
        print("\n🎉 All imports verified successfully!")
        print("\n📚 Next steps:")
        print("   1. Configure your database connection in config.py")
        print("   2. Run database migrations: python -m alembic upgrade head")
        print("   3. Start the API server: python main_api.py")
        print("   4. Run tests: python run_api_tests.py")
        print("   5. View API docs: http://localhost:8000/docs")
        return True
    else:
        print("\n⚠️  Some imports failed. Please check the error messages above.")
        return False


def main():
    """Main installation function"""
    try:
        success = install_dependencies()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Installation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Installation failed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()