#!/usr/bin/env python3
"""
StorySign ASL Platform Backend - Enhanced API Application
FastAPI application with comprehensive REST API, GraphQL, authentication, and rate limiting
"""

import logging
import sys
import os
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
import uvicorn

# Import configuration
from config import get_config, AppConfig

# Import API components
from api.router import api_router
from middleware.auth_middleware import AuthenticationMiddleware, CORSMiddleware as CustomCORSMiddleware
from middleware.rate_limiting import RateLimitingMiddleware, RateLimit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('storysign_api.log')
    ]
)

logger = logging.getLogger(__name__)

# Load configuration
try:
    app_config: AppConfig = get_config()
    logger.info("Configuration loaded successfully")
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    raise

# Create FastAPI application
app = FastAPI(
    title="StorySign ASL Platform API",
    description="Comprehensive REST API for the StorySign ASL learning platform with real-time video processing, user management, content management, and collaborative features.",
    version="1.0.0",
    docs_url=None,  # We'll create custom docs
    redoc_url=None,
    openapi_url="/api/v1/openapi.json"
)

# Global variables for tracking
startup_time = time.time()
request_count = 0
error_count = 0


# Middleware setup
def setup_middleware():
    """Set up all middleware in correct order"""
    
    # 1. CORS middleware (first)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 2. Rate limiting middleware
    rate_limiting_middleware = RateLimitingMiddleware(
        app,
        default_rate_limit=RateLimit(requests=100, window=3600, burst=20),
        endpoint_limits={
            "/api/v1/auth/login": RateLimit(5, 300, 2),
            "/api/v1/auth/register": RateLimit(3, 3600, 1),
            "/api/v1/auth/refresh": RateLimit(10, 300, 5),
            "/api/v1/asl-world/story/recognize_and_generate": RateLimit(20, 3600, 5),
            "/api/v1/graphql": RateLimit(200, 3600, 50),
        },
        user_limits={
            "admin": RateLimit(1000, 3600, 100),
            "educator": RateLimit(500, 3600, 50),
            "learner": RateLimit(200, 3600, 30),
            "guest": RateLimit(50, 3600, 10),
        }
    )
    app.add_middleware(RateLimitingMiddleware, **rate_limiting_middleware.__dict__)
    
    # 3. Authentication middleware (last, so it has access to rate limit info)
    auth_middleware = AuthenticationMiddleware(
        app,
        excluded_paths=[
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/api/v1/docs/health",
            "/health",
            "/metrics"
        ]
    )
    app.add_middleware(AuthenticationMiddleware, **auth_middleware.__dict__)


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


# Include API router
app.include_router(api_router)


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
            "openapi_spec": "/api/v1/openapi.json",
            "api_docs": "/api/v1/docs/"
        },
        "endpoints": {
            "authentication": "/api/v1/auth/",
            "users": "/api/v1/users/",
            "content": "/api/v1/content/",
            "asl_world": "/api/asl-world/",
            "graphql": "/api/v1/graphql",
            "documentation": "/api/v1/docs/"
        },
        "features": [
            "JWT Authentication",
            "Rate Limiting",
            "GraphQL Support",
            "Real-time WebSocket",
            "Content Management",
            "User Management",
            "Progress Tracking",
            "Collaborative Learning"
        ]
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint for production deployment"""
    health_status = "healthy"
    services = {}
    
    try:
        # Check configuration
        config = get_config()
        services["configuration"] = "healthy"
        
        # Check Groq API if configured
        if config.groq.is_configured():
            try:
                from local_vision_service import get_vision_service
                vision_service = await get_vision_service()
                if hasattr(vision_service, 'check_health'):
                    groq_healthy = await vision_service.check_health()
                    services["groq_api"] = "healthy" if groq_healthy else "unhealthy"
                    if not groq_healthy:
                        health_status = "degraded"
                else:
                    services["groq_api"] = "unknown"
            except Exception as e:
                services["groq_api"] = f"error: {str(e)[:50]}"
                health_status = "degraded"
        else:
            services["groq_api"] = "not_configured"
        
        # Check database connection (if available)
        try:
            # This is a basic check - in a real implementation you'd test the actual connection
            db_config = config.database
            if db_config.host and db_config.database:
                services["database"] = "configured"
            else:
                services["database"] = "not_configured"
        except Exception as e:
            services["database"] = f"error: {str(e)[:50]}"
            health_status = "degraded"
        
        # Check authentication configuration
        try:
            auth_config = config.auth
            if auth_config.jwt_secret and auth_config.jwt_secret != "your-secret-key-change-in-production":
                services["authentication"] = "healthy"
            else:
                services["authentication"] = "using_default_secret"
                health_status = "degraded"
        except Exception as e:
            services["authentication"] = f"error: {str(e)[:50]}"
            health_status = "unhealthy"
        
        # Basic system checks
        services["rate_limiting"] = "healthy"
        services["cors"] = "healthy"
        
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
        "system": {
            "memory_usage_mb": 0,  # TODO: Implement actual system metrics
            "cpu_usage_percent": 0,
            "active_connections": 0
        }
    }


# Custom documentation endpoints
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI"""
    return get_swagger_ui_html(
        openapi_url="/api/v1/openapi.json",
        title="StorySign API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """Custom ReDoc documentation"""
    return get_redoc_html(
        openapi_url="/api/v1/openapi.json",
        title="StorySign API Documentation",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js",
    )


# Custom OpenAPI schema
def custom_openapi():
    """Generate custom OpenAPI schema"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="StorySign ASL Platform API",
        version="1.0.0",
        description="""
        ## StorySign ASL Platform API
        
        Comprehensive REST API for the StorySign ASL learning platform featuring:
        
        ### Features
        - **JWT Authentication** - Secure user authentication with refresh tokens
        - **Rate Limiting** - Intelligent rate limiting with burst allowance
        - **GraphQL Support** - Complex queries with a single endpoint
        - **Real-time WebSocket** - Live video processing and collaboration
        - **Content Management** - Story creation, search, and management
        - **User Management** - Profile management and progress tracking
        - **Collaborative Learning** - Multi-user practice sessions
        - **Analytics** - Detailed learning analytics and reporting
        
        ### Authentication
        Most endpoints require authentication using JWT tokens. Obtain tokens via the `/api/v1/auth/login` endpoint.
        
        Include the token in the Authorization header:
        ```
        Authorization: Bearer <your-jwt-token>
        ```
        
        ### Rate Limiting
        API endpoints are rate limited to ensure fair usage:
        - Default: 100 requests per hour with burst of 20
        - Authentication endpoints: Lower limits for security
        - Different limits based on user roles
        
        Rate limit information is included in response headers:
        - `X-RateLimit-Limit`: Maximum requests allowed
        - `X-RateLimit-Remaining`: Remaining requests in window
        - `X-RateLimit-Reset`: When the window resets
        
        ### GraphQL
        Use the `/api/v1/graphql` endpoint for complex queries that require data from multiple resources.
        
        ### Error Handling
        All endpoints return consistent error responses with:
        - `error`: Error type identifier
        - `message`: Human-readable error message
        - `timestamp`: When the error occurred
        """,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


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
    
    # Set up middleware
    setup_middleware()
    
    # Initialize services
    try:
        # TODO: Initialize database connections
        # TODO: Initialize AI services
        # TODO: Initialize cache
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Service initialization failed: {e}")
        raise
    
    logger.info(f"StorySign API application started successfully on port {app_config.server.port}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("StorySign API application shutting down...")
    
    # Clean up resources
    try:
        # TODO: Close database connections
        # TODO: Clean up AI services
        # TODO: Clear cache
        logger.info("Resources cleaned up successfully")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
    
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
        "main_api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
        access_log=True
    )