"""
Demo API endpoints showing integration with the core services architecture
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from core.service_container import get_service_container
from services.user_service import UserService
from services.content_service import ContentService
from services.session_service import SessionService
from services.analytics_service import AnalyticsService

router = APIRouter(prefix="/services-demo", tags=["services-demo"])


# Pydantic models for API requests/responses
class CreateUserRequest(BaseModel):
    email: str
    username: str
    first_name: str
    last_name: str


class CreateStoryRequest(BaseModel):
    title: str
    content: str
    difficulty_level: str = "beginner"
    sentences: List[str]
    is_public: bool = False


class CreateSessionRequest(BaseModel):
    user_id: str
    story_id: str
    session_type: str = "individual"


# Dependency to get services
async def get_user_service() -> UserService:
    container = get_service_container()
    return await container.get_service("UserService")


async def get_content_service() -> ContentService:
    container = get_service_container()
    return await container.get_service("ContentService")


async def get_session_service() -> SessionService:
    container = get_service_container()
    return await container.get_service("SessionService")


async def get_analytics_service() -> AnalyticsService:
    container = get_service_container()
    return await container.get_service("AnalyticsService")


# User management endpoints
@router.post("/users", response_model=Dict[str, Any])
async def create_user(
    request: CreateUserRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Create a new user account"""
    try:
        user_data = request.dict()
        created_user = await user_service.create_user(user_data)
        return {"success": True, "user": created_user}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}", response_model=Dict[str, Any])
async def get_user(
    user_id: str,
    user_service: UserService = Depends(get_user_service)
):
    """Get user by ID"""
    try:
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"success": True, "user": user}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/profile", response_model=Dict[str, Any])
async def get_user_profile(
    user_id: str,
    user_service: UserService = Depends(get_user_service)
):
    """Get user profile"""
    try:
        profile = await user_service.get_user_profile(user_id)
        return {"success": True, "profile": profile}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/progress", response_model=Dict[str, Any])
async def get_user_progress(
    user_id: str,
    user_service: UserService = Depends(get_user_service)
):
    """Get user learning progress"""
    try:
        progress = await user_service.get_user_progress(user_id)
        return {"success": True, "progress": progress}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Content management endpoints
@router.post("/stories", response_model=Dict[str, Any])
async def create_story(
    request: CreateStoryRequest,
    created_by: str = "demo-user",  # In real app, get from auth
    content_service: ContentService = Depends(get_content_service)
):
    """Create a new story"""
    try:
        story_data = request.dict()
        created_story = await content_service.create_story(story_data, created_by)
        return {"success": True, "story": created_story}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stories", response_model=Dict[str, Any])
async def get_stories(
    limit: int = 50,
    offset: int = 0,
    difficulty_level: Optional[str] = None,
    content_service: ContentService = Depends(get_content_service)
):
    """Get stories with filtering"""
    try:
        stories = await content_service.get_stories(
            limit=limit,
            offset=offset,
            difficulty_level=difficulty_level
        )
        return {"success": True, "stories": stories, "count": len(stories)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stories/{story_id}", response_model=Dict[str, Any])
async def get_story(
    story_id: str,
    content_service: ContentService = Depends(get_content_service)
):
    """Get story by ID"""
    try:
        story = await content_service.get_story_by_id(story_id)
        if not story:
            raise HTTPException(status_code=404, detail="Story not found")
        return {"success": True, "story": story}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stories/search/{query}", response_model=Dict[str, Any])
async def search_stories(
    query: str,
    limit: int = 20,
    content_service: ContentService = Depends(get_content_service)
):
    """Search stories"""
    try:
        stories = await content_service.search_stories(query, limit)
        return {"success": True, "stories": stories, "query": query}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Session management endpoints
@router.post("/sessions", response_model=Dict[str, Any])
async def create_session(
    request: CreateSessionRequest,
    session_service: SessionService = Depends(get_session_service)
):
    """Create a new practice session"""
    try:
        session = await session_service.create_practice_session(
            user_id=request.user_id,
            story_id=request.story_id,
            session_type=request.session_type
        )
        return {"success": True, "session": session}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=Dict[str, Any])
async def get_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service)
):
    """Get session by ID"""
    try:
        session = await session_service.get_session_by_id(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"success": True, "session": session}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/sessions", response_model=Dict[str, Any])
async def get_user_sessions(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    session_service: SessionService = Depends(get_session_service)
):
    """Get sessions for a user"""
    try:
        sessions = await session_service.get_user_sessions(user_id, limit, offset)
        return {"success": True, "sessions": sessions, "count": len(sessions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/progress-summary", response_model=Dict[str, Any])
async def get_progress_summary(
    user_id: str,
    session_service: SessionService = Depends(get_session_service)
):
    """Get user progress summary"""
    try:
        summary = await session_service.get_user_progress_summary(user_id)
        return {"success": True, "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Analytics endpoints
@router.get("/analytics/users/{user_id}/insights", response_model=Dict[str, Any])
async def get_learning_insights(
    user_id: str,
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get personalized learning insights"""
    try:
        insights = await analytics_service.get_learning_insights(user_id)
        return {"success": True, "insights": insights}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/platform", response_model=Dict[str, Any])
async def get_platform_metrics(
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get platform-wide metrics"""
    try:
        metrics = await analytics_service.get_platform_metrics()
        return {"success": True, "metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/modules/{module_name}", response_model=Dict[str, Any])
async def get_module_analytics(
    module_name: str,
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """Get analytics for a specific module"""
    try:
        analytics = await analytics_service.get_module_analytics(module_name)
        return {"success": True, "analytics": analytics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Service health endpoint
@router.get("/health", response_model=Dict[str, Any])
async def get_service_health():
    """Get health status of all services"""
    try:
        from core.service_registry import get_service_health_status
        container = get_service_container()
        health_status = get_service_health_status(container)
        return health_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))