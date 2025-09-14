#!/usr/bin/env python3
"""
Check available Groq models to find vision models
"""

import asyncio
import aiohttp
import json

async def check_groq_models():
    """Check what models are available in Groq API"""
    api_key = "your_groq_api_key_here"  # Replace with your actual API key
    base_url = "https://api.groq.com/openai/v1"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{base_url}/models", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get('data', [])
                    
                    print("Available Groq Models:")
                    print("=" * 50)
                    
                    vision_models = []
                    text_models = []
                    
                    for model in models:
                        model_id = model.get('id', '')
                        model_type = model.get('object', '')
                        
                        # Check if it's likely a vision model
                        if any(keyword in model_id.lower() for keyword in ['vision', 'llava', 'gpt-4v', 'claude-3']):
                            vision_models.append(model_id)
                        else:
                            text_models.append(model_id)
                    
                    if vision_models:
                        print("🔍 VISION MODELS:")
                        for model in vision_models:
                            print(f"  - {model}")
                    else:
                        print("❌ No obvious vision models found")
                    
                    print(f"\n📝 TEXT MODELS ({len(text_models)}):")
                    for model in text_models[:10]:  # Show first 10
                        print(f"  - {model}")
                    if len(text_models) > 10:
                        print(f"  ... and {len(text_models) - 10} more")
                    
                    print(f"\n📊 Total models: {len(models)}")
                    
                    # Check if any models support vision by testing capabilities
                    print("\n🔍 Testing models for vision capabilities...")
                    
                    # Test a few promising models
                    test_models = [
                        'llama-3.3-70b-versatile',
                        'gemma2-9b-it',
                        'openai/gpt-oss-120b'
                    ]
                    
                    for model_id in test_models:
                        if model_id in text_models:
                            print(f"\n🧪 Testing {model_id}...")
                            await test_model_vision_capability(session, headers, base_url, model_id)
                
                else:
                    print(f"❌ Failed to fetch models: {response.status}")
                    print(await response.text())
        
        except Exception as e:
            print(f"❌ Error: {e}")

async def test_model_vision_capability(session, headers, base_url, model_id):
    """Test if a model can handle vision inputs"""
    try:
        # Simple test image (1x1 red pixel)
        test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        
        payload = {
            "model": model_id,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What color is this image?"},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{test_image_b64}"}
                        }
                    ]
                }
            ],
            "max_tokens": 50,
            "temperature": 0.1
        }
        
        timeout = aiohttp.ClientTimeout(total=10)
        async with session.post(
            f"{base_url}/chat/completions",
            json=payload,
            headers=headers,
            timeout=timeout
        ) as response:
            if response.status == 200:
                data = await response.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                print(f"  ✅ Supports vision! Response: {content[:100]}...")
                return True
            else:
                error_text = await response.text()
                if "image" in error_text.lower() or "vision" in error_text.lower():
                    print(f"  ❌ No vision support: {error_text[:100]}...")
                else:
                    print(f"  ❓ Unknown error ({response.status}): {error_text[:100]}...")
                return False
    
    except Exception as e:
        print(f"  ❌ Test failed: {str(e)[:100]}...")
        return False

if __name__ == "__main__":
    asyncio.run(check_groq_models())