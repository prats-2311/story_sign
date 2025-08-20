#!/usr/bin/env python3
"""
Environment Setup Script for StorySign Advanced Optimizations
Ensures all packages are installed in the correct conda environment
"""

import subprocess
import sys
import os
import platform
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnvironmentSetup:
    """Setup and verify conda environment for StorySign optimizations"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.python_executable = sys.executable
        self.environment_info = self._get_environment_info()
        
    def _get_environment_info(self):
        """Get current environment information"""
        info = {
            "python_executable": self.python_executable,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "is_conda": "conda" in self.python_executable.lower() or "CONDA_DEFAULT_ENV" in os.environ,
            "conda_env": os.environ.get("CONDA_DEFAULT_ENV", "unknown"),
            "virtual_env": os.environ.get("VIRTUAL_ENV", None),
            "pip_executable": None
        }
        
        # Find pip executable in the same environment
        pip_candidates = [
            os.path.join(os.path.dirname(self.python_executable), "pip"),
            os.path.join(os.path.dirname(self.python_executable), "pip3"),
            "pip3", "pip"
        ]
        
        for pip_cmd in pip_candidates:
            try:
                result = subprocess.run([pip_cmd, "--version"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and "python" in result.stdout.lower():
                    info["pip_executable"] = pip_cmd
                    break
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        return info
    
    def print_environment_info(self):
        """Print current environment information"""
        print("🐍 PYTHON ENVIRONMENT INFORMATION")
        print("=" * 50)
        print(f"Python Executable:    {self.environment_info['python_executable']}")
        print(f"Python Version:       {self.environment_info['python_version']}")
        print(f"Is Conda Environment: {'✅ Yes' if self.environment_info['is_conda'] else '❌ No'}")
        
        if self.environment_info['is_conda']:
            print(f"Conda Environment:    {self.environment_info['conda_env']}")
        
        if self.environment_info['virtual_env']:
            print(f"Virtual Environment:  {self.environment_info['virtual_env']}")
        
        print(f"Pip Executable:       {self.environment_info['pip_executable']}")
        print()
    
    def verify_mediapipe_env(self):
        """Verify we're in the mediapipe_env environment"""
        conda_env = self.environment_info.get('conda_env', '').lower()
        
        if 'mediapipe' in conda_env:
            logger.info("✅ Running in MediaPipe conda environment")
            return True
        elif self.environment_info['is_conda']:
            logger.warning(f"⚠️  Running in conda environment '{conda_env}' but not 'mediapipe_env'")
            print(f"\n⚠️  WARNING: You're in conda environment '{conda_env}'")
            print("For best results, activate the mediapipe_env environment:")
            print("   conda activate mediapipe_env")
            print("   python setup_environment.py")
            
            response = input("\nContinue with current environment? (y/N): ").lower().strip()
            return response in ['y', 'yes']
        else:
            logger.warning("⚠️  Not running in a conda environment")
            print("\n⚠️  WARNING: Not in a conda environment")
            print("For best results, create and activate mediapipe_env:")
            print("   conda create -n mediapipe_env python=3.9")
            print("   conda activate mediapipe_env")
            print("   python setup_environment.py")
            
            response = input("\nContinue anyway? (y/N): ").lower().strip()
            return response in ['y', 'yes']
    
    def install_base_requirements(self):
        """Install base requirements first"""
        logger.info("📦 Installing base requirements...")
        
        base_packages = [
            "pip>=23.0",
            "setuptools>=65.0",
            "wheel>=0.38.0",
            "opencv-python>=4.8.0",
            "numpy>=1.21.0",
            "mediapipe>=0.10.0",
            "fastapi>=0.100.0",
            "uvicorn>=0.23.0",
            "websockets>=11.0",
            "pydantic>=2.0.0",
            "PyYAML>=6.0",
            "psutil>=5.9.0"
        ]
        
        pip_cmd = self.environment_info['pip_executable'] or 'pip'
        
        for package in base_packages:
            try:
                logger.info(f"Installing {package}...")
                subprocess.check_call([pip_cmd, "install", package], 
                                    stdout=subprocess.DEVNULL, 
                                    stderr=subprocess.PIPE)
                logger.info(f"✅ {package} installed successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Failed to install {package}: {e}")
                return False
        
        return True
    
    def install_advanced_optimizations(self):
        """Install advanced optimization packages"""
        logger.info("🚀 Installing advanced optimization packages...")
        
        pip_cmd = self.environment_info['pip_executable'] or 'pip'
        
        # Install from requirements file if it exists
        requirements_file = Path("requirements_advanced.txt")
        if requirements_file.exists():
            try:
                logger.info("Installing from requirements_advanced.txt...")
                subprocess.check_call([pip_cmd, "install", "-r", str(requirements_file)])
                logger.info("✅ Advanced requirements installed successfully")
                return True
            except subprocess.CalledProcessError as e:
                logger.warning(f"⚠️  Some advanced packages failed to install: {e}")
                logger.info("Continuing with individual package installation...")
        
        # Install individual packages with error handling
        advanced_packages = [
            ("PyTurboJPEG", "Ultra-fast JPEG processing", True),
            ("av", "Advanced video codecs", True),
            ("lz4", "Ultra-fast compression", True),
            ("zstandard", "Facebook's Zstandard compression", True),
            ("pillow-heif", "HEIF/HEIC image format", True),
            ("Pillow>=10.0.0", "Enhanced image processing", False),
            ("numba", "JIT compilation for speed", True),
            ("uvloop", "Fast asyncio event loop", True),
            ("memory-profiler", "Memory optimization", True),
            ("py-spy", "Performance profiling", True),
            ("gpustat", "GPU monitoring", True),
        ]
        
        success_count = 0
        for package_info in advanced_packages:
            if len(package_info) == 3:
                package, description, optional = package_info
            else:
                package, description = package_info
                optional = False
            
            try:
                logger.info(f"Installing {package} ({description})...")
                subprocess.check_call([pip_cmd, "install", package], 
                                    stdout=subprocess.DEVNULL, 
                                    stderr=subprocess.PIPE)
                logger.info(f"✅ {package} installed successfully")
                success_count += 1
            except subprocess.CalledProcessError as e:
                if optional:
                    logger.warning(f"⚠️  Optional package {package} failed to install")
                else:
                    logger.error(f"❌ Required package {package} failed to install: {e}")
        
        logger.info(f"📊 Advanced optimizations: {success_count}/{len(advanced_packages)} packages installed")
        return success_count > len(advanced_packages) // 2  # At least half should succeed
    
    def install_gpu_acceleration(self):
        """Install GPU acceleration packages"""
        logger.info("🎮 Installing GPU acceleration packages...")
        
        pip_cmd = self.environment_info['pip_executable'] or 'pip'
        gpu_packages_installed = 0
        
        # Try CUDA packages (CuPy)
        cuda_packages = ["cupy-cuda12x", "cupy-cuda11x", "cupy-cuda10x"]
        for cuda_package in cuda_packages:
            try:
                logger.info(f"Trying {cuda_package}...")
                subprocess.check_call([pip_cmd, "install", cuda_package], 
                                    stdout=subprocess.DEVNULL, 
                                    stderr=subprocess.PIPE, 
                                    timeout=300)  # 5 minute timeout
                logger.info(f"✅ {cuda_package} installed successfully")
                gpu_packages_installed += 1
                break  # Only need one CUDA version
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                logger.debug(f"❌ {cuda_package} installation failed")
                continue
        
        # Try OpenCL
        if self.system != "windows":  # OpenCL installation can be tricky on Windows
            try:
                logger.info("Installing PyOpenCL...")
                subprocess.check_call([pip_cmd, "install", "pyopencl"], 
                                    stdout=subprocess.DEVNULL, 
                                    stderr=subprocess.PIPE,
                                    timeout=180)
                logger.info("✅ PyOpenCL installed successfully")
                gpu_packages_installed += 1
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                logger.warning("⚠️  PyOpenCL installation failed")
        
        # Try Intel OpenVINO
        if self.system != "windows":
            try:
                logger.info("Installing OpenVINO...")
                subprocess.check_call([pip_cmd, "install", "openvino"], 
                                    stdout=subprocess.DEVNULL, 
                                    stderr=subprocess.PIPE,
                                    timeout=300)
                logger.info("✅ OpenVINO installed successfully")
                gpu_packages_installed += 1
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                logger.warning("⚠️  OpenVINO installation failed")
        
        if gpu_packages_installed > 0:
            logger.info(f"✅ GPU acceleration: {gpu_packages_installed} packages installed")
            return True
        else:
            logger.warning("⚠️  No GPU acceleration packages could be installed")
            logger.info("The system will work with CPU-only optimizations")
            return False
    
    def verify_installation(self):
        """Verify that key packages are working in the current environment"""
        logger.info("🔍 Verifying installation in current environment...")
        
        test_imports = [
            ("cv2", "OpenCV", False),
            ("numpy", "NumPy", False),
            ("mediapipe", "MediaPipe", False),
            ("fastapi", "FastAPI", False),
            ("websockets", "WebSockets", False),
            ("cupy", "CuPy (CUDA)", True),
            ("pyopencl", "PyOpenCL", True),
            ("turbojpeg", "TurboJPEG", True),
            ("av", "PyAV", True),
            ("lz4", "LZ4", True),
            ("zstandard", "Zstandard", True),
            ("numba", "Numba", True),
        ]
        
        results = {}
        required_working = 0
        optional_working = 0
        
        for import_name, display_name, optional in test_imports:
            try:
                __import__(import_name)
                logger.info(f"✅ {display_name} is working")
                results[import_name] = True
                if optional:
                    optional_working += 1
                else:
                    required_working += 1
            except ImportError:
                if optional:
                    logger.info(f"⚠️  {display_name} not available (optional)")
                else:
                    logger.error(f"❌ {display_name} not working (required)")
                results[import_name] = False
        
        # Check if we have minimum requirements
        required_packages = [name for name, _, optional in test_imports if not optional]
        required_success = sum(1 for name, _, optional in test_imports 
                             if not optional and results.get(name, False))
        
        success_rate = required_success / len(required_packages)
        
        print(f"\n📊 INSTALLATION VERIFICATION RESULTS:")
        print(f"   Required packages:  {required_success}/{len(required_packages)} working ({success_rate*100:.1f}%)")
        print(f"   Optional packages:  {optional_working} working")
        
        if success_rate >= 1.0:
            print("✅ All required packages are working!")
        elif success_rate >= 0.8:
            print("✅ Most required packages are working - should be functional")
        else:
            print("❌ Too many required packages are missing - may not work properly")
        
        return results, success_rate >= 0.8
    
    def create_activation_script(self):
        """Create a script to easily activate the environment and run the system"""
        script_content = f"""#!/bin/bash
# StorySign Environment Activation Script
# This script ensures you're in the correct environment before running

echo "🚀 StorySign Environment Setup"
echo "=============================="

# Check if we're in a conda environment
if [[ -z "$CONDA_DEFAULT_ENV" ]]; then
    echo "❌ No conda environment active"
    echo "Please run: conda activate mediapipe_env"
    exit 1
fi

# Check if we're in the right environment
if [[ "$CONDA_DEFAULT_ENV" != *"mediapipe"* ]]; then
    echo "⚠️  Current environment: $CONDA_DEFAULT_ENV"
    echo "Recommended environment: mediapipe_env"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Please run: conda activate mediapipe_env"
        exit 1
    fi
fi

echo "✅ Environment: $CONDA_DEFAULT_ENV"
echo "✅ Python: $(which python)"
echo ""

# Show available commands
echo "Available commands:"
echo "  1. python main.py              - Start backend server"
echo "  2. python test_latency_improvements.py - Test latency"
echo "  3. python benchmark_optimizations.py   - Benchmark performance"
echo "  4. npm start                    - Start frontend (in frontend/ directory)"
echo ""

# Ask what to run
echo "What would you like to do?"
echo "1) Start backend server"
echo "2) Test latency improvements"
echo "3) Benchmark optimizations"
echo "4) Just activate environment"
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        echo "🚀 Starting backend server..."
        cd backend && python main.py
        ;;
    2)
        echo "🧪 Testing latency improvements..."
        python test_latency_improvements.py
        ;;
    3)
        echo "📊 Running performance benchmark..."
        python benchmark_optimizations.py
        ;;
    4)
        echo "✅ Environment ready! You can now run Python scripts."
        ;;
    *)
        echo "✅ Environment ready! You can now run Python scripts."
        ;;
esac
"""
        
        with open("activate_storysign.sh", "w") as f:
            f.write(script_content)
        
        # Make executable
        os.chmod("activate_storysign.sh", 0o755)
        
        logger.info("📝 Created activation script: activate_storysign.sh")
        print("\n💡 TIP: You can use './activate_storysign.sh' to easily run the system")
    
    def setup_complete_environment(self):
        """Complete environment setup process"""
        print("🚀 StorySign Advanced Environment Setup")
        print("=" * 50)
        
        # Show environment info
        self.print_environment_info()
        
        # Verify we're in the right environment
        if not self.verify_mediapipe_env():
            print("❌ Environment setup cancelled")
            return False
        
        try:
            # Install base requirements
            if not self.install_base_requirements():
                print("❌ Failed to install base requirements")
                return False
            
            # Install advanced optimizations
            if not self.install_advanced_optimizations():
                print("⚠️  Some advanced optimizations failed to install")
                print("The system will still work with basic optimizations")
            
            # Install GPU acceleration
            gpu_success = self.install_gpu_acceleration()
            
            # Verify installation
            results, success = self.verify_installation()
            
            if success:
                print("\n✅ Environment setup completed successfully!")
                
                # Create activation script
                self.create_activation_script()
                
                print("\n🎉 Ready to run StorySign with advanced optimizations!")
                print("\nNext steps:")
                print("1. cd StorySign_Platform/backend && python main.py  # Start backend")
                print("2. cd StorySign_Platform/frontend && npm start      # Start frontend")
                print("3. python test_latency_improvements.py              # Test performance")
                
                return True
            else:
                print("\n❌ Environment setup completed with issues")
                print("Some packages may not work correctly")
                return False
                
        except Exception as e:
            logger.error(f"Environment setup failed: {e}")
            print(f"❌ Environment setup failed: {e}")
            return False

def main():
    """Main setup function"""
    setup = EnvironmentSetup()
    success = setup.setup_complete_environment()
    
    if success:
        print("\n🎉 Environment setup complete!")
        return 0
    else:
        print("\n❌ Environment setup failed!")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())