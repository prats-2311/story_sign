#!/usr/bin/env python3
"""
StorySign ASL Platform Backend
FastAPI application for real-time ASL recognition and learning
"""

import logging
import sys
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from config import get_config, AppConfig

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
                "active_connections": 0
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