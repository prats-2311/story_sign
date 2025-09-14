#!/usr/bin/env python3
"""
StorySign ASL Platform Backend - Production API (Fixed)
FastAPI application with real Groq Vision + Ollama integration and robust error handling
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

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Import configuration with error handling
CONFIG_AVAILABLE = False
try:
    from config import get_config
    CONFIG_AVAILABLE = True
    logger.info("Configuration module loaded successfully")
except ImportError as e:
    logger.warning(f"Configuration module not available: {e}")
except Exception as e:
    logger.error(f"Configuration error: {e}")

# Import core API modules with error handling
API_MODULES = {}

# Core working modules
try:
    from api import asl_world
    API_MODULES['asl_world'] = asl_world
    logger.info("ASL World module loaded (includes Groq + Ollama)")
except ImportError as e:
    logger.error(f"ASL World module failed to load: {e}")

try:
    from api import system
    API_MODULES['system'] = system
    logger.info("System module loaded")
except ImportError as e:
    logger.warning(f"System module not available: {e}")

try:
    from api import harmony
    API_MODULES['harmony'] = harmony
    logger.info("Harmony module loaded")
except ImportError as e:
    logger.warning(f"Harmony module not available: {e}")

try:
    from api import reconnect
    API_MODULES['reconnect'] = reconnect
    logger.info("Reconnect module loaded")
except ImportError as e:
    logger.warning(f"Reconnect module not available: {e}")

try:
    from api import websocket
    API_MODULES['websocket'] = websocket
    logger.info("WebSocket module loaded")
except ImportError as e:
    logger.warning(f"WebSocket module not available: {e}")

# Authentication with fallback
AUTH_AVAILABLE = False
try:
    from api import auth_db as auth
    API_MODULES['auth'] = auth
    AUTH_AVAILABLE = True
    logger.info("Database authentication loaded")
except ImportError:
    try:
        from api import auth_simple as auth
        API_MODULES['auth'] = auth
        AUTH_AVAILABLE = True
        logger.info("Simple authentication loaded")
    except ImportError as e:
        logger.warning(f"No authentication module available: {e}")

# Global variables for tracking
startup_time = time.time()
request_count = 0
error_count = 0

# Create FastAPI application
app = FastAPI(
    title="StorySign ASL Platform API",
    description="Production REST API for StorySign ASL learning platform with Groq Vision + Ollama integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://storysign-platform.netlify.app",
        "https://www.storysign-platform.netlify.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"  # Allow all origins for now
    ],
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

# Include API routers with error handling
for module_name, module in API_MODULES.items():
    try:
        if hasattr(module, 'router'):
            app.include_router(module.router)
            logger.info(f"Included {module_name} router")
        else:
            logger.warning(f"{module_name} module has no router attribute")
    except Exception as e:
        logger.error(f"Failed to include {module_name} router: {e}")

# Root endpoints
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "StorySign ASL Platform API - Production",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": time.time() - startup_time,
        "features": [
            "Groq Vision API Integration",
            "Ollama Story Generation", 
            "Real-time WebSocket",
            "JWT Authentication" if AUTH_AVAILABLE else "No Authentication",
            "TiDB Cloud Database" if CONFIG_AVAILABLE else "No Database"
        ],
        "loaded_modules": list(API_MODULES.keys()),
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_spec": "/openapi.json"
        },
        "endpoints": {
            "health": "/health",
            "asl_world": "/api/asl-world/" if 'asl_world' in API_MODULES else "not_available",
            "auth": "/api/v1/auth/" if AUTH_AVAILABLE else "not_available",
            "websocket": "/ws/" if 'websocket' in API_MODULES else "not_available"
        }
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint for production deployment"""
    health_status = "healthy"
    services = {}
    
    try:
        # Check configuration
        if CONFIG_AVAILABLE:
            try:
                config = get_config()
                services["configuration"] = "healthy"
                
                # Check Groq API configuration
                if hasattr(config, 'groq') and config.groq.is_configured():
                    services["groq_api"] = "configured"
                else:
                    services["groq_api"] = "not_configured"
                    health_status = "degraded"
                
                # Check Ollama configuration  
                if hasattr(config, 'ollama') and config.ollama.enabled:
                    services["ollama"] = "configured"
                else:
                    services["ollama"] = "not_configured"
                    health_status = "degraded"
                    
            except Exception as e:
                services["configuration"] = f"error: {str(e)[:50]}"
                health_status = "degraded"
        else:
            services["configuration"] = "not_available"
            health_status = "degraded"
        
        # Check vision service health
        try:
            from local_vision_service import get_vision_service
            vision_service = await get_vision_service()
            if hasattr(vision_service, 'check_health'):
                vision_healthy = await vision_service.check_health()
                services["vision_service"] = "healthy" if vision_healthy else "unhealthy"
                if not vision_healthy:
                    health_status = "degraded"
            else:
                services["vision_service"] = "unknown"
        except Exception as e:
            services["vision_service"] = f"error: {str(e)[:50]}"
            health_status = "degraded"
        
        # Check story generation service
        try:
            from ollama_service import get_ollama_service
            ollama_service = await get_ollama_service()
            if hasattr(ollama_service, 'check_health'):
                ollama_healthy = await ollama_service.check_health()
                services["story_service"] = "healthy" if ollama_healthy else "unhealthy"
                if not ollama_healthy:
                    health_status = "degraded"
            else:
                services["story_service"] = "unknown"
        except Exception as e:
            services["story_service"] = f"error: {str(e)[:50]}"
            health_status = "degraded"
        
        # Check loaded modules
        services["loaded_modules"] = list(API_MODULES.keys())
        services["authentication"] = "available" if AUTH_AVAILABLE else "not_available"
        
        # Check environment variables
        required_env_vars = ["GROQ_API_KEY", "JWT_SECRET"]
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
        },
        "loaded_modules": list(API_MODULES.keys()),
        "system": {
            "memory_usage_mb": 0,  # TODO: Implement actual system metrics
            "cpu_usage_percent": 0,
            "active_connections": 0
        }
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
    logger.info("StorySign Production API starting up...")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Port: {os.getenv('PORT', '8000')}")
    logger.info(f"Loaded modules: {list(API_MODULES.keys())}")
    
    # Initialize services
    try:
        # Test vision service
        if 'asl_world' in API_MODULES:
            try:
                from local_vision_service import get_vision_service
                vision_service = await get_vision_service()
                vision_healthy = await vision_service.check_health()
                logger.info(f"Vision service (Groq): {'healthy' if vision_healthy else 'unhealthy'}")
            except Exception as e:
                logger.warning(f"Vision service check failed: {e}")
            
            # Test story service
            try:
                from ollama_service import get_ollama_service
                ollama_service = await get_ollama_service()
                ollama_healthy = await ollama_service.check_health()
                logger.info(f"Story service (Ollama): {'healthy' if ollama_healthy else 'unhealthy'}")
            except Exception as e:
                logger.warning(f"Story service check failed: {e}")
        
    except Exception as e:
        logger.warning(f"Service initialization warning: {e}")
    
    logger.info("StorySign Production API started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("StorySign Production API shutting down...")
    logger.info("StorySign Production API shut down complete")

# Development server
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run StorySign Production API server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")), help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    logger.info(f"Starting StorySign Production API server on {args.host}:{args.port}")
    
    uvicorn.run(
        "main_api_fixed:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
        access_log=True
    )