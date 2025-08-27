#!/usr/bin/env python3
"""
Test script to verify the story generation service fixes
"""

import asyncio
import logging
from ollama_service import get_ollama_service
from local_vision_service import get_vision_service
from config import get_config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_ollama_service():
    """Test Ollama service with fallback functionality"""
    print("\n=== Testing Ollama Service ===")
    
    try:
        ollama_service = await get_ollama_service()
        
        # Test health check
        print("Testing health check...")
        health_status = await ollama_service.check_health()
        print(f"Health status: {health_status}")
        
        # Test story generation
        print("Testing story generation...")
        test_topic = "Book"
        story_result = await ollama_service.generate_story(test_topic)
        
        if story_result:
            print(f"✅ Story generation successful for topic: {test_topic}")
            print(f"Generated {len(story_result)} difficulty levels")
            
            # Check if all difficulty levels are present
            expected_levels = ["amateur", "normal", "mid_level", "difficult", "expert"]
            for level in expected_levels:
                if level in story_result:
                    sentences_count = len(story_result[level].get("sentences", []))
                    print(f"  - {level}: {sentences_count} sentences")
                else:
                    print(f"  - {level}: MISSING")
        else:
            print("❌ Story generation failed")
            
    except Exception as e:
        print(f"❌ Ollama service test failed: {e}")


async def test_local_vision_service():
    """Test local vision service with improved error handling"""
    print("\n=== Testing Local Vision Service ===")
    
    try:
        vision_service = await get_vision_service()
        
        # Test health check
        print("Testing health check...")
        health_status = await vision_service.check_health()
        print(f"Health status: {health_status}")
        
        # Get service status
        print("Getting service status...")
        status = await vision_service.get_service_status()
        print(f"Service enabled: {status['enabled']}")
        print(f"Service URL: {status['service_url']}")
        print(f"Service type: {status['service_type']}")
        print(f"Model name: {status['model_name']}")
        print(f"Healthy: {status['healthy']}")
        
        if status['error']:
            print(f"Error: {status['error']}")
        
        if status['available_models']:
            print(f"Available models: {status['available_models']}")
            
    except Exception as e:
        print(f"❌ Local vision service test failed: {e}")


async def test_configuration():
    """Test configuration loading"""
    print("\n=== Testing Configuration ===")
    
    try:
        config = get_config()
        
        print("Ollama Configuration:")
        print(f"  Service URL: {config.ollama.service_url}")
        print(f"  Story Model: {config.ollama.story_model}")
        print(f"  Analysis Model: {config.ollama.analysis_model}")
        print(f"  Enabled: {config.ollama.enabled}")
        
        print("\nLocal Vision Configuration:")
        print(f"  Service URL: {config.local_vision.service_url}")
        print(f"  Service Type: {config.local_vision.service_type}")
        print(f"  Model Name: {config.local_vision.model_name}")
        print(f"  Enabled: {config.local_vision.enabled}")
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")


async def main():
    """Run all tests"""
    print("🔧 Testing Service Fixes")
    print("=" * 50)
    
    await test_configuration()
    await test_ollama_service()
    await test_local_vision_service()
    
    print("\n" + "=" * 50)
    print("✅ Service fix testing completed")


if __name__ == "__main__":
    asyncio.run(main())