#!/usr/bin/env python3
"""
Test Groq Vision Service integration
"""

import os
import json
import base64
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
import aiohttp
from aiohttp import ClientResponseError

from local_vision_service import LocalVisionService, VisionResult
from config import ConfigManager, GroqConfig


class TestGroqVisionService:
    """Test cases for Groq Vision Service integration"""

    @pytest.fixture
    def mock_groq_config(self):
        """Mock Groq configuration"""
        return GroqConfig(
            api_key="test-groq-api-key",
            base_url="https://api.groq.com/openai/v1",
            model_name="llava-v1.5-7b-4096-preview",
            enabled=True,
            timeout_seconds=30,
            max_retries=3,
            max_tokens=1000,
            temperature=0.7
        )

    @pytest.fixture
    def mock_local_vision_config(self):
        """Mock local vision configuration for Groq"""
        from config import LocalVisionConfig
        return LocalVisionConfig(
            service_type="groq",
            enabled=True,
            timeout_seconds=30,
            max_retries=3
        )

    @pytest.fixture
    def sample_base64_image(self):
        """Sample base64 encoded image for testing"""
        # Create a minimal JPEG header for testing
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00'
        jpeg_data = jpeg_header + b'\x00' * 500  # Pad to minimum size
        return base64.b64encode(jpeg_data).decode('utf-8')

    @pytest.fixture
    def mock_groq_models_response(self):
        """Mock response for Groq models API"""
        return {
            "data": [
                {"id": "llava-v1.5-7b-4096-preview", "object": "model"},
                {"id": "llama-3.2-90b-vision-preview", "object": "model"},
                {"id": "llama-3.2-11b-vision-preview", "object": "model"}
            ]
        }

    @pytest.fixture
    def mock_groq_vision_response(self):
        """Mock response for Groq vision API"""
        return {
            "choices": [
                {
                    "message": {
                        "content": "coffee cup"
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 2,
                "total_tokens": 102
            }
        }

    @pytest.mark.asyncio
    @patch('local_vision_service.get_config')
    async def test_groq_health_check_success(self, mock_get_config, mock_groq_config, mock_local_vision_config, mock_groq_models_response):
        """Test successful Groq API health check"""
        # Mock configuration
        mock_config = MagicMock()
        mock_config.local_vision = mock_local_vision_config
        mock_config.groq = mock_groq_config
        mock_get_config.return_value = mock_config

        # Mock HTTP session
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_groq_models_response)
        mock_session.get.return_value.__aenter__.return_value = mock_response

        service = LocalVisionService()
        service.session = mock_session

        # Test health check
        is_healthy = await service.check_health()

        assert is_healthy is True
        assert service.is_healthy() is True

        # Verify API call
        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        assert call_args[0][0] == "https://api.groq.com/openai/v1/models"
        assert call_args[1]["headers"]["Authorization"] == "Bearer test-groq-api-key"

    @pytest.mark.asyncio
    @patch('local_vision_service.get_config')
    async def test_groq_health_check_model_not_found(self, mock_get_config, mock_groq_config, mock_local_vision_config):
        """Test Groq health check when model is not available"""
        # Mock configuration with different model
        mock_groq_config.model_name = "non-existent-model"
        mock_config = MagicMock()
        mock_config.local_vision = mock_local_vision_config
        mock_config.groq = mock_groq_config
        mock_get_config.return_value = mock_config

        # Mock HTTP session
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"data": [{"id": "other-model"}]})
        mock_session.get.return_value.__aenter__.return_value = mock_response

        service = LocalVisionService()
        service.session = mock_session

        # Test health check
        is_healthy = await service.check_health()

        assert is_healthy is False
        assert service.is_healthy() is False

    @pytest.mark.asyncio
    @patch('local_vision_service.get_config')
    async def test_groq_health_check_authentication_error(self, mock_get_config, mock_groq_config, mock_local_vision_config):
        """Test Groq health check with authentication error"""
        # Mock configuration
        mock_config = MagicMock()
        mock_config.local_vision = mock_local_vision_config
        mock_config.groq = mock_groq_config
        mock_get_config.return_value = mock_config

        # Mock HTTP session with 401 error
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_session.get.return_value.__aenter__.return_value = mock_response

        service = LocalVisionService()
        service.session = mock_session

        # Test health check
        is_healthy = await service.check_health()

        assert is_healthy is False
        assert service.is_healthy() is False

    @pytest.mark.asyncio
    @patch('local_vision_service.get_config')
    async def test_groq_vision_request_success(self, mock_get_config, mock_groq_config, mock_local_vision_config, sample_base64_image, mock_groq_vision_response):
        """Test successful Groq vision request"""
        # Mock configuration
        mock_config = MagicMock()
        mock_config.local_vision = mock_local_vision_config
        mock_config.groq = mock_groq_config
        mock_get_config.return_value = mock_config

        # Mock HTTP session
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_groq_vision_response)
        mock_session.post.return_value.__aenter__.return_value = mock_response

        service = LocalVisionService()
        service.session = mock_session
        service._health_status = True  # Skip health check

        # Test vision request
        result = await service.identify_object(sample_base64_image)

        assert result.success is True
        assert result.object_name == "coffee cup"
        assert result.confidence == 0.9  # High confidence for Groq + short response
        assert result.error_message is None

        # Verify API call
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        assert call_args[0][0] == "https://api.groq.com/openai/v1/chat/completions"
        assert call_args[1]["headers"]["Authorization"] == "Bearer test-groq-api-key"

        # Verify payload structure
        payload = call_args[1]["json"]
        assert payload["model"] == "llava-v1.5-7b-4096-preview"
        assert payload["temperature"] == 0.7
        assert payload["max_tokens"] == 1000
        assert len(payload["messages"]) == 1
        assert payload["messages"][0]["role"] == "user"
        assert len(payload["messages"][0]["content"]) == 2
        assert payload["messages"][0]["content"][0]["type"] == "text"
        assert payload["messages"][0]["content"][1]["type"] == "image_url"

    @pytest.mark.asyncio
    @patch('local_vision_service.get_config')
    async def test_groq_vision_request_rate_limit(self, mock_get_config, mock_groq_config, mock_local_vision_config, sample_base64_image):
        """Test Groq vision request with rate limiting"""
        # Mock configuration with max_retries = 1 for faster test
        mock_groq_config.max_retries = 1
        mock_config = MagicMock()
        mock_config.local_vision = mock_local_vision_config
        mock_config.groq = mock_groq_config
        mock_get_config.return_value = mock_config

        # Mock HTTP session with 429 error
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_response.request_info = MagicMock()
        mock_response.history = []
        
        # Create a proper ClientResponseError
        error = ClientResponseError(
            request_info=mock_response.request_info,
            history=mock_response.history,
            status=429,
            message="Rate limited"
        )
        mock_session.post.return_value.__aenter__.side_effect = error

        service = LocalVisionService()
        service.session = mock_session
        service._health_status = True  # Skip health check

        # Test vision request
        result = await service.identify_object(sample_base64_image)

        assert result.success is False
        assert "Rate limited" in result.error_message
        assert result.object_name is None

    @pytest.mark.asyncio
    @patch('local_vision_service.get_config')
    async def test_groq_vision_request_authentication_error(self, mock_get_config, mock_groq_config, mock_local_vision_config, sample_base64_image):
        """Test Groq vision request with authentication error"""
        # Mock configuration
        mock_config = MagicMock()
        mock_config.local_vision = mock_local_vision_config
        mock_config.groq = mock_groq_config
        mock_get_config.return_value = mock_config

        # Mock HTTP session with 401 error
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.request_info = MagicMock()
        mock_response.history = []
        
        # Create a proper ClientResponseError
        error = ClientResponseError(
            request_info=mock_response.request_info,
            history=mock_response.history,
            status=401,
            message="Authentication failed"
        )
        mock_session.post.return_value.__aenter__.side_effect = error

        service = LocalVisionService()
        service.session = mock_session
        service._health_status = True  # Skip health check

        # Test vision request
        result = await service.identify_object(sample_base64_image)

        assert result.success is False
        assert "Authentication failed" in result.error_message
        assert result.object_name is None

    @pytest.mark.asyncio
    @patch('local_vision_service.get_config')
    async def test_groq_service_status(self, mock_get_config, mock_groq_config, mock_local_vision_config, mock_groq_models_response):
        """Test Groq service status reporting"""
        # Mock configuration
        mock_config = MagicMock()
        mock_config.local_vision = mock_local_vision_config
        mock_config.groq = mock_groq_config
        mock_get_config.return_value = mock_config

        # Mock HTTP session
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_groq_models_response)
        mock_session.get.return_value.__aenter__.return_value = mock_response

        service = LocalVisionService()
        service.session = mock_session

        # Test service status
        status = await service.get_service_status()

        assert status["enabled"] is True
        assert status["service_type"] == "groq"
        assert status["service_url"] == "https://api.groq.com/openai/v1"
        assert status["model_name"] == "llava-v1.5-7b-4096-preview"
        assert status["healthy"] is True
        assert status["api_configured"] is True
        assert "llava-v1.5-7b-4096-preview" in status["available_models"]
        assert status["error"] is None

    @pytest.mark.asyncio
    @patch('local_vision_service.get_config')
    async def test_groq_service_status_not_configured(self, mock_get_config, mock_local_vision_config):
        """Test Groq service status when not configured"""
        # Mock configuration with no API key
        mock_groq_config = GroqConfig(enabled=False, api_key=None)
        mock_config = MagicMock()
        mock_config.local_vision = mock_local_vision_config
        mock_config.groq = mock_groq_config
        mock_get_config.return_value = mock_config

        service = LocalVisionService()

        # Test service status
        status = await service.get_service_status()

        assert status["enabled"] is False
        assert status["api_configured"] is False
        assert "not configured" in status["error"]

    def test_groq_config_validation(self):
        """Test Groq configuration validation"""
        # Test valid configuration
        config = GroqConfig(
            api_key="valid-key",
            enabled=True
        )
        assert config.is_configured() is True

        # Test invalid configuration - no API key
        config = GroqConfig(
            api_key=None,
            enabled=True
        )
        assert config.is_configured() is False

        # Test invalid configuration - disabled
        config = GroqConfig(
            api_key="valid-key",
            enabled=False
        )
        assert config.is_configured() is False

    @pytest.mark.asyncio
    @patch('local_vision_service.get_config')
    async def test_groq_vision_response_parsing(self, mock_get_config, mock_groq_config, mock_local_vision_config):
        """Test parsing of various Groq vision responses"""
        # Mock configuration
        mock_config = MagicMock()
        mock_config.local_vision = mock_local_vision_config
        mock_config.groq = mock_groq_config
        mock_get_config.return_value = mock_config

        service = LocalVisionService()

        # Test simple object name
        response_data = {
            "choices": [{"message": {"content": "red apple"}}]
        }
        object_name, confidence = service._parse_vision_response(response_data)
        assert object_name == "red apple"
        assert confidence == 0.9  # High confidence for Groq + short response

        # Test verbose response
        response_data = {
            "choices": [{"message": {"content": "I can see a red apple on the table"}}]
        }
        object_name, confidence = service._parse_vision_response(response_data)
        assert object_name == "red apple"
        assert confidence == 0.6  # Lower confidence for uncertain language

        # Test uncertain response
        response_data = {
            "choices": [{"message": {"content": "This might be a book"}}]
        }
        object_name, confidence = service._parse_vision_response(response_data)
        assert object_name == "book"
        assert confidence == 0.6  # Lower confidence for uncertain language

        # Test empty response
        response_data = {
            "choices": [{"message": {"content": ""}}]
        }
        object_name, confidence = service._parse_vision_response(response_data)
        assert object_name is None
        assert confidence is None

    @patch.dict(os.environ, {
        'GROQ_API_KEY': 'env-test-key',
        'STORYSIGN_LOCAL_VISION__SERVICE_TYPE': 'groq',
        'STORYSIGN_GROQ__ENABLED': 'true'
    })
    def test_groq_environment_configuration(self):
        """Test Groq configuration from environment variables"""
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        assert config.groq.api_key == 'env-test-key'
        assert config.groq.enabled is True
        assert config.local_vision.service_type == 'groq'
        assert config.groq.is_configured() is True

    @pytest.mark.asyncio
    @patch('local_vision_service.get_config')
    async def test_groq_timeout_handling(self, mock_get_config, mock_groq_config, mock_local_vision_config, sample_base64_image):
        """Test Groq request timeout handling"""
        # Mock configuration
        mock_config = MagicMock()
        mock_config.local_vision = mock_local_vision_config
        mock_config.groq = mock_groq_config
        mock_get_config.return_value = mock_config

        # Mock HTTP session with timeout
        mock_session = AsyncMock()
        mock_session.post.side_effect = asyncio.TimeoutError()

        service = LocalVisionService()
        service.session = mock_session
        service._health_status = True  # Skip health check

        # Test vision request
        result = await service.identify_object(sample_base64_image)

        assert result.success is False
        assert "timed out" in result.error_message.lower()
        assert result.object_name is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])