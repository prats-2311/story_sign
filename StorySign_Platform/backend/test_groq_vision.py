#!/usr/bin/env python3
"""
Test script to verify vision service configuration (Ollama + Groq)
"""

import asyncio
import base64
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_vision_configuration():
    """Test the complete vision service configuration"""
    try:
        # Import after setting up logging
        from local_vision_service import get_vision_service
        from config import get_config
        
        # Load configuration
        config = get_config()
        logger.info(f"Local vision service type: {config.local_vision.service_type}")
        logger.info(f"Vision service URL: {config.local_vision.service_url}")
        logger.info(f"Vision model: {config.local_vision.model_name}")
        logger.info(f"Groq enabled: {config.groq.enabled}")
        logger.info(f"Groq configured: {config.groq.is_configured()}")
        logger.info(f"Groq model: {config.groq.model_name}")
        
        # Get vision service
        vision_service = await get_vision_service()
        
        # Check health
        logger.info("Checking vision service health...")
        health_status = await vision_service.check_health()
        logger.info(f"Health status: {health_status}")
        
        if health_status:
            logger.info("✅ Vision service is configured and healthy!")
            
            # Test with a larger test image (100x100 pixel red square PNG)
            test_image_b64 = "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/wA=="
            
            logger.info("Testing object identification with sample image...")
            result = await vision_service.identify_object(test_image_b64, "What do you see in this image? Respond with just the main color or object.")
            
            if result.success:
                logger.info(f"✅ Object identification successful!")
                logger.info(f"   Object: {result.object_name}")
                logger.info(f"   Confidence: {result.confidence}")
                logger.info(f"   Processing time: {result.processing_time_ms:.2f}ms")
            else:
                logger.error(f"❌ Object identification failed: {result.error_message}")
        else:
            logger.error("❌ Vision service health check failed")
            logger.info("💡 Make sure Ollama is running with the llava:7b model")
            logger.info("💡 Run: python setup_ollama_vision.py")
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        try:
            from local_vision_service import cleanup_vision_service
            await cleanup_vision_service()
        except:
            pass

async def test_groq_text_generation():
    """Test Groq API for text generation"""
    try:
        import aiohttp
        from config import get_config
        
        config = get_config()
        
        if not config.groq.is_configured():
            logger.warning("❌ Groq API not configured")
            return False
        
        logger.info("Testing Groq API for text generation...")
        
        headers = {
            "Authorization": f"Bearer {config.groq.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": config.groq.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": "Write a very short story about a red ball in exactly 2 sentences."
                }
            ],
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{config.groq.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                    logger.info(f"✅ Groq text generation successful!")
                    logger.info(f"   Response: {content}")
                    return True
                else:
                    logger.error(f"❌ Groq API failed: {response.status}")
                    error_text = await response.text()
                    logger.error(f"   Error: {error_text}")
                    return False
    
    except Exception as e:
        logger.error(f"❌ Groq test failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing StorySign Vision Configuration...")
    print("=" * 50)
    
    async def run_all_tests():
        # Test vision service (Ollama)
        await test_vision_configuration()
        
        print("\n" + "=" * 50)
        
        # Test text generation (Groq)
        await test_groq_text_generation()
    
    asyncio.run(run_all_tests())
    print("=" * 50)
    print("✅ All tests completed!")