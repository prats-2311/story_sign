#!/usr/bin/env python3
"""
Simple test script to verify Groq Vision API with a real object identification
"""

import asyncio
import base64
import logging
from io import BytesIO
from PIL import Image, ImageDraw

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_image():
    """Create a simple test image with a red circle (representing a ball)"""
    # Create a 200x200 white image
    img = Image.new('RGB', (200, 200), 'white')
    draw = ImageDraw.Draw(img)
    
    # Draw a red circle in the center
    draw.ellipse([50, 50, 150, 150], fill='red', outline='darkred', width=3)
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    img_bytes = buffer.getvalue()
    
    return base64.b64encode(img_bytes).decode('utf-8')

async def test_groq_vision():
    """Test Groq vision service with a simple object"""
    try:
        # Import after setting up logging
        from local_vision_service import get_vision_service
        from config import get_config
        
        # Load configuration
        config = get_config()
        logger.info(f"🔧 Configuration:")
        logger.info(f"   Service type: {config.local_vision.service_type}")
        logger.info(f"   Model: {config.local_vision.model_name}")
        logger.info(f"   Groq enabled: {config.groq.enabled}")
        logger.info(f"   Groq configured: {config.groq.is_configured()}")
        
        # Get vision service
        vision_service = await get_vision_service()
        
        # Check health
        logger.info("🏥 Checking Groq API health...")
        health_status = await vision_service.check_health()
        
        if health_status:
            logger.info("✅ Groq Vision API is healthy!")
            
            # Create test image
            logger.info("🎨 Creating test image (red ball)...")
            test_image_b64 = create_test_image()
            logger.info(f"   Image size: {len(test_image_b64)} characters")
            
            # Test object identification
            logger.info("🔍 Testing object identification...")
            result = await vision_service.identify_object(
                test_image_b64, 
                "What is the main object in this image? Respond with just the object name in 1-2 words."
            )
            
            if result.success:
                logger.info("✅ Object identification successful!")
                logger.info(f"   🎯 Object: '{result.object_name}'")
                logger.info(f"   📊 Confidence: {result.confidence:.2f}")
                logger.info(f"   ⏱️  Processing time: {result.processing_time_ms:.1f}ms")
                
                # Test with a different prompt
                logger.info("\n🔍 Testing with different prompt...")
                result2 = await vision_service.identify_object(
                    test_image_b64, 
                    "Describe what you see in this image in one word."
                )
                
                if result2.success:
                    logger.info(f"   🎯 Second result: '{result2.object_name}' (confidence: {result2.confidence:.2f})")
                else:
                    logger.warning(f"   ⚠️  Second test failed: {result2.error_message}")
                
            else:
                logger.error(f"❌ Object identification failed: {result.error_message}")
                
        else:
            logger.error("❌ Groq Vision API health check failed")
            
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

if __name__ == "__main__":
    print("🔍 Testing Groq Vision API with Llama 4 Scout...")
    print("=" * 60)
    asyncio.run(test_groq_vision())
    print("=" * 60)
    print("✅ Test completed!")