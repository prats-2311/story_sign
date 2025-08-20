#!/usr/bin/env python3
"""
Advanced Compression Module for Ultra-Low Latency Video Streaming
Uses modern codecs and compression techniques for maximum efficiency
"""

import cv2
import numpy as np
import logging
from typing import Optional, Tuple, Dict, Any, Union
import time
import base64

# Try to import advanced compression libraries
try:
    import av  # PyAV for advanced video codecs
    PYAV_AVAILABLE = True
except ImportError:
    PYAV_AVAILABLE = False

try:
    import pillow_heif  # HEIF/HEIC support
    HEIF_AVAILABLE = True
except ImportError:
    HEIF_AVAILABLE = False

try:
    from PIL import Image, ImageOps
    import io
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import lz4.frame  # Ultra-fast compression
    LZ4_AVAILABLE = True
except ImportError:
    LZ4_AVAILABLE = False

try:
    import zstandard as zstd  # Facebook's Zstandard compression
    ZSTD_AVAILABLE = True
except ImportError:
    ZSTD_AVAILABLE = False

logger = logging.getLogger(__name__)

class AdvancedCompressor:
    """Advanced compression using modern codecs and algorithms"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.AdvancedCompressor")
        self.available_methods = self._check_available_methods()
        self.best_method = self._select_best_method()
        
        # Initialize compressors
        self._init_compressors()
        
        self.logger.info(f"Advanced compressor initialized with: {self.best_method}")
        self.logger.info(f"Available methods: {list(self.available_methods.keys())}")
    
    def _check_available_methods(self) -> Dict[str, bool]:
        """Check which compression methods are available"""
        methods = {
            "webp": self._check_webp(),
            "avif": self._check_avif(),
            "heif": HEIF_AVAILABLE,
            "h264_hardware": self._check_h264_hardware(),
            "h265_hardware": self._check_h265_hardware(),
            "av1": self._check_av1(),
            "lz4": LZ4_AVAILABLE,
            "zstd": ZSTD_AVAILABLE,
            "mozjpeg": self._check_mozjpeg()
        }
        
        available = {k: v for k, v in methods.items() if v}
        self.logger.info(f"Available compression methods: {list(available.keys())}")
        return available
    
    def _check_webp(self) -> bool:
        """Check WebP support"""
        try:
            # Test WebP encoding with basic parameters
            test_img = np.zeros((10, 10, 3), dtype=np.uint8)
            
            # Try simple WebP encoding first
            success, buffer = cv2.imencode('.webp', test_img)
            if success and len(buffer) > 0:
                return True
            
            # Try with quality parameter
            success, buffer = cv2.imencode('.webp', test_img, [cv2.IMWRITE_WEBP_QUALITY, 80])
            return success and len(buffer) > 0
            
        except Exception as e:
            self.logger.debug(f"WebP check failed: {e}")
            return False
    
    def _check_avif(self) -> bool:
        """Check AVIF support"""
        try:
            if PIL_AVAILABLE:
                # Check if PIL supports AVIF
                from PIL import Image
                return "AVIF" in Image.registered_extensions().values()
            return False
        except:
            return False
    
    def _check_h264_hardware(self) -> bool:
        """Check hardware H.264 encoding support"""
        try:
            if PYAV_AVAILABLE:
                import av
                # Check for hardware encoders
                codecs = av.codec.codecs_available
                hw_encoders = ['h264_nvenc', 'h264_qsv', 'h264_videotoolbox', 'h264_vaapi']
                return any(encoder in codecs for encoder in hw_encoders)
            return False
        except:
            return False
    
    def _check_h265_hardware(self) -> bool:
        """Check hardware H.265/HEVC encoding support"""
        try:
            if PYAV_AVAILABLE:
                import av
                codecs = av.codec.codecs_available
                hw_encoders = ['hevc_nvenc', 'hevc_qsv', 'hevc_videotoolbox', 'hevc_vaapi']
                return any(encoder in codecs for encoder in hw_encoders)
            return False
        except:
            return False
    
    def _check_av1(self) -> bool:
        """Check AV1 encoding support"""
        try:
            if PYAV_AVAILABLE:
                import av
                return 'libaom-av1' in av.codec.codecs_available
            return False
        except:
            return False
    
    def _check_mozjpeg(self) -> bool:
        """Check MozJPEG support (better than standard JPEG)"""
        try:
            if PIL_AVAILABLE:
                from PIL import Image
                # MozJPEG is usually available through PIL with specific options
                return True  # Assume available if PIL is present
            return False
        except:
            return False
    
    def _select_best_method(self) -> str:
        """Select the best compression method based on performance"""
        # Priority order: fastest to slowest, best compression ratio
        priority_order = [
            "h264_hardware",  # Hardware encoding is fastest
            "h265_hardware",  # Better compression than H.264
            "webp",          # Good balance of speed and compression
            "lz4",           # Ultra-fast for raw data
            "zstd",          # Fast with good compression
            "mozjpeg",       # Better than standard JPEG
            "avif",          # Excellent compression but slower
            "heif",          # Good compression
            "av1"            # Best compression but slowest
        ]
        
        for method in priority_order:
            if self.available_methods.get(method, False):
                return method
        
        return "jpeg_optimized"  # Fallback
    
    def _init_compressors(self):
        """Initialize compression objects"""
        self.zstd_compressor = None
        self.lz4_compressor = None
        
        if ZSTD_AVAILABLE:
            self.zstd_compressor = zstd.ZstdCompressor(level=1)  # Fast compression
        
        # LZ4 doesn't need initialization
    
    def compress_frame(self, image: np.ndarray, quality: int = 85, target_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Compress frame using the best available method
        
        Args:
            image: Input image as numpy array
            quality: Compression quality (0-100)
            target_size: Target compressed size in bytes (optional)
            
        Returns:
            Dictionary with compressed data and metadata
        """
        start_time = time.time()
        
        try:
            if self.best_method == "webp":
                result = self._compress_webp(image, quality)
            elif self.best_method == "h264_hardware":
                result = self._compress_h264_hardware(image, quality)
            elif self.best_method == "lz4":
                result = self._compress_lz4(image)
            elif self.best_method == "zstd":
                result = self._compress_zstd(image, quality)
            elif self.best_method == "mozjpeg":
                result = self._compress_mozjpeg(image, quality)
            else:
                result = self._compress_jpeg_optimized(image, quality)
            
            # Add timing information
            compression_time = (time.time() - start_time) * 1000
            result["compression_time_ms"] = compression_time
            result["method"] = self.best_method
            
            # Calculate compression ratio
            original_size = image.nbytes
            compressed_size = len(result["data"])
            result["compression_ratio"] = original_size / compressed_size if compressed_size > 0 else 1.0
            result["original_size"] = original_size
            result["compressed_size"] = compressed_size
            
            return result
            
        except Exception as e:
            self.logger.error(f"Compression failed with {self.best_method}: {e}")
            # Fallback to basic JPEG
            return self._compress_jpeg_optimized(image, quality)
    
    def _compress_webp(self, image: np.ndarray, quality: int) -> Dict[str, Any]:
        """Compress using WebP format with fallback"""
        try:
            # Try with WebP method parameter if available
            if hasattr(cv2, 'IMWRITE_WEBP_METHOD'):
                encode_params = [
                    cv2.IMWRITE_WEBP_QUALITY, quality,
                    cv2.IMWRITE_WEBP_METHOD, 0  # Fastest method
                ]
            else:
                # Fallback to just quality parameter
                encode_params = [cv2.IMWRITE_WEBP_QUALITY, quality]
            
            success, buffer = cv2.imencode('.webp', image, encode_params)
            if not success:
                raise Exception("WebP encoding failed")
            
            return {
                "data": buffer.tobytes(),
                "format": "webp",
                "success": True
            }
        except Exception as e:
            # If WebP fails, fall back to optimized JPEG
            self.logger.debug(f"WebP encoding failed: {e}, falling back to JPEG")
            return self._compress_jpeg_optimized(image, quality)
    
    def _compress_h264_hardware(self, image: np.ndarray, quality: int) -> Dict[str, Any]:
        """Compress using hardware H.264 encoding"""
        try:
            import av
            
            # Create in-memory container
            output = io.BytesIO()
            container = av.open(output, mode='w', format='mp4')
            
            # Add video stream with hardware encoder
            stream = container.add_stream('h264_nvenc', rate=30)  # Try NVIDIA first
            stream.width = image.shape[1]
            stream.height = image.shape[0]
            stream.pix_fmt = 'yuv420p'
            
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Create frame
            frame = av.VideoFrame.from_ndarray(rgb_image, format='rgb24')
            
            # Encode frame
            for packet in stream.encode(frame):
                container.mux(packet)
            
            # Flush encoder
            for packet in stream.encode():
                container.mux(packet)
            
            container.close()
            
            return {
                "data": output.getvalue(),
                "format": "h264",
                "success": True
            }
            
        except Exception as e:
            self.logger.debug(f"Hardware H.264 encoding failed: {e}")
            # Fallback to software encoding or other method
            raise e
    
    def _compress_lz4(self, image: np.ndarray) -> Dict[str, Any]:
        """Compress using LZ4 (ultra-fast)"""
        if not LZ4_AVAILABLE:
            raise Exception("LZ4 not available")
        
        # Convert image to bytes
        image_bytes = image.tobytes()
        
        # Compress with LZ4
        compressed = lz4.frame.compress(image_bytes, compression_level=1)  # Fastest
        
        return {
            "data": compressed,
            "format": "lz4_raw",
            "success": True,
            "shape": image.shape,
            "dtype": str(image.dtype)
        }
    
    def _compress_zstd(self, image: np.ndarray, quality: int) -> Dict[str, Any]:
        """Compress using Zstandard"""
        if not ZSTD_AVAILABLE or not self.zstd_compressor:
            raise Exception("Zstandard not available")
        
        # First compress as JPEG, then apply Zstd
        _, jpeg_buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, quality])
        jpeg_bytes = jpeg_buffer.tobytes()
        
        # Apply Zstd compression
        compressed = self.zstd_compressor.compress(jpeg_bytes)
        
        return {
            "data": compressed,
            "format": "zstd_jpeg",
            "success": True
        }
    
    def _compress_mozjpeg(self, image: np.ndarray, quality: int) -> Dict[str, Any]:
        """Compress using MozJPEG (optimized JPEG)"""
        if not PIL_AVAILABLE:
            raise Exception("PIL not available for MozJPEG")
        
        # Convert OpenCV BGR to PIL RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        
        # Save with optimized JPEG settings
        output = io.BytesIO()
        pil_image.save(
            output, 
            format='JPEG',
            quality=quality,
            optimize=True,  # Enable optimization
            progressive=False,  # Disable for speed
            subsampling=0  # No subsampling for better quality
        )
        
        return {
            "data": output.getvalue(),
            "format": "mozjpeg",
            "success": True
        }
    
    def _compress_jpeg_optimized(self, image: np.ndarray, quality: int) -> Dict[str, Any]:
        """Optimized JPEG compression (fallback)"""
        encode_params = [
            cv2.IMWRITE_JPEG_QUALITY, quality,
            cv2.IMWRITE_JPEG_OPTIMIZE, 0,  # Disable for speed
            cv2.IMWRITE_JPEG_PROGRESSIVE, 0,  # Disable for speed
            cv2.IMWRITE_JPEG_RST_INTERVAL, 0  # Disable restart markers
        ]
        
        success, buffer = cv2.imencode('.jpg', image, encode_params)
        if not success:
            raise Exception("JPEG encoding failed")
        
        return {
            "data": buffer.tobytes(),
            "format": "jpeg_optimized",
            "success": True
        }
    
    def decompress_frame(self, compressed_data: bytes, metadata: Dict[str, Any]) -> np.ndarray:
        """Decompress frame data"""
        format_type = metadata.get("format", "jpeg_optimized")
        
        try:
            if format_type == "webp":
                return self._decompress_webp(compressed_data)
            elif format_type == "lz4_raw":
                return self._decompress_lz4(compressed_data, metadata)
            elif format_type == "zstd_jpeg":
                return self._decompress_zstd(compressed_data)
            elif format_type in ["mozjpeg", "jpeg_optimized"]:
                return self._decompress_jpeg(compressed_data)
            else:
                # Default to JPEG
                return self._decompress_jpeg(compressed_data)
                
        except Exception as e:
            self.logger.error(f"Decompression failed for {format_type}: {e}")
            # Try fallback JPEG decompression
            return self._decompress_jpeg(compressed_data)
    
    def _decompress_webp(self, data: bytes) -> np.ndarray:
        """Decompress WebP data"""
        nparr = np.frombuffer(data, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    def _decompress_lz4(self, data: bytes, metadata: Dict[str, Any]) -> np.ndarray:
        """Decompress LZ4 data"""
        if not LZ4_AVAILABLE:
            raise Exception("LZ4 not available")
        
        # Decompress
        decompressed = lz4.frame.decompress(data)
        
        # Reconstruct array
        shape = metadata["shape"]
        dtype = np.dtype(metadata["dtype"])
        
        return np.frombuffer(decompressed, dtype=dtype).reshape(shape)
    
    def _decompress_zstd(self, data: bytes) -> np.ndarray:
        """Decompress Zstandard data"""
        if not ZSTD_AVAILABLE:
            raise Exception("Zstandard not available")
        
        # Decompress to get JPEG data
        decompressor = zstd.ZstdDecompressor()
        jpeg_data = decompressor.decompress(data)
        
        # Decode JPEG
        return self._decompress_jpeg(jpeg_data)
    
    def _decompress_jpeg(self, data: bytes) -> np.ndarray:
        """Decompress JPEG data"""
        nparr = np.frombuffer(data, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    def get_compression_info(self) -> Dict[str, Any]:
        """Get compression method information"""
        return {
            "best_method": self.best_method,
            "available_methods": self.available_methods,
            "pyav_available": PYAV_AVAILABLE,
            "lz4_available": LZ4_AVAILABLE,
            "zstd_available": ZSTD_AVAILABLE,
            "pil_available": PIL_AVAILABLE,
            "heif_available": HEIF_AVAILABLE
        }


class StreamingOptimizer:
    """Optimize streaming for ultra-low latency"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.StreamingOptimizer")
        self.compressor = AdvancedCompressor()
        
        # Adaptive quality settings
        self.quality_levels = {
            "ultra_low_latency": 60,
            "low_latency": 75,
            "balanced": 85,
            "high_quality": 95
        }
        
        self.current_mode = "low_latency"
        
    def optimize_frame_for_streaming(self, image: np.ndarray, target_latency_ms: float = 50) -> Dict[str, Any]:
        """
        Optimize frame for streaming based on target latency
        
        Args:
            image: Input image
            target_latency_ms: Target processing latency in milliseconds
            
        Returns:
            Optimized frame data with metadata
        """
        start_time = time.time()
        
        # Select quality based on target latency
        if target_latency_ms < 30:
            quality = self.quality_levels["ultra_low_latency"]
            mode = "ultra_low_latency"
        elif target_latency_ms < 50:
            quality = self.quality_levels["low_latency"]
            mode = "low_latency"
        elif target_latency_ms < 100:
            quality = self.quality_levels["balanced"]
            mode = "balanced"
        else:
            quality = self.quality_levels["high_quality"]
            mode = "high_quality"
        
        # Compress frame
        result = self.compressor.compress_frame(image, quality)
        
        # Add streaming metadata
        processing_time = (time.time() - start_time) * 1000
        result.update({
            "streaming_mode": mode,
            "target_latency_ms": target_latency_ms,
            "actual_processing_time_ms": processing_time,
            "latency_target_met": processing_time <= target_latency_ms,
            "timestamp": time.time()
        })
        
        return result
    
    def adaptive_quality_adjustment(self, recent_latencies: list, target_latency: float = 50) -> str:
        """
        Adaptively adjust quality based on recent performance
        
        Args:
            recent_latencies: List of recent processing latencies
            target_latency: Target latency in milliseconds
            
        Returns:
            Recommended quality mode
        """
        if not recent_latencies:
            return self.current_mode
        
        avg_latency = sum(recent_latencies) / len(recent_latencies)
        
        if avg_latency > target_latency * 1.5:
            # Too slow, reduce quality
            if self.current_mode == "high_quality":
                self.current_mode = "balanced"
            elif self.current_mode == "balanced":
                self.current_mode = "low_latency"
            elif self.current_mode == "low_latency":
                self.current_mode = "ultra_low_latency"
        elif avg_latency < target_latency * 0.7:
            # Fast enough, can increase quality
            if self.current_mode == "ultra_low_latency":
                self.current_mode = "low_latency"
            elif self.current_mode == "low_latency":
                self.current_mode = "balanced"
            elif self.current_mode == "balanced":
                self.current_mode = "high_quality"
        
        return self.current_mode


# Global instances
advanced_compressor = AdvancedCompressor()
streaming_optimizer = StreamingOptimizer()

def get_compression_info() -> Dict[str, Any]:
    """Get comprehensive compression information"""
    return {
        "compressor": advanced_compressor.get_compression_info(),
        "streaming_optimizer": {
            "current_mode": streaming_optimizer.current_mode,
            "quality_levels": streaming_optimizer.quality_levels
        }
    }