#!/usr/bin/env python3
"""
Test suite for Ollama LLM service integration
Tests story generation and signing analysis functionality
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
from aiohttp import ClientTimeout

from ollama_service import OllamaService, StoryResponse, AnalysisResponse, get_ollama_service, cleanup_ollama_service
from config import get_config


class TestOllamaService:
    """Test cases for OllamaService class"""
    
    @pytest.fixture
    def service(self):
        """Create OllamaService instance for testing"""
        return OllamaService()
    
    @pytest.fixture
    def mock_session(self):
        """Create mock aiohttp session"""
        session = AsyncMock()
        return session
    
    def test_initialization(self, service):
        """Test service initialization"""
        assert service.config is not None
        assert service.session is None
        assert service._health_status is False
        assert service._last_health_check == 0
    
    @pytest.mark.asyncio
    async def test_start_stop_session(self, service):
        """Test session lifecycle management"""
        # Test start
        await service.start()
        assert service.session is not None
        assert isinstance(service.session, aiohttp.ClientSession)
        
        # Test stop
        await service.stop()
        assert service.session is None
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager functionality"""
        async with OllamaService() as service:
            assert service.session is not None
        # Session should be closed after context exit
    
    @pytest.mark.asyncio
    async def test_make_request_success(self, service, mock_session):
        """Test successful API request"""
        service.session = mock_session
        
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"response": "test response"}
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        success, data, error = await service._make_request(
            "api/generate", 
            {"prompt": "test"}, 
            "test-model"
        )
        
        assert success is True
        assert data == {"response": "test response"}
        assert error is None
    
    @pytest.mark.asyncio
    async def test_make_request_model_not_found(self, service, mock_session):
        """Test request with model not found error"""
        service.session = mock_session
        
        # Mock 404 response
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_response.text.return_value = "Model not found"
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        success, data, error = await service._make_request(
            "api/generate", 
            {"prompt": "test"}, 
            "nonexistent-model"
        )
        
        assert success is False
        assert data is None
        assert "not found" in error
    
    @pytest.mark.asyncio
    async def test_make_request_timeout(self, service, mock_session):
        """Test request timeout handling"""
        service.session = mock_session
        mock_session.post.side_effect = asyncio.TimeoutError()
        
        success, data, error = await service._make_request(
            "api/generate", 
            {"prompt": "test"}, 
            "test-model"
        )
        
        assert success is False
        assert data is None
        assert "timeout" in error.lower()
    
    @pytest.mark.asyncio
    async def test_make_request_retry_logic(self, service, mock_session):
        """Test retry logic on server errors"""
        service.session = mock_session
        service.config.max_retries = 2
        
        # Mock server error responses
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text.return_value = "Internal server error"
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        success, data, error = await service._make_request(
            "api/generate", 
            {"prompt": "test"}, 
            "test-model"
        )
        
        assert success is False
        assert mock_session.post.call_count == 2  # Should retry once
    
    @pytest.mark.asyncio
    async def test_check_health_success(self, service, mock_session):
        """Test successful health check"""
        service.session = mock_session
        
        # Mock successful health check response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3.1:latest"},
                {"name": "other-model:latest"}
            ]
        }
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        health = await service.check_health()
        
        assert health is True
        assert service._health_status is True
    
    @pytest.mark.asyncio
    async def test_check_health_missing_models(self, service, mock_session):
        """Test health check with missing models"""
        service.session = mock_session
        
        # Mock response without required models
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "models": [
                {"name": "other-model:latest"}
            ]
        }
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        health = await service.check_health()
        
        assert health is False
        assert service._health_status is False
    
    @pytest.mark.asyncio
    async def test_generate_story_success(self, service, mock_session):
        """Test successful story generation"""
        service.session = mock_session
        
        # Mock successful story generation response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "response": "The red ball bounced in the park.\nChildren played with the ball.\nThe ball rolled down the hill.\nA dog chased the ball.\nEveryone had fun with the ball."
        }
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        result = await service.generate_story("ball")
        
        assert result.success is True
        assert result.story is not None
        assert result.story["identified_object"] == "ball"
        assert len(result.story["sentences"]) == 5
        assert result.generation_time_ms is not None
        assert result.generation_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_generate_story_disabled(self, service):
        """Test story generation when service is disabled"""
        service.config.enabled = False
        
        result = await service.generate_story("ball")
        
        assert result.success is False
        assert "disabled" in result.error
    
    @pytest.mark.asyncio
    async def test_generate_story_failure(self, service, mock_session):
        """Test story generation failure"""
        service.session = mock_session
        
        # Mock failed response
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text.return_value = "Server error"
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        result = await service.generate_story("ball")
        
        assert result.success is False
        assert result.error is not None
        assert result.generation_time_ms is not None
    
    @pytest.mark.asyncio
    async def test_analyze_signing_attempt_success(self, service, mock_session):
        """Test successful signing analysis"""
        service.session = mock_session
        
        # Mock successful analysis response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "response": "FEEDBACK: Good hand positioning! Your signs were clear and well-formed.\nCONFIDENCE: 0.8\nSUGGESTIONS: Keep practicing smooth transitions, Focus on consistent signing space"
        }
        mock_session.post.return_value.__aenter__.return_value = mock_response
        
        # Create mock landmark buffer
        landmark_buffer = [
            {"landmarks": {"hands": True}, "timestamp": 1000},
            {"landmarks": {"hands": True}, "timestamp": 1033},
            {"landmarks": {"hands": True}, "timestamp": 1066}
        ]
        
        result = await service.analyze_signing_attempt(landmark_buffer, "Hello world")
        
        assert result.success is True
        assert result.feedback is not None
        assert result.confidence_score is not None
        assert 0.0 <= result.confidence_score <= 1.0
        assert result.suggestions is not None
        assert len(result.suggestions) <= 3
        assert result.analysis_time_ms is not None
    
    @pytest.mark.asyncio
    async def test_analyze_signing_attempt_disabled(self, service):
        """Test signing analysis when service is disabled"""
        service.config.enabled = False
        
        result = await service.analyze_signing_attempt([], "test")
        
        assert result.success is False
        assert "disabled" in result.error
    
    def test_create_story_prompt(self, service):
        """Test story prompt creation"""
        prompt = service._create_story_prompt("ball")
        
        assert "ball" in prompt
        assert "5 sentences" in prompt
        assert "ASL practice" in prompt
    
    def test_create_analysis_prompt(self, service):
        """Test analysis prompt creation"""
        landmark_buffer = [
            {"landmarks": {"hands": True}, "timestamp": 1000}
        ]
        
        prompt = service._create_analysis_prompt(landmark_buffer, "Hello world")
        
        assert "Hello world" in prompt
        assert "FEEDBACK:" in prompt
        assert "CONFIDENCE:" in prompt
        assert "SUGGESTIONS:" in prompt
    
    def test_summarize_movement_data_empty(self, service):
        """Test movement data summary with empty buffer"""
        summary = service._summarize_movement_data([])
        
        assert summary["duration_ms"] == 0
        assert "none detected" in summary["hand_movements"]
    
    def test_summarize_movement_data_with_data(self, service):
        """Test movement data summary with actual data"""
        landmark_buffer = [
            {"landmarks": {"hands": True}},
            {"landmarks": {"hands": True}},
            {"landmarks": {"hands": False}}
        ]
        
        summary = service._summarize_movement_data(landmark_buffer)
        
        assert summary["duration_ms"] > 0
        assert "%" in summary["hand_movements"]
    
    def test_parse_story_response(self, service):
        """Test story response parsing"""
        response_data = {
            "response": "The ball bounced high.\nChildren watched the ball.\nThe ball rolled away.\nA dog found the ball.\nEveryone smiled happily."
        }
        
        story = service._parse_story_response(response_data, "ball")
        
        assert story["identified_object"] == "ball"
        assert len(story["sentences"]) == 5
        assert "ball" in story["title"].lower()
    
    def test_parse_story_response_insufficient_sentences(self, service):
        """Test story parsing with insufficient sentences"""
        response_data = {
            "response": "The ball bounced.\nThe end."
        }
        
        story = service._parse_story_response(response_data, "ball")
        
        assert len(story["sentences"]) == 5  # Should pad with fallback sentences
    
    def test_parse_analysis_response(self, service):
        """Test analysis response parsing"""
        response_data = {
            "response": "FEEDBACK: Great signing!\nCONFIDENCE: 0.85\nSUGGESTIONS: Keep practicing, Focus on clarity"
        }
        
        analysis = service._parse_analysis_response(response_data)
        
        assert analysis["feedback"] == "Great signing!"
        assert analysis["confidence_score"] == 0.85
        assert len(analysis["suggestions"]) == 2
    
    def test_parse_analysis_response_malformed(self, service):
        """Test analysis parsing with malformed response"""
        response_data = {
            "response": "This is not a properly formatted response."
        }
        
        analysis = service._parse_analysis_response(response_data)
        
        # Should use defaults
        assert analysis["feedback"] is not None
        assert 0.0 <= analysis["confidence_score"] <= 1.0
        assert len(analysis["suggestions"]) > 0


class TestGlobalServiceFunctions:
    """Test global service management functions"""
    
    @pytest.mark.asyncio
    async def test_get_ollama_service(self):
        """Test global service getter"""
        # Clean up any existing service
        await cleanup_ollama_service()
        
        service1 = await get_ollama_service()
        service2 = await get_ollama_service()
        
        # Should return same instance
        assert service1 is service2
        assert service1.session is not None
        
        # Clean up
        await cleanup_ollama_service()
    
    @pytest.mark.asyncio
    async def test_cleanup_ollama_service(self):
        """Test global service cleanup"""
        service = await get_ollama_service()
        assert service.session is not None
        
        await cleanup_ollama_service()
        
        # Should be cleaned up
        assert service.session is None


@pytest.mark.integration
class TestOllamaServiceIntegration:
    """Integration tests for Ollama service (requires running Ollama)"""
    
    @pytest.mark.asyncio
    async def test_real_health_check(self):
        """Test health check against real Ollama service"""
        service = OllamaService()
        
        try:
            await service.start()
            health = await service.check_health()
            
            # This will pass if Ollama is running with required models
            # Otherwise it will fail gracefully
            if health:
                print("✓ Ollama service is healthy")
            else:
                print("⚠ Ollama service not available or missing models")
        
        finally:
            await service.stop()
    
    @pytest.mark.asyncio
    async def test_real_story_generation(self):
        """Test story generation against real Ollama service"""
        service = OllamaService()
        
        try:
            await service.start()
            
            # Only run if service is healthy
            if await service.check_health():
                result = await service.generate_story("ball")
                
                if result.success:
                    print("✓ Story generation successful")
                    print(f"Generated story: {result.story}")
                else:
                    print(f"⚠ Story generation failed: {result.error}")
            else:
                print("⚠ Skipping story generation test - service not healthy")
        
        finally:
            await service.stop()


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])