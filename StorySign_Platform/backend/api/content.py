"""
Content management API endpoints for StorySign ASL Platform
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from pydantic import BaseModel, Field, validator
from datetime import datetime

from ..services.enhanced_content_service import EnhancedContentService, ContentApprovalService
from ..models.content import ContentStatus, DifficultyLevel, ContentType
from ..core.database_service import DatabaseService

router = APIRouter()


# Pydantic models for request/response
class StoryCreateRequest(BaseModel):
    """Request model for creating a story"""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    content: Optional[str] = None
    sentences: List[Dict[str, Any]] = Field(..., min_items=1)
    difficulty_level: str = Field(default=DifficultyLevel.BEGINNER.value)
    content_type: str = Field(default=ContentType.STORY.value)
    learning_objectives: Optional[List[str]] = None
    skill_areas: Optional[List[str]] = None
    tags: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    language: str = Field(default="en")
    
    @validator('difficulty_level')
    def validate_difficulty(cls, v):
        valid_levels = [level.value for level in DifficultyLevel]
        if v not in valid_levels:
            raise ValueError(f"Difficulty level must be one of: {valid_levels}")
        return v
    
    @validator('content_type')
    def validate_content_type(cls, v):
        valid_types = [type_.value for type_ in ContentType]
        if v not in valid_types:
            raise ValueError(f"Content type must be one of: {valid_types}")
        return v


class StoryUpdateRequest(BaseModel):
    """Request model for updating a story"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    content: Optional[str] = None
    sentences: Optional[List[Dict[str, Any]]] = None
    difficulty_level: Optional[str] = None
    learning_objectives: Optional[List[str]] = None
    skill_areas: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    change_summary: Optional[str] = None


class StorySearchRequest(BaseModel):
    """Request model for story search"""
    query: Optional[str] = None
    difficulty_levels: Optional[List[str]] = None
    content_types: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    skill_areas: Optional[List[str]] = None
    language: Optional[str] = None
    min_rating: Optional[float] = Field(None, ge=0.0, le=5.0)
    max_duration: Optional[int] = Field(None, gt=0)
    is_public: Optional[bool] = None
    status: Optional[str] = None
    created_by: Optional[str] = None
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc")
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class StoryRatingRequest(BaseModel):
    """Request model for rating a story"""
    rating: int = Field(..., ge=1, le=5)
    review_text: Optional[str] = Field(None, max_length=1000)
    difficulty_rating: Optional[int] = Field(None, ge=1, le=5)
    engagement_rating: Optional[int] = Field(None, ge=1, le=5)
    educational_value_rating: Optional[int] = Field(None, ge=1, le=5)


class TagManagementRequest(BaseModel):
    """Request model for managing story tags"""
    add_tags: Optional[List[Dict[str, Any]]] = None
    remove_tags: Optional[List[str]] = None


class ContentApprovalRequest(BaseModel):
    """Request model for content approval"""
    status: str = Field(..., regex="^(approved|rejected|needs_revision)$")
    review_notes: Optional[str] = Field(None, max_length=1000)
    content_quality_score: Optional[int] = Field(None, ge=1, le=5)
    educational_value_score: Optional[int] = Field(None, ge=1, le=5)
    technical_accuracy_score: Optional[int] = Field(None, ge=1, le=5)


class StoryResponse(BaseModel):
    """Response model for story data"""
    id: str
    title: str
    description: Optional[str]
    difficulty_level: str
    content_type: str
    estimated_duration: Optional[int]
    sentence_count: Optional[int]
    word_count: Optional[int]
    avg_rating: float
    rating_count: int
    view_count: int
    practice_count: int
    is_public: bool
    is_featured: bool
    status: str
    language: str
    created_at: datetime
    published_at: Optional[datetime]
    tags: List[str]


# Dependency injection
async def get_content_service() -> EnhancedContentService:
    """Get content service instance"""
    # TODO: Implement proper dependency injection
    from ..core.database_service import DatabaseService
    db_service = DatabaseService()
    return EnhancedContentService(db_service)


async def get_approval_service() -> ContentApprovalService:
    """Get content approval service instance"""
    # TODO: Implement proper dependency injection
    from ..core.database_service import DatabaseService
    db_service = DatabaseService()
    return ContentApprovalService(db_service)


# API Endpoints

@router.post("/stories", response_model=Dict[str, Any])
async def create_story(
    request: StoryCreateRequest,
    created_by: str = Query(..., description="ID of user creating the story"),
    content_service: EnhancedContentService = Depends(get_content_service)
):
    """
    Create a new story
    
    Args:
        request: Story creation data
        created_by: ID of user creating the story
        content_service: Content service dependency
        
    Returns:
        Created story information
    """
    try:
        story = await content_service.create_story(
            title=request.title,
            sentences=request.sentences,
            created_by=created_by,
            description=request.description,
            content=request.content,
            difficulty_level=request.difficulty_level,
            learning_objectives=request.learning_objectives,
            skill_areas=request.skill_areas,
            tags=request.tags,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "story_id": story.id,
            "message": "Story created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stories/{story_id}")
async def get_story(
    story_id: str = Path(..., description="Story ID"),
    content_service: EnhancedContentService = Depends(get_content_service)
):
    """
    Get story details by ID
    
    Args:
        story_id: Story ID
        content_service: Content service dependency
        
    Returns:
        Story details
    """
    story = await content_service.get_story_details(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    return story.get_summary()


@router.put("/stories/{story_id}")
async def update_story(
    story_id: str = Path(..., description="Story ID"),
    request: StoryUpdateRequest = Body(...),
    updated_by: str = Query(..., description="ID of user updating the story"),
    content_service: EnhancedContentService = Depends(get_content_service)
):
    """
    Update an existing story
    
    Args:
        story_id: Story ID
        request: Story update data
        updated_by: ID of user updating the story
        content_service: Content service dependency
        
    Returns:
        Update confirmation
    """
    # Filter out None values
    update_data = {k: v for k, v in request.dict().items() if v is not None}
    
    story = await content_service.update_story(
        story_id=story_id,
        updated_by=updated_by,
        **update_data
    )
    
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    return {
        "success": True,
        "message": "Story updated successfully"
    }


@router.post("/stories/search")
async def search_stories(
    request: StorySearchRequest = Body(...),
    content_service: EnhancedContentService = Depends(get_content_service)
):
    """
    Search stories with advanced filtering
    
    Args:
        request: Search parameters
        content_service: Content service dependency
        
    Returns:
        Search results with pagination
    """
    # Convert request to filters dict
    filters = {
        "difficulty_levels": request.difficulty_levels,
        "content_types": request.content_types,
        "tags": request.tags,
        "skill_areas": request.skill_areas,
        "language": request.language,
        "min_rating": request.min_rating,
        "max_duration": request.max_duration,
        "is_public": request.is_public,
        "status": request.status,
        "created_by": request.created_by
    }
    
    stories, total_count = await content_service.search_stories(
        query=request.query,
        filters=filters,
        sort_by=request.sort_by,
        sort_order=request.sort_order,
        limit=request.limit,
        offset=request.offset
    )
    
    return {
        "stories": [story.get_summary() for story in stories],
        "total_count": total_count,
        "limit": request.limit,
        "offset": request.offset,
        "has_more": (request.offset + request.limit) < total_count
    }


@router.get("/stories")
async def list_stories(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    difficulty_level: Optional[str] = Query(None),
    is_public: Optional[bool] = Query(None),
    status: Optional[str] = Query(None),
    content_service: EnhancedContentService = Depends(get_content_service)
):
    """
    List stories with basic filtering
    
    Args:
        limit: Maximum number of stories to return
        offset: Number of stories to skip
        difficulty_level: Filter by difficulty level
        is_public: Filter by public status
        status: Filter by content status
        content_service: Content service dependency
        
    Returns:
        List of stories
    """
    filters = {
        "difficulty_levels": [difficulty_level] if difficulty_level else None,
        "is_public": is_public,
        "status": status
    }
    
    stories, total_count = await content_service.search_stories(
        filters=filters,
        limit=limit,
        offset=offset
    )
    
    return {
        "stories": [story.get_summary() for story in stories],
        "total_count": total_count,
        "limit": limit,
        "offset": offset
    }


@router.post("/stories/{story_id}/rating")
async def rate_story(
    story_id: str = Path(..., description="Story ID"),
    request: StoryRatingRequest = Body(...),
    user_id: str = Query(..., description="ID of user providing the rating"),
    content_service: EnhancedContentService = Depends(get_content_service)
):
    """
    Rate a story
    
    Args:
        story_id: Story ID
        request: Rating data
        user_id: ID of user providing the rating
        content_service: Content service dependency
        
    Returns:
        Rating confirmation
    """
    success = await content_service.add_story_rating(
        story_id=story_id,
        user_id=user_id,
        rating=request.rating,
        review_text=request.review_text,
        difficulty_rating=request.difficulty_rating,
        engagement_rating=request.engagement_rating,
        educational_value_rating=request.educational_value_rating
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add rating")
    
    return {
        "success": True,
        "message": "Rating added successfully"
    }


@router.post("/stories/{story_id}/tags")
async def manage_story_tags(
    story_id: str = Path(..., description="Story ID"),
    request: TagManagementRequest = Body(...),
    content_service: EnhancedContentService = Depends(get_content_service)
):
    """
    Add or remove tags from a story
    
    Args:
        story_id: Story ID
        request: Tag management data
        content_service: Content service dependency
        
    Returns:
        Tag management confirmation
    """
    success = await content_service.manage_story_tags(
        story_id=story_id,
        add_tags=request.add_tags,
        remove_tags=request.remove_tags
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to manage tags")
    
    return {
        "success": True,
        "message": "Tags updated successfully"
    }


@router.post("/stories/{story_id}/publish")
async def publish_story(
    story_id: str = Path(..., description="Story ID"),
    publisher_id: str = Query(..., description="ID of user publishing the story"),
    content_service: EnhancedContentService = Depends(get_content_service)
):
    """
    Publish a story
    
    Args:
        story_id: Story ID
        publisher_id: ID of user publishing the story
        content_service: Content service dependency
        
    Returns:
        Publication confirmation
    """
    success = await content_service.publish_story(story_id, publisher_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to publish story")
    
    return {
        "success": True,
        "message": "Story published successfully"
    }


@router.get("/stories/popular")
async def get_popular_stories(
    limit: int = Query(default=10, ge=1, le=50),
    content_service: EnhancedContentService = Depends(get_content_service)
):
    """
    Get popular stories
    
    Args:
        limit: Maximum number of stories to return
        content_service: Content service dependency
        
    Returns:
        List of popular stories
    """
    stories = await content_service.get_popular_stories(limit=limit)
    
    return {
        "stories": [story.get_summary() for story in stories]
    }


@router.get("/stories/featured")
async def get_featured_stories(
    limit: int = Query(default=5, ge=1, le=20),
    content_service: EnhancedContentService = Depends(get_content_service)
):
    """
    Get featured stories
    
    Args:
        limit: Maximum number of stories to return
        content_service: Content service dependency
        
    Returns:
        List of featured stories
    """
    stories = await content_service.get_featured_stories(limit=limit)
    
    return {
        "stories": [story.get_summary() for story in stories]
    }


@router.get("/stories/{story_id}/analytics")
async def get_story_analytics(
    story_id: str = Path(..., description="Story ID"),
    content_service: EnhancedContentService = Depends(get_content_service)
):
    """
    Get analytics data for a story
    
    Args:
        story_id: Story ID
        content_service: Content service dependency
        
    Returns:
        Story analytics data
    """
    analytics = await content_service.get_story_analytics(story_id)
    
    if not analytics:
        raise HTTPException(status_code=404, detail="Story not found")
    
    return analytics


# Content Approval Endpoints

@router.post("/stories/{story_id}/submit-review")
async def submit_for_review(
    story_id: str = Path(..., description="Story ID"),
    approval_service: ContentApprovalService = Depends(get_approval_service)
):
    """
    Submit story for review
    
    Args:
        story_id: Story ID
        approval_service: Approval service dependency
        
    Returns:
        Submission confirmation
    """
    success = await approval_service.submit_for_review(story_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to submit for review")
    
    return {
        "success": True,
        "message": "Story submitted for review"
    }


@router.post("/stories/{story_id}/review")
async def review_content(
    story_id: str = Path(..., description="Story ID"),
    request: ContentApprovalRequest = Body(...),
    reviewer_id: str = Query(..., description="ID of reviewer"),
    approval_service: ContentApprovalService = Depends(get_approval_service)
):
    """
    Review and approve/reject content
    
    Args:
        story_id: Story ID
        request: Approval data
        reviewer_id: ID of reviewer
        approval_service: Approval service dependency
        
    Returns:
        Review confirmation
    """
    success = await approval_service.review_content(
        story_id=story_id,
        reviewer_id=reviewer_id,
        status=request.status,
        review_notes=request.review_notes,
        content_quality_score=request.content_quality_score,
        educational_value_score=request.educational_value_score,
        technical_accuracy_score=request.technical_accuracy_score
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to review content")
    
    return {
        "success": True,
        "message": "Content reviewed successfully"
    }


@router.get("/stories/pending-review")
async def get_pending_reviews(
    reviewer_id: Optional[str] = Query(None, description="Filter by reviewer ID"),
    approval_service: ContentApprovalService = Depends(get_approval_service)
):
    """
    Get stories pending review
    
    Args:
        reviewer_id: Optional reviewer ID to filter by
        approval_service: Approval service dependency
        
    Returns:
        List of stories pending review
    """
    stories = await approval_service.get_pending_reviews(reviewer_id)
    
    return {
        "stories": [story.get_summary() for story in stories]
    }