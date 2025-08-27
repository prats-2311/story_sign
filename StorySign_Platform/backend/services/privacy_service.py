"""
Privacy and GDPR compliance service
"""

import json
import hashlib
import secrets
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, and_, or_
from sqlalchemy.orm import selectinload
import logging

from core.base_service import BaseService
from models.privacy import (
    UserConsent, ConsentType, ConsentStatus,
    DataProcessingRecord, DataProcessingPurpose, DataRetentionPolicy,
    DataDeletionRequest, DataExportRequest, PrivacySettings,
    AnonymizedUserData, PrivacyAuditLog
)
# Import with error handling for optional dependencies
try:
    from models.user import User
    USER_MODEL_AVAILABLE = True
except ImportError:
    USER_MODEL_AVAILABLE = False

try:
    from models.progress import PracticeSession, SentenceAttempt, UserProgress
    PROGRESS_MODEL_AVAILABLE = True
except ImportError:
    PROGRESS_MODEL_AVAILABLE = False

try:
    from models.content import Story
    CONTENT_MODEL_AVAILABLE = True
except ImportError:
    CONTENT_MODEL_AVAILABLE = False

try:
    from models.analytics import AnalyticsEvent
    ANALYTICS_MODEL_AVAILABLE = True
except ImportError:
    ANALYTICS_MODEL_AVAILABLE = False


class PrivacyService(BaseService):
    """
    Service for handling privacy compliance, GDPR requirements, and data protection
    """
    
    def __init__(self, service_name: str = "PrivacyService", config: Optional[Dict[str, Any]] = None):
        super().__init__(service_name, config)
        
        # Configuration
        self.gdpr_enabled = config.get("gdpr_enabled", True) if config else True
        self.data_retention_days = config.get("data_retention_days", 365) if config else 365
        self.anonymization_salt = config.get("anonymization_salt", "storysign_privacy_salt") if config else "storysign_privacy_salt"
        self.export_expiry_hours = config.get("export_expiry_hours", 72) if config else 72
        self.verification_expiry_hours = config.get("verification_expiry_hours", 24) if config else 24
        
        # Current consent version
        self.consent_version = "1.0"
        
    async def initialize(self) -> None:
        """Initialize privacy service"""
        self.logger.info("Privacy service initialized")
        
        # Schedule background tasks for data retention and cleanup
        import asyncio
        asyncio.create_task(self._schedule_data_retention_cleanup())
        asyncio.create_task(self._schedule_export_cleanup())
    
    async def cleanup(self) -> None:
        """Clean up privacy service"""
        self.logger.info("Privacy service cleaned up")
    
    # Consent Management
    
    async def grant_consent(
        self,
        session: AsyncSession,
        user_id: str,
        consent_type: ConsentType,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        consent_details: Optional[Dict[str, Any]] = None
    ) -> UserConsent:
        """
        Grant user consent for specific data processing
        
        Args:
            session: Database session
            user_id: User ID
            consent_type: Type of consent
            ip_address: User's IP address
            user_agent: User's browser/app info
            consent_details: Additional consent details
            
        Returns:
            UserConsent record
        """
        try:
            # Check if consent already exists
            existing_consent = await session.execute(
                select(UserConsent).where(
                    and_(
                        UserConsent.user_id == user_id,
                        UserConsent.consent_type == consent_type.value,
                        UserConsent.status.in_([ConsentStatus.GRANTED.value])
                    )
                )
            )
            existing = existing_consent.scalar_one_or_none()
            
            if existing:
                # Update existing consent
                existing.status = ConsentStatus.GRANTED.value
                existing.granted_at = datetime.utcnow()
                existing.withdrawn_at = None
                existing.consent_version = self.consent_version
                existing.ip_address = ip_address
                existing.user_agent = user_agent
                existing.consent_details = consent_details
                consent_record = existing
            else:
                # Create new consent
                consent_record = UserConsent(
                    user_id=user_id,
                    consent_type=consent_type.value,
                    status=ConsentStatus.GRANTED.value,
                    granted_at=datetime.utcnow(),
                    consent_version=self.consent_version,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    consent_details=consent_details
                )
                session.add(consent_record)
            
            # Log consent action
            await self._log_privacy_action(
                session=session,
                user_id=user_id,
                action_type="consent_granted",
                action_details={
                    "consent_type": consent_type.value,
                    "consent_version": self.consent_version,
                    "consent_details": consent_details
                },
                ip_address=ip_address,
                user_agent=user_agent,
                legal_basis="consent"
            )
            
            await session.commit()
            return consent_record
            
        except Exception as e:
            await session.rollback()
            self.logger.error(f"Error granting consent: {e}")
            raise
    
    async def withdraw_consent(
        self,
        session: AsyncSession,
        user_id: str,
        consent_type: ConsentType,
        withdrawal_reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Withdraw user consent
        
        Args:
            session: Database session
            user_id: User ID
            consent_type: Type of consent to withdraw
            withdrawal_reason: Reason for withdrawal
            ip_address: User's IP address
            user_agent: User's browser/app info
            
        Returns:
            True if consent was withdrawn
        """
        try:
            # Find active consent
            result = await session.execute(
                select(UserConsent).where(
                    and_(
                        UserConsent.user_id == user_id,
                        UserConsent.consent_type == consent_type.value,
                        UserConsent.status == ConsentStatus.GRANTED.value
                    )
                )
            )
            consent = result.scalar_one_or_none()
            
            if not consent:
                return False
            
            # Withdraw consent
            consent.status = ConsentStatus.WITHDRAWN.value
            consent.withdrawn_at = datetime.utcnow()
            consent.withdrawal_reason = withdrawal_reason
            
            # Log withdrawal
            await self._log_privacy_action(
                session=session,
                user_id=user_id,
                action_type="consent_withdrawn",
                action_details={
                    "consent_type": consent_type.value,
                    "withdrawal_reason": withdrawal_reason
                },
                ip_address=ip_address,
                user_agent=user_agent,
                legal_basis="user_request"
            )
            
            # If research consent is withdrawn, schedule data anonymization
            if consent_type == ConsentType.RESEARCH_PARTICIPATION:
                await self._schedule_research_data_anonymization(session, user_id)
            
            await session.commit()
            return True
            
        except Exception as e:
            await session.rollback()
            self.logger.error(f"Error withdrawing consent: {e}")
            raise
    
    async def check_consent(
        self,
        session: AsyncSession,
        user_id: str,
        consent_type: ConsentType
    ) -> bool:
        """
        Check if user has granted specific consent
        
        Args:
            session: Database session
            user_id: User ID
            consent_type: Type of consent to check
            
        Returns:
            True if consent is granted and valid
        """
        try:
            result = await session.execute(
                select(UserConsent).where(
                    and_(
                        UserConsent.user_id == user_id,
                        UserConsent.consent_type == consent_type.value,
                        UserConsent.status == ConsentStatus.GRANTED.value,
                        or_(
                            UserConsent.expires_at.is_(None),
                            UserConsent.expires_at > datetime.utcnow()
                        )
                    )
                )
            )
            consent = result.scalar_one_or_none()
            return consent is not None
            
        except Exception as e:
            self.logger.error(f"Error checking consent: {e}")
            return False
    
    # Data Processing Records
    
    async def record_data_processing(
        self,
        session: AsyncSession,
        user_id: str,
        purpose: DataProcessingPurpose,
        data_categories: List[str],
        legal_basis: str,
        processor_id: str,
        retention_policy: DataRetentionPolicy,
        processing_details: Optional[Dict[str, Any]] = None
    ) -> DataProcessingRecord:
        """
        Record data processing activity for compliance
        
        Args:
            session: Database session
            user_id: User ID
            purpose: Purpose of data processing
            data_categories: Categories of data being processed
            legal_basis: Legal basis for processing (GDPR Article 6)
            processor_id: ID of the processing system
            retention_policy: Data retention policy
            processing_details: Additional processing details
            
        Returns:
            DataProcessingRecord
        """
        try:
            # Calculate scheduled deletion date
            scheduled_deletion = None
            if retention_policy != DataRetentionPolicy.INDEFINITE_ANONYMIZED:
                days_map = {
                    DataRetentionPolicy.IMMEDIATE_DELETE: 0,
                    DataRetentionPolicy.THIRTY_DAYS: 30,
                    DataRetentionPolicy.ONE_YEAR: 365,
                    DataRetentionPolicy.SEVEN_YEARS: 2555  # 7 years
                }
                days = days_map.get(retention_policy, 365)
                scheduled_deletion = datetime.utcnow() + timedelta(days=days)
            
            record = DataProcessingRecord(
                user_id=user_id,
                processing_purpose=purpose.value,
                data_categories=data_categories,
                legal_basis=legal_basis,
                processor_id=processor_id,
                processing_details=processing_details or {},
                retention_policy=retention_policy.value,
                scheduled_deletion=scheduled_deletion,
                processed_at=datetime.utcnow()
            )
            
            session.add(record)
            await session.commit()
            
            return record
            
        except Exception as e:
            await session.rollback()
            self.logger.error(f"Error recording data processing: {e}")
            raise
    
    # Data Deletion (Right to be Forgotten)
    
    async def request_data_deletion(
        self,
        session: AsyncSession,
        user_id: str,
        request_type: str = "full_deletion",
        deletion_scope: Optional[Dict[str, Any]] = None
    ) -> DataDeletionRequest:
        """
        Create data deletion request
        
        Args:
            session: Database session
            user_id: User ID
            request_type: Type of deletion ('full_deletion', 'partial_deletion', 'anonymization')
            deletion_scope: Scope of data to delete
            
        Returns:
            DataDeletionRequest
        """
        try:
            # Generate verification token
            verification_token = secrets.token_urlsafe(32)
            verification_expires = datetime.utcnow() + timedelta(hours=self.verification_expiry_hours)
            
            request = DataDeletionRequest(
                user_id=user_id,
                request_type=request_type,
                deletion_scope=deletion_scope or {},
                verification_token=verification_token,
                verification_expires=verification_expires,
                status="pending"
            )
            
            session.add(request)
            
            # Log deletion request
            await self._log_privacy_action(
                session=session,
                user_id=user_id,
                action_type="deletion_requested",
                action_details={
                    "request_type": request_type,
                    "deletion_scope": deletion_scope
                },
                legal_basis="user_request"
            )
            
            await session.commit()
            return request
            
        except Exception as e:
            await session.rollback()
            self.logger.error(f"Error creating deletion request: {e}")
            raise
    
    async def process_data_deletion(
        self,
        session: AsyncSession,
        request_id: str,
        verification_token: str
    ) -> bool:
        """
        Process verified data deletion request
        
        Args:
            session: Database session
            request_id: Deletion request ID
            verification_token: Verification token
            
        Returns:
            True if deletion was processed
        """
        try:
            # Get deletion request
            result = await session.execute(
                select(DataDeletionRequest).where(
                    and_(
                        DataDeletionRequest.id == request_id,
                        DataDeletionRequest.verification_token == verification_token,
                        DataDeletionRequest.verification_expires > datetime.utcnow(),
                        DataDeletionRequest.status == "pending"
                    )
                )
            )
            request = result.scalar_one_or_none()
            
            if not request:
                return False
            
            # Update request status
            request.status = "processing"
            request.processed_at = datetime.utcnow()
            request.verified_at = datetime.utcnow()
            
            # Process deletion based on type
            if request.request_type == "full_deletion":
                await self._delete_user_data(session, request.user_id)
            elif request.request_type == "anonymization":
                await self._anonymize_user_data(session, request.user_id)
            elif request.request_type == "partial_deletion":
                await self._partial_delete_user_data(session, request.user_id, request.deletion_scope)
            
            # Mark as completed
            request.status = "completed"
            request.completed_at = datetime.utcnow()
            
            # Log completion
            await self._log_privacy_action(
                session=session,
                user_id=request.user_id,
                action_type="deletion_completed",
                action_details={
                    "request_type": request.request_type,
                    "deletion_scope": request.deletion_scope
                },
                legal_basis="user_request"
            )
            
            await session.commit()
            return True
            
        except Exception as e:
            await session.rollback()
            self.logger.error(f"Error processing data deletion: {e}")
            raise
    
    # Data Export (Data Portability)
    
    async def request_data_export(
        self,
        session: AsyncSession,
        user_id: str,
        export_format: str = "json",
        export_scope: Optional[Dict[str, Any]] = None
    ) -> DataExportRequest:
        """
        Create data export request
        
        Args:
            session: Database session
            user_id: User ID
            export_format: Export format ('json', 'csv', 'xml')
            export_scope: Scope of data to export
            
        Returns:
            DataExportRequest
        """
        try:
            # Generate download token
            download_token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=self.export_expiry_hours)
            
            request = DataExportRequest(
                user_id=user_id,
                export_format=export_format,
                export_scope=export_scope or {},
                expires_at=expires_at,
                download_token=download_token,
                status="pending"
            )
            
            session.add(request)
            
            # Log export request
            await self._log_privacy_action(
                session=session,
                user_id=user_id,
                action_type="export_requested",
                action_details={
                    "export_format": export_format,
                    "export_scope": export_scope
                },
                legal_basis="user_request"
            )
            
            await session.commit()
            
            # Schedule export processing
            import asyncio
            asyncio.create_task(self._process_data_export(request.id))
            
            return request
            
        except Exception as e:
            await session.rollback()
            self.logger.error(f"Error creating export request: {e}")
            raise
    
    # Data Anonymization
    
    async def anonymize_user_for_research(
        self,
        session: AsyncSession,
        user_id: str,
        research_consent_granted: bool = True
    ) -> Optional[AnonymizedUserData]:
        """
        Create anonymized user data for research purposes
        
        Args:
            session: Database session
            user_id: User ID to anonymize
            research_consent_granted: Whether user consented to research
            
        Returns:
            AnonymizedUserData record or None
        """
        try:
            # Check if user has research consent
            if research_consent_granted:
                has_consent = await self.check_consent(
                    session, user_id, ConsentType.RESEARCH_PARTICIPATION
                )
                if not has_consent:
                    return None
            
            # Get user data
            result = await session.execute(
                select(User).options(
                    selectinload(User.user_profile),
                    selectinload(User.practice_sessions),
                    selectinload(User.user_progress)
                ).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            # Generate anonymous ID
            anonymous_id = self._generate_anonymous_id(user_id)
            
            # Calculate anonymized metrics
            total_sessions = len(user.practice_sessions) if user.practice_sessions else 0
            total_time = sum(
                (session.completed_at - session.started_at).total_seconds() / 60
                for session in user.practice_sessions
                if session.completed_at and session.started_at
            ) if user.practice_sessions else 0
            
            avg_score = sum(
                session.overall_score for session in user.practice_sessions
                if session.overall_score is not None
            ) / max(total_sessions, 1) if user.practice_sessions else 0
            
            # Create anonymized record
            anonymized_data = AnonymizedUserData(
                anonymous_id=anonymous_id,
                original_user_id=user_id if research_consent_granted else None,
                anonymization_method="hash",
                age_range=self._anonymize_age(user.user_profile.age if user.user_profile else None),
                region=self._anonymize_location(user.user_profile.location if user.user_profile else None),
                language_preference=user.user_profile.language if user.user_profile else "en",
                total_practice_sessions=total_sessions,
                total_practice_time_minutes=int(total_time),
                average_session_score=round(avg_score, 2),
                research_consent_granted=research_consent_granted,
                research_consent_date=datetime.utcnow() if research_consent_granted else None,
                research_data_categories=["practice_sessions", "performance_metrics", "learning_progress"]
            )
            
            session.add(anonymized_data)
            await session.commit()
            
            return anonymized_data
            
        except Exception as e:
            await session.rollback()
            self.logger.error(f"Error anonymizing user data: {e}")
            raise
    
    # Privacy Settings Management
    
    async def get_privacy_settings(
        self,
        session: AsyncSession,
        user_id: str
    ) -> Optional[PrivacySettings]:
        """
        Get user privacy settings
        
        Args:
            session: Database session
            user_id: User ID
            
        Returns:
            PrivacySettings or None
        """
        try:
            result = await session.execute(
                select(PrivacySettings).where(PrivacySettings.user_id == user_id)
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            self.logger.error(f"Error getting privacy settings: {e}")
            return None
    
    async def update_privacy_settings(
        self,
        session: AsyncSession,
        user_id: str,
        settings_update: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> PrivacySettings:
        """
        Update user privacy settings
        
        Args:
            session: Database session
            user_id: User ID
            settings_update: Settings to update
            ip_address: User's IP address
            user_agent: User's browser/app info
            
        Returns:
            Updated PrivacySettings
        """
        try:
            # Get or create privacy settings
            result = await session.execute(
                select(PrivacySettings).where(PrivacySettings.user_id == user_id)
            )
            settings = result.scalar_one_or_none()
            
            if not settings:
                settings = PrivacySettings(user_id=user_id)
                session.add(settings)
            
            # Update settings
            for key, value in settings_update.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
            
            settings.last_privacy_review = datetime.utcnow()
            
            # Log settings update
            await self._log_privacy_action(
                session=session,
                user_id=user_id,
                action_type="privacy_settings_updated",
                action_details={"updated_settings": settings_update},
                ip_address=ip_address,
                user_agent=user_agent,
                legal_basis="user_request"
            )
            
            await session.commit()
            return settings
            
        except Exception as e:
            await session.rollback()
            self.logger.error(f"Error updating privacy settings: {e}")
            raise
    
    # Helper Methods
    
    def _generate_anonymous_id(self, user_id: str) -> str:
        """Generate anonymous ID for user"""
        combined = f"{user_id}{self.anonymization_salt}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def _anonymize_age(self, age: Optional[int]) -> Optional[str]:
        """Anonymize age into ranges"""
        if not age:
            return None
        
        if age < 18:
            return "under_18"
        elif age < 25:
            return "18-24"
        elif age < 35:
            return "25-34"
        elif age < 45:
            return "35-44"
        elif age < 55:
            return "45-54"
        elif age < 65:
            return "55-64"
        else:
            return "65_plus"
    
    def _anonymize_location(self, location: Optional[str]) -> Optional[str]:
        """Anonymize location to broad regions"""
        if not location:
            return None
        
        # Simple region mapping - in production, use proper geolocation service
        location_lower = location.lower()
        
        # Check more specific matches first to avoid conflicts
        if any(country in location_lower for country in ["australia", "new zealand"]):
            return "oceania"
        elif any(country in location_lower for country in ["canada"]):
            return "north_america"
        elif any(country in location_lower for country in ["us", "usa", "united states"]):
            return "north_america"
        elif "america" in location_lower and "north" in location_lower:
            return "north_america"
        elif any(country in location_lower for country in ["uk", "england", "scotland", "wales", "ireland"]):
            return "uk_ireland"
        elif any(country in location_lower for country in ["germany", "france", "spain", "italy", "netherlands"]):
            return "western_europe"
        else:
            return "other"
    
    async def _log_privacy_action(
        self,
        session: AsyncSession,
        user_id: str,
        action_type: str,
        action_details: Dict[str, Any],
        performed_by: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        legal_basis: Optional[str] = None
    ) -> None:
        """Log privacy-related action for audit trail"""
        try:
            log_entry = PrivacyAuditLog(
                user_id=user_id,
                action_type=action_type,
                action_details=action_details,
                performed_by=performed_by or user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                legal_basis=legal_basis,
                action_timestamp=datetime.utcnow()
            )
            
            session.add(log_entry)
            # Note: Don't commit here, let the calling method handle it
            
        except Exception as e:
            self.logger.error(f"Error logging privacy action: {e}")
    
    async def _delete_user_data(self, session: AsyncSession, user_id: str) -> None:
        """Delete all user data (full deletion)"""
        try:
            # Delete in order to respect foreign key constraints
            
            # Delete practice data
            await session.execute(
                delete(SentenceAttempt).where(
                    SentenceAttempt.session_id.in_(
                        select(PracticeSession.id).where(PracticeSession.user_id == user_id)
                    )
                )
            )
            
            await session.execute(
                delete(PracticeSession).where(PracticeSession.user_id == user_id)
            )
            
            await session.execute(
                delete(UserProgress).where(UserProgress.user_id == user_id)
            )
            
            # Delete analytics data
            await session.execute(
                delete(AnalyticsEvent).where(AnalyticsEvent.user_id == user_id)
            )
            
            # Delete privacy records
            await session.execute(
                delete(UserConsent).where(UserConsent.user_id == user_id)
            )
            
            await session.execute(
                delete(DataProcessingRecord).where(DataProcessingRecord.user_id == user_id)
            )
            
            await session.execute(
                delete(PrivacySettings).where(PrivacySettings.user_id == user_id)
            )
            
            # Finally delete user
            await session.execute(
                delete(User).where(User.id == user_id)
            )
            
        except Exception as e:
            self.logger.error(f"Error deleting user data: {e}")
            raise
    
    async def _anonymize_user_data(self, session: AsyncSession, user_id: str) -> None:
        """Anonymize user data instead of deleting"""
        try:
            # Create anonymized record first
            await self.anonymize_user_for_research(session, user_id, research_consent_granted=True)
            
            # Then anonymize identifiable data
            anonymous_id = self._generate_anonymous_id(user_id)
            
            # Update user record with anonymized data
            await session.execute(
                update(User).where(User.id == user_id).values(
                    email=f"anonymized_{anonymous_id[:8]}@deleted.local",
                    username=f"anonymized_{anonymous_id[:8]}",
                    first_name="[Anonymized]",
                    last_name="[User]",
                    is_active=False
                )
            )
            
        except Exception as e:
            self.logger.error(f"Error anonymizing user data: {e}")
            raise
    
    async def _partial_delete_user_data(
        self,
        session: AsyncSession,
        user_id: str,
        deletion_scope: Dict[str, Any]
    ) -> None:
        """Partially delete user data based on scope"""
        try:
            # Implement partial deletion based on scope
            # This is a simplified implementation
            
            if deletion_scope.get("practice_sessions"):
                await session.execute(
                    delete(SentenceAttempt).where(
                        SentenceAttempt.session_id.in_(
                            select(PracticeSession.id).where(PracticeSession.user_id == user_id)
                        )
                    )
                )
                await session.execute(
                    delete(PracticeSession).where(PracticeSession.user_id == user_id)
                )
            
            if deletion_scope.get("analytics_data"):
                await session.execute(
                    delete(AnalyticsEvent).where(AnalyticsEvent.user_id == user_id)
                )
            
        except Exception as e:
            self.logger.error(f"Error partially deleting user data: {e}")
            raise
    
    async def _schedule_research_data_anonymization(self, session: AsyncSession, user_id: str) -> None:
        """Schedule research data anonymization when consent is withdrawn"""
        try:
            # Create anonymized data before removing consent link
            await self.anonymize_user_for_research(session, user_id, research_consent_granted=False)
            
        except Exception as e:
            self.logger.error(f"Error scheduling research data anonymization: {e}")
    
    async def _process_data_export(self, request_id: str) -> None:
        """Process data export request in background"""
        # This would be implemented to generate export files
        # For now, just a placeholder
        self.logger.info(f"Processing data export request: {request_id}")
    
    async def _schedule_data_retention_cleanup(self) -> None:
        """Schedule periodic data retention cleanup"""
        import asyncio
        
        while True:
            try:
                await asyncio.sleep(86400)  # Run daily
                # Implement data retention cleanup
                self.logger.info("Running data retention cleanup")
                
            except Exception as e:
                self.logger.error(f"Data retention cleanup error: {e}")
    
    async def _schedule_export_cleanup(self) -> None:
        """Schedule cleanup of expired export files"""
        import asyncio
        
        while True:
            try:
                await asyncio.sleep(3600)  # Run hourly
                # Implement export file cleanup
                self.logger.info("Running export file cleanup")
                
            except Exception as e:
                self.logger.error(f"Export cleanup error: {e}")