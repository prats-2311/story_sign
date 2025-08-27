"""
Authentication middleware for API requests
"""

import logging
from typing import Optional, Callable
from fastapi import Request, Response, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time

from ..services.auth_service import AuthService
from ..repositories.user_repository import UserRepository, UserSessionRepository
from ..core.database_service import DatabaseService

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling API authentication
    """
    
    def __init__(self, app, excluded_paths: Optional[list] = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/health",
            "/metrics"
        ]
        self.auth_service = None
        self.security = HTTPBearer(auto_error=False)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request through authentication middleware
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
            
        Returns:
            Response from next handler or authentication error
        """
        start_time = time.time()
        
        try:
            # Skip authentication for excluded paths
            if self._is_excluded_path(request.url.path):
                response = await call_next(request)
                return response
            
            # Skip authentication for OPTIONS requests (CORS preflight)
            if request.method == "OPTIONS":
                response = await call_next(request)
                return response
            
            # Initialize auth service if needed
            if not self.auth_service:
                await self._initialize_auth_service()
            
            # Initialize security services
            threat_service = await self._get_threat_detection_service()
            audit_service = await self._get_audit_service()
            
            # Analyze request for threats
            if threat_service:
                request_data = {
                    "ip_address": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent", ""),
                    "path": request.url.path,
                    "method": request.method,
                    "params": dict(request.query_params),
                    "headers": dict(request.headers)
                }
                
                threat_analysis = await threat_service.analyze_request(request_data)
                
                if threat_analysis.get("blocked", False):
                    # Log blocked request
                    if audit_service:
                        await audit_service.log_security_event(
                            event_type="THREAT_DETECTED",
                            severity="CRITICAL",
                            message=f"Request blocked due to threats: {threat_analysis.get('threats', [])}",
                            ip_address=request_data["ip_address"],
                            threat_details=threat_analysis
                        )
                    
                    return JSONResponse(
                        status_code=403,
                        content={
                            "error": "request_blocked",
                            "message": "Request blocked due to security threats",
                            "timestamp": time.time()
                        }
                    )
            
            # Extract and validate token
            user = await self._authenticate_request(request)
            
            # Add user to request state
            request.state.current_user = user
            
            # Log successful authentication
            if audit_service and user:
                await audit_service.log_authentication_event(
                    event_type="ACCESS_GRANTED",
                    user_identifier=user.email,
                    success=True,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    details={"path": request.url.path, "method": request.method}
                )
            
            # Process request
            response = await call_next(request)
            
            # Add authentication headers
            response.headers["X-Auth-Status"] = "authenticated"
            response.headers["X-User-ID"] = user.id if user else "anonymous"
            
            return response
            
        except HTTPException as e:
            # Log failed authentication
            if hasattr(self, '_audit_service') and self._audit_service:
                await self._audit_service.log_authentication_event(
                    event_type="ACCESS_DENIED",
                    user_identifier="unknown",
                    success=False,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    details={"error": e.detail, "path": request.url.path}
                )
            
            # Return authentication error
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": "authentication_failed",
                    "message": e.detail,
                    "timestamp": time.time()
                }
            )
        except Exception as e:
            logger.error(f"Authentication middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "authentication_error",
                    "message": "Internal authentication error",
                    "timestamp": time.time()
                }
            )
        finally:
            # Log request processing time
            processing_time = time.time() - start_time
            logger.debug(f"Auth middleware processed {request.url.path} in {processing_time:.3f}s")
    
    def _is_excluded_path(self, path: str) -> bool:
        """
        Check if path is excluded from authentication
        
        Args:
            path: Request path
            
        Returns:
            True if path is excluded, False otherwise
        """
        for excluded_path in self.excluded_paths:
            if path.startswith(excluded_path):
                return True
        return False
    
    async def _initialize_auth_service(self):
        """Initialize authentication service"""
        try:
            config = {
                "jwt_secret": "your-jwt-secret-key-change-in-production",
                "jwt_algorithm": "HS256"
            }
            self.auth_service = AuthService(config=config)
            await self.auth_service.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize auth service: {e}")
            raise HTTPException(status_code=500, detail="Authentication service unavailable")
    
    async def _authenticate_request(self, request: Request) -> Optional[object]:
        """
        Authenticate request and return user
        
        Args:
            request: FastAPI request
            
        Returns:
            User object if authenticated, None otherwise
            
        Raises:
            HTTPException: If authentication fails
        """
        try:
            # Extract authorization header
            authorization = request.headers.get("Authorization")
            if not authorization:
                raise HTTPException(
                    status_code=401,
                    detail="Authorization header required"
                )
            
            # Parse Bearer token
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid authorization header format"
                )
            
            token = authorization.split(" ")[1]
            
            # Verify JWT token
            payload = self.auth_service.verify_access_token(token)
            if not payload:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid or expired token"
                )
            
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token payload"
                )
            
            # Get user from database
            db_service = DatabaseService()
            session = await db_service.get_session()
            user_repo = UserRepository(session)
            
            user = await user_repo.get_by_id_with_profile(user_id)
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=401,
                    detail="User not found or inactive"
                )
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Request authentication error: {e}")
            raise HTTPException(
                status_code=401,
                detail="Authentication failed"
            )


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API key authentication (for external integrations)
    """
    
    def __init__(self, app, api_keys: Optional[dict] = None):
        super().__init__(app)
        self.api_keys = api_keys or {}  # {api_key: {"name": "service_name", "permissions": []}}
        self.api_key_paths = [
            "/api/v1/external/",
            "/api/v1/webhooks/",
            "/api/v1/integrations/"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request through API key middleware
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
            
        Returns:
            Response from next handler or authentication error
        """
        try:
            # Check if path requires API key authentication
            if not self._requires_api_key(request.url.path):
                response = await call_next(request)
                return response
            
            # Extract and validate API key
            api_key_info = await self._authenticate_api_key(request)
            
            # Add API key info to request state
            request.state.api_key_info = api_key_info
            
            # Process request
            response = await call_next(request)
            
            # Add API key headers
            response.headers["X-API-Auth"] = "api-key"
            response.headers["X-API-Client"] = api_key_info.get("name", "unknown")
            
            return response
            
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": "api_key_authentication_failed",
                    "message": e.detail,
                    "timestamp": time.time()
                }
            )
        except Exception as e:
            logger.error(f"API key middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "api_key_error",
                    "message": "Internal API key authentication error",
                    "timestamp": time.time()
                }
            )
    
    def _requires_api_key(self, path: str) -> bool:
        """
        Check if path requires API key authentication
        
        Args:
            path: Request path
            
        Returns:
            True if API key is required, False otherwise
        """
        for api_path in self.api_key_paths:
            if path.startswith(api_path):
                return True
        return False
    
    async def _authenticate_api_key(self, request: Request) -> dict:
        """
        Authenticate API key and return key info
        
        Args:
            request: FastAPI request
            
        Returns:
            API key information
            
        Raises:
            HTTPException: If API key authentication fails
        """
        try:
            # Extract API key from header or query parameter
            api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
            
            if not api_key:
                raise HTTPException(
                    status_code=401,
                    detail="API key required"
                )
            
            # Validate API key
            api_key_info = self.api_keys.get(api_key)
            if not api_key_info:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid API key"
                )
            
            return api_key_info
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"API key authentication error: {e}")
            raise HTTPException(
                status_code=401,
                detail="API key authentication failed"
            )


class CORSMiddleware(BaseHTTPMiddleware):
    """
    Custom CORS middleware with authentication awareness
    """
    
    def __init__(self, app, allowed_origins: Optional[list] = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["*"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request through CORS middleware
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
            
        Returns:
            Response with CORS headers
        """
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
            self._add_cors_headers(response, request)
            return response
        
        # Process request
        response = await call_next(request)
        
        # Add CORS headers
        self._add_cors_headers(response, request)
        
        return response
    
    def _add_cors_headers(self, response: Response, request: Request):
        """
        Add CORS headers to response
        
        Args:
            response: Response object
            request: Request object
        """
        origin = request.headers.get("Origin")
        
        # Check if origin is allowed
        if origin and (origin in self.allowed_origins or "*" in self.allowed_origins):
            response.headers["Access-Control-Allow-Origin"] = origin
        elif "*" in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = "*"
        
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = (
            "Authorization, Content-Type, X-API-Key, X-Requested-With, Accept, Origin"
        )
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Max-Age"] = "86400"  # 24 hours
    
    async def _get_threat_detection_service(self):
        """Get threat detection service instance"""
        if not hasattr(self, '_threat_service'):
            try:
                from ..services.threat_detection_service import ThreatDetectionService
                self._threat_service = ThreatDetectionService()
                await self._threat_service.initialize()
            except ImportError:
                self._threat_service = None
        return self._threat_service
    
    async def _get_audit_service(self):
        """Get audit service instance"""
        if not hasattr(self, '_audit_service'):
            try:
                from ..services.security_audit_service import SecurityAuditService
                config = {"audit_log_path": "logs/security_audit.log"}
                self._audit_service = SecurityAuditService(config=config)
                await self._audit_service.initialize()
            except ImportError:
                self._audit_service = None
        return self._audit_service