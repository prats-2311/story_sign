#!/usr/bin/env python3
"""
Test the image resize function that's causing the 400 errors
"""

import asyncio
import base64
import logging
from io import BytesIO
from PIL import Image

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_large_test_image():
    """Create a large test image similar to what comes from frontend"""
    # Create a large image (similar to webcam capture)
    img = Image.new('RGB', (640, 480), 'white')
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    
    # Draw a recognizable object
    draw.ellipse([200, 150, 440, 330], fill='blue', outline='darkblue', width=5)
    
    # Save as high quality JPEG
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=95)
    img_bytes = buffer.getvalue()
    
    # Convert to base64 (as it would come from frontend)
    img_b64 = base64.b64encode(img_bytes).decode('utf-8')
    
    print(f"Original image: {len(img_bytes)} bytes, {len(img_b64)} base64 chars")
    return img_b64

def test_resize_function(base64_data, max_size_kb=4):
    """Test the resize function from local_vision_service.py"""
    try:
        import base64
        from PIL import Image
        from io import BytesIO
        
        print(f"\n🔧 Testing resize function with max_size_kb={max_size_kb}")
        
        # Decode the base64 image
        clean_data = base64_data
        if clean_data.startswith('data:image/'):
            clean_data = clean_data.split(',', 1)[1]
        
        img_bytes = base64.b64decode(clean_data)
        print(f"Input image size: {len(img_bytes)} bytes")
        
        # If image is already small enough, return as-is
        if len(img_bytes) <= max_size_kb * 1024:
            print("Image already small enough, no resize needed")
            return base64_data
        
        # Open image with PIL
        img = Image.open(BytesIO(img_bytes))
        print(f"Image dimensions: {img.size}")
        print(f"Image format: {img.format}")
        print(f"Image mode: {img.mode}")
        
        # Calculate new size to fit within limit
        width, height = img.size
        quality = 85
        
        resize_attempts = 0
        while resize_attempts < 10:  # Prevent infinite loop
            resize_attempts += 1
            
            # Try current size with current quality
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=quality)
            new_size = len(buffer.getvalue())
            
            print(f"  Attempt {resize_attempts}: {width}x{height} @ quality {quality} = {new_size} bytes")
            
            if new_size <= max_size_kb * 1024:
                # Size is good, return the resized image
                resized_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                print(f"✅ Resize successful: {len(img_bytes)} -> {new_size} bytes")
                
                # Test if the resized image is valid
                try:
                    test_img = Image.open(BytesIO(buffer.getvalue()))
                    print(f"✅ Resized image is valid: {test_img.size}, {test_img.format}, {test_img.mode}")
                except Exception as e:
                    print(f"❌ Resized image is invalid: {e}")
                
                return resized_b64
            
            # Reduce quality first
            if quality > 60:
                quality -= 10
                continue
            
            # If quality is already low, reduce dimensions
            if width > 150 or height > 150:
                width = int(width * 0.8)
                height = int(height * 0.8)
                img = img.resize((width, height), Image.Resampling.LANCZOS)
                quality = 85  # Reset quality for new size
                continue
            
            # If we can't reduce further, return what we have
            break
        
        # Return the best we could do
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=60)
        resized_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        print(f"⚠️ Could not resize below {max_size_kb}KB, final size: {len(buffer.getvalue())} bytes")
        return resized_b64
        
    except Exception as e:
        print(f"❌ Error resizing image: {e}")
        import traceback
        traceback.print_exc()
        return base64_data

async def test_resized_image_with_groq(resized_b64):
    """Test the resized image with Groq API"""
    import aiohttp
    
    api_key = "your_groq_api_key_here"  # Replace with your actual API key
    model_name = "meta-llama/llama-4-scout-17b-16e-instruct"
    base_url = "https://api.groq.com/openai/v1"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Clean the base64 data
    clean_data = resized_b64
    if clean_data.startswith('data:image/'):
        clean_data = clean_data.split(',', 1)[1]
    
    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What do you see in this image? Answer in one word."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{clean_data}"}
                    }
                ]
            }
        ],
        "temperature": 0.1,
        "max_tokens": 50,
        "stream": False
    }
    
    print(f"\n🌐 Testing resized image with Groq API...")
    print(f"Base64 length: {len(clean_data)}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                    print(f"✅ Groq API success: '{content}'")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Groq API failed: {response.status}")
                    print(f"Error: {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Groq API exception: {e}")
            return False

async def main():
    """Main test function"""
    print("🧪 Testing Image Resize Function")
    print("="*50)
    
    # Create a large test image
    large_image_b64 = create_large_test_image()
    
    # Test the resize function
    resized_image_b64 = test_resize_function(large_image_b64, max_size_kb=4)
    
    # Test the resized image with Groq API
    success = await test_resized_image_with_groq(resized_image_b64)
    
    if success:
        print("\n✅ Image resize function is working correctly!")
    else:
        print("\n❌ Image resize function has issues!")

if __name__ == "__main__":
    asyncio.run(main())