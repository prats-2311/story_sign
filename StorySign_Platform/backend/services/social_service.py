"""
Social learning service for StorySign ASL Platform
Handles business logic for friendships, community feedback, ratings, and progress sharing
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories.social_repository import SocialRepository
from ..models.social import (
    Friendship, CommunityFeedback, CommunityRating, ProgressShare, SocialInteraction,
    FriendshipStatus, FeedbackType, RatingType, PrivacyLevel
)
from ..models.user import User
from .base_service import BaseService


class SocialService(BaseService):
    """Service for social learning features"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.social_repo = SocialRepository(session)
    
    # Friendship Management
    
    async def send_friend_request(
        self,
        requester_id: str,
        addressee_username: str,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a friend request to another user"""
        
        # Find addressee by username
        addressee = await self.social_repo.get_by_field(User, "username", addressee_username)
        if not addressee:
            raise ValueError("User not found")
        
        if requester_id == addressee.id:
            raise ValueError("Cannot send friend request to yourself")
        
        try:
            friendship = await self.social_repo.create_friendship_request(
                requester_id=requester_id,
                addressee_id=addressee.id,
                message=message
            )
            
            await self.session.commit()
            
            return {
                "success": True,
                "friendship_id": friendship.id,
                "message": f"Friend request sent to {addressee.username}"
            }
            
        except ValueError as e:
            await self.session.rollback()
            raise e
    
    async def respond_to_friend_request(
        self,
        friendship_id: str,
        user_id: str,
        accept: bool
    ) -> Dict[str, Any]:
        """Accept or decline a friend request"""
        
        try:
            response = FriendshipStatus.ACCEPTED if accept else FriendshipStatus.DECLINED
            
            friendship = await self.social_repo.respond_to_friendship(
                friendship_id=friendship_id,
                response=response,
                responder_id=user_id
            )
            
            await self.session.commit()
            
            action = "accepted" if accept else "declined"
            return {
                "success": True,
                "friendship_id": friendship.id,
                "status": friendship.status,
                "message": f"Friend request {action}"
            }
            
        except ValueError as e:
            await self.session.rollback()
            raise e
    
    async def get_friends_list(
        self,
        user_id: str,
        include_pending: bool = False
    ) -> Dict[str, Any]:
        """Get user's friends list with optional pending requests"""
        
        # Get accepted friends
        friends = await self.social_repo.get_user_friends(
            user_id=user_id,
            status=FriendshipStatus.ACCEPTED
        )
        
        result = {
            "friends": friends,
            "friends_count": len(friends)
        }
        
        if include_pending:
            # Get incoming requests
            incoming_requests = await self.social_repo.get_friendship_requests(
                user_id=user_id,
                incoming=True
            )
            
            # Get outgoing requests
            outgoing_requests = await self.social_repo.get_friendship_requests(
                user_id=user_id,
                incoming=False
            )
            
            result.update({
                "incoming_requests": [req.get_friendship_summary(user_id) for req in incoming_requests],
                "outgoing_requests": [req.get_friendship_summary(user_id) for req in outgoing_requests],
                "pending_incoming_count": len(incoming_requests),
                "pending_outgoing_count": len(outgoing_requests)
            })
        
        return result
    
    async def update_friendship_privacy(
        self,
        friendship_id: str,
        user_id: str,
        privacy_settings: Dict[str, bool]
    ) -> Dict[str, Any]:
        """Update privacy settings for a friendship"""
        
        try:
            friendship = await self.social_repo.update_friendship_settings(
                friendship_id=friendship_id,
                user_id=user_id,
                settings=privacy_settings
            )
            
            await self.session.commit()
            
            return {
                "success": True,
                "friendship_id": friendship.id,
                "updated_settings": privacy_settings
            }
            
        except ValueError as e:
            await self.session.rollback()
            raise e
    
    async def remove_friend(
        self,
        friendship_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Remove a friend (block the friendship)"""
        
        try:
            friendship = await self.social_repo.respond_to_friendship(
                friendship_id=friendship_id,
                response=FriendshipStatus.BLOCKED,
                responder_id=user_id
            )
            
            await self.session.commit()
            
            return {
                "success": True,
                "message": "Friend removed successfully"
            }
            
        except ValueError as e:
            await self.session.rollback()
            raise e
    
    # Community Feedback
    
    async def give_feedback(
        self,
        giver_id: str,
        receiver_username: str,
        feedback_type: str,
        content: str,
        session_id: Optional[str] = None,
        story_id: Optional[str] = None,
        sentence_index: Optional[int] = None,
        is_public: bool = False,
        is_anonymous: bool = False,
        tags: Optional[List[str]] = None,
        skill_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Give feedback to another user"""
        
        # Find receiver by username
        receiver = await self.social_repo.get_by_field(User, "username", receiver_username)
        if not receiver:
            raise ValueError("User not found")
        
        if giver_id == receiver.id:
            raise ValueError("Cannot give feedback to yourself")
        
        # Check if users are friends (for privacy)
        friends = await self.social_repo.get_user_friends(giver_id, FriendshipStatus.ACCEPTED)
        friend_ids = [friend["friend"]["id"] for friend in friends]
        
        if receiver.id not in friend_ids and not is_public:
            raise ValueError("Can only give private feedback to friends")
        
        try:
            feedback_type_enum = FeedbackType(feedback_type)
            
            feedback = await self.social_repo.create_feedback(
                giver_id=giver_id,
                receiver_id=receiver.id,
                feedback_type=feedback_type_enum,
                content=content,
                session_id=session_id,
                story_id=story_id,
                sentence_index=sentence_index,
                is_public=is_public,
                is_anonymous=is_anonymous,
                tags=tags,
                skill_areas=skill_areas
            )
            
            await self.session.commit()
            
            return {
                "success": True,
                "feedback_id": feedback.id,
                "message": f"Feedback given to {receiver.username}"
            }
            
        except ValueError as e:
            await self.session.rollback()
            raise e
    
    async def get_user_feedback(
        self,
        user_id: str,
        feedback_direction: str = "received",  # "received" or "given"
        feedback_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get feedback for a user"""
        
        received = feedback_direction == "received"
        feedback_type_enum = FeedbackType(feedback_type) if feedback_type else None
        
        feedback_list = await self.social_repo.get_user_feedback(
            user_id=user_id,
            received=received,
            feedback_type=feedback_type_enum,
            limit=limit,
            offset=offset
        )
        
        # Enrich with user information
        enriched_feedback = []
        for feedback in feedback_list:
            # Get giver/receiver info
            other_user_id = feedback.receiver_id if not received else feedback.giver_id
            other_user = await self.social_repo.get_by_id(User, other_user_id)
            
            if other_user:
                feedback_data = feedback.get_feedback_summary()
                feedback_data["other_user"] = {
                    "id": other_user.id,
                    "username": other_user.username if not feedback.is_anonymous else "Anonymous",
                    "first_name": other_user.first_name if not feedback.is_anonymous else None,
                    "last_name": other_user.last_name if not feedback.is_anonymous else None
                }
                enriched_feedback.append(feedback_data)
        
        return {
            "feedback": enriched_feedback,
            "total_count": len(enriched_feedback),
            "direction": feedback_direction,
            "feedback_type": feedback_type
        }
    
    async def rate_feedback_helpfulness(
        self,
        feedback_id: str,
        user_id: str,
        is_helpful: bool
    ) -> Dict[str, Any]:
        """Rate the helpfulness of feedback"""
        
        try:
            feedback = await self.social_repo.rate_feedback_helpfulness(
                feedback_id=feedback_id,
                user_id=user_id,
                is_helpful=is_helpful
            )
            
            await self.session.commit()
            
            return {
                "success": True,
                "feedback_id": feedback.id,
                "new_helpfulness_score": feedback.helpfulness_score,
                "total_votes": feedback.helpfulness_votes
            }
            
        except ValueError as e:
            await self.session.rollback()
            raise e
    
    # Community Ratings
    
    async def rate_content(
        self,
        user_id: str,
        rating_type: str,
        target_id: str,
        rating_value: float,
        review_text: Optional[str] = None,
        detailed_ratings: Optional[Dict[str, float]] = None,
        user_experience_level: Optional[str] = None,
        completion_percentage: Optional[float] = None
    ) -> Dict[str, Any]:
        """Rate content (story, session, etc.)"""
        
        if not (1.0 <= rating_value <= 5.0):
            raise ValueError("Rating value must be between 1 and 5")
        
        try:
            rating_type_enum = RatingType(rating_type)
            
            rating = await self.social_repo.create_rating(
                user_id=user_id,
                rating_type=rating_type_enum,
                target_id=target_id,
                rating_value=rating_value,
                review_text=review_text,
                difficulty_rating=detailed_ratings.get("difficulty") if detailed_ratings else None,
                clarity_rating=detailed_ratings.get("clarity") if detailed_ratings else None,
                engagement_rating=detailed_ratings.get("engagement") if detailed_ratings else None,
                educational_value_rating=detailed_ratings.get("educational_value") if detailed_ratings else None,
                user_experience_level=user_experience_level,
                completion_percentage=completion_percentage
            )
            
            await self.session.commit()
            
            return {
                "success": True,
                "rating_id": rating.id,
                "message": f"Rating submitted for {rating_type}"
            }
            
        except ValueError as e:
            await self.session.rollback()
            raise e
    
    async def get_content_ratings(
        self,
        rating_type: str,
        target_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get ratings for specific content"""
        
        rating_type_enum = RatingType(rating_type)
        
        ratings, stats = await self.social_repo.get_ratings_for_item(
            rating_type=rating_type_enum,
            target_id=target_id,
            limit=limit,
            offset=offset
        )
        
        # Enrich with user information
        enriched_ratings = []
        for rating in ratings:
            user = await self.social_repo.get_by_id(User, rating.user_id)
            if user:
                rating_data = rating.get_rating_summary()
                rating_data["user"] = {
                    "id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name
                }
                enriched_ratings.append(rating_data)
        
        return {
            "ratings": enriched_ratings,
            "statistics": stats,
            "rating_type": rating_type,
            "target_id": target_id
        }
    
    # Progress Sharing
    
    async def share_progress(
        self,
        user_id: str,
        share_type: str,
        title: str,
        description: Optional[str] = None,
        session_id: Optional[str] = None,
        progress_data: Optional[Dict[str, Any]] = None,
        achievement_type: Optional[str] = None,
        privacy_level: str = "friends",
        visible_to_groups: Optional[List[str]] = None,
        visible_to_friends: Optional[List[str]] = None,
        allow_comments: bool = True,
        allow_reactions: bool = True,
        expires_in_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Share learning progress with friends/community"""
        
        try:
            privacy_enum = PrivacyLevel(privacy_level)
            
            expires_at = None
            if expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            
            share = await self.social_repo.create_progress_share(
                user_id=user_id,
                share_type=share_type,
                title=title,
                description=description,
                session_id=session_id,
                progress_data=progress_data,
                achievement_type=achievement_type,
                privacy_level=privacy_enum,
                visible_to_groups=visible_to_groups,
                visible_to_friends=visible_to_friends,
                allow_comments=allow_comments,
                allow_reactions=allow_reactions,
                expires_at=expires_at
            )
            
            await self.session.commit()
            
            return {
                "success": True,
                "share_id": share.id,
                "message": "Progress shared successfully"
            }
            
        except ValueError as e:
            await self.session.rollback()
            raise e
    
    async def get_progress_feed(
        self,
        user_id: str,
        feed_type: str = "friends",  # "friends", "own", "public"
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get progress sharing feed"""
        
        if feed_type == "friends":
            shares = await self.social_repo.get_friends_progress_feed(
                user_id=user_id,
                limit=limit,
                offset=offset
            )
        elif feed_type == "own":
            share_objects = await self.social_repo.get_user_progress_shares(
                user_id=user_id,
                viewer_id=user_id,
                limit=limit,
                offset=offset
            )
            shares = []
            user = await self.social_repo.get_by_id(User, user_id)
            for share in share_objects:
                shares.append({
                    "share": share.get_share_summary(),
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "first_name": user.first_name,
                        "last_name": user.last_name
                    }
                })
        else:  # public
            # For public feed, we'd need to implement a more complex query
            # For now, return empty list
            shares = []
        
        return {
            "shares": shares,
            "feed_type": feed_type,
            "total_count": len(shares)
        }
    
    async def interact_with_share(
        self,
        user_id: str,
        share_id: str,
        interaction_type: str,
        content: Optional[str] = None,
        reaction_emoji: Optional[str] = None
    ) -> Dict[str, Any]:
        """Interact with a progress share (like, comment, react)"""
        
        # Verify share exists and is accessible
        share = await self.social_repo.get_by_id(ProgressShare, share_id)
        if not share:
            raise ValueError("Progress share not found")
        
        # Check if interaction is allowed
        if interaction_type == "comment" and not share.allow_comments:
            raise ValueError("Comments are not allowed on this share")
        
        if interaction_type == "reaction" and not share.allow_reactions:
            raise ValueError("Reactions are not allowed on this share")
        
        try:
            interaction = await self.social_repo.create_interaction(
                user_id=user_id,
                target_type="progress_share",
                target_id=share_id,
                interaction_type=interaction_type,
                content=content,
                reaction_emoji=reaction_emoji
            )
            
            await self.session.commit()
            
            return {
                "success": True,
                "interaction_id": interaction.id,
                "message": f"Successfully {interaction_type}d the share"
            }
            
        except ValueError as e:
            await self.session.rollback()
            raise e
    
    # Social Analytics and Discovery
    
    async def get_user_social_profile(
        self,
        user_id: str,
        viewer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive social profile for a user"""
        
        # Get basic user info
        user = await self.social_repo.get_by_id(User, user_id)
        if not user:
            raise ValueError("User not found")
        
        # Get social statistics
        social_stats = await self.social_repo.get_user_social_stats(user_id)
        
        # Get recent progress shares (public or friend-visible)
        recent_shares = await self.social_repo.get_user_progress_shares(
            user_id=user_id,
            viewer_id=viewer_id,
            limit=10,
            offset=0
        )
        
        # Check if viewer is friends with this user
        is_friend = False
        friendship_status = None
        if viewer_id and viewer_id != user_id:
            friends = await self.social_repo.get_user_friends(viewer_id, FriendshipStatus.ACCEPTED)
            friend_ids = [friend["friend"]["id"] for friend in friends]
            is_friend = user_id in friend_ids
            
            # Check for pending friendship
            if not is_friend:
                incoming_requests = await self.social_repo.get_friendship_requests(viewer_id, incoming=True)
                outgoing_requests = await self.social_repo.get_friendship_requests(viewer_id, incoming=False)
                
                for req in incoming_requests:
                    if req.requester_id == user_id:
                        friendship_status = "incoming_request"
                        break
                
                for req in outgoing_requests:
                    if req.addressee_id == user_id:
                        friendship_status = "outgoing_request"
                        break
        
        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.get_full_name()
            },
            "social_stats": social_stats,
            "recent_shares": [share.get_share_summary() for share in recent_shares],
            "relationship": {
                "is_friend": is_friend,
                "friendship_status": friendship_status,
                "can_send_friend_request": viewer_id != user_id and not is_friend and friendship_status is None
            }
        }
    
    async def search_users(
        self,
        query: str,
        searcher_id: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Search for users to connect with"""
        
        # Simple username/name search
        users = await self.social_repo.search_users_by_name(query, limit)
        
        # Get searcher's friends to mark existing relationships
        friends = await self.social_repo.get_user_friends(searcher_id, FriendshipStatus.ACCEPTED)
        friend_ids = {friend["friend"]["id"] for friend in friends}
        
        # Get pending requests
        incoming_requests = await self.social_repo.get_friendship_requests(searcher_id, incoming=True)
        outgoing_requests = await self.social_repo.get_friendship_requests(searcher_id, incoming=False)
        
        incoming_ids = {req.requester_id for req in incoming_requests}
        outgoing_ids = {req.addressee_id for req in outgoing_requests}
        
        # Enrich results with relationship status
        enriched_users = []
        for user in users:
            if user.id == searcher_id:
                continue  # Skip self
            
            relationship_status = "none"
            if user.id in friend_ids:
                relationship_status = "friend"
            elif user.id in incoming_ids:
                relationship_status = "incoming_request"
            elif user.id in outgoing_ids:
                relationship_status = "outgoing_request"
            
            enriched_users.append({
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "full_name": user.get_full_name(),
                "relationship_status": relationship_status
            })
        
        return {
            "users": enriched_users,
            "query": query,
            "total_found": len(enriched_users)
        }
    
    async def get_community_leaderboard(
        self,
        metric: str = "progress_shares",  # "progress_shares", "feedback_given", "helpful_ratings"
        time_period: str = "month",  # "week", "month", "all_time"
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get community leaderboard for social engagement"""
        
        # Calculate date range
        end_date = datetime.utcnow()
        if time_period == "week":
            start_date = end_date - timedelta(weeks=1)
        elif time_period == "month":
            start_date = end_date - timedelta(days=30)
        else:  # all_time
            start_date = None
        
        leaderboard = await self.social_repo.get_community_leaderboard(
            metric=metric,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return {
            "leaderboard": leaderboard,
            "metric": metric,
            "time_period": time_period,
            "generated_at": datetime.utcnow().isoformat()
        }