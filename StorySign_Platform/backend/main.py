#!/usr/bin/env python3
"""
StorySign ASL Platform Backend
FastAPI application for real-time ASL recognition and learning
"""

import logging
import sys
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import json
import asyncio
from typing import Optional
import time
from collections import deque
import psutil
import threading

from config import get_config, AppConfig
from video_processor import FrameProcessor

# Load application configuration
try:
    app_config: AppConfig = get_config()
    logger = logging.getLogger(__name__)
    logger.info("Configuration loaded successfully")
except Exception as e:
    # Configure basic logging if config loading fails
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to load configuration: {e}")
    raise

# Configure logging based on configuration
log_level = getattr(logging, app_config.server.log_level.upper())
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('storysign_backend.log')
    ]
)

logger = logging.getLogger(__name__)

class ResourceMonitor:
    """
    Monitor system resources for individual client sessions
    Tracks CPU, memory usage, and processing performance
    """
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.logger = logging.getLogger(f"{__name__}.ResourceMonitor.{client_id}")
        self.monitoring_active = False
        self.monitoring_task = None
        self.stats_history = deque([], 60)  # Keep last 60 measurements (1 minute at 1Hz)
        
    async def start_monitoring(self):
        """Start resource monitoring"""
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info(f"Resource monitoring started for client {self.client_id}")
        
    async def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring_active = False
        if self.monitoring_task and not self.monitoring_task.done():
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        self.logger.info(f"Resource monitoring stopped for client {self.client_id}")
        
    async def _monitoring_loop(self):
        """Monitoring loop that runs every second"""
        try:
            while self.monitoring_active:
                try:
                    # Get current resource stats
                    stats = await self._collect_resource_stats()
                    self.stats_history.append(stats)
                    
                    # Log warning if resources are high
                    if stats['cpu_percent'] > 80 or stats['memory_percent'] > 85:
                        self.logger.warning(f"High resource usage for client {self.client_id}: "
                                          f"CPU: {stats['cpu_percent']:.1f}%, "
                                          f"Memory: {stats['memory_percent']:.1f}%")
                    
                    await asyncio.sleep(1.0)  # Monitor every second
                    
                except Exception as e:
                    self.logger.error(f"Error in resource monitoring for client {self.client_id}: {e}")
                    await asyncio.sleep(1.0)
                    
        except asyncio.CancelledError:
            pass
        
    async def _collect_resource_stats(self) -> dict:
        """Collect current resource statistics"""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            stats = await loop.run_in_executor(None, self._get_system_stats)
            return stats
        except Exception as e:
            self.logger.error(f"Failed to collect resource stats: {e}")
            return {
                'cpu_percent': 0.0,
                'memory_percent': 0.0,
                'memory_mb': 0.0,
                'timestamp': time.time()
            }
    
    def _get_system_stats(self) -> dict:
        """Get system statistics (runs in thread pool)"""
        process = psutil.Process()
        return {
            'cpu_percent': process.cpu_percent(),
            'memory_percent': process.memory_percent(),
            'memory_mb': process.memory_info().rss / 1024 / 1024,
            'timestamp': time.time()
        }
    
    async def get_current_stats(self) -> dict:
        """Get current resource statistics"""
        if self.stats_history:
            return self.stats_history[-1]
        else:
            return await self._collect_resource_stats()
    
    def get_average_stats(self, window_seconds: int = 30) -> dict:
        """Get average statistics over time window"""
        if not self.stats_history:
            return {'cpu_percent': 0.0, 'memory_percent': 0.0, 'memory_mb': 0.0}
        
        # Filter stats within time window
        current_time = time.time()
        recent_stats = [
            stats for stats in self.stats_history 
            if current_time - stats['timestamp'] <= window_seconds
        ]
        
        if not recent_stats:
            return self.stats_history[-1]
        
        # Calculate averages
        avg_cpu = sum(s['cpu_percent'] for s in recent_stats) / len(recent_stats)
        avg_memory = sum(s['memory_percent'] for s in recent_stats) / len(recent_stats)
        avg_memory_mb = sum(s['memory_mb'] for s in recent_stats) / len(recent_stats)
        
        return {
            'cpu_percent': avg_cpu,
            'memory_percent': avg_memory,
            'memory_mb': avg_memory_mb,
            'sample_count': len(recent_stats)
        }


class PerformanceOptimizer:
    """
    Performance optimizer that adjusts processing parameters based on system load
    """
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.PerformanceOptimizer")
        self.optimization_level = 0  # 0 = normal, 1 = light optimization, 2 = aggressive
        self.last_optimization_time = 0
        self.optimization_cooldown = 5.0  # Seconds between optimizations
        
    async def optimize_if_needed(self, resource_stats: dict, processing_stats: dict) -> bool:
        """
        Check if optimization is needed and apply if necessary
        
        Args:
            resource_stats: Current resource usage statistics
            processing_stats: Current processing performance statistics
            
        Returns:
            True if optimization was applied, False otherwise
        """
        current_time = time.time()
        
        # Check cooldown period
        if current_time - self.last_optimization_time < self.optimization_cooldown:
            return False
        
        # Determine if optimization is needed
        cpu_usage = resource_stats.get('cpu_percent', 0)
        memory_usage = resource_stats.get('memory_percent', 0)
        avg_processing_time = processing_stats.get('average_processing_time', 0)
        frames_dropped = processing_stats.get('frames_dropped', 0)
        
        # Define optimization thresholds
        high_cpu_threshold = 75.0
        high_memory_threshold = 80.0
        high_processing_time_threshold = 50.0  # ms
        high_drop_rate_threshold = 10
        
        optimization_needed = False
        new_optimization_level = self.optimization_level
        
        # Check if we need to increase optimization
        if (cpu_usage > high_cpu_threshold or 
            memory_usage > high_memory_threshold or
            avg_processing_time > high_processing_time_threshold or
            frames_dropped > high_drop_rate_threshold):
            
            if self.optimization_level < 2:
                new_optimization_level = min(2, self.optimization_level + 1)
                optimization_needed = True
                
        # Check if we can reduce optimization (system is performing well)
        elif (cpu_usage < 50.0 and 
              memory_usage < 60.0 and
              avg_processing_time < 25.0 and
              frames_dropped == 0):
            
            if self.optimization_level > 0:
                new_optimization_level = max(0, self.optimization_level - 1)
                optimization_needed = True
        
        # Apply optimization if needed
        if optimization_needed:
            await self._apply_optimization_level(new_optimization_level)
            self.optimization_level = new_optimization_level
            self.last_optimization_time = current_time
            
            self.logger.info(f"Performance optimization applied: level {self.optimization_level} "
                           f"(CPU: {cpu_usage:.1f}%, Memory: {memory_usage:.1f}%, "
                           f"Avg time: {avg_processing_time:.1f}ms, Dropped: {frames_dropped})")
            return True
        
        return False
    
    async def _apply_optimization_level(self, level: int):
        """
        Apply specific optimization level
        
        Args:
            level: Optimization level (0=normal, 1=light, 2=aggressive)
        """
        try:
            if level == 0:
                # Normal performance - no optimizations
                self.logger.debug("Applying normal performance settings")
                
            elif level == 1:
                # Light optimization - reduce quality slightly
                self.logger.info("Applying light performance optimization")
                # Could adjust MediaPipe model complexity or frame resolution
                
            elif level == 2:
                # Aggressive optimization - significant quality reduction
                self.logger.info("Applying aggressive performance optimization")
                # Could skip frames, reduce resolution, or disable some features
                
        except Exception as e:
            self.logger.error(f"Failed to apply optimization level {level}: {e}")


class VideoProcessingService:
    """
    Enhanced video processing service for individual WebSocket client sessions
    Handles frame processing isolation per client connection with async processing loop,
    queue management, performance monitoring, and resource cleanup
    """
    
    def __init__(self, client_id: str, config: AppConfig):
        self.client_id = client_id
        self.config = config
        self.is_active = False
        self.frame_count = 0
        self.logger = logging.getLogger(f"{__name__}.VideoProcessingService.{client_id}")
        
        # Initialize frame processor with MediaPipe
        self.frame_processor = FrameProcessor(
            video_config=config.video,
            mediapipe_config=config.mediapipe
        )
        
        # Frame processing queue management
        self.frame_queue = asyncio.Queue(maxsize=10)  # Limit queue size to prevent memory issues
        self.processing_loop_task = None
        self.websocket = None
        
        # Performance monitoring
        self.processing_stats = {
            'frames_processed': 0,
            'frames_dropped': 0,
            'total_processing_time': 0.0,
            'average_processing_time': 0.0,
            'peak_processing_time': 0.0,
            'queue_overflows': 0,
            'last_frame_timestamp': None
        }
        
        # Resource monitoring
        self.resource_monitor = ResourceMonitor(client_id)
        self.performance_optimizer = PerformanceOptimizer(config)
        
        # Processing loop control
        self._shutdown_event = asyncio.Event()
        
    async def start_processing(self, websocket: WebSocket):
        """Start video processing for this client session with async processing loop"""
        self.is_active = True
        self.websocket = websocket
        self.logger.info(f"Starting enhanced video processing for client {self.client_id}")
        
        # Start the async processing loop
        self.processing_loop_task = asyncio.create_task(self._processing_loop())
        
        # Start resource monitoring
        await self.resource_monitor.start_monitoring()
        
        self.logger.info(f"Processing loop and resource monitoring started for client {self.client_id}")
        
    async def stop_processing(self):
        """Stop video processing for this client session with proper cleanup"""
        self.is_active = False
        
        # Signal shutdown to processing loop
        self._shutdown_event.set()
        
        # Cancel processing loop task
        if self.processing_loop_task and not self.processing_loop_task.done():
            self.processing_loop_task.cancel()
            try:
                await self.processing_loop_task
            except asyncio.CancelledError:
                self.logger.info(f"Processing loop cancelled for client {self.client_id}")
        
        # Stop resource monitoring
        await self.resource_monitor.stop_monitoring()
        
        # Clean up frame processor resources
        if hasattr(self, 'frame_processor'):
            self.frame_processor.close()
        
        # Clear remaining frames in queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        # Log final statistics
        self._log_final_stats()
        
        self.logger.info(f"Enhanced video processing stopped for client {self.client_id}")
    
    async def _processing_loop(self):
        """
        Async processing loop for handling incoming frames from queue
        Implements performance optimization and resource management
        """
        self.logger.info(f"Starting async processing loop for client {self.client_id}")
        
        try:
            while not self._shutdown_event.is_set():
                try:
                    # Wait for frame with timeout to allow periodic checks
                    frame_data = await asyncio.wait_for(
                        self.frame_queue.get(), 
                        timeout=1.0
                    )
                    
                    # Process frame with performance monitoring
                    await self._process_frame_with_monitoring(frame_data)
                    
                    # Mark task as done
                    self.frame_queue.task_done()
                    
                    # Check resource usage and optimize if needed
                    await self._check_and_optimize_performance()
                    
                except asyncio.TimeoutError:
                    # Periodic check - continue loop
                    continue
                except Exception as e:
                    self.logger.error(f"Error in processing loop for client {self.client_id}: {e}", exc_info=True)
                    # Continue processing other frames
                    continue
                    
        except asyncio.CancelledError:
            self.logger.info(f"Processing loop cancelled for client {self.client_id}")
        except Exception as e:
            self.logger.error(f"Critical error in processing loop for client {self.client_id}: {e}", exc_info=True)
        finally:
            self.logger.info(f"Processing loop ended for client {self.client_id}")
    
    async def _process_frame_with_monitoring(self, frame_data: dict):
        """
        Process frame with comprehensive performance monitoring
        
        Args:
            frame_data: Frame data dictionary from queue
        """
        start_time = time.time()
        
        try:
            # Process the frame
            response = await self._process_raw_frame(frame_data)
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Update performance statistics
            self._update_processing_stats(processing_time)
            
            # Send response to client if websocket is still active
            if self.websocket and response:
                try:
                    await self.websocket.send_text(json.dumps(response))
                except Exception as e:
                    self.logger.warning(f"Failed to send response to client {self.client_id}: {e}")
                    # Don't raise exception - continue processing
            
        except Exception as e:
            self.logger.error(f"Error processing frame for client {self.client_id}: {e}", exc_info=True)
    
    async def _check_and_optimize_performance(self):
        """
        Check system resources and optimize performance if needed
        """
        try:
            # Get current resource usage
            resource_stats = await self.resource_monitor.get_current_stats()
            
            # Apply performance optimizations if needed
            optimization_applied = await self.performance_optimizer.optimize_if_needed(
                resource_stats, 
                self.processing_stats
            )
            
            if optimization_applied:
                self.logger.info(f"Performance optimization applied for client {self.client_id}")
                
        except Exception as e:
            self.logger.warning(f"Performance optimization check failed for client {self.client_id}: {e}")
    
    def _update_processing_stats(self, processing_time_ms: float):
        """
        Update processing statistics for performance monitoring
        
        Args:
            processing_time_ms: Processing time in milliseconds
        """
        self.processing_stats['frames_processed'] += 1
        self.processing_stats['total_processing_time'] += processing_time_ms
        self.processing_stats['average_processing_time'] = (
            self.processing_stats['total_processing_time'] / 
            self.processing_stats['frames_processed']
        )
        
        if processing_time_ms > self.processing_stats['peak_processing_time']:
            self.processing_stats['peak_processing_time'] = processing_time_ms
            
        self.processing_stats['last_frame_timestamp'] = time.time()
    
    def _log_final_stats(self):
        """Log final processing statistics"""
        stats = self.processing_stats
        self.logger.info(f"Final stats for client {self.client_id}: "
                        f"Processed: {stats['frames_processed']}, "
                        f"Dropped: {stats['frames_dropped']}, "
                        f"Avg time: {stats['average_processing_time']:.2f}ms, "
                        f"Peak time: {stats['peak_processing_time']:.2f}ms, "
                        f"Queue overflows: {stats['queue_overflows']}")
    
    async def queue_frame_for_processing(self, message_data: dict) -> bool:
        """
        Queue frame for processing with overflow handling
        
        Args:
            message_data: Frame message data
            
        Returns:
            True if queued successfully, False if dropped due to overflow
        """
        try:
            # Try to put frame in queue without blocking
            self.frame_queue.put_nowait(message_data)
            return True
        except asyncio.QueueFull:
            # Queue is full - drop frame and update statistics
            self.processing_stats['frames_dropped'] += 1
            self.processing_stats['queue_overflows'] += 1
            
            self.logger.warning(f"Frame dropped for client {self.client_id} - queue full "
                              f"(dropped: {self.processing_stats['frames_dropped']})")
            return False
    
    def get_processing_stats(self) -> dict:
        """
        Get current processing statistics for monitoring
        
        Returns:
            Dictionary with current processing statistics
        """
        stats = self.processing_stats.copy()
        stats['client_id'] = self.client_id
        stats['is_active'] = self.is_active
        stats['queue_size'] = self.frame_queue.qsize()
        stats['queue_maxsize'] = self.frame_queue.maxsize
        
        # Add resource stats if available
        if hasattr(self, 'resource_monitor'):
            try:
                # Get the most recent stats from history
                if self.resource_monitor.stats_history:
                    stats['resource_stats'] = self.resource_monitor.stats_history[-1]
                else:
                    stats['resource_stats'] = {'status': 'no_data'}
            except Exception:
                stats['resource_stats'] = {'status': 'unavailable'}
        
        return stats
        
    async def process_message(self, message_data: dict) -> Optional[dict]:
        """
        Process incoming WebSocket message from client using queue-based system
        
        Args:
            message_data: Parsed JSON message from client
            
        Returns:
            Response message dict or None if queued for async processing
        """
        try:
            message_type = message_data.get("type")
            
            if message_type == "raw_frame":
                # Queue frame for async processing instead of processing immediately
                queued = await self.queue_frame_for_processing(message_data)
                
                if not queued:
                    # Frame was dropped due to queue overflow
                    return {
                        "type": "error",
                        "message": "Frame dropped - processing queue full",
                        "timestamp": datetime.utcnow().isoformat(),
                        "metadata": {
                            "client_id": self.client_id,
                            "frames_dropped": self.processing_stats['frames_dropped'],
                            "queue_overflows": self.processing_stats['queue_overflows']
                        }
                    }
                
                # Frame queued successfully - no immediate response needed
                # Response will be sent by processing loop
                return None
                
            else:
                self.logger.warning(f"Unknown message type: {message_type}")
                return {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}", exc_info=True)
            return {
                "type": "error", 
                "message": "Failed to process message",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _process_raw_frame(self, message_data: dict) -> dict:
        """
        Process raw frame data through MediaPipe with enhanced streaming response
        
        Args:
            message_data: Message containing raw frame data
            
        Returns:
            Processed frame response message with comprehensive metadata
        """
        self.frame_count += 1
        
        try:
            # Get base64 frame data from message
            frame_data = message_data.get("frame_data", "")
            if not frame_data:
                self.logger.warning(f"No frame data received from client {self.client_id}")
                return self._create_streaming_error_response("No frame data provided")
            
            # Extract client metadata if available
            client_metadata = message_data.get("metadata", {})
            client_frame_number = client_metadata.get("frame_number", self.frame_count)
            
            # Process frame through enhanced MediaPipe pipeline
            processing_result = self.frame_processor.process_base64_frame(frame_data, self.frame_count)
            
            # Create streaming response based on processing result
            if processing_result["success"]:
                response = self._create_successful_streaming_response(processing_result, client_metadata)
            else:
                # Graceful degradation - return error but continue operation
                response = self._create_degraded_streaming_response(processing_result, client_metadata)
            
            # Log processing status
            if processing_result["success"]:
                landmarks = processing_result["landmarks_detected"]
                processing_time = processing_result["processing_metadata"]["total_pipeline_time_ms"]
                self.logger.debug(f"Frame {self.frame_count} processed successfully for client {self.client_id} - "
                                f"Landmarks: {landmarks}, Time: {processing_time:.2f}ms")
            else:
                self.logger.warning(f"Frame {self.frame_count} processing degraded for client {self.client_id}: "
                                  f"{processing_result.get('error', 'Unknown error')}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Critical error processing raw frame for client {self.client_id}: {e}", exc_info=True)
            # Return error response but continue operation (graceful degradation)
            return self._create_streaming_error_response(f"Critical processing error: {str(e)}")
    
    def _create_successful_streaming_response(self, processing_result: dict, client_metadata: dict) -> dict:
        """
        Create successful streaming response with comprehensive metadata
        
        Args:
            processing_result: Result from frame processing pipeline
            client_metadata: Metadata from client message
            
        Returns:
            Formatted streaming response message
        """
        return {
            "type": "processed_frame",
            "timestamp": datetime.utcnow().isoformat(),
            "frame_data": processing_result["frame_data"],
            "metadata": {
                "client_id": self.client_id,
                "server_frame_number": self.frame_count,
                "client_frame_number": client_metadata.get("frame_number", self.frame_count),
                "processing_time_ms": processing_result["processing_metadata"]["mediapipe_processing_time_ms"],
                "total_pipeline_time_ms": processing_result["processing_metadata"]["total_pipeline_time_ms"],
                "landmarks_detected": processing_result["landmarks_detected"],
                "quality_metrics": processing_result["quality_metrics"],
                "encoding_info": processing_result["processing_metadata"].get("encoding_metadata", {}),
                "success": True
            }
        }
    
    def _create_degraded_streaming_response(self, processing_result: dict, client_metadata: dict) -> dict:
        """
        Create degraded streaming response for graceful error handling
        
        Args:
            processing_result: Failed processing result
            client_metadata: Metadata from client message
            
        Returns:
            Formatted degraded response message
        """
        return {
            "type": "processed_frame",
            "timestamp": datetime.utcnow().isoformat(),
            "frame_data": None,  # No frame data due to processing failure
            "metadata": {
                "client_id": self.client_id,
                "server_frame_number": self.frame_count,
                "client_frame_number": client_metadata.get("frame_number", self.frame_count),
                "processing_time_ms": 0.0,
                "total_pipeline_time_ms": 0.0,
                "landmarks_detected": {"hands": False, "face": False, "pose": False},
                "quality_metrics": {"landmarks_confidence": 0.0, "processing_efficiency": 0.0},
                "success": False,
                "error": processing_result.get("error", "Processing failed"),
                "degraded_mode": True
            }
        }
    
    def _create_streaming_error_response(self, error_message: str) -> dict:
        """
        Create standardized streaming error response
        
        Args:
            error_message: Error description
            
        Returns:
            Formatted error response message
        """
        return {
            "type": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "message": error_message,
            "metadata": {
                "client_id": self.client_id,
                "server_frame_number": self.frame_count,
                "error_type": "streaming_error"
            }
        }

# Global connection manager
class ConnectionManager:
    """Manages WebSocket connections and their associated processing services"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.processing_services: Dict[str, VideoProcessingService] = {}
        self.connection_counter = 0
        
    def generate_client_id(self) -> str:
        """Generate unique client ID"""
        self.connection_counter += 1
        return f"client_{self.connection_counter}"
        
    async def connect(self, websocket: WebSocket) -> str:
        """Accept WebSocket connection and create processing service"""
        await websocket.accept()
        client_id = self.generate_client_id()
        
        self.active_connections[client_id] = websocket
        self.processing_services[client_id] = VideoProcessingService(client_id, app_config)
        
        await self.processing_services[client_id].start_processing(websocket)
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
        return client_id
        
    async def disconnect(self, client_id: str):
        """Disconnect client and cleanup resources"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            
        if client_id in self.processing_services:
            await self.processing_services[client_id].stop_processing()
            del self.processing_services[client_id]
            
        logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
        
    async def send_message(self, client_id: str, message: dict):
        """Send message to specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_text(json.dumps(message))
            
    def get_connection_count(self) -> int:
        """Get current number of active connections"""
        return len(self.active_connections)
    
    def get_all_processing_stats(self) -> Dict[str, dict]:
        """Get processing statistics for all active connections"""
        stats = {}
        for client_id, service in self.processing_services.items():
            try:
                stats[client_id] = service.get_processing_stats()
            except Exception as e:
                logger.warning(f"Failed to get stats for client {client_id}: {e}")
                stats[client_id] = {'error': str(e)}
        return stats
    
    def get_system_summary(self) -> dict:
        """Get system-wide processing summary"""
        all_stats = self.get_all_processing_stats()
        
        total_frames_processed = sum(
            stats.get('frames_processed', 0) 
            for stats in all_stats.values() 
            if isinstance(stats, dict) and 'frames_processed' in stats
        )
        
        total_frames_dropped = sum(
            stats.get('frames_dropped', 0) 
            for stats in all_stats.values() 
            if isinstance(stats, dict) and 'frames_dropped' in stats
        )
        
        active_queues = sum(
            1 for stats in all_stats.values() 
            if isinstance(stats, dict) and stats.get('queue_size', 0) > 0
        )
        
        return {
            'active_connections': len(self.active_connections),
            'total_frames_processed': total_frames_processed,
            'total_frames_dropped': total_frames_dropped,
            'active_processing_queues': active_queues,
            'client_stats': all_stats
        }

# Initialize connection manager
connection_manager = ConnectionManager()

# Create FastAPI application instance
app = FastAPI(
    title="StorySign ASL Platform Backend",
    description="Real-time ASL recognition and learning system backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Global exception handler for unhandled errors
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for logging and graceful error responses"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please check the server logs.",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint returning system status and information
    
    Returns:
        Dict containing welcome message, status, and system information
    """
    try:
        logger.info("Health check endpoint accessed")
        
        response_data = {
            "message": "Hello from the StorySign Backend!",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "services": {
                "mediapipe": "ready",
                "websocket": "active", 
                "active_connections": connection_manager.get_connection_count()
            },
            "configuration": {
                "video": {
                    "resolution": f"{app_config.video.width}x{app_config.video.height}",
                    "fps": app_config.video.fps,
                    "format": app_config.video.format
                },
                "mediapipe": {
                    "model_complexity": app_config.mediapipe.model_complexity,
                    "detection_confidence": app_config.mediapipe.min_detection_confidence,
                    "tracking_confidence": app_config.mediapipe.min_tracking_confidence
                },
                "server": {
                    "max_connections": app_config.server.max_connections,
                    "log_level": app_config.server.log_level
                }
            }
        }
        
        logger.info("Health check completed successfully")
        return response_data
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Health check failed"
        )

@app.get("/config")
async def get_configuration() -> Dict[str, Any]:
    """
    Get current application configuration
    
    Returns:
        Dict containing current configuration settings
    """
    try:
        logger.info("Configuration endpoint accessed")
        
        config_data = {
            "video": app_config.video.model_dump(),
            "mediapipe": app_config.mediapipe.model_dump(),
            "server": {
                "host": app_config.server.host,
                "port": app_config.server.port,
                "log_level": app_config.server.log_level,
                "max_connections": app_config.server.max_connections
                # Exclude reload setting for security
            }
        }
        
        logger.info("Configuration retrieved successfully")
        return config_data
        
    except Exception as e:
        logger.error(f"Configuration retrieval failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Configuration retrieval failed"
        )

@app.get("/stats")
async def get_processing_statistics() -> Dict[str, Any]:
    """
    Get current processing statistics for all connections
    
    Returns:
        Dict containing system-wide processing statistics
    """
    try:
        logger.info("Processing statistics endpoint accessed")
        
        # Get system summary with all client statistics
        system_summary = connection_manager.get_system_summary()
        
        # Add timestamp and system info
        stats_response = {
            "timestamp": datetime.utcnow().isoformat(),
            "system_summary": system_summary,
            "server_info": {
                "uptime_seconds": time.time() - startup_time if 'startup_time' in globals() else 0,
                "configuration": {
                    "max_connections": app_config.server.max_connections,
                    "video_resolution": f"{app_config.video.width}x{app_config.video.height}",
                    "mediapipe_complexity": app_config.mediapipe.model_complexity
                }
            }
        }
        
        logger.info("Processing statistics retrieved successfully")
        return stats_response
        
    except Exception as e:
        logger.error(f"Processing statistics retrieval failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Processing statistics retrieval failed"
        )

@app.websocket("/ws/video")
async def websocket_video_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time video streaming and processing
    
    Handles client connections and processes video frame messages
    """
    client_id = None
    try:
        # Accept connection and create processing service
        client_id = await connection_manager.connect(websocket)
        logger.info(f"WebSocket connection established for client {client_id}")
        
        # Main message processing loop
        while True:
            try:
                # Receive message from client with timeout
                raw_message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Check message size (limit to 10MB)
                if len(raw_message) > 10 * 1024 * 1024:
                    logger.warning(f"Message too large from client {client_id}: {len(raw_message)} bytes")
                    error_response = {
                        "type": "error",
                        "message": "Message too large",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await connection_manager.send_message(client_id, error_response)
                    continue
                
                # Parse JSON message
                try:
                    message_data = json.loads(raw_message)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received from client {client_id}: {e}")
                    error_response = {
                        "type": "error",
                        "message": "Invalid JSON format",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await connection_manager.send_message(client_id, error_response)
                    continue
                
                # Validate message structure
                if not isinstance(message_data, dict) or "type" not in message_data:
                    logger.error(f"Invalid message structure from client {client_id}")
                    error_response = {
                        "type": "error", 
                        "message": "Message must be JSON object with 'type' field",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await connection_manager.send_message(client_id, error_response)
                    continue
                
                # Process message through enhanced video processing service
                processing_service = connection_manager.processing_services[client_id]
                response = await processing_service.process_message(message_data)
                
                # Send immediate response if available (errors, non-frame messages)
                # Frame processing responses are handled by the async processing loop
                if response:
                    await connection_manager.send_message(client_id, response)
                    
            except asyncio.TimeoutError:
                logger.warning(f"Timeout waiting for message from client {client_id}")
                # Send ping to check if connection is still alive
                try:
                    await websocket.ping()
                except:
                    logger.info(f"Client {client_id} connection lost (ping failed)")
                    break
            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected normally")
                break
            except Exception as e:
                logger.error(f"Error in WebSocket message loop for client {client_id}: {e}", exc_info=True)
                # Try to send error message to client
                try:
                    error_response = {
                        "type": "error",
                        "message": "Server processing error", 
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await connection_manager.send_message(client_id, error_response)
                except:
                    # If we can't send error message, connection is likely broken
                    logger.warning(f"Failed to send error message to client {client_id}, closing connection")
                    break
                    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}", exc_info=True)
    finally:
        # Cleanup connection
        if client_id:
            await connection_manager.disconnect(client_id)

# Global startup time for uptime calculation
startup_time = time.time()

# Application startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event handler"""
    global startup_time
    startup_time = time.time()
    
    logger.info("StorySign Backend starting up...")
    logger.info(f"Server configuration: {app_config.server.host}:{app_config.server.port}")
    logger.info(f"Video configuration: {app_config.video.width}x{app_config.video.height} @ {app_config.video.fps}fps")
    logger.info(f"MediaPipe configuration: complexity={app_config.mediapipe.model_complexity}, detection={app_config.mediapipe.min_detection_confidence}")
    logger.info("Enhanced video processing with async loops and resource monitoring initialized")
    logger.info("FastAPI application initialized successfully")

# Application shutdown event  
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler"""
    logger.info("StorySign Backend shutting down...")

if __name__ == "__main__":
    # This allows running the app directly with python main.py
    # Use configuration values for server settings
    uvicorn.run(
        "main:app",
        host=app_config.server.host, 
        port=app_config.server.port,
        reload=app_config.server.reload,
        log_level=app_config.server.log_level
    )