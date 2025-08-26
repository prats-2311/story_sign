"""
Service layer for collaborative learning features
Handles business logic for groups, memberships, and collaborative sessions
"""

import secrets
import string
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.collaborative_repository import (
    LearningGroupRepository, GroupMembershipRepository,
    CollaborativeSessionRepository, GroupAnalyticsRepository
)
from repositories.user_repository import UserRepository
from repositories.progress_repository import ProgressRepository
from models.collaborative import (
    LearningGroup, GroupMembership, CollaborativeSession, GroupAnalytics,
    GroupRole, GroupPrivacy, SessionStatus, DataSharingLevel
)
from models.user import User


class CollaborativeService:
    """Service for managing collaborative learning features"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.group_repo = LearningGroupRepository(session)
        self.membership_repo = GroupMembershipRepository(session)
        self.session_repo = CollaborativeSessionRepository(session)
        self.analytics_repo = GroupAnalyticsRepository(session)
        self.user_repo = UserRepository(session)
        self.progress_repo = ProgressRepository(session)
    
    # Learning Group Management
    
    async def create_learning_group(
        self,
        creator_id: str,
        name: str,
        description: str = None,
        privacy_level: str = GroupPrivacy.PRIVATE.value,
        max_members: int = None,
        skill_focus: List[str] = None,
        difficulty_level: str = None,
        **kwargs
    ) -> Tuple[LearningGroup, str]:
        """
        Create a new learning group
        
        Returns:
            Tuple of (group, error_message). Error message is None on success.
        """
        try:
            # Validate creator exists
            creator = await self.user_repo.get_by_id(creator_id)
            if not creator:
                return None, "Creator user not found"
            
            # Create group
            group_data = {
                "name": name,
                "description": description,
                "privacy_level": privacy_level,
                "max_members": max_members,
                "skill_focus": skill_focus or [],
                "difficulty_level": difficulty_level,
                **kwargs
            }
            
            group = await self.group_repo.create_group(
                name=name,
                creator_id=creator_id,
                **group_data
            )
            
            # Generate join code if needed
            if privacy_level in [GroupPrivacy.INVITE_ONLY.value, GroupPrivacy.PRIVATE.value]:
                group.generate_join_code()
                await self.session.commit()
            
            return group, None
            
        except Exception as e:
            await self.session.rollback()
            return None, f"Failed to create group: {str(e)}"
    
    async def get_user_groups(
        self,
        user_id: str,
        include_created: bool = True,
        include_joined: bool = True
    ) -> List[Dict[str, Any]]:
        """Get all groups associated with a user"""
        groups = []
        
        if include_created:
            created_groups = await self.group_repo.get_groups_by_creator(user_id)
            for group in created_groups:
                groups.append({
                    **group.get_group_summary(),
                    "user_role": GroupRole.OWNER.value,
                    "relationship": "creator"
                })
        
        if include_joined:
            memberships = await self.membership_repo.get_user_memberships(user_id)
            for membership in memberships:
                if membership.group.creator_id != user_id:  # Avoid duplicates
                    groups.append({
                        **membership.group.get_group_summary(),
                        "user_role": membership.role,
                        "relationship": "member",
                        "joined_at": membership.joined_at.isoformat() if membership.joined_at else None,
                        "data_sharing_level": membership.data_sharing_level
                    })
        
        return groups
    
    async def join_group(
        self,
        user_id: str,
        group_id: str = None,
        join_code: str = None,
        invited_by: str = None
    ) -> Tuple[GroupMembership, str]:
        """
        Join a learning group by ID or join code
        
        Returns:
            Tuple of (membership, error_message). Error message is None on success.
        """
        try:
            # Find group
            if join_code:
                group = await self.group_repo.get_group_by_join_code(join_code)
                if not group:
                    return None, "Invalid join code"
            elif group_id:
                group = await self.group_repo.get_by_id(group_id)
                if not group:
                    return None, "Group not found"
            else:
                return None, "Must provide either group_id or join_code"
            
            # Check if user exists
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                return None, "User not found"
            
            # Check if already a member
            existing_membership = await self.membership_repo.get_membership(group.id, user_id)
            if existing_membership and existing_membership.is_active:
                return None, "Already a member of this group"
            
            # Check if group can accept new members
            if not group.can_accept_new_members():
                return None, "Group is full or not accepting new members"
            
            # Create membership
            membership = await self.membership_repo.create_membership(
                group_id=group.id,
                user_id=user_id,
                role=GroupRole.MEMBER.value,
                invited_by=invited_by
            )
            
            # Update group activity
            await self.group_repo.update_group_activity(group.id)
            
            await self.session.commit()
            return membership, None
            
        except Exception as e:
            await self.session.rollback()
            return None, f"Failed to join group: {str(e)}"
    
    async def leave_group(self, user_id: str, group_id: str) -> Tuple[bool, str]:
        """
        Leave a learning group
        
        Returns:
            Tuple of (success, error_message). Error message is None on success.
        """
        try:
            # Check if user is group owner
            group = await self.group_repo.get_by_id(group_id)
            if not group:
                return False, "Group not found"
            
            if group.creator_id == user_id:
                return False, "Group owner cannot leave group. Transfer ownership or delete group instead."
            
            # Leave group
            success = await self.membership_repo.leave_group(group_id, user_id)
            if not success:
                return False, "Not a member of this group or already left"
            
            await self.session.commit()
            return True, None
            
        except Exception as e:
            await self.session.rollback()
            return False, f"Failed to leave group: {str(e)}"
    
    async def update_member_role(
        self,
        group_id: str,
        user_id: str,
        new_role: str,
        updated_by: str
    ) -> Tuple[GroupMembership, str]:
        """Update a member's role in the group"""
        try:
            # Check if updater has permission
            updater_membership = await self.membership_repo.get_membership(group_id, updated_by)
            if not updater_membership or not updater_membership.has_permission("manage_members"):
                return None, "Insufficient permissions to update member roles"
            
            # Update role
            membership = await self.membership_repo.update_membership_role(
                group_id, user_id, new_role, updated_by
            )
            
            if not membership:
                return None, "Member not found in group"
            
            await self.session.commit()
            return membership, None
            
        except Exception as e:
            await self.session.rollback()
            return None, f"Failed to update member role: {str(e)}"
    
    # Privacy and Data Sharing
    
    async def update_privacy_settings(
        self,
        user_id: str,
        group_id: str,
        privacy_settings: Dict[str, Any]
    ) -> Tuple[GroupMembership, str]:
        """Update user's privacy settings for a group"""
        try:
            membership = await self.membership_repo.get_membership(group_id, user_id)
            if not membership:
                return None, "Not a member of this group"
            
            # Update privacy settings
            update_data = {}
            for key, value in privacy_settings.items():
                if key in [
                    "data_sharing_level", "share_progress", "share_performance",
                    "share_practice_sessions", "allow_peer_feedback"
                ]:
                    update_data[key] = value
            
            if update_data:
                membership = await self.membership_repo.update(membership.id, update_data)
                await self.session.commit()
            
            return membership, None
            
        except Exception as e:
            await self.session.rollback()
            return None, f"Failed to update privacy settings: {str(e)}"
    
    async def get_shared_member_data(
        self,
        group_id: str,
        requesting_user_id: str
    ) -> List[Dict[str, Any]]:
        """Get member data that can be shared based on privacy settings"""
        try:
            # Check if requesting user is a member
            requester_membership = await self.membership_repo.get_membership(group_id, requesting_user_id)
            if not requester_membership or not requester_membership.is_active:
                return []
            
            # Get members who allow data sharing
            sharing_members = await self.membership_repo.get_members_with_data_sharing(group_id)
            
            shared_data = []
            for membership in sharing_members:
                if membership.user_id == requesting_user_id:
                    continue  # Skip self
                
                # Get shared data fields based on privacy settings
                shared_fields = membership.get_shared_data_fields()
                
                if not shared_fields:
                    continue
                
                # Get user progress data
                user_progress = await self.progress_repo.get_user_progress_summary(membership.user_id)
                
                # Filter data based on sharing permissions
                member_data = {
                    "user_id": membership.user_id,
                    "username": membership.user.username if membership.user else "Unknown",
                    "role": membership.role,
                    "joined_at": membership.joined_at.isoformat() if membership.joined_at else None
                }
                
                # Add shared progress data
                for field in shared_fields:
                    if field in user_progress:
                        member_data[field] = user_progress[field]
                
                shared_data.append(member_data)
            
            return shared_data
            
        except Exception as e:
            return []
    
    # Collaborative Sessions
    
    async def create_collaborative_session(
        self,
        host_id: str,
        group_id: str,
        session_name: str,
        description: str = None,
        story_id: str = None,
        scheduled_start: datetime = None,
        scheduled_end: datetime = None,
        **kwargs
    ) -> Tuple[CollaborativeSession, str]:
        """Create a new collaborative session"""
        try:
            # Verify host is a member of the group
            membership = await self.membership_repo.get_membership(group_id, host_id)
            if not membership or not membership.is_active:
                return None, "Host must be a member of the group"
            
            # Check if host has permission to create sessions
            if not membership.has_permission("manage_sessions"):
                return None, "Insufficient permissions to create sessions"
            
            # Create session
            session_data = {
                "session_name": session_name,
                "description": description,
                "story_id": story_id,
                "scheduled_start": scheduled_start,
                "scheduled_end": scheduled_end,
                **kwargs
            }
            
            session = await self.session_repo.create_session(
                session_name=session_name,
                host_id=host_id,
                group_id=group_id,
                **session_data
            )
            
            # Update group activity
            await self.group_repo.update_group_activity(group_id)
            
            await self.session.commit()
            return session, None
            
        except Exception as e:
            await self.session.rollback()
            return None, f"Failed to create session: {str(e)}"
    
    async def join_collaborative_session(
        self,
        session_id: str,
        user_id: str
    ) -> Tuple[bool, str]:
        """Join a collaborative session"""
        try:
            session = await self.session_repo.get_by_id(session_id)
            if not session:
                return False, "Session not found"
            
            # Check if user is a member of the group
            membership = await self.membership_repo.get_membership(session.group_id, user_id)
            if not membership or not membership.is_active:
                return False, "Must be a group member to join session"
            
            # Add participant
            success = await self.session_repo.add_participant(session_id, user_id)
            if not success:
                return False, "Cannot join session (may be full or not accepting participants)"
            
            return True, None
            
        except Exception as e:
            await self.session.rollback()
            return False, f"Failed to join session: {str(e)}"
    
    async def start_collaborative_session(
        self,
        session_id: str,
        host_id: str
    ) -> Tuple[CollaborativeSession, str]:
        """Start a collaborative session"""
        try:
            session = await self.session_repo.get_by_id(session_id)
            if not session:
                return None, "Session not found"
            
            if session.host_id != host_id:
                return None, "Only the session host can start the session"
            
            if session.status != SessionStatus.SCHEDULED.value:
                return None, f"Cannot start session with status: {session.status}"
            
            # Start session
            session = await self.session_repo.start_session(session_id)
            await self.session.commit()
            
            return session, None
            
        except Exception as e:
            await self.session.rollback()
            return None, f"Failed to start session: {str(e)}"
    
    async def end_collaborative_session(
        self,
        session_id: str,
        host_id: str,
        performance_summary: Dict[str, Any] = None
    ) -> Tuple[CollaborativeSession, str]:
        """End a collaborative session"""
        try:
            session = await self.session_repo.get_by_id(session_id)
            if not session:
                return None, "Session not found"
            
            if session.host_id != host_id:
                return None, "Only the session host can end the session"
            
            if session.status != SessionStatus.ACTIVE.value:
                return None, f"Cannot end session with status: {session.status}"
            
            # End session
            session = await self.session_repo.end_session(session_id, performance_summary)
            
            # Update group activity
            await self.group_repo.update_group_activity(session.group_id)
            
            await self.session.commit()
            return session, None
            
        except Exception as e:
            await self.session.rollback()
            return None, f"Failed to end session: {str(e)}"
    
    # Group Analytics
    
    async def generate_group_analytics(
        self,
        group_id: str,
        period_type: str = "weekly"
    ) -> Tuple[GroupAnalytics, str]:
        """Generate analytics for a group"""
        try:
            # Calculate period dates
            now = datetime.utcnow()
            if period_type == "daily":
                period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                period_end = period_start + timedelta(days=1)
            elif period_type == "weekly":
                days_since_monday = now.weekday()
                period_start = (now - timedelta(days=days_since_monday)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                period_end = period_start + timedelta(days=7)
            elif period_type == "monthly":
                period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                next_month = period_start.replace(month=period_start.month + 1) if period_start.month < 12 else period_start.replace(year=period_start.year + 1, month=1)
                period_end = next_month
            else:
                return None, "Invalid period type"
            
            # Check if analytics already exist for this period
            existing_analytics = await self.analytics_repo.find_one({
                "group_id": group_id,
                "period_start": period_start,
                "period_end": period_end,
                "period_type": period_type
            })
            
            if existing_analytics:
                return existing_analytics, None
            
            # Calculate metrics
            metrics = await self.analytics_repo.calculate_group_metrics(
                group_id, period_start, period_end
            )
            
            # Create analytics record
            analytics = await self.analytics_repo.create_analytics_record(
                group_id, period_start, period_end, period_type
            )
            
            # Update with calculated metrics
            analytics = await self.analytics_repo.update_analytics_with_metrics(
                analytics.id, metrics
            )
            
            await self.session.commit()
            return analytics, None
            
        except Exception as e:
            await self.session.rollback()
            return None, f"Failed to generate analytics: {str(e)}"
    
    async def get_group_analytics_summary(
        self,
        group_id: str,
        requesting_user_id: str,
        period_type: str = "weekly",
        limit: int = 12
    ) -> Tuple[List[Dict[str, Any]], str]:
        """Get analytics summary for a group"""
        try:
            # Check if requesting user has permission to view analytics
            membership = await self.membership_repo.get_membership(group_id, requesting_user_id)
            if not membership or not membership.is_active:
                return [], "Not a member of this group"
            
            # Only educators, moderators, and owners can view detailed analytics
            if membership.role not in [GroupRole.OWNER.value, GroupRole.EDUCATOR.value, GroupRole.MODERATOR.value]:
                return [], "Insufficient permissions to view group analytics"
            
            # Get analytics records
            analytics_records = await self.analytics_repo.get_group_analytics(
                group_id, period_type, limit
            )
            
            # Convert to summary format
            analytics_summary = [
                record.get_analytics_summary() for record in analytics_records
            ]
            
            return analytics_summary, None
            
        except Exception as e:
            return [], f"Failed to get analytics: {str(e)}"
    
    # Utility Methods
    
    async def search_public_groups(
        self,
        search_term: str = None,
        skill_areas: List[str] = None,
        difficulty_level: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Search for public groups"""
        try:
            groups = await self.group_repo.get_public_groups(limit, offset, search_term)
            
            # Filter by additional criteria if provided
            filtered_groups = []
            for group in groups:
                if skill_areas and group.skill_focus:
                    if not any(skill in group.skill_focus for skill in skill_areas):
                        continue
                
                if difficulty_level and group.difficulty_level != difficulty_level:
                    continue
                
                filtered_groups.append(group.get_group_summary())
            
            return filtered_groups
            
        except Exception as e:
            return []
    
    async def get_upcoming_sessions_for_user(
        self,
        user_id: str,
        hours_ahead: int = 24
    ) -> List[Dict[str, Any]]:
        """Get upcoming sessions for a user"""
        try:
            sessions = await self.session_repo.get_user_sessions(
                user_id, SessionStatus.SCHEDULED.value
            )
            
            # Filter for upcoming sessions
            now = datetime.utcnow()
            future_time = now + timedelta(hours=hours_ahead)
            
            upcoming_sessions = []
            for session in sessions:
                if (session.scheduled_start and 
                    now <= session.scheduled_start <= future_time):
                    upcoming_sessions.append(session.get_session_summary())
            
            return upcoming_sessions
            
        except Exception as e:
            return []