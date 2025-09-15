#!/usr/bin/env python3
"""
StorySign ASL Platform Backend - Unified API
Single file that works both locally and in production
Automatically detects environment and adjusts behavior accordingly
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

# Environment detection
IS_PRODUCTION = os.getenv("ENVIRONMENT") == "production" or os.getenv("RENDER") is not None
IS_LOCAL = not IS_PRODUCTION

# Configure logging
log_level = logging.INFO if IS_PRODUCTION else logging.DEBUG
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
logger.info(f"🌍 Environment detected: {'PRODUCTION' if IS_PRODUCTION else 'LOCAL DEVELOPMENT'}")

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

# Core working modules - try to load each one safely
modules_to_try = [
    ('asl_world', 'ASL World module loaded (includes Groq + Ollama)'),
    ('system', 'System module loaded'),
    ('harmony', 'Harmony module loaded'),
    ('reconnect', 'Reconnect module loaded'),
    ('websocket', 'WebSocket module loaded'),
    ('services_demo', 'Services demo module loaded')
]

for module_name, success_message in modules_to_try:
    try:
        module = __import__(f'api.{module_name}', fromlist=[module_name])
        API_MODULES[module_name] = module
        logger.info(success_message)
    except ImportError as e:
        if IS_LOCAL:
            logger.warning(f"{module_name.title()} module not available: {e}")
        else:
            logger.error(f"{module_name.title()} module failed to load: {e}")
    except Exception as e:
        logger.error(f"Error loading {module_name} module: {e}")

# Authentication with fallback - try database first, then simple
AUTH_AVAILABLE = False
auth_type = "none"

try:
    from api import auth_db as auth
    API_MODULES['auth'] = auth
    AUTH_AVAILABLE = True
    auth_type = "database"
    logger.info("Database authentication loaded (REAL DATA)")
except ImportError:
    try:
        from api import auth_simple as auth
        API_MODULES['auth'] = auth
        AUTH_AVAILABLE = True
        auth_type = "simple"
        logger.info("Simple authentication loaded")
    except ImportError as e:
        logger.warning(f"No authentication module available: {e}")

# Global variables for tracking
startup_time = time.time()
request_count = 0
error_count = 0

# Create FastAPI application
app_title = f"StorySign ASL Platform API - {'Production' if IS_PRODUCTION else 'Local Development'}"
app_description = f"{'Production' if IS_PRODUCTION else 'Local development'} API with real Groq Vision + Ollama integration"

app = FastAPI(
    title=app_title,
    description=app_description,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware - different settings for local vs production
if IS_LOCAL:
    # Local development - allow all origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("CORS configured for local development (allow all origins)")
else:
    # Production - specific origins only
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://storysign-platform.netlify.app",
            "https://www.storysign-platform.netlify.app",
            "http://localhost:3000",
            "http://127.0.0.1:3000"
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("CORS configured for production (specific origins)")

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
            logger.info(f"✅ Included {module_name} router")
        else:
            logger.warning(f"⚠️ {module_name} module has no router attribute")
    except Exception as e:
        logger.error(f"❌ Failed to include {module_name} router: {e}")

# Root endpoints
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": f"StorySign ASL Platform API - {'Production' if IS_PRODUCTION else 'Local Development'}",
        "version": "1.0.0",
        "status": "healthy",
        "environment": "production" if IS_PRODUCTION else "local_development",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": time.time() - startup_time,
        "features": [
            "Groq Vision API Integration",
            "Ollama Story Generation", 
            "Real-time WebSocket",
            f"JWT Authentication ({auth_type})" if AUTH_AVAILABLE else "No Authentication",
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
    """Comprehensive health check endpoint"""
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
                    if IS_PRODUCTION:
                        health_status = "degraded"
                
                # Check Ollama configuration  
                if hasattr(config, 'ollama') and config.ollama.enabled:
                    services["ollama"] = "configured"
                else:
                    services["ollama"] = "not_configured"
                    if IS_PRODUCTION:
                        health_status = "degraded"
                    
            except Exception as e:
                services["configuration"] = f"error: {str(e)[:50]}"
                health_status = "degraded"
        else:
            services["configuration"] = "not_available"
            if IS_PRODUCTION:
                health_status = "degraded"
        
        # Check vision service health (only in production or if explicitly requested)
        if IS_PRODUCTION or os.getenv("CHECK_SERVICES") == "true":
            try:
                from local_vision_service import get_vision_service
                vision_service = await get_vision_service()
                if hasattr(vision_service, 'check_health'):
                    vision_healthy = await vision_service.check_health()
                    services["vision_service"] = "healthy" if vision_healthy else "unhealthy"
                    if not vision_healthy and IS_PRODUCTION:
                        health_status = "degraded"
                else:
                    services["vision_service"] = "unknown"
            except Exception as e:
                services["vision_service"] = f"error: {str(e)[:50]}"
                if IS_PRODUCTION:
                    health_status = "degraded"
        else:
            services["vision_service"] = "skipped_in_local"
        
        # Check story generation service (only in production or if explicitly requested)
        if IS_PRODUCTION or os.getenv("CHECK_SERVICES") == "true":
            try:
                from ollama_service import get_ollama_service
                ollama_service = await get_ollama_service()
                if hasattr(ollama_service, 'check_health'):
                    ollama_healthy = await ollama_service.check_health()
                    services["story_service"] = "healthy" if ollama_healthy else "unhealthy"
                    if not ollama_healthy and IS_PRODUCTION:
                        health_status = "degraded"
                else:
                    services["story_service"] = "unknown"
            except Exception as e:
                services["story_service"] = f"error: {str(e)[:50]}"
                if IS_PRODUCTION:
                    health_status = "degraded"
        else:
            services["story_service"] = "skipped_in_local"
        
        # Check loaded modules
        services["loaded_modules"] = list(API_MODULES.keys())
        services["authentication"] = f"available ({auth_type})" if AUTH_AVAILABLE else "not_available"
        
        # Check environment variables (only critical ones in production)
        required_env_vars = ["GROQ_API_KEY", "JWT_SECRET"] if IS_PRODUCTION else []
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
        "environment": "production" if IS_PRODUCTION else "local_development",
        "request_count": request_count,
        "error_count": error_count,
        "error_rate": round((error_count / max(1, request_count)) * 100, 2),
        "services": services,
        "deployment": {
            "platform": "render" if IS_PRODUCTION else "local",
            "port": os.getenv("PORT", "8000"),
            "workers": os.getenv("MAX_WORKERS", "1")
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
        "environment": "production" if IS_PRODUCTION else "local_development"
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
    env_name = "Production" if IS_PRODUCTION else "Local Development"
    logger.info(f"StorySign {env_name} API starting up...")
    logger.info(f"Environment: {'production' if IS_PRODUCTION else 'local_development'}")
    logger.info(f"Port: {os.getenv('PORT', '8000')}")
    logger.info(f"Loaded modules: {list(API_MODULES.keys())}")
    logger.info(f"Authentication: {auth_type if AUTH_AVAILABLE else 'not_available'}")
    
    # Initialize services (only in production or if explicitly requested)
    if IS_PRODUCTION or os.getenv("CHECK_SERVICES") == "true":
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
    else:
        logger.info("Service health checks skipped in local development")
    
    logger.info(f"StorySign {env_name} API started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    env_name = "Production" if IS_PRODUCTION else "Local Development"
    logger.info(f"StorySign {env_name} API shutting down...")
    logger.info(f"StorySign {env_name} API shut down complete")

# Development server
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run StorySign API server")
    parser.add_argument("--host", default="127.0.0.1" if IS_LOCAL else "0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")), help="Port to bind to")
    parser.add_argument("--reload", action="store_true", default=IS_LOCAL, help="Enable auto-reload")
    parser.add_argument("--log-level", default="debug" if IS_LOCAL else "info", help="Log level")
    
    args = parser.parse_args()
    
    env_name = "Production" if IS_PRODUCTION else "Local Development"
    logger.info(f"🚀 Starting StorySign {env_name} API server")
    logger.info(f"📍 URL: http://{args.host}:{args.port}")
    logger.info(f"📚 Docs: http://{args.host}:{args.port}/docs")
    logger.info(f"🔧 Loaded modules: {list(API_MODULES.keys())}")
    logger.info(f"🔐 Authentication: {auth_type if AUTH_AVAILABLE else 'not_available'}")
    
    uvicorn.run(
        "main_api_unified:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
        access_log=True
    )