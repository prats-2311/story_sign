"""
Database-backed Authentication API endpoints for StorySign ASL Platform
Uses TiDB cloud database for persistent user storage
"""

import uuid
import hashlib
import jwt
import secrets
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, EmailStr
import logging

# Database imports
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text, select
from config import get_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

# JWT Configuration
JWT_SECRET = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

# Database engine (will be initialized on first use)
_engine = None

async def get_engine():
    """Get or create database engine"""
    global _engine
    if _engine is None:
        config = get_config()
        db_config = config.database
        _engine = create_async_engine(
            db_config.get_connection_url(async_driver=True),
            echo=False,
            connect_args=db_config.get_connect_args()
        )
    return _engine

async def get_db_session():
    """Get database session"""
    engine = await get_engine()
    async with AsyncSession(engine) as session:
        yield session

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
    return str(uuid.uuid4())

# Database operations
async def create_user_in_db(session: AsyncSession, user_data: dict) -> dict:
    """Create a new user in the database"""
    user_id = generate_user_id()
    
    # Insert user
    insert_user_query = text("""
        INSERT INTO users (id, email, username, password_hash, first_name, last_name, is_active, is_verified)
        VALUES (:id, :email, :username, :password_hash, :first_name, :last_name, :is_active, :is_verified)
    """)
    
    await session.execute(insert_user_query, {
        "id": user_id,
        "email": user_data["email"],
        "username": user_data["username"],
        "password_hash": user_data["password_hash"],
        "first_name": user_data.get("first_name"),
        "last_name": user_data.get("last_name"),
        "is_active": True,
        "is_verified": True  # Auto-verify for now
    })
    
    # Create user profile
    profile_id = generate_user_id()
    insert_profile_query = text("""
        INSERT INTO user_profiles (id, user_id, language, skill_level)
        VALUES (:id, :user_id, :language, :skill_level)
    """)
    
    await session.execute(insert_profile_query, {
        "id": profile_id,
        "user_id": user_id,
        "language": "en",
        "skill_level": "beginner"
    })
    
    await session.commit()
    
    return {
        "id": user_id,
        "email": user_data["email"],
        "username": user_data["username"],
        "first_name": user_data.get("first_name"),
        "last_name": user_data.get("last_name"),
        "is_active": True,
        "is_verified": True,
        "created_at": datetime.utcnow().isoformat()
    }

async def find_user_by_identifier(session: AsyncSession, identifier: str) -> Optional[dict]:
    """Find user by email or username"""
    query = text("""
        SELECT id, email, username, password_hash, first_name, last_name, is_active, is_verified, created_at
        FROM users 
        WHERE (email = :identifier OR username = :identifier) AND is_active = 1
    """)
    
    result = await session.execute(query, {"identifier": identifier})
    row = result.fetchone()
    
    if row:
        return {
            "id": row[0],
            "email": row[1],
            "username": row[2],
            "password_hash": row[3],
            "first_name": row[4],
            "last_name": row[5],
            "is_active": bool(row[6]),
            "is_verified": bool(row[7]),
            "created_at": row[8].isoformat() if row[8] else None
        }
    return None

async def check_user_exists(session: AsyncSession, email: str, username: str) -> bool:
    """Check if user with email or username already exists"""
    query = text("""
        SELECT COUNT(*) FROM users 
        WHERE email = :email OR username = :username
    """)
    
    result = await session.execute(query, {"email": email, "username": username})
    count = result.scalar()
    return count > 0

# API Endpoints
@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest, client_request: Request):
    """
    Register a new user account
    """
    try:
        logger.info(f"User registration attempt: {request.email}")
        
        async with AsyncSession(await get_engine()) as session:
            # Check if user already exists
            if await check_user_exists(session, request.email, request.username):
                raise HTTPException(status_code=400, detail="User already exists")
            
            # Create new user
            user_data = {
                "email": request.email,
                "username": request.username,
                "password_hash": hash_password(request.password),
                "first_name": request.first_name,
                "last_name": request.last_name
            }
            
            user = await create_user_in_db(session, user_data)
            
            # Create access token
            token_data = {"sub": user["id"], "email": user["email"]}
            access_token = create_access_token(token_data)
            
            # Prepare user response (without password)
            user_response = {k: v for k, v in user.items() if k != "password_hash"}
            
            logger.info(f"User registered successfully: {user['id']}")
            
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
        
        async with AsyncSession(await get_engine()) as session:
            # Find user by email or username
            user = await find_user_by_identifier(session, request.identifier)
            
            if not user:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            # Verify password
            if not verify_password(request.password, user["password_hash"]):
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            # Check if user is active
            if not user.get("is_active", True):
                raise HTTPException(status_code=401, detail="Account is disabled")
            
            # Update last login
            update_login_query = text("""
                UPDATE users 
                SET last_login = CURRENT_TIMESTAMP(6), login_count = login_count + 1
                WHERE id = :user_id
            """)
            await session.execute(update_login_query, {"user_id": user["id"]})
            await session.commit()
            
            # Create access token
            token_data = {"sub": user["id"], "email": user["email"]}
            access_token = create_access_token(token_data)
            
            # Prepare user response (without password)
            user_response = {k: v for k, v in user.items() if k != "password_hash"}
            
            logger.info(f"User logged in successfully: {user['id']}")
            
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

@router.post("/logout", response_model=MessageResponse)
async def logout(client_request: Request):
    """
    Logout user (client-side token invalidation)
    
    Since we're using stateless JWT tokens, logout is primarily handled on the client side
    by removing the token. This endpoint provides a confirmation response.
    """
    try:
        logger.info("User logout request received")
        
        # In a stateless JWT system, we don't need to do anything server-side
        # The client will remove the token from storage
        # For enhanced security, you could implement a token blacklist here
        
        return MessageResponse(
            success=True,
            message="Logout successful. Token should be removed from client storage."
        )
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")

@router.get("/me")
async def get_current_user_info():
    """
    Get current user information
    """
    try:
        async with AsyncSession(await get_engine()) as session:
            # Get user count
            count_query = text("SELECT COUNT(*) FROM users WHERE is_active = 1")
            result = await session.execute(count_query)
            user_count = result.scalar()
            
            return {
                "success": True,
                "message": "Database authentication endpoint is working",
                "users_count": user_count,
                "storage": "TiDB Cloud Database"
            }
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        return {
            "success": False,
            "message": "Database connection error",
            "users_count": 0,
            "storage": "TiDB Cloud Database (Error)"
        }

@router.get("/health")
async def auth_health():
    """
    Authentication service health check
    """
    try:
        async with AsyncSession(await get_engine()) as session:
            # Test database connection
            test_query = text("SELECT 1")
            await session.execute(test_query)
            
            # Get user count
            count_query = text("SELECT COUNT(*) FROM users WHERE is_active = 1")
            result = await session.execute(count_query)
            user_count = result.scalar()
            
            return {
                "success": True,
                "service": "auth_db",
                "status": "healthy",
                "users_registered": user_count,
                "storage": "TiDB Cloud Database",
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "success": False,
            "service": "auth_db",
            "status": "unhealthy",
            "error": str(e),
            "storage": "TiDB Cloud Database",
            "timestamp": datetime.utcnow().isoformat()
        }