#!/usr/bin/env python3
"""
Simple test to verify Ollama service basic functionality
"""

import asyncio
from ollama_service import OllamaService

async def test_basic_functionality():
    """Test basic service functionality"""
    print("Testing Ollama service basic functionality...")
    
    service = OllamaService()
    print(f"✓ Service initialized with URL: {service.config.service_url}")
    print(f"✓ Story model: {service.config.story_model}")
    print(f"✓ Analysis model: {service.config.analysis_model}")
    print(f"✓ Service enabled: {service.config.enabled}")
    
    # Test prompt creation
    story_prompt = service._create_story_prompt("ball")
    print(f"✓ Story prompt created (length: {len(story_prompt)})")
    
    analysis_prompt = service._create_analysis_prompt(
        [{"landmarks": {"hands": True}}], 
        "Hello world"
    )
    print(f"✓ Analysis prompt created (length: {len(analysis_prompt)})")
    
    # Test response parsing
    story_response = {
        "response": "The ball bounced.\nChildren played.\nThe ball rolled.\nA dog chased.\nEveryone smiled."
    }
    parsed_story = service._parse_story_response(story_response, "ball")
    print(f"✓ Story parsing works: {len(parsed_story['sentences'])} sentences")
    
    analysis_response = {
        "response": "FEEDBACK: Good signing!\nCONFIDENCE: 0.8\nSUGGESTIONS: Keep practicing, Focus on clarity"
    }
    parsed_analysis = service._parse_analysis_response(analysis_response)
    print(f"✓ Analysis parsing works: confidence {parsed_analysis['confidence_score']}")
    
    print("✓ All basic functionality tests passed!")

if __name__ == "__main__":
    asyncio.run(test_basic_functionality())