#!/usr/bin/env python3
"""
Quick fix to improve Groq error handling and test with a real frontend-like request
"""

import asyncio
import aiohttp
import base64
import json
import logging
from io import BytesIO
from PIL import Image

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_with_improved_error_handling():
    """Test Groq API with improved error handling"""
    
    # Create a test image similar to what frontend sends
    img = Image.new('RGB', (640, 480), 'white')
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.ellipse([200, 150, 440, 330], fill='red', outline='darkred', width=5)
    
    # Save with high quality (like frontend would)
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=95)
    img_bytes = buffer.getvalue()
    img_b64 = base64.b64encode(img_bytes).decode('utf-8')
    
    print(f"Test image: {len(img_bytes)} bytes")
    
    # Groq API configuration
    api_key = "your_groq_api_key_here"  # Replace with your actual API key
    model_name = "meta-llama/llama-4-scout-17b-16e-instruct"
    base_url = "https://api.groq.com/openai/v1"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test multiple scenarios
    test_cases = [
        {
            "name": "Original large image",
            "image": img_b64,
            "prompt": "What do you see in this image? Answer in one word."
        }
    ]
    
    # Add resized version
    if len(img_bytes) > 4096:  # 4KB
        print("Creating resized version...")
        
        # Resize image
        img_resized = img.resize((300, 225), Image.Resampling.LANCZOS)
        buffer_resized = BytesIO()
        img_resized.save(buffer_resized, format='JPEG', quality=75)
        resized_bytes = buffer_resized.getvalue()
        resized_b64 = base64.b64encode(resized_bytes).decode('utf-8')
        
        print(f"Resized image: {len(resized_bytes)} bytes")
        
        test_cases.append({
            "name": "Resized image",
            "image": resized_b64,
            "prompt": "What do you see in this image? Answer in one word."
        })
    
    async with aiohttp.ClientSession() as session:
        
        for i, test_case in enumerate(test_cases):
            print(f"\n🧪 Test {i+1}: {test_case['name']}")
            
            payload = {
                "model": model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": test_case["prompt"]},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{test_case['image']}"}
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
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    print(f"   Status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                        print(f"   ✅ Success: '{content[:50]}...'")
                    else:
                        # Get detailed error information
                        error_text = await response.text()
                        print(f"   ❌ Failed: {response.status}")
                        print(f"   Error text: {error_text}")
                        
                        # Try to parse as JSON for more details
                        try:
                            error_json = json.loads(error_text)
                            print(f"   Error details: {json.dumps(error_json, indent=2)}")
                        except:
                            print(f"   Raw error: {error_text[:500]}")
                        
                        # Check response headers for additional info
                        print(f"   Response headers:")
                        for header, value in response.headers.items():
                            if 'rate' in header.lower() or 'limit' in header.lower() or 'retry' in header.lower():
                                print(f"     {header}: {value}")
            
            except Exception as e:
                print(f"   ❌ Exception: {e}")
            
            # Wait between tests to avoid rate limiting
            await asyncio.sleep(2)

async def test_rate_limiting():
    """Test if we're hitting rate limits"""
    print(f"\n🔄 Testing rate limiting with multiple quick requests...")
    
    api_key = "your_groq_api_key_here"  # Replace with your actual API key
    model_name = "meta-llama/llama-4-scout-17b-16e-instruct"
    base_url = "https://api.groq.com/openai/v1"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Simple text requests to test rate limiting
    async with aiohttp.ClientSession() as session:
        
        for i in range(5):
            print(f"   Request {i+1}/5...")
            
            payload = {
                "model": model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": f"Hello, this is test request {i+1}. Please respond briefly."
                    }
                ],
                "max_tokens": 10,
                "temperature": 0.1
            }
            
            try:
                async with session.post(
                    f"{base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        print(f"     ✅ Success")
                    elif response.status == 429:
                        print(f"     ⚠️ Rate limited (429)")
                        # Check rate limit headers
                        for header, value in response.headers.items():
                            if 'rate' in header.lower() or 'limit' in header.lower():
                                print(f"       {header}: {value}")
                    else:
                        print(f"     ❌ Error: {response.status}")
            
            except Exception as e:
                print(f"     ❌ Exception: {e}")
            
            # Small delay
            await asyncio.sleep(0.5)

async def main():
    """Main test function"""
    print("🔧 Testing Groq API Error Handling")
    print("="*50)
    
    await test_with_improved_error_handling()
    await test_rate_limiting()

if __name__ == "__main__":
    asyncio.run(main())