"""
Test privacy and GDPR compliance features
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.ext.asyncio import AsyncSession

# Test imports
try:
    from services.privacy_service import PrivacyService
    from models.privacy import (
        ConsentType, ConsentStatus, DataProcessingPurpose, 
        DataRetentionPolicy, UserConsent, PrivacySettings,
        DataDeletionRequest, DataExportRequest, AnonymizedUserData
    )
    from models.user import User
    from core.database_service import DatabaseService
    PRIVACY_AVAILABLE = True
except ImportError as e:
    print(f"Privacy imports not available: {e}")
    PRIVACY_AVAILABLE = False


class TestPrivacyCompliance:
    """Test privacy and GDPR compliance functionality"""
    
    @pytest.fixture
    async def privacy_service(self):
        """Create privacy service for testing"""
        if not PRIVACY_AVAILABLE:
            pytest.skip("Privacy service not available")
        
        config = {
            "gdpr_enabled": True,
            "data_retention_days": 365,
            "anonymization_salt": "test_salt_2024"
        }
        service = PrivacyService(config=config)
        await service.initialize()
        return service
    
    @pytest.fixture
    async def mock_db_session(self):
        """Create mock database session"""
        session = Mock(spec=AsyncSession)
        session.execute = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        return session
    
    @pytest.fixture
    def sample_user_id(self):
        """Sample user ID for testing"""
        return "test-user-123"
    
    def test_privacy_service_initialization(self):
        """Test privacy service initialization"""
        if not PRIVACY_AVAILABLE:
            pytest.skip("Privacy service not available")
        
        config = {
            "gdpr_enabled": True,
            "data_retention_days": 730
        }
        service = PrivacyService(config=config)
        
        assert service.gdpr_enabled == True
        assert service.data_retention_days == 730
        assert service.consent_version == "1.0"
    
    @pytest.mark.asyncio
    async def test_consent_management(self, privacy_service, mock_db_session, sample_user_id):
        """Test consent granting and withdrawal"""
        if not PRIVACY_AVAILABLE:
            pytest.skip("Privacy service not available")
        
        # Mock database responses
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        
        # Test granting consent
        consent_record = await privacy_service.grant_consent(
            session=mock_db_session,
            user_id=sample_user_id,
            consent_type=ConsentType.RESEARCH_PARTICIPATION,
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            consent_details={"version": "1.0", "method": "web_form"}
        )
        
        assert consent_record.user_id == sample_user_id
        assert consent_record.consent_type == ConsentType.RESEARCH_PARTICIPATION.value
        assert consent_record.status == ConsentStatus.GRANTED.value
        assert consent_record.ip_address == "192.168.1.1"
        
        # Verify database calls
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_consent_withdrawal(self, privacy_service, mock_db_session, sample_user_id):
        """Test consent withdrawal"""
        if not PRIVACY_AVAILABLE:
            pytest.skip("Privacy service not available")
        
        # Mock existing consent
        existing_consent = Mock()
        existing_consent.status = ConsentStatus.GRANTED.value
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = existing_consent
        
        # Test withdrawing consent
        success = await privacy_service.withdraw_consent(
            session=mock_db_session,
            user_id=sample_user_id,
            consent_type=ConsentType.RESEARCH_PARTICIPATION,
            withdrawal_reason="No longer interested",
            ip_address="192.168.1.1"
        )
        
        assert success == True
        assert existing_consent.status == ConsentStatus.WITHDRAWN.value
        assert existing_consent.withdrawal_reason == "No longer interested"
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_check_consent(self, privacy_service, mock_db_session, sample_user_id):
        """Test consent checking"""
        if not PRIVACY_AVAILABLE:
            pytest.skip("Privacy service not available")
        
        # Mock active consent
        mock_consent = Mock()
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_consent
        
        has_consent = await privacy_service.check_consent(
            session=mock_db_session,
            user_id=sample_user_id,
            consent_type=ConsentType.ANALYTICS_TRACKING
        )
        
        assert has_consent == True
        
        # Test no consent
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        
        has_consent = await privacy_service.check_consent(
            session=mock_db_session,
            user_id=sample_user_id,
            consent_type=ConsentType.ANALYTICS_TRACKING
        )
        
        assert has_consent == False
    
    @pytest.mark.asyncio
    async def test_data_processing_record(self, privacy_service, mock_db_session, sample_user_id):
        """Test data processing recording"""
        if not PRIVACY_AVAILABLE:
            pytest.skip("Privacy service not available")
        
        record = await privacy_service.record_data_processing(
            session=mock_db_session,
            user_id=sample_user_id,
            purpose=DataProcessingPurpose.RESEARCH_ANALYTICS,
            data_categories=["practice_sessions", "performance_metrics"],
            legal_basis="consent",
            processor_id="analytics_engine_v1",
            retention_policy=DataRetentionPolicy.ONE_YEAR,
            processing_details={"algorithm": "ml_analysis", "version": "2.1"}
        )
        
        assert record.user_id == sample_user_id
        assert record.processing_purpose == DataProcessingPurpose.RESEARCH_ANALYTICS.value
        assert record.data_categories == ["practice_sessions", "performance_metrics"]
        assert record.legal_basis == "consent"
        assert record.retention_policy == DataRetentionPolicy.ONE_YEAR.value
        
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_data_deletion_request(self, privacy_service, mock_db_session, sample_user_id):
        """Test data deletion request"""
        if not PRIVACY_AVAILABLE:
            pytest.skip("Privacy service not available")
        
        deletion_request = await privacy_service.request_data_deletion(
            session=mock_db_session,
            user_id=sample_user_id,
            request_type="full_deletion",
            deletion_scope={"include_analytics": True, "include_practice_data": True}
        )
        
        assert deletion_request.user_id == sample_user_id
        assert deletion_request.request_type == "full_deletion"
        assert deletion_request.status == "pending"
        assert deletion_request.verification_token is not None
        assert deletion_request.verification_expires > datetime.utcnow()
        
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_data_export_request(self, privacy_service, mock_db_session, sample_user_id):
        """Test data export request"""
        if not PRIVACY_AVAILABLE:
            pytest.skip("Privacy service not available")
        
        export_request = await privacy_service.request_data_export(
            session=mock_db_session,
            user_id=sample_user_id,
            export_format="json",
            export_scope={"include_profile": True, "include_progress": True}
        )
        
        assert export_request.user_id == sample_user_id
        assert export_request.export_format == "json"
        assert export_request.status == "pending"
        assert export_request.download_token is not None
        assert export_request.expires_at > datetime.utcnow()
        
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_privacy_settings_management(self, privacy_service, mock_db_session, sample_user_id):
        """Test privacy settings management"""
        if not PRIVACY_AVAILABLE:
            pytest.skip("Privacy service not available")
        
        # Test getting non-existent settings
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        
        settings = await privacy_service.get_privacy_settings(
            session=mock_db_session,
            user_id=sample_user_id
        )
        
        assert settings is None
        
        # Test updating settings
        settings_update = {
            "allow_research_participation": True,
            "allow_analytics_tracking": False,
            "data_retention_preference": "seven_years"
        }
        
        updated_settings = await privacy_service.update_privacy_settings(
            session=mock_db_session,
            user_id=sample_user_id,
            settings_update=settings_update,
            ip_address="192.168.1.1"
        )
        
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
    
    @pytest.mark.asyncio
    async def test_user_anonymization(self, privacy_service, mock_db_session, sample_user_id):
        """Test user data anonymization"""
        if not PRIVACY_AVAILABLE:
            pytest.skip("Privacy service not available")
        
        # Mock user data
        mock_user = Mock()
        mock_user.id = sample_user_id
        mock_user.user_profile = Mock()
        mock_user.user_profile.age = 28
        mock_user.user_profile.location = "United States"
        mock_user.user_profile.language = "en"
        mock_user.practice_sessions = []
        mock_user.user_progress = []
        
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = mock_user
        
        # Mock consent check
        with patch.object(privacy_service, 'check_consent', return_value=True):
            anonymized_data = await privacy_service.anonymize_user_for_research(
                session=mock_db_session,
                user_id=sample_user_id,
                research_consent_granted=True
            )
        
        assert anonymized_data.original_user_id == sample_user_id
        assert anonymized_data.age_range == "25-34"
        assert anonymized_data.region == "north_america"
        assert anonymized_data.research_consent_granted == True
        assert anonymized_data.anonymous_id is not None
        
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()
    
    def test_anonymous_id_generation(self, privacy_service, sample_user_id):
        """Test anonymous ID generation"""
        if not PRIVACY_AVAILABLE:
            pytest.skip("Privacy service not available")
        
        anonymous_id1 = privacy_service._generate_anonymous_id(sample_user_id)
        anonymous_id2 = privacy_service._generate_anonymous_id(sample_user_id)
        
        # Same input should produce same output
        assert anonymous_id1 == anonymous_id2
        
        # Different input should produce different output
        different_id = privacy_service._generate_anonymous_id("different-user")
        assert anonymous_id1 != different_id
        
        # Should be a valid hex string
        assert len(anonymous_id1) == 64  # SHA256 hex length
        assert all(c in '0123456789abcdef' for c in anonymous_id1)
    
    def test_age_anonymization(self, privacy_service):
        """Test age anonymization into ranges"""
        if not PRIVACY_AVAILABLE:
            pytest.skip("Privacy service not available")
        
        assert privacy_service._anonymize_age(16) == "under_18"
        assert privacy_service._anonymize_age(22) == "18-24"
        assert privacy_service._anonymize_age(30) == "25-34"
        assert privacy_service._anonymize_age(40) == "35-44"
        assert privacy_service._anonymize_age(50) == "45-54"
        assert privacy_service._anonymize_age(60) == "55-64"
        assert privacy_service._anonymize_age(70) == "65_plus"
        assert privacy_service._anonymize_age(None) is None
    
    def test_location_anonymization(self, privacy_service):
        """Test location anonymization into regions"""
        if not PRIVACY_AVAILABLE:
            pytest.skip("Privacy service not available")
        
        assert privacy_service._anonymize_location("United States") == "north_america"
        assert privacy_service._anonymize_location("USA") == "north_america"
        assert privacy_service._anonymize_location("Canada") == "north_america"
        assert privacy_service._anonymize_location("United Kingdom") == "uk_ireland"
        assert privacy_service._anonymize_location("Germany") == "western_europe"
        assert privacy_service._anonymize_location("Australia") == "oceania"
        assert privacy_service._anonymize_location("Japan") == "other"
        assert privacy_service._anonymize_location(None) is None


class TestPrivacyAPI:
    """Test privacy API endpoints"""
    
    def test_consent_request_validation(self):
        """Test consent request validation"""
        if not PRIVACY_AVAILABLE:
            pytest.skip("Privacy API not available")
        
        from api.privacy import ConsentRequest
        
        # Valid request
        request = ConsentRequest(
            consent_type="research_participation",
            action="grant",
            consent_details={"version": "1.0"}
        )
        
        assert request.consent_type == "research_participation"
        assert request.action == "grant"
        assert request.consent_details == {"version": "1.0"}
    
    def test_privacy_settings_request_validation(self):
        """Test privacy settings request validation"""
        if not PRIVACY_AVAILABLE:
            pytest.skip("Privacy API not available")
        
        from api.privacy import PrivacySettingsRequest
        
        # Valid request
        request = PrivacySettingsRequest(
            allow_research_participation=True,
            allow_analytics_tracking=False,
            data_retention_preference="one_year"
        )
        
        assert request.allow_research_participation == True
        assert request.allow_analytics_tracking == False
        assert request.data_retention_preference == "one_year"
    
    def test_data_deletion_request_validation(self):
        """Test data deletion request validation"""
        if not PRIVACY_AVAILABLE:
            pytest.skip("Privacy API not available")
        
        from api.privacy import DataDeletionRequest
        
        # Valid request
        request = DataDeletionRequest(
            request_type="full_deletion",
            deletion_scope={"include_all": True}
        )
        
        assert request.request_type == "full_deletion"
        assert request.deletion_scope == {"include_all": True}
    
    def test_data_export_request_validation(self):
        """Test data export request validation"""
        if not PRIVACY_AVAILABLE:
            pytest.skip("Privacy API not available")
        
        from api.privacy import DataExportRequest
        
        # Valid request
        request = DataExportRequest(
            export_format="json",
            export_scope={"include_profile": True}
        )
        
        assert request.export_format == "json"
        assert request.export_scope == {"include_profile": True}


async def test_privacy_database_migration():
    """Test privacy database migration"""
    if not PRIVACY_AVAILABLE:
        pytest.skip("Privacy migration not available")
    
    try:
        from migrations.create_privacy_tables import create_privacy_tables, drop_privacy_tables
        
        # Test table creation
        await create_privacy_tables()
        print("✓ Privacy tables created successfully")
        
        # Test table dropping
        await drop_privacy_tables()
        print("✓ Privacy tables dropped successfully")
        
    except Exception as e:
        print(f"✗ Privacy migration test failed: {e}")
        raise


def test_privacy_models():
    """Test privacy model definitions"""
    if not PRIVACY_AVAILABLE:
        pytest.skip("Privacy models not available")
    
    # Test enum values
    assert ConsentType.RESEARCH_PARTICIPATION.value == "research_participation"
    assert ConsentStatus.GRANTED.value == "granted"
    assert DataProcessingPurpose.RESEARCH_ANALYTICS.value == "research_analytics"
    assert DataRetentionPolicy.ONE_YEAR.value == "one_year"
    
    print("✓ Privacy model enums validated")


async def run_privacy_compliance_tests():
    """Run all privacy compliance tests"""
    print("Running Privacy and GDPR Compliance Tests...")
    print("=" * 50)
    
    if not PRIVACY_AVAILABLE:
        print("✗ Privacy service not available - skipping tests")
        return False
    
    try:
        # Test model definitions
        test_privacy_models()
        
        # Test database migration
        await test_privacy_database_migration()
        
        # Test service functionality
        privacy_service = PrivacyService(config={
            "gdpr_enabled": True,
            "data_retention_days": 365
        })
        
        # Test anonymization functions
        test_user_id = "test-user-123"
        anonymous_id = privacy_service._generate_anonymous_id(test_user_id)
        assert len(anonymous_id) == 64
        print("✓ Anonymous ID generation working")
        
        # Test age anonymization
        assert privacy_service._anonymize_age(25) == "25-34"
        print("✓ Age anonymization working")
        
        # Test location anonymization
        assert privacy_service._anonymize_location("United States") == "north_america"
        print("✓ Location anonymization working")
        
        print("\n" + "=" * 50)
        print("✓ All privacy compliance tests passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Privacy compliance tests failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_privacy_compliance_tests())
    exit(0 if success else 1)