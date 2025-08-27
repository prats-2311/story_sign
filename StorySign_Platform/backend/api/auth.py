"""
Authentication API endpoints for StorySign ASL Platform
"""

from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr, validator
import logging

# Import with error handling
try:
    from ..services.auth_service import AuthService
    AUTH_SERVICE_AVAILABLE = True
except ImportError:
    AUTH_SERVICE_AVAILABLE = False

try:
    from ..repositories.user_repository import UserRepository, UserSessionRepository
    USER_REPO_AVAILABLE = True
except ImportError:
    USER_REPO_AVAILABLE = False

try:
    from ..core.database_service import DatabaseService
    DB_SERVICE_AVAILABLE = True
except ImportError:
    DB_SERVICE_AVAILABLE = False

try:
    from ..models.user import User
    USER_MODEL_AVAILABLE = True
except ImportError:
    USER_MODEL_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
security = HTTPBearer()


# Request/Response Models
class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, description="Password")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    timezone: Optional[str] = Field("UTC", description="User timezone")
    language: Optional[str] = Field("en", description="Preferred language")
    learning_goals: Optional[list] = Field([], description="Learning goals")
    
    @validator('username')
    def validate_username(cls, v):
        if not v.isalnum() and '_' not in v and '-' not in v:
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v


class LoginRequest(BaseModel):
    """User login request"""
    identifier: str = Field(..., description="Email or username")
    password: str = Field(..., description="Password")


class RefreshTokenRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str = Field(..., description="Refresh token")


class ChangePasswordRequest(BaseModel):
    """Change password request"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")


class AuthResponse(BaseModel):
    """Authentication response"""
    success: bool
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes
    user: Dict[str, Any]


class TokenResponse(BaseModel):
    """Token refresh response"""
    success: bool
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900


class MessageResponse(BaseModel):
    """Generic message response"""
    success: bool
    message: str


# Dependency injection with error handling
async def get_auth_service():
    """Get authentication service instance"""
    if not AUTH_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Authentication service not available")
    
    config = {
        "jwt_secret": "your-jwt-secret-key-change-in-production",
        "jwt_algorithm": "HS256"
    }
    service = AuthService(config=config)
    await service.initialize()
    return service


async def get_user_repository():
    """Get user repository instance"""
    if not USER_REPO_AVAILABLE or not DB_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="User repository not available")
    
    db_service = DatabaseService()
    session = await db_service.get_session()
    return UserRepository(session)


async def get_session_repository():
    """Get session repository instance"""
    if not USER_REPO_AVAILABLE or not DB_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Session repository not available")
    
    db_service = DatabaseService()
    session = await db_service.get_session()
    return UserSessionRepository(session)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service = Depends(get_auth_service),
    session_repo = Depends(get_session_repository)
):
    """Get current authenticated user from JWT token"""
    try:
        # Verify JWT token
        payload = auth_service.verify_access_token(credentials.credentials)
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
        user_repo = await get_user_repository()
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
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=401,
            detail="Authentication failed"
        )


# API Endpoints

@router.post("/register", response_model=AuthResponse)
async def register(
    request: RegisterRequest,
    client_request: Request,
    auth_service = Depends(get_auth_service),
    user_repo = Depends(get_user_repository)
):
    """
    Register a new user account
    
    Args:
        request: Registration data
        client_request: FastAPI request object
        auth_service: Authentication service
        user_repo: User repository
        
    Returns:
        Authentication response with tokens and user data
    """
    try:
        logger.info(f"User registration attempt: {request.email}")
        
        # Prepare registration data
        registration_data = {
            "email": request.email,
            "username": request.username,
            "password": request.password,
            "first_name": request.first_name,
            "last_name": request.last_name,
            "timezone": request.timezone,
            "language": request.language,
            "learning_goals": request.learning_goals or []
        }
        
        # Register user
        user, access_token = await auth_service.register_user(
            user_repo, registration_data
        )
        
        # Create session for immediate login
        session_repo = await get_session_repository()
        user_agent = client_request.headers.get("user-agent")
        ip_address = client_request.client.host if client_request.client else None
        
        _, _, refresh_token = await auth_service.authenticate_user(
            user_repo, session_repo, request.email, request.password,
            user_agent, ip_address
        )
        
        logger.info(f"User registered successfully: {user.id}")
        
        return AuthResponse(
            success=True,
            access_token=access_token,
            refresh_token=refresh_token,
            user=user.to_dict()
        )
        
    except ValueError as e:
        logger.warning(f"Registration validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    client_request: Request,
    auth_service = Depends(get_auth_service),
    user_repo = Depends(get_user_repository),
    session_repo = Depends(get_session_repository)
):
    """
    Authenticate user and create session
    
    Args:
        request: Login credentials
        client_request: FastAPI request object
        auth_service: Authentication service
        user_repo: User repository
        session_repo: Session repository
        
    Returns:
        Authentication response with tokens and user data
    """
    try:
        logger.info(f"Login attempt: {request.identifier}")
        
        # Get client information
        user_agent = client_request.headers.get("user-agent")
        ip_address = client_request.client.host if client_request.client else None
        
        # Authenticate user
        user, access_token, refresh_token = await auth_service.authenticate_user(
            user_repo, session_repo, request.identifier, request.password,
            user_agent, ip_address
        )
        
        logger.info(f"User logged in successfully: {user.id}")
        
        return AuthResponse(
            success=True,
            access_token=access_token,
            refresh_token=refresh_token,
            user=user.to_dict()
        )
        
    except ValueError as e:
        logger.warning(f"Login failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service = Depends(get_auth_service),
    session_repo = Depends(get_session_repository)
):
    """
    Refresh access token using refresh token
    
    Args:
        request: Refresh token request
        auth_service: Authentication service
        session_repo: Session repository
        
    Returns:
        New access token
    """
    try:
        access_token = await auth_service.refresh_access_token(
            session_repo, request.refresh_token
        )
        
        if not access_token:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired refresh token"
            )
        
        return TokenResponse(
            success=True,
            access_token=access_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=500, detail="Token refresh failed")


@router.post("/logout", response_model=MessageResponse)
async def logout(
    authorization: str = Header(None),
    auth_service = Depends(get_auth_service),
    session_repo = Depends(get_session_repository)
):
    """
    Logout user by deactivating current session
    
    Args:
        authorization: Authorization header with session token
        auth_service: Authentication service
        session_repo: Session repository
        
    Returns:
        Logout confirmation
    """
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="No valid session token provided")
        
        session_token = authorization.split(" ")[1]
        success = await auth_service.logout_user(session_repo, session_token)
        
        if not success:
            raise HTTPException(status_code=401, detail="Invalid session token")
        
        return MessageResponse(
            success=True,
            message="Logged out successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all(
    current_user = Depends(get_current_user),
    auth_service = Depends(get_auth_service),
    session_repo = Depends(get_session_repository)
):
    """
    Logout user from all sessions
    
    Args:
        current_user: Current authenticated user
        auth_service: Authentication service
        session_repo: Session repository
        
    Returns:
        Logout confirmation with session count
    """
    try:
        count = await auth_service.logout_all_sessions(session_repo, current_user.id)
        
        return MessageResponse(
            success=True,
            message=f"Logged out from {count} sessions"
        )
        
    except Exception as e:
        logger.error(f"Logout all error: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user = Depends(get_current_user),
    auth_service = Depends(get_auth_service),
    user_repo = Depends(get_user_repository),
    session_repo = Depends(get_session_repository)
):
    """
    Change user password
    
    Args:
        request: Password change request
        current_user: Current authenticated user
        auth_service: Authentication service
        user_repo: User repository
        session_repo: Session repository
        
    Returns:
        Password change confirmation
    """
    try:
        success = await auth_service.change_password(
            user_repo, session_repo, current_user.id,
            request.current_password, request.new_password
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Password change failed")
        
        return MessageResponse(
            success=True,
            message="Password changed successfully. Please log in again."
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(status_code=500, detail="Password change failed")


@router.get("/me")
async def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """
    Get current user information
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User information
    """
    return {
        "success": True,
        "user": current_user.to_dict()
    }


@router.get("/sessions")
async def get_user_sessions(
    current_user = Depends(get_current_user),
    session_repo = Depends(get_session_repository)
):
    """
    Get user's active sessions
    
    Args:
        current_user: Current authenticated user
        session_repo: Session repository
        
    Returns:
        List of user sessions
    """
    try:
        sessions = await session_repo.get_user_sessions(current_user.id, active_only=True)
        
        return {
            "success": True,
            "sessions": [
                {
                    "id": session.id,
                    "created_at": session.created_at.isoformat(),
                    "expires_at": session.expires_at.isoformat(),
                    "user_agent": session.user_agent,
                    "ip_address": session.ip_address
                }
                for session in sessions
            ]
        }
        
    except Exception as e:
        logger.error(f"Get sessions error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sessions")


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user = Depends(get_current_user),
    session_repo = Depends(get_session_repository)
):
    """
    Revoke a specific session
    
    Args:
        session_id: Session ID to revoke
        current_user: Current authenticated user
        session_repo: Session repository
        
    Returns:
        Revocation confirmation
    """
    try:
        # Verify session belongs to current user
        session = await session_repo.get_by_id(session_id)
        if not session or session.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Session not found")
        
        success = await session_repo.deactivate_session(session_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to revoke session")
        
        return MessageResponse(
            success=True,
            message="Session revoked successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Revoke session error: {e}")
        raise HTTPException(status_code=500, detail="Failed to revoke session")