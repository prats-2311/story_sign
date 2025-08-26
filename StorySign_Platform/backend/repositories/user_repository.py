"""
User repository for database operations
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.orm import selectinload

from models.user import User, UserProfile, UserSession
from .base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository for user-related database operations
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
    
    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """
        Create a new user with profile
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user instance
        """
        # Create user
        user = User(
            id=str(uuid.uuid4()),
            email=user_data["email"],
            username=user_data["username"],
            password_hash=user_data["password_hash"],
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            preferences=user_data.get("preferences", {}),
            role=user_data.get("role", "learner")
        )
        
        self.session.add(user)
        await self.session.flush()  # Get the user ID
        
        # Create user profile
        profile = UserProfile(
            id=str(uuid.uuid4()),
            user_id=user.id,
            timezone=user_data.get("timezone", "UTC"),
            language=user_data.get("language", "en"),
            learning_goals=user_data.get("learning_goals", []),
            accessibility_settings=user_data.get("accessibility_settings", {})
        )
        
        self.session.add(profile)
        await self.session.commit()
        
        # Reload with relationships
        return await self.get_by_id_with_profile(user.id)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address
        
        Args:
            email: User email address
            
        Returns:
            User instance or None if not found
        """
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username
        
        Args:
            username: Username
            
        Returns:
            User instance or None if not found
        """
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_email_or_username(self, identifier: str) -> Optional[User]:
        """
        Get user by email or username
        
        Args:
            identifier: Email or username
            
        Returns:
            User instance or None if not found
        """
        stmt = select(User).where(
            or_(User.email == identifier, User.username == identifier)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_id_with_profile(self, user_id: str) -> Optional[User]:
        """
        Get user by ID with profile loaded
        
        Args:
            user_id: User ID
            
        Returns:
            User instance with profile or None if not found
        """
        stmt = select(User).options(selectinload(User.profile)).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Optional[User]:
        """
        Update user information
        
        Args:
            user_id: User ID
            update_data: Data to update
            
        Returns:
            Updated user instance or None if not found
        """
        # Update user
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(**update_data)
            .returning(User.id)
        )
        result = await self.session.execute(stmt)
        
        if result.rowcount == 0:
            return None
            
        await self.session.commit()
        return await self.get_by_id_with_profile(user_id)
    
    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Optional[UserProfile]:
        """
        Update user profile
        
        Args:
            user_id: User ID
            profile_data: Profile data to update
            
        Returns:
            Updated profile instance or None if not found
        """
        stmt = (
            update(UserProfile)
            .where(UserProfile.user_id == user_id)
            .values(**profile_data)
            .returning(UserProfile.id)
        )
        result = await self.session.execute(stmt)
        
        if result.rowcount == 0:
            return None
            
        await self.session.commit()
        
        # Return updated profile
        profile_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        profile_result = await self.session.execute(profile_stmt)
        return profile_result.scalar_one_or_none()
    
    async def deactivate_user(self, user_id: str) -> bool:
        """
        Deactivate user account
        
        Args:
            user_id: User ID
            
        Returns:
            True if user was deactivated, False if not found
        """
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(is_active=False)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Permanently delete user and all related data
        
        Args:
            user_id: User ID
            
        Returns:
            True if user was deleted, False if not found
        """
        # Delete user (cascade will handle profile and sessions)
        stmt = delete(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0
    
    async def get_active_users(self, limit: int = 50, offset: int = 0) -> List[User]:
        """
        Get list of active users
        
        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip
            
        Returns:
            List of active users
        """
        stmt = (
            select(User)
            .where(User.is_active == True)
            .options(selectinload(User.profile))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def search_users(self, query: str, limit: int = 20) -> List[User]:
        """
        Search users by name, username, or email
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching users
        """
        search_pattern = f"%{query}%"
        stmt = (
            select(User)
            .where(
                and_(
                    User.is_active == True,
                    or_(
                        User.first_name.ilike(search_pattern),
                        User.last_name.ilike(search_pattern),
                        User.username.ilike(search_pattern),
                        User.email.ilike(search_pattern)
                    )
                )
            )
            .options(selectinload(User.profile))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class UserSessionRepository(BaseRepository[UserSession]):
    """
    Repository for user session management
    """
    
    def __init__(self, session: AsyncSession):
        super().__init__(UserSession, session)
    
    async def create_session(self, user_id: str, session_data: Dict[str, Any]) -> UserSession:
        """
        Create a new user session
        
        Args:
            user_id: User ID
            session_data: Session creation data
            
        Returns:
            Created session instance
        """
        session = UserSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            session_token=session_data["session_token"],
            refresh_token=session_data["refresh_token"],
            expires_at=session_data["expires_at"],
            user_agent=session_data.get("user_agent"),
            ip_address=session_data.get("ip_address")
        )
        
        self.session.add(session)
        await self.session.commit()
        return session
    
    async def get_by_session_token(self, session_token: str) -> Optional[UserSession]:
        """
        Get session by session token
        
        Args:
            session_token: Session token
            
        Returns:
            Session instance or None if not found
        """
        stmt = (
            select(UserSession)
            .options(selectinload(UserSession.user))
            .where(
                and_(
                    UserSession.session_token == session_token,
                    UserSession.is_active == True
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_refresh_token(self, refresh_token: str) -> Optional[UserSession]:
        """
        Get session by refresh token
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            Session instance or None if not found
        """
        stmt = (
            select(UserSession)
            .options(selectinload(UserSession.user))
            .where(
                and_(
                    UserSession.refresh_token == refresh_token,
                    UserSession.is_active == True
                )
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_session(self, session_id: str, update_data: Dict[str, Any]) -> Optional[UserSession]:
        """
        Update session information
        
        Args:
            session_id: Session ID
            update_data: Data to update
            
        Returns:
            Updated session instance or None if not found
        """
        stmt = (
            update(UserSession)
            .where(UserSession.id == session_id)
            .values(**update_data)
            .returning(UserSession.id)
        )
        result = await self.session.execute(stmt)
        
        if result.rowcount == 0:
            return None
            
        await self.session.commit()
        return await self.get_by_id(session_id)
    
    async def deactivate_session(self, session_id: str) -> bool:
        """
        Deactivate a session
        
        Args:
            session_id: Session ID
            
        Returns:
            True if session was deactivated, False if not found
        """
        stmt = (
            update(UserSession)
            .where(UserSession.id == session_id)
            .values(is_active=False)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0
    
    async def deactivate_user_sessions(self, user_id: str) -> int:
        """
        Deactivate all sessions for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Number of sessions deactivated
        """
        stmt = (
            update(UserSession)
            .where(UserSession.user_id == user_id)
            .values(is_active=False)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions
        
        Returns:
            Number of sessions cleaned up
        """
        current_time = datetime.utcnow()
        stmt = delete(UserSession).where(UserSession.expires_at < current_time)
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount
    
    async def get_user_sessions(self, user_id: str, active_only: bool = True) -> List[UserSession]:
        """
        Get all sessions for a user
        
        Args:
            user_id: User ID
            active_only: Whether to return only active sessions
            
        Returns:
            List of user sessions
        """
        conditions = [UserSession.user_id == user_id]
        if active_only:
            conditions.append(UserSession.is_active == True)
            
        stmt = select(UserSession).where(and_(*conditions))
        result = await self.session.execute(stmt)
        return result.scalars().all()