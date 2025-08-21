#!/usr/bin/env python3
"""
Test for the story generation endpoint
"""

import pytest
import asyncio
import base64
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app
from local_vision_service import VisionResult
from ollama_service import StoryResponse


class TestStoryGenerationEndpoint:
    """Test cases for the story generation endpoint"""
    
    def setup_method(self):
        """Set up test client"""
        self.client = TestClient(app)
        
        # Create a simple test image (1x1 pixel JPEG)
        self.test_image_base64 = "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A8A"
    
    @patch('main.get_vision_service')
    @patch('main.get_ollama_service')
    def test_successful_story_generation(self, mock_ollama_service, mock_vision_service):
        """Test successful story generation with both services working"""
        
        # Mock vision service
        mock_vision = AsyncMock()
        mock_vision.check_health.return_value = True
        mock_vision.identify_object.return_value = VisionResult(
            success=True,
            object_name="red ball",
            confidence=0.8,
            processing_time_ms=150.0
        )
        mock_vision_service.return_value = mock_vision
        
        # Mock Ollama service
        mock_ollama = AsyncMock()
        mock_ollama.check_health.return_value = True
        mock_ollama.generate_story.return_value = StoryResponse(
            success=True,
            story={
                "title": "The Adventure of the Red Ball",
                "sentences": [
                    "Once upon a time, there was a bright red ball.",
                    "The ball loved to bounce in the sunny park.",
                    "Children would come to play with the happy ball.",
                    "One day, the ball rolled into a magical forest.",
                    "The ball made many new friends among the trees."
                ],
                "identified_object": "red ball"
            },
            generation_time_ms=2340.0
        )
        mock_ollama_service.return_value = mock_ollama
        
        # Make request
        response = self.client.post(
            "/api/story/recognize_and_generate",
            json={
                "frame_data": self.test_image_base64
            }
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "story" in data
        assert data["story"]["title"] == "The Adventure of the Red Ball"
        assert len(data["story"]["sentences"]) == 5
        assert data["story"]["identified_object"] == "red ball"
        
        # Verify processing info
        assert "processing_info" in data
        assert data["processing_info"]["object_identification"]["success"] is True
        assert data["processing_info"]["object_identification"]["identified_object"] == "red ball"
        assert data["processing_info"]["story_generation"]["success"] is True
    
    @patch('main.get_vision_service')
    @patch('main.get_ollama_service')
    def test_vision_service_failure_with_fallback(self, mock_ollama_service, mock_vision_service):
        """Test story generation when vision service fails but Ollama works"""
        
        # Mock vision service failure
        mock_vision = AsyncMock()
        mock_vision.check_health.return_value = False
        mock_vision_service.return_value = mock_vision
        
        # Mock Ollama service success
        mock_ollama = AsyncMock()
        mock_ollama.check_health.return_value = True
        mock_ollama.generate_story.return_value = StoryResponse(
            success=True,
            story={
                "title": "The Adventure of the Ball",
                "sentences": [
                    "The ball was very special.",
                    "Everyone loved the ball.",
                    "The ball brought joy to all.",
                    "People gathered around the ball.",
                    "The ball made everyone happy."
                ],
                "identified_object": "ball"
            },
            generation_time_ms=1500.0
        )
        mock_ollama_service.return_value = mock_ollama
        
        # Make request
        response = self.client.post(
            "/api/story/recognize_and_generate",
            json={
                "frame_data": self.test_image_base64
            }
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "story" in data
        
        # Verify fallback was used
        processing_info = data["processing_info"]["object_identification"]
        assert processing_info["vision_service_used"] is False
        assert processing_info["fallback_used"] is True
        assert processing_info["identified_object"] in ["ball", "book", "flower", "cup", "toy"]
    
    @patch('main.get_vision_service')
    @patch('main.get_ollama_service')
    def test_ollama_service_failure(self, mock_ollama_service, mock_vision_service):
        """Test story generation when Ollama service fails"""
        
        # Mock vision service success
        mock_vision = AsyncMock()
        mock_vision.check_health.return_value = True
        mock_vision.identify_object.return_value = VisionResult(
            success=True,
            object_name="book",
            confidence=0.9,
            processing_time_ms=120.0
        )
        mock_vision_service.return_value = mock_vision
        
        # Mock Ollama service failure
        mock_ollama = AsyncMock()
        mock_ollama.check_health.return_value = False
        mock_ollama_service.return_value = mock_ollama
        
        # Make request
        response = self.client.post(
            "/api/story/recognize_and_generate",
            json={
                "frame_data": self.test_image_base64
            }
        )
        
        # Verify error response
        assert response.status_code == 503
        assert "Story generation service is unavailable" in response.json()["detail"]
    
    def test_missing_frame_data(self):
        """Test request with missing frame data"""
        
        response = self.client.post(
            "/api/story/recognize_and_generate",
            json={}
        )
        
        # Should return validation error
        assert response.status_code == 422  # Validation error
    
    def test_empty_frame_data(self):
        """Test request with empty frame data"""
        
        response = self.client.post(
            "/api/story/recognize_and_generate",
            json={
                "frame_data": ""
            }
        )
        
        # Should return bad request
        assert response.status_code == 400
        assert "No image data provided" in response.json()["detail"]
    
    @patch('main.get_vision_service')
    @patch('main.get_ollama_service')
    def test_both_services_unavailable(self, mock_ollama_service, mock_vision_service):
        """Test when both services are unavailable"""
        
        # Mock both services as unhealthy
        mock_vision = AsyncMock()
        mock_vision.check_health.return_value = False
        mock_vision_service.return_value = mock_vision
        
        mock_ollama = AsyncMock()
        mock_ollama.check_health.return_value = False
        mock_ollama_service.return_value = mock_ollama
        
        # Make request
        response = self.client.post(
            "/api/story/recognize_and_generate",
            json={
                "frame_data": self.test_image_base64
            }
        )
        
        # Verify error response
        assert response.status_code == 503
        assert "Both vision and story generation services are unavailable" in response.json()["detail"]
    
    @patch('main.get_vision_service')
    @patch('main.get_ollama_service')
    def test_custom_prompt(self, mock_ollama_service, mock_vision_service):
        """Test story generation with custom prompt"""
        
        # Mock vision service
        mock_vision = AsyncMock()
        mock_vision.check_health.return_value = True
        mock_vision.identify_object.return_value = VisionResult(
            success=True,
            object_name="custom object",
            confidence=0.7,
            processing_time_ms=200.0
        )
        mock_vision_service.return_value = mock_vision
        
        # Mock Ollama service
        mock_ollama = AsyncMock()
        mock_ollama.check_health.return_value = True
        mock_ollama.generate_story.return_value = StoryResponse(
            success=True,
            story={
                "title": "The Adventure of the Custom Object",
                "sentences": ["Test sentence 1", "Test sentence 2", "Test sentence 3", "Test sentence 4", "Test sentence 5"],
                "identified_object": "custom object"
            },
            generation_time_ms=1800.0
        )
        mock_ollama_service.return_value = mock_ollama
        
        # Make request with custom prompt
        custom_prompt = "Look for a specific type of object in this image"
        response = self.client.post(
            "/api/story/recognize_and_generate",
            json={
                "frame_data": self.test_image_base64,
                "custom_prompt": custom_prompt
            }
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify custom prompt was passed to vision service
        mock_vision.identify_object.assert_called_once_with(
            self.test_image_base64,
            custom_prompt
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])