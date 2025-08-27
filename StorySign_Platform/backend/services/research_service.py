"""
Research Data Management Service
Handles research consent, data anonymization, retention policies, and research data exports
"""

from typing import Dict, Any, Optional, List, Union
import uuid
import json
import hashlib
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.base_service import BaseService
from models.research import (
    ResearchParticipant, ResearchDataset, DataRetentionRule, 
    AnonymizedDataMapping, ResearchConsentType, DataAnonymizationLevel
)
from models.analytics import AnalyticsEvent, UserConsent
from models.progress import PracticeSession, SentenceAttempt
from models.user import User
import logging


class ResearchService(BaseService):
    """Service for managing research data, consent, and privacy compliance"""
    
    def __init__(self, service_name: str = "ResearchService", config: Optional[Dict[str, Any]] = None):
        super().__init__(service_name, config)
        self.database_service: Optional[Any] = None
        self._anonymization_cache: Dict[str, str] = {}
        
    async def initialize(self) -> None:
        """Initialize research service"""
        self.logger.info("Research service initialized")
    
    async def cleanup(self) -> None:
        """Clean up research service"""
        self.database_service = None
        self._anonymization_cache.clear()
        
    async def _get_database_service(self) -> Any:
        """Get database service lazily"""
        if self.database_service is None:
            from core.service_container import get_service_container
            container = get_service_container()
            self.database_service = await container.get_service("DatabaseService")
        return self.database_service

    # Research Participation Management
    
    async def register_research_participant(
        self,
        user_id: str,
        research_id: str,
        consent_version: str,
        anonymization_level: DataAnonymizationLevel = DataAnonymizationLevel.PSEUDONYMIZED,
        data_retention_years: int = 5,
        allow_data_sharing: bool = False,
        research_metadata: Optional[Dict[str, Any]] = None
    ) -> ResearchParticipant:
        """Register a user as a research participant"""
        try:
            db_service = await self._get_database_service()
            
            # Check if participant already exists
            existing = await self.get_research_participant(user_id, research_id)
            if existing:
                raise ValueError(f"User {user_id} is already registered for research {research_id}")
            
            # Create new participant
            participant = ResearchParticipant(
                user_id=user_id,
                research_id=research_id,
                consent_version=consent_version,
                consent_given=True,
                consent_date=datetime.utcnow(),
                study_start_date=datetime.utcnow(),
                anonymization_level=anonymization_level,
                data_retention_years=data_retention_years,
                allow_data_sharing=allow_data_sharing,
                research_metadata=research_metadata or {}
            )
            
            # Generate unique participant code
            participant.participant_code = participant.generate_participant_code()
            
            # Save to database
            async with db_service.get_session() as session:
                session.add(participant)
                await session.commit()
                await session.refresh(participant)
            
            self.logger.info(f"Registered research participant {participant.participant_code} for study {research_id}")
            return participant
            
        except Exception as e:
            self.logger.error(f"Error registering research participant: {str(e)}")
            raise

    async def get_research_participant(
        self,
        user_id: str,
        research_id: str
    ) -> Optional[ResearchParticipant]:
        """Get research participant by user and research ID"""
        try:
            db_service = await self._get_database_service()
            
            async with db_service.get_session() as session:
                result = await session.execute(
                    select(ResearchParticipant).where(
                        and_(
                            ResearchParticipant.user_id == user_id,
                            ResearchParticipant.research_id == research_id
                        )
                    )
                )
                return result.scalar_one_or_none()
                
        except Exception as e:
            self.logger.error(f"Error getting research participant: {str(e)}")
            return None

    async def update_research_consent(
        self,
        user_id: str,
        research_id: str,
        consent_given: bool,
        consent_version: Optional[str] = None
    ) -> Optional[ResearchParticipant]:
        """Update research consent for a participant"""
        try:
            db_service = await self._get_database_service()
            
            async with db_service.get_session() as session:
                participant = await session.execute(
                    select(ResearchParticipant).where(
                        and_(
                            ResearchParticipant.user_id == user_id,
                            ResearchParticipant.research_id == research_id
                        )
                    )
                )
                participant = participant.scalar_one_or_none()
                
                if not participant:
                    return None
                
                participant.consent_given = consent_given
                if consent_version:
                    participant.consent_version = consent_version
                
                if not consent_given:
                    participant.withdraw_consent()
                
                await session.commit()
                await session.refresh(participant)
                
                self.logger.info(f"Updated consent for participant {participant.participant_code}: {consent_given}")
                return participant
                
        except Exception as e:
            self.logger.error(f"Error updating research consent: {str(e)}")
            raise

    async def withdraw_from_research(
        self,
        user_id: str,
        research_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """Withdraw user from research participation"""
        try:
            participant = await self.get_research_participant(user_id, research_id)
            if not participant:
                return False
            
            participant.withdraw_consent(reason)
            
            db_service = await self._get_database_service()
            async with db_service.get_session() as session:
                await session.merge(participant)
                await session.commit()
            
            # Optionally anonymize or delete existing research data
            await self._handle_withdrawal_data_cleanup(user_id, research_id)
            
            self.logger.info(f"User {user_id} withdrew from research {research_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error withdrawing from research: {str(e)}")
            return False

    # Data Anonymization
    
    async def anonymize_user_data(
        self,
        user_id: str,
        research_id: str,
        data_types: Optional[List[str]] = None
    ) -> Dict[str, int]:
        """Anonymize user data for research purposes"""
        try:
            db_service = await self._get_database_service()
            anonymized_counts = {}
            
            # Get participant to check anonymization level
            participant = await self.get_research_participant(user_id, research_id)
            if not participant or not participant.is_active():
                raise ValueError("User is not an active research participant")
            
            data_types = data_types or ['analytics_events', 'practice_sessions', 'sentence_attempts']
            
            async with db_service.get_session() as session:
                for data_type in data_types:
                    count = await self._anonymize_data_type(
                        session, user_id, research_id, data_type, participant.anonymization_level
                    )
                    anonymized_counts[data_type] = count
                
                await session.commit()
            
            self.logger.info(f"Anonymized data for user {user_id} in research {research_id}: {anonymized_counts}")
            return anonymized_counts
            
        except Exception as e:
            self.logger.error(f"Error anonymizing user data: {str(e)}")
            raise

    async def _anonymize_data_type(
        self,
        session: AsyncSession,
        user_id: str,
        research_id: str,
        data_type: str,
        anonymization_level: DataAnonymizationLevel
    ) -> int:
        """Anonymize specific data type for a user"""
        count = 0
        
        if data_type == 'analytics_events':
            # Anonymize analytics events
            result = await session.execute(
                select(AnalyticsEvent).where(AnalyticsEvent.user_id == user_id)
            )
            events = result.scalars().all()
            
            for event in events:
                if anonymization_level == DataAnonymizationLevel.ANONYMIZED:
                    event.anonymize()
                elif anonymization_level == DataAnonymizationLevel.PSEUDONYMIZED:
                    # Create pseudonymized mapping
                    anonymized_id = AnonymizedDataMapping.generate_anonymized_id(
                        event.id, research_id
                    )
                    await self._create_anonymization_mapping(
                        session, event.id, anonymized_id, data_type, research_id, event.created_at
                    )
                    event.user_id = anonymized_id
                
                count += 1
        
        elif data_type == 'practice_sessions':
            # Anonymize practice sessions
            result = await session.execute(
                select(PracticeSession).where(PracticeSession.user_id == user_id)
            )
            sessions = result.scalars().all()
            
            for session_obj in sessions:
                if anonymization_level == DataAnonymizationLevel.PSEUDONYMIZED:
                    anonymized_id = AnonymizedDataMapping.generate_anonymized_id(
                        session_obj.id, research_id
                    )
                    await self._create_anonymization_mapping(
                        session, session_obj.id, anonymized_id, data_type, research_id, session_obj.created_at
                    )
                    session_obj.user_id = anonymized_id
                
                count += 1
        
        return count

    async def _create_anonymization_mapping(
        self,
        session: AsyncSession,
        original_id: str,
        anonymized_id: str,
        data_type: str,
        research_id: str,
        original_created_at: datetime
    ) -> None:
        """Create anonymization mapping record"""
        mapping = AnonymizedDataMapping(
            original_id=original_id,
            anonymized_id=anonymized_id,
            data_type=data_type,
            research_id=research_id,
            anonymization_method="hash",
            original_created_at=original_created_at,
            expires_at=datetime.utcnow() + timedelta(days=365 * 7)  # 7 years default
        )
        session.add(mapping)

    # Research Data Queries and Export
    
    async def create_research_dataset(
        self,
        researcher_id: str,
        dataset_name: str,
        research_id: str,
        query_parameters: Dict[str, Any],
        anonymization_level: DataAnonymizationLevel = DataAnonymizationLevel.PSEUDONYMIZED,
        export_format: str = "json"
    ) -> ResearchDataset:
        """Create a research dataset export request"""
        try:
            db_service = await self._get_database_service()
            
            dataset = ResearchDataset(
                dataset_name=dataset_name,
                research_id=research_id,
                researcher_id=researcher_id,
                query_parameters=query_parameters,
                anonymization_level=anonymization_level,
                export_format=export_format,
                data_start_date=query_parameters.get('start_date', datetime.utcnow() - timedelta(days=365)),
                data_end_date=query_parameters.get('end_date', datetime.utcnow()),
                include_demographics=query_parameters.get('include_demographics', False),
                include_video_data=query_parameters.get('include_video_data', False),
                expires_at=datetime.utcnow() + timedelta(days=30)  # 30 days default expiration
            )
            
            async with db_service.get_session() as session:
                session.add(dataset)
                await session.commit()
                await session.refresh(dataset)
            
            # Start background processing
            asyncio.create_task(self._process_research_dataset(dataset.id))
            
            self.logger.info(f"Created research dataset {dataset.id} for researcher {researcher_id}")
            return dataset
            
        except Exception as e:
            self.logger.error(f"Error creating research dataset: {str(e)}")
            raise

    async def _process_research_dataset(self, dataset_id: str) -> None:
        """Process research dataset in background"""
        try:
            db_service = await self._get_database_service()
            
            async with db_service.get_session() as session:
                result = await session.execute(
                    select(ResearchDataset).where(ResearchDataset.id == dataset_id)
                )
                dataset = result.scalar_one_or_none()
                
                if not dataset:
                    return
                
                # Update status to processing
                dataset.status = "processing"
                dataset.processing_started_at = datetime.utcnow()
                await session.commit()
                
                try:
                    # Generate the dataset
                    data = await self._generate_research_data(dataset)
                    
                    # Save to file (in production, this would be to cloud storage)
                    file_path = f"/tmp/research_datasets/{dataset_id}.{dataset.export_format}"
                    await self._save_dataset_file(data, file_path, dataset.export_format)
                    
                    # Update dataset with results
                    dataset.status = "completed"
                    dataset.processing_completed_at = datetime.utcnow()
                    dataset.file_path = file_path
                    dataset.record_count = len(data.get('records', []))
                    dataset.file_size_bytes = await self._get_file_size(file_path)
                    
                except Exception as e:
                    dataset.status = "failed"
                    dataset.error_message = str(e)
                    self.logger.error(f"Error processing dataset {dataset_id}: {str(e)}")
                
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Error in dataset processing: {str(e)}")

    async def _generate_research_data(self, dataset: ResearchDataset) -> Dict[str, Any]:
        """Generate research data based on dataset parameters"""
        db_service = await self._get_database_service()
        
        # Get active research participants for this study
        async with db_service.get_session() as session:
            participants_result = await session.execute(
                select(ResearchParticipant).where(
                    and_(
                        ResearchParticipant.research_id == dataset.research_id,
                        ResearchParticipant.consent_given == True,
                        ResearchParticipant.participation_status == "active"
                    )
                )
            )
            participants = participants_result.scalars().all()
            
            if not participants:
                return {"records": [], "metadata": {"participant_count": 0}}
            
            # Collect data based on query parameters
            records = []
            
            for participant in participants:
                participant_data = await self._collect_participant_data(
                    session, participant, dataset
                )
                if participant_data:
                    records.extend(participant_data)
            
            return {
                "records": records,
                "metadata": {
                    "participant_count": len(participants),
                    "research_id": dataset.research_id,
                    "anonymization_level": dataset.anonymization_level.value,
                    "generated_at": datetime.utcnow().isoformat(),
                    "data_range": {
                        "start_date": dataset.data_start_date.isoformat(),
                        "end_date": dataset.data_end_date.isoformat()
                    }
                }
            }

    async def _collect_participant_data(
        self,
        session: AsyncSession,
        participant: ResearchParticipant,
        dataset: ResearchDataset
    ) -> List[Dict[str, Any]]:
        """Collect data for a specific participant"""
        records = []
        
        # Determine user identifier based on anonymization level
        if dataset.anonymization_level == DataAnonymizationLevel.ANONYMIZED:
            user_identifier = None
        elif dataset.anonymization_level == DataAnonymizationLevel.PSEUDONYMIZED:
            user_identifier = participant.participant_code
        else:
            user_identifier = participant.user_id
        
        # Collect analytics events
        if 'analytics_events' in dataset.query_parameters.get('data_types', []):
            events_result = await session.execute(
                select(AnalyticsEvent).where(
                    and_(
                        AnalyticsEvent.user_id == participant.user_id,
                        AnalyticsEvent.occurred_at >= dataset.data_start_date,
                        AnalyticsEvent.occurred_at <= dataset.data_end_date
                    )
                )
            )
            events = events_result.scalars().all()
            
            for event in events:
                record = {
                    'record_type': 'analytics_event',
                    'participant_id': user_identifier,
                    'event_type': event.event_type,
                    'module_name': event.module_name,
                    'occurred_at': event.occurred_at.isoformat(),
                    'event_data': event.event_data if dataset.anonymization_level != DataAnonymizationLevel.AGGREGATED else None
                }
                records.append(record)
        
        # Collect practice sessions
        if 'practice_sessions' in dataset.query_parameters.get('data_types', []):
            sessions_result = await session.execute(
                select(PracticeSession).where(
                    and_(
                        PracticeSession.user_id == participant.user_id,
                        PracticeSession.started_at >= dataset.data_start_date,
                        PracticeSession.started_at <= dataset.data_end_date
                    )
                )
            )
            sessions = sessions_result.scalars().all()
            
            for session_obj in sessions:
                record = {
                    'record_type': 'practice_session',
                    'participant_id': user_identifier,
                    'session_type': session_obj.session_type,
                    'overall_score': session_obj.overall_score,
                    'sentences_completed': session_obj.sentences_completed,
                    'started_at': session_obj.started_at.isoformat(),
                    'completed_at': session_obj.completed_at.isoformat() if session_obj.completed_at else None,
                    'performance_metrics': session_obj.performance_metrics if dataset.anonymization_level != DataAnonymizationLevel.AGGREGATED else None
                }
                records.append(record)
        
        return records

    async def _save_dataset_file(
        self,
        data: Dict[str, Any],
        file_path: str,
        format: str
    ) -> None:
        """Save dataset to file"""
        import os
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        if format == "json":
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        elif format == "csv":
            import pandas as pd
            df = pd.DataFrame(data['records'])
            df.to_csv(file_path, index=False)
        # Add other formats as needed

    async def _get_file_size(self, file_path: str) -> int:
        """Get file size in bytes"""
        import os
        try:
            return os.path.getsize(file_path)
        except:
            return 0

    # Data Retention and Deletion
    
    async def create_retention_rule(
        self,
        rule_name: str,
        data_type: str,
        retention_days: int,
        anonymize_after_days: Optional[int] = None,
        hard_delete_after_days: Optional[int] = None,
        compliance_framework: Optional[str] = None,
        rule_config: Optional[Dict[str, Any]] = None
    ) -> DataRetentionRule:
        """Create a data retention rule"""
        try:
            db_service = await self._get_database_service()
            
            rule = DataRetentionRule(
                rule_name=rule_name,
                data_type=data_type,
                retention_days=retention_days,
                anonymize_after_days=anonymize_after_days,
                hard_delete_after_days=hard_delete_after_days,
                compliance_framework=compliance_framework,
                rule_config=rule_config or {},
                next_execution_at=datetime.utcnow() + timedelta(hours=24)
            )
            
            async with db_service.get_session() as session:
                session.add(rule)
                await session.commit()
                await session.refresh(rule)
            
            self.logger.info(f"Created retention rule {rule_name} for {data_type}")
            return rule
            
        except Exception as e:
            self.logger.error(f"Error creating retention rule: {str(e)}")
            raise

    async def execute_retention_policies(self) -> Dict[str, int]:
        """Execute all active retention policies"""
        try:
            db_service = await self._get_database_service()
            results = {}
            
            async with db_service.get_session() as session:
                # Get all active retention rules that are due for execution
                rules_result = await session.execute(
                    select(DataRetentionRule).where(
                        and_(
                            DataRetentionRule.is_active == True,
                            DataRetentionRule.next_execution_at <= datetime.utcnow()
                        )
                    )
                )
                rules = rules_result.scalars().all()
                
                for rule in rules:
                    try:
                        result = await self._execute_retention_rule(session, rule)
                        results[rule.rule_name] = result
                        
                        # Update next execution time
                        rule.last_executed_at = datetime.utcnow()
                        rule.next_execution_at = datetime.utcnow() + timedelta(hours=rule.execution_frequency_hours)
                        
                    except Exception as e:
                        self.logger.error(f"Error executing retention rule {rule.rule_name}: {str(e)}")
                        results[rule.rule_name] = {"error": str(e)}
                
                await session.commit()
            
            self.logger.info(f"Executed retention policies: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error executing retention policies: {str(e)}")
            raise

    async def _execute_retention_rule(
        self,
        session: AsyncSession,
        rule: DataRetentionRule
    ) -> Dict[str, int]:
        """Execute a specific retention rule"""
        results = {"anonymized": 0, "deleted": 0}
        
        # This is a simplified implementation - in production, you'd want more sophisticated logic
        if rule.data_type == "analytics_events":
            # Handle analytics events retention
            cutoff_date = datetime.utcnow() - timedelta(days=rule.retention_days)
            
            if rule.anonymize_after_days:
                anonymize_date = datetime.utcnow() - timedelta(days=rule.anonymize_after_days)
                # Anonymize old events
                events_to_anonymize = await session.execute(
                    select(AnalyticsEvent).where(
                        and_(
                            AnalyticsEvent.created_at <= anonymize_date,
                            AnalyticsEvent.is_anonymous == False
                        )
                    )
                )
                for event in events_to_anonymize.scalars():
                    event.anonymize()
                    results["anonymized"] += 1
            
            # Delete very old events
            if rule.hard_delete_after_days:
                delete_date = datetime.utcnow() - timedelta(days=rule.hard_delete_after_days)
                delete_result = await session.execute(
                    delete(AnalyticsEvent).where(AnalyticsEvent.created_at <= delete_date)
                )
                results["deleted"] = delete_result.rowcount
        
        return results

    async def _handle_withdrawal_data_cleanup(
        self,
        user_id: str,
        research_id: str
    ) -> None:
        """Handle data cleanup when user withdraws from research"""
        try:
            # This could involve anonymizing or deleting the user's research data
            # depending on the research requirements and legal obligations
            await self.anonymize_user_data(user_id, research_id)
            self.logger.info(f"Completed data cleanup for withdrawn participant {user_id}")
            
        except Exception as e:
            self.logger.error(f"Error in withdrawal data cleanup: {str(e)}")

    # Utility Methods
    
    async def get_research_compliance_report(
        self,
        research_id: str
    ) -> Dict[str, Any]:
        """Generate compliance report for a research study"""
        try:
            db_service = await self._get_database_service()
            
            async with db_service.get_session() as session:
                # Get participant statistics
                participants_result = await session.execute(
                    select(ResearchParticipant).where(ResearchParticipant.research_id == research_id)
                )
                participants = participants_result.scalars().all()
                
                active_count = sum(1 for p in participants if p.is_active())
                withdrawn_count = sum(1 for p in participants if p.participation_status == "withdrawn")
                
                # Get dataset statistics
                datasets_result = await session.execute(
                    select(ResearchDataset).where(ResearchDataset.research_id == research_id)
                )
                datasets = datasets_result.scalars().all()
                
                return {
                    "research_id": research_id,
                    "generated_at": datetime.utcnow().isoformat(),
                    "participants": {
                        "total": len(participants),
                        "active": active_count,
                        "withdrawn": withdrawn_count,
                        "consent_versions": list(set(p.consent_version for p in participants))
                    },
                    "datasets": {
                        "total": len(datasets),
                        "completed": sum(1 for d in datasets if d.status == "completed"),
                        "processing": sum(1 for d in datasets if d.status == "processing"),
                        "failed": sum(1 for d in datasets if d.status == "failed")
                    },
                    "data_retention": {
                        "anonymization_levels": [p.anonymization_level.value for p in participants],
                        "retention_periods": [p.data_retention_years for p in participants]
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Error generating compliance report: {str(e)}")
            raise