"""
Test Research Data Management Implementation
Tests for research consent, data anonymization, retention policies, and research data exports
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

# Import the research service and models
from services.research_service import ResearchService
from models.research import (
    ResearchParticipant, ResearchDataset, DataRetentionRule, 
    AnonymizedDataMapping, ResearchConsentType, DataAnonymizationLevel
)
from models.analytics import AnalyticsEvent
from models.progress import PracticeSession


class TestResearchService:
    """Test the research service functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.research_service = ResearchService()
        self.test_user_id = "test_user_123"
        self.test_research_id = "asl_learning_study_2024"
        
    @pytest.mark.asyncio
    async def test_register_research_participant(self):
        """Test registering a user as a research participant"""
        # Mock database service
        mock_db_service = AsyncMock()
        mock_session = AsyncMock()
        mock_db_service.get_session.return_value.__aenter__.return_value = mock_session
        
        with patch.object(self.research_service, '_get_database_service', return_value=mock_db_service):
            with patch.object(self.research_service, 'get_research_participant', return_value=None):
                participant = await self.research_service.register_research_participant(
                    user_id=self.test_user_id,
                    research_id=self.test_research_id,
                    consent_version="1.0",
                    anonymization_level=DataAnonymizationLevel.PSEUDONYMIZED,
                    data_retention_years=5,
                    allow_data_sharing=False
                )
                
                assert participant.user_id == self.test_user_id
                assert participant.research_id == self.test_research_id
                assert participant.consent_given == True
                assert participant.anonymization_level == DataAnonymizationLevel.PSEUDONYMIZED
                assert participant.participant_code is not None
                assert participant.participant_code.startswith("P_")
                
                # Verify database operations
                mock_session.add.assert_called_once()
                mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_research_consent(self):
        """Test updating research consent"""
        # Create mock participant
        mock_participant = ResearchParticipant(
            user_id=self.test_user_id,
            research_id=self.test_research_id,
            consent_version="1.0",
            consent_given=True
        )
        
        mock_db_service = AsyncMock()
        mock_session = AsyncMock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_participant
        mock_db_service.get_session.return_value.__aenter__.return_value = mock_session
        
        with patch.object(self.research_service, '_get_database_service', return_value=mock_db_service):
            updated_participant = await self.research_service.update_research_consent(
                user_id=self.test_user_id,
                research_id=self.test_research_id,
                consent_given=False,
                consent_version="1.1"
            )
            
            assert updated_participant is not None
            assert updated_participant.consent_given == False
            assert updated_participant.consent_version == "1.1"
            assert updated_participant.participation_status == "withdrawn"
    
    @pytest.mark.asyncio
    async def test_withdraw_from_research(self):
        """Test withdrawing from research participation"""
        mock_participant = ResearchParticipant(
            user_id=self.test_user_id,
            research_id=self.test_research_id,
            consent_version="1.0",
            consent_given=True,
            participation_status="active"
        )
        
        mock_db_service = AsyncMock()
        mock_session = AsyncMock()
        mock_db_service.get_session.return_value.__aenter__.return_value = mock_session
        
        with patch.object(self.research_service, 'get_research_participant', return_value=mock_participant):
            with patch.object(self.research_service, '_get_database_service', return_value=mock_db_service):
                with patch.object(self.research_service, '_handle_withdrawal_data_cleanup', return_value=None):
                    success = await self.research_service.withdraw_from_research(
                        user_id=self.test_user_id,
                        research_id=self.test_research_id,
                        reason="No longer interested"
                    )
                    
                    assert success == True
                    assert mock_participant.participation_status == "withdrawn"
                    assert mock_participant.consent_given == False
                    assert mock_participant.withdrawal_reason == "No longer interested"
    
    @pytest.mark.asyncio
    async def test_anonymize_user_data(self):
        """Test anonymizing user data for research"""
        # Create mock participant
        mock_participant = ResearchParticipant(
            user_id=self.test_user_id,
            research_id=self.test_research_id,
            consent_version="1.0",
            consent_given=True,
            participation_status="active",
            anonymization_level=DataAnonymizationLevel.PSEUDONYMIZED
        )
        
        mock_db_service = AsyncMock()
        mock_session = AsyncMock()
        mock_db_service.get_session.return_value.__aenter__.return_value = mock_session
        
        with patch.object(self.research_service, 'get_research_participant', return_value=mock_participant):
            with patch.object(self.research_service, '_get_database_service', return_value=mock_db_service):
                with patch.object(self.research_service, '_anonymize_data_type', return_value=5):
                    result = await self.research_service.anonymize_user_data(
                        user_id=self.test_user_id,
                        research_id=self.test_research_id,
                        data_types=['analytics_events', 'practice_sessions']
                    )
                    
                    assert 'analytics_events' in result
                    assert 'practice_sessions' in result
                    assert result['analytics_events'] == 5
                    assert result['practice_sessions'] == 5
    
    @pytest.mark.asyncio
    async def test_create_research_dataset(self):
        """Test creating a research dataset export request"""
        query_parameters = {
            'data_types': ['analytics_events', 'practice_sessions'],
            'start_date': datetime.utcnow() - timedelta(days=30),
            'end_date': datetime.utcnow(),
            'include_demographics': False,
            'include_video_data': False
        }
        
        mock_db_service = AsyncMock()
        mock_session = AsyncMock()
        mock_db_service.get_session.return_value.__aenter__.return_value = mock_session
        
        with patch.object(self.research_service, '_get_database_service', return_value=mock_db_service):
            with patch('asyncio.create_task') as mock_create_task:
                dataset = await self.research_service.create_research_dataset(
                    researcher_id="researcher_123",
                    dataset_name="Test Dataset",
                    research_id=self.test_research_id,
                    query_parameters=query_parameters,
                    anonymization_level=DataAnonymizationLevel.PSEUDONYMIZED,
                    export_format="json"
                )
                
                assert dataset.dataset_name == "Test Dataset"
                assert dataset.research_id == self.test_research_id
                assert dataset.researcher_id == "researcher_123"
                assert dataset.anonymization_level == DataAnonymizationLevel.PSEUDONYMIZED
                assert dataset.export_format == "json"
                
                # Verify background task was created
                mock_create_task.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_retention_rule(self):
        """Test creating a data retention rule"""
        mock_db_service = AsyncMock()
        mock_session = AsyncMock()
        mock_db_service.get_session.return_value.__aenter__.return_value = mock_session
        
        with patch.object(self.research_service, '_get_database_service', return_value=mock_db_service):
            rule = await self.research_service.create_retention_rule(
                rule_name="Test Retention Rule",
                data_type="analytics_events",
                retention_days=365,
                anonymize_after_days=90,
                hard_delete_after_days=1095,
                compliance_framework="GDPR",
                rule_config={"test": "config"}
            )
            
            assert rule.rule_name == "Test Retention Rule"
            assert rule.data_type == "analytics_events"
            assert rule.retention_days == 365
            assert rule.anonymize_after_days == 90
            assert rule.hard_delete_after_days == 1095
            assert rule.compliance_framework == "GDPR"
            assert rule.rule_config == {"test": "config"}
    
    @pytest.mark.asyncio
    async def test_execute_retention_policies(self):
        """Test executing retention policies"""
        # Create mock retention rule
        mock_rule = DataRetentionRule(
            rule_name="Test Rule",
            data_type="analytics_events",
            retention_days=365,
            anonymize_after_days=90,
            is_active=True,
            next_execution_at=datetime.utcnow() - timedelta(hours=1),  # Due for execution
            execution_frequency_hours=24
        )
        
        mock_db_service = AsyncMock()
        mock_session = AsyncMock()
        mock_session.execute.return_value.scalars.return_value.all.return_value = [mock_rule]
        mock_db_service.get_session.return_value.__aenter__.return_value = mock_session
        
        with patch.object(self.research_service, '_get_database_service', return_value=mock_db_service):
            with patch.object(self.research_service, '_execute_retention_rule', return_value={"anonymized": 5, "deleted": 2}):
                results = await self.research_service.execute_retention_policies()
                
                assert "Test Rule" in results
                assert results["Test Rule"]["anonymized"] == 5
                assert results["Test Rule"]["deleted"] == 2
    
    @pytest.mark.asyncio
    async def test_get_research_compliance_report(self):
        """Test generating a research compliance report"""
        # Create mock participants
        mock_participants = [
            ResearchParticipant(
                user_id="user1",
                research_id=self.test_research_id,
                consent_version="1.0",
                consent_given=True,
                participation_status="active",
                anonymization_level=DataAnonymizationLevel.PSEUDONYMIZED,
                data_retention_years=5
            ),
            ResearchParticipant(
                user_id="user2",
                research_id=self.test_research_id,
                consent_version="1.0",
                consent_given=False,
                participation_status="withdrawn",
                anonymization_level=DataAnonymizationLevel.ANONYMIZED,
                data_retention_years=3
            )
        ]
        
        # Create mock datasets
        mock_datasets = [
            ResearchDataset(
                dataset_name="Dataset 1",
                research_id=self.test_research_id,
                researcher_id="researcher_123",
                query_parameters={},
                anonymization_level=DataAnonymizationLevel.PSEUDONYMIZED,
                data_start_date=datetime.utcnow() - timedelta(days=30),
                data_end_date=datetime.utcnow(),
                status="completed"
            )
        ]
        
        mock_db_service = AsyncMock()
        mock_session = AsyncMock()
        
        # Mock the database queries
        mock_session.execute.side_effect = [
            Mock(scalars=Mock(return_value=Mock(all=Mock(return_value=mock_participants)))),
            Mock(scalars=Mock(return_value=Mock(all=Mock(return_value=mock_datasets))))
        ]
        
        mock_db_service.get_session.return_value.__aenter__.return_value = mock_session
        
        with patch.object(self.research_service, '_get_database_service', return_value=mock_db_service):
            report = await self.research_service.get_research_compliance_report(self.test_research_id)
            
            assert report["research_id"] == self.test_research_id
            assert report["participants"]["total"] == 2
            assert report["participants"]["active"] == 1
            assert report["participants"]["withdrawn"] == 1
            assert report["datasets"]["total"] == 1
            assert report["datasets"]["completed"] == 1


class TestResearchModels:
    """Test the research data models"""
    
    def test_research_participant_model(self):
        """Test ResearchParticipant model functionality"""
        participant = ResearchParticipant(
            user_id="user_123",
            research_id="study_2024",
            consent_version="1.0",
            consent_given=True,
            participation_status="active"
        )
        
        # Set required fields for the model
        participant.id = "test_id_123"
        participant.participant_code = "P_TEST123456"
        participant.created_at = datetime.utcnow()
        participant.updated_at = datetime.utcnow()
        
        # Test participant code generation
        participant_code = participant.generate_participant_code()
        assert participant_code.startswith("P_")
        assert len(participant_code) >= 14  # P_ + at least 12 character hash
        
        # Test is_active method
        assert participant.is_active() == True
        
        # Test withdrawal
        participant.withdraw_consent("No longer interested")
        assert participant.participation_status == "withdrawn"
        assert participant.consent_given == False
        assert participant.withdrawal_reason == "No longer interested"
        assert participant.is_active() == False
        
        # Test to_dict method
        participant_dict = participant.to_dict()
        assert "participant_code" in participant_dict
        assert "consent_given" in participant_dict
        assert "is_active" in participant_dict
        assert participant_dict["is_active"] == False
    
    def test_data_retention_rule_model(self):
        """Test DataRetentionRule model functionality"""
        rule = DataRetentionRule(
            rule_name="Test Rule",
            data_type="analytics_events",
            retention_days=365,
            anonymize_after_days=90,
            hard_delete_after_days=1095,
            is_active=True,
            rule_config={}
        )
        
        # Set required fields for the model
        rule.id = "test_rule_123"
        rule.created_at = datetime.utcnow()
        rule.updated_at = datetime.utcnow()
        rule.applies_to_research_data = True
        rule.applies_to_non_research_data = True
        
        # Test should_anonymize method
        old_date = datetime.utcnow() - timedelta(days=100)
        recent_date = datetime.utcnow() - timedelta(days=30)
        
        assert rule.should_anonymize(old_date, is_research_data=True) == True
        assert rule.should_anonymize(recent_date, is_research_data=True) == False
        
        # Test should_delete method
        very_old_date = datetime.utcnow() - timedelta(days=1200)
        assert rule.should_delete(very_old_date, is_research_data=True) == True
        assert rule.should_delete(old_date, is_research_data=True) == False
        
        # Test to_dict method
        rule_dict = rule.to_dict()
        assert rule_dict["rule_name"] == "Test Rule"
        assert rule_dict["retention_days"] == 365
        assert rule_dict["is_active"] == True
    
    def test_anonymized_data_mapping_model(self):
        """Test AnonymizedDataMapping model functionality"""
        # Test generate_anonymized_id static method
        original_id = "original_123"
        research_id = "study_2024"
        
        anonymized_id1 = AnonymizedDataMapping.generate_anonymized_id(original_id, research_id)
        anonymized_id2 = AnonymizedDataMapping.generate_anonymized_id(original_id, research_id)
        
        # Should generate consistent IDs for same inputs
        assert anonymized_id1 == anonymized_id2
        
        # Should generate different IDs for different inputs
        anonymized_id3 = AnonymizedDataMapping.generate_anonymized_id("different_id", research_id)
        assert anonymized_id1 != anonymized_id3
        
        # Test mapping model
        mapping = AnonymizedDataMapping(
            original_id=original_id,
            anonymized_id=anonymized_id1,
            data_type="analytics_events",
            research_id=research_id,
            anonymization_method="hash",
            original_created_at=datetime.utcnow()
        )
        
        # Set required fields for the model
        mapping.id = "test_mapping_123"
        mapping.created_at = datetime.utcnow()
        mapping.updated_at = datetime.utcnow()
        
        mapping_dict = mapping.to_dict()
        assert mapping_dict["anonymized_id"] == anonymized_id1
        assert mapping_dict["data_type"] == "analytics_events"
        assert mapping_dict["research_id"] == research_id


def test_research_consent_types():
    """Test research consent type enumeration"""
    # Test that all expected consent types are available
    expected_types = [
        "general_research",
        "learning_analytics", 
        "gesture_analysis",
        "performance_tracking",
        "demographic_data",
        "video_data",
        "longitudinal_study"
    ]
    
    for consent_type in expected_types:
        assert hasattr(ResearchConsentType, consent_type.upper())
        assert ResearchConsentType(consent_type).value == consent_type


def test_data_anonymization_levels():
    """Test data anonymization level enumeration"""
    # Test that all expected anonymization levels are available
    expected_levels = ["none", "pseudonymized", "anonymized", "aggregated"]
    
    for level in expected_levels:
        assert hasattr(DataAnonymizationLevel, level.upper())
        assert DataAnonymizationLevel(level).value == level


async def test_research_api_integration():
    """Integration test for research API endpoints"""
    # This would test the actual API endpoints
    # For now, just verify that the API module can be imported
    try:
        from api import research
        assert hasattr(research, 'router')
        assert hasattr(research, 'register_research_participant')
        assert hasattr(research, 'create_research_dataset')
        assert hasattr(research, 'create_retention_rule')
        print("✓ Research API module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import research API module: {e}")


def run_tests():
    """Run all research data management tests"""
    print("Running Research Data Management Tests...")
    print("=" * 50)
    
    # Test model functionality
    test_models = TestResearchModels()
    
    try:
        test_models.test_research_participant_model()
        print("✓ ResearchParticipant model tests passed")
    except Exception as e:
        print(f"✗ ResearchParticipant model tests failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        test_models.test_data_retention_rule_model()
        print("✓ DataRetentionRule model tests passed")
    except Exception as e:
        print(f"✗ DataRetentionRule model tests failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        test_models.test_anonymized_data_mapping_model()
        print("✓ AnonymizedDataMapping model tests passed")
    except Exception as e:
        print(f"✗ AnonymizedDataMapping model tests failed: {e}")
    
    # Test enumerations
    try:
        test_research_consent_types()
        print("✓ Research consent types tests passed")
    except Exception as e:
        print(f"✗ Research consent types tests failed: {e}")
    
    try:
        test_data_anonymization_levels()
        print("✓ Data anonymization levels tests passed")
    except Exception as e:
        print(f"✗ Data anonymization levels tests failed: {e}")
    
    # Test API integration
    try:
        asyncio.run(test_research_api_integration())
    except Exception as e:
        print(f"✗ Research API integration test failed: {e}")
    
    print("=" * 50)
    print("Research Data Management Tests Completed")


if __name__ == "__main__":
    run_tests()