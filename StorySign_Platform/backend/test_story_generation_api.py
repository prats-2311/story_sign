#!/usr/bin/env python3
"""
Test the complete story generation API endpoint with Groq vision
"""

import asyncio
import aiohttp
import base64
import json
import logging
from io import BytesIO
from PIL import Image, ImageDraw

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_images():
    """Create test images for different objects"""
    images = {}
    
    # Red ball
    img = Image.new('RGB', (200, 200), 'white')
    draw = ImageDraw.Draw(img)
    draw.ellipse([50, 50, 150, 150], fill='red', outline='darkred', width=3)
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    images['ball'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    # Blue book
    img = Image.new('RGB', (200, 200), 'white')
    draw = ImageDraw.Draw(img)
    draw.rectangle([40, 60, 160, 140], fill='blue', outline='darkblue', width=3)
    draw.line([40, 80, 160, 80], fill='white', width=2)
    draw.line([40, 100, 160, 100], fill='white', width=2)
    draw.line([40, 120, 160, 120], fill='white', width=2)
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    images['book'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    # Yellow cup
    img = Image.new('RGB', (200, 200), 'white')
    draw = ImageDraw.Draw(img)
    # Cup body
    draw.rectangle([70, 80, 130, 150], fill='yellow', outline='orange', width=2)
    # Handle
    draw.arc([130, 100, 150, 130], 270, 90, fill='orange', width=3)
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    images['cup'] = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return images

async def test_story_api(base_url="http://127.0.0.1:8000"):
    """Test the story generation API endpoint"""
    
    logger.info(f"🧪 Testing Story Generation API at {base_url}")
    
    # Create test images
    logger.info("🎨 Creating test images...")
    test_images = create_test_images()
    
    async with aiohttp.ClientSession() as session:
        
        for object_name, image_data in test_images.items():
            logger.info(f"\n🔍 Testing with {object_name} image...")
            
            try:
                # Prepare the request
                payload = {
                    "frame_data": image_data,
                    "custom_prompt": f"What is the main object in this image? Respond with just the object name."
                }
                
                # Make the API request
                logger.info("📡 Sending request to /api/v1/story/recognize_and_generate...")
                
                timeout = aiohttp.ClientTimeout(total=60)  # 60 second timeout
                async with session.post(
                    f"{base_url}/api/v1/story/recognize_and_generate",
                    json=payload,
                    timeout=timeout
                ) as response:
                    
                    logger.info(f"📊 Response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        logger.info("✅ Story generation successful!")
                        logger.info(f"   🎯 Identified object: '{data.get('identified_object', 'N/A')}'")
                        logger.info(f"   📖 Story title: '{data.get('story', {}).get('title', 'N/A')}'")
                        
                        story_sentences = data.get('story', {}).get('sentences', [])
                        logger.info(f"   📝 Story sentences: {len(story_sentences)}")
                        
                        if story_sentences:
                            logger.info(f"   📄 First sentence: '{story_sentences[0][:100]}...'")
                        
                        processing_time = data.get('processing_time_ms', 0)
                        logger.info(f"   ⏱️  Total processing time: {processing_time:.1f}ms")
                        
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ API request failed: {response.status}")
                        logger.error(f"   Error: {error_text[:200]}...")
                        
            except asyncio.TimeoutError:
                logger.error(f"❌ Request timed out for {object_name}")
            except Exception as e:
                logger.error(f"❌ Request failed for {object_name}: {e}")
        
        # Test health endpoint
        logger.info(f"\n🏥 Testing health endpoint...")
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    logger.info("✅ Health check passed!")
                    logger.info(f"   Status: {health_data.get('status', 'unknown')}")
                    
                    services = health_data.get('services', {})
                    for service, status in services.items():
                        logger.info(f"   {service}: {status}")
                else:
                    logger.warning(f"⚠️  Health check returned {response.status}")
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")

async def main():
    """Main test function"""
    print("🚀 Testing StorySign Story Generation API with Groq Vision")
    print("=" * 70)
    
    # Test the API
    await test_story_api()
    
    print("=" * 70)
    print("✅ API testing completed!")

if __name__ == "__main__":
    asyncio.run(main())