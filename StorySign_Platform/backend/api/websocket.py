"""
WebSocket API router
Contains WebSocket endpoints for real-time video processing
"""

import logging
import json
import asyncio
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

# Create router for WebSocket endpoints
router = APIRouter(tags=["websocket"])

# Global variables that will be set by main.py
connection_manager = None
VideoProcessingService = None

def set_dependencies(conn_manager, video_service_class):
    """Set dependencies from main.py"""
    global connection_manager, VideoProcessingService
    connection_manager = conn_manager
    VideoProcessingService = video_service_class


@router.websocket("/ws/video")
async def websocket_video_endpoint(websocket: WebSocket):
    """
    Enhanced WebSocket endpoint with comprehensive error handling and graceful shutdown

    Handles real-time video processing for ASL recognition with MediaPipe integration,
    performance monitoring, resource management, and graceful error recovery.

    Args:
        websocket: WebSocket connection for real-time communication

    Features:
        - Individual client session management with unique client IDs
        - Async video processing with queue management and performance optimization
        - Comprehensive error handling with graceful degradation
        - Resource monitoring and automatic cleanup
        - Enhanced logging and debugging capabilities
        - Graceful shutdown handling for server maintenance
    """
    client_id = None
    video_service = None

    try:
        # Accept WebSocket connection
        await websocket.accept()
        logger.info("WebSocket connection accepted, initializing client session")

        # Connect client and get unique client ID
        client_id = await connection_manager.connect(websocket)
        logger.info(f"Client {client_id} connected successfully")

        # Initialize video processing service for this client
        from config import get_config
        app_config = get_config()
        video_service = VideoProcessingService(client_id, app_config)

        # Start video processing for this client session
        await video_service.start_processing(websocket)

        # Send initial connection confirmation
        connection_message = {
            "type": "connection_established",
            "timestamp": datetime.utcnow().isoformat(),
            "client_id": client_id,
            "message": "WebSocket connection established successfully",
            "server_info": {
                "version": "1.0.0",
                "features": ["real_time_processing", "gesture_analysis", "story_generation"],
                "max_frame_rate": app_config.video.fps,
                "supported_formats": [app_config.video.format]
            }
        }

        await websocket.send_text(json.dumps(connection_message))
        logger.info(f"Connection confirmation sent to client {client_id}")

        # Main message processing loop
        while True:
            try:
                # Receive message from client with timeout
                message_text = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=60.0  # 60 second timeout for client messages
                )

                # Parse and validate message
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
                    await websocket.send_text(json.dumps(error_response))
                    continue

                # Handle different message types
                message_type = message_data.get("type", "unknown")

                if message_type == "raw_frame":
                    # Add frame to processing queue (non-blocking)
                    try:
                        await asyncio.wait_for(
                            video_service.frame_queue.put(message_data),
                            timeout=0.1  # Very short timeout to prevent blocking
                        )
                    except asyncio.TimeoutError:
                        # Queue is full, drop frame to maintain real-time performance
                        video_service.processing_stats['frames_dropped'] += 1
                        logger.debug(f"Frame dropped for client {client_id} - queue full")

                elif message_type == "ping":
                    # Respond to ping with pong
                    pong_response = {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat(),
                        "client_id": client_id
                    }
                    await websocket.send_text(json.dumps(pong_response))

                elif message_type == "get_stats":
                    # Send current processing statistics
                    current_stats = await video_service.resource_monitor.get_current_stats()
                    stats_response = {
                        "type": "stats",
                        "timestamp": datetime.utcnow().isoformat(),
                        "client_id": client_id,
                        "processing_stats": video_service.processing_stats,
                        "resource_stats": current_stats
                    }
                    await websocket.send_text(json.dumps(stats_response))

                else:
                    logger.warning(f"Unknown message type '{message_type}' from client {client_id}")
                    error_response = {
                        "type": "error",
                        "timestamp": datetime.utcnow().isoformat(),
                        "message": f"Unknown message type: {message_type}",
                        "client_id": client_id
                    }
                    await websocket.send_text(json.dumps(error_response))

            except asyncio.TimeoutError:
                # Client hasn't sent a message in 60 seconds - send keepalive
                keepalive_message = {
                    "type": "keepalive",
                    "timestamp": datetime.utcnow().isoformat(),
                    "client_id": client_id,
                    "message": "Connection is active"
                }
                try:
                    await websocket.send_text(json.dumps(keepalive_message))
                except Exception as e:
                    logger.warning(f"Failed to send keepalive to client {client_id}: {e}")
                    break  # Connection is likely broken

            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected normally")
                break

            except Exception as e:
                logger.error(f"Error processing message from client {client_id}: {e}", exc_info=True)
                
                # Try to send error response
                try:
                    error_response = {
                        "type": "processing_error",
                        "timestamp": datetime.utcnow().isoformat(),
                        "message": "Error processing your request",
                        "client_id": client_id,
                        "retry_allowed": True
                    }
                    await websocket.send_text(json.dumps(error_response))
                except Exception as send_error:
                    logger.error(f"Failed to send error response to client {client_id}: {send_error}")
                    break  # Connection is likely broken

    except WebSocketDisconnect:
        logger.info(f"Client {client_id or 'unknown'} disconnected during setup")

    except Exception as e:
        logger.error(f"Critical error in WebSocket endpoint for client {client_id or 'unknown'}: {e}", exc_info=True)

        # Try to send critical error message
        try:
            if websocket and client_id:
                critical_error_response = {
                    "type": "critical_error",
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "A critical error occurred. Please reconnect.",
                    "client_id": client_id,
                    "requires_reconnection": True
                }
                await websocket.send_text(json.dumps(critical_error_response))
        except Exception as send_error:
            logger.error(f"Failed to send critical error response to client {client_id}: {send_error}")

    finally:
        # Comprehensive cleanup
        try:
            # Stop video processing service
            if video_service:
                await video_service.stop_processing()
                logger.info(f"Video processing stopped for client {client_id}")

            # Disconnect from connection manager
            if client_id and connection_manager:
                await connection_manager.disconnect(client_id)
                logger.info(f"Client {client_id} disconnected and cleaned up")

            # Close WebSocket connection if still open
            try:
                if websocket:
                    await websocket.close()
            except Exception as close_error:
                logger.debug(f"WebSocket already closed for client {client_id}: {close_error}")

        except Exception as cleanup_error:
            logger.error(f"Error during cleanup for client {client_id}: {cleanup_error}", exc_info=True)

        logger.info(f"WebSocket endpoint cleanup completed for client {client_id or 'unknown'}")