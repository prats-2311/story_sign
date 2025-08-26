"""
Authentication service for user management and security
"""

import secrets
import hashlib
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import bcrypt

from core.base_service import BaseService
from repositories.user_repository import UserRepository, UserSessionRepository
from models.user import User, UserSession


class AuthService(BaseService):
    """
    Service for user authentication, password management, and session handling
    """
    
    def __init__(self, service_name: str = "AuthService", config: Optional[Dict[str, Any]] = None):
        super().__init__(service_name, config)
        self.jwt_secret = config.get("jwt_secret", "your-secret-key") if config else "your-secret-key"
        self.jwt_algorithm = "HS256"
        self.access_token_expire_minutes = 15
        self.refresh_token_expire_days = 7
        
    async def initialize(self) -> None:
        """Initialize authentication service"""
        self.logger.info("Authentication service initialized")
    
    async def cleanup(self) -> None:
        """Clean up authentication service"""
        pass
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            password: Plain text password
            hashed_password: Hashed password to verify against
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception as e:
            self.logger.error(f"Password verification error: {e}")
            return False
    
    def generate_session_token(self) -> str:
        """
        Generate a secure session token
        
        Returns:
            Random session token
        """
        return secrets.token_urlsafe(32)
    
    def generate_refresh_token(self) -> str:
        """
        Generate a secure refresh token
        
        Returns:
            Random refresh token
        """
        return secrets.token_urlsafe(32)
    
    def create_access_token(self, user_id: str, additional_claims: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a JWT access token
        
        Args:
            user_id: User ID to encode in token
            additional_claims: Additional claims to include
            
        Returns:
            JWT access token
        """
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT access token
        
        Args:
            token: JWT token to verify
            
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Check token type
            if payload.get("type") != "access":
                return None
                
            return payload
        except jwt.ExpiredSignatureError:
            self.logger.debug("Access token expired")
            return None
        except jwt.InvalidTokenError as e:
            self.logger.debug(f"Invalid access token: {e}")
            return None
    
    async def register_user(
        self, 
        user_repository: UserRepository,
        registration_data: Dict[str, Any]
    ) -> Tuple[User, str]:
        """
        Register a new user
        
        Args:
            user_repository: User repository instance
            registration_data: User registration data
            
        Returns:
            Tuple of (created user, access token)
            
        Raises:
            ValueError: If user already exists or validation fails
        """
        # Check if user already exists
        existing_user = await user_repository.get_by_email(registration_data["email"])
        if existing_user:
            raise ValueError("User with this email already exists")
        
        existing_username = await user_repository.get_by_username(registration_data["username"])
        if existing_username:
            raise ValueError("Username already taken")
        
        # Validate password strength
        self._validate_password(registration_data["password"])
        
        # Hash password
        password_hash = self.hash_password(registration_data["password"])
        
        # Prepare user data
        user_data = {
            "email": registration_data["email"],
            "username": registration_data["username"],
            "password_hash": password_hash,
            "first_name": registration_data.get("first_name"),
            "last_name": registration_data.get("last_name"),
            "preferences": registration_data.get("preferences", {}),
            "role": registration_data.get("role", "learner"),
            "timezone": registration_data.get("timezone", "UTC"),
            "language": registration_data.get("language", "en"),
            "learning_goals": registration_data.get("learning_goals", []),
            "accessibility_settings": registration_data.get("accessibility_settings", {})
        }
        
        # Create user
        user = await user_repository.create_user(user_data)
        
        # Create access token
        access_token = self.create_access_token(user.id, {"role": user.role})
        
        self.logger.info(f"User registered successfully: {user.id}")
        return user, access_token
    
    async def authenticate_user(
        self, 
        user_repository: UserRepository,
        session_repository: UserSessionRepository,
        identifier: str, 
        password: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[User, str, str]:
        """
        Authenticate user and create session
        
        Args:
            user_repository: User repository instance
            session_repository: Session repository instance
            identifier: Email or username
            password: Plain text password
            user_agent: User agent string
            ip_address: Client IP address
            
        Returns:
            Tuple of (user, access_token, refresh_token)
            
        Raises:
            ValueError: If authentication fails
        """
        # Get user by email or username
        user = await user_repository.get_by_email_or_username(identifier)
        if not user:
            raise ValueError("Invalid credentials")
        
        # Check if user is active
        if not user.is_active:
            raise ValueError("Account is deactivated")
        
        # Verify password
        if not self.verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")
        
        # Create session tokens
        session_token = self.generate_session_token()
        refresh_token = self.generate_refresh_token()
        expires_at = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        # Create session record
        session_data = {
            "session_token": session_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
            "user_agent": user_agent,
            "ip_address": ip_address
        }
        
        await session_repository.create_session(user.id, session_data)
        
        # Create access token
        access_token = self.create_access_token(user.id, {"role": user.role})
        
        self.logger.info(f"User authenticated successfully: {user.id}")
        return user, access_token, refresh_token
    
    async def refresh_access_token(
        self,
        session_repository: UserSessionRepository,
        refresh_token: str
    ) -> Optional[str]:
        """
        Refresh access token using refresh token
        
        Args:
            session_repository: Session repository instance
            refresh_token: Refresh token
            
        Returns:
            New access token or None if refresh token is invalid
        """
        # Get session by refresh token
        session = await session_repository.get_by_refresh_token(refresh_token)
        if not session or session.is_expired():
            return None
        
        # Create new access token
        access_token = self.create_access_token(session.user_id, {"role": session.user.role})
        
        self.logger.debug(f"Access token refreshed for user: {session.user_id}")
        return access_token
    
    async def logout_user(
        self,
        session_repository: UserSessionRepository,
        session_token: str
    ) -> bool:
        """
        Logout user by deactivating session
        
        Args:
            session_repository: Session repository instance
            session_token: Session token to deactivate
            
        Returns:
            True if logout successful, False otherwise
        """
        session = await session_repository.get_by_session_token(session_token)
        if not session:
            return False
        
        success = await session_repository.deactivate_session(session.id)
        
        if success:
            self.logger.info(f"User logged out: {session.user_id}")
        
        return success
    
    async def logout_all_sessions(
        self,
        session_repository: UserSessionRepository,
        user_id: str
    ) -> int:
        """
        Logout user from all sessions
        
        Args:
            session_repository: Session repository instance
            user_id: User ID
            
        Returns:
            Number of sessions deactivated
        """
        count = await session_repository.deactivate_user_sessions(user_id)
        
        self.logger.info(f"All sessions logged out for user {user_id}: {count} sessions")
        return count
    
    async def validate_session(
        self,
        session_repository: UserSessionRepository,
        session_token: str
    ) -> Optional[User]:
        """
        Validate session token and return user
        
        Args:
            session_repository: Session repository instance
            session_token: Session token to validate
            
        Returns:
            User instance if session is valid, None otherwise
        """
        session = await session_repository.get_by_session_token(session_token)
        if not session or session.is_expired():
            return None
        
        return session.user
    
    async def change_password(
        self,
        user_repository: UserRepository,
        session_repository: UserSessionRepository,
        user_id: str,
        current_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password
        
        Args:
            user_repository: User repository instance
            session_repository: Session repository instance
            user_id: User ID
            current_password: Current password
            new_password: New password
            
        Returns:
            True if password changed successfully, False otherwise
            
        Raises:
            ValueError: If current password is incorrect or new password is invalid
        """
        # Get user
        user = await user_repository.get_by_id(user_id)
        if not user:
            return False
        
        # Verify current password
        if not self.verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")
        
        # Validate new password
        self._validate_password(new_password)
        
        # Hash new password
        new_password_hash = self.hash_password(new_password)
        
        # Update user password
        success = await user_repository.update_user(user_id, {"password_hash": new_password_hash})
        
        if success:
            # Logout all sessions to force re-authentication
            await session_repository.deactivate_user_sessions(user_id)
            self.logger.info(f"Password changed for user: {user_id}")
        
        return success is not None
    
    def _validate_password(self, password: str) -> None:
        """
        Validate password strength
        
        Args:
            password: Password to validate
            
        Raises:
            ValueError: If password doesn't meet requirements
        """
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one digit")
        
        # Check for special characters
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            raise ValueError("Password must contain at least one special character")
    
    async def cleanup_expired_sessions(self, session_repository: UserSessionRepository) -> int:
        """
        Clean up expired sessions
        
        Args:
            session_repository: Session repository instance
            
        Returns:
            Number of sessions cleaned up
        """
        count = await session_repository.cleanup_expired_sessions()
        self.logger.info(f"Cleaned up {count} expired sessions")
        return count