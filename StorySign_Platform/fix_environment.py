#!/usr/bin/env python3
"""
Environment Fix Script for StorySign
Addresses common environment and installation issues
"""

import subprocess
import sys
import os
import platform
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnvironmentFixer:
    """Fix common environment and installation issues"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        self.python_executable = sys.executable
        
    def check_environment_conflicts(self):
        """Check for environment conflicts"""
        logger.info("🔍 Checking for environment conflicts...")
        
        issues = []
        
        # Check if both venv and conda are active
        venv_active = os.environ.get("VIRTUAL_ENV") is not None
        conda_active = os.environ.get("CONDA_DEFAULT_ENV") is not None
        
        if venv_active and conda_active:
            issues.append("Both virtual environment and conda environment are active")
            logger.warning("⚠️  Conflict: Both .venv and conda environment active")
            logger.info(f"   Virtual Env: {os.environ.get('VIRTUAL_ENV')}")
            logger.info(f"   Conda Env: {os.environ.get('CONDA_DEFAULT_ENV')}")
        
        # Check Python version compatibility
        if sys.version_info >= (3, 13):
            issues.append(f"Python {self.python_version} is very new - some packages may not be compatible")
            logger.warning(f"⚠️  Python {self.python_version} is very new - consider using Python 3.9-3.11")
        
        # Check if using the right Python executable
        if "mediapipe_env" not in self.python_executable and conda_active:
            issues.append("Python executable doesn't match conda environment")
            logger.warning("⚠️  Python executable may not be from mediapipe_env")
        
        return issues
    
    def fix_mediapipe_installation(self):
        """Fix MediaPipe installation issues"""
        logger.info("🔧 Fixing MediaPipe installation...")
        
        # Try different MediaPipe installation methods
        methods = [
            # Method 1: Standard pip install
            ["pip", "install", "mediapipe"],
            
            # Method 2: Specific version that's known to work
            ["pip", "install", "mediapipe==0.10.9"],
            
            # Method 3: Pre-release version for newer Python
            ["pip", "install", "--pre", "mediapipe"],
            
            # Method 4: Force reinstall
            ["pip", "install", "--force-reinstall", "--no-cache-dir", "mediapipe==0.10.9"],
            
            # Method 5: Use conda-forge
            ["conda", "install", "-c", "conda-forge", "mediapipe", "-y"]
        ]
        
        for i, method in enumerate(methods, 1):
            try:
                logger.info(f"Trying method {i}: {' '.join(method)}")
                result = subprocess.run(method, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    logger.info(f"✅ MediaPipe installed successfully with method {i}")
                    return True
                else:
                    logger.debug(f"Method {i} failed: {result.stderr}")
                    
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                logger.debug(f"Method {i} failed: {e}")
                continue
        
        logger.error("❌ All MediaPipe installation methods failed")
        return False
    
    def fix_opencv_webp_support(self):
        """Fix OpenCV WebP support"""
        logger.info("🔧 Fixing OpenCV WebP support...")
        
        try:
            # First, check if WebP is supported
            import cv2
            
            # Test WebP support
            test_img = [[0, 0, 0]]
            try:
                cv2.imencode('.webp', test_img)
                logger.info("✅ OpenCV already has WebP support")
                return True
            except:
                logger.info("❌ OpenCV doesn't have WebP support")
        
            # Try to install opencv-contrib-python which has more codecs
            logger.info("Installing opencv-contrib-python for better codec support...")
            
            # Remove existing opencv first
            subprocess.run(["pip", "uninstall", "-y", "opencv-python"], 
                         capture_output=True)
            
            # Install contrib version
            result = subprocess.run(["pip", "install", "opencv-contrib-python>=4.8.0"], 
                                  capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info("✅ opencv-contrib-python installed")
                
                # Test WebP support again
                import importlib
                importlib.reload(cv2)
                
                try:
                    cv2.imencode('.webp', test_img)
                    logger.info("✅ WebP support now available")
                    return True
                except:
                    logger.warning("⚠️  WebP still not supported, will use JPEG fallback")
                    return False
            else:
                logger.warning("⚠️  opencv-contrib-python installation failed")
                return False
                
        except Exception as e:
            logger.error(f"Error fixing OpenCV WebP support: {e}")
            return False
    
    def create_clean_environment_script(self):
        """Create script to set up clean environment"""
        script_content = '''#!/bin/bash
# Clean Environment Setup for StorySign

echo "🧹 Setting up clean environment for StorySign..."

# Deactivate any virtual environment
if [[ -n "$VIRTUAL_ENV" ]]; then
    echo "Deactivating virtual environment: $VIRTUAL_ENV"
    deactivate 2>/dev/null || true
fi

# Check if mediapipe_env exists
if conda env list | grep -q "mediapipe_env"; then
    echo "✅ mediapipe_env exists"
else
    echo "📦 Creating mediapipe_env with Python 3.10 (more compatible)..."
    conda create -n mediapipe_env python=3.10 -y
fi

# Activate mediapipe_env
echo "🔄 Activating mediapipe_env..."
conda activate mediapipe_env

# Verify environment
echo "🔍 Environment verification:"
echo "  Python: $(which python)"
echo "  Pip: $(which pip)"
echo "  Environment: $CONDA_DEFAULT_ENV"

# Install essential packages
echo "📦 Installing essential packages..."
pip install --upgrade pip setuptools wheel

# Install core packages one by one with error handling
packages=(
    "numpy>=1.21.0"
    "opencv-contrib-python>=4.8.0"
    "mediapipe==0.10.9"
    "fastapi>=0.100.0"
    "uvicorn>=0.23.0"
    "websockets>=11.0"
    "pydantic>=2.0.0"
    "PyYAML>=6.0"
    "psutil>=5.9.0"
)

for package in "${packages[@]}"; do
    echo "Installing $package..."
    if pip install "$package"; then
        echo "✅ $package installed successfully"
    else
        echo "❌ Failed to install $package"
    fi
done

echo "🎉 Clean environment setup complete!"
echo "Now run: python fix_environment.py"
'''
        
        with open("setup_clean_environment.sh", "w") as f:
            f.write(script_content)
        
        os.chmod("setup_clean_environment.sh", 0o755)
        logger.info("📝 Created setup_clean_environment.sh")
    
    def test_critical_imports(self):
        """Test if critical packages can be imported"""
        logger.info("🧪 Testing critical package imports...")
        
        critical_packages = [
            ("cv2", "OpenCV"),
            ("numpy", "NumPy"),
            ("mediapipe", "MediaPipe"),
            ("fastapi", "FastAPI"),
            ("websockets", "WebSockets")
        ]
        
        results = {}
        for package, name in critical_packages:
            try:
                __import__(package)
                logger.info(f"✅ {name} imports successfully")
                results[package] = True
            except ImportError as e:
                logger.error(f"❌ {name} import failed: {e}")
                results[package] = False
        
        return results
    
    def run_comprehensive_fix(self):
        """Run comprehensive environment fix"""
        logger.info("🔧 Starting comprehensive environment fix...")
        
        # Check for conflicts
        issues = self.check_environment_conflicts()
        
        if issues:
            logger.warning("⚠️  Environment issues detected:")
            for issue in issues:
                logger.warning(f"   • {issue}")
            
            logger.info("\n💡 RECOMMENDED SOLUTION:")
            logger.info("1. Exit all Python processes")
            logger.info("2. Run: ./setup_clean_environment.sh")
            logger.info("3. Then run: python fix_environment.py")
            
            # Create the clean setup script
            self.create_clean_environment_script()
            
            response = input("\nWould you like to continue fixing the current environment? (y/N): ").lower().strip()
            if response not in ['y', 'yes']:
                logger.info("Environment fix cancelled. Use setup_clean_environment.sh for a clean setup.")
                return False
        
        # Fix MediaPipe
        if not self.fix_mediapipe_installation():
            logger.error("❌ Could not fix MediaPipe installation")
            return False
        
        # Fix OpenCV WebP support
        self.fix_opencv_webp_support()
        
        # Test imports
        results = self.test_critical_imports()
        
        # Check success rate
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        if success_count == total_count:
            logger.info("✅ All critical packages are working!")
            return True
        elif success_count >= total_count * 0.8:
            logger.info(f"✅ Most packages working ({success_count}/{total_count})")
            return True
        else:
            logger.error(f"❌ Too many packages failed ({success_count}/{total_count})")
            return False

def main():
    """Main fix function"""
    print("🔧 StorySign Environment Fixer")
    print("=" * 40)
    
    fixer = EnvironmentFixer()
    success = fixer.run_comprehensive_fix()
    
    if success:
        print("\n✅ Environment fixes completed!")
        print("\nNext steps:")
        print("1. python benchmark_optimizations.py  # Test performance")
        print("2. cd backend && python main.py       # Start backend")
        print("3. cd frontend && npm start           # Start frontend")
        return 0
    else:
        print("\n❌ Environment fixes failed!")
        print("\nTry the clean setup:")
        print("1. ./setup_clean_environment.sh")
        print("2. python fix_environment.py")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())