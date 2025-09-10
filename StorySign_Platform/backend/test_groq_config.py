#!/usr/bin/env python3
"""
Test configuration for Groq API integration
"""

import os
import pytest
from unittest.mock import patch
from config import ConfigManager, AppConfig, GroqConfig


class TestGroqConfig:
    """Test cases for Groq API configuration"""

    def test_groq_config_defaults(self):
        """Test Groq configuration with default values"""
        config = GroqConfig()
        
        assert config.api_key is None
        assert config.base_url == "https://api.groq.com/openai/v1"
        assert config.model_name == "llava-v1.5-7b-4096-preview"
        assert config.timeout_seconds == 30
        assert config.max_retries == 3
        assert config.max_tokens == 1000
        assert config.temperature == 0.7
        assert config.enabled is False
        assert config.is_configured() is False

    def test_groq_config_with_api_key(self):
        """Test Groq configuration with API key"""
        config = GroqConfig(
            api_key="test-api-key-123",
            enabled=True
        )
        
        assert config.api_key == "test-api-key-123"
        assert config.enabled is True
        assert config.is_configured() is True

    def test_groq_config_validation_empty_api_key(self):
        """Test validation fails with empty API key"""
        with pytest.raises(ValueError, match="Groq API key cannot be empty"):
            GroqConfig(api_key="")

    def test_groq_config_validation_whitespace_api_key(self):
        """Test validation fails with whitespace-only API key"""
        with pytest.raises(ValueError, match="Groq API key cannot be empty"):
            GroqConfig(api_key="   ")

    def test_groq_config_validation_empty_model_name(self):
        """Test validation fails with empty model name"""
        with pytest.raises(ValueError, match="Groq model name cannot be empty"):
            GroqConfig(model_name="")

    def test_groq_config_validation_whitespace_model_name(self):
        """Test validation fails with whitespace-only model name"""
        with pytest.raises(ValueError, match="Groq model name cannot be empty"):
            GroqConfig(model_name="   ")

    def test_groq_config_strips_whitespace(self):
        """Test that API key and model name whitespace is stripped"""
        config = GroqConfig(
            api_key="  test-key  ",
            model_name="  test-model  "
        )
        
        assert config.api_key == "test-key"
        assert config.model_name == "test-model"

    @patch.dict(os.environ, {
        'GROQ_API_KEY': 'env-test-key',
        'STORYSIGN_GROQ__ENABLED': 'true',
        'STORYSIGN_GROQ__MODEL_NAME': 'env-test-model'
    })
    def test_groq_config_from_environment(self):
        """Test Groq configuration loading from environment variables"""
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        assert config.groq.api_key == 'env-test-key'
        assert config.groq.enabled is True
        assert config.groq.model_name == 'env-test-model'
        assert config.groq.is_configured() is True

    @patch.dict(os.environ, {
        'STORYSIGN_GROQ__API_KEY': 'prefixed-key',
        'GROQ_API_KEY': 'standard-key'
    })
    def test_groq_config_environment_precedence(self):
        """Test that STORYSIGN_GROQ__API_KEY takes precedence over GROQ_API_KEY"""
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # The prefixed version should take precedence
        assert config.groq.api_key == 'prefixed-key'

    @patch.dict(os.environ, {
        'STORYSIGN_GROQ__TIMEOUT_SECONDS': '60',
        'STORYSIGN_GROQ__MAX_RETRIES': '5',
        'STORYSIGN_GROQ__MAX_TOKENS': '2000',
        'STORYSIGN_GROQ__TEMPERATURE': '0.9'
    })
    def test_groq_config_numeric_environment_vars(self):
        """Test numeric environment variable parsing"""
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        assert config.groq.timeout_seconds == 60
        assert config.groq.max_retries == 5
        assert config.groq.max_tokens == 2000
        assert config.groq.temperature == 0.9

    def test_app_config_includes_groq(self):
        """Test that AppConfig includes Groq configuration"""
        config = AppConfig()
        
        assert hasattr(config, 'groq')
        assert isinstance(config.groq, GroqConfig)

    @patch.dict(os.environ, {
        'STORYSIGN_LOCAL_VISION__SERVICE_TYPE': 'groq'
    })
    def test_local_vision_service_type_groq(self):
        """Test that local vision service type can be set to groq"""
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        assert config.local_vision.service_type == 'groq'

    def test_groq_config_validation_ranges(self):
        """Test Groq configuration parameter ranges"""
        # Test valid ranges
        config = GroqConfig(
            timeout_seconds=5,  # minimum
            max_retries=1,      # minimum
            max_tokens=100,     # minimum
            temperature=0.0     # minimum
        )
        assert config.timeout_seconds == 5
        assert config.max_retries == 1
        assert config.max_tokens == 100
        assert config.temperature == 0.0

        config = GroqConfig(
            timeout_seconds=120,  # maximum
            max_retries=10,       # maximum
            max_tokens=4000,      # maximum
            temperature=2.0       # maximum
        )
        assert config.timeout_seconds == 120
        assert config.max_retries == 10
        assert config.max_tokens == 4000
        assert config.temperature == 2.0

        # Test invalid ranges
        with pytest.raises(ValueError):
            GroqConfig(timeout_seconds=4)  # below minimum
        
        with pytest.raises(ValueError):
            GroqConfig(timeout_seconds=121)  # above maximum
        
        with pytest.raises(ValueError):
            GroqConfig(max_retries=0)  # below minimum
        
        with pytest.raises(ValueError):
            GroqConfig(max_retries=11)  # above maximum
        
        with pytest.raises(ValueError):
            GroqConfig(max_tokens=99)  # below minimum
        
        with pytest.raises(ValueError):
            GroqConfig(max_tokens=4001)  # above maximum
        
        with pytest.raises(ValueError):
            GroqConfig(temperature=-0.1)  # below minimum
        
        with pytest.raises(ValueError):
            GroqConfig(temperature=2.1)  # above maximum


if __name__ == "__main__":
    pytest.main([__file__, "-v"])