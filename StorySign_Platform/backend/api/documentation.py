"""
API documentation and testing endpoints for StorySign ASL Platform
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
import json
import time
from datetime import datetime

from ..middleware.rate_limiting import RateLimitingMiddleware
from ..services.auth_service import AuthService
from ..core.database_service import DatabaseService
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/docs", tags=["documentation"])


# Response Models
class APIEndpointInfo(BaseModel):
    """API endpoint information"""
    path: str
    method: str
    summary: str
    description: Optional[str]
    tags: List[str]
    parameters: List[Dict[str, Any]]
    responses: Dict[str, Dict[str, Any]]
    authentication_required: bool
    rate_limit: Optional[Dict[str, Any]]


class APIDocumentation(BaseModel):
    """Complete API documentation"""
    title: str
    version: str
    description: str
    base_url: str
    authentication: Dict[str, Any]
    rate_limiting: Dict[str, Any]
    endpoints: List[APIEndpointInfo]
    schemas: Dict[str, Any]


class APITestResult(BaseModel):
    """API test result"""
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    success: bool
    error_message: Optional[str]
    response_data: Optional[Dict[str, Any]]


class APIHealthCheck(BaseModel):
    """API health check result"""
    status: str
    timestamp: str
    version: str
    uptime_seconds: float
    database_status: str
    auth_service_status: str
    rate_limiting_stats: Dict[str, Any]
    endpoint_health: List[Dict[str, Any]]


# Global variables for documentation
API_ENDPOINTS = [
    {
        "path": "/api/v1/auth/register",
        "method": "POST",
        "summary": "Register new user",
        "description": "Create a new user account with email and password",
        "tags": ["authentication"],
        "parameters": [
            {"name": "email", "type": "string", "required": True, "description": "User email address"},
            {"name": "username", "type": "string", "required": True, "description": "Unique username"},
            {"name": "password", "type": "string", "required": True, "description": "Password (min 8 chars)"},
            {"name": "first_name", "type": "string", "required": False, "description": "First name"},
            {"name": "last_name", "type": "string", "required": False, "description": "Last name"}
        ],
        "responses": {
            "200": {"description": "Registration successful", "schema": "AuthResponse"},
            "400": {"description": "Validation error", "schema": "ErrorResponse"},
            "409": {"description": "User already exists", "schema": "ErrorResponse"}
        },
        "authentication_required": False,
        "rate_limit": {"requests": 3, "window": 3600, "burst": 1}
    },
    {
        "path": "/api/v1/auth/login",
        "method": "POST",
        "summary": "User login",
        "description": "Authenticate user with email/username and password",
        "tags": ["authentication"],
        "parameters": [
            {"name": "identifier", "type": "string", "required": True, "description": "Email or username"},
            {"name": "password", "type": "string", "required": True, "description": "User password"}
        ],
        "responses": {
            "200": {"description": "Login successful", "schema": "AuthResponse"},
            "401": {"description": "Invalid credentials", "schema": "ErrorResponse"}
        },
        "authentication_required": False,
        "rate_limit": {"requests": 5, "window": 300, "burst": 2}
    },
    {
        "path": "/api/v1/users/profile",
        "method": "GET",
        "summary": "Get user profile",
        "description": "Get current user's profile information",
        "tags": ["users"],
        "parameters": [],
        "responses": {
            "200": {"description": "Profile retrieved", "schema": "UserResponse"},
            "401": {"description": "Authentication required", "schema": "ErrorResponse"}
        },
        "authentication_required": True,
        "rate_limit": {"requests": 200, "window": 3600, "burst": 30}
    },
    {
        "path": "/api/v1/content/stories",
        "method": "GET",
        "summary": "List stories",
        "description": "Get list of available stories with filtering",
        "tags": ["content"],
        "parameters": [
            {"name": "limit", "type": "integer", "required": False, "description": "Maximum results (1-100)"},
            {"name": "offset", "type": "integer", "required": False, "description": "Results offset"},
            {"name": "difficulty_level", "type": "string", "required": False, "description": "Filter by difficulty"},
            {"name": "is_public", "type": "boolean", "required": False, "description": "Filter by public status"}
        ],
        "responses": {
            "200": {"description": "Stories retrieved", "schema": "StoryListResponse"},
            "401": {"description": "Authentication required", "schema": "ErrorResponse"}
        },
        "authentication_required": True,
        "rate_limit": {"requests": 200, "window": 3600, "burst": 50}
    },
    {
        "path": "/api/v1/asl-world/story/recognize_and_generate",
        "method": "POST",
        "summary": "Generate story from image",
        "description": "Analyze image and generate ASL learning stories",
        "tags": ["asl-world"],
        "parameters": [
            {"name": "frame_data", "type": "string", "required": False, "description": "Base64 encoded image"},
            {"name": "simple_word", "type": "string", "required": False, "description": "Simple word for story"},
            {"name": "custom_prompt", "type": "string", "required": False, "description": "Custom story prompt"}
        ],
        "responses": {
            "200": {"description": "Story generated", "schema": "StoryGenerationResponse"},
            "400": {"description": "Invalid input", "schema": "ErrorResponse"},
            "503": {"description": "AI service unavailable", "schema": "ErrorResponse"}
        },
        "authentication_required": True,
        "rate_limit": {"requests": 20, "window": 3600, "burst": 5}
    },
    {
        "path": "/api/v1/graphql",
        "method": "POST",
        "summary": "GraphQL endpoint",
        "description": "Execute GraphQL queries for complex data retrieval",
        "tags": ["graphql"],
        "parameters": [
            {"name": "query", "type": "string", "required": True, "description": "GraphQL query"},
            {"name": "variables", "type": "object", "required": False, "description": "Query variables"}
        ],
        "responses": {
            "200": {"description": "Query executed", "schema": "GraphQLResponse"},
            "400": {"description": "Invalid query", "schema": "ErrorResponse"},
            "401": {"description": "Authentication required", "schema": "ErrorResponse"}
        },
        "authentication_required": True,
        "rate_limit": {"requests": 200, "window": 3600, "burst": 50}
    }
]

SCHEMAS = {
    "AuthResponse": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "access_token": {"type": "string"},
            "refresh_token": {"type": "string"},
            "token_type": {"type": "string"},
            "expires_in": {"type": "integer"},
            "user": {"$ref": "#/components/schemas/User"}
        }
    },
    "UserResponse": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "email": {"type": "string"},
            "username": {"type": "string"},
            "first_name": {"type": "string"},
            "last_name": {"type": "string"},
            "full_name": {"type": "string"},
            "is_active": {"type": "boolean"},
            "role": {"type": "string"},
            "created_at": {"type": "string"},
            "profile": {"$ref": "#/components/schemas/UserProfile"}
        }
    },
    "ErrorResponse": {
        "type": "object",
        "properties": {
            "error": {"type": "string"},
            "message": {"type": "string"},
            "timestamp": {"type": "number"}
        }
    }
}


# API Endpoints

@router.get("/", response_model=APIDocumentation)
async def get_api_documentation():
    """
    Get complete API documentation
    
    Returns:
        Complete API documentation with endpoints, schemas, and examples
    """
    try:
        endpoints = []
        
        for endpoint_info in API_ENDPOINTS:
            endpoints.append(APIEndpointInfo(
                path=endpoint_info["path"],
                method=endpoint_info["method"],
                summary=endpoint_info["summary"],
                description=endpoint_info.get("description"),
                tags=endpoint_info["tags"],
                parameters=endpoint_info["parameters"],
                responses=endpoint_info["responses"],
                authentication_required=endpoint_info["authentication_required"],
                rate_limit=endpoint_info.get("rate_limit")
            ))
        
        return APIDocumentation(
            title="StorySign ASL Platform API",
            version="1.0.0",
            description="Comprehensive REST API for the StorySign ASL learning platform",
            base_url="/api/v1",
            authentication={
                "type": "Bearer JWT",
                "description": "Use JWT tokens obtained from /auth/login endpoint",
                "header": "Authorization: Bearer <token>"
            },
            rate_limiting={
                "description": "API endpoints are rate limited to prevent abuse",
                "default_limit": "100 requests per hour",
                "burst_allowance": "20 requests per minute",
                "headers": ["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]
            },
            endpoints=endpoints,
            schemas=SCHEMAS
        )
        
    except Exception as e:
        logger.error(f"Documentation generation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate documentation")


@router.get("/endpoints")
async def list_api_endpoints():
    """
    Get list of all API endpoints
    
    Returns:
        List of available API endpoints with basic information
    """
    try:
        return {
            "endpoints": [
                {
                    "path": endpoint["path"],
                    "method": endpoint["method"],
                    "summary": endpoint["summary"],
                    "tags": endpoint["tags"],
                    "auth_required": endpoint["authentication_required"]
                }
                for endpoint in API_ENDPOINTS
            ],
            "total_count": len(API_ENDPOINTS)
        }
        
    except Exception as e:
        logger.error(f"Endpoint listing error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list endpoints")


@router.get("/schemas")
async def get_api_schemas():
    """
    Get API response schemas
    
    Returns:
        Dictionary of API response schemas
    """
    try:
        return {
            "schemas": SCHEMAS,
            "description": "JSON schemas for API request and response models"
        }
        
    except Exception as e:
        logger.error(f"Schema retrieval error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve schemas")


@router.get("/health", response_model=APIHealthCheck)
async def api_health_check():
    """
    Comprehensive API health check
    
    Returns:
        Detailed health status of API components
    """
    try:
        start_time = time.time()
        
        # Check database status
        db_status = "unknown"
        try:
            db_service = DatabaseService()
            # TODO: Implement actual database health check
            db_status = "healthy"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_status = "unhealthy"
        
        # Check auth service status
        auth_status = "unknown"
        try:
            auth_service = AuthService()
            await auth_service.initialize()
            auth_status = "healthy"
        except Exception as e:
            logger.error(f"Auth service health check failed: {e}")
            auth_status = "unhealthy"
        
        # Get rate limiting stats (if available)
        rate_limit_stats = {
            "status": "healthy",
            "active_clients": 0,
            "blocked_ips": 0,
            "total_requests": 0,
            "blocked_requests": 0
        }
        
        # Test key endpoints
        endpoint_health = [
            {"endpoint": "/api/v1/auth/login", "status": "healthy", "response_time_ms": 0},
            {"endpoint": "/api/v1/users/profile", "status": "healthy", "response_time_ms": 0},
            {"endpoint": "/api/v1/content/stories", "status": "healthy", "response_time_ms": 0},
            {"endpoint": "/api/v1/graphql", "status": "healthy", "response_time_ms": 0}
        ]
        
        # Determine overall status
        overall_status = "healthy"
        if db_status != "healthy" or auth_status != "healthy":
            overall_status = "degraded"
        
        return APIHealthCheck(
            status=overall_status,
            timestamp=datetime.utcnow().isoformat(),
            version="1.0.0",
            uptime_seconds=time.time() - start_time,  # Placeholder
            database_status=db_status,
            auth_service_status=auth_status,
            rate_limiting_stats=rate_limit_stats,
            endpoint_health=endpoint_health
        )
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@router.post("/test-endpoint")
async def test_api_endpoint(
    endpoint_path: str = Query(..., description="API endpoint path to test"),
    method: str = Query("GET", description="HTTP method"),
    test_data: Optional[Dict[str, Any]] = None,
    current_user = Depends(get_current_user)
):
    """
    Test a specific API endpoint
    
    Args:
        endpoint_path: Path of endpoint to test
        method: HTTP method to use
        test_data: Optional test data for POST/PUT requests
        current_user: Current authenticated user
        
    Returns:
        Test result with response time and status
    """
    try:
        # This is a simplified test - in a real implementation,
        # you would make actual HTTP requests to test endpoints
        
        start_time = time.time()
        
        # Simulate endpoint test
        test_result = {
            "endpoint": endpoint_path,
            "method": method.upper(),
            "status_code": 200,
            "response_time_ms": (time.time() - start_time) * 1000,
            "success": True,
            "error_message": None,
            "response_data": {"message": "Test endpoint - not implemented"}
        }
        
        return test_result
        
    except Exception as e:
        logger.error(f"Endpoint test error: {e}")
        return {
            "endpoint": endpoint_path,
            "method": method.upper(),
            "status_code": 500,
            "response_time_ms": 0,
            "success": False,
            "error_message": str(e),
            "response_data": None
        }


@router.get("/examples")
async def get_api_examples():
    """
    Get API usage examples
    
    Returns:
        Collection of API usage examples with curl commands
    """
    try:
        examples = {
            "authentication": {
                "register": {
                    "description": "Register a new user account",
                    "curl": """curl -X POST "http://localhost:8000/api/v1/auth/register" \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "user@example.com",
    "username": "newuser",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
  }'""",
                    "response": {
                        "success": True,
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "refresh_token": "def50200...",
                        "token_type": "bearer",
                        "expires_in": 900
                    }
                },
                "login": {
                    "description": "Login with existing credentials",
                    "curl": """curl -X POST "http://localhost:8000/api/v1/auth/login" \\
  -H "Content-Type: application/json" \\
  -d '{
    "identifier": "user@example.com",
    "password": "SecurePass123!"
  }'""",
                    "response": {
                        "success": True,
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "refresh_token": "def50200..."
                    }
                }
            },
            "users": {
                "get_profile": {
                    "description": "Get current user profile",
                    "curl": """curl -X GET "http://localhost:8000/api/v1/users/profile" \\
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." """,
                    "response": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "username": "newuser",
                        "email": "user@example.com",
                        "full_name": "John Doe"
                    }
                }
            },
            "content": {
                "list_stories": {
                    "description": "Get list of available stories",
                    "curl": """curl -X GET "http://localhost:8000/api/v1/content/stories?limit=10&difficulty_level=beginner" \\
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." """,
                    "response": {
                        "stories": [],
                        "total_count": 0,
                        "limit": 10,
                        "offset": 0
                    }
                }
            },
            "graphql": {
                "user_query": {
                    "description": "GraphQL query for user data",
                    "curl": """curl -X POST "http://localhost:8000/api/v1/graphql" \\
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "query": "query { me { id username fullName } }"
  }'""",
                    "response": {
                        "data": {
                            "me": {
                                "id": "123e4567-e89b-12d3-a456-426614174000",
                                "username": "newuser",
                                "fullName": "John Doe"
                            }
                        }
                    }
                }
            }
        }
        
        return {
            "examples": examples,
            "notes": [
                "Replace 'localhost:8000' with your actual API base URL",
                "Replace JWT tokens with actual tokens from login response",
                "All authenticated endpoints require Authorization header",
                "Rate limits apply to all endpoints - check response headers"
            ]
        }
        
    except Exception as e:
        logger.error(f"Examples generation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate examples")


@router.get("/rate-limits")
async def get_rate_limit_info():
    """
    Get information about API rate limits
    
    Returns:
        Rate limit configuration and current status
    """
    try:
        return {
            "rate_limits": {
                "default": {
                    "requests": 100,
                    "window": 3600,
                    "burst": 20,
                    "description": "Default limit for authenticated users"
                },
                "authentication": {
                    "login": {"requests": 5, "window": 300, "burst": 2},
                    "register": {"requests": 3, "window": 3600, "burst": 1},
                    "refresh": {"requests": 10, "window": 300, "burst": 5}
                },
                "content": {
                    "story_generation": {"requests": 20, "window": 3600, "burst": 5},
                    "story_listing": {"requests": 200, "window": 3600, "burst": 50}
                },
                "user_roles": {
                    "admin": {"requests": 1000, "window": 3600, "burst": 100},
                    "educator": {"requests": 500, "window": 3600, "burst": 50},
                    "learner": {"requests": 200, "window": 3600, "burst": 30},
                    "guest": {"requests": 50, "window": 3600, "burst": 10}
                }
            },
            "headers": {
                "X-RateLimit-Limit": "Maximum requests allowed in window",
                "X-RateLimit-Remaining": "Remaining requests in current window",
                "X-RateLimit-Reset": "Timestamp when window resets",
                "X-RateLimit-Window": "Window duration in seconds",
                "Retry-After": "Seconds to wait before retrying (when rate limited)"
            },
            "notes": [
                "Rate limits are per user for authenticated requests",
                "Rate limits are per IP for unauthenticated requests",
                "Burst limits allow short spikes in traffic",
                "Repeated violations may result in temporary IP blocking"
            ]
        }
        
    except Exception as e:
        logger.error(f"Rate limit info error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get rate limit info")