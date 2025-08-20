#!/usr/bin/env python3
"""
Installation script for advanced optimization packages
Installs GPU acceleration, advanced compression, and performance libraries
"""

import subprocess
import sys
import os
import platform
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedOptimizationInstaller:
    """Install advanced optimization packages for ultra-low latency"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.architecture = platform.machine().lower()
        self.python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        
        logger.info(f"System: {self.system}, Architecture: {self.architecture}, Python: {self.python_version}")
    
    def install_package(self, package: str, description: str = "", optional: bool = False) -> bool:
        """Install a Python package"""
        try:
            logger.info(f"Installing {package}... {description}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            logger.info(f"✅ Successfully installed {package}")
            return True
        except subprocess.CalledProcessError as e:
            if optional:
                logger.warning(f"⚠️  Optional package {package} failed to install: {e}")
                return False
            else:
                logger.error(f"❌ Failed to install {package}: {e}")
                return False
    
    def install_system_package(self, package: str, description: str = "") -> bool:
        """Install system package using appropriate package manager"""
        try:
            if self.system == "linux":
                # Try apt-get first (Ubuntu/Debian)
                try:
                    subprocess.check_call(["sudo", "apt-get", "update"])
                    subprocess.check_call(["sudo", "apt-get", "install", "-y", package])
                    logger.info(f"✅ Installed {package} via apt-get")
                    return True
                except subprocess.CalledProcessError:
                    # Try yum (CentOS/RHEL)
                    try:
                        subprocess.check_call(["sudo", "yum", "install", "-y", package])
                        logger.info(f"✅ Installed {package} via yum")
                        return True
                    except subprocess.CalledProcessError:
                        logger.warning(f"⚠️  Could not install {package} via package manager")
                        return False
            elif self.system == "darwin":  # macOS
                try:
                    subprocess.check_call(["brew", "install", package])
                    logger.info(f"✅ Installed {package} via brew")
                    return True
                except subprocess.CalledProcessError:
                    logger.warning(f"⚠️  Could not install {package} via brew")
                    return False
            else:
                logger.warning(f"⚠️  System package installation not supported on {self.system}")
                return False
        except Exception as e:
            logger.warning(f"⚠️  System package installation failed: {e}")
            return False
    
    def install_gpu_acceleration(self):
        """Install GPU acceleration packages"""
        logger.info("🚀 Installing GPU acceleration packages...")
        
        # CUDA support (CuPy)
        if self.install_package("cupy-cuda12x", "CUDA 12.x support for GPU acceleration", optional=True):
            logger.info("✅ CUDA 12.x support installed")
        elif self.install_package("cupy-cuda11x", "CUDA 11.x support for GPU acceleration", optional=True):
            logger.info("✅ CUDA 11.x support installed")
        else:
            logger.warning("⚠️  CUDA support not available - GPU acceleration will be limited")
        
        # OpenCL support
        self.install_package("pyopencl", "OpenCL support for cross-platform GPU acceleration", optional=True)
        
        # Intel OpenVINO (CPU optimization)
        self.install_package("openvino", "Intel OpenVINO for CPU optimization", optional=True)
        
        # TurboJPEG for ultra-fast JPEG encoding/decoding
        if self.system == "linux":
            self.install_system_package("libturbojpeg0-dev", "TurboJPEG development libraries")
        elif self.system == "darwin":
            self.install_system_package("jpeg-turbo", "TurboJPEG libraries")
        
        self.install_package("PyTurboJPEG", "Python bindings for TurboJPEG", optional=True)
    
    def install_advanced_compression(self):
        """Install advanced compression packages"""
        logger.info("🗜️  Installing advanced compression packages...")
        
        # Modern video codecs
        self.install_package("av", "PyAV for advanced video codecs (H.264, H.265, AV1)", optional=True)
        
        # Ultra-fast compression
        self.install_package("lz4", "LZ4 ultra-fast compression", optional=True)
        self.install_package("zstandard", "Facebook's Zstandard compression", optional=True)
        
        # Modern image formats
        self.install_package("pillow-heif", "HEIF/HEIC image format support", optional=True)
        
        # Enhanced PIL/Pillow
        self.install_package("Pillow>=9.0.0", "Enhanced PIL for better image processing")
        
        # WebP support (usually included with OpenCV)
        if self.system == "linux":
            self.install_system_package("libwebp-dev", "WebP development libraries")
        elif self.system == "darwin":
            self.install_system_package("webp", "WebP libraries")
    
    def install_performance_libraries(self):
        """Install performance optimization libraries"""
        logger.info("⚡ Installing performance optimization libraries...")
        
        # NumPy with optimized BLAS
        self.install_package("numpy", "NumPy with optimized linear algebra")
        
        # Intel Math Kernel Library (if available)
        self.install_package("mkl", "Intel Math Kernel Library for faster computations", optional=True)
        
        # Numba for JIT compilation
        self.install_package("numba", "JIT compilation for faster Python code", optional=True)
        
        # Memory profiling and optimization
        self.install_package("psutil", "System and process utilities")
        self.install_package("memory-profiler", "Memory usage profiling", optional=True)
        
        # Async I/O optimizations
        self.install_package("uvloop", "Ultra-fast asyncio event loop", optional=True)
    
    def install_monitoring_tools(self):
        """Install monitoring and profiling tools"""
        logger.info("📊 Installing monitoring and profiling tools...")
        
        # Performance monitoring
        self.install_package("py-spy", "Sampling profiler for Python", optional=True)
        self.install_package("line-profiler", "Line-by-line profiling", optional=True)
        
        # GPU monitoring
        self.install_package("gpustat", "GPU utilization monitoring", optional=True)
        self.install_package("nvidia-ml-py", "NVIDIA GPU monitoring", optional=True)
    
    def verify_installations(self):
        """Verify that key packages are working"""
        logger.info("🔍 Verifying installations...")
        
        # Test imports
        test_packages = [
            ("cv2", "OpenCV"),
            ("numpy", "NumPy"),
            ("PIL", "Pillow"),
            ("cupy", "CuPy (CUDA)", True),
            ("pyopencl", "PyOpenCL", True),
            ("turbojpeg", "TurboJPEG", True),
            ("av", "PyAV", True),
            ("lz4", "LZ4", True),
            ("zstandard", "Zstandard", True),
            ("numba", "Numba", True),
            ("psutil", "PSUtil"),
        ]
        
        results = {}
        for package_info in test_packages:
            if len(package_info) == 3:
                package, name, optional = package_info
            else:
                package, name = package_info
                optional = False
            
            try:
                __import__(package)
                logger.info(f"✅ {name} is working")
                results[package] = True
            except ImportError:
                if optional:
                    logger.info(f"⚠️  {name} not available (optional)")
                else:
                    logger.error(f"❌ {name} not working")
                results[package] = False
        
        return results
    
    def create_optimization_report(self, results: dict):
        """Create optimization capabilities report"""
        report = {
            "timestamp": str(subprocess.check_output(["date"]).decode().strip()),
            "system_info": {
                "system": self.system,
                "architecture": self.architecture,
                "python_version": self.python_version
            },
            "gpu_acceleration": {
                "cuda_available": results.get("cupy", False),
                "opencl_available": results.get("pyopencl", False),
                "turbojpeg_available": results.get("turbojpeg", False)
            },
            "advanced_compression": {
                "av_available": results.get("av", False),
                "lz4_available": results.get("lz4", False),
                "zstd_available": results.get("zstandard", False)
            },
            "performance_libraries": {
                "numba_available": results.get("numba", False),
                "psutil_available": results.get("psutil", False)
            }
        }
        
        # Save report
        import json
        with open("optimization_capabilities.json", "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info("📋 Optimization capabilities report saved to: optimization_capabilities.json")
        return report
    
    def install_all(self):
        """Install all optimization packages"""
        logger.info("🚀 Starting advanced optimization installation...")
        logger.info("=" * 60)
        
        try:
            # Install in order of importance
            self.install_gpu_acceleration()
            self.install_advanced_compression()
            self.install_performance_libraries()
            self.install_monitoring_tools()
            
            # Verify installations
            results = self.verify_installations()
            
            # Create report
            report = self.create_optimization_report(results)
            
            # Summary
            logger.info("=" * 60)
            logger.info("🎉 Advanced optimization installation complete!")
            
            gpu_count = sum([
                report["gpu_acceleration"]["cuda_available"],
                report["gpu_acceleration"]["opencl_available"],
                report["gpu_acceleration"]["turbojpeg_available"]
            ])
            
            compression_count = sum([
                report["advanced_compression"]["av_available"],
                report["advanced_compression"]["lz4_available"],
                report["advanced_compression"]["zstd_available"]
            ])
            
            logger.info(f"GPU Acceleration: {gpu_count}/3 packages available")
            logger.info(f"Advanced Compression: {compression_count}/3 packages available")
            
            if gpu_count >= 1 and compression_count >= 1:
                logger.info("✅ Excellent! Advanced optimizations are ready for ultra-low latency")
            elif gpu_count >= 1 or compression_count >= 1:
                logger.info("✅ Good! Some advanced optimizations are available")
            else:
                logger.info("⚠️  Limited optimizations available - will use CPU fallbacks")
            
            logger.info("🚀 Ready to achieve ultra-low latency video processing!")
            
        except Exception as e:
            logger.error(f"❌ Installation failed: {e}")
            return False
        
        return True

def main():
    """Main installation function"""
    print("🚀 StorySign Advanced Optimization Installer")
    print("=" * 50)
    print("This will install packages for:")
    print("• GPU acceleration (CUDA, OpenCL)")
    print("• Advanced compression (H.264, WebP, LZ4, Zstd)")
    print("• Performance libraries (TurboJPEG, Numba)")
    print("• Monitoring tools")
    print()
    
    response = input("Continue with installation? (y/N): ").lower().strip()
    if response not in ['y', 'yes']:
        print("Installation cancelled.")
        return
    
    installer = AdvancedOptimizationInstaller()
    success = installer.install_all()
    
    if success:
        print("\n🎉 Installation completed successfully!")
        print("You can now run the StorySign platform with advanced optimizations.")
        print("\nNext steps:")
        print("1. Restart your Python environment")
        print("2. Run: python test_latency_improvements.py")
        print("3. Start the backend: python main.py")
        print("4. Start the frontend: npm start")
    else:
        print("\n❌ Installation encountered some issues.")
        print("Check the logs above for details.")
        print("The system will still work with basic optimizations.")

if __name__ == "__main__":
    main()