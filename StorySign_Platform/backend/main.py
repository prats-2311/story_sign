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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
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

# Application startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event handler"""
    logger.info("StorySign Backend starting up...")
    logger.info("FastAPI application initialized successfully")

# Application shutdown event  
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler"""
    logger.info("StorySign Backend shutting down...")

if __name__ == "__main__":
    # This allows running the app directly with python main.py
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=8000,
        reload=True,
        log_level="info"
    )