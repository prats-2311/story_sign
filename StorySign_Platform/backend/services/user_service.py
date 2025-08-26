"""
User service for managing user accounts and profiles
"""

from typing import Dict, Any, Optional, List, Tuple
import uuid
from datetime import datetime

from core.base_service import BaseService
from repositories.user_repository import UserRepository, UserSessionRepository
from services.auth_service import AuthService
from models.user import User, UserProfile


class UserService(BaseService):
    """
    Service for managing user accounts, profiles, and authentication
    """
    
    def __init__(self, service_name: str = "UserService", config: Optional[Dict[str, Any]] = None):
        super().__init__(service_name, config)
        self.database_service: Optional[Any] = None
        self.auth_service: Optional[AuthService] = None
        
    async def initialize(self) -> None:
        """
        Initialize user service
        """
        # Initialize auth service
        self.auth_service = AuthService("AuthService", self.config)
        await self.auth_service.initialize()
        
        self.logger.info("User service initialized")
    
    async def cleanup(self) -> None:
        """
        Clean up user service
        """
        if self.auth_service:
            await self.auth_service.cleanup()
        self.database_service = None
        
    async def _get_database_service(self) -> Any:
        """Get database service lazily"""
        if self.database_service is None:
            from core.service_container import get_service_container
            container = get_service_container()
            self.database_service = await container.get_service("DatabaseService")
        return self.database_service
    
    async def _get_repositories(self) -> Tuple[UserRepository, UserSessionRepository]:
        """Get repository instances"""
        db_service = await self._get_database_service()
        session = await db_service.get_session()
        
        user_repo = UserRepository(session)
        session_repo = UserSessionRepository(session)
        
        return user_repo, session_repo
    
    async def register_user(self, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new user account
        
        Args:
            registration_data: User registration data including password
            
        Returns:
            Created user information with access token
            
        Raises:
            ValueError: If registration fails
        """
        user_repo, _ = await self._get_repositories()
        
        try:
            user, access_token = await self.auth_service.register_user(user_repo, registration_data)
            
            result = user.to_dict()
            result["access_token"] = access_token
            
            self.logger.info(f"User registered successfully: {user.id}")
            return result
            
        except Exception as e:
            self.logger.error(f"User registration failed: {e}")
            raise
    
    async def authenticate_user(
        self, 
        identifier: str, 
        password: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Authenticate user credentials
        
        Args:
            identifier: Email or username
            password: User password
            user_agent: User agent string
            ip_address: Client IP address
            
        Returns:
            User data with tokens if authentication successful
            
        Raises:
            ValueError: If authentication fails
        """
        user_repo, session_repo = await self._get_repositories()
        
        try:
            user, access_token, refresh_token = await self.auth_service.authenticate_user(
                user_repo, session_repo, identifier, password, user_agent, ip_address
            )
            
            result = user.to_dict()
            result["access_token"] = access_token
            result["refresh_token"] = refresh_token
            
            self.logger.info(f"User authenticated successfully: {user.id}")
            return result
            
        except Exception as e:
            self.logger.error(f"User authentication failed: {e}")
            raise
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh access token
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New access token or None if refresh failed
        """
        _, session_repo = await self._get_repositories()
        
        access_token = await self.auth_service.refresh_access_token(session_repo, refresh_token)
        
        if access_token:
            return {"access_token": access_token}
        
        return None
    
    async def logout_user(self, session_token: str) -> bool:
        """
        Logout user by session token
        
        Args:
            session_token: Session token to deactivate
            
        Returns:
            True if logout successful
        """
        _, session_repo = await self._get_repositories()
        
        return await self.auth_service.logout_user(session_repo, session_token)
    
    async def logout_all_sessions(self, user_id: str) -> int:
        """
        Logout user from all sessions
        
        Args:
            user_id: User ID
            
        Returns:
            Number of sessions deactivated
        """
        _, session_repo = await self._get_repositories()
        
        return await self.auth_service.logout_all_sessions(session_repo, user_id)
    
    async def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate session token
        
        Args:
            session_token: Session token to validate
            
        Returns:
            User data if session is valid, None otherwise
        """
        _, session_repo = await self._get_repositories()
        
        user = await self.auth_service.validate_session(session_repo, session_token)
        
        if user:
            return user.to_dict()
        
        return None
    
    async def get_user_by_id(self, user_id: str, include_profile: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get user by ID
        
        Args:
            user_id: User ID
            include_profile: Whether to include profile data
            
        Returns:
            User data or None if not found
        """
        user_repo, _ = await self._get_repositories()
        
        if include_profile:
            user = await user_repo.get_by_id_with_profile(user_id)
        else:
            user = await user_repo.get_by_id(user_id)
        
        if user:
            result = user.to_dict()
            if include_profile and user.profile:
                result["profile"] = user.profile.to_dict()
            return result
        
        return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email address
        
        Args:
            email: User email address
            
        Returns:
            User data or None if not found
        """
        user_repo, _ = await self._get_repositories()
        
        user = await user_repo.get_by_email(email)
        
        if user:
            return user.to_dict()
        
        return None
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update user information
        
        Args:
            user_id: User ID
            update_data: Data to update
            
        Returns:
            Updated user data or None if not found
        """
        user_repo, _ = await self._get_repositories()
        
        # Remove sensitive fields that shouldn't be updated directly
        safe_update_data = {k: v for k, v in update_data.items() 
                           if k not in ['password_hash', 'id', 'created_at']}
        
        user = await user_repo.update_user(user_id, safe_update_data)
        
        if user:
            result = user.to_dict()
            if user.profile:
                result["profile"] = user.profile.to_dict()
            
            self.logger.info(f"User updated: {user_id}")
            return result
        
        return None
    
    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update user profile
        
        Args:
            user_id: User ID
            profile_data: Profile data to update
            
        Returns:
            Updated profile data or None if not found
        """
        user_repo, _ = await self._get_repositories()
        
        # Remove fields that shouldn't be updated directly
        safe_profile_data = {k: v for k, v in profile_data.items() 
                            if k not in ['id', 'user_id', 'created_at']}
        
        profile = await user_repo.update_user_profile(user_id, safe_profile_data)
        
        if profile:
            self.logger.info(f"User profile updated: {user_id}")
            return profile.to_dict()
        
        return None
    
    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """
        Change user password
        
        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password
            
        Returns:
            True if password changed successfully
            
        Raises:
            ValueError: If password change fails
        """
        user_repo, session_repo = await self._get_repositories()
        
        return await self.auth_service.change_password(
            user_repo, session_repo, user_id, current_password, new_password
        )
    
    async def deactivate_user(self, user_id: str) -> bool:
        """
        Deactivate user account
        
        Args:
            user_id: User ID
            
        Returns:
            True if user was deactivated
        """
        user_repo, session_repo = await self._get_repositories()
        
        # Deactivate user
        success = await user_repo.deactivate_user(user_id)
        
        if success:
            # Logout all sessions
            await session_repo.deactivate_user_sessions(user_id)
            self.logger.info(f"User deactivated: {user_id}")
        
        return success
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Permanently delete user account
        
        Args:
            user_id: User ID
            
        Returns:
            True if user was deleted
        """
        user_repo, _ = await self._get_repositories()
        
        success = await user_repo.delete_user(user_id)
        
        if success:
            self.logger.info(f"User deleted: {user_id}")
        
        return success
    
    async def search_users(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search users by name, username, or email
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching users
        """
        user_repo, _ = await self._get_repositories()
        
        users = await user_repo.search_users(query, limit)
        
        return [user.to_dict() for user in users]
    
    async def get_user_sessions(self, user_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get user sessions
        
        Args:
            user_id: User ID
            active_only: Whether to return only active sessions
            
        Returns:
            List of user sessions
        """
        _, session_repo = await self._get_repositories()
        
        sessions = await session_repo.get_user_sessions(user_id, active_only)
        
        return [session.to_dict() for session in sessions]
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions
        
        Returns:
            Number of sessions cleaned up
        """
        _, session_repo = await self._get_repositories()
        
        return await self.auth_service.cleanup_expired_sessions(session_repo)