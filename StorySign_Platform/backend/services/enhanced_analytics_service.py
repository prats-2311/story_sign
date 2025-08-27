"""
Enhanced Analytics Service
Handles analytics event collection, privacy compliance, and real-time processing
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from repositories.analytics_repository import AnalyticsRepository, ConsentRepository, AnalyticsSessionRepository
from models.analytics import AnalyticsEvent, UserConsent, ConsentType, EventType
from core.database_service import DatabaseService
import asyncio
import logging
import json
import hashlib
import uuid
from collections import defaultdict

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Enhanced analytics service with privacy compliance and real-time processing"""

    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self._event_queue = asyncio.Queue()
        self._processing_task = None
        self._consent_cache = {}
        self._session_cache = {}

    async def start_processing(self):
        """Start the background event processing task"""
        if not self._processing_task:
            self._processing_task = asyncio.create_task(self._process_events())
            logger.info("Analytics event processing started")

    async def stop_processing(self):
        """Stop the background event processing task"""
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
            self._processing_task = None
            logger.info("Analytics event processing stopped")

    async def track_event(
        self,
        user_id: Optional[str],
        session_id: str,
        event_type: str,
        module_name: str,
        event_data: Dict[str, Any],
        processing_time_ms: Optional[float] = None,
        force_anonymous: bool = False
    ) -> bool:
        """
        Track an analytics event with privacy compliance
        
        Args:
            user_id: User identifier (can be None for anonymous events)
            session_id: Session identifier
            event_type: Type of event (from EventType enum)
            module_name: Name of the module generating the event
            event_data: Event-specific data
            processing_time_ms: Optional processing time for performance tracking
            force_anonymous: Force event to be anonymous regardless of consent
            
        Returns:
            bool: True if event was queued successfully
        """
        try:
            # Check consent if user is identified
            is_anonymous = force_anonymous
            consent_version = None
            
            if user_id and not force_anonymous:
                consent_status = await self._check_analytics_consent(user_id)
                if not consent_status['has_consent']:
                    is_anonymous = True
                else:
                    consent_version = consent_status['consent_version']

            # Sanitize event data for privacy
            sanitized_data = await self._sanitize_event_data(event_data, is_anonymous)

            # Create event object
            event = {
                'user_id': user_id if not is_anonymous else None,
                'session_id': session_id,
                'event_type': event_type,
                'module_name': module_name,
                'event_data': sanitized_data,
                'is_anonymous': is_anonymous,
                'consent_version': consent_version,
                'processing_time_ms': processing_time_ms,
                'occurred_at': datetime.utcnow()
            }

            # Queue event for processing
            await self._event_queue.put(event)
            
            # Update session activity
            await self._update_session_activity(session_id)
            
            logger.debug(f"Queued analytics event: {event_type} for session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error tracking event: {str(e)}")
            return False

    async def track_user_action(
        self,
        user_id: str,
        session_id: str,
        action: str,
        module: str,
        details: Dict[str, Any] = None
    ) -> bool:
        """Convenience method for tracking user actions"""
        event_data = {
            'action': action,
            'details': details or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return await self.track_event(
            user_id=user_id,
            session_id=session_id,
            event_type=EventType.FEATURE_USED,
            module_name=module,
            event_data=event_data
        )

    async def track_performance_metric(
        self,
        user_id: Optional[str],
        session_id: str,
        metric_name: str,
        metric_value: float,
        module: str,
        additional_data: Dict[str, Any] = None
    ) -> bool:
        """Track performance metrics"""
        event_data = {
            'metric_name': metric_name,
            'metric_value': metric_value,
            'additional_data': additional_data or {}
        }
        
        return await self.track_event(
            user_id=user_id,
            session_id=session_id,
            event_type='performance_metric',
            module_name=module,
            event_data=event_data,
            processing_time_ms=metric_value if 'time' in metric_name.lower() else None
        )

    async def track_learning_event(
        self,
        user_id: str,
        session_id: str,
        event_type: str,
        story_id: Optional[str] = None,
        sentence_index: Optional[int] = None,
        score: Optional[float] = None,
        additional_data: Dict[str, Any] = None
    ) -> bool:
        """Track learning-specific events"""
        event_data = {
            'story_id': story_id,
            'sentence_index': sentence_index,
            'score': score,
            'additional_data': additional_data or {}
        }
        
        return await self.track_event(
            user_id=user_id,
            session_id=session_id,
            event_type=event_type,
            module_name='asl_world',
            event_data=event_data
        )

    async def get_user_analytics(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[str]] = None,
        include_raw_events: bool = False
    ) -> Dict[str, Any]:
        """Get analytics data for a specific user"""
        try:
            # Check if user has analytics consent
            consent_status = await self._check_analytics_consent(user_id)
            if not consent_status['has_consent']:
                return {'error': 'User has not consented to analytics data access'}

            async with self.db_service.get_session() as session:
                analytics_repo = AnalyticsRepository(session)
                
                # Set default date range if not provided
                if not end_date:
                    end_date = datetime.utcnow()
                if not start_date:
                    start_date = end_date - timedelta(days=30)

                # Get aggregated metrics
                metrics = await analytics_repo.get_aggregated_metrics(
                    start_date=start_date,
                    end_date=end_date,
                    include_anonymous=False
                )

                result = {
                    'user_id': user_id,
                    'period_start': start_date.isoformat(),
                    'period_end': end_date.isoformat(),
                    'metrics': metrics
                }

                # Include raw events if requested
                if include_raw_events:
                    events = await analytics_repo.get_events_by_user(
                        user_id=user_id,
                        start_date=start_date,
                        end_date=end_date,
                        event_types=event_types
                    )
                    result['events'] = [event.to_dict(include_sensitive=True) for event in events]

                return result

        except Exception as e:
            logger.error(f"Error getting user analytics: {str(e)}")
            raise

    async def get_platform_analytics(
        self,
        start_date: datetime,
        end_date: datetime,
        module_name: Optional[str] = None,
        include_anonymous: bool = True
    ) -> Dict[str, Any]:
        """Get platform-wide analytics (anonymized)"""
        try:
            async with self.db_service.get_session() as session:
                analytics_repo = AnalyticsRepository(session)
                
                # Get basic aggregated metrics
                metrics = await analytics_repo.get_aggregated_metrics(
                    start_date=start_date,
                    end_date=end_date,
                    module_name=module_name,
                    include_anonymous=include_anonymous
                )

                # Enhance with dashboard-specific metrics
                enhanced_metrics = await self._generate_dashboard_metrics(
                    analytics_repo, start_date, end_date, module_name, include_anonymous
                )

                return {
                    'platform_metrics': {**metrics, **enhanced_metrics},
                    'generated_at': datetime.utcnow().isoformat(),
                    'includes_anonymous': include_anonymous,
                    'date_range': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat()
                    }
                }

        except Exception as e:
            logger.error(f"Error getting platform analytics: {str(e)}")
            raise

    async def _generate_dashboard_metrics(
        self,
        analytics_repo,
        start_date: datetime,
        end_date: datetime,
        module_name: Optional[str] = None,
        include_anonymous: bool = True
    ) -> Dict[str, Any]:
        """Generate enhanced metrics for dashboard display"""
        try:
            # Enhanced mock data for demonstration - in real implementation, these would be actual queries
            dashboard_metrics = {
                'total_users': 150,
                'active_sessions': 45,
                'practice_sessions': 320,
                'stories_completed': 180,
                'daily_activity': [
                    {'date': '2024-01-01', 'active_users': 25},
                    {'date': '2024-01-02', 'active_users': 30},
                    {'date': '2024-01-03', 'active_users': 28},
                    {'date': '2024-01-04', 'active_users': 35},
                    {'date': '2024-01-05', 'active_users': 32},
                ],
                'module_usage': {
                    'asl_world': 65,
                    'harmony': 20,
                    'reconnect': 15
                },
                'learning_metrics': {
                    'average_score': 78.5,
                    'completion_rate': 85.2,
                    'avg_session_time': 24.5,
                    'gesture_accuracy': 82.3,
                    'score_trend': 2.1,
                    'completion_trend': 1.8,
                    'session_time_trend': -0.5,
                    'accuracy_trend': 3.2,
                    'progress_over_time': [
                        {'date': '2024-01-01', 'average_score': 75, 'completion_rate': 80},
                        {'date': '2024-01-02', 'average_score': 76, 'completion_rate': 82},
                        {'date': '2024-01-03', 'average_score': 78, 'completion_rate': 84},
                        {'date': '2024-01-04', 'average_score': 79, 'completion_rate': 85},
                        {'date': '2024-01-05', 'average_score': 78.5, 'completion_rate': 85.2},
                    ],
                    'difficulty_distribution': {
                        'easy': 120,
                        'medium': 150,
                        'hard': 50
                    },
                    'gesture_accuracy_by_type': [
                        {'gesture_type': 'Hand Shapes', 'accuracy': 85.2},
                        {'gesture_type': 'Movement', 'accuracy': 78.9},
                        {'gesture_type': 'Facial Expression', 'accuracy': 82.1},
                        {'gesture_type': 'Body Position', 'accuracy': 79.5},
                        {'gesture_type': 'Finger Spelling', 'accuracy': 88.3},
                    ],
                    'session_duration_trends': [
                        {'date': '2024-01-01', 'avg_duration': 22.5},
                        {'date': '2024-01-02', 'avg_duration': 24.1},
                        {'date': '2024-01-03', 'avg_duration': 23.8},
                        {'date': '2024-01-04', 'avg_duration': 25.2},
                        {'date': '2024-01-05', 'avg_duration': 24.5},
                    ],
                    'top_performing_areas': [
                        {'name': 'Finger Spelling', 'score': 88.3},
                        {'name': 'Basic Greetings', 'score': 86.7},
                        {'name': 'Numbers', 'score': 85.9},
                    ],
                    'improvement_areas': [
                        {'name': 'Complex Sentences', 'score': 65.2},
                        {'name': 'Spatial Grammar', 'score': 68.1},
                        {'name': 'Classifiers', 'score': 70.4},
                    ],
                    'recommendations': [
                        {'text': 'Focus on spatial grammar exercises', 'priority': 'high'},
                        {'text': 'Practice complex sentence structures', 'priority': 'high'},
                        {'text': 'Increase classifier practice time', 'priority': 'medium'},
                    ]
                },
                'performance_metrics': {
                    'avg_response_time': 145,
                    'avg_video_processing': 85,
                    'error_rate': 2.1,
                    'response_time_trends': [
                        {'timestamp': '2024-01-01T00:00:00Z', 'response_time': 150},
                        {'timestamp': '2024-01-01T06:00:00Z', 'response_time': 140},
                        {'timestamp': '2024-01-01T12:00:00Z', 'response_time': 145},
                        {'timestamp': '2024-01-01T18:00:00Z', 'response_time': 155},
                    ],
                    'system_load': [
                        {'timestamp': '2024-01-01T00:00:00Z', 'cpu_usage': 45, 'memory_usage': 60},
                        {'timestamp': '2024-01-01T06:00:00Z', 'cpu_usage': 50, 'memory_usage': 65},
                        {'timestamp': '2024-01-01T12:00:00Z', 'cpu_usage': 55, 'memory_usage': 70},
                        {'timestamp': '2024-01-01T18:00:00Z', 'cpu_usage': 48, 'memory_usage': 62},
                    ]
                },
                'research_metrics': {
                    'total_participants': 125,
                    'consented_users': 98,
                    'data_points': 45620,
                    'research_sessions': 1250,
                    'learning_outcomes': [
                        {'outcome': 'Basic Communication', 'count': 85},
                        {'outcome': 'Intermediate Fluency', 'count': 45},
                        {'outcome': 'Advanced Proficiency', 'count': 18},
                        {'outcome': 'Teaching Capability', 'count': 8},
                    ],
                    'engagement_heatmap': {
                        'hours': ['6AM', '9AM', '12PM', '3PM', '6PM', '9PM'],
                        'monday': [12, 25, 35, 42, 38, 20],
                        'tuesday': [15, 28, 38, 45, 40, 22],
                        'wednesday': [18, 32, 40, 48, 42, 25],
                        'thursday': [16, 30, 36, 44, 39, 23],
                        'friday': [14, 26, 34, 41, 37, 21],
                        'saturday': [20, 35, 45, 52, 48, 30],
                        'sunday': [22, 38, 48, 55, 50, 32],
                    },
                    'retention_data': [
                        {'week': 1, 'retention_rate': 95.2},
                        {'week': 2, 'retention_rate': 87.8},
                        {'week': 4, 'retention_rate': 78.5},
                        {'week': 8, 'retention_rate': 68.2},
                        {'week': 12, 'retention_rate': 62.1},
                        {'week': 24, 'retention_rate': 55.8},
                    ],
                    'gesture_progression': [
                        {'date': '2024-01-01', 'average_score': 65, 'completion_rate': 70},
                        {'date': '2024-01-02', 'average_score': 68, 'completion_rate': 73},
                        {'date': '2024-01-03', 'average_score': 72, 'completion_rate': 76},
                        {'date': '2024-01-04', 'average_score': 75, 'completion_rate': 79},
                        {'date': '2024-01-05', 'average_score': 78, 'completion_rate': 82},
                    ],
                    'key_findings': [
                        {'text': 'Users show 23% improvement in gesture accuracy after 4 weeks', 'confidence': 95},
                        {'text': 'Evening practice sessions yield 15% better retention', 'confidence': 87},
                        {'text': 'Collaborative sessions improve engagement by 32%', 'confidence': 92},
                    ],
                    'statistical_tests': [
                        {'name': 'Learning Improvement', 'p_value': 0.001, 'significant': True},
                        {'name': 'Retention Correlation', 'p_value': 0.023, 'significant': True},
                        {'name': 'Gender Differences', 'p_value': 0.156, 'significant': False},
                    ],
                    'educator_recommendations': [
                        {'text': 'Schedule practice sessions in the evening for better retention', 'evidence_level': 'Strong'},
                        {'text': 'Incorporate collaborative elements to boost engagement', 'evidence_level': 'Strong'},
                        {'text': 'Focus on gesture accuracy in early learning phases', 'evidence_level': 'Moderate'},
                    ]
                },
                'total_events': 15420
            }

            return dashboard_metrics

        except Exception as e:
            logger.error(f"Error generating dashboard metrics: {str(e)}")
            return {}

    async def manage_user_consent(
        self,
        user_id: str,
        consent_type: str,
        consent_given: bool,
        consent_version: str = "1.0"
    ) -> UserConsent:
        """Manage user consent for analytics collection"""
        try:
            async with self.db_service.get_session() as session:
                consent_repo = ConsentRepository(session)
                
                consent = await consent_repo.create_consent(
                    user_id=user_id,
                    consent_type=consent_type,
                    consent_given=consent_given,
                    consent_version=consent_version
                )

                # Clear consent cache for this user
                if user_id in self._consent_cache:
                    del self._consent_cache[user_id]

                # If consent is revoked for analytics, anonymize existing data
                if consent_type == ConsentType.ANALYTICS and not consent_given:
                    await self._anonymize_user_data(user_id)

                return consent

        except Exception as e:
            logger.error(f"Error managing user consent: {str(e)}")
            raise

    async def get_user_consents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all consents for a user"""
        try:
            async with self.db_service.get_session() as session:
                consent_repo = ConsentRepository(session)
                consents = await consent_repo.get_user_consents(user_id)
                return [consent.to_dict() for consent in consents]

        except Exception as e:
            logger.error(f"Error getting user consents: {str(e)}")
            raise

    async def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export all analytics data for a user (GDPR compliance)"""
        try:
            # Check consent
            consent_status = await self._check_analytics_consent(user_id)
            if not consent_status['has_consent']:
                return {'error': 'User has not consented to data export'}

            async with self.db_service.get_session() as session:
                analytics_repo = AnalyticsRepository(session)
                consent_repo = ConsentRepository(session)
                session_repo = AnalyticsSessionRepository(session)

                # Get all user events
                events = await analytics_repo.get_events_by_user(
                    user_id=user_id,
                    limit=10000  # Large limit for export
                )

                # Get all consents
                consents = await consent_repo.get_user_consents(user_id)

                # Get session data
                sessions_query = await session.execute(
                    session_repo.model.__table__.select().where(
                        session_repo.model.user_id == user_id
                    )
                )
                sessions = sessions_query.fetchall()

                return {
                    'user_id': user_id,
                    'export_date': datetime.utcnow().isoformat(),
                    'events': [event.to_dict(include_sensitive=True) for event in events],
                    'consents': [consent.to_dict() for consent in consents],
                    'sessions': [dict(session) for session in sessions],
                    'total_events': len(events)
                }

        except Exception as e:
            logger.error(f"Error exporting user data: {str(e)}")
            raise

    async def delete_user_data(self, user_id: str) -> Dict[str, Any]:
        """Delete all analytics data for a user (GDPR right to be forgotten)"""
        try:
            async with self.db_service.get_session() as session:
                analytics_repo = AnalyticsRepository(session)
                
                # Count events before deletion
                events = await analytics_repo.get_events_by_user(user_id=user_id, limit=10000)
                event_count = len(events)

                # Anonymize events instead of deleting (preserves research data)
                anonymized_count = await analytics_repo.anonymize_user_events(user_id)

                # Delete consent records
                consent_repo = ConsentRepository(session)
                consents = await consent_repo.get_user_consents(user_id)
                for consent in consents:
                    await session.delete(consent)

                await session.commit()

                return {
                    'user_id': user_id,
                    'deletion_date': datetime.utcnow().isoformat(),
                    'events_anonymized': anonymized_count,
                    'consents_deleted': len(consents),
                    'status': 'completed'
                }

        except Exception as e:
            logger.error(f"Error deleting user data: {str(e)}")
            raise

    async def _process_events(self):
        """Background task to process queued analytics events"""
        while True:
            try:
                # Get event from queue with timeout
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                
                async with self.db_service.get_session() as session:
                    analytics_repo = AnalyticsRepository(session)
                    
                    await analytics_repo.create_event(**event)
                    
                    # Mark task as done
                    self._event_queue.task_done()

            except asyncio.TimeoutError:
                # No events to process, continue
                continue
            except Exception as e:
                logger.error(f"Error processing analytics event: {str(e)}")
                # Mark task as done even on error to prevent queue backup
                self._event_queue.task_done()

    async def _check_analytics_consent(self, user_id: str) -> Dict[str, Any]:
        """Check if user has given analytics consent (with caching)"""
        if user_id in self._consent_cache:
            return self._consent_cache[user_id]

        try:
            async with self.db_service.get_session() as session:
                consent_repo = ConsentRepository(session)
                consent = await consent_repo.check_consent(user_id, ConsentType.ANALYTICS)
                
                result = {
                    'has_consent': consent is not None and consent.is_active,
                    'consent_version': consent.consent_version if consent else None
                }
                
                # Cache result for 5 minutes
                self._consent_cache[user_id] = result
                asyncio.create_task(self._clear_consent_cache(user_id, 300))
                
                return result

        except Exception as e:
            logger.error(f"Error checking consent for user {user_id}: {str(e)}")
            return {'has_consent': False, 'consent_version': None}

    async def _clear_consent_cache(self, user_id: str, delay: int):
        """Clear consent cache entry after delay"""
        await asyncio.sleep(delay)
        if user_id in self._consent_cache:
            del self._consent_cache[user_id]

    async def _sanitize_event_data(self, event_data: Dict[str, Any], is_anonymous: bool) -> Dict[str, Any]:
        """Sanitize event data for privacy compliance"""
        if not is_anonymous:
            return event_data

        # Remove or hash sensitive fields for anonymous events
        sanitized = event_data.copy()
        sensitive_fields = ['email', 'name', 'ip_address', 'device_id', 'user_agent']
        
        for field in sensitive_fields:
            if field in sanitized:
                # Hash sensitive data instead of removing completely
                sanitized[field] = hashlib.sha256(str(sanitized[field]).encode()).hexdigest()[:16]

        return sanitized

    async def _update_session_activity(self, session_id: str):
        """Update session activity timestamp"""
        try:
            if session_id not in self._session_cache:
                self._session_cache[session_id] = datetime.utcnow()
                return

            # Only update if more than 1 minute has passed
            last_update = self._session_cache[session_id]
            if (datetime.utcnow() - last_update).seconds > 60:
                async with self.db_service.get_session() as session:
                    session_repo = AnalyticsSessionRepository(session)
                    await session_repo.update_session_activity(session_id)
                    self._session_cache[session_id] = datetime.utcnow()

        except Exception as e:
            logger.error(f"Error updating session activity: {str(e)}")

    async def _anonymize_user_data(self, user_id: str):
        """Anonymize all analytics data for a user"""
        try:
            async with self.db_service.get_session() as session:
                analytics_repo = AnalyticsRepository(session)
                await analytics_repo.anonymize_user_events(user_id)
                logger.info(f"Anonymized analytics data for user {user_id}")

        except Exception as e:
            logger.error(f"Error anonymizing user data: {str(e)}")


# Singleton instance
_analytics_service = None

def get_analytics_service(db_service: DatabaseService) -> AnalyticsService:
    """Get or create analytics service singleton"""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService(db_service)
    return _analytics_service