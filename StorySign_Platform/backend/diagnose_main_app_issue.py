#!/usr/bin/env python3
"""
Diagnose the issue by using the exact same code path as the main application
"""

import asyncio
import base64
import logging
from io import BytesIO
from PIL import Image

# Set up logging to match main app
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_exact_main_app_flow():
    """Test using the exact same flow as the main application"""
    
    print("🔍 Testing with exact main application flow...")
    
    # Import the same modules as main app
    try:
        from local_vision_service import get_vision_service
        from config import get_config
        
        # Load config exactly like main app
        config = get_config()
        print(f"✅ Config loaded successfully")
        print(f"   Service type: {config.local_vision.service_type}")
        print(f"   Model name: {config.local_vision.model_name}")
        print(f"   Groq enabled: {config.groq.enabled}")
        print(f"   Groq configured: {config.groq.is_configured()}")
        print(f"   Groq API key length: {len(config.groq.api_key) if config.groq.api_key else 0}")
        
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return False
    
    # Create test image exactly like frontend would send
    print(f"\n📸 Creating test image (simulating frontend capture)...")
    
    # Simulate a webcam capture (640x480, high quality)
    img = Image.new('RGB', (640, 480), 'white')
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    
    # Draw a simple object
    draw.ellipse([200, 150, 440, 330], fill='blue', outline='darkblue', width=5)
    
    # Save with high quality like frontend
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=95)
    img_bytes = buffer.getvalue()
    
    # Convert to base64 like frontend
    img_b64 = base64.b64encode(img_bytes).decode('utf-8')
    
    print(f"   Image size: {len(img_bytes)} bytes")
    print(f"   Base64 length: {len(img_b64)} characters")
    
    # Test vision service exactly like main app
    try:
        print(f"\n🔧 Getting vision service...")
        vision_service = await get_vision_service()
        print(f"✅ Vision service obtained")
        
        # Health check like main app
        print(f"🏥 Checking service health...")
        is_healthy = await vision_service.check_health()
        print(f"   Health status: {is_healthy}")
        
        if not is_healthy:
            print(f"❌ Service is not healthy, stopping test")
            return False
        
        # Object identification exactly like main app
        print(f"\n🎯 Testing object identification...")
        print(f"   Using prompt: 'What do you see in this image? Answer in one word.'")
        
        result = await vision_service.identify_object(
            img_b64,
            "What do you see in this image? Answer in one word."
        )
        
        print(f"\n📊 Results:")
        print(f"   Success: {result.success}")
        if result.success:
            print(f"   Object: '{result.object_name}'")
            print(f"   Confidence: {result.confidence}")
            print(f"   Processing time: {result.processing_time_ms:.1f}ms")
        else:
            print(f"   Error: {result.error_message}")
        
        return result.success
        
    except Exception as e:
        print(f"❌ Vision service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_endpoint_simulation():
    """Simulate the exact API endpoint call"""
    
    print(f"\n🌐 Testing API endpoint simulation...")
    
    try:
        # Import the exact modules used in API
        from local_vision_service import get_vision_service
        from ollama_service import get_ollama_service
        
        # Create test image
        img = Image.new('RGB', (640, 480), 'white')
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.ellipse([200, 150, 440, 330], fill='red', outline='darkred', width=5)
        
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=95)
        img_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        print(f"   Test image created: {len(buffer.getvalue())} bytes")
        
        # Step 1: Vision service (like in API)
        print(f"   Step 1: Object identification...")
        vision_service = await get_vision_service()
        
        vision_result = await vision_service.identify_object(
            img_b64,
            "What is the main object in this image? Respond with just the object name."
        )
        
        if vision_result.success:
            identified_object = vision_result.object_name
            print(f"   ✅ Object identified: '{identified_object}'")
            
            # Step 2: Story generation (like in API)
            print(f"   Step 2: Story generation...")
            ollama_service = await get_ollama_service()
            
            story_result = await ollama_service.generate_story(identified_object)
            
            if story_result.success:
                print(f"   ✅ Story generated: '{story_result.story.title}'")
                return True
            else:
                print(f"   ❌ Story generation failed: {story_result.error_message}")
                return False
        else:
            print(f"   ❌ Object identification failed: {vision_result.error_message}")
            
            # Test fallback like main app
            print(f"   Testing fallback mechanism...")
            fallback_object = "a friendly cat"
            print(f"   Using fallback: '{fallback_object}'")
            
            ollama_service = await get_ollama_service()
            story_result = await ollama_service.generate_story(fallback_object)
            
            if story_result.success:
                print(f"   ✅ Fallback story generated: '{story_result.story.title}'")
                print(f"   ⚠️ This matches your log behavior - vision failed, fallback worked")
                return False  # Vision failed, but fallback worked
            else:
                print(f"   ❌ Even fallback failed: {story_result.error_message}")
                return False
    
    except Exception as e:
        print(f"❌ API simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main diagnostic function"""
    print("🔍 Diagnosing Main Application Issue")
    print("="*60)
    
    # Test 1: Exact main app flow
    success1 = await test_exact_main_app_flow()
    
    # Test 2: API endpoint simulation
    success2 = await test_api_endpoint_simulation()
    
    print(f"\n" + "="*60)
    print(f"📊 DIAGNOSTIC RESULTS")
    print(f"="*60)
    print(f"Main app flow test: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"API endpoint test: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if not success1:
        print(f"\n🔧 RECOMMENDED FIXES:")
        print(f"1. Check if Groq API key is properly loaded in main app")
        print(f"2. Verify configuration file is being read correctly")
        print(f"3. Check for rate limiting or API quota issues")
        print(f"4. Verify image processing pipeline")
    else:
        print(f"\n✅ Vision service is working correctly!")
        print(f"The issue might be intermittent or environment-specific.")

if __name__ == "__main__":
    asyncio.run(main())