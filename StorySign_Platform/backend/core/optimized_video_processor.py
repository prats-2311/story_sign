#!/usr/bin/env python3
"""
Optimized Video Processing Pipeline
High-performance video processing with adaptive quality, connection pooling, and message queuing
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import cv2
import numpy as np
import base64

from .websocket_pool import WebSocketConnectionPool, get_connection_pool
from .message_queue import MessageQueueManager, MessagePriority, get_queue_manager
from .adaptive_quality import (
    AdaptiveQualityManager, NetworkMetrics, PerformanceMetrics, 
    QualitySettings, get_adaptive_quality_service
)
from video_processor import FrameProcessor
from config import AppConfig


@dataclass
class ProcessingResult:
    """Result of video processing operation"""
    success: bool
    frame_data: Optional[str] = None
    landmarks_detected: Optional[Dict[str, bool]] = None
    processing_time_ms: float = 0.0
    quality_settings: Optional[QualitySettings] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class OptimizedVideoProcessor:
    """
    High-performance video processor with adaptive quality and optimized pipeline
    """
    
    def __init__(self, client_id: str, config: AppConfig):
        self.client_id = client_id
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.OptimizedVideoProcessor.{client_id}")
        
        # Core components
        self.frame_processor: Optional[FrameProcessor] = None
        self.quality_manager: Optional[AdaptiveQualityManager] = None
        self.connection_pool: Optional[WebSocketConnectionPool] = None
        self.queue_manager: Optional[MessageQueueManager] = None
        
        # Processing state
        self.is_active = False
        self.frame_count = 0
        self.last_frame_time = 0.0
        
        # Performance tracking
        self.processing_stats = {
            "frames_processed": 0,
            "frames_dropped": 0,
            "frames_skipped": 0,
            "total_processing_time": 0.0,
            "avg_processing_time": 0.0,
            "peak_processing_time": 0.0,
            "quality_adaptations": 0,
            "errors": 0
        }
        
        # Frame skipping for adaptive quality
        self.frame_skip_counter = 0
        self.current_skip_rate = 0
        
        # Batch processing
        self.batch_frames: List[Dict[str, Any]] = []
        self.batch_timer: Optional[asyncio.Task] = None
        self.batch_timeout = 0.05  # 50ms
        
        # Network monitoring
        self.network_monitor = NetworkMonitor(client_id)
        
    async def initialize(self):
        """Initialize the optimized video processor"""
        try:
            # Initialize frame processor
            self.frame_processor = FrameProcessor(
                video_config=self.config.video,
                mediapipe_config=self.config.mediapipe,
                gesture_config=self.config.gesture_detection
            )
            
            # Get global services
            adaptive_service = await get_adaptive_quality_service()
            self.quality_manager = adaptive_service.add_client(self.client_id)
            
            self.connection_pool = await get_connection_pool()
            self.queue_manager = get_queue_manager()
            
            # Create processing queues
            await self._setup_processing_queues()
            
            # Start network monitoring
            await self.network_monitor.start()
            
            self.logger.info(f"Optimized video processor initialized for client {self.client_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize video processor: {e}")
            raise
    
    async def _setup_processing_queues(self):
        """Setup message queues for processing pipeline"""
        try:
            # Create high-priority queue for real-time frames
            await self.queue_manager.create_queue(
                name=f"frames_{self.client_id}",
                max_size=100,  # Small queue for low latency
                batch_size=1,  # No batching for frames
                processor_count=2
            )
            
            # Create normal priority queue for analysis results
            await self.queue_manager.create_queue(
                name=f"analysis_{self.client_id}",
                max_size=50,
                batch_size=3,
                processor_count=1
            )
            
            # Add message handlers
            frame_queue = self.queue_manager.get_queue(f"frames_{self.client_id}")
            if frame_queue:
                frame_queue.add_handler(self._handle_frame_message)
            
            analysis_queue = self.queue_manager.get_queue(f"analysis_{self.client_id}")
            if analysis_queue:
                analysis_queue.add_handler(self._handle_analysis_message)
            
            self.logger.debug(f"Processing queues setup for client {self.client_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to setup processing queues: {e}")
            raise
    
    async def start_processing(self):
        """Start the optimized processing pipeline"""
        self.is_active = True
        self.logger.info(f"Started optimized processing for client {self.client_id}")
    
    async def stop_processing(self):
        """Stop the processing pipeline and cleanup"""
        self.is_active = False
        
        # Cancel batch timer
        if self.batch_timer:
            self.batch_timer.cancel()
        
        # Stop network monitoring
        await self.network_monitor.stop()
        
        # Remove from adaptive quality service
        adaptive_service = await get_adaptive_quality_service()
        adaptive_service.remove_client(self.client_id)
        
        # Remove queues
        await self.queue_manager.remove_queue(f"frames_{self.client_id}")
        await self.queue_manager.remove_queue(f"analysis_{self.client_id}")
        
        # Cleanup frame processor
        if self.frame_processor:
            self.frame_processor.close()
        
        self.logger.info(f"Stopped optimized processing for client {self.client_id}")
    
    async def process_frame(self, frame_data: Dict[str, Any]) -> ProcessingResult:
        """
        Process a video frame through the optimized pipeline
        
        Args:
            frame_data: Frame data dictionary
            
        Returns:
            ProcessingResult with processed frame and metadata
        """
        start_time = time.time()
        
        try:
            # Update network metrics
            await self._update_network_metrics(frame_data)
            
            # Get current quality settings
            quality_settings = self.quality_manager.get_current_settings()
            
            # Check if frame should be skipped for adaptive quality
            if self._should_skip_frame(quality_settings):
                self.processing_stats["frames_skipped"] += 1
                return ProcessingResult(
                    success=True,
                    frame_data=frame_data.get("frame_data"),  # Return original frame
                    landmarks_detected={"hands": False, "face": False, "pose": False},
                    processing_time_ms=0.0,
                    quality_settings=quality_settings,
                    metadata={"skipped": True, "reason": "adaptive_quality"}
                )
            
            # Process frame based on quality settings
            if quality_settings.batch_size > 1:
                # Add to batch
                return await self._add_to_batch(frame_data, quality_settings)
            else:
                # Process immediately
                return await self._process_single_frame(frame_data, quality_settings)
        
        except Exception as e:
            self.processing_stats["errors"] += 1
            self.logger.error(f"Frame processing error: {e}")
            
            return ProcessingResult(
                success=False,
                error_message=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    def _should_skip_frame(self, quality_settings: QualitySettings) -> bool:
        """Determine if frame should be skipped based on quality settings"""
        if quality_settings.skip_frames == 0:
            return False
        
        self.frame_skip_counter += 1
        
        if self.frame_skip_counter >= quality_settings.skip_frames:
            self.frame_skip_counter = 0
            return False  # Process this frame
        
        return True  # Skip this frame
    
    async def _add_to_batch(self, frame_data: Dict[str, Any], quality_settings: QualitySettings) -> ProcessingResult:
        """Add frame to batch for processing"""
        self.batch_frames.append({
            "frame_data": frame_data,
            "timestamp": time.time(),
            "quality_settings": quality_settings
        })
        
        # Check if batch is ready
        if len(self.batch_frames) >= quality_settings.batch_size:
            return await self._process_batch()
        elif len(self.batch_frames) == 1:
            # Start batch timer
            self.batch_timer = asyncio.create_task(self._batch_timeout_handler())
        
        # Return placeholder result for batched processing
        return ProcessingResult(
            success=True,
            frame_data=frame_data.get("frame_data"),
            landmarks_detected={"hands": False, "face": False, "pose": False},
            processing_time_ms=0.0,
            quality_settings=quality_settings,
            metadata={"batched": True, "batch_size": len(self.batch_frames)}
        )
    
    async def _batch_timeout_handler(self):
        """Handle batch timeout"""
        try:
            await asyncio.sleep(self.batch_timeout)
            if self.batch_frames:
                await self._process_batch()
        except asyncio.CancelledError:
            pass
    
    async def _process_batch(self) -> ProcessingResult:
        """Process batched frames"""
        if not self.batch_frames:
            return ProcessingResult(success=False, error_message="Empty batch")
        
        # Cancel batch timer
        if self.batch_timer:
            self.batch_timer.cancel()
            self.batch_timer = None
        
        batch = self.batch_frames.copy()
        self.batch_frames.clear()
        
        start_time = time.time()
        
        try:
            # Process the most recent frame from the batch
            latest_frame = batch[-1]
            result = await self._process_single_frame(
                latest_frame["frame_data"],
                latest_frame["quality_settings"]
            )
            
            # Update metadata
            if result.metadata is None:
                result.metadata = {}
            result.metadata.update({
                "batch_processed": True,
                "batch_size": len(batch),
                "frames_dropped": len(batch) - 1
            })
            
            # Update stats
            self.processing_stats["frames_dropped"] += len(batch) - 1
            
            return result
        
        except Exception as e:
            self.logger.error(f"Batch processing error: {e}")
            return ProcessingResult(
                success=False,
                error_message=str(e),
                processing_time_ms=(time.time() - start_time) * 1000
            )
    
    async def _process_single_frame(self, frame_data: Dict[str, Any], quality_settings: QualitySettings) -> ProcessingResult:
        """Process a single frame with quality optimizations"""
        start_time = time.time()
        
        try:
            # Decode frame
            base64_data = frame_data.get("frame_data", "")
            if not base64_data:
                raise ValueError("No frame data provided")
            
            frame = self._decode_frame(base64_data)
            if frame is None:
                raise ValueError("Failed to decode frame")
            
            # Apply resolution scaling
            if quality_settings.resolution_scale < 1.0:
                frame = self._scale_frame(frame, quality_settings.resolution_scale)
            
            # Process with MediaPipe (with complexity setting)
            processed_frame, landmarks_detected = await self._process_with_mediapipe(
                frame, quality_settings.mediapipe_complexity
            )
            
            # Encode result with quality settings
            encoded_result = self._encode_frame(processed_frame, quality_settings)
            
            processing_time = (time.time() - start_time) * 1000
            
            # Update statistics
            self._update_processing_stats(processing_time)
            
            # Update performance metrics for adaptive quality
            await self._update_performance_metrics(processing_time)
            
            return ProcessingResult(
                success=True,
                frame_data=encoded_result,
                landmarks_detected=landmarks_detected,
                processing_time_ms=processing_time,
                quality_settings=quality_settings,
                metadata={
                    "frame_number": self.frame_count,
                    "resolution_scale": quality_settings.resolution_scale,
                    "jpeg_quality": quality_settings.jpeg_quality,
                    "mediapipe_complexity": quality_settings.mediapipe_complexity
                }
            )
        
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            self.logger.error(f"Single frame processing error: {e}")
            
            return ProcessingResult(
                success=False,
                error_message=str(e),
                processing_time_ms=processing_time
            )
    
    def _decode_frame(self, base64_data: str) -> Optional[np.ndarray]:
        """Decode base64 frame data"""
        try:
            # Remove data URL prefix if present
            if base64_data.startswith('data:image/jpeg;base64,'):
                base64_data = base64_data.split(',', 1)[1]
            
            # Decode base64
            image_bytes = base64.b64decode(base64_data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            
            # Decode JPEG
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return frame
        
        except Exception as e:
            self.logger.error(f"Frame decode error: {e}")
            return None
    
    def _scale_frame(self, frame: np.ndarray, scale: float) -> np.ndarray:
        """Scale frame for resolution optimization"""
        try:
            height, width = frame.shape[:2]
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            return cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
        
        except Exception as e:
            self.logger.error(f"Frame scaling error: {e}")
            return frame
    
    async def _process_with_mediapipe(self, frame: np.ndarray, complexity: int) -> tuple:
        """Process frame with MediaPipe using specified complexity"""
        try:
            # Update MediaPipe complexity if needed
            if hasattr(self.frame_processor.mediapipe_processor, 'holistic'):
                # Note: MediaPipe complexity can't be changed after initialization
                # This would require recreating the processor, which is expensive
                pass
            
            # Process frame
            processed_frame, landmarks_detected, _ = self.frame_processor.process_frame_with_mediapipe(frame)
            
            return processed_frame, landmarks_detected
        
        except Exception as e:
            self.logger.error(f"MediaPipe processing error: {e}")
            return frame, {"hands": False, "face": False, "pose": False}
    
    def _encode_frame(self, frame: np.ndarray, quality_settings: QualitySettings) -> str:
        """Encode frame with quality settings"""
        try:
            # Set JPEG encoding parameters
            encode_params = [
                cv2.IMWRITE_JPEG_QUALITY, quality_settings.jpeg_quality,
                cv2.IMWRITE_JPEG_OPTIMIZE, 1 if quality_settings.compression_level < 5 else 0,
                cv2.IMWRITE_JPEG_PROGRESSIVE, 0  # Disable for speed
            ]
            
            # Encode frame
            success, buffer = cv2.imencode('.jpg', frame, encode_params)
            if not success:
                raise ValueError("Failed to encode frame")
            
            # Convert to base64
            base64_data = base64.b64encode(buffer).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_data}"
        
        except Exception as e:
            self.logger.error(f"Frame encoding error: {e}")
            raise
    
    def _update_processing_stats(self, processing_time_ms: float):
        """Update processing statistics"""
        self.frame_count += 1
        self.processing_stats["frames_processed"] += 1
        self.processing_stats["total_processing_time"] += processing_time_ms
        
        # Update averages
        if self.processing_stats["frames_processed"] > 0:
            self.processing_stats["avg_processing_time"] = (
                self.processing_stats["total_processing_time"] / 
                self.processing_stats["frames_processed"]
            )
        
        # Update peak
        self.processing_stats["peak_processing_time"] = max(
            self.processing_stats["peak_processing_time"],
            processing_time_ms
        )
    
    async def _update_network_metrics(self, frame_data: Dict[str, Any]):
        """Update network metrics from frame data"""
        try:
            metadata = frame_data.get("metadata", {})
            
            # Extract network metrics if available
            latency = metadata.get("network_latency_ms", 0.0)
            throughput = metadata.get("throughput_mbps", 0.0)
            
            if latency > 0 or throughput > 0:
                network_metrics = NetworkMetrics(
                    latency_ms=latency,
                    throughput_mbps=throughput,
                    bandwidth_mbps=throughput,  # Approximate
                    packet_loss_percent=0.0,  # Would need separate measurement
                    jitter_ms=0.0,  # Would need separate measurement
                    connection_stability=1.0  # Assume stable if receiving frames
                )
                
                self.quality_manager.update_network_metrics(network_metrics)
        
        except Exception as e:
            self.logger.debug(f"Network metrics update error: {e}")
    
    async def _update_performance_metrics(self, processing_time_ms: float):
        """Update performance metrics for adaptive quality"""
        try:
            import psutil
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            
            # Calculate frame drop rate
            total_frames = (self.processing_stats["frames_processed"] + 
                          self.processing_stats["frames_dropped"] + 
                          self.processing_stats["frames_skipped"])
            
            frame_drop_rate = 0.0
            if total_frames > 0:
                frame_drop_rate = (self.processing_stats["frames_dropped"] / total_frames) * 100
            
            # Calculate error rate
            error_rate = 0.0
            if total_frames > 0:
                error_rate = (self.processing_stats["errors"] / total_frames) * 100
            
            performance_metrics = PerformanceMetrics(
                cpu_usage_percent=cpu_percent,
                memory_usage_percent=memory_percent,
                processing_time_ms=processing_time_ms,
                queue_depth=0,  # Would need queue reference
                frame_drop_rate=frame_drop_rate,
                error_rate=error_rate
            )
            
            self.quality_manager.update_performance_metrics(performance_metrics)
        
        except Exception as e:
            self.logger.debug(f"Performance metrics update error: {e}")
    
    async def _handle_frame_message(self, message):
        """Handle frame processing message from queue"""
        try:
            frame_data = message.content
            result = await self.process_frame(frame_data)
            
            # Send result back through connection pool if successful
            if result.success and self.connection_pool:
                response = {
                    "type": "processed_frame",
                    "timestamp": datetime.now().isoformat(),
                    "frame_data": result.frame_data,
                    "landmarks_detected": result.landmarks_detected,
                    "metadata": {
                        "processing_time_ms": result.processing_time_ms,
                        "quality_profile": result.quality_settings.profile.value if result.quality_settings else None,
                        **(result.metadata or {})
                    }
                }
                
                await self.connection_pool.send_message(
                    self.client_id, 
                    response, 
                    priority=True
                )
        
        except Exception as e:
            self.logger.error(f"Frame message handling error: {e}")
    
    async def _handle_analysis_message(self, message):
        """Handle analysis result message from queue"""
        try:
            analysis_data = message.content
            
            # Send analysis result through connection pool
            if self.connection_pool:
                response = {
                    "type": "asl_feedback",
                    "timestamp": datetime.now().isoformat(),
                    "data": analysis_data
                }
                
                await self.connection_pool.send_message(
                    self.client_id,
                    response,
                    priority=False
                )
        
        except Exception as e:
            self.logger.error(f"Analysis message handling error: {e}")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            "client_id": self.client_id,
            "is_active": self.is_active,
            "frame_count": self.frame_count,
            "processing_stats": self.processing_stats.copy(),
            "current_quality": self.quality_manager.get_current_settings().to_dict() if self.quality_manager else None,
            "adaptation_stats": self.quality_manager.get_adaptation_stats() if self.quality_manager else None
        }


class NetworkMonitor:
    """
    Network performance monitor for adaptive quality
    """
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.logger = logging.getLogger(f"{__name__}.NetworkMonitor.{client_id}")
        
        self.monitoring_active = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Metrics tracking
        self.last_bytes_sent = 0
        self.last_bytes_received = 0
        self.last_measurement_time = 0.0
    
    async def start(self):
        """Start network monitoring"""
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.debug(f"Network monitoring started for client {self.client_id}")
    
    async def stop(self):
        """Stop network monitoring"""
        self.monitoring_active = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.debug(f"Network monitoring stopped for client {self.client_id}")
    
    async def _monitoring_loop(self):
        """Network monitoring loop"""
        while self.monitoring_active:
            try:
                await asyncio.sleep(5.0)  # Monitor every 5 seconds
                
                # Collect network metrics
                # This is a placeholder - in a real implementation,
                # you would collect actual network statistics
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Network monitoring error: {e}")


# Global optimized processors
_processors: Dict[str, OptimizedVideoProcessor] = {}


async def create_optimized_processor(client_id: str, config: AppConfig) -> OptimizedVideoProcessor:
    """Create and initialize an optimized video processor"""
    global _processors
    
    if client_id in _processors:
        return _processors[client_id]
    
    processor = OptimizedVideoProcessor(client_id, config)
    await processor.initialize()
    await processor.start_processing()
    
    _processors[client_id] = processor
    return processor


async def remove_optimized_processor(client_id: str):
    """Remove and cleanup an optimized video processor"""
    global _processors
    
    if client_id in _processors:
        processor = _processors[client_id]
        await processor.stop_processing()
        del _processors[client_id]


def get_optimized_processor(client_id: str) -> Optional[OptimizedVideoProcessor]:
    """Get an existing optimized video processor"""
    return _processors.get(client_id)


async def cleanup_all_processors():
    """Cleanup all optimized video processors"""
    global _processors
    
    for processor in _processors.values():
        await processor.stop_processing()
    
    _processors.clear()