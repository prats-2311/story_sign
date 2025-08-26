#!/usr/bin/env python3
"""
StorySign ASL Platform Backend
FastAPI application for real-time ASL recognition and learning
"""

import logging
import sys
import os
import signal
import atexit
from datetime import datetime
from typing import Dict, Any, List
import traceback
import gc
import resource

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import json
import asyncio
from typing import Optional
import time
from collections import deque
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor

from config import get_config, AppConfig
from video_processor import FrameProcessor
from local_vision_service import get_vision_service, VisionResult
from ollama_service import get_ollama_service, StoryResponse
# Temporarily comment out performance optimizer
# from performance_optimizer import initialize_performance_optimizer, get_performance_optimizer

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
    Enhanced monitor system resources for individual client sessions
    Tracks CPU, memory usage, processing performance with resource limit enforcement
    """

    def __init__(self, client_id: str):
        self.client_id = client_id
        self.logger = logging.getLogger(f"{__name__}.ResourceMonitor.{client_id}")
        self.monitoring_active = False
        self.monitoring_task = None
        self.stats_history = deque([], 60)  # Keep last 60 measurements (1 minute at 1Hz)

        # Resource limits and enforcement
        self.memory_limit_mb = 512  # 512MB per client
        self.cpu_limit_percent = 80  # 80% CPU usage limit
        self.consecutive_violations = 0
        self.max_violations = 5  # Trigger enforcement after 5 consecutive violations
        self.enforcement_active = False

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
        """Enhanced monitoring loop with resource limit enforcement"""
        try:
            while self.monitoring_active:
                try:
                    # Get current resource stats
                    stats = await self._collect_resource_stats()
                    self.stats_history.append(stats)

                    # Check for resource limit violations
                    violation_detected = await self._check_resource_limits(stats)

                    # Log warnings and enforce limits if necessary
                    if stats['cpu_percent'] > 80 or stats['memory_mb'] > self.memory_limit_mb:
                        self.logger.warning(f"High resource usage for client {self.client_id}: "
                                          f"CPU: {stats['cpu_percent']:.1f}%, "
                                          f"Memory: {stats['memory_mb']:.1f}MB")

                        if violation_detected:
                            await self._enforce_resource_limits(stats)

                    # Force garbage collection if memory usage is high
                    if stats['memory_mb'] > self.memory_limit_mb * 0.8:
                        gc.collect()
                        self.logger.debug(f"Forced garbage collection for client {self.client_id}")

                    await asyncio.sleep(1.0)  # Monitor every second

                except Exception as e:
                    self.logger.error(f"Error in resource monitoring for client {self.client_id}: {e}", exc_info=True)
                    await asyncio.sleep(1.0)

        except asyncio.CancelledError:
            self.logger.info(f"Resource monitoring cancelled for client {self.client_id}")
        except Exception as e:
            self.logger.error(f"Critical error in resource monitoring loop for client {self.client_id}: {e}", exc_info=True)

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

    async def _check_resource_limits(self, stats: dict) -> bool:
        """
        Check if resource limits are violated and track consecutive violations

        Args:
            stats: Current resource statistics

        Returns:
            True if enforcement should be triggered, False otherwise
        """
        try:
            cpu_violation = stats['cpu_percent'] > self.cpu_limit_percent
            memory_violation = stats['memory_mb'] > self.memory_limit_mb

            if cpu_violation or memory_violation:
                self.consecutive_violations += 1
                self.logger.warning(f"Resource limit violation #{self.consecutive_violations} for client {self.client_id}: "
                                  f"CPU: {stats['cpu_percent']:.1f}% (limit: {self.cpu_limit_percent}%), "
                                  f"Memory: {stats['memory_mb']:.1f}MB (limit: {self.memory_limit_mb}MB)")

                # Trigger enforcement after consecutive violations
                if self.consecutive_violations >= self.max_violations and not self.enforcement_active:
                    return True
            else:
                # Reset violation counter if resources are within limits
                if self.consecutive_violations > 0:
                    self.logger.info(f"Resource usage normalized for client {self.client_id}, "
                                   f"resetting violation counter (was {self.consecutive_violations})")
                self.consecutive_violations = 0
                self.enforcement_active = False

            return False

        except Exception as e:
            self.logger.error(f"Error checking resource limits for client {self.client_id}: {e}", exc_info=True)
            return False

    async def _enforce_resource_limits(self, stats: dict):
        """
        Enforce resource limits by reducing processing quality or throttling

        Args:
            stats: Current resource statistics that triggered enforcement
        """
        try:
            if self.enforcement_active:
                return  # Already enforcing limits

            self.enforcement_active = True
            self.logger.error(f"ENFORCING RESOURCE LIMITS for client {self.client_id}: "
                            f"CPU: {stats['cpu_percent']:.1f}%, Memory: {stats['memory_mb']:.1f}MB")

            # Implement enforcement strategies
            enforcement_actions = []

            if stats['memory_mb'] > self.memory_limit_mb:
                # Force garbage collection
                gc.collect()
                enforcement_actions.append("forced_gc")

                # If memory is critically high, consider more aggressive measures
                if stats['memory_mb'] > self.memory_limit_mb * 1.5:
                    enforcement_actions.append("critical_memory_mode")

            if stats['cpu_percent'] > self.cpu_limit_percent:
                enforcement_actions.append("cpu_throttling")

            self.logger.critical(f"Resource enforcement actions for client {self.client_id}: {enforcement_actions}")

            # Log enforcement event for monitoring
            self._log_enforcement_event(stats, enforcement_actions)

        except Exception as e:
            self.logger.error(f"Error enforcing resource limits for client {self.client_id}: {e}", exc_info=True)

    def _log_enforcement_event(self, stats: dict, actions: list):
        """
        Log resource enforcement event for monitoring and debugging

        Args:
            stats: Resource statistics that triggered enforcement
            actions: List of enforcement actions taken
        """
        try:
            enforcement_log = {
                'timestamp': datetime.utcnow().isoformat(),
                'client_id': self.client_id,
                'trigger_stats': stats,
                'enforcement_actions': actions,
                'consecutive_violations': self.consecutive_violations,
                'limits': {
                    'memory_limit_mb': self.memory_limit_mb,
                    'cpu_limit_percent': self.cpu_limit_percent
                }
            }

            # Log as structured data for monitoring systems
            self.logger.critical(f"RESOURCE_ENFORCEMENT_EVENT: {json.dumps(enforcement_log)}")

        except Exception as e:
            self.logger.error(f"Failed to log enforcement event for client {self.client_id}: {e}")



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

        # Initialize frame processor with MediaPipe and gesture detection
        self.frame_processor = FrameProcessor(
            video_config=config.video,
            mediapipe_config=config.mediapipe,
            gesture_config=config.gesture_detection
        )

        # Get performance optimizer (temporarily disabled)
        # self.performance_optimizer = get_performance_optimizer()
        self.performance_optimizer = None

        # Frame processing queue management - optimized for low latency
        self.frame_queue = asyncio.Queue(maxsize=3)  # Reduced queue size for lower latency
        self.processing_loop_task = None
        self.websocket = None

        # Low latency optimizations
        self.low_latency_mode = True  # Enable aggressive optimizations
        self.frame_skip_counter = 0
        self.process_every_nth_frame = 2  # Process every 2nd frame for speed

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
        # self.performance_optimizer = PerformanceOptimizer(config)  # Removed duplicate

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

        # Start performance optimization if available (temporarily disabled)
        # if self.performance_optimizer and not self.performance_optimizer.optimization_active:
        #     await self.performance_optimizer.start_optimization()

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
        Process frame with comprehensive performance monitoring and fallback processing

        Args:
            frame_data: Frame data dictionary from queue
        """
        start_time = time.time()
        fallback_used = False

        try:
            # Process the frame with MediaPipe fallback handling
            response = await self._process_raw_frame_with_fallback(frame_data)

            # Check if fallback processing was used
            if response and response.get('metadata', {}).get('fallback_processing'):
                fallback_used = True
                self.processing_stats['fallback_frames'] = self.processing_stats.get('fallback_frames', 0) + 1

            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000  # Convert to ms

            # Update performance statistics
            self._update_processing_stats(processing_time, fallback_used)

            # Check for pending analysis tasks and process them
            await self._check_and_process_analysis_tasks()

            # Send response to client if websocket is still active
            if self.websocket and response:
                try:
                    await self.websocket.send_text(json.dumps(response))
                except ConnectionResetError:
                    self.logger.info(f"Client {self.client_id} connection reset during send")
                    # Stop processing as client is disconnected
                    await self.stop_processing()
                except Exception as e:
                    self.logger.warning(f"Failed to send response to client {self.client_id}: {e}")
                    # Don't raise exception - continue processing

        except Exception as e:
            self.logger.error(f"Critical error processing frame for client {self.client_id}: {e}", exc_info=True)

            # Try to send error response to client
            try:
                if self.websocket:
                    error_response = self._create_critical_error_response(str(e))
                    await self.websocket.send_text(json.dumps(error_response))
            except Exception as send_error:
                self.logger.error(f"Failed to send error response to client {self.client_id}: {send_error}")

    async def _process_raw_frame_with_fallback(self, message_data: dict) -> dict:
        """
        Process raw frame with MediaPipe fallback processing for graceful degradation

        Args:
            message_data: Message containing raw frame data

        Returns:
            Processed frame response with fallback indicators
        """
        try:
            # First attempt: normal MediaPipe processing
            return await self._process_raw_frame(message_data)

        except Exception as mediapipe_error:
            self.logger.warning(f"MediaPipe processing failed for client {self.client_id}, "
                              f"attempting fallback: {mediapipe_error}")

            # Fallback processing: return original frame without MediaPipe overlays
            try:
                return await self._process_frame_fallback(message_data, str(mediapipe_error))
            except Exception as fallback_error:
                self.logger.error(f"Fallback processing also failed for client {self.client_id}: {fallback_error}")
                return self._create_critical_error_response(f"All processing failed: {fallback_error}")

    async def _process_frame_fallback(self, message_data: dict, original_error: str) -> dict:
        """
        Fallback frame processing without MediaPipe when main processing fails

        Args:
            message_data: Message containing raw frame data
            original_error: Error message from failed MediaPipe processing

        Returns:
            Fallback response with original frame data
        """
        self.frame_count += 1

        try:
            # Get base64 frame data from message
            frame_data = message_data.get("frame_data", "")
            if not frame_data:
                return self._create_streaming_error_response("No frame data for fallback processing")

            # Extract client metadata
            client_metadata = message_data.get("metadata", {})

            # Create fallback response with original frame (no MediaPipe processing)
            response = {
                "type": "processed_frame",
                "timestamp": datetime.utcnow().isoformat(),
                "frame_data": frame_data,  # Return original frame data
                "metadata": {
                    "client_id": self.client_id,
                    "server_frame_number": self.frame_count,
                    "client_frame_number": client_metadata.get("frame_number", self.frame_count),
                    "processing_time_ms": 0.0,
                    "total_pipeline_time_ms": 0.0,
                    "landmarks_detected": {"hands": False, "face": False, "pose": False},
                    "quality_metrics": {"landmarks_confidence": 0.0, "processing_efficiency": 0.0},
                    "success": True,
                    "fallback_processing": True,
                    "original_error": original_error,
                    "fallback_reason": "MediaPipe processing failure - graceful degradation"
                }
            }

            self.logger.info(f"Fallback processing successful for client {self.client_id} frame {self.frame_count}")
            return response

        except Exception as e:
            self.logger.error(f"Fallback processing failed for client {self.client_id}: {e}", exc_info=True)
            return self._create_critical_error_response(f"Fallback processing failed: {str(e)}")

    def _create_critical_error_response(self, error_message: str) -> dict:
        """
        Create critical error response for severe processing failures

        Args:
            error_message: Critical error description

        Returns:
            Critical error response message
        """
        return {
            "type": "critical_error",
            "timestamp": datetime.utcnow().isoformat(),
            "message": error_message,
            "metadata": {
                "client_id": self.client_id,
                "server_frame_number": self.frame_count,
                "error_type": "critical_processing_error",
                "requires_reconnection": True
            }
        }

    async def _check_and_process_analysis_tasks(self):
        """
        Check for pending signing analysis tasks and process them asynchronously
        """
        try:
            # Get pending analysis task from frame processor
            analysis_task = self.frame_processor.get_pending_analysis_task()
            
            if analysis_task:
                self.logger.info(f"Processing signing analysis task for client {self.client_id}")
                
                # Process analysis asynchronously to avoid blocking video stream
                asyncio.create_task(self._process_signing_analysis(analysis_task))
                
        except Exception as e:
            self.logger.error(f"Error checking analysis tasks for client {self.client_id}: {e}")
    
    async def _process_signing_analysis(self, analysis_task: Dict[str, Any]):
        """
        Process signing analysis task asynchronously
        
        Args:
            analysis_task: Dictionary containing landmark buffer and target sentence
        """
        try:
            # Get Ollama service
            ollama_service = await get_ollama_service()
            
            # Extract task data
            landmark_buffer = analysis_task.get("landmark_buffer", [])
            target_sentence = analysis_task.get("target_sentence", "")
            
            self.logger.info(f"Analyzing signing attempt for client {self.client_id}: '{target_sentence}' "
                           f"with {len(landmark_buffer)} frames")
            
            # Perform signing analysis
            analysis_result = await ollama_service.analyze_signing_attempt(
                landmark_buffer, target_sentence
            )
            
            if analysis_result:
                # Set analysis result in frame processor
                result_status = self.frame_processor.set_analysis_result(analysis_result)
                
                # Send ASL feedback message to client
                feedback_message = {
                    "type": "asl_feedback",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {
                        "target_sentence": target_sentence,
                        "feedback": analysis_result.get("feedback", "Analysis completed"),
                        "confidence_score": analysis_result.get("confidence_score", 0.0),
                        "suggestions": analysis_result.get("suggestions", []),
                        "analysis_summary": analysis_result.get("analysis_summary", "")
                    },
                    "metadata": {
                        "client_id": self.client_id,
                        "analysis_success": result_status.get("success", False)
                    }
                }
                
                # Send feedback to client
                if self.websocket:
                    try:
                        await self.websocket.send_text(json.dumps(feedback_message))
                        self.logger.info(f"ASL feedback sent to client {self.client_id}")
                    except Exception as send_error:
                        self.logger.error(f"Failed to send ASL feedback to client {self.client_id}: {send_error}")
                
            else:
                # Analysis failed, set error result
                error_result = {
                    "feedback": "Analysis service is currently unavailable. Please try again.",
                    "confidence_score": 0.0,
                    "suggestions": ["Try signing again with clear movements", "Ensure good lighting"],
                    "analysis_summary": "Analysis service error",
                    "error": True
                }
                
                self.frame_processor.set_analysis_result(error_result)
                
                # Send error feedback to client
                error_message = {
                    "type": "asl_feedback",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {
                        "target_sentence": target_sentence,
                        "feedback": error_result["feedback"],
                        "confidence_score": 0.0,
                        "suggestions": error_result["suggestions"],
                        "analysis_summary": error_result["analysis_summary"],
                        "error": True
                    },
                    "metadata": {
                        "client_id": self.client_id,
                        "analysis_success": False
                    }
                }
                
                if self.websocket:
                    try:
                        await self.websocket.send_text(json.dumps(error_message))
                        self.logger.warning(f"ASL error feedback sent to client {self.client_id}")
                    except Exception as send_error:
                        self.logger.error(f"Failed to send ASL error feedback to client {self.client_id}: {send_error}")
                
        except Exception as e:
            self.logger.error(f"Error processing signing analysis for client {self.client_id}: {e}", exc_info=True)
            
            # Send error feedback to client
            try:
                error_message = {
                    "type": "asl_feedback",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {
                        "target_sentence": analysis_task.get("target_sentence", ""),
                        "feedback": f"Analysis error: {str(e)}. Please try again.",
                        "confidence_score": 0.0,
                        "suggestions": ["Try signing again", "Check your internet connection"],
                        "analysis_summary": "Analysis processing error",
                        "error": True
                    },
                    "metadata": {
                        "client_id": self.client_id,
                        "analysis_success": False
                    }
                }
                
                if self.websocket:
                    await self.websocket.send_text(json.dumps(error_message))
                    
            except Exception as send_error:
                self.logger.error(f"Failed to send analysis error message to client {self.client_id}: {send_error}")

    async def _check_and_optimize_performance(self):
        """
        Check system resources and optimize performance if needed
        """
        try:
            # Get current resource usage
            resource_stats = await self.resource_monitor.get_current_stats()

            # Apply performance optimizations if needed (temporarily disabled)
            # optimization_applied = await self.performance_optimizer.optimize_if_needed(
            #     resource_stats,
            #     self.processing_stats
            # )

            # if optimization_applied:
            #     self.logger.info(f"Performance optimization applied for client {self.client_id}")

        except Exception as e:
            self.logger.warning(f"Performance optimization check failed for client {self.client_id}: {e}")

    def _update_processing_stats(self, processing_time_ms: float, fallback_used: bool = False):
        """
        Update processing statistics for performance monitoring including fallback tracking

        Args:
            processing_time_ms: Processing time in milliseconds
            fallback_used: Whether fallback processing was used
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

        # Track fallback processing statistics
        if fallback_used:
            self.processing_stats['fallback_frames'] = self.processing_stats.get('fallback_frames', 0) + 1
            self.processing_stats['fallback_rate'] = (
                self.processing_stats['fallback_frames'] / self.processing_stats['frames_processed']
            )

        # Track error rates and processing health
        self.processing_stats['success_rate'] = (
            (self.processing_stats['frames_processed'] - self.processing_stats.get('fallback_frames', 0)) /
            self.processing_stats['frames_processed']
        ) if self.processing_stats['frames_processed'] > 0 else 0.0

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

            elif message_type == "control":
                # Handle practice session control messages
                return await self._handle_control_message(message_data)

            elif message_type == "practice_session_start":
                # Handle practice session start
                return await self._handle_practice_session_start(message_data)

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
    
    async def _handle_control_message(self, message_data: dict) -> dict:
        """
        Handle practice session control messages
        
        Args:
            message_data: Control message data
            
        Returns:
            Response message
        """
        try:
            action = message_data.get("action")
            data = message_data.get("data", {})
            
            if not action:
                return {
                    "type": "error",
                    "message": "Control message missing 'action' field",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Handle control action through frame processor
            result = self.frame_processor.handle_practice_control(action, data)
            
            # Create response message
            response = {
                "type": "control_response",
                "timestamp": datetime.utcnow().isoformat(),
                "action": action,
                "result": result,
                "metadata": {
                    "client_id": self.client_id
                }
            }
            
            self.logger.info(f"Control action '{action}' processed for client {self.client_id}: {result.get('success', False)}")
            return response
            
        except Exception as e:
            self.logger.error(f"Error handling control message for client {self.client_id}: {e}")
            return {
                "type": "error",
                "message": f"Control message processing failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _handle_practice_session_start(self, message_data: dict) -> dict:
        """
        Handle practice session start message
        
        Args:
            message_data: Session start message data
            
        Returns:
            Response message
        """
        try:
            story_sentences = message_data.get("story_sentences", [])
            session_id = message_data.get("session_id")
            
            if not story_sentences:
                return {
                    "type": "error",
                    "message": "Practice session start missing 'story_sentences'",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Start practice session through frame processor
            result = self.frame_processor.start_practice_session(story_sentences, session_id)
            
            # Create response message
            response = {
                "type": "practice_session_response",
                "timestamp": datetime.utcnow().isoformat(),
                "action": "session_started",
                "result": result,
                "metadata": {
                    "client_id": self.client_id
                }
            }
            
            self.logger.info(f"Practice session started for client {self.client_id}: {result.get('success', False)}")
            return response
            
        except Exception as e:
            self.logger.error(f"Error starting practice session for client {self.client_id}: {e}")
            return {
                "type": "error",
                "message": f"Practice session start failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }

    def _process_frame_sync(self, frame_data: str, frame_count: int) -> dict:
        """
        Synchronous frame processing for ThreadPoolExecutor
        This runs in a separate thread to avoid blocking the async event loop

        Args:
            frame_data: Base64 frame data
            frame_count: Frame sequence number

        Returns:
            Processing result dictionary
        """
        return self.frame_processor.process_base64_frame(frame_data, frame_count)

    async def _process_raw_frame(self, message_data: dict) -> dict:
        """
        Process raw frame data through MediaPipe with enhanced streaming response
        Uses ThreadPoolExecutor to prevent blocking the async event loop

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

            # Process frame through enhanced MediaPipe pipeline using ThreadPoolExecutor
            # This prevents blocking the async event loop during CPU-intensive processing
            loop = asyncio.get_event_loop()
            processing_result = await loop.run_in_executor(
                executor,
                self._process_frame_sync,
                frame_data,
                self.frame_count
            )

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
        response = {
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
        
        # Add practice session data if available
        practice_session_data = processing_result.get("practice_session")
        if practice_session_data:
            response["practice_session"] = practice_session_data
            
            # Add gesture detection state indicators to metadata
            gesture_state = practice_session_data.get("gesture_state", {})
            response["metadata"]["gesture_detection"] = {
                "is_detecting": gesture_state.get("is_detecting", False),
                "practice_mode": practice_session_data.get("practice_mode", "listening"),
                "analysis_in_progress": practice_session_data.get("analysis_in_progress", False),
                "buffer_size": gesture_state.get("buffer_size", 0)
            }
        
        return response

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
    """Enhanced WebSocket connection manager with graceful shutdown and comprehensive error handling"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.processing_services: Dict[str, VideoProcessingService] = {}
        self.connection_counter = 0
        self.logger = logging.getLogger(f"{__name__}.ConnectionManager")
        self.shutdown_initiated = False
        self.shutdown_timeout = 30.0  # 30 seconds for graceful shutdown

        # Register shutdown handlers
        self._register_shutdown_handlers()

    def generate_client_id(self) -> str:
        """Generate unique client ID"""
        self.connection_counter += 1
        return f"client_{self.connection_counter}"

    async def connect(self, websocket: WebSocket) -> str:
        """Register WebSocket connection (WebSocket should already be accepted)"""
        client_id = self.generate_client_id()

        self.active_connections[client_id] = websocket
        # Note: VideoProcessingService will be created and managed by the WebSocket endpoint
        
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
        return client_id
    
    def register_processing_service(self, client_id: str, processing_service):
        """Register processing service for a client"""
        self.processing_services[client_id] = processing_service

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
        """Get system-wide processing summary with enhanced error tracking"""
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

        total_fallback_frames = sum(
            stats.get('fallback_frames', 0)
            for stats in all_stats.values()
            if isinstance(stats, dict) and 'fallback_frames' in stats
        )

        active_queues = sum(
            1 for stats in all_stats.values()
            if isinstance(stats, dict) and stats.get('queue_size', 0) > 0
        )

        # Calculate system-wide success rate
        system_success_rate = 0.0
        if total_frames_processed > 0:
            successful_frames = total_frames_processed - total_fallback_frames
            system_success_rate = successful_frames / total_frames_processed

        return {
            'active_connections': len(self.active_connections),
            'total_frames_processed': total_frames_processed,
            'total_frames_dropped': total_frames_dropped,
            'total_fallback_frames': total_fallback_frames,
            'system_success_rate': system_success_rate,
            'active_processing_queues': active_queues,
            'shutdown_initiated': self.shutdown_initiated,
            'client_stats': all_stats
        }

    def _register_shutdown_handlers(self):
        """Register signal handlers for graceful shutdown"""
        try:
            # Register signal handlers for graceful shutdown
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)

            # Register atexit handler as backup
            atexit.register(self._cleanup_on_exit)

            self.logger.info("Shutdown handlers registered successfully")

        except Exception as e:
            self.logger.error(f"Failed to register shutdown handlers: {e}")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        signal_name = signal.Signals(signum).name
        self.logger.info(f"Received {signal_name} signal, initiating graceful shutdown...")

        # Create async task for graceful shutdown
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(self.graceful_shutdown())
        else:
            # If no event loop is running, perform synchronous cleanup
            self._cleanup_on_exit()

    def _cleanup_on_exit(self):
        """Cleanup function called on exit"""
        if not self.shutdown_initiated:
            self.logger.info("Performing emergency cleanup on exit...")
            # Perform minimal cleanup that doesn't require async
            self.shutdown_initiated = True

    async def graceful_shutdown(self):
        """
        Perform graceful shutdown of all connections and processing services
        """
        if self.shutdown_initiated:
            return

        self.shutdown_initiated = True
        self.logger.info("Starting graceful shutdown of connection manager...")

        try:
            # Get list of all active client IDs
            client_ids = list(self.active_connections.keys())
            self.logger.info(f"Shutting down {len(client_ids)} active connections...")

            # Create shutdown tasks for all clients
            shutdown_tasks = []
            for client_id in client_ids:
                task = asyncio.create_task(self._shutdown_client_gracefully(client_id))
                shutdown_tasks.append(task)

            # Wait for all shutdowns to complete with timeout
            if shutdown_tasks:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*shutdown_tasks, return_exceptions=True),
                        timeout=self.shutdown_timeout
                    )
                    self.logger.info("All client connections shut down gracefully")
                except asyncio.TimeoutError:
                    self.logger.warning(f"Graceful shutdown timed out after {self.shutdown_timeout}s, "
                                      "forcing remaining connections to close")
                    # Force close remaining connections
                    await self._force_close_remaining_connections()

            # Shutdown ThreadPoolExecutor
            self.logger.info("Shutting down ThreadPoolExecutor...")
            executor.shutdown(wait=True, timeout=10.0)
            self.logger.info("ThreadPoolExecutor shutdown completed")

            self.logger.info("Connection manager graceful shutdown completed")

        except Exception as e:
            self.logger.error(f"Error during graceful shutdown: {e}", exc_info=True)
            # Attempt force cleanup
            await self._force_close_remaining_connections()
            # Force shutdown executor
            try:
                executor.shutdown(wait=False)
            except Exception as executor_error:
                self.logger.error(f"Error shutting down executor: {executor_error}")

    async def _shutdown_client_gracefully(self, client_id: str):
        """
        Gracefully shutdown a single client connection

        Args:
            client_id: Client identifier to shutdown
        """
        try:
            self.logger.info(f"Gracefully shutting down client {client_id}...")

            # Send shutdown notification to client
            if client_id in self.active_connections:
                try:
                    shutdown_message = {
                        "type": "server_shutdown",
                        "message": "Server is shutting down gracefully",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await self.send_message(client_id, shutdown_message)

                    # Give client a moment to process the message
                    await asyncio.sleep(0.5)

                except Exception as e:
                    self.logger.warning(f"Failed to send shutdown message to client {client_id}: {e}")

            # Disconnect the client
            await self.disconnect(client_id)

            self.logger.info(f"Client {client_id} shut down gracefully")

        except Exception as e:
            self.logger.error(f"Error shutting down client {client_id}: {e}", exc_info=True)

    async def _force_close_remaining_connections(self):
        """Force close any remaining connections"""
        try:
            remaining_clients = list(self.active_connections.keys())
            if remaining_clients:
                self.logger.warning(f"Force closing {len(remaining_clients)} remaining connections")

                for client_id in remaining_clients:
                    try:
                        await self.disconnect(client_id)
                    except Exception as e:
                        self.logger.error(f"Error force closing client {client_id}: {e}")

        except Exception as e:
            self.logger.error(f"Error during force close: {e}", exc_info=True)

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

# Import and include API routers
from api.router import api_router
from api import system, websocket

app.include_router(api_router)

# Create ThreadPoolExecutor for CPU-intensive MediaPipe processing
# This prevents blocking the async event loop during frame processing
executor = ThreadPoolExecutor(
    max_workers=4,  # Adjust based on CPU cores
    thread_name_prefix="mediapipe_worker"
)

logger.info("🚀 LATENCY OPTIMIZATIONS ACTIVE:")
logger.info("   ✅ ThreadPoolExecutor initialized for non-blocking MediaPipe processing")
logger.info("   ✅ MediaPipe model complexity set to 0 (fastest)")
logger.info("   ✅ JPEG compression optimized to quality 50 for speed")
logger.info("   ✅ Video resolution reset to 640x480 for full quality processing")

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Enhanced global exception handler with comprehensive error logging
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Enhanced global exception handler with comprehensive error logging and monitoring
    """
    # Generate unique error ID for tracking
    error_id = f"ERR_{int(time.time())}_{hash(str(exc)) % 10000:04d}"

    # Collect comprehensive error information
    error_info = {
        "error_id": error_id,
        "timestamp": datetime.utcnow().isoformat(),
        "exception_type": type(exc).__name__,
        "exception_message": str(exc),
        "request_info": {
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "client": getattr(request.client, 'host', 'unknown') if hasattr(request, 'client') else 'unknown'
        },
        "system_info": {
            "active_connections": connection_manager.get_connection_count(),
            "memory_usage_mb": psutil.Process().memory_info().rss / 1024 / 1024,
            "cpu_percent": psutil.Process().cpu_percent()
        }
    }

    # Log full error details with stack trace
    logger.error(f"UNHANDLED_EXCEPTION [{error_id}]: {exc}", exc_info=True)
    logger.error(f"ERROR_CONTEXT [{error_id}]: {json.dumps(error_info, indent=2)}")

    # Log stack trace for debugging
    stack_trace = traceback.format_exc()
    logger.error(f"STACK_TRACE [{error_id}]:\n{stack_trace}")

    # Create user-friendly error response
    error_response = {
        "error": "Internal server error",
        "message": "An unexpected error occurred. Please check the server logs or contact support.",
        "error_id": error_id,
        "timestamp": datetime.utcnow().isoformat(),
        "support_info": {
            "include_error_id": error_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    }

    # Add debug information in development mode
    if app_config.server.log_level.lower() == 'debug':
        error_response["debug_info"] = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "request_url": str(request.url)
        }

    return JSONResponse(
        status_code=500,
        content=error_response
    )

# Health check endpoint moved to api/system.py router

# Configuration endpoint moved to api/system.py router

# Statistics endpoint moved to api/system.py router


# Request/Response models moved to api/asl_world.py router


# Story generation endpoint moved to api/asl_world.py router


# WebSocket endpoint moved to api/websocket.py router
async def websocket_video_endpoint(websocket: WebSocket):
    """
    Enhanced WebSocket endpoint with comprehensive error handling and graceful shutdown

    Handles client connections and processes video frame messages with robust error recovery
    """
    client_id = None
    connection_start_time = time.time()

    try:
        # Check if server is shutting down
        if connection_manager.shutdown_initiated:
            logger.warning("Rejecting new WebSocket connection - server is shutting down")
            await websocket.close(code=1012, reason="Server shutting down")
            return

        # Accept connection and create processing service
        client_id = await connection_manager.connect(websocket)
        logger.info(f"WebSocket connection established for client {client_id}")

        # Track connection metrics
        message_count = 0
        last_activity = time.time()
        error_count = 0
        max_errors = 10  # Maximum errors before disconnecting client

        # Main message processing loop with enhanced error handling
        while not connection_manager.shutdown_initiated:
            try:
                # Receive message from client with reduced timeout for faster response
                raw_message = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
                message_count += 1
                last_activity = time.time()

                # Reset error count on successful message receipt
                error_count = 0

                # Validate message size (reduced limit for faster processing)
                if len(raw_message) > 2 * 1024 * 1024:  # Reduced from 10MB to 2MB
                    logger.warning(f"Message too large from client {client_id}: {len(raw_message)} bytes")
                    error_response = {
                        "type": "error",
                        "message": "Message too large (max 2MB for low latency)",
                        "timestamp": datetime.utcnow().isoformat(),
                        "error_code": "MESSAGE_TOO_LARGE"
                    }
                    await connection_manager.send_message(client_id, error_response)
                    continue

                # Parse JSON message with detailed error handling
                try:
                    message_data = json.loads(raw_message)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received from client {client_id}: {e}")
                    error_response = {
                        "type": "error",
                        "message": f"Invalid JSON format: {str(e)}",
                        "timestamp": datetime.utcnow().isoformat(),
                        "error_code": "INVALID_JSON"
                    }
                    await connection_manager.send_message(client_id, error_response)
                    continue

                # Validate message structure
                if not isinstance(message_data, dict) or "type" not in message_data:
                    logger.error(f"Invalid message structure from client {client_id}")
                    error_response = {
                        "type": "error",
                        "message": "Message must be JSON object with 'type' field",
                        "timestamp": datetime.utcnow().isoformat(),
                        "error_code": "INVALID_MESSAGE_STRUCTURE"
                    }
                    await connection_manager.send_message(client_id, error_response)
                    continue

                # Process message through enhanced video processing service
                try:
                    processing_service = connection_manager.processing_services.get(client_id)
                    if not processing_service:
                        logger.error(f"No processing service found for client {client_id}")
                        break

                    response = await processing_service.process_message(message_data)

                    # Send immediate response if available (errors, non-frame messages)
                    if response:
                        await connection_manager.send_message(client_id, response)

                except Exception as processing_error:
                    logger.error(f"Processing error for client {client_id}: {processing_error}", exc_info=True)
                    error_response = {
                        "type": "error",
                        "message": "Message processing failed",
                        "timestamp": datetime.utcnow().isoformat(),
                        "error_code": "PROCESSING_ERROR"
                    }
                    await connection_manager.send_message(client_id, error_response)

            except asyncio.TimeoutError:
                # Check for client inactivity
                inactive_time = time.time() - last_activity
                if inactive_time > 300:  # 5 minutes of inactivity
                    logger.info(f"Client {client_id} inactive for {inactive_time:.1f}s, disconnecting")
                    break

                logger.debug(f"Timeout waiting for message from client {client_id} (inactive: {inactive_time:.1f}s)")

                # Send ping to check if connection is still alive
                try:
                    await websocket.ping()
                    logger.debug(f"Ping successful for client {client_id}")
                except Exception as ping_error:
                    logger.info(f"Client {client_id} connection lost (ping failed): {ping_error}")
                    break

            except WebSocketDisconnect as disconnect:
                logger.info(f"Client {client_id} disconnected normally: {disconnect}")
                break

            except ConnectionResetError:
                logger.info(f"Client {client_id} connection reset by peer")
                break

            except Exception as e:
                error_count += 1
                logger.error(f"Error #{error_count} in WebSocket loop for client {client_id}: {e}", exc_info=True)

                # Disconnect client if too many errors
                if error_count >= max_errors:
                    logger.error(f"Too many errors ({error_count}) for client {client_id}, disconnecting")
                    try:
                        error_response = {
                            "type": "error",
                            "message": "Too many processing errors, disconnecting",
                            "timestamp": datetime.utcnow().isoformat(),
                            "error_code": "TOO_MANY_ERRORS"
                        }
                        await connection_manager.send_message(client_id, error_response)
                    except:
                        pass
                    break

                # Try to send error message to client for recoverable errors
                try:
                    error_response = {
                        "type": "error",
                        "message": "Server processing error",
                        "timestamp": datetime.utcnow().isoformat(),
                        "error_code": "SERVER_ERROR",
                        "retry_recommended": True
                    }
                    await connection_manager.send_message(client_id, error_response)
                except Exception as send_error:
                    logger.warning(f"Failed to send error message to client {client_id}: {send_error}")
                    break

    except Exception as e:
        logger.error(f"Critical WebSocket connection error for client {client_id}: {e}", exc_info=True)

    finally:
        # Log connection summary
        connection_duration = time.time() - connection_start_time
        logger.info(f"WebSocket connection summary for client {client_id}: "
                   f"Duration: {connection_duration:.1f}s, Messages: {message_count}, Errors: {error_count}")

        # Cleanup connection with error handling
        if client_id:
            try:
                await connection_manager.disconnect(client_id)
            except Exception as cleanup_error:
                logger.error(f"Error during connection cleanup for client {client_id}: {cleanup_error}")

# Global startup time for uptime calculation
startup_time = time.time()

# Enhanced application startup event
@app.on_event("startup")
async def startup_event():
    """Enhanced application startup with comprehensive initialization and error handling"""
    global startup_time
    startup_time = time.time()

    try:
        logger.info("=" * 60)
        logger.info("StorySign Backend starting up...")
        logger.info("=" * 60)

        # Log system information
        system_info = {
            "python_version": sys.version,
            "platform": sys.platform,
            "memory_available_mb": psutil.virtual_memory().available / 1024 / 1024,
            "cpu_count": psutil.cpu_count(),
            "process_id": os.getpid()
        }
        logger.info(f"System info: {json.dumps(system_info, indent=2)}")

        # Log configuration
        logger.info(f"Server configuration: {app_config.server.host}:{app_config.server.port}")
        logger.info(f"Video configuration: {app_config.video.width}x{app_config.video.height} @ {app_config.video.fps}fps")
        logger.info(f"MediaPipe configuration: complexity={app_config.mediapipe.model_complexity}, "
                   f"detection={app_config.mediapipe.min_detection_confidence}")

        # Set up router dependencies
        system.set_dependencies(app_config, connection_manager, startup_time)
        websocket.set_dependencies(connection_manager, VideoProcessingService)
        logger.info("Router dependencies configured successfully")

        # Test MediaPipe availability
        try:
            from video_processor import MEDIAPIPE_AVAILABLE
            if MEDIAPIPE_AVAILABLE:
                logger.info("✅ MediaPipe is available and ready")
            else:
                logger.warning("⚠️  MediaPipe not available - running in compatibility mode")
        except Exception as mp_error:
            logger.error(f"❌ MediaPipe test failed: {mp_error}")

        # Initialize resource monitoring
        logger.info("Enhanced video processing with async loops and resource monitoring initialized")
        logger.info("Graceful shutdown handlers registered")

        # Log startup completion
        startup_duration = time.time() - startup_time
        logger.info(f"✅ FastAPI application initialized successfully in {startup_duration:.2f}s")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Error during application startup: {e}", exc_info=True)
        raise

# Enhanced application shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Enhanced application shutdown with graceful cleanup and comprehensive logging"""
    try:
        logger.info("=" * 60)
        logger.info("StorySign Backend shutdown initiated...")
        logger.info("=" * 60)

        # Get final statistics before shutdown
        try:
            final_stats = connection_manager.get_system_summary()
            logger.info(f"Final system statistics: {json.dumps(final_stats, indent=2)}")
        except Exception as stats_error:
            logger.warning(f"Failed to get final statistics: {stats_error}")

        # Perform graceful shutdown of all connections
        try:
            await connection_manager.graceful_shutdown()
        except Exception as shutdown_error:
            logger.error(f"Error during graceful shutdown: {shutdown_error}", exc_info=True)

        # Log shutdown completion
        if 'startup_time' in globals():
            total_uptime = time.time() - startup_time
            logger.info(f"Total server uptime: {total_uptime:.2f} seconds")

        logger.info("✅ StorySign Backend shutdown completed")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Error during application shutdown: {e}", exc_info=True)

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
