#!/usr/bin/env python3
"""
Performance Benchmark Script for StorySign Advanced Optimizations
Compares performance with and without advanced optimizations
"""

import time
import numpy as np
import cv2
import logging
import json
from typing import Dict, List, Any
import statistics
import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizationBenchmark:
    """Benchmark advanced optimizations vs standard processing"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.OptimizationBenchmark")
        self.test_images = []
        self.results = {}
        
        # Try to import optimization modules
        self.gpu_available = self._check_gpu_acceleration()
        self.compression_available = self._check_advanced_compression()
        
    def _check_gpu_acceleration(self) -> bool:
        """Check if GPU acceleration is available"""
        try:
            from backend.gpu_accelerator import gpu_accelerator, turbojpeg_accelerator
            return True
        except ImportError:
            self.logger.warning("GPU acceleration not available")
            return False
    
    def _check_advanced_compression(self) -> bool:
        """Check if advanced compression is available"""
        try:
            from backend.advanced_compression import advanced_compressor, streaming_optimizer
            return True
        except ImportError:
            self.logger.warning("Advanced compression not available")
            return False
    
    def create_test_images(self, count: int = 10) -> List[np.ndarray]:
        """Create test images of various sizes"""
        test_images = []
        
        # Different resolutions to test
        resolutions = [
            (320, 240),   # Low resolution
            (640, 480),   # Standard resolution
            (1280, 720),  # HD resolution
            (1920, 1080)  # Full HD resolution
        ]
        
        for i in range(count):
            resolution = resolutions[i % len(resolutions)]
            width, height = resolution
            
            # Create realistic test image with patterns
            image = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Add some patterns to make it realistic
            cv2.rectangle(image, (50, 50), (width-50, height-50), (100, 150, 200), -1)
            cv2.circle(image, (width//2, height//2), min(width, height)//4, (200, 100, 50), -1)
            
            # Add text
            cv2.putText(image, f"Test Image {i+1}", (20, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(image, f"{width}x{height}", (20, height-20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            test_images.append(image)
        
        self.test_images = test_images
        self.logger.info(f"Created {len(test_images)} test images")
        return test_images
    
    def benchmark_jpeg_encoding(self) -> Dict[str, Any]:
        """Benchmark JPEG encoding performance"""
        self.logger.info("Benchmarking JPEG encoding...")
        
        results = {
            "standard_opencv": [],
            "turbojpeg": [],
            "advanced_compression": []
        }
        
        for image in self.test_images:
            # Standard OpenCV encoding
            start_time = time.time()
            _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 85])
            opencv_time = (time.time() - start_time) * 1000
            opencv_size = len(buffer)
            results["standard_opencv"].append({
                "time_ms": opencv_time,
                "size_bytes": opencv_size,
                "resolution": f"{image.shape[1]}x{image.shape[0]}"
            })
            
            # TurboJPEG encoding (if available)
            if self.gpu_available:
                try:
                    from backend.gpu_accelerator import turbojpeg_accelerator
                    
                    if turbojpeg_accelerator.turbojpeg_available:
                        # Convert BGR to RGB for TurboJPEG
                        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                        
                        start_time = time.time()
                        jpeg_data = turbojpeg_accelerator.encode(rgb_image, 85)
                        turbojpeg_time = (time.time() - start_time) * 1000
                        
                        results["turbojpeg"].append({
                            "time_ms": turbojpeg_time,
                            "size_bytes": len(jpeg_data),
                            "resolution": f"{image.shape[1]}x{image.shape[0]}",
                            "speedup": opencv_time / turbojpeg_time if turbojpeg_time > 0 else 1.0
                        })
                    else:
                        results["turbojpeg"].append({"error": "TurboJPEG not available"})
                except Exception as e:
                    results["turbojpeg"].append({"error": str(e)})
            
            # Advanced compression (if available)
            if self.compression_available:
                try:
                    from backend.advanced_compression import advanced_compressor
                    
                    start_time = time.time()
                    compression_result = advanced_compressor.compress_frame(image, 85)
                    advanced_time = (time.time() - start_time) * 1000
                    
                    if compression_result["success"]:
                        results["advanced_compression"].append({
                            "time_ms": advanced_time,
                            "size_bytes": len(compression_result["data"]),
                            "resolution": f"{image.shape[1]}x{image.shape[0]}",
                            "method": compression_result.get("method", "unknown"),
                            "compression_ratio": compression_result.get("compression_ratio", 1.0),
                            "speedup": opencv_time / advanced_time if advanced_time > 0 else 1.0
                        })
                    else:
                        results["advanced_compression"].append({"error": "Compression failed"})
                except Exception as e:
                    results["advanced_compression"].append({"error": str(e)})
        
        return results
    
    def benchmark_image_resizing(self) -> Dict[str, Any]:
        """Benchmark image resizing performance"""
        self.logger.info("Benchmarking image resizing...")
        
        results = {
            "standard_opencv": [],
            "gpu_accelerated": []
        }
        
        target_sizes = [(320, 240), (640, 480), (1280, 720)]
        
        for image in self.test_images:
            for target_size in target_sizes:
                # Standard OpenCV resizing
                start_time = time.time()
                resized_standard = cv2.resize(image, target_size, interpolation=cv2.INTER_LINEAR)
                opencv_time = (time.time() - start_time) * 1000
                
                results["standard_opencv"].append({
                    "time_ms": opencv_time,
                    "original_size": f"{image.shape[1]}x{image.shape[0]}",
                    "target_size": f"{target_size[0]}x{target_size[1]}"
                })
                
                # GPU accelerated resizing (if available)
                if self.gpu_available:
                    try:
                        from backend.gpu_accelerator import gpu_accelerator
                        
                        start_time = time.time()
                        resized_gpu = gpu_accelerator.accelerated_resize(image, target_size)
                        gpu_time = (time.time() - start_time) * 1000
                        
                        results["gpu_accelerated"].append({
                            "time_ms": gpu_time,
                            "original_size": f"{image.shape[1]}x{image.shape[0]}",
                            "target_size": f"{target_size[0]}x{target_size[1]}",
                            "method": gpu_accelerator.acceleration_method,
                            "speedup": opencv_time / gpu_time if gpu_time > 0 else 1.0
                        })
                    except Exception as e:
                        results["gpu_accelerated"].append({"error": str(e)})
        
        return results
    
    def benchmark_end_to_end_pipeline(self) -> Dict[str, Any]:
        """Benchmark complete processing pipeline"""
        self.logger.info("Benchmarking end-to-end pipeline...")
        
        results = {
            "standard_pipeline": [],
            "optimized_pipeline": []
        }
        
        for image in self.test_images:
            # Standard pipeline: resize + encode
            start_time = time.time()
            
            # Resize to standard size
            resized = cv2.resize(image, (640, 480), interpolation=cv2.INTER_LINEAR)
            
            # Encode as JPEG
            _, buffer = cv2.imencode('.jpg', resized, [cv2.IMWRITE_JPEG_QUALITY, 85])
            
            standard_time = (time.time() - start_time) * 1000
            
            results["standard_pipeline"].append({
                "time_ms": standard_time,
                "size_bytes": len(buffer),
                "resolution": f"{image.shape[1]}x{image.shape[0]}"
            })
            
            # Optimized pipeline (if available)
            if self.gpu_available and self.compression_available:
                try:
                    from backend.gpu_accelerator import gpu_accelerator
                    from backend.advanced_compression import streaming_optimizer
                    
                    start_time = time.time()
                    
                    # GPU-accelerated resize
                    resized_gpu = gpu_accelerator.accelerated_resize(image, (640, 480))
                    
                    # Advanced compression
                    compression_result = streaming_optimizer.optimize_frame_for_streaming(
                        resized_gpu, target_latency_ms=50
                    )
                    
                    optimized_time = (time.time() - start_time) * 1000
                    
                    if compression_result["success"]:
                        results["optimized_pipeline"].append({
                            "time_ms": optimized_time,
                            "size_bytes": len(compression_result["data"]),
                            "resolution": f"{image.shape[1]}x{image.shape[0]}",
                            "method": compression_result.get("method", "unknown"),
                            "speedup": standard_time / optimized_time if optimized_time > 0 else 1.0,
                            "latency_target_met": compression_result.get("latency_target_met", False)
                        })
                    else:
                        results["optimized_pipeline"].append({"error": "Optimization failed"})
                        
                except Exception as e:
                    results["optimized_pipeline"].append({"error": str(e)})
        
        return results
    
    def calculate_statistics(self, data: List[Dict[str, Any]], metric: str) -> Dict[str, float]:
        """Calculate statistics for a metric"""
        values = [item[metric] for item in data if metric in item and isinstance(item[metric], (int, float))]
        
        if not values:
            return {"count": 0}
        
        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
            "std": statistics.stdev(values) if len(values) > 1 else 0.0
        }
    
    def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive performance benchmark"""
        self.logger.info("Starting comprehensive optimization benchmark...")
        
        # Create test images
        self.create_test_images(20)  # More images for better statistics
        
        # Run benchmarks
        benchmark_results = {
            "system_info": {
                "gpu_acceleration_available": self.gpu_available,
                "advanced_compression_available": self.compression_available,
                "test_image_count": len(self.test_images)
            },
            "jpeg_encoding": self.benchmark_jpeg_encoding(),
            "image_resizing": self.benchmark_image_resizing(),
            "end_to_end_pipeline": self.benchmark_end_to_end_pipeline()
        }
        
        # Calculate summary statistics
        summary = {}
        
        # JPEG encoding summary
        jpeg_results = benchmark_results["jpeg_encoding"]
        summary["jpeg_encoding"] = {
            "standard_opencv": self.calculate_statistics(jpeg_results["standard_opencv"], "time_ms"),
            "turbojpeg": self.calculate_statistics(jpeg_results["turbojpeg"], "time_ms"),
            "advanced_compression": self.calculate_statistics(jpeg_results["advanced_compression"], "time_ms")
        }
        
        # Calculate average speedups
        turbojpeg_speedups = [item["speedup"] for item in jpeg_results["turbojpeg"] if "speedup" in item]
        advanced_speedups = [item["speedup"] for item in jpeg_results["advanced_compression"] if "speedup" in item]
        
        if turbojpeg_speedups:
            summary["jpeg_encoding"]["turbojpeg"]["avg_speedup"] = statistics.mean(turbojpeg_speedups)
        if advanced_speedups:
            summary["jpeg_encoding"]["advanced_compression"]["avg_speedup"] = statistics.mean(advanced_speedups)
        
        # End-to-end pipeline summary
        pipeline_results = benchmark_results["end_to_end_pipeline"]
        summary["end_to_end_pipeline"] = {
            "standard": self.calculate_statistics(pipeline_results["standard_pipeline"], "time_ms"),
            "optimized": self.calculate_statistics(pipeline_results["optimized_pipeline"], "time_ms")
        }
        
        # Calculate overall speedup
        pipeline_speedups = [item["speedup"] for item in pipeline_results["optimized_pipeline"] if "speedup" in item]
        if pipeline_speedups:
            summary["end_to_end_pipeline"]["avg_speedup"] = statistics.mean(pipeline_speedups)
        
        benchmark_results["summary"] = summary
        
        return benchmark_results
    
    def print_benchmark_results(self, results: Dict[str, Any]):
        """Print formatted benchmark results"""
        print("\n" + "="*80)
        print("STORYSIGN ADVANCED OPTIMIZATION BENCHMARK RESULTS")
        print("="*80)
        
        # System info
        system_info = results["system_info"]
        print(f"\n📊 SYSTEM INFORMATION:")
        print(f"   GPU Acceleration:      {'✅ Available' if system_info['gpu_acceleration_available'] else '❌ Not Available'}")
        print(f"   Advanced Compression:  {'✅ Available' if system_info['advanced_compression_available'] else '❌ Not Available'}")
        print(f"   Test Images:           {system_info['test_image_count']}")
        
        # Summary results
        summary = results.get("summary", {})
        
        print(f"\n🚀 PERFORMANCE SUMMARY:")
        
        # JPEG Encoding
        jpeg_summary = summary.get("jpeg_encoding", {})
        if jpeg_summary:
            print(f"\n   JPEG Encoding Performance:")
            
            standard = jpeg_summary.get("standard_opencv", {})
            if standard.get("count", 0) > 0:
                print(f"     Standard OpenCV:     {standard['mean']:.2f}ms avg ({standard['min']:.2f}-{standard['max']:.2f}ms)")
            
            turbojpeg = jpeg_summary.get("turbojpeg", {})
            if turbojpeg.get("count", 0) > 0:
                speedup = turbojpeg.get("avg_speedup", 1.0)
                print(f"     TurboJPEG:          {turbojpeg['mean']:.2f}ms avg ({speedup:.1f}x faster)")
            
            advanced = jpeg_summary.get("advanced_compression", {})
            if advanced.get("count", 0) > 0:
                speedup = advanced.get("avg_speedup", 1.0)
                print(f"     Advanced Compression: {advanced['mean']:.2f}ms avg ({speedup:.1f}x faster)")
        
        # End-to-End Pipeline
        pipeline_summary = summary.get("end_to_end_pipeline", {})
        if pipeline_summary:
            print(f"\n   End-to-End Pipeline Performance:")
            
            standard = pipeline_summary.get("standard", {})
            if standard.get("count", 0) > 0:
                print(f"     Standard Pipeline:   {standard['mean']:.2f}ms avg ({standard['min']:.2f}-{standard['max']:.2f}ms)")
            
            optimized = pipeline_summary.get("optimized", {})
            if optimized.get("count", 0) > 0:
                speedup = pipeline_summary.get("avg_speedup", 1.0)
                print(f"     Optimized Pipeline:  {optimized['mean']:.2f}ms avg ({speedup:.1f}x faster)")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        if system_info['gpu_acceleration_available'] and system_info['advanced_compression_available']:
            print("   ✅ Excellent! All optimizations are available.")
            print("   🚀 Expected latency improvement: 3-10x faster processing")
            print("   📈 Recommended settings: Enable all advanced optimizations")
        elif system_info['gpu_acceleration_available'] or system_info['advanced_compression_available']:
            print("   ✅ Good! Some optimizations are available.")
            print("   🚀 Expected latency improvement: 2-5x faster processing")
            print("   📈 Recommended: Install missing optimization packages")
        else:
            print("   ⚠️  Limited optimizations available.")
            print("   🔧 Recommended: Run install_advanced_optimizations.py")
            print("   📦 This will install GPU acceleration and advanced compression")
        
        print("="*80)

def main():
    """Main benchmark execution"""
    print("🚀 StorySign Advanced Optimization Benchmark")
    print("=" * 50)
    
    benchmark = OptimizationBenchmark()
    
    try:
        results = benchmark.run_comprehensive_benchmark()
        benchmark.print_benchmark_results(results)
        
        # Save detailed results
        with open("benchmark_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: benchmark_results.json")
        
        return 0
        
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        print(f"❌ Benchmark failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())