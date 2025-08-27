"""
GraphQL endpoint for complex queries in StorySign ASL Platform
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.types import Info
from fastapi import Depends, HTTPException

# Import with error handling
try:
    from ..models.user import User
    USER_MODEL_AVAILABLE = True
except ImportError:
    USER_MODEL_AVAILABLE = False
    # Create a simple fallback User class
    class User:
        def __init__(self):
            self.id = "unknown"
            self.username = "unknown"
            self.email = "unknown"

try:
    from ..repositories.user_repository import UserRepository
    USER_REPO_AVAILABLE = True
except ImportError:
    USER_REPO_AVAILABLE = False

try:
    from ..repositories.progress_repository import ProgressRepository
    PROGRESS_REPO_AVAILABLE = True
except ImportError:
    PROGRESS_REPO_AVAILABLE = False

try:
    from ..repositories.content_repository import ContentRepository
    CONTENT_REPO_AVAILABLE = True
except ImportError:
    CONTENT_REPO_AVAILABLE = False

try:
    from ..core.database_service import DatabaseService
    DB_SERVICE_AVAILABLE = True
except ImportError:
    DB_SERVICE_AVAILABLE = False

try:
    from .auth import get_current_user
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    # Create a fallback function
    async def get_current_user():
        return User()

logger = logging.getLogger(__name__)


# GraphQL Types
@strawberry.type
class UserType:
    id: str
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    is_active: bool
    created_at: str
    
    @strawberry.field
    def full_name(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.username


@strawberry.type
class UserProfileType:
    bio: Optional[str]
    avatar_url: Optional[str]
    timezone: str
    language: str
    learning_goals: List[str]


@strawberry.type
class StoryType:
    id: str
    title: str
    description: Optional[str]
    difficulty_level: str
    sentence_count: int
    avg_rating: float
    rating_count: int
    is_public: bool
    created_at: str
    
    @strawberry.field
    def tags(self) -> List[str]:
        # TODO: Implement tag loading
        return []


@strawberry.type
class PracticeSessionType:
    id: str
    story_id: str
    session_type: str
    overall_score: Optional[float]
    sentences_completed: int
    total_sentences: int
    started_at: str
    completed_at: Optional[str]
    
    @strawberry.field
    async def story(self, info: Info) -> Optional[StoryType]:
        # TODO: Implement story loading from session
        return None


@strawberry.type
class UserProgressType:
    user_id: str
    skill_area: str
    current_level: float
    experience_points: float
    last_updated: str


@strawberry.type
class LearningAnalyticsType:
    total_sessions: int
    total_practice_time: int
    stories_completed: int
    average_score: float
    learning_streak: int
    skill_levels: List[UserProgressType]


@strawberry.type
class CollaborativeSessionType:
    id: str
    session_name: str
    host_id: str
    participant_count: int
    story_id: str
    status: str
    created_at: str
    
    @strawberry.field
    async def host(self, info: Info) -> Optional[UserType]:
        # TODO: Implement host loading
        return None


# Input Types
@strawberry.input
class UserSearchInput:
    query: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    limit: int = 20
    offset: int = 0


@strawberry.input
class StorySearchInput:
    query: Optional[str] = None
    difficulty_levels: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None
    min_rating: Optional[float] = None
    limit: int = 50
    offset: int = 0


@strawberry.input
class ProgressFilterInput:
    skill_areas: Optional[List[str]] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


@strawberry.input
class AnalyticsTimeRangeInput:
    days: int = 30
    include_detailed: bool = False


# Dependency injection for GraphQL with error handling
async def get_user_repository():
    """Get user repository instance"""
    if not USER_REPO_AVAILABLE or not DB_SERVICE_AVAILABLE:
        return None
    
    db_service = DatabaseService()
    session = await db_service.get_session()
    return UserRepository(session)


async def get_progress_repository():
    """Get progress repository instance"""
    if not PROGRESS_REPO_AVAILABLE or not DB_SERVICE_AVAILABLE:
        return None
    
    db_service = DatabaseService()
    session = await db_service.get_session()
    return ProgressRepository(session)


async def get_content_repository():
    """Get content repository instance"""
    if not CONTENT_REPO_AVAILABLE or not DB_SERVICE_AVAILABLE:
        return None
    
    db_service = DatabaseService()
    session = await db_service.get_session()
    return ContentRepository(session)


# GraphQL Context
@strawberry.type
class Context:
    current_user: Optional[object] = None
    user_repo: Optional[object] = None
    progress_repo: Optional[object] = None
    content_repo: Optional[object] = None


# Query resolvers
@strawberry.type
class Query:
    
    @strawberry.field
    async def me(self, info: Info) -> Optional[UserType]:
        """Get current user information"""
        try:
            context: Context = info.context
            if not context.current_user:
                return None
            
            user = context.current_user
            return UserType(
                id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                is_active=user.is_active,
                created_at=user.created_at.isoformat()
            )
        except Exception as e:
            logger.error(f"GraphQL me query error: {e}")
            return None
    
    @strawberry.field
    async def user(self, info: Info, user_id: str) -> Optional[UserType]:
        """Get user by ID"""
        try:
            context: Context = info.context
            if not context.user_repo:
                return None
            
            user = await context.user_repo.get_by_id_with_profile(user_id)
            if not user:
                return None
            
            # Return limited public information
            return UserType(
                id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                email="",  # Don't expose email
                is_active=user.is_active,
                created_at=user.created_at.isoformat()
            )
        except Exception as e:
            logger.error(f"GraphQL user query error: {e}")
            return None
    
    @strawberry.field
    async def users(self, info: Info, search: Optional[UserSearchInput] = None) -> List[UserType]:
        """Search users"""
        try:
            context: Context = info.context
            if not context.user_repo:
                return []
            
            search = search or UserSearchInput()
            
            if search.query:
                users = await context.user_repo.search_users(search.query, search.limit)
            else:
                users = await context.user_repo.get_active_users(search.limit, search.offset)
            
            return [
                UserType(
                    id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    email="",  # Don't expose emails in search
                    is_active=user.is_active,
                    created_at=user.created_at.isoformat()
                )
                for user in users
            ]
        except Exception as e:
            logger.error(f"GraphQL users query error: {e}")
            return []
    
    @strawberry.field
    async def my_progress(self, info: Info, filters: Optional[ProgressFilterInput] = None) -> List[UserProgressType]:
        """Get current user's learning progress"""
        try:
            context: Context = info.context
            if not context.current_user or not context.progress_repo:
                return []
            
            progress_records = await context.progress_repo.get_user_progress(context.current_user.id)
            
            return [
                UserProgressType(
                    user_id=progress.user_id,
                    skill_area=progress.skill_area,
                    current_level=progress.current_level,
                    experience_points=progress.experience_points,
                    last_updated=progress.last_updated.isoformat()
                )
                for progress in progress_records
            ]
        except Exception as e:
            logger.error(f"GraphQL my_progress query error: {e}")
            return []
    
    @strawberry.field
    async def my_sessions(self, info: Info, limit: int = 20, offset: int = 0) -> List[PracticeSessionType]:
        """Get current user's practice sessions"""
        try:
            context: Context = info.context
            if not context.current_user or not context.progress_repo:
                return []
            
            sessions = await context.progress_repo.get_user_sessions(
                context.current_user.id, limit, offset
            )
            
            return [
                PracticeSessionType(
                    id=session.id,
                    story_id=session.story_id,
                    session_type=session.session_type,
                    overall_score=session.overall_score,
                    sentences_completed=session.sentences_completed,
                    total_sentences=session.total_sentences,
                    started_at=session.started_at.isoformat(),
                    completed_at=session.completed_at.isoformat() if session.completed_at else None
                )
                for session in sessions
            ]
        except Exception as e:
            logger.error(f"GraphQL my_sessions query error: {e}")
            return []
    
    @strawberry.field
    async def stories(self, info: Info, search: Optional[StorySearchInput] = None) -> List[StoryType]:
        """Search stories"""
        try:
            context: Context = info.context
            if not context.content_repo:
                return []
            
            search = search or StorySearchInput()
            
            # Build filters
            filters = {}
            if search.difficulty_levels:
                filters["difficulty_levels"] = search.difficulty_levels
            if search.tags:
                filters["tags"] = search.tags
            if search.is_public is not None:
                filters["is_public"] = search.is_public
            if search.min_rating is not None:
                filters["min_rating"] = search.min_rating
            
            stories, _ = await context.content_repo.search_stories(
                query=search.query,
                filters=filters,
                limit=search.limit,
                offset=search.offset
            )
            
            return [
                StoryType(
                    id=story.id,
                    title=story.title,
                    description=story.description,
                    difficulty_level=story.difficulty_level,
                    sentence_count=len(story.sentences) if story.sentences else 0,
                    avg_rating=story.avg_rating or 0.0,
                    rating_count=story.rating_count or 0,
                    is_public=story.is_public,
                    created_at=story.created_at.isoformat()
                )
                for story in stories
            ]
        except Exception as e:
            logger.error(f"GraphQL stories query error: {e}")
            return []
    
    @strawberry.field
    async def my_analytics(self, info: Info, time_range: Optional[AnalyticsTimeRangeInput] = None) -> Optional[LearningAnalyticsType]:
        """Get current user's learning analytics"""
        try:
            context: Context = info.context
            if not context.current_user or not context.progress_repo:
                return None
            
            time_range = time_range or AnalyticsTimeRangeInput()
            
            # Get analytics data
            analytics_data = await context.progress_repo.get_user_analytics(
                context.current_user.id, time_range.days
            )
            
            # Get skill levels
            progress_records = await context.progress_repo.get_user_progress(context.current_user.id)
            skill_levels = [
                UserProgressType(
                    user_id=progress.user_id,
                    skill_area=progress.skill_area,
                    current_level=progress.current_level,
                    experience_points=progress.experience_points,
                    last_updated=progress.last_updated.isoformat()
                )
                for progress in progress_records
            ]
            
            return LearningAnalyticsType(
                total_sessions=analytics_data.get("total_sessions", 0),
                total_practice_time=analytics_data.get("total_practice_time", 0),
                stories_completed=analytics_data.get("stories_completed", 0),
                average_score=analytics_data.get("average_score", 0.0),
                learning_streak=analytics_data.get("learning_streak", 0),
                skill_levels=skill_levels
            )
        except Exception as e:
            logger.error(f"GraphQL my_analytics query error: {e}")
            return None
    
    @strawberry.field
    async def collaborative_sessions(self, info: Info, active_only: bool = True) -> List[CollaborativeSessionType]:
        """Get collaborative sessions"""
        try:
            context: Context = info.context
            if not context.current_user:
                return []
            
            # TODO: Implement collaborative session repository
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"GraphQL collaborative_sessions query error: {e}")
            return []


# Mutation resolvers
@strawberry.type
class Mutation:
    
    @strawberry.field
    async def update_learning_goals(self, info: Info, goals: List[str]) -> bool:
        """Update user's learning goals"""
        try:
            context: Context = info.context
            if not context.current_user or not context.user_repo:
                return False
            
            success = await context.user_repo.update_user_profile(
                context.current_user.id,
                {"learning_goals": goals}
            )
            
            return success is not None
        except Exception as e:
            logger.error(f"GraphQL update_learning_goals mutation error: {e}")
            return False
    
    @strawberry.field
    async def update_preferences(self, info: Info, preferences: str) -> bool:
        """Update user preferences (JSON string)"""
        try:
            import json
            
            context: Context = info.context
            if not context.current_user or not context.user_repo:
                return False
            
            # Parse JSON preferences
            prefs_dict = json.loads(preferences)
            
            success = await context.user_repo.update_user(
                context.current_user.id,
                {"preferences": prefs_dict}
            )
            
            return success is not None
        except Exception as e:
            logger.error(f"GraphQL update_preferences mutation error: {e}")
            return False


# Schema
schema = strawberry.Schema(query=Query, mutation=Mutation)


# Context dependency
async def get_graphql_context(
    current_user = Depends(get_current_user)
):
    """Create GraphQL context with dependencies"""
    try:
        user_repo = await get_user_repository()
        progress_repo = await get_progress_repository()
        content_repo = await get_content_repository()
        
        return Context(
            current_user=current_user,
            user_repo=user_repo,
            progress_repo=progress_repo,
            content_repo=content_repo
        )
    except Exception as e:
        logger.error(f"GraphQL context creation error: {e}")
        # Return context with current user only
        return Context(current_user=current_user)


# Create GraphQL router
graphql_app = GraphQLRouter(
    schema,
    context_getter=get_graphql_context,
    path="/api/v1/graphql"
)