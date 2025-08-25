"""
System API router
Contains system-level endpoints like health checks, configuration, and statistics
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

# Create router for system endpoints
router = APIRouter(tags=["system"])

# Global variables that will be set by main.py
app_config = None
connection_manager = None
startup_time = None

def set_dependencies(config, conn_manager, start_time):
    """Set dependencies from main.py"""
    global app_config, connection_manager, startup_time
    app_config = config
    connection_manager = conn_manager
    startup_time = start_time


@router.get("/")
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
                "active_connections": connection_manager.get_connection_count() if connection_manager else 0
            },
            "configuration": {
                "video": {
                    "resolution": f"{app_config.video.width}x{app_config.video.height}" if app_config else "unknown",
                    "fps": app_config.video.fps if app_config else "unknown",
                    "format": app_config.video.format if app_config else "unknown"
                },
                "mediapipe": {
                    "model_complexity": app_config.mediapipe.model_complexity if app_config else "unknown",
                    "detection_confidence": app_config.mediapipe.min_detection_confidence if app_config else "unknown",
                    "tracking_confidence": app_config.mediapipe.min_tracking_confidence if app_config else "unknown"
                },
                "server": {
                    "max_connections": app_config.server.max_connections if app_config else "unknown",
                    "log_level": app_config.server.log_level if app_config else "unknown"
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


@router.get("/config")
async def get_configuration() -> Dict[str, Any]:
    """
    Get current application configuration

    Returns:
        Dict containing current configuration settings
    """
    try:
        logger.info("Configuration endpoint accessed")

        if not app_config:
            raise HTTPException(
                status_code=503,
                detail="Configuration not available"
            )

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


@router.get("/stats")
async def get_processing_statistics() -> Dict[str, Any]:
    """
    Get current processing statistics for all connections

    Returns:
        Dict containing system-wide processing statistics
    """
    try:
        logger.info("Processing statistics endpoint accessed")

        if not connection_manager:
            raise HTTPException(
                status_code=503,
                detail="Connection manager not available"
            )

        # Get system summary with all client statistics
        system_summary = connection_manager.get_system_summary()

        # Add timestamp and system info
        stats_response = {
            "timestamp": datetime.utcnow().isoformat(),
            "system_summary": system_summary,
            "server_info": {
                "uptime_seconds": time.time() - startup_time if startup_time else 0,
                "configuration": {
                    "max_connections": app_config.server.max_connections if app_config else "unknown",
                    "video_resolution": f"{app_config.video.width}x{app_config.video.height}" if app_config else "unknown",
                    "mediapipe_complexity": app_config.mediapipe.model_complexity if app_config else "unknown"
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