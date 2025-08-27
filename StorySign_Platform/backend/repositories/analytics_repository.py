"""
Analytics Repository
Handles database operations for analytics events, user consent, and data aggregation
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc, text
from sqlalchemy.orm import selectinload
from repositories.base_repository import BaseRepository
from models.analytics import (
    AnalyticsEvent, UserConsent, AnalyticsAggregation, 
    DataRetentionPolicy, AnalyticsSession, ConsentType, EventType
)
import logging

logger = logging.getLogger(__name__)


class AnalyticsRepository(BaseRepository):
    """Repository for analytics data operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.model = AnalyticsEvent

    async def create_event(
        self,
        user_id: Optional[str],
        session_id: str,
        event_type: str,
        module_name: str,
        event_data: Dict[str, Any],
        is_anonymous: bool = False,
        consent_version: Optional[str] = None,
        processing_time_ms: Optional[float] = None
    ) -> AnalyticsEvent:
        """Create a new analytics event"""
        try:
            event = AnalyticsEvent(
                user_id=user_id if not is_anonymous else None,
                session_id=session_id,
                event_type=event_type,
                module_name=module_name,
                event_data=event_data,
                is_anonymous=is_anonymous,
                consent_version=consent_version,
                processing_time_ms=processing_time_ms,
                occurred_at=datetime.utcnow()
            )
            
            self.session.add(event)
            await self.session.commit()
            await self.session.refresh(event)
            
            logger.info(f"Created analytics event: {event_type} for session {session_id}")
            return event
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating analytics event: {str(e)}")
            raise

    async def get_events_by_user(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[str]] = None,
        module_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AnalyticsEvent]:
        """Get analytics events for a specific user"""
        try:
            query = select(AnalyticsEvent).where(AnalyticsEvent.user_id == user_id)
            
            if start_date:
                query = query.where(AnalyticsEvent.occurred_at >= start_date)
            if end_date:
                query = query.where(AnalyticsEvent.occurred_at <= end_date)
            if event_types:
                query = query.where(AnalyticsEvent.event_type.in_(event_types))
            if module_name:
                query = query.where(AnalyticsEvent.module_name == module_name)
            
            query = query.order_by(desc(AnalyticsEvent.occurred_at))
            query = query.offset(offset).limit(limit)
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting events for user {user_id}: {str(e)}")
            raise

    async def get_events_by_session(
        self,
        session_id: str,
        event_types: Optional[List[str]] = None
    ) -> List[AnalyticsEvent]:
        """Get all events for a specific session"""
        try:
            query = select(AnalyticsEvent).where(AnalyticsEvent.session_id == session_id)
            
            if event_types:
                query = query.where(AnalyticsEvent.event_type.in_(event_types))
            
            query = query.order_by(asc(AnalyticsEvent.occurred_at))
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting events for session {session_id}: {str(e)}")
            raise

    async def get_aggregated_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        module_name: Optional[str] = None,
        event_types: Optional[List[str]] = None,
        include_anonymous: bool = True
    ) -> Dict[str, Any]:
        """Get aggregated analytics metrics for a time period"""
        try:
            query = select(AnalyticsEvent).where(
                and_(
                    AnalyticsEvent.occurred_at >= start_date,
                    AnalyticsEvent.occurred_at <= end_date
                )
            )
            
            if module_name:
                query = query.where(AnalyticsEvent.module_name == module_name)
            if event_types:
                query = query.where(AnalyticsEvent.event_type.in_(event_types))
            if not include_anonymous:
                query = query.where(AnalyticsEvent.is_anonymous == False)
            
            # Get basic counts
            total_events_query = select(func.count(AnalyticsEvent.id)).select_from(query.subquery())
            unique_users_query = select(func.count(func.distinct(AnalyticsEvent.user_id))).select_from(
                query.where(AnalyticsEvent.user_id.isnot(None)).subquery()
            )
            unique_sessions_query = select(func.count(func.distinct(AnalyticsEvent.session_id))).select_from(query.subquery())
            
            total_events = await self.session.scalar(total_events_query) or 0
            unique_users = await self.session.scalar(unique_users_query) or 0
            unique_sessions = await self.session.scalar(unique_sessions_query) or 0
            
            # Get event type breakdown
            event_type_query = select(
                AnalyticsEvent.event_type,
                func.count(AnalyticsEvent.id).label('count')
            ).select_from(query.subquery()).group_by(AnalyticsEvent.event_type)
            
            event_type_result = await self.session.execute(event_type_query)
            event_types_breakdown = {row.event_type: row.count for row in event_type_result}
            
            # Get module breakdown
            module_query = select(
                AnalyticsEvent.module_name,
                func.count(AnalyticsEvent.id).label('count')
            ).select_from(query.subquery()).group_by(AnalyticsEvent.module_name)
            
            module_result = await self.session.execute(module_query)
            modules_breakdown = {row.module_name: row.count for row in module_result}
            
            return {
                'total_events': total_events,
                'unique_users': unique_users,
                'unique_sessions': unique_sessions,
                'event_types': event_types_breakdown,
                'modules': modules_breakdown,
                'period_start': start_date.isoformat(),
                'period_end': end_date.isoformat(),
                'includes_anonymous': include_anonymous
            }
            
        except Exception as e:
            logger.error(f"Error getting aggregated metrics: {str(e)}")
            raise

    async def anonymize_user_events(self, user_id: str) -> int:
        """Anonymize all events for a specific user"""
        try:
            # Get all events for the user
            events_query = select(AnalyticsEvent).where(AnalyticsEvent.user_id == user_id)
            result = await self.session.execute(events_query)
            events = result.scalars().all()
            
            count = 0
            for event in events:
                event.anonymize()
                count += 1
            
            await self.session.commit()
            logger.info(f"Anonymized {count} events for user {user_id}")
            return count
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error anonymizing events for user {user_id}: {str(e)}")
            raise

    async def delete_expired_events(self) -> int:
        """Delete events that have exceeded their retention period"""
        try:
            # Get active retention policies
            policies_query = select(DataRetentionPolicy).where(
                and_(
                    DataRetentionPolicy.is_active == True,
                    DataRetentionPolicy.data_type == 'analytics_events'
                )
            )
            policies_result = await self.session.execute(policies_query)
            policies = policies_result.scalars().all()
            
            total_deleted = 0
            
            for policy in policies:
                cutoff_date = datetime.utcnow() - timedelta(days=policy.retention_days)
                
                # Delete events older than retention period
                delete_query = select(AnalyticsEvent).where(
                    AnalyticsEvent.created_at < cutoff_date
                )
                
                events_result = await self.session.execute(delete_query)
                events_to_delete = events_result.scalars().all()
                
                for event in events_to_delete:
                    await self.session.delete(event)
                    total_deleted += 1
            
            await self.session.commit()
            logger.info(f"Deleted {total_deleted} expired analytics events")
            return total_deleted
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting expired events: {str(e)}")
            raise


class ConsentRepository(BaseRepository):
    """Repository for user consent management"""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.model = UserConsent

    async def create_consent(
        self,
        user_id: str,
        consent_type: str,
        consent_given: bool,
        consent_version: str,
        consent_text: Optional[str] = None
    ) -> UserConsent:
        """Create or update user consent"""
        try:
            # Check if consent already exists
            existing_query = select(UserConsent).where(
                and_(
                    UserConsent.user_id == user_id,
                    UserConsent.consent_type == consent_type,
                    UserConsent.revoked_at.is_(None)
                )
            )
            result = await self.session.execute(existing_query)
            existing_consent = result.scalar_one_or_none()
            
            if existing_consent:
                # Revoke existing consent
                existing_consent.revoke()
            
            # Create new consent record
            consent = UserConsent(
                user_id=user_id,
                consent_type=consent_type,
                consent_given=consent_given,
                consent_version=consent_version,
                consent_text=consent_text
            )
            
            self.session.add(consent)
            await self.session.commit()
            await self.session.refresh(consent)
            
            logger.info(f"Created consent record: {consent_type} for user {user_id}")
            return consent
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating consent: {str(e)}")
            raise

    async def get_user_consents(self, user_id: str) -> List[UserConsent]:
        """Get all active consents for a user"""
        try:
            query = select(UserConsent).where(
                and_(
                    UserConsent.user_id == user_id,
                    UserConsent.revoked_at.is_(None)
                )
            ).order_by(desc(UserConsent.granted_at))
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting consents for user {user_id}: {str(e)}")
            raise

    async def check_consent(
        self,
        user_id: str,
        consent_type: str
    ) -> Optional[UserConsent]:
        """Check if user has given specific consent"""
        try:
            query = select(UserConsent).where(
                and_(
                    UserConsent.user_id == user_id,
                    UserConsent.consent_type == consent_type,
                    UserConsent.consent_given == True,
                    UserConsent.revoked_at.is_(None)
                )
            ).order_by(desc(UserConsent.granted_at))
            
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error checking consent for user {user_id}: {str(e)}")
            raise

    async def revoke_consent(
        self,
        user_id: str,
        consent_type: str
    ) -> bool:
        """Revoke user consent"""
        try:
            query = select(UserConsent).where(
                and_(
                    UserConsent.user_id == user_id,
                    UserConsent.consent_type == consent_type,
                    UserConsent.revoked_at.is_(None)
                )
            )
            
            result = await self.session.execute(query)
            consent = result.scalar_one_or_none()
            
            if consent:
                consent.revoke()
                await self.session.commit()
                logger.info(f"Revoked consent: {consent_type} for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error revoking consent: {str(e)}")
            raise


class AnalyticsSessionRepository(BaseRepository):
    """Repository for analytics session management"""

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.model = AnalyticsSession

    async def create_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        device_type: Optional[str] = None,
        platform: Optional[str] = None,
        is_anonymous: bool = False,
        consent_version: Optional[str] = None
    ) -> AnalyticsSession:
        """Create a new analytics session"""
        try:
            session_obj = AnalyticsSession(
                session_id=session_id,
                user_id=user_id if not is_anonymous else None,
                user_agent=user_agent,
                ip_address=ip_address,
                device_type=device_type,
                platform=platform,
                is_anonymous=is_anonymous,
                consent_version=consent_version
            )
            
            self.session.add(session_obj)
            await self.session.commit()
            await self.session.refresh(session_obj)
            
            logger.info(f"Created analytics session: {session_id}")
            return session_obj
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating analytics session: {str(e)}")
            raise

    async def update_session_activity(self, session_id: str) -> bool:
        """Update last activity timestamp for a session"""
        try:
            query = select(AnalyticsSession).where(AnalyticsSession.session_id == session_id)
            result = await self.session.execute(query)
            session_obj = result.scalar_one_or_none()
            
            if session_obj:
                session_obj.last_activity_at = datetime.utcnow()
                await self.session.commit()
                return True
            
            return False
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating session activity: {str(e)}")
            raise

    async def end_session(self, session_id: str) -> bool:
        """Mark a session as ended"""
        try:
            query = select(AnalyticsSession).where(AnalyticsSession.session_id == session_id)
            result = await self.session.execute(query)
            session_obj = result.scalar_one_or_none()
            
            if session_obj and not session_obj.ended_at:
                session_obj.ended_at = datetime.utcnow()
                await self.session.commit()
                logger.info(f"Ended analytics session: {session_id}")
                return True
            
            return False
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error ending session: {str(e)}")
            raise