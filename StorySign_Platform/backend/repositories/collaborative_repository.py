"""
Repository layer for collaborative learning features
Handles database operations for groups, memberships, and collaborative sessions
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from repositories.base_repository import BaseRepository
from models.collaborative import (
    LearningGroup, GroupMembership, CollaborativeSession, GroupAnalytics,
    GroupRole, GroupPrivacy, SessionStatus, DataSharingLevel
)
from models.user import User
from models.progress import PracticeSession, UserProgress


class LearningGroupRepository(BaseRepository[LearningGroup]):
    """Repository for learning group operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, LearningGroup)
    
    async def create_group(
        self,
        name: str,
        creator_id: str,
        description: str = None,
        privacy_level: str = GroupPrivacy.PRIVATE.value,
        **kwargs
    ) -> LearningGroup:
        """Create a new learning group"""
        group_data = {
            "name": name,
            "creator_id": creator_id,
            "description": description,
            "privacy_level": privacy_level,
            **kwargs
        }
        
        group = await self.create(group_data)
        
        # Automatically create owner membership for creator
        membership_repo = GroupMembershipRepository(self.session)
        await membership_repo.create_membership(
            group_id=group.id,
            user_id=creator_id,
            role=GroupRole.OWNER.value
        )
        
        return group
    
    async def get_groups_by_creator(self, creator_id: str) -> List[LearningGroup]:
        """Get all groups created by a specific user"""
        return await self.find_many(
            filters={"creator_id": creator_id, "is_active": True},
            order_by=[desc(LearningGroup.created_at)]
        )
    
    async def get_public_groups(
        self,
        limit: int = 50,
        offset: int = 0,
        search_term: str = None
    ) -> List[LearningGroup]:
        """Get public groups with optional search"""
        filters = {
            "is_public": True,
            "is_active": True,
            "privacy_level": GroupPrivacy.PUBLIC.value
        }
        
        if search_term:
            # This would need to be implemented with proper text search
            # For now, we'll use a simple name filter
            query = self.session.query(LearningGroup).filter(
                and_(
                    LearningGroup.is_public == True,
                    LearningGroup.is_active == True,
                    LearningGroup.privacy_level == GroupPrivacy.PUBLIC.value,
                    or_(
                        LearningGroup.name.ilike(f"%{search_term}%"),
                        LearningGroup.description.ilike(f"%{search_term}%")
                    )
                )
            ).order_by(desc(LearningGroup.last_activity_at))
            
            return query.offset(offset).limit(limit).all()
        
        return await self.find_many(
            filters=filters,
            limit=limit,
            offset=offset,
            order_by=[desc(LearningGroup.last_activity_at)]
        )
    
    async def get_group_by_join_code(self, join_code: str) -> Optional[LearningGroup]:
        """Get group by join code"""
        return await self.find_one({"join_code": join_code, "is_active": True})
    
    async def get_groups_by_skill_focus(
        self,
        skill_areas: List[str],
        difficulty_level: str = None
    ) -> List[LearningGroup]:
        """Get groups that focus on specific skill areas"""
        # This would need custom SQL for JSON array matching
        # For now, return empty list - would need proper implementation
        return []
    
    async def update_group_activity(self, group_id: str) -> None:
        """Update group's last activity timestamp"""
        await self.update(group_id, {"last_activity_at": datetime.utcnow()})
    
    async def get_group_with_members(self, group_id: str) -> Optional[LearningGroup]:
        """Get group with all member information loaded"""
        query = self.session.query(LearningGroup).options(
            selectinload(LearningGroup.memberships).selectinload(GroupMembership.user)
        ).filter(LearningGroup.id == group_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class GroupMembershipRepository(BaseRepository[GroupMembership]):
    """Repository for group membership operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, GroupMembership)
    
    async def create_membership(
        self,
        group_id: str,
        user_id: str,
        role: str = GroupRole.MEMBER.value,
        invited_by: str = None,
        **kwargs
    ) -> GroupMembership:
        """Create a new group membership"""
        membership_data = {
            "group_id": group_id,
            "user_id": user_id,
            "role": role,
            "invited_by": invited_by,
            **kwargs
        }
        
        return await self.create(membership_data)
    
    async def get_user_memberships(
        self,
        user_id: str,
        active_only: bool = True
    ) -> List[GroupMembership]:
        """Get all memberships for a user"""
        filters = {"user_id": user_id}
        if active_only:
            filters["is_active"] = True
        
        return await self.find_many(
            filters=filters,
            order_by=[desc(GroupMembership.joined_at)],
            options=[joinedload(GroupMembership.group)]
        )
    
    async def get_group_members(
        self,
        group_id: str,
        active_only: bool = True,
        role: str = None
    ) -> List[GroupMembership]:
        """Get all members of a group"""
        filters = {"group_id": group_id}
        if active_only:
            filters["is_active"] = True
        if role:
            filters["role"] = role
        
        return await self.find_many(
            filters=filters,
            order_by=[asc(GroupMembership.joined_at)],
            options=[joinedload(GroupMembership.user)]
        )
    
    async def get_membership(
        self,
        group_id: str,
        user_id: str
    ) -> Optional[GroupMembership]:
        """Get specific membership"""
        return await self.find_one({
            "group_id": group_id,
            "user_id": user_id
        })
    
    async def update_membership_role(
        self,
        group_id: str,
        user_id: str,
        new_role: str,
        updated_by: str = None
    ) -> Optional[GroupMembership]:
        """Update member role"""
        membership = await self.get_membership(group_id, user_id)
        if membership:
            update_data = {"role": new_role}
            if updated_by:
                update_data["approved_by"] = updated_by
                update_data["approved_at"] = datetime.utcnow()
            
            return await self.update(membership.id, update_data)
        return None
    
    async def leave_group(self, group_id: str, user_id: str) -> bool:
        """Mark membership as inactive (user leaves group)"""
        membership = await self.get_membership(group_id, user_id)
        if membership and membership.is_active:
            await self.update(membership.id, {
                "is_active": False,
                "left_at": datetime.utcnow()
            })
            return True
        return False
    
    async def get_members_with_data_sharing(
        self,
        group_id: str,
        sharing_level: str = None
    ) -> List[GroupMembership]:
        """Get members who allow data sharing at specified level"""
        filters = {
            "group_id": group_id,
            "is_active": True
        }
        
        if sharing_level:
            filters["data_sharing_level"] = sharing_level
        
        # Additional filter for members who share progress
        query = self.session.query(GroupMembership).filter(
            and_(
                GroupMembership.group_id == group_id,
                GroupMembership.is_active == True,
                GroupMembership.share_progress == True
            )
        )
        
        if sharing_level:
            query = query.filter(GroupMembership.data_sharing_level == sharing_level)
        
        result = await self.session.execute(query)
        return result.scalars().all()


class CollaborativeSessionRepository(BaseRepository[CollaborativeSession]):
    """Repository for collaborative session operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, CollaborativeSession)
    
    async def create_session(
        self,
        session_name: str,
        host_id: str,
        group_id: str,
        **kwargs
    ) -> CollaborativeSession:
        """Create a new collaborative session"""
        session_data = {
            "session_name": session_name,
            "host_id": host_id,
            "group_id": group_id,
            **kwargs
        }
        
        return await self.create(session_data)
    
    async def get_group_sessions(
        self,
        group_id: str,
        status: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[CollaborativeSession]:
        """Get sessions for a specific group"""
        filters = {"group_id": group_id}
        if status:
            filters["status"] = status
        
        return await self.find_many(
            filters=filters,
            limit=limit,
            offset=offset,
            order_by=[desc(CollaborativeSession.scheduled_start)]
        )
    
    async def get_user_sessions(
        self,
        user_id: str,
        status: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[CollaborativeSession]:
        """Get sessions where user is host or participant"""
        # This requires custom query to check both host_id and participant_ids JSON
        query = self.session.query(CollaborativeSession).filter(
            or_(
                CollaborativeSession.host_id == user_id,
                CollaborativeSession.participant_ids.contains([user_id])
            )
        )
        
        if status:
            query = query.filter(CollaborativeSession.status == status)
        
        query = query.order_by(desc(CollaborativeSession.scheduled_start))
        
        result = await self.session.execute(query.offset(offset).limit(limit))
        return result.scalars().all()
    
    async def get_upcoming_sessions(
        self,
        group_id: str = None,
        hours_ahead: int = 24
    ) -> List[CollaborativeSession]:
        """Get upcoming sessions within specified time window"""
        now = datetime.utcnow()
        future_time = now + timedelta(hours=hours_ahead)
        
        filters = {
            "status": SessionStatus.SCHEDULED.value
        }
        
        query = self.session.query(CollaborativeSession).filter(
            and_(
                CollaborativeSession.status == SessionStatus.SCHEDULED.value,
                CollaborativeSession.scheduled_start >= now,
                CollaborativeSession.scheduled_start <= future_time
            )
        )
        
        if group_id:
            query = query.filter(CollaborativeSession.group_id == group_id)
        
        query = query.order_by(asc(CollaborativeSession.scheduled_start))
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def start_session(self, session_id: str) -> Optional[CollaborativeSession]:
        """Start a collaborative session"""
        return await self.update(session_id, {
            "status": SessionStatus.ACTIVE.value,
            "actual_start": datetime.utcnow()
        })
    
    async def end_session(
        self,
        session_id: str,
        performance_summary: Dict[str, Any] = None
    ) -> Optional[CollaborativeSession]:
        """End a collaborative session"""
        update_data = {
            "status": SessionStatus.COMPLETED.value,
            "actual_end": datetime.utcnow()
        }
        
        if performance_summary:
            update_data["performance_summary"] = performance_summary
        
        return await self.update(session_id, update_data)
    
    async def add_participant(self, session_id: str, user_id: str) -> bool:
        """Add participant to session"""
        session = await self.get_by_id(session_id)
        if session and session.can_accept_participants():
            if session.add_participant(user_id):
                await self.session.commit()
                return True
        return False
    
    async def remove_participant(self, session_id: str, user_id: str) -> bool:
        """Remove participant from session"""
        session = await self.get_by_id(session_id)
        if session and session.remove_participant(user_id):
            await self.session.commit()
            return True
        return False


class GroupAnalyticsRepository(BaseRepository[GroupAnalytics]):
    """Repository for group analytics operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, GroupAnalytics)
    
    async def create_analytics_record(
        self,
        group_id: str,
        period_start: datetime,
        period_end: datetime,
        period_type: str = "weekly"
    ) -> GroupAnalytics:
        """Create a new analytics record for a group"""
        analytics_data = {
            "group_id": group_id,
            "period_start": period_start,
            "period_end": period_end,
            "period_type": period_type
        }
        
        return await self.create(analytics_data)
    
    async def get_group_analytics(
        self,
        group_id: str,
        period_type: str = None,
        limit: int = 12
    ) -> List[GroupAnalytics]:
        """Get analytics records for a group"""
        filters = {"group_id": group_id}
        if period_type:
            filters["period_type"] = period_type
        
        return await self.find_many(
            filters=filters,
            limit=limit,
            order_by=[desc(GroupAnalytics.period_start)]
        )
    
    async def get_latest_analytics(
        self,
        group_id: str,
        period_type: str = "weekly"
    ) -> Optional[GroupAnalytics]:
        """Get the most recent analytics record for a group"""
        return await self.find_one(
            filters={"group_id": group_id, "period_type": period_type},
            order_by=[desc(GroupAnalytics.period_start)]
        )
    
    async def calculate_group_metrics(
        self,
        group_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, Any]:
        """Calculate aggregated metrics for a group period"""
        # Get active memberships during period
        memberships = await self.session.execute(
            self.session.query(GroupMembership).filter(
                and_(
                    GroupMembership.group_id == group_id,
                    GroupMembership.is_active == True,
                    GroupMembership.joined_at <= period_end
                )
            )
        )
        memberships = memberships.scalars().all()
        
        # Get practice sessions during period
        user_ids = [m.user_id for m in memberships if m.share_progress]
        
        if not user_ids:
            return {
                "total_members": len(memberships),
                "active_members": 0,
                "total_sessions": 0,
                "collaborative_sessions": 0,
                "total_practice_time": 0,
                "average_group_score": None,
                "average_completion_rate": None
            }
        
        # Query practice sessions
        sessions_query = self.session.query(PracticeSession).filter(
            and_(
                PracticeSession.user_id.in_(user_ids),
                PracticeSession.started_at >= period_start,
                PracticeSession.started_at <= period_end
            )
        )
        
        sessions_result = await self.session.execute(sessions_query)
        sessions = sessions_result.scalars().all()
        
        # Query collaborative sessions
        collab_sessions_query = self.session.query(CollaborativeSession).filter(
            and_(
                CollaborativeSession.group_id == group_id,
                CollaborativeSession.actual_start >= period_start,
                CollaborativeSession.actual_start <= period_end
            )
        )
        
        collab_sessions_result = await self.session.execute(collab_sessions_query)
        collab_sessions = collab_sessions_result.scalars().all()
        
        # Calculate metrics
        active_users = set(session.user_id for session in sessions)
        total_practice_time = sum(
            session.duration_seconds or 0 for session in sessions
        ) // 60  # Convert to minutes
        
        scores = [session.overall_score for session in sessions if session.overall_score]
        avg_score = sum(scores) / len(scores) if scores else None
        
        completed_sessions = [s for s in sessions if s.status == "completed"]
        completion_rate = len(completed_sessions) / len(sessions) if sessions else None
        
        return {
            "total_members": len(memberships),
            "active_members": len(active_users),
            "total_sessions": len(sessions),
            "collaborative_sessions": len(collab_sessions),
            "total_practice_time": total_practice_time,
            "average_group_score": avg_score,
            "average_completion_rate": completion_rate,
            "peer_feedback_count": 0,  # Would need to implement peer feedback tracking
            "group_interactions": 0,   # Would need to implement interaction tracking
        }
    
    async def update_analytics_with_metrics(
        self,
        analytics_id: str,
        metrics: Dict[str, Any]
    ) -> Optional[GroupAnalytics]:
        """Update analytics record with calculated metrics"""
        return await self.update(analytics_id, metrics)