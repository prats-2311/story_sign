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

class VideoProcessingService:
    """
    Video processing service for individual WebSocket client sessions
    Handles frame processing isolation per client connection
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
        
    async def start_processing(self, websocket: WebSocket):
        """Start video processing for this client session"""
        self.is_active = True
        self.logger.info(f"Starting video processing for client {self.client_id}")
        
    async def stop_processing(self):
        """Stop video processing for this client session"""
        self.is_active = False
        
        # Clean up frame processor resources
        if hasattr(self, 'frame_processor'):
            self.frame_processor.close()
            
        self.logger.info(f"Stopping video processing for client {self.client_id}")
        
    async def process_message(self, message_data: dict) -> Optional[dict]:
        """
        Process incoming WebSocket message from client
        
        Args:
            message_data: Parsed JSON message from client
            
        Returns:
            Response message dict or None if no response needed
        """
        try:
            message_type = message_data.get("type")
            
            if message_type == "raw_frame":
                return await self._process_raw_frame(message_data)
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
                
                # Process message through video processing service
                processing_service = connection_manager.processing_services[client_id]
                response = await processing_service.process_message(message_data)
                
                # Send response if available
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

# Application startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event handler"""
    logger.info("StorySign Backend starting up...")
    logger.info(f"Server configuration: {app_config.server.host}:{app_config.server.port}")
    logger.info(f"Video configuration: {app_config.video.width}x{app_config.video.height} @ {app_config.video.fps}fps")
    logger.info(f"MediaPipe configuration: complexity={app_config.mediapipe.model_complexity}, detection={app_config.mediapipe.min_detection_confidence}")
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