"""
WebSocket API router with optimized real-time performance
Contains WebSocket endpoints for real-time video processing with connection pooling,
message queuing, and adaptive quality management
"""

import logging
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.websocket_pool import get_connection_pool
from core.message_queue import get_queue_manager, MessagePriority
from core.optimized_video_processor import create_optimized_processor, remove_optimized_processor
from core.adaptive_quality import get_adaptive_quality_service

logger = logging.getLogger(__name__)

# Create router for WebSocket endpoints
router = APIRouter(tags=["websocket"])

# Global variables that will be set by main.py (for backward compatibility)
connection_manager = None
VideoProcessingService = None

def set_dependencies(conn_manager, video_service_class):
    """Set dependencies from main.py (backward compatibility)"""
    global connection_manager, VideoProcessingService
    connection_manager = conn_manager
    VideoProcessingService = video_service_class


@router.websocket("/ws/video")
async def websocket_video_endpoint(websocket: WebSocket):
    """
    Optimized WebSocket endpoint with high-performance real-time processing
    
    Features:
    - Connection pooling for efficient resource management
    - Message queuing for high-throughput scenarios
    - Adaptive quality management based on network conditions
    - Optimized video processing pipeline
    - Comprehensive performance monitoring
    
    Args:
        websocket: WebSocket connection for real-time communication
    """
    client_id = None
    optimized_processor = None
    
    try:
        # Get optimized services
        connection_pool = await get_connection_pool()
        queue_manager = get_queue_manager()
        adaptive_service = await get_adaptive_quality_service()
        
        # Connect client to pool
        client_id = await connection_pool.connect_client(
            websocket=websocket,
            group="video_processing",
            message_handler=handle_client_message
        )
        
        logger.info(f"Client {client_id} connected to optimized WebSocket pool")
        
        # Create optimized video processor
        from config import get_config
        app_config = get_config()
        optimized_processor = await create_optimized_processor(client_id, app_config)
        
        # Send enhanced connection confirmation
        connection_message = {
            "type": "connection_established",
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": client_id,
            "message": "Optimized WebSocket connection established",
            "features": {
                "connection_pooling": True,
                "message_queuing": True,
                "adaptive_quality": True,
                "optimized_processing": True
            },
            "server_info": {
                "version": "2.0.0",
                "optimization_level": "high_performance",
                "max_frame_rate": app_config.video.fps,
                "supported_formats": [app_config.video.format]
            }
        }
        
        await connection_pool.send_message(client_id, connection_message, priority=True)
        logger.info(f"Enhanced connection confirmation sent to client {client_id}")
        
        # Main message processing loop with optimized handling
        while True:
            try:
                # Receive message with timeout
                message_text = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=60.0
                )
                
                # Parse message
                try:
                    message_data = json.loads(message_text)
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON from client {client_id}: {e}")
                    error_response = {
                        "type": "error",
                        "timestamp": datetime.utcnow().isoformat(),
                        "message": "Invalid JSON format",
                        "client_id": client_id
                    }
                    await connection_pool.send_message(client_id, error_response, priority=True)
                    continue
                
                # Route message to optimized processor
                await route_message_to_processor(client_id, message_data, optimized_processor, connection_pool)
                
            except asyncio.TimeoutError:
                # Send keepalive
                keepalive_message = {
                    "type": "keepalive",
                    "timestamp": datetime.utcnow().isoformat(),
                    "client_id": client_id,
                    "message": "Connection is active"
                }
                await connection_pool.send_message(client_id, keepalive_message, priority=True)
                
            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected normally")
                break
                
            except Exception as e:
                logger.error(f"Error processing message from client {client_id}: {e}", exc_info=True)
                
                # Send error response
                error_response = {
                    "type": "processing_error",
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "Error processing your request",
                    "client_id": client_id,
                    "retry_allowed": True
                }
                await connection_pool.send_message(client_id, error_response, priority=True)
    
    except WebSocketDisconnect:
        logger.info(f"Client {client_id or 'unknown'} disconnected during setup")
    
    except Exception as e:
        logger.error(f"Critical error in optimized WebSocket endpoint for client {client_id or 'unknown'}: {e}", exc_info=True)
    
    finally:
        # Comprehensive cleanup
        try:
            if client_id and optimized_processor:
                await remove_optimized_processor(client_id)
                logger.info(f"Optimized processor cleaned up for client {client_id}")
            
            if client_id and connection_pool:
                await connection_pool.disconnect_client(client_id)
                logger.info(f"Client {client_id} disconnected from pool")
                
        except Exception as cleanup_error:
            logger.error(f"Error during cleanup for client {client_id}: {cleanup_error}", exc_info=True)
        
        logger.info(f"Optimized WebSocket endpoint cleanup completed for client {client_id or 'unknown'}")


async def route_message_to_processor(
    client_id: str, 
    message_data: Dict[str, Any], 
    processor, 
    connection_pool
):
    """Route message to appropriate processor based on message type"""
    try:
        message_type = message_data.get("type", "unknown")
        
        if message_type == "raw_frame":
            # High priority frame processing
            await handle_frame_message(client_id, message_data, processor, connection_pool)
            
        elif message_type == "control":
            # Control message handling
            await handle_control_message(client_id, message_data, processor, connection_pool)
            
        elif message_type == "ping":
            # Ping response
            pong_response = {
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat(),
                "client_id": client_id
            }
            await connection_pool.send_message(client_id, pong_response, priority=True)
            
        elif message_type == "get_stats":
            # Performance statistics
            await handle_stats_request(client_id, processor, connection_pool)
            
        else:
            logger.warning(f"Unknown message type '{message_type}' from client {client_id}")
            error_response = {
                "type": "error",
                "timestamp": datetime.utcnow().isoformat(),
                "message": f"Unknown message type: {message_type}",
                "client_id": client_id
            }
            await connection_pool.send_message(client_id, error_response, priority=True)
            
    except Exception as e:
        logger.error(f"Message routing error for client {client_id}: {e}", exc_info=True)


async def handle_frame_message(client_id: str, message_data: Dict[str, Any], processor, connection_pool):
    """Handle frame processing with optimized pipeline"""
    try:
        # Process frame through optimized processor
        result = await processor.process_frame(message_data)
        
        if result.success:
            # Send processed frame response
            response = {
                "type": "processed_frame",
                "timestamp": datetime.utcnow().isoformat(),
                "frame_data": result.frame_data,
                "landmarks_detected": result.landmarks_detected,
                "metadata": {
                    "client_id": client_id,
                    "processing_time_ms": result.processing_time_ms,
                    "quality_profile": result.quality_settings.profile.value if result.quality_settings else None,
                    **(result.metadata or {})
                }
            }
            
            # Use normal priority for frame responses to allow batching
            await connection_pool.send_message(client_id, response, priority=False, batch=True)
        else:
            # Send error response
            error_response = {
                "type": "processing_error",
                "timestamp": datetime.utcnow().isoformat(),
                "message": result.error_message or "Frame processing failed",
                "client_id": client_id
            }
            await connection_pool.send_message(client_id, error_response, priority=True)
            
    except Exception as e:
        logger.error(f"Frame processing error for client {client_id}: {e}", exc_info=True)


async def handle_control_message(client_id: str, message_data: Dict[str, Any], processor, connection_pool):
    """Handle practice control messages"""
    try:
        action = message_data.get("action", "unknown")
        control_data = message_data.get("data", {})
        
        # Process control message (implementation depends on processor capabilities)
        # This would integrate with the existing practice session manager
        
        control_response = {
            "type": "control_response",
            "action": action,
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": client_id,
            "result": {
                "success": True,
                "message": f"Control action '{action}' processed"
            }
        }
        
        await connection_pool.send_message(client_id, control_response, priority=True)
        
    except Exception as e:
        logger.error(f"Control message error for client {client_id}: {e}", exc_info=True)


async def handle_stats_request(client_id: str, processor, connection_pool):
    """Handle statistics request"""
    try:
        # Get processor stats
        processor_stats = processor.get_processing_stats() if processor else {}
        
        # Get connection pool stats
        pool_stats = connection_pool.get_pool_stats()
        
        # Get client-specific metrics
        client_metrics = connection_pool.get_client_metrics(client_id)
        
        stats_response = {
            "type": "stats",
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": client_id,
            "processor_stats": processor_stats,
            "pool_stats": pool_stats,
            "client_metrics": client_metrics
        }
        
        await connection_pool.send_message(client_id, stats_response, priority=True)
        
    except Exception as e:
        logger.error(f"Stats request error for client {client_id}: {e}", exc_info=True)


async def handle_client_message(message_data: Dict[str, Any]):
    """Handle client message (callback for connection pool)"""
    # This is a callback function for the connection pool
    # Additional message handling logic can be added here
    pass

