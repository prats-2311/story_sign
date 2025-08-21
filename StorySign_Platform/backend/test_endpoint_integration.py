#!/usr/bin/env python3
"""
Simple integration test for the story generation endpoint
"""

import asyncio
import json
import base64
import sys
import os
from unittest.mock import AsyncMock, patch

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_endpoint_integration():
    """Test the story generation endpoint with mocked services"""
    
    # Import after path setup
    from main import recognize_and_generate_story, StoryGenerationRequest
    from local_vision_service import VisionResult
    from ollama_service import StoryResponse
    
    print("🧪 Testing story generation endpoint integration...")
    
    # Create test request
    test_image_base64 = "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A8A"
    
    request = StoryGenerationRequest(
        frame_data=test_image_base64,
        custom_prompt="Identify the main object in this image"
    )
    
    # Mock the services
    with patch('main.get_vision_service') as mock_vision_service, \
         patch('main.get_ollama_service') as mock_ollama_service:
        
        # Mock vision service
        mock_vision = AsyncMock()
        mock_vision.check_health.return_value = True
        mock_vision.identify_object.return_value = VisionResult(
            success=True,
            object_name="test ball",
            confidence=0.85,
            processing_time_ms=120.0
        )
        mock_vision_service.return_value = mock_vision
        
        # Mock Ollama service
        mock_ollama = AsyncMock()
        mock_ollama.check_health.return_value = True
        mock_ollama.generate_story.return_value = StoryResponse(
            success=True,
            story={
                "title": "The Adventure of the Test Ball",
                "sentences": [
                    "Once upon a time, there was a bright test ball.",
                    "The ball loved to bounce in the playground.",
                    "Children would gather to play with the ball.",
                    "One day, the ball discovered a secret path.",
                    "The ball made many friends on its journey."
                ],
                "identified_object": "test ball"
            },
            generation_time_ms=1800.0
        )
        mock_ollama_service.return_value = mock_ollama
        
        try:
            # Call the endpoint function directly
            result = await recognize_and_generate_story(request)
            
            # Verify the response
            assert result["success"] is True, "Response should indicate success"
            assert "story" in result, "Response should contain story data"
            assert "processing_info" in result, "Response should contain processing info"
            
            story = result["story"]
            assert story["title"] == "The Adventure of the Test Ball", f"Unexpected title: {story['title']}"
            assert len(story["sentences"]) == 5, f"Expected 5 sentences, got {len(story['sentences'])}"
            assert story["identified_object"] == "test ball", f"Unexpected object: {story['identified_object']}"
            
            # Verify processing info
            processing_info = result["processing_info"]
            assert processing_info["object_identification"]["success"] is True
            assert processing_info["object_identification"]["identified_object"] == "test ball"
            assert processing_info["story_generation"]["success"] is True
            
            print("✅ Success case test passed")
            
            # Test vision service failure with fallback
            mock_vision.check_health.return_value = False
            
            result_fallback = await recognize_and_generate_story(request)
            
            assert result_fallback["success"] is True, "Should succeed with fallback"
            processing_info_fallback = result_fallback["processing_info"]["object_identification"]
            assert processing_info_fallback["vision_service_used"] is False
            assert processing_info_fallback["fallback_used"] is True
            
            print("✅ Fallback case test passed")
            
            # Test Ollama service failure
            mock_ollama.check_health.return_value = False
            
            try:
                await recognize_and_generate_story(request)
                assert False, "Should have raised HTTPException"
            except Exception as e:
                # Check if it's the expected HTTPException
                print(f"Exception type: {type(e)}")
                print(f"Exception details: {e}")
                if hasattr(e, 'status_code'):
                    print(f"Status code: {e.status_code}")
                if hasattr(e, 'detail'):
                    print(f"Detail: {e.detail}")
                
                # Should raise HTTPException with 503 status
                if hasattr(e, 'status_code') and e.status_code == 503:
                    print("✅ Service failure case test passed")
                elif "unavailable" in str(e).lower():
                    print("✅ Service failure case test passed")
                else:
                    print(f"❌ Unexpected exception: {e}")
                    raise
            
            print("🎉 All integration tests passed!")
            return True
            
        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = asyncio.run(test_endpoint_integration())
    if success:
        print("\n✅ Integration test completed successfully")
        exit(0)
    else:
        print("\n❌ Integration test failed")
        exit(1)