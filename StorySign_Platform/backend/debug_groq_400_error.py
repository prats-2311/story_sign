#!/usr/bin/env python3
"""
Debug script to investigate the Groq API 400 error from the logs
"""

import asyncio
import aiohttp
import base64
import json
import logging
from io import BytesIO
from PIL import Image

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_groq_400_error():
    """Debug the exact 400 error from the logs"""
    
    # Recreate the exact scenario from the logs
    api_key = "your_groq_api_key_here"  # Replace with your actual API key
    model_name = "meta-llama/llama-4-scout-17b-16e-instruct"
    base_url = "https://api.groq.com/openai/v1"
    
    # Create a test image similar to what would come from frontend (larger image)
    img = Image.new('RGB', (640, 480), 'white')  # Typical webcam resolution
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    
    # Draw something recognizable
    draw.ellipse([200, 150, 440, 330], fill='red', outline='darkred', width=5)
    draw.text((280, 220), "BALL", fill='white')
    
    # Save as JPEG with different qualities to test
    test_cases = [
        {"quality": 85, "format": "JPEG", "name": "high_quality"},
        {"quality": 65, "format": "JPEG", "name": "medium_quality"},
        {"quality": 45, "format": "JPEG", "name": "low_quality"},
    ]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        
        for test_case in test_cases:
            print(f"\n🧪 Testing {test_case['name']} (quality: {test_case['quality']})")
            
            # Create image with specific quality
            buffer = BytesIO()
            img.save(buffer, format=test_case['format'], quality=test_case['quality'])
            img_bytes = buffer.getvalue()
            img_b64 = base64.b64encode(img_bytes).decode('utf-8')
            
            print(f"   Image size: {len(img_bytes)} bytes")
            print(f"   Base64 size: {len(img_b64)} characters")
            
            # Test 1: Simple text request (should work)
            print("   Testing text-only request...")
            payload_text = {
                "model": model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello, can you help me?"
                    }
                ],
                "max_tokens": 50,
                "temperature": 0.1
            }
            
            try:
                async with session.post(
                    f"{base_url}/chat/completions",
                    json=payload_text,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        print("   ✅ Text request successful")
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Text request failed: {response.status} - {error_text[:100]}")
            except Exception as e:
                print(f"   ❌ Text request exception: {e}")
            
            # Test 2: Vision request (the failing one)
            print("   Testing vision request...")
            payload_vision = {
                "model": model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What do you see in this image?"},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                            }
                        ]
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 100,
                "stream": False
            }
            
            try:
                async with session.post(
                    f"{base_url}/chat/completions",
                    json=payload_vision,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                        print(f"   ✅ Vision request successful: '{content}'")
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Vision request failed: {response.status}")
                        print(f"   Error details: {error_text}")
                        
                        # Try to parse error JSON
                        try:
                            error_json = json.loads(error_text)
                            print(f"   Error JSON: {json.dumps(error_json, indent=2)}")
                        except:
                            pass
            except Exception as e:
                print(f"   ❌ Vision request exception: {e}")
            
            # Small delay between tests
            await asyncio.sleep(1)
        
        # Test 3: Try with a very small, simple image
        print(f"\n🧪 Testing with minimal image")
        
        # Create minimal image
        small_img = Image.new('RGB', (100, 100), 'red')
        buffer = BytesIO()
        small_img.save(buffer, format='JPEG', quality=90)
        small_bytes = buffer.getvalue()
        small_b64 = base64.b64encode(small_bytes).decode('utf-8')
        
        print(f"   Minimal image size: {len(small_bytes)} bytes")
        
        payload_minimal = {
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What color is this?"},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{small_b64}"}
                        }
                    ]
                }
            ],
            "temperature": 0.1,
            "max_tokens": 10,
            "stream": False
        }
        
        try:
            async with session.post(
                f"{base_url}/chat/completions",
                json=payload_minimal,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                    print(f"   ✅ Minimal image successful: '{content}'")
                else:
                    error_text = await response.text()
                    print(f"   ❌ Minimal image failed: {response.status} - {error_text}")
        except Exception as e:
            print(f"   ❌ Minimal image exception: {e}")

if __name__ == "__main__":
    asyncio.run(debug_groq_400_error())