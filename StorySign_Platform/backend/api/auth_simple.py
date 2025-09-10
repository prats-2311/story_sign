"""
Simple Authentication API endpoints for StorySign ASL Platform
Minimal implementation without database dependencies for testing
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, EmailStr
import logging
import jwt
import hashlib
import secrets

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

# In-memory user storage for testing (replace with database in production)
users_db = {}
sessions_db = {}

# JWT Configuration
JWT_SECRET = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

# Request/Response Models
class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, description="Password")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")

class LoginRequest(BaseModel):
    """User login request"""
    identifier: str = Field(..., description="Email or username")
    password: str = Field(..., description="Password")

class AuthResponse(BaseModel):
    """Authentication response"""
    success: bool
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 900  # 15 minutes
    user: Dict[str, Any]

class MessageResponse(BaseModel):
    """Generic message response"""
    success: bool
    message: str

# Helper functions
def hash_password(password: str) -> str:
    """Hash a password using SHA256 (simple implementation)"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return hash_password(password) == hashed

def create_access_token(data: dict) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def generate_user_id() -> str:
    """Generate a unique user ID"""
    return secrets.token_hex(16)

# API Endpoints
@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest, client_request: Request):
    """
    Register a new user account
    """
    try:
        logger.info(f"User registration attempt: {request.email}")
        
        # Check if user already exists
        for user_id, user_data in users_db.items():
            if user_data["email"] == request.email or user_data["username"] == request.username:
                raise HTTPException(status_code=400, detail="User already exists")
        
        # Create new user
        user_id = generate_user_id()
        user_data = {
            "id": user_id,
            "email": request.email,
            "username": request.username,
            "password_hash": hash_password(request.password),
            "first_name": request.first_name,
            "last_name": request.last_name,
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True
        }
        
        # Store user
        users_db[user_id] = user_data
        
        # Create access token
        token_data = {"sub": user_id, "email": request.email}
        access_token = create_access_token(token_data)
        
        # Prepare user response (without password)
        user_response = {k: v for k, v in user_data.items() if k != "password_hash"}
        
        logger.info(f"User registered successfully: {user_id}")
        
        return AuthResponse(
            success=True,
            access_token=access_token,
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, client_request: Request):
    """
    Authenticate user and create session
    """
    try:
        logger.info(f"Login attempt: {request.identifier}")
        
        # Find user by email or username
        user_data = None
        user_id = None
        for uid, data in users_db.items():
            if data["email"] == request.identifier or data["username"] == request.identifier:
                user_data = data
                user_id = uid
                break
        
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password
        if not verify_password(request.password, user_data["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if user is active
        if not user_data.get("is_active", True):
            raise HTTPException(status_code=401, detail="Account is disabled")
        
        # Create access token
        token_data = {"sub": user_id, "email": user_data["email"]}
        access_token = create_access_token(token_data)
        
        # Prepare user response (without password)
        user_response = {k: v for k, v in user_data.items() if k != "password_hash"}
        
        logger.info(f"User logged in successfully: {user_id}")
        
        return AuthResponse(
            success=True,
            access_token=access_token,
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")

@router.get("/me")
async def get_current_user_info():
    """
    Get current user information (placeholder)
    """
    return {
        "success": True,
        "message": "Authentication endpoint is working",
        "users_count": len(users_db)
    }

@router.get("/health")
async def auth_health():
    """
    Authentication service health check
    """
    return {
        "success": True,
        "service": "auth",
        "status": "healthy",
        "users_registered": len(users_db),
        "timestamp": datetime.utcnow().isoformat()
    }