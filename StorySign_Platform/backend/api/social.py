"""
Social learning API endpoints for StorySign ASL Platform
Handles friendships, community feedback, ratings, and progress sharing
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database_service import get_database_session
from ..services.social_service import SocialService
from ..models.social import FriendshipStatus, FeedbackType, RatingType, PrivacyLevel

router = APIRouter()


# Pydantic models for request/response

class FriendRequestModel(BaseModel):
    username: str = Field(..., description="Username of user to send friend request to")
    message: Optional[str] = Field(None, description="Optional message with friend request")


class FriendResponseModel(BaseModel):
    accept: bool = Field(..., description="Whether to accept or decline the friend request")


class FeedbackCreateModel(BaseModel):
    receiver_username: str = Field(..., description="Username of user to give feedback to")
    feedback_type: str = Field(..., description="Type of feedback: encouragement, suggestion, correction, question, praise")
    content: str = Field(..., description="Feedback content")
    session_id: Optional[str] = Field(None, description="Practice session ID if feedback is session-specific")
    story_id: Optional[str] = Field(None, description="Story ID if feedback is story-specific")
    sentence_index: Optional[int] = Field(None, description="Sentence index if feedback is sentence-specific")
    is_public: bool = Field(False, description="Whether feedback is publicly visible")
    is_anonymous: bool = Field(False, description="Whether to give feedback anonymously")
    tags: Optional[List[str]] = Field(None, description="Tags for categorizing feedback")
    skill_areas: Optional[List[str]] = Field(None, description="Skill areas this feedback addresses")


class RatingCreateModel(BaseModel):
    rating_type: str = Field(..., description="Type of content being rated: story, session, feedback, user_content")
    target_id: str = Field(..., description="ID of the content being rated")
    rating_value: float = Field(..., ge=1.0, le=5.0, description="Rating value (1-5)")
    review_text: Optional[str] = Field(None, description="Optional text review")
    detailed_ratings: Optional[Dict[str, float]] = Field(None, description="Detailed ratings for different aspects")
    user_experience_level: Optional[str] = Field(None, description="User's experience level when rating")
    completion_percentage: Optional[float] = Field(None, ge=0.0, le=100.0, description="Percentage of content completed")


class ProgressShareModel(BaseModel):
    share_type: str = Field(..., description="Type of progress being shared")
    title: str = Field(..., description="Title of the progress share")
    description: Optional[str] = Field(None, description="Description of the achievement")
    session_id: Optional[str] = Field(None, description="Practice session ID if sharing session progress")
    progress_data: Optional[Dict[str, Any]] = Field(None, description="Detailed progress information")
    achievement_type: Optional[str] = Field(None, description="Type of achievement")
    privacy_level: str = Field("friends", description="Privacy level: public, friends, groups, private")
    visible_to_groups: Optional[List[str]] = Field(None, description="Group IDs that can see this share")
    visible_to_friends: Optional[List[str]] = Field(None, description="Friend IDs that can see this share")
    allow_comments: bool = Field(True, description="Whether to allow comments")
    allow_reactions: bool = Field(True, description="Whether to allow reactions")
    expires_in_days: Optional[int] = Field(None, description="Number of days until share expires")


class InteractionModel(BaseModel):
    interaction_type: str = Field(..., description="Type of interaction: like, comment, reaction, view")
    content: Optional[str] = Field(None, description="Content for comments")
    reaction_emoji: Optional[str] = Field(None, description="Emoji for reactions")


class FriendshipSettingsModel(BaseModel):
    allow_progress_sharing: Optional[bool] = Field(None, description="Allow progress sharing")
    allow_session_invites: Optional[bool] = Field(None, description="Allow session invites")
    allow_feedback: Optional[bool] = Field(None, description="Allow feedback")


# Friendship endpoints

@router.post("/friends/request")
async def send_friend_request(
    request: FriendRequestModel,
    current_user_id: str = Depends(lambda: "user123"),  # TODO: Replace with actual auth
    session: AsyncSession = Depends(get_database_session)
):
    """Send a friend request to another user"""
    
    try:
        social_service = SocialService(session)
        result = await social_service.send_friend_request(
            requester_id=current_user_id,
            addressee_username=request.username,
            message=request.message
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to send friend request")


@router.post("/friends/respond/{friendship_id}")
async def respond_to_friend_request(
    friendship_id: str,
    response: FriendResponseModel,
    current_user_id: str = Depends(lambda: "user123"),  # TODO: Replace with actual auth
    session: AsyncSession = Depends(get_database_session)
):
    """Accept or decline a friend request"""
    
    try:
        social_service = SocialService(session)
        result = await social_service.respond_to_friend_request(
            friendship_id=friendship_id,
            user_id=current_user_id,
            accept=response.accept
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to respond to friend request")


@router.get("/friends")
async def get_friends_list(
    include_pending: bool = Query(False, description="Include pending friend requests"),
    current_user_id: str = Depends(lambda: "user123"),  # TODO: Replace with actual auth
    session: AsyncSession = Depends(get_database_session)
):
    """Get user's friends list"""
    
    try:
        social_service = SocialService(session)
        result = await social_service.get_friends_list(
            user_id=current_user_id,
            include_pending=include_pending
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get friends list")


@router.put("/friends/{friendship_id}/settings")
async def update_friendship_settings(
    friendship_id: str,
    settings: FriendshipSettingsModel,
    current_user_id: str = Depends(lambda: "user123"),  # TODO: Replace with actual auth
    session: AsyncSession = Depends(get_database_session)
):
    """Update privacy settings for a friendship"""
    
    try:
        social_service = SocialService(session)
        
        # Filter out None values
        privacy_settings = {k: v for k, v in settings.dict().items() if v is not None}
        
        result = await social_service.update_friendship_privacy(
            friendship_id=friendship_id,
            user_id=current_user_id,
            privacy_settings=privacy_settings
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update friendship settings")


@router.delete("/friends/{friendship_id}")
async def remove_friend(
    friendship_id: str,
    current_user_id: str = Depends(lambda: "user123"),  # TODO: Replace with actual auth
    session: AsyncSession = Depends(get_database_session)
):
    """Remove a friend"""
    
    try:
        social_service = SocialService(session)
        result = await social_service.remove_friend(
            friendship_id=friendship_id,
            user_id=current_user_id
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to remove friend")


# Community feedback endpoints

@router.post("/feedback")
async def give_feedback(
    feedback: FeedbackCreateModel,
    current_user_id: str = Depends(lambda: "user123"),  # TODO: Replace with actual auth
    session: AsyncSession = Depends(get_database_session)
):
    """Give feedback to another user"""
    
    try:
        social_service = SocialService(session)
        result = await social_service.give_feedback(
            giver_id=current_user_id,
            receiver_username=feedback.receiver_username,
            feedback_type=feedback.feedback_type,
            content=feedback.content,
            session_id=feedback.session_id,
            story_id=feedback.story_id,
            sentence_index=feedback.sentence_index,
            is_public=feedback.is_public,
            is_anonymous=feedback.is_anonymous,
            tags=feedback.tags,
            skill_areas=feedback.skill_areas
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to give feedback")


@router.get("/feedback")
async def get_user_feedback(
    direction: str = Query("received", description="Direction: received or given"),
    feedback_type: Optional[str] = Query(None, description="Filter by feedback type"),
    limit: int = Query(50, ge=1, le=100, description="Number of feedback items to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user_id: str = Depends(lambda: "user123"),  # TODO: Replace with actual auth
    session: AsyncSession = Depends(get_database_session)
):
    """Get feedback for the current user"""
    
    try:
        social_service = SocialService(session)
        result = await social_service.get_user_feedback(
            user_id=current_user_id,
            feedback_direction=direction,
            feedback_type=feedback_type,
            limit=limit,
            offset=offset
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get feedback")


@router.post("/feedback/{feedback_id}/rate")
async def rate_feedback_helpfulness(
    feedback_id: str,
    is_helpful: bool = Body(..., description="Whether the feedback is helpful"),
    current_user_id: str = Depends(lambda: "user123"),  # TODO: Replace with actual auth
    session: AsyncSession = Depends(get_database_session)
):
    """Rate the helpfulness of feedback"""
    
    try:
        social_service = SocialService(session)
        result = await social_service.rate_feedback_helpfulness(
            feedback_id=feedback_id,
            user_id=current_user_id,
            is_helpful=is_helpful
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to rate feedback")


# Community ratings endpoints

@router.post("/ratings")
async def rate_content(
    rating: RatingCreateModel,
    current_user_id: str = Depends(lambda: "user123"),  # TODO: Replace with actual auth
    session: AsyncSession = Depends(get_database_session)
):
    """Rate content (story, session, etc.)"""
    
    try:
        social_service = SocialService(session)
        result = await social_service.rate_content(
            user_id=current_user_id,
            rating_type=rating.rating_type,
            target_id=rating.target_id,
            rating_value=rating.rating_value,
            review_text=rating.review_text,
            detailed_ratings=rating.detailed_ratings,
            user_experience_level=rating.user_experience_level,
            completion_percentage=rating.completion_percentage
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to rate content")


@router.get("/ratings/{rating_type}/{target_id}")
async def get_content_ratings(
    rating_type: str,
    target_id: str,
    limit: int = Query(50, ge=1, le=100, description="Number of ratings to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    session: AsyncSession = Depends(get_database_session)
):
    """Get ratings for specific content"""
    
    try:
        social_service = SocialService(session)
        result = await social_service.get_content_ratings(
            rating_type=rating_type,
            target_id=target_id,
            limit=limit,
            offset=offset
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get ratings")


# Progress sharing endpoints

@router.post("/progress/share")
async def share_progress(
    share: ProgressShareModel,
    current_user_id: str = Depends(lambda: "user123"),  # TODO: Replace with actual auth
    session: AsyncSession = Depends(get_database_session)
):
    """Share learning progress"""
    
    try:
        social_service = SocialService(session)
        result = await social_service.share_progress(
            user_id=current_user_id,
            share_type=share.share_type,
            title=share.title,
            description=share.description,
            session_id=share.session_id,
            progress_data=share.progress_data,
            achievement_type=share.achievement_type,
            privacy_level=share.privacy_level,
            visible_to_groups=share.visible_to_groups,
            visible_to_friends=share.visible_to_friends,
            allow_comments=share.allow_comments,
            allow_reactions=share.allow_reactions,
            expires_in_days=share.expires_in_days
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to share progress")


@router.get("/progress/feed")
async def get_progress_feed(
    feed_type: str = Query("friends", description="Feed type: friends, own, public"),
    limit: int = Query(50, ge=1, le=100, description="Number of shares to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user_id: str = Depends(lambda: "user123"),  # TODO: Replace with actual auth
    session: AsyncSession = Depends(get_database_session)
):
    """Get progress sharing feed"""
    
    try:
        social_service = SocialService(session)
        result = await social_service.get_progress_feed(
            user_id=current_user_id,
            feed_type=feed_type,
            limit=limit,
            offset=offset
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get progress feed")


@router.post("/progress/{share_id}/interact")
async def interact_with_share(
    share_id: str,
    interaction: InteractionModel,
    current_user_id: str = Depends(lambda: "user123"),  # TODO: Replace with actual auth
    session: AsyncSession = Depends(get_database_session)
):
    """Interact with a progress share (like, comment, react)"""
    
    try:
        social_service = SocialService(session)
        result = await social_service.interact_with_share(
            user_id=current_user_id,
            share_id=share_id,
            interaction_type=interaction.interaction_type,
            content=interaction.content,
            reaction_emoji=interaction.reaction_emoji
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to interact with share")


# Social discovery and analytics endpoints

@router.get("/users/search")
async def search_users(
    q: str = Query(..., description="Search query for usernames or names"),
    limit: int = Query(20, ge=1, le=50, description="Number of users to return"),
    current_user_id: str = Depends(lambda: "user123"),  # TODO: Replace with actual auth
    session: AsyncSession = Depends(get_database_session)
):
    """Search for users to connect with"""
    
    try:
        social_service = SocialService(session)
        result = await social_service.search_users(
            query=q,
            searcher_id=current_user_id,
            limit=limit
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to search users")


@router.get("/users/{user_id}/profile")
async def get_user_social_profile(
    user_id: str,
    current_user_id: str = Depends(lambda: "user123"),  # TODO: Replace with actual auth
    session: AsyncSession = Depends(get_database_session)
):
    """Get social profile for a user"""
    
    try:
        social_service = SocialService(session)
        result = await social_service.get_user_social_profile(
            user_id=user_id,
            viewer_id=current_user_id
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get user profile")


@router.get("/community/leaderboard")
async def get_community_leaderboard(
    metric: str = Query("progress_shares", description="Metric: progress_shares, feedback_given, helpful_ratings"),
    time_period: str = Query("month", description="Time period: week, month, all_time"),
    limit: int = Query(50, ge=1, le=100, description="Number of users to return"),
    session: AsyncSession = Depends(get_database_session)
):
    """Get community leaderboard for social engagement"""
    
    try:
        social_service = SocialService(session)
        result = await social_service.get_community_leaderboard(
            metric=metric,
            time_period=time_period,
            limit=limit
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get leaderboard")


@router.get("/stats")
async def get_user_social_stats(
    current_user_id: str = Depends(lambda: "user123"),  # TODO: Replace with actual auth
    session: AsyncSession = Depends(get_database_session)
):
    """Get social statistics for the current user"""
    
    try:
        social_service = SocialService(session)
        result = await social_service.get_user_social_profile(
            user_id=current_user_id,
            viewer_id=current_user_id
        )
        return {
            "user_id": current_user_id,
            "social_stats": result["social_stats"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get social stats")