#!/usr/bin/env python3
"""
Simple integration test for Groq Vision Service
"""

import os
import base64
import pytest
from unittest.mock import patch, MagicMock

from config import ConfigManager, GroqConfig, LocalVisionConfig
from local_vision_service import LocalVisionService


class TestGroqIntegrationSimple:
    """Simple test cases for Groq integration"""

    def test_groq_config_integration(self):
        """Test that Groq configuration integrates properly with local vision config"""
        # Test that service type can be set to groq
        local_config = LocalVisionConfig(service_type="groq")
        assert local_config.service_type == "groq"

        # Test Groq configuration
        groq_config = GroqConfig(
            api_key="test-key",
            enabled=True,
            model_name="llava-v1.5-7b-4096-preview"
        )
        assert groq_config.is_configured() is True

    def test_groq_response_parsing(self):
        """Test Groq response parsing without network calls"""
        # Mock configuration
        with patch('local_vision_service.get_config') as mock_get_config:
            mock_config = MagicMock()
            mock_config.local_vision = LocalVisionConfig(service_type="groq")
            mock_config.groq = GroqConfig(api_key="test", enabled=True)
            mock_get_config.return_value = mock_config

            service = LocalVisionService()

            # Test simple Groq response
            response_data = {
                "choices": [{"message": {"content": "coffee cup"}}]
            }
            object_name, confidence = service._parse_vision_response(response_data)
            assert object_name == "coffee cup"
            assert confidence == 0.9  # High confidence for Groq + short response

            # Test verbose Groq response
            response_data = {
                "choices": [{"message": {"content": "I can see a red apple on the table"}}]
            }
            object_name, confidence = service._parse_vision_response(response_data)
            assert object_name == "red apple"
            # Original response has >5 words, so it gets lower confidence
            assert confidence == 0.6

            # Test uncertain response
            response_data = {
                "choices": [{"message": {"content": "This might be a book"}}]
            }
            object_name, confidence = service._parse_vision_response(response_data)
            assert object_name == "book"
            assert confidence == 0.6  # Lower confidence for uncertain language

    def test_groq_service_type_validation(self):
        """Test that Groq is accepted as a valid service type"""
        # Should not raise an exception
        config = LocalVisionConfig(service_type="groq")
        assert config.service_type == "groq"

        # Test validation
        with pytest.raises(ValueError):
            LocalVisionConfig(service_type="invalid_service")

    def test_groq_config_validation_comprehensive(self):
        """Test comprehensive Groq configuration validation"""
        # Valid configuration
        config = GroqConfig(
            api_key="gsk_test123",
            enabled=True,
            model_name="llava-v1.5-7b-4096-preview",
            timeout_seconds=30,
            max_retries=3,
            max_tokens=1000,
            temperature=0.7
        )
        assert config.is_configured() is True

        # Invalid - no API key
        config = GroqConfig(enabled=True, api_key=None)
        assert config.is_configured() is False

        # Invalid - disabled
        config = GroqConfig(api_key="test", enabled=False)
        assert config.is_configured() is False

        # Invalid - empty API key
        with pytest.raises(ValueError):
            GroqConfig(api_key="")

        # Invalid - empty model name
        with pytest.raises(ValueError):
            GroqConfig(model_name="")

    @patch.dict(os.environ, {
        'GROQ_API_KEY': 'env-groq-key',
        'STORYSIGN_LOCAL_VISION__SERVICE_TYPE': 'groq',
        'STORYSIGN_GROQ__ENABLED': 'true',
        'STORYSIGN_GROQ__MODEL_NAME': 'llava-v1.5-7b-4096-preview'
    })
    def test_groq_environment_configuration(self):
        """Test Groq configuration from environment variables"""
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        assert config.groq.api_key == 'env-groq-key'
        assert config.groq.enabled is True
        assert config.groq.model_name == 'llava-v1.5-7b-4096-preview'
        assert config.local_vision.service_type == 'groq'
        assert config.groq.is_configured() is True

    def test_groq_config_parameter_ranges(self):
        """Test Groq configuration parameter validation ranges"""
        # Test valid ranges
        config = GroqConfig(
            api_key="test",
            timeout_seconds=5,  # minimum
            max_retries=1,      # minimum
            max_tokens=100,     # minimum
            temperature=0.0     # minimum
        )
        assert config.timeout_seconds == 5

        config = GroqConfig(
            api_key="test",
            timeout_seconds=120,  # maximum
            max_retries=10,       # maximum
            max_tokens=4000,      # maximum
            temperature=2.0       # maximum
        )
        assert config.timeout_seconds == 120

        # Test invalid ranges
        with pytest.raises(ValueError):
            GroqConfig(api_key="test", timeout_seconds=4)  # below minimum
        
        with pytest.raises(ValueError):
            GroqConfig(api_key="test", max_retries=0)  # below minimum

    def test_vision_service_initialization_with_groq(self):
        """Test that vision service can be initialized with Groq configuration"""
        with patch('local_vision_service.get_config') as mock_get_config:
            mock_config = MagicMock()
            mock_config.local_vision = LocalVisionConfig(
                service_type="groq",
                enabled=True
            )
            mock_config.groq = GroqConfig(
                api_key="test-key",
                enabled=True,
                model_name="llava-v1.5-7b-4096-preview"
            )
            mock_get_config.return_value = mock_config

            # Should not raise an exception
            service = LocalVisionService()
            assert service.config.service_type == "groq"

    def test_base64_image_validation(self):
        """Test base64 image validation works with Groq service"""
        with patch('local_vision_service.get_config') as mock_get_config:
            mock_config = MagicMock()
            mock_config.local_vision = LocalVisionConfig(service_type="groq")
            mock_config.groq = GroqConfig(api_key="test", enabled=True)
            mock_get_config.return_value = mock_config

            service = LocalVisionService()

            # Test valid JPEG image
            jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00'
            jpeg_data = jpeg_header + b'\x00' * 500  # Pad to minimum size
            valid_base64 = base64.b64encode(jpeg_data).decode('utf-8')

            validation_result = service._validate_base64_image(valid_base64)
            assert validation_result["valid"] is True
            assert validation_result["format"] == "JPEG"

            # Test invalid base64
            validation_result = service._validate_base64_image("invalid_base64")
            assert validation_result["valid"] is False

            # Test empty base64
            validation_result = service._validate_base64_image("")
            assert validation_result["valid"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])