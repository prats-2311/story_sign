#!/usr/bin/env python3
"""
Test different image sizes and formats to identify the issue
"""

import asyncio
import base64
import logging
from io import BytesIO
from PIL import Image, ImageDraw

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_various_images():
    """Test various image configurations"""
    
    from local_vision_service import get_vision_service
    
    vision_service = await get_vision_service()
    
    # Test different image sizes and qualities
    test_configs = [
        {"size": (100, 100), "quality": 95, "name": "small_high_quality"},
        {"size": (200, 200), "quality": 85, "name": "medium_good_quality"},
        {"size": (300, 300), "quality": 75, "name": "large_medium_quality"},
        {"size": (400, 400), "quality": 60, "name": "xlarge_low_quality"},
        {"size": (150, 150), "quality": 90, "name": "optimal_size"},
    ]
    
    for config in test_configs:
        print(f"\n🧪 Testing {config['name']}: {config['size']} at {config['quality']}% quality")
        
        # Create test image
        img = Image.new('RGB', config['size'], 'white')
        draw = ImageDraw.Draw(img)
        
        # Draw a simple blue rectangle
        margin = config['size'][0] // 4
        draw.rectangle([
            margin, margin, 
            config['size'][0] - margin, 
            config['size'][1] - margin
        ], fill='blue', outline='darkblue', width=2)
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=config['quality'])
        img_bytes = buffer.getvalue()
        image_b64 = base64.b64encode(img_bytes).decode('utf-8')
        
        print(f"   Image bytes: {len(img_bytes)}")
        print(f"   Base64 chars: {len(image_b64)}")
        
        # Test with vision service
        try:
            result = await vision_service.identify_object(
                image_b64,
                "What shape do you see in this image? Respond with just the shape name."
            )
            
            if result.success:
                print(f"   ✅ Success: '{result.object_name}' (confidence: {result.confidence:.2f})")
            else:
                print(f"   ❌ Failed: {result.error_message}")
        
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(1)
    
    # Test with different prompts
    print(f"\n🧪 Testing different prompts with optimal image")
    
    # Create optimal image
    img = Image.new('RGB', (200, 200), 'white')
    draw = ImageDraw.Draw(img)
    draw.ellipse([50, 50, 150, 150], fill='red', outline='darkred', width=3)
    
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    image_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    prompts = [
        "What do you see?",
        "What is the main object?",
        "What shape is this?",
        "What color is the main object?",
        "Describe this image in one word.",
        "What is the primary shape in this image? Answer with just the shape name.",
    ]
    
    for i, prompt in enumerate(prompts):
        print(f"\n   Prompt {i+1}: '{prompt}'")
        try:
            result = await vision_service.identify_object(image_b64, prompt)
            
            if result.success:
                print(f"   ✅ Success: '{result.object_name}' (confidence: {result.confidence:.2f})")
            else:
                print(f"   ❌ Failed: {result.error_message}")
        
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(test_various_images())