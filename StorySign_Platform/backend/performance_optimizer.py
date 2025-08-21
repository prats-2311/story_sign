#!/usr/bin/env python3
"""
Advanced Performance Optimizer for StorySign ASL Platform
Implements adaptive quality settings, frame rate optimization, and threading strategies
"""

import asyncio
import logging
import time
import threading
from typing import Dict, Any, Optional, List, Tuple
from collections import deque
from dataclasses import dataclass
import psutil
import numpy as np

from config import AppConfig

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics for optimization decisions"""
    avg_processing_time: float = 0.0
    peak_processing_time: float = 0.0
    frames_per_second: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    queue_depth: int = 0
    frames_dropped: int = 0
    error_rate: float = 0.0
    latency_ms: float = 0.0

class AdaptiveQualityManager:
    """Manages adaptive quality settings based on performance"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.AdaptiveQualityManager")
        
        # Quality levels with performance targets
        self.quality_profiles = {
            "ultra_performance": {
                "jpeg_quality": 40,
                "resolution_scale": 0.6,
                "frame_skip": 3,
                "mediapipe_complexity": 0,
                "target_fps": 30,
                "target_latency_ms": 30
            },
            "high_performance": {
                "jpeg_quality": 50,
                "resolution_scale": 0.75,
                "frame_skip": 2,
                "mediapipe_complexity": 0,
                "target_fps": 25,
                "target_latency_ms": 50
            },
            "balanced": {
                "jpeg_quality": 65,
                "resolution_scale": 0.85,
                "frame_skip": 1,
                "mediapipe_complexity": 1,
                "target_fps": 20,
                "target_latency_ms": 75
            },
            "high_quality": {
                "jpeg_quality": 80,
                "resolution_scale": 1.0,
                "frame_skip": 0,
                "mediapipe_complexity": 1,
                "target_fps": 15,
                "target_latency_ms": 100
            }
        }
        
        self.current_profile = "balanced"
        self.performance_history = deque(maxlen=30)  # 30 seconds of history
        self.last_adjustment = 0
        self.adjustment_cooldown = 5.0  # 5 seconds between adjustments
        
    def get_current_settings(self) -> Dict[str, Any]:
        """Get current quality settings"""
        return self.quality_profiles[self.current_profile].copy()
    
    def update_performance_metrics(self, metrics: PerformanceMetrics):
        """Update performance metrics and adjust quality if needed"""
        self.performance_history.append({
            "timestamp": time.time(),
            "metrics": metrics,
            "profile": self.current_profile
        })
        
        # Check if adjustment is needed
        if time.time() - self.last_adjustment > self.adjustment_cooldown:
            new_profile = self._calculate_optimal_profile(metrics)
            if new_profile != self.current_profile:
                self._adjust_quality_profile(new_profile, metrics)
    
    def _calculate_optimal_profile(self, metrics: PerformanceMetrics) -> str:
        """Calculate optimal quality profile based on current performance"""
        current_settings = self.quality_profiles[self.current_profile]
        target_latency = current_settings["target_latency_ms"]
        
        # Performance indicators
        latency_ratio = metrics.latency_ms / target_latency if target_latency > 0 else 1.0
        cpu_pressure = metrics.cpu_usage / 100.0
        memory_pressure = metrics.memory_usage / 100.0
        error_pressure = metrics.error_rate
        
        # Calculate performance score (lower is better)
        performance_score = (
            latency_ratio * 0.4 +
            cpu_pressure * 0.3 +
            memory_pressure * 0.2 +
            error_pressure * 0.1
        )
        
        # Determine optimal profile
        if performance_score > 1.5:
            # System under heavy load - use ultra performance
            return "ultra_performance"
        elif performance_score > 1.2:
            # System under moderate load - use high performance
            return "high_performance"
        elif performance_score < 0.7:
            # System performing well - can increase quality
            profiles = list(self.quality_profiles.keys())
            current_idx = profiles.index(self.current_profile)
            if current_idx < len(profiles) - 1:
                return profiles[current_idx + 1]
        elif performance_score > 1.0:
            # System struggling - reduce quality
            profiles = list(self.quality_profiles.keys())
            current_idx = profiles.index(self.current_profile)
            if current_idx > 0:
                return profiles[current_idx - 1]
        
        return self.current_profile
    
    def _adjust_quality_profile(self, new_profile: str, metrics: PerformanceMetrics):
        """Adjust quality profile with logging"""
        old_profile = self.current_profile
        self.current_profile = new_profile
        self.last_adjustment = time.time()
        
        self.logger.info(
            f"Quality profile adjusted: {old_profile} → {new_profile} "
            f"(latency: {metrics.latency_ms:.1f}ms, CPU: {metrics.cpu_usage:.1f}%, "
            f"memory: {metrics.memory_usage:.1f}%, errors: {metrics.error_rate:.2f})"
        )

class FrameRateOptimizer:
    """Optimizes frame rate based on processing capability"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.FrameRateOptimizer")
        self.processing_times = deque(maxlen=60)  # 1 minute of history
        self.target_processing_time = 33.33  # 30 FPS target
        self.adaptive_fps = 30
        self.min_fps = 10
        self.max_fps = 60
        
    def update_processing_time(self, processing_time_ms: float):
        """Update processing time and adjust frame rate"""
        self.processing_times.append(processing_time_ms)
        
        if len(self.processing_times) >= 10:  # Need some history
            avg_time = sum(list(self.processing_times)[-10:]) / 10
            self._adjust_frame_rate(avg_time)
    
    def _adjust_frame_rate(self, avg_processing_time: float):
        """Adjust frame rate based on processing performance"""
        # Calculate sustainable FPS based on processing time
        if avg_processing_time > 0:
            sustainable_fps = min(1000 / avg_processing_time, self.max_fps)
            
            # Add safety margin (80% of sustainable rate)
            target_fps = sustainable_fps * 0.8
            
            # Smooth adjustment
            self.adaptive_fps = (self.adaptive_fps * 0.7) + (target_fps * 0.3)
            self.adaptive_fps = max(self.min_fps, min(self.max_fps, self.adaptive_fps))
            
            self.logger.debug(
                f"Frame rate adjusted: {self.adaptive_fps:.1f} FPS "
                f"(processing: {avg_processing_time:.1f}ms, sustainable: {sustainable_fps:.1f})"
            )
    
    def get_frame_interval_ms(self) -> float:
        """Get current frame interval in milliseconds"""
        return 1000 / self.adaptive_fps
    
    def should_process_frame(self, last_frame_time: float) -> bool:
        """Determine if frame should be processed based on timing"""
        current_time = time.time() * 1000  # Convert to ms
        return (current_time - last_frame_time) >= self.get_frame_interval_ms()

class ThreadingOptimizer:
    """Optimizes threading strategy for video processing"""
    
    def __init__(self, max_workers: int = None):
        self.logger = logging.getLogger(f"{__name__}.ThreadingOptimizer")
        self.max_workers = max_workers or min(4, (psutil.cpu_count() or 1) + 1)
        self.thread_pool = None
        self.processing_threads = {}
        self.thread_metrics = {}
        
    def initialize_thread_pool(self):
        """Initialize optimized thread pool"""
        from concurrent.futures import ThreadPoolExecutor
        
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="storysign_processor"
        )
        
        self.logger.info(f"Thread pool initialized with {self.max_workers} workers")
    
    def submit_processing_task(self, task_func, *args, **kwargs):
        """Submit processing task to optimized thread pool"""
        if not self.thread_pool:
            self.initialize_thread_pool()
        
        return self.thread_pool.submit(task_func, *args, **kwargs)
    
    def get_optimal_worker_count(self) -> int:
        """Calculate optimal worker count based on system resources"""
        cpu_count = psutil.cpu_count(logical=False) or 1
        logical_cpu_count = psutil.cpu_count(logical=True) or 1
        
        # For video processing, optimal is usually CPU cores + 1
        # But consider hyperthreading and current load
        current_load = psutil.cpu_percent(interval=0.1)
        
        if current_load > 80:
            # High load - use fewer workers
            return max(1, cpu_count // 2)
        elif current_load < 50:
            # Low load - can use more workers
            return min(logical_cpu_count, cpu_count + 2)
        else:
            # Moderate load - use standard formula
            return cpu_count + 1
    
    def adjust_worker_count(self):
        """Dynamically adjust worker count based on performance"""
        optimal_count = self.get_optimal_worker_count()
        
        if optimal_count != self.max_workers:
            self.logger.info(f"Adjusting worker count: {self.max_workers} → {optimal_count}")
            
            # Shutdown current pool
            if self.thread_pool:
                self.thread_pool.shutdown(wait=False)
            
            # Create new pool with optimal count
            self.max_workers = optimal_count
            self.initialize_thread_pool()
    
    def cleanup(self):
        """Cleanup thread pool resources"""
        if self.thread_pool:
            self.thread_pool.shutdown(wait=True)
            self.logger.info("Thread pool cleaned up")

class CompressionOptimizer:
    """Optimizes compression settings for different scenarios"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.CompressionOptimizer")
        self.compression_profiles = {
            "ultra_fast": {
                "jpeg_quality": 35,
                "optimize": False,
                "progressive": False,
                "subsampling": 2
            },
            "fast": {
                "jpeg_quality": 50,
                "optimize": False,
                "progressive": False,
                "subsampling": 1
            },
            "balanced": {
                "jpeg_quality": 65,
                "optimize": True,
                "progressive": False,
                "subsampling": 1
            },
            "quality": {
                "jpeg_quality": 80,
                "optimize": True,
                "progressive": True,
                "subsampling": 0
            }
        }
        
        self.current_profile = "fast"
    
    def get_compression_params(self, profile: str = None) -> List[int]:
        """Get OpenCV compression parameters for current profile"""
        profile = profile or self.current_profile
        settings = self.compression_profiles.get(profile, self.compression_profiles["fast"])
        
        import cv2
        params = [
            cv2.IMWRITE_JPEG_QUALITY, settings["jpeg_quality"],
            cv2.IMWRITE_JPEG_OPTIMIZE, 1 if settings["optimize"] else 0,
            cv2.IMWRITE_JPEG_PROGRESSIVE, 1 if settings["progressive"] else 0
        ]
        
        # Add subsampling if supported
        if hasattr(cv2, 'IMWRITE_JPEG_SAMPLING_FACTOR'):
            params.extend([cv2.IMWRITE_JPEG_SAMPLING_FACTOR, settings["subsampling"]])
        
        return params
    
    def adjust_compression_profile(self, target_latency_ms: float, current_latency_ms: float):
        """Adjust compression profile based on latency requirements"""
        if current_latency_ms > target_latency_ms * 1.5:
            # Too slow - use faster compression
            if self.current_profile == "quality":
                self.current_profile = "balanced"
            elif self.current_profile == "balanced":
                self.current_profile = "fast"
            elif self.current_profile == "fast":
                self.current_profile = "ultra_fast"
        elif current_latency_ms < target_latency_ms * 0.7:
            # Fast enough - can use better quality
            if self.current_profile == "ultra_fast":
                self.current_profile = "fast"
            elif self.current_profile == "fast":
                self.current_profile = "balanced"
            elif self.current_profile == "balanced":
                self.current_profile = "quality"

class PerformanceOptimizer:
    """Main performance optimizer coordinating all optimization strategies"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.PerformanceOptimizer")
        
        # Initialize optimizers
        self.quality_manager = AdaptiveQualityManager(config)
        self.framerate_optimizer = FrameRateOptimizer()
        self.threading_optimizer = ThreadingOptimizer()
        self.compression_optimizer = CompressionOptimizer()
        
        # Performance monitoring
        self.metrics_history = deque(maxlen=300)  # 5 minutes of history
        self.optimization_active = False
        self.monitoring_task = None
        
    async def start_optimization(self):
        """Start performance optimization monitoring"""
        self.optimization_active = True
        self.threading_optimizer.initialize_thread_pool()
        
        # Start monitoring task
        self.monitoring_task = asyncio.create_task(self._optimization_loop())
        
        self.logger.info("Performance optimization started")
    
    async def stop_optimization(self):
        """Stop performance optimization"""
        self.optimization_active = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.threading_optimizer.cleanup()
        self.logger.info("Performance optimization stopped")
    
    async def _optimization_loop(self):
        """Main optimization monitoring loop"""
        try:
            while self.optimization_active:
                try:
                    # Collect current metrics
                    metrics = await self._collect_performance_metrics()
                    
                    # Update optimizers
                    self.quality_manager.update_performance_metrics(metrics)
                    self.framerate_optimizer.update_processing_time(metrics.avg_processing_time)
                    
                    # Adjust compression based on quality settings
                    quality_settings = self.quality_manager.get_current_settings()
                    self.compression_optimizer.adjust_compression_profile(
                        quality_settings["target_latency_ms"],
                        metrics.latency_ms
                    )
                    
                    # Periodically adjust thread pool
                    if len(self.metrics_history) % 60 == 0:  # Every minute
                        self.threading_optimizer.adjust_worker_count()
                    
                    # Store metrics
                    self.metrics_history.append({
                        "timestamp": time.time(),
                        "metrics": metrics,
                        "quality_profile": self.quality_manager.current_profile,
                        "adaptive_fps": self.framerate_optimizer.adaptive_fps
                    })
                    
                    await asyncio.sleep(1.0)  # Check every second
                    
                except Exception as e:
                    self.logger.error(f"Error in optimization loop: {e}", exc_info=True)
                    await asyncio.sleep(5.0)  # Wait longer on error
                    
        except asyncio.CancelledError:
            self.logger.info("Optimization loop cancelled")
    
    async def _collect_performance_metrics(self) -> PerformanceMetrics:
        """Collect current system performance metrics"""
        try:
            # System metrics
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Calculate averages from recent history
            recent_metrics = list(self.metrics_history)[-10:] if self.metrics_history else []
            
            if recent_metrics:
                avg_processing_time = sum(m["metrics"].avg_processing_time for m in recent_metrics) / len(recent_metrics)
                avg_latency = sum(m["metrics"].latency_ms for m in recent_metrics) / len(recent_metrics)
                total_dropped = sum(m["metrics"].frames_dropped for m in recent_metrics)
            else:
                avg_processing_time = 0.0
                avg_latency = 0.0
                total_dropped = 0
            
            return PerformanceMetrics(
                avg_processing_time=avg_processing_time,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                latency_ms=avg_latency,
                frames_dropped=total_dropped
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting performance metrics: {e}")
            return PerformanceMetrics()
    
    def get_current_optimization_settings(self) -> Dict[str, Any]:
        """Get current optimization settings for all components"""
        return {
            "quality_settings": self.quality_manager.get_current_settings(),
            "adaptive_fps": self.framerate_optimizer.adaptive_fps,
            "frame_interval_ms": self.framerate_optimizer.get_frame_interval_ms(),
            "compression_profile": self.compression_optimizer.current_profile,
            "compression_params": self.compression_optimizer.get_compression_params(),
            "thread_workers": self.threading_optimizer.max_workers,
            "optimization_active": self.optimization_active
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for monitoring"""
        if not self.metrics_history:
            return {"status": "no_data"}
        
        recent_metrics = list(self.metrics_history)[-30:]  # Last 30 seconds
        
        avg_cpu = sum(m["metrics"].cpu_usage for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m["metrics"].memory_usage for m in recent_metrics) / len(recent_metrics)
        avg_latency = sum(m["metrics"].latency_ms for m in recent_metrics) / len(recent_metrics)
        
        return {
            "status": "active",
            "current_profile": self.quality_manager.current_profile,
            "adaptive_fps": round(self.framerate_optimizer.adaptive_fps, 1),
            "avg_cpu_usage": round(avg_cpu, 1),
            "avg_memory_usage": round(avg_memory, 1),
            "avg_latency_ms": round(avg_latency, 1),
            "thread_workers": self.threading_optimizer.max_workers,
            "compression_profile": self.compression_optimizer.current_profile
        }

# Global performance optimizer instance
performance_optimizer: Optional[PerformanceOptimizer] = None

def initialize_performance_optimizer(config: AppConfig) -> PerformanceOptimizer:
    """Initialize global performance optimizer"""
    global performance_optimizer
    performance_optimizer = PerformanceOptimizer(config)
    return performance_optimizer

def get_performance_optimizer() -> Optional[PerformanceOptimizer]:
    """Get global performance optimizer instance"""
    return performance_optimizer