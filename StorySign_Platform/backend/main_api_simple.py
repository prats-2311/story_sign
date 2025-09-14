#!/usr/bin/env python3
"""
StorySign ASL Platform Backend - Simplified API for Deployment
Minimal FastAPI application for production deployment
"""

import logging
import sys
import os
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="StorySign ASL Platform API",
    description="REST API for the StorySign ASL learning platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Global variables for tracking
startup_time = time.time()
request_count = 0
error_count = 0

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request tracking middleware
@app.middleware("http")
async def track_requests(request: Request, call_next):
    """Track request metrics"""
    global request_count, error_count
    
    start_time = time.time()
    request_count += 1
    
    try:
        response = await call_next(request)
        
        # Track errors
        if response.status_code >= 400:
            error_count += 1
        
        # Add performance headers
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = str(request_count)
        
        return response
        
    except Exception as e:
        error_count += 1
        logger.error(f"Request processing error: {e}")
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An internal error occurred",
                "timestamp": time.time()
            }
        )

# Root endpoints
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "StorySign ASL Platform API",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": time.time() - startup_time,
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_spec": "/openapi.json"
        },
        "endpoints": {
            "health": "/health",
            "auth": "/api/v1/auth/",
            "users": "/api/v1/users/"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for production deployment"""
    health_status = "healthy"
    services = {}
    
    try:
        # Basic system checks
        services["api"] = "healthy"
        services["cors"] = "healthy"
        
        # Check environment variables
        required_env_vars = ["DATABASE_HOST", "JWT_SECRET"]
        missing_vars = []
        
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            services["environment"] = f"missing_vars: {', '.join(missing_vars)}"
            health_status = "degraded"
        else:
            services["environment"] = "healthy"
        
    except Exception as e:
        health_status = "unhealthy"
        services["system"] = f"error: {str(e)[:50]}"
    
    return {
        "status": health_status,
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": time.time() - startup_time,
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "request_count": request_count,
        "error_count": error_count,
        "error_rate": round((error_count / max(1, request_count)) * 100, 2),
        "services": services,
        "deployment": {
            "platform": "render" if os.getenv("RENDER") else "local",
            "port": os.getenv("PORT", "8000"),
            "workers": os.getenv("MAX_WORKERS", "4")
        }
    }

@app.get("/metrics")
async def get_metrics():
    """Get application metrics"""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": time.time() - startup_time,
        "requests": {
            "total": request_count,
            "errors": error_count,
            "error_rate_percent": (error_count / max(1, request_count)) * 100
        }
    }

# Basic API endpoints
@app.get("/api/v1/status")
async def api_status():
    """API status endpoint"""
    return {
        "api_version": "v1",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }

# User endpoints
@app.get("/api/v1/users/profile")
async def get_user_profile(request: Request):
    """Get user profile (demo mode)"""
    return {
        "success": True,
        "user": {
            "id": 1,
            "email": "demo@example.com",
            "username": "demo_user",
            "full_name": "Demo User",
            "role": "learner",
            "created_at": "2025-09-14T10:00:00Z",
            "progress": {
                "stories_completed": 5,
                "total_practice_time": 120,
                "current_level": "beginner"
            }
        }
    }

# Practice session endpoints
@app.post("/api/v1/practice/session")
async def create_practice_session(request: Request):
    """Create practice session (demo mode)"""
    try:
        body = await request.json()
        return {
            "success": True,
            "session": {
                "id": 1,
                "story_id": body.get("story_id", 1),
                "user_id": 1,
                "status": "active",
                "created_at": datetime.utcnow().isoformat()
            },
            "message": "Practice session created (demo mode)"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Session creation failed: {str(e)}"
        }

# Auth endpoints (simplified)
@app.post("/api/v1/auth/login")
async def login(request: Request):
    """Simplified login endpoint"""
    try:
        # For demo purposes, accept any login
        body = await request.json()
        return {
            "success": True,
            "message": "Login successful (demo mode)",
            "token": "demo-jwt-token-12345",
            "user": {
                "id": 1,
                "email": body.get("email", "demo@example.com"),
                "username": body.get("username", "demo_user"),
                "role": "learner"
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Login failed: {str(e)}",
            "status": "error"
        }

@app.post("/api/v1/auth/register")
async def register(request: Request):
    """Simplified register endpoint"""
    try:
        body = await request.json()
        return {
            "success": True,
            "message": "Registration successful (demo mode)",
            "user": {
                "id": 1,
                "email": body.get("email", "demo@example.com"),
                "username": body.get("username", "demo_user"),
                "role": "learner"
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Registration failed: {str(e)}",
            "status": "error"
        }

@app.post("/api/v1/auth/logout")
async def logout(request: Request):
    """Simplified logout endpoint"""
    return {
        "success": True,
        "message": "Logout successful (demo mode)"
    }

# Story generation endpoints (v1 versioned)
@app.post("/api/v1/asl-world/story/generate")
async def generate_story_v1(request: Request):
    """Simplified story generation endpoint (v1)"""
    try:
        body = await request.json()
        return {
            "success": True,
            "stories": [{
                "id": 1,
                "title": "Demo Story",
                "content": "This is a demo story generated from your scan. In a real implementation, this would use AI to create a personalized ASL learning story based on the objects you scanned.",
                "difficulty": "beginner",
                "sentences": [
                    "I see a book on the table.",
                    "The book is red and interesting.",
                    "I want to read this book."
                ],
                "vocabulary": ["book", "table", "red", "read"],
                "created_at": "2025-09-14T15:00:00Z"
            }],
            "message": "Story generated successfully (demo mode)"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Story generation failed: {str(e)}",
            "status": "error"
        }

@app.post("/api/v1/asl-world/story/recognize_and_generate")
async def recognize_and_generate_story_v1(request: Request):
    """Simplified object recognition and story generation (v1)"""
    try:
        # In demo mode, return a sample story regardless of input
        return {
            "success": True,
            "recognized_objects": ["book", "table", "lamp"],
            "stories": [{
                "id": 2,
                "title": "Objects Around Me",
                "content": "I can see several objects in this scene. There is a book, a table, and a lamp. These everyday objects can help us learn new signs in ASL.",
                "difficulty": "beginner",
                "sentences": [
                    "I see a book.",
                    "The table is brown.",
                    "The lamp gives light."
                ],
                "vocabulary": ["book", "table", "lamp", "see", "brown", "light"],
                "created_at": "2025-09-14T15:00:00Z"
            }],
            "message": "Objects recognized and story generated (demo mode)"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Recognition failed: {str(e)}",
            "status": "error"
        }

# Story generation endpoints (non-versioned - for frontend compatibility)
@app.post("/api/asl-world/story/generate")
async def generate_story(request: Request):
    """Simplified story generation endpoint (non-versioned)"""
    return await generate_story_v1(request)

@app.post("/api/asl-world/story/recognize_and_generate")
async def recognize_and_generate_story(request: Request):
    """Simplified object recognition and story generation (non-versioned)"""
    try:
        # In demo mode, return a sample story regardless of input
        body = await request.json()
        logger.info(f"Story generation request received with data: {len(str(body))} characters")
        
        return {
            "success": True,
            "recognized_objects": ["book", "table", "lamp", "chair"],
            "stories": [{
                "id": 2,
                "title": "My Scanned Objects Story",
                "content": "I used my camera to scan the objects around me. I can see a book, a table, a lamp, and a chair. These everyday objects help me practice ASL signs and learn new vocabulary.",
                "difficulty": "beginner",
                "sentences": [
                    "I see a book on the table.",
                    "The table is brown and sturdy.",
                    "The lamp gives bright light.",
                    "I sit on the comfortable chair."
                ],
                "vocabulary": ["book", "table", "lamp", "chair", "see", "brown", "light", "sit"],
                "created_at": "2025-09-14T15:00:00Z"
            }],
            "message": "Objects recognized and story generated from your scan (demo mode)"
        }
    except Exception as e:
        logger.error(f"Story generation error: {e}")
        return {
            "success": False,
            "message": f"Recognition failed: {str(e)}",
            "status": "error"
        }

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": time.time(),
            "path": str(request.url.path)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An internal error occurred",
            "timestamp": time.time(),
            "path": str(request.url.path)
        }
    )

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info("StorySign API application starting up...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Port: {os.getenv('PORT', '8000')}")
    logger.info("StorySign API application started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("StorySign API application shutting down...")
    logger.info("StorySign API application shut down complete")

# Development server
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run StorySign API server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    logger.info(f"Starting StorySign API server on {args.host}:{args.port}")
    
    uvicorn.run(
        "main_api_simple:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
        access_log=True
    )