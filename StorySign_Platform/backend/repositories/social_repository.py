"""
Repository layer for social learning features
Handles database operations for friendships, feedback, ratings, and progress sharing
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .base_repository import BaseRepository
from ..models.social import (
    Friendship, CommunityFeedback, CommunityRating, ProgressShare, SocialInteraction,
    FriendshipStatus, FeedbackType, RatingType, PrivacyLevel
)
from ..models.user import User


class SocialRepository(BaseRepository):
    """Repository for social learning features"""
    
    # Friendship Management
    
    async def create_friendship_request(
        self,
        requester_id: str,
        addressee_id: str,
        message: Optional[str] = None
    ) -> Friendship:
        """Create a new friendship request"""
        
        # Check if friendship already exists
        existing = await self.session.execute(
            self.session.query(Friendship).filter(
                or_(
                    and_(Friendship.requester_id == requester_id, Friendship.addressee_id == addressee_id),
                    and_(Friendship.requester_id == addressee_id, Friendship.addressee_id == requester_id)
                )
            )
        )
        
        if existing.scalar_one_or_none():
            raise ValueError("Friendship request already exists")
        
        friendship = Friendship(
            id=str(uuid.uuid4()),
            requester_id=requester_id,
            addressee_id=addressee_id,
            status=FriendshipStatus.PENDING.value,
            requester_notes=message
        )
        
        self.session.add(friendship)
        await self.session.flush()
        return friendship
    
    async def respond_to_friendship(
        self,
        friendship_id: str,
        response: FriendshipStatus,
        responder_id: str
    ) -> Friendship:
        """Respond to a friendship request"""
        
        friendship = await self.get_by_id(Friendship, friendship_id)
        if not friendship:
            raise ValueError("Friendship not found")
        
        # Verify responder is the addressee
        if friendship.addressee_id != responder_id:
            raise ValueError("Only the addressee can respond to friendship requests")
        
        friendship.status = response.value
        friendship.responded_at = datetime.utcnow()
        
        await self.session.flush()
        return friendship
    
    async def get_user_friends(
        self,
        user_id: str,
        status: Optional[FriendshipStatus] = None
    ) -> List[Dict[str, Any]]:
        """Get all friends for a user"""
        
        query = self.session.query(Friendship).filter(
            or_(
                Friendship.requester_id == user_id,
                Friendship.addressee_id == user_id
            )
        )
        
        if status:
            query = query.filter(Friendship.status == status.value)
        
        result = await self.session.execute(query)
        friendships = result.scalars().all()
        
        friends = []
        for friendship in friendships:
            friend_id = friendship.get_friend_id(user_id)
            if friend_id:
                # Get friend user info
                friend_user = await self.get_by_id(User, friend_id)
                if friend_user:
                    friends.append({
                        "friendship": friendship.get_friendship_summary(user_id),
                        "friend": {
                            "id": friend_user.id,
                            "username": friend_user.username,
                            "first_name": friend_user.first_name,
                            "last_name": friend_user.last_name
                        }
                    })
        
        return friends
    
    async def get_friendship_requests(
        self,
        user_id: str,
        incoming: bool = True
    ) -> List[Friendship]:
        """Get pending friendship requests for a user"""
        
        if incoming:
            query = self.session.query(Friendship).filter(
                and_(
                    Friendship.addressee_id == user_id,
                    Friendship.status == FriendshipStatus.PENDING.value
                )
            )
        else:
            query = self.session.query(Friendship).filter(
                and_(
                    Friendship.requester_id == user_id,
                    Friendship.status == FriendshipStatus.PENDING.value
                )
            )
        
        result = await self.session.execute(query.order_by(desc(Friendship.requested_at)))
        return result.scalars().all()
    
    async def update_friendship_settings(
        self,
        friendship_id: str,
        user_id: str,
        settings: Dict[str, Any]
    ) -> Friendship:
        """Update friendship privacy and interaction settings"""
        
        friendship = await self.get_by_id(Friendship, friendship_id)
        if not friendship:
            raise ValueError("Friendship not found")
        
        # Verify user is part of this friendship
        if user_id not in [friendship.requester_id, friendship.addressee_id]:
            raise ValueError("User is not part of this friendship")
        
        # Update settings
        for key, value in settings.items():
            if hasattr(friendship, key):
                setattr(friendship, key, value)
        
        await self.session.flush()
        return friendship
    
    # Community Feedback
    
    async def create_feedback(
        self,
        giver_id: str,
        receiver_id: str,
        feedback_type: FeedbackType,
        content: str,
        session_id: Optional[str] = None,
        story_id: Optional[str] = None,
        sentence_index: Optional[int] = None,
        is_public: bool = False,
        is_anonymous: bool = False,
        tags: Optional[List[str]] = None,
        skill_areas: Optional[List[str]] = None
    ) -> CommunityFeedback:
        """Create new community feedback"""
        
        feedback = CommunityFeedback(
            id=str(uuid.uuid4()),
            giver_id=giver_id,
            receiver_id=receiver_id,
            session_id=session_id,
            story_id=story_id,
            sentence_index=sentence_index,
            feedback_type=feedback_type.value,
            content=content,
            is_public=is_public,
            is_anonymous=is_anonymous,
            tags=tags,
            skill_areas=skill_areas
        )
        
        self.session.add(feedback)
        await self.session.flush()
        return feedback
    
    async def get_user_feedback(
        self,
        user_id: str,
        received: bool = True,
        feedback_type: Optional[FeedbackType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[CommunityFeedback]:
        """Get feedback for a user (received or given)"""
        
        if received:
            query = self.session.query(CommunityFeedback).filter(
                CommunityFeedback.receiver_id == user_id
            )
        else:
            query = self.session.query(CommunityFeedback).filter(
                CommunityFeedback.giver_id == user_id
            )
        
        if feedback_type:
            query = query.filter(CommunityFeedback.feedback_type == feedback_type.value)
        
        query = query.order_by(desc(CommunityFeedback.created_at))
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_session_feedback(
        self,
        session_id: str,
        public_only: bool = True
    ) -> List[CommunityFeedback]:
        """Get all feedback for a specific practice session"""
        
        query = self.session.query(CommunityFeedback).filter(
            CommunityFeedback.session_id == session_id
        )
        
        if public_only:
            query = query.filter(CommunityFeedback.is_public == True)
        
        query = query.order_by(asc(CommunityFeedback.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def rate_feedback_helpfulness(
        self,
        feedback_id: str,
        user_id: str,
        is_helpful: bool
    ) -> CommunityFeedback:
        """Rate the helpfulness of feedback"""
        
        feedback = await self.get_by_id(CommunityFeedback, feedback_id)
        if not feedback:
            raise ValueError("Feedback not found")
        
        # Check if user already rated this feedback
        existing_rating = await self.session.execute(
            self.session.query(SocialInteraction).filter(
                and_(
                    SocialInteraction.user_id == user_id,
                    SocialInteraction.target_type == "feedback",
                    SocialInteraction.target_id == feedback_id,
                    SocialInteraction.interaction_type == "helpfulness_vote"
                )
            )
        )
        
        if existing_rating.scalar_one_or_none():
            raise ValueError("User has already rated this feedback")
        
        # Create interaction record
        interaction = SocialInteraction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            target_type="feedback",
            target_id=feedback_id,
            interaction_type="helpfulness_vote",
            content="helpful" if is_helpful else "unhelpful"
        )
        
        self.session.add(interaction)
        
        # Update feedback helpfulness
        feedback.helpfulness_votes += 1
        
        # Recalculate helpfulness score
        helpful_count = await self.session.execute(
            self.session.query(func.count(SocialInteraction.id)).filter(
                and_(
                    SocialInteraction.target_type == "feedback",
                    SocialInteraction.target_id == feedback_id,
                    SocialInteraction.interaction_type == "helpfulness_vote",
                    SocialInteraction.content == "helpful"
                )
            )
        )
        
        total_votes = feedback.helpfulness_votes
        helpful_votes = helpful_count.scalar() or 0
        
        if total_votes > 0:
            feedback.helpfulness_score = (helpful_votes / total_votes) * 5.0
        
        await self.session.flush()
        return feedback
    
    # Community Ratings
    
    async def create_rating(
        self,
        user_id: str,
        rating_type: RatingType,
        target_id: str,
        rating_value: float,
        review_text: Optional[str] = None,
        difficulty_rating: Optional[float] = None,
        clarity_rating: Optional[float] = None,
        engagement_rating: Optional[float] = None,
        educational_value_rating: Optional[float] = None,
        user_experience_level: Optional[str] = None,
        completion_percentage: Optional[float] = None
    ) -> CommunityRating:
        """Create a new community rating"""
        
        # Check if user already rated this item
        existing = await self.session.execute(
            self.session.query(CommunityRating).filter(
                and_(
                    CommunityRating.user_id == user_id,
                    CommunityRating.rating_type == rating_type.value,
                    CommunityRating.target_id == target_id
                )
            )
        )
        
        if existing.scalar_one_or_none():
            raise ValueError("User has already rated this item")
        
        rating = CommunityRating(
            id=str(uuid.uuid4()),
            user_id=user_id,
            rating_type=rating_type.value,
            target_id=target_id,
            rating_value=rating_value,
            review_text=review_text,
            difficulty_rating=difficulty_rating,
            clarity_rating=clarity_rating,
            engagement_rating=engagement_rating,
            educational_value_rating=educational_value_rating,
            user_experience_level=user_experience_level,
            completion_percentage=completion_percentage
        )
        
        self.session.add(rating)
        await self.session.flush()
        return rating
    
    async def get_ratings_for_item(
        self,
        rating_type: RatingType,
        target_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[CommunityRating], Dict[str, float]]:
        """Get ratings for a specific item with aggregated statistics"""
        
        # Get individual ratings
        query = self.session.query(CommunityRating).filter(
            and_(
                CommunityRating.rating_type == rating_type.value,
                CommunityRating.target_id == target_id,
                CommunityRating.is_approved == True
            )
        ).order_by(desc(CommunityRating.created_at))
        
        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        ratings = result.scalars().all()
        
        # Get aggregated statistics
        stats_query = self.session.query(
            func.count(CommunityRating.id).label('total_ratings'),
            func.avg(CommunityRating.rating_value).label('avg_rating'),
            func.avg(CommunityRating.difficulty_rating).label('avg_difficulty'),
            func.avg(CommunityRating.clarity_rating).label('avg_clarity'),
            func.avg(CommunityRating.engagement_rating).label('avg_engagement'),
            func.avg(CommunityRating.educational_value_rating).label('avg_educational_value')
        ).filter(
            and_(
                CommunityRating.rating_type == rating_type.value,
                CommunityRating.target_id == target_id,
                CommunityRating.is_approved == True
            )
        )
        
        stats_result = await self.session.execute(stats_query)
        stats = stats_result.first()
        
        aggregated_stats = {
            "total_ratings": stats.total_ratings or 0,
            "average_rating": float(stats.avg_rating or 0),
            "average_difficulty": float(stats.avg_difficulty or 0) if stats.avg_difficulty else None,
            "average_clarity": float(stats.avg_clarity or 0) if stats.avg_clarity else None,
            "average_engagement": float(stats.avg_engagement or 0) if stats.avg_engagement else None,
            "average_educational_value": float(stats.avg_educational_value or 0) if stats.avg_educational_value else None
        }
        
        return ratings, aggregated_stats
    
    async def get_user_ratings(
        self,
        user_id: str,
        rating_type: Optional[RatingType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[CommunityRating]:
        """Get all ratings by a specific user"""
        
        query = self.session.query(CommunityRating).filter(
            CommunityRating.user_id == user_id
        )
        
        if rating_type:
            query = query.filter(CommunityRating.rating_type == rating_type.value)
        
        query = query.order_by(desc(CommunityRating.created_at))
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    # Progress Sharing
    
    async def create_progress_share(
        self,
        user_id: str,
        share_type: str,
        title: str,
        description: Optional[str] = None,
        session_id: Optional[str] = None,
        progress_data: Optional[Dict[str, Any]] = None,
        achievement_type: Optional[str] = None,
        privacy_level: PrivacyLevel = PrivacyLevel.FRIENDS,
        visible_to_groups: Optional[List[str]] = None,
        visible_to_friends: Optional[List[str]] = None,
        allow_comments: bool = True,
        allow_reactions: bool = True,
        expires_at: Optional[datetime] = None
    ) -> ProgressShare:
        """Create a new progress share"""
        
        share = ProgressShare(
            id=str(uuid.uuid4()),
            user_id=user_id,
            session_id=session_id,
            share_type=share_type,
            title=title,
            description=description,
            progress_data=progress_data,
            achievement_type=achievement_type,
            privacy_level=privacy_level.value,
            visible_to_groups=visible_to_groups,
            visible_to_friends=visible_to_friends,
            allow_comments=allow_comments,
            allow_reactions=allow_reactions,
            expires_at=expires_at
        )
        
        self.session.add(share)
        await self.session.flush()
        return share
    
    async def get_user_progress_shares(
        self,
        user_id: str,
        viewer_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ProgressShare]:
        """Get progress shares for a user, filtered by privacy settings"""
        
        query = self.session.query(ProgressShare).filter(
            and_(
                ProgressShare.user_id == user_id,
                ProgressShare.is_active == True
            )
        )
        
        # If viewer is different from user, apply privacy filtering
        if viewer_id and viewer_id != user_id:
            # For now, only show public and friends shares
            # In a full implementation, we'd check friendship status and group memberships
            query = query.filter(
                ProgressShare.privacy_level.in_([PrivacyLevel.PUBLIC.value, PrivacyLevel.FRIENDS.value])
            )
        
        query = query.order_by(desc(ProgressShare.created_at))
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_friends_progress_feed(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get progress shares from user's friends"""
        
        # Get user's friends
        friends = await self.get_user_friends(user_id, FriendshipStatus.ACCEPTED)
        friend_ids = [friend["friend"]["id"] for friend in friends]
        
        if not friend_ids:
            return []
        
        # Get progress shares from friends
        query = self.session.query(ProgressShare).filter(
            and_(
                ProgressShare.user_id.in_(friend_ids),
                ProgressShare.is_active == True,
                ProgressShare.privacy_level.in_([
                    PrivacyLevel.PUBLIC.value,
                    PrivacyLevel.FRIENDS.value
                ])
            )
        ).order_by(desc(ProgressShare.created_at))
        
        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        shares = result.scalars().all()
        
        # Enrich with user information
        enriched_shares = []
        for share in shares:
            user = await self.get_by_id(User, share.user_id)
            if user:
                enriched_shares.append({
                    "share": share.get_share_summary(),
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "first_name": user.first_name,
                        "last_name": user.last_name
                    }
                })
        
        return enriched_shares
    
    # Social Interactions
    
    async def create_interaction(
        self,
        user_id: str,
        target_type: str,
        target_id: str,
        interaction_type: str,
        content: Optional[str] = None,
        reaction_emoji: Optional[str] = None,
        is_anonymous: bool = False,
        is_public: bool = True,
        response_to: Optional[str] = None
    ) -> SocialInteraction:
        """Create a new social interaction"""
        
        # Check for duplicate interactions (like, view, etc.)
        if interaction_type in ["like", "view"]:
            existing = await self.session.execute(
                self.session.query(SocialInteraction).filter(
                    and_(
                        SocialInteraction.user_id == user_id,
                        SocialInteraction.target_type == target_type,
                        SocialInteraction.target_id == target_id,
                        SocialInteraction.interaction_type == interaction_type
                    )
                )
            )
            
            if existing.scalar_one_or_none():
                raise ValueError(f"User has already {interaction_type}d this item")
        
        interaction = SocialInteraction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            target_type=target_type,
            target_id=target_id,
            interaction_type=interaction_type,
            content=content,
            reaction_emoji=reaction_emoji,
            is_anonymous=is_anonymous,
            is_public=is_public,
            response_to=response_to
        )
        
        self.session.add(interaction)
        
        # Update counters on target object
        await self._update_interaction_counters(target_type, target_id, interaction_type, 1)
        
        await self.session.flush()
        return interaction
    
    async def get_interactions_for_target(
        self,
        target_type: str,
        target_id: str,
        interaction_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[SocialInteraction]:
        """Get interactions for a specific target"""
        
        query = self.session.query(SocialInteraction).filter(
            and_(
                SocialInteraction.target_type == target_type,
                SocialInteraction.target_id == target_id,
                SocialInteraction.is_approved == True
            )
        )
        
        if interaction_type:
            query = query.filter(SocialInteraction.interaction_type == interaction_type)
        
        query = query.order_by(desc(SocialInteraction.created_at))
        query = query.offset(offset).limit(limit)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def _update_interaction_counters(
        self,
        target_type: str,
        target_id: str,
        interaction_type: str,
        delta: int
    ):
        """Update interaction counters on target objects"""
        
        if target_type == "progress_share":
            share = await self.get_by_id(ProgressShare, target_id)
            if share:
                if interaction_type == "like":
                    share.like_count += delta
                elif interaction_type == "comment":
                    share.comment_count += delta
                elif interaction_type == "view":
                    share.view_count += delta
        
        # Add similar logic for other target types as needed
    
    async def get_user_social_stats(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive social statistics for a user"""
        
        # Get friendship stats
        friends_count = await self.session.execute(
            self.session.query(func.count(Friendship.id)).filter(
                and_(
                    or_(
                        Friendship.requester_id == user_id,
                        Friendship.addressee_id == user_id
                    ),
                    Friendship.status == FriendshipStatus.ACCEPTED.value
                )
            )
        )
        
        # Get feedback stats
        feedback_given = await self.session.execute(
            self.session.query(func.count(CommunityFeedback.id)).filter(
                CommunityFeedback.giver_id == user_id
            )
        )
        
        feedback_received = await self.session.execute(
            self.session.query(func.count(CommunityFeedback.id)).filter(
                CommunityFeedback.receiver_id == user_id
            )
        )
        
        # Get rating stats
        ratings_given = await self.session.execute(
            self.session.query(func.count(CommunityRating.id)).filter(
                CommunityRating.user_id == user_id
            )
        )
        
        # Get progress sharing stats
        shares_created = await self.session.execute(
            self.session.query(func.count(ProgressShare.id)).filter(
                ProgressShare.user_id == user_id
            )
        )
        
        total_likes = await self.session.execute(
            self.session.query(func.sum(ProgressShare.like_count)).filter(
                ProgressShare.user_id == user_id
            )
        )
        
        return {
            "friends_count": friends_count.scalar() or 0,
            "feedback_given": feedback_given.scalar() or 0,
            "feedback_received": feedback_received.scalar() or 0,
            "ratings_given": ratings_given.scalar() or 0,
            "shares_created": shares_created.scalar() or 0,
            "total_likes_received": total_likes.scalar() or 0
        }