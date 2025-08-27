"""
User management API endpoints for StorySign ASL Platform
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from pydantic import BaseModel, Field, EmailStr, validator
import logging

from ..services.user_service import UserService
from ..repositories.user_repository import UserRepository
from ..repositories.progress_repository import ProgressRepository
from ..core.database_service import DatabaseService
from ..models.user import User
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


# Request/Response Models
class UserProfileUpdateRequest(BaseModel):
    """User profile update request"""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=1000)
    avatar_url: Optional[str] = Field(None, max_length=500)
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)
    learning_goals: Optional[List[str]] = None
    accessibility_settings: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None


class UserSearchRequest(BaseModel):
    """User search request"""
    query: Optional[str] = Field(None, description="Search query")
    role: Optional[str] = Field(None, description="Filter by role")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    language: Optional[str] = Field(None, description="Filter by language")
    limit: int = Field(20, ge=1, le=100, description="Maximum results")
    offset: int = Field(0, ge=0, description="Results offset")


class UserResponse(BaseModel):
    """User response model"""
    id: str
    email: str
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: str
    is_active: bool
    role: str
    created_at: str
    profile: Optional[Dict[str, Any]] = None


class UserListResponse(BaseModel):
    """User list response"""
    users: List[UserResponse]
    total_count: int
    limit: int
    offset: int
    has_more: bool


class UserProgressResponse(BaseModel):
    """User progress response"""
    user_id: str
    total_sessions: int
    total_practice_time: int
    stories_completed: int
    average_score: float
    skill_levels: Dict[str, Any]
    recent_activity: List[Dict[str, Any]]
    achievements: List[Dict[str, Any]]


class UserAnalyticsResponse(BaseModel):
    """User analytics response"""
    user_id: str
    learning_streak: int
    practice_frequency: Dict[str, int]
    improvement_trends: Dict[str, Any]
    skill_progression: Dict[str, Any]
    engagement_metrics: Dict[str, Any]


# Dependency injection
async def get_user_service() -> UserService:
    """Get user service instance"""
    # TODO: Implement proper dependency injection
    db_service = DatabaseService()
    return UserService(db_service)


async def get_user_repository() -> UserRepository:
    """Get user repository instance"""
    db_service = DatabaseService()
    session = await db_service.get_session()
    return UserRepository(session)


async def get_progress_repository() -> ProgressRepository:
    """Get progress repository instance"""
    db_service = DatabaseService()
    session = await db_service.get_session()
    return ProgressRepository(session)


# API Endpoints

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's profile
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User profile information
    """
    try:
        profile_data = None
        if current_user.profile:
            profile_data = current_user.profile.to_dict()
        
        return UserResponse(
            id=current_user.id,
            email=current_user.email,
            username=current_user.username,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            full_name=current_user.get_full_name(),
            is_active=current_user.is_active,
            role=getattr(current_user, 'role', 'learner'),
            created_at=current_user.created_at.isoformat(),
            profile=profile_data
        )
        
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve profile")


@router.put("/profile")
async def update_user_profile(
    request: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Update current user's profile
    
    Args:
        request: Profile update data
        current_user: Current authenticated user
        user_repo: User repository
        
    Returns:
        Update confirmation
    """
    try:
        # Separate user and profile updates
        user_updates = {}
        profile_updates = {}
        
        # User table updates
        if request.first_name is not None:
            user_updates["first_name"] = request.first_name
        if request.last_name is not None:
            user_updates["last_name"] = request.last_name
        if request.preferences is not None:
            user_updates["preferences"] = request.preferences
        
        # Profile table updates
        if request.bio is not None:
            profile_updates["bio"] = request.bio
        if request.avatar_url is not None:
            profile_updates["avatar_url"] = request.avatar_url
        if request.timezone is not None:
            profile_updates["timezone"] = request.timezone
        if request.language is not None:
            profile_updates["language"] = request.language
        if request.learning_goals is not None:
            profile_updates["learning_goals"] = request.learning_goals
        if request.accessibility_settings is not None:
            profile_updates["accessibility_settings"] = request.accessibility_settings
        
        # Update user if there are user updates
        if user_updates:
            await user_repo.update_user(current_user.id, user_updates)
        
        # Update profile if there are profile updates
        if profile_updates:
            await user_repo.update_user_profile(current_user.id, profile_updates)
        
        logger.info(f"Profile updated for user: {current_user.id}")
        
        return {
            "success": True,
            "message": "Profile updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update profile")


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str = Path(..., description="User ID"),
    current_user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Get user by ID (public profile information only)
    
    Args:
        user_id: User ID to retrieve
        current_user: Current authenticated user
        user_repo: User repository
        
    Returns:
        User profile information
    """
    try:
        user = await user_repo.get_by_id_with_profile(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Return limited public information
        profile_data = None
        if user.profile:
            # Only include public profile fields
            profile_data = {
                "bio": user.profile.bio,
                "avatar_url": user.profile.avatar_url,
                "language": user.profile.language,
                "timezone": user.profile.timezone
            }
        
        return UserResponse(
            id=user.id,
            email=user.email if user.id == current_user.id else "",  # Hide email for other users
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.get_full_name(),
            is_active=user.is_active,
            role=getattr(user, 'role', 'learner'),
            created_at=user.created_at.isoformat(),
            profile=profile_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user")


@router.post("/search", response_model=UserListResponse)
async def search_users(
    request: UserSearchRequest,
    current_user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Search users with filtering
    
    Args:
        request: Search parameters
        current_user: Current authenticated user
        user_repo: User repository
        
    Returns:
        List of matching users
    """
    try:
        if request.query:
            users = await user_repo.search_users(request.query, request.limit)
            total_count = len(users)  # For search, we don't have total count
        else:
            users = await user_repo.get_active_users(request.limit, request.offset)
            # TODO: Implement total count query
            total_count = len(users)
        
        # Convert to response format
        user_responses = []
        for user in users:
            profile_data = None
            if user.profile:
                profile_data = {
                    "bio": user.profile.bio,
                    "avatar_url": user.profile.avatar_url,
                    "language": user.profile.language
                }
            
            user_responses.append(UserResponse(
                id=user.id,
                email="",  # Don't expose emails in search
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                full_name=user.get_full_name(),
                is_active=user.is_active,
                role=getattr(user, 'role', 'learner'),
                created_at=user.created_at.isoformat(),
                profile=profile_data
            ))
        
        return UserListResponse(
            users=user_responses,
            total_count=total_count,
            limit=request.limit,
            offset=request.offset,
            has_more=(request.offset + request.limit) < total_count
        )
        
    except Exception as e:
        logger.error(f"User search error: {e}")
        raise HTTPException(status_code=500, detail="User search failed")


@router.get("/progress/summary", response_model=UserProgressResponse)
async def get_user_progress_summary(
    current_user: User = Depends(get_current_user),
    progress_repo: ProgressRepository = Depends(get_progress_repository)
):
    """
    Get current user's learning progress summary
    
    Args:
        current_user: Current authenticated user
        progress_repo: Progress repository
        
    Returns:
        User progress summary
    """
    try:
        # Get user progress data
        progress_data = await progress_repo.get_user_progress_summary(current_user.id)
        
        return UserProgressResponse(
            user_id=current_user.id,
            total_sessions=progress_data.get("total_sessions", 0),
            total_practice_time=progress_data.get("total_practice_time", 0),
            stories_completed=progress_data.get("stories_completed", 0),
            average_score=progress_data.get("average_score", 0.0),
            skill_levels=progress_data.get("skill_levels", {}),
            recent_activity=progress_data.get("recent_activity", []),
            achievements=progress_data.get("achievements", [])
        )
        
    except Exception as e:
        logger.error(f"Get progress error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve progress")


@router.get("/analytics/detailed", response_model=UserAnalyticsResponse)
async def get_user_analytics(
    current_user: User = Depends(get_current_user),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    progress_repo: ProgressRepository = Depends(get_progress_repository)
):
    """
    Get detailed analytics for current user
    
    Args:
        current_user: Current authenticated user
        days: Number of days to analyze
        progress_repo: Progress repository
        
    Returns:
        Detailed user analytics
    """
    try:
        # Get analytics data
        analytics_data = await progress_repo.get_user_analytics(current_user.id, days)
        
        return UserAnalyticsResponse(
            user_id=current_user.id,
            learning_streak=analytics_data.get("learning_streak", 0),
            practice_frequency=analytics_data.get("practice_frequency", {}),
            improvement_trends=analytics_data.get("improvement_trends", {}),
            skill_progression=analytics_data.get("skill_progression", {}),
            engagement_metrics=analytics_data.get("engagement_metrics", {})
        )
        
    except Exception as e:
        logger.error(f"Get analytics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")


@router.delete("/account")
async def delete_user_account(
    current_user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Delete current user's account (soft delete - deactivate)
    
    Args:
        current_user: Current authenticated user
        user_repo: User repository
        
    Returns:
        Deletion confirmation
    """
    try:
        # Soft delete by deactivating account
        success = await user_repo.deactivate_user(current_user.id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete account")
        
        logger.info(f"User account deactivated: {current_user.id}")
        
        return {
            "success": True,
            "message": "Account deactivated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Account deletion error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete account")


@router.get("/preferences")
async def get_user_preferences(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's preferences
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User preferences
    """
    try:
        preferences = current_user.preferences or {}
        
        # Add profile preferences if available
        if current_user.profile:
            preferences.update({
                "timezone": current_user.profile.timezone,
                "language": current_user.profile.language,
                "accessibility_settings": current_user.profile.accessibility_settings or {}
            })
        
        return {
            "success": True,
            "preferences": preferences
        }
        
    except Exception as e:
        logger.error(f"Get preferences error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve preferences")


@router.put("/preferences")
async def update_user_preferences(
    preferences: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Update current user's preferences
    
    Args:
        preferences: New preferences data
        current_user: Current authenticated user
        user_repo: User repository
        
    Returns:
        Update confirmation
    """
    try:
        # Update user preferences
        success = await user_repo.update_user(current_user.id, {"preferences": preferences})
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update preferences")
        
        logger.info(f"Preferences updated for user: {current_user.id}")
        
        return {
            "success": True,
            "message": "Preferences updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update preferences error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update preferences")


@router.get("/learning-goals")
async def get_learning_goals(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's learning goals
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User learning goals
    """
    try:
        learning_goals = []
        if current_user.profile and current_user.profile.learning_goals:
            learning_goals = current_user.profile.learning_goals
        
        return {
            "success": True,
            "learning_goals": learning_goals
        }
        
    except Exception as e:
        logger.error(f"Get learning goals error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve learning goals")


@router.put("/learning-goals")
async def update_learning_goals(
    learning_goals: List[str],
    current_user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """
    Update current user's learning goals
    
    Args:
        learning_goals: New learning goals
        current_user: Current authenticated user
        user_repo: User repository
        
    Returns:
        Update confirmation
    """
    try:
        # Update profile learning goals
        success = await user_repo.update_user_profile(
            current_user.id, 
            {"learning_goals": learning_goals}
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update learning goals")
        
        logger.info(f"Learning goals updated for user: {current_user.id}")
        
        return {
            "success": True,
            "message": "Learning goals updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update learning goals error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update learning goals")