"""
Test suite for branding and white-labeling functionality.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from services.branding_service import BrandingService, ThemeService, FeatureFlagService, CustomDomainService
from repositories.branding_repository import BrandingRepository, ThemeRepository, FeatureFlagRepository, CustomDomainRepository
from models.branding import BrandingConfiguration, ThemeConfiguration, FeatureFlag, CustomDomain


class TestBrandingService:
    """Test branding service functionality."""
    
    @pytest.fixture
    def mock_branding_repo(self):
        return AsyncMock(spec=BrandingRepository)
    
    @pytest.fixture
    def branding_service(self, mock_branding_repo):
        return BrandingService(mock_branding_repo)
    
    @pytest.mark.asyncio
    async def test_create_branding_configuration(self, branding_service, mock_branding_repo):
        """Test creating a new branding configuration."""
        config_data = {
            "organization_name": "Test Organization",
            "domain": "test.example.com",
            "primary_color": "#FF0000",
            "secondary_color": "#00FF00"
        }
        created_by = "user123"
        
        mock_config = BrandingConfiguration(
            id="config123",
            organization_name="Test Organization",
            domain="test.example.com",
            primary_color="#FF0000",
            secondary_color="#00FF00",
            created_by=created_by
        )
        mock_branding_repo.create_branding_config.return_value = mock_config
        
        result = await branding_service.create_branding_configuration(config_data, created_by)
        
        assert result.organization_name == "Test Organization"
        assert result.domain == "test.example.com"
        assert result.created_by == created_by
        mock_branding_repo.create_branding_config.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_branding_by_domain(self, branding_service, mock_branding_repo):
        """Test retrieving branding configuration by domain."""
        domain = "test.example.com"
        mock_config = BrandingConfiguration(
            id="config123",
            organization_name="Test Organization",
            domain=domain
        )
        mock_branding_repo.get_by_domain.return_value = mock_config
        
        result = await branding_service.get_branding_by_domain(domain)
        
        assert result.domain == domain
        mock_branding_repo.get_by_domain.assert_called_once_with(domain)


class TestThemeService:
    """Test theme service functionality."""
    
    @pytest.fixture
    def mock_theme_repo(self):
        return AsyncMock(spec=ThemeRepository)
    
    @pytest.fixture
    def theme_service(self, mock_theme_repo):
        return ThemeService(mock_theme_repo)
    
    @pytest.mark.asyncio
    async def test_create_theme(self, theme_service, mock_theme_repo):
        """Test creating a new theme configuration."""
        theme_data = {
            "branding_id": "branding123",
            "theme_name": "Dark Theme",
            "theme_mode": "dark",
            "layout_type": "compact"
        }
        
        mock_theme = ThemeConfiguration(
            id="theme123",
            branding_id="branding123",
            theme_name="Dark Theme",
            theme_mode="dark",
            layout_type="compact"
        )
        mock_theme_repo.create_theme.return_value = mock_theme
        
        result = await theme_service.create_theme(theme_data)
        
        assert result.theme_name == "Dark Theme"
        assert result.theme_mode == "dark"
        mock_theme_repo.create_theme.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_default_theme(self, theme_service, mock_theme_repo):
        """Test retrieving default theme for branding."""
        branding_id = "branding123"
        mock_theme = ThemeConfiguration(
            id="theme123",
            branding_id=branding_id,
            theme_name="Default Theme",
            is_default=True
        )
        mock_theme_repo.get_default_theme.return_value = mock_theme
        
        result = await theme_service.get_default_theme(branding_id)
        
        assert result.is_default is True
        mock_theme_repo.get_default_theme.assert_called_once_with(branding_id)


class TestFeatureFlagService:
    """Test feature flag service functionality."""
    
    @pytest.fixture
    def mock_flag_repo(self):
        return AsyncMock(spec=FeatureFlagRepository)
    
    @pytest.fixture
    def flag_service(self, mock_flag_repo):
        return FeatureFlagService(mock_flag_repo)
    
    @pytest.mark.asyncio
    async def test_is_feature_enabled_simple_boolean(self, flag_service, mock_flag_repo):
        """Test checking if a simple boolean feature flag is enabled."""
        branding_id = "branding123"
        flag_key = "test_feature"
        user_id = "user123"
        
        mock_flag = FeatureFlag(
            id="flag123",
            branding_id=branding_id,
            flag_key=flag_key,
            is_enabled=True,
            flag_type="boolean",
            is_active=True
        )
        mock_flag_repo.get_flag_by_key.return_value = mock_flag
        
        result = await flag_service.is_feature_enabled(branding_id, flag_key, user_id)
        
        assert result is True
        mock_flag_repo.get_flag_by_key.assert_called_once_with(branding_id, flag_key)
    
    @pytest.mark.asyncio
    async def test_is_feature_enabled_with_rollout(self, flag_service, mock_flag_repo):
        """Test feature flag with rollout percentage."""
        branding_id = "branding123"
        flag_key = "test_feature"
        user_id = "user123"
        
        mock_flag = FeatureFlag(
            id="flag123",
            branding_id=branding_id,
            flag_key=flag_key,
            is_enabled=True,
            flag_type="boolean",
            rollout_percentage=50.0,
            is_active=True
        )
        mock_flag_repo.get_flag_by_key.return_value = mock_flag
        
        # Mock hash function to return predictable value
        with patch('builtins.hash', return_value=25):  # 25 % 100 = 25, which is < 50
            result = await flag_service.is_feature_enabled(branding_id, flag_key, user_id)
            assert result is True
        
        with patch('builtins.hash', return_value=75):  # 75 % 100 = 75, which is >= 50
            result = await flag_service.is_feature_enabled(branding_id, flag_key, user_id)
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_feature_value(self, flag_service, mock_flag_repo):
        """Test getting feature flag value."""
        branding_id = "branding123"
        flag_key = "test_config"
        
        mock_flag = FeatureFlag(
            id="flag123",
            branding_id=branding_id,
            flag_key=flag_key,
            is_enabled=True,
            flag_type="json",
            flag_value={"max_users": 100, "timeout": 30},
            is_active=True
        )
        mock_flag_repo.get_flag_by_key.return_value = mock_flag
        
        result = await flag_service.get_feature_value(branding_id, flag_key)
        
        assert result == {"max_users": 100, "timeout": 30}
    
    @pytest.mark.asyncio
    async def test_toggle_feature_flag(self, flag_service, mock_flag_repo):
        """Test toggling a feature flag."""
        flag_id = "flag123"
        
        mock_flag = FeatureFlag(
            id=flag_id,
            flag_key="test_feature",
            is_enabled=False
        )
        mock_flag_repo.get_by_id.return_value = mock_flag
        
        updated_flag = FeatureFlag(
            id=flag_id,
            flag_key="test_feature",
            is_enabled=True
        )
        mock_flag_repo.update_flag_status.return_value = updated_flag
        
        result = await flag_service.toggle_feature_flag(flag_id)
        
        assert result.is_enabled is True
        mock_flag_repo.update_flag_status.assert_called_once_with(flag_id, True)


class TestCustomDomainService:
    """Test custom domain service functionality."""
    
    @pytest.fixture
    def mock_domain_repo(self):
        return AsyncMock(spec=CustomDomainRepository)
    
    @pytest.fixture
    def domain_service(self, mock_domain_repo):
        return CustomDomainService(mock_domain_repo)
    
    @pytest.mark.asyncio
    async def test_create_custom_domain(self, domain_service, mock_domain_repo):
        """Test creating a custom domain configuration."""
        domain_data = {
            "branding_id": "branding123",
            "domain_name": "custom.example.com"
        }
        
        mock_domain = CustomDomain(
            id="domain123",
            branding_id="branding123",
            domain_name="custom.example.com",
            dns_verification_token="token123",
            cname_target="storysign-abc123.platform.com"
        )
        mock_domain_repo.create_custom_domain.return_value = mock_domain
        
        result = await domain_service.create_custom_domain(domain_data)
        
        assert result.domain_name == "custom.example.com"
        assert result.dns_verification_token is not None
        assert result.cname_target is not None
        mock_domain_repo.create_custom_domain.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_provision_ssl_certificate(self, domain_service, mock_domain_repo):
        """Test SSL certificate provisioning."""
        domain_id = "domain123"
        
        mock_domain = CustomDomain(
            id=domain_id,
            domain_name="custom.example.com",
            dns_verified=True
        )
        mock_domain_repo.get_by_id.return_value = mock_domain
        mock_domain_repo.update_ssl_status.return_value = mock_domain
        
        result = await domain_service.provision_ssl_certificate(domain_id)
        
        assert result is True
        mock_domain_repo.update_ssl_status.assert_called_once()


def test_default_branding_features():
    """Test default feature flags for new branding configurations."""
    branding_service = BrandingService(AsyncMock())
    default_features = branding_service._get_default_features()
    
    # Check that essential features are enabled by default
    assert default_features["asl_world"] is True
    assert default_features["analytics"] is True
    assert default_features["collaborative_sessions"] is True
    assert default_features["white_labeling"] is True
    
    # Check that advanced features are disabled by default
    assert default_features["harmony"] is False
    assert default_features["reconnect"] is False
    assert default_features["plugin_system"] is False
    assert default_features["api_access"] is False


if __name__ == "__main__":
    # Run basic functionality test
    async def test_basic_functionality():
        print("Testing branding service basic functionality...")
        
        # Test default features
        branding_service = BrandingService(AsyncMock())
        default_features = branding_service._get_default_features()
        print(f"✅ Default features: {len(default_features)} features configured")
        
        # Test theme service default styles
        theme_service = ThemeService(AsyncMock())
        button_style = theme_service._get_default_button_style()
        print(f"✅ Default button style: {len(button_style)} properties configured")
        
        print("✅ All basic functionality tests passed!")
    
    asyncio.run(test_basic_functionality())