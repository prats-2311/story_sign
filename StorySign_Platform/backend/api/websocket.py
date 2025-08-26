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
        
        # Send initial connection confirmation immediately
        initial_message = {
            "type": "connection_established",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "WebSocket connection established successfully"
        }
        await websocket.send_text(json.dumps(initial_message))
        logger.info("Initial connection message sent")

        # Check if connection manager is available
        try:
            if connection_manager is None:
                logger.error("Connection manager not initialized - creating temporary instance")
                # Import and create temporary connection manager
                from main import ConnectionManager
                temp_connection_manager = ConnectionManager()
                client_id = await temp_connection_manager.connect(websocket)
                logger.info("Temporary connection manager created and client connected")
            else:
                # Connect client and get unique client ID
                client_id = await connection_manager.connect(websocket)
                logger.info("Client connected using global connection manager")
            
            logger.info(f"Client {client_id} connected successfully")
        except Exception as conn_error:
            logger.error(f"Error connecting client: {conn_error}", exc_info=True)
            await websocket.close(code=1011, reason="Connection setup failed")
            return

        # Initialize video processing service for this client
        try:
            if VideoProcessingService is None:
                logger.error("VideoProcessingService not available - importing directly")
                # Import directly from main
                from main import VideoProcessingService as MainVideoProcessingService
                video_service_class = MainVideoProcessingService
            else:
                video_service_class = VideoProcessingService

            from config import get_config
            app_config = get_config()
            logger.info(f"Creating video service for client {client_id}")
            video_service = video_service_class(client_id, app_config)
            logger.info(f"Video service created, starting processing...")

            # Start video processing for this client session
            await video_service.start_processing(websocket)
            logger.info(f"Video processing started for client {client_id}")
            
            # Register the processing service with the connection manager
            if connection_manager:
                connection_manager.register_processing_service(client_id, video_service)
            elif 'temp_connection_manager' in locals():
                temp_connection_manager.register_processing_service(client_id, video_service)
                
        except Exception as video_error:
            logger.error(f"Error initializing video service: {video_error}", exc_info=True)
            await websocket.close(code=1011, reason="Video service initialization failed")
            return

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
                    logger.debug(f"Responded to ping from client {client_id}")

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

                elif message_type == "control":
                    # Handle practice control messages (start_session, next_sentence, etc.)
                    logger.info(f"Received control message from client {client_id}: {message_data}")
                    
                    action = message_data.get("action", "unknown")
                    control_data = message_data.get("data", {})
                    
                    # Process control message through video service
                    try:
                        # Handle practice control through the frame processor
                        if hasattr(video_service, 'frame_processor') and hasattr(video_service.frame_processor, 'practice_session_manager'):
                            practice_manager = video_service.frame_processor.practice_session_manager
                            
                            if action == "start_session":
                                # Start practice session using control message handler
                                if practice_manager:
                                    result = practice_manager.handle_control_message(action, control_data)
                                    logger.info(f"Practice session started for client {client_id}: {result}")
                                
                                    # Send success response
                                    control_response = {
                                        "type": "practice_session_response",
                                        "action": "session_started",
                                        "timestamp": datetime.utcnow().isoformat(),
                                        "client_id": client_id,
                                        "result": result
                                    }
                                    await websocket.send_text(json.dumps(control_response))
                                else:
                                    # Send error if practice manager not available
                                    control_response = {
                                        "type": "practice_session_response",
                                        "action": "session_started",
                                        "timestamp": datetime.utcnow().isoformat(),
                                        "client_id": client_id,
                                        "result": {
                                            "success": False,
                                            "error": "Practice manager not available"
                                        }
                                    }
                                    await websocket.send_text(json.dumps(control_response))
                            
                            elif action in ["next_sentence", "try_again", "complete_story", "restart_story", "stop_session"]:
                                # Handle practice control actions through the practice manager
                                if practice_manager:
                                    result = practice_manager.handle_control_message(action, control_data)
                                    logger.info(f"Processing practice control: {action} for client {client_id}, result: {result}")
                                    
                                    # Send result response
                                    control_response = {
                                        "type": "control_response",
                                        "action": action,
                                        "timestamp": datetime.utcnow().isoformat(),
                                        "client_id": client_id,
                                        "result": result
                                    }
                                    await websocket.send_text(json.dumps(control_response))
                                else:
                                    # Send error if practice manager not available
                                    control_response = {
                                        "type": "control_response",
                                        "action": action,
                                        "timestamp": datetime.utcnow().isoformat(),
                                        "client_id": client_id,
                                        "result": {
                                            "success": False,
                                            "error": "Practice manager not available"
                                        }
                                    }
                                    await websocket.send_text(json.dumps(control_response))
                            
                            else:
                                logger.warning(f"Unknown control action '{action}' from client {client_id}")
                                error_response = {
                                    "type": "control_response",
                                    "action": action,
                                    "timestamp": datetime.utcnow().isoformat(),
                                    "client_id": client_id,
                                    "result": {
                                        "success": False,
                                        "error": f"Unknown control action: {action}"
                                    }
                                }
                                await websocket.send_text(json.dumps(error_response))
                        
                        else:
                            logger.error(f"Practice session manager not available for client {client_id}")
                            error_response = {
                                "type": "control_response",
                                "action": action,
                                "timestamp": datetime.utcnow().isoformat(),
                                "client_id": client_id,
                                "result": {
                                    "success": False,
                                    "error": "Practice session manager not available"
                                }
                            }
                            await websocket.send_text(json.dumps(error_response))
                    
                    except Exception as control_error:
                        logger.error(f"Error processing control message for client {client_id}: {control_error}", exc_info=True)
                        error_response = {
                            "type": "control_response",
                            "action": action,
                            "timestamp": datetime.utcnow().isoformat(),
                            "client_id": client_id,
                            "result": {
                                "success": False,
                                "error": f"Control processing error: {str(control_error)}"
                            }
                        }
                        await websocket.send_text(json.dumps(error_response))

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
                    logger.debug(f"Sent keepalive to client {client_id}")
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
            if client_id:
                if connection_manager:
                    await connection_manager.disconnect(client_id)
                elif 'temp_connection_manager' in locals():
                    await temp_connection_manager.disconnect(client_id)
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