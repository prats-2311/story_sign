#!/usr/bin/env python3
"""
Debug script to investigate Groq API 400 errors
"""

import asyncio
import aiohttp
import base64
import json
import logging
from io import BytesIO
from PIL import Image, ImageDraw

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_groq_request():
    """Debug what's causing the 400 errors"""
    
    # Create a simple test image
    img = Image.new('RGB', (200, 200), 'white')
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 150, 150], fill='blue', outline='darkblue', width=3)
    
    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    img_bytes = buffer.getvalue()
    image_b64 = base64.b64encode(img_bytes).decode('utf-8')
    
    print(f"Image size: {len(img_bytes)} bytes")
    print(f"Base64 size: {len(image_b64)} characters")
    
    # Test direct Groq API call
    api_key = "your_groq_api_key_here"  # Replace with your actual API key
    model_name = "meta-llama/llama-4-scout-17b-16e-instruct"
    base_url = "https://api.groq.com/openai/v1"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test 1: Simple text request (should work)
    print("\n🧪 Test 1: Simple text request")
    payload1 = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": "Hello, can you see images?"
            }
        ],
        "max_tokens": 50,
        "temperature": 0.1
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{base_url}/chat/completions",
                json=payload1,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                print(f"Status: {response.status}")
                text = await response.text()
                print(f"Response: {text[:200]}...")
        except Exception as e:
            print(f"Error: {e}")
    
    # Test 2: Vision request with image
    print("\n🧪 Test 2: Vision request with image")
    payload2 = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What do you see in this image?"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                    }
                ]
            }
        ],
        "max_tokens": 50,
        "temperature": 0.1
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{base_url}/chat/completions",
                json=payload2,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                print(f"Status: {response.status}")
                text = await response.text()
                print(f"Response: {text[:500]}...")
                
                if response.status != 200:
                    try:
                        error_data = json.loads(text)
                        print(f"Error details: {json.dumps(error_data, indent=2)}")
                    except:
                        pass
        except Exception as e:
            print(f"Error: {e}")
    
    # Test 3: Check if model supports vision
    print("\n🧪 Test 3: Check model capabilities")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"{base_url}/models",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get('data', [])
                    
                    for model in models:
                        if model_name in model.get('id', ''):
                            print(f"Found model: {json.dumps(model, indent=2)}")
                            break
                    else:
                        print(f"Model {model_name} not found in available models")
                        print("Available models:")
                        for model in models[:5]:
                            print(f"  - {model.get('id', 'unknown')}")
        except Exception as e:
            print(f"Error checking models: {e}")

if __name__ == "__main__":
    asyncio.run(debug_groq_request())