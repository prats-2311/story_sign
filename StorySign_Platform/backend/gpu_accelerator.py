#!/usr/bin/env python3
"""
GPU Acceleration Module for Ultra-Low Latency Video Processing
Uses CUDA, OpenCL, and hardware acceleration for maximum performance
"""

import cv2
import numpy as np
import logging
from typing import Optional, Tuple, Dict, Any
import time

# Try to import GPU acceleration libraries
try:
    import cupy as cp
    CUPY_AVAILABLE = True
except ImportError:
    CUPY_AVAILABLE = False

try:
    import pyopencl as cl
    OPENCL_AVAILABLE = True
except ImportError:
    OPENCL_AVAILABLE = False

try:
    # Intel OpenVINO for CPU optimization
    from openvino.runtime import Core
    OPENVINO_AVAILABLE = True
except ImportError:
    OPENVINO_AVAILABLE = False

logger = logging.getLogger(__name__)

class GPUAccelerator:
    """GPU acceleration for video processing operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.GPUAccelerator")
        self.cuda_available = self._check_cuda()
        self.opencl_available = self._check_opencl()
        self.openvino_available = self._check_openvino()
        
        # Initialize best available acceleration
        self.acceleration_method = self._select_best_acceleration()
        self.logger.info(f"GPU Accelerator initialized with: {self.acceleration_method}")
        
    def _check_cuda(self) -> bool:
        """Check if CUDA is available"""
        try:
            if CUPY_AVAILABLE and cv2.cuda.getCudaEnabledDeviceCount() > 0:
                # Test CUDA functionality
                test_array = cp.array([1, 2, 3])
                _ = cp.sum(test_array)
                self.logger.info("✅ CUDA acceleration available")
                return True
        except Exception as e:
            self.logger.debug(f"CUDA not available: {e}")
        return False
    
    def _check_opencl(self) -> bool:
        """Check if OpenCL is available"""
        try:
            if OPENCL_AVAILABLE:
                platforms = cl.get_platforms()
                if platforms:
                    self.logger.info("✅ OpenCL acceleration available")
                    return True
        except Exception as e:
            self.logger.debug(f"OpenCL not available: {e}")
        return False
    
    def _check_openvino(self) -> bool:
        """Check if Intel OpenVINO is available"""
        try:
            if OPENVINO_AVAILABLE:
                core = Core()
                devices = core.available_devices
                if devices:
                    self.logger.info(f"✅ OpenVINO acceleration available on: {devices}")
                    return True
        except Exception as e:
            self.logger.debug(f"OpenVINO not available: {e}")
        return False
    
    def _select_best_acceleration(self) -> str:
        """Select the best available acceleration method"""
        if self.cuda_available:
            return "CUDA"
        elif self.opencl_available:
            return "OpenCL"
        elif self.openvino_available:
            return "OpenVINO"
        else:
            return "CPU_Optimized"
    
    def accelerated_resize(self, image: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
        """GPU-accelerated image resizing"""
        try:
            if self.acceleration_method == "CUDA" and CUPY_AVAILABLE:
                return self._cuda_resize(image, target_size)
            elif self.acceleration_method == "OpenCL":
                return self._opencl_resize(image, target_size)
            else:
                return self._optimized_cpu_resize(image, target_size)
        except Exception as e:
            self.logger.warning(f"GPU resize failed, falling back to CPU: {e}")
            return cv2.resize(image, target_size, interpolation=cv2.INTER_LINEAR)
    
    def _cuda_resize(self, image: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
        """CUDA-accelerated resize using CuPy"""
        # Upload to GPU
        gpu_image = cp.asarray(image)
        
        # Use CuPy's optimized resize (via SciPy)
        from cupyx.scipy.ndimage import zoom
        
        height, width = image.shape[:2]
        target_width, target_height = target_size
        
        zoom_factors = (target_height / height, target_width / width)
        if len(image.shape) == 3:
            zoom_factors = zoom_factors + (1,)  # Don't zoom color channels
        
        resized_gpu = zoom(gpu_image, zoom_factors, order=1)  # Linear interpolation
        
        # Download from GPU
        return cp.asnumpy(resized_gpu).astype(np.uint8)
    
    def _opencl_resize(self, image: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
        """OpenCL-accelerated resize"""
        # Use OpenCV's OpenCL backend if available
        try:
            # Enable OpenCL in OpenCV
            cv2.ocl.setUseOpenCL(True)
            
            # Create UMat (OpenCL memory)
            umat_image = cv2.UMat(image)
            
            # Resize using OpenCL
            resized_umat = cv2.resize(umat_image, target_size, interpolation=cv2.INTER_LINEAR)
            
            # Convert back to numpy array
            return resized_umat.get()
        except Exception as e:
            self.logger.debug(f"OpenCL resize failed: {e}")
            return cv2.resize(image, target_size, interpolation=cv2.INTER_LINEAR)
    
    def _optimized_cpu_resize(self, image: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
        """Optimized CPU resize using best interpolation"""
        # Use INTER_AREA for downscaling (faster and better quality)
        # Use INTER_LINEAR for upscaling
        height, width = image.shape[:2]
        target_width, target_height = target_size
        
        if target_width < width or target_height < height:
            # Downscaling - use INTER_AREA
            interpolation = cv2.INTER_AREA
        else:
            # Upscaling - use INTER_LINEAR
            interpolation = cv2.INTER_LINEAR
        
        return cv2.resize(image, target_size, interpolation=interpolation)
    
    def accelerated_encode(self, image: np.ndarray, quality: int = 85) -> bytes:
        """GPU-accelerated JPEG encoding"""
        try:
            if self.acceleration_method == "CUDA":
                return self._cuda_encode(image, quality)
            else:
                return self._optimized_cpu_encode(image, quality)
        except Exception as e:
            self.logger.warning(f"GPU encode failed, falling back to CPU: {e}")
            _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, quality])
            return buffer.tobytes()
    
    def _cuda_encode(self, image: np.ndarray, quality: int) -> bytes:
        """CUDA-accelerated JPEG encoding"""
        try:
            # Use NVIDIA's nvJPEG if available through OpenCV
            if hasattr(cv2, 'cuda') and hasattr(cv2.cuda, 'JPEG'):
                gpu_image = cv2.cuda_GpuMat()
                gpu_image.upload(image)
                
                # Encode on GPU
                encoded = cv2.cuda.imencode('.jpg', gpu_image, [cv2.IMWRITE_JPEG_QUALITY, quality])
                return encoded.tobytes()
            else:
                # Fallback to CPU with optimized parameters
                return self._optimized_cpu_encode(image, quality)
        except Exception as e:
            self.logger.debug(f"CUDA encode failed: {e}")
            return self._optimized_cpu_encode(image, quality)
    
    def _optimized_cpu_encode(self, image: np.ndarray, quality: int) -> bytes:
        """Optimized CPU JPEG encoding"""
        # Use optimized JPEG parameters for speed
        encode_params = [
            cv2.IMWRITE_JPEG_QUALITY, quality,
            cv2.IMWRITE_JPEG_OPTIMIZE, 0,  # Disable optimization for speed
            cv2.IMWRITE_JPEG_PROGRESSIVE, 0,  # Disable progressive for speed
            cv2.IMWRITE_JPEG_RST_INTERVAL, 0  # Disable restart markers
        ]
        
        _, buffer = cv2.imencode('.jpg', image, encode_params)
        return buffer.tobytes()
    
    def get_acceleration_info(self) -> Dict[str, Any]:
        """Get information about available acceleration"""
        return {
            "method": self.acceleration_method,
            "cuda_available": self.cuda_available,
            "opencl_available": self.opencl_available,
            "openvino_available": self.openvino_available,
            "cuda_devices": cv2.cuda.getCudaEnabledDeviceCount() if self.cuda_available else 0,
            "opencv_version": cv2.__version__,
            "cuda_support": cv2.cuda.getCudaEnabledDeviceCount() > 0 if hasattr(cv2, 'cuda') else False
        }


class TurboJPEGAccelerator:
    """Ultra-fast JPEG encoding/decoding using TurboJPEG"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.TurboJPEGAccelerator")
        self.turbojpeg_available = self._check_turbojpeg()
        
        if self.turbojpeg_available:
            from turbojpeg import TurboJPEG
            self.jpeg = TurboJPEG()
            self.logger.info("✅ TurboJPEG acceleration available")
        else:
            self.jpeg = None
            self.logger.info("❌ TurboJPEG not available, using standard JPEG")
    
    def _check_turbojpeg(self) -> bool:
        """Check if TurboJPEG is available"""
        try:
            from turbojpeg import TurboJPEG
            # Test TurboJPEG functionality
            test_jpeg = TurboJPEG()
            test_image = np.zeros((100, 100, 3), dtype=np.uint8)
            encoded = test_jpeg.encode(test_image, quality=85)
            decoded = test_jpeg.decode(encoded)
            return True
        except ImportError:
            self.logger.debug("TurboJPEG not installed")
            return False
        except Exception as e:
            self.logger.debug(f"TurboJPEG test failed: {e}")
            return False
    
    def encode(self, image: np.ndarray, quality: int = 85) -> bytes:
        """Ultra-fast JPEG encoding"""
        if self.turbojpeg_available and self.jpeg:
            try:
                # TurboJPEG is typically 2-6x faster than standard JPEG
                return self.jpeg.encode(image, quality=quality)
            except Exception as e:
                self.logger.warning(f"TurboJPEG encode failed: {e}")
        
        # Fallback to standard JPEG
        _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, quality])
        return buffer.tobytes()
    
    def decode(self, jpeg_data: bytes) -> np.ndarray:
        """Ultra-fast JPEG decoding"""
        if self.turbojpeg_available and self.jpeg:
            try:
                return self.jpeg.decode(jpeg_data)
            except Exception as e:
                self.logger.warning(f"TurboJPEG decode failed: {e}")
        
        # Fallback to standard JPEG
        nparr = np.frombuffer(jpeg_data, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)


class MemoryPoolManager:
    """Memory pool for reducing allocation overhead"""
    
    def __init__(self, pool_size: int = 10):
        self.logger = logging.getLogger(f"{__name__}.MemoryPoolManager")
        self.pool_size = pool_size
        self.image_pools = {}  # Size -> list of arrays
        self.buffer_pools = {}  # Size -> list of buffers
        
    def get_image_buffer(self, shape: Tuple[int, ...], dtype=np.uint8) -> np.ndarray:
        """Get a reusable image buffer"""
        key = (shape, dtype)
        
        if key not in self.image_pools:
            self.image_pools[key] = []
        
        pool = self.image_pools[key]
        
        if pool:
            return pool.pop()
        else:
            return np.empty(shape, dtype=dtype)
    
    def return_image_buffer(self, buffer: np.ndarray):
        """Return buffer to pool for reuse"""
        key = (buffer.shape, buffer.dtype)
        
        if key not in self.image_pools:
            self.image_pools[key] = []
        
        pool = self.image_pools[key]
        
        if len(pool) < self.pool_size:
            pool.append(buffer)
    
    def get_byte_buffer(self, size: int) -> bytearray:
        """Get a reusable byte buffer"""
        if size not in self.buffer_pools:
            self.buffer_pools[size] = []
        
        pool = self.buffer_pools[size]
        
        if pool:
            return pool.pop()
        else:
            return bytearray(size)
    
    def return_byte_buffer(self, buffer: bytearray):
        """Return byte buffer to pool"""
        size = len(buffer)
        
        if size not in self.buffer_pools:
            self.buffer_pools[size] = []
        
        pool = self.buffer_pools[size]
        
        if len(pool) < self.pool_size:
            pool.append(buffer)


# Global instances
gpu_accelerator = GPUAccelerator()
turbojpeg_accelerator = TurboJPEGAccelerator()
memory_pool = MemoryPoolManager()

def get_acceleration_info() -> Dict[str, Any]:
    """Get comprehensive acceleration information"""
    return {
        "gpu": gpu_accelerator.get_acceleration_info(),
        "turbojpeg": turbojpeg_accelerator.turbojpeg_available,
        "memory_pool": {
            "image_pools": len(memory_pool.image_pools),
            "buffer_pools": len(memory_pool.buffer_pools)
        }
    }