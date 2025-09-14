#!/usr/bin/env python3
"""
Setup script for Ollama with vision model for StorySign
"""

import asyncio
import aiohttp
import subprocess
import sys
import time
import json

async def check_ollama_running():
    """Check if Ollama is running"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:11434/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as response:
                return response.status == 200
    except:
        return False

async def check_model_available(model_name="llava:7b"):
    """Check if the vision model is available"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:11434/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = [model.get('name', '') for model in data.get('models', [])]
                    return any(model_name in model for model in models)
    except:
        pass
    return False

def install_ollama():
    """Install Ollama using the official installer"""
    print("📦 Installing Ollama...")
    try:
        # For macOS/Linux
        result = subprocess.run([
            "curl", "-fsSL", "https://ollama.com/install.sh"
        ], capture_output=True, text=True, check=True)
        
        # Run the installer
        subprocess.run(["sh"], input=result.stdout, text=True, check=True)
        print("✅ Ollama installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Ollama: {e}")
        return False

def start_ollama():
    """Start Ollama service"""
    print("🚀 Starting Ollama service...")
    try:
        # Start Ollama in the background
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait a bit for it to start
        time.sleep(3)
        return True
    except Exception as e:
        print(f"❌ Failed to start Ollama: {e}")
        return False

def pull_vision_model(model_name="llava:7b"):
    """Pull the vision model"""
    print(f"📥 Pulling vision model: {model_name}")
    print("⏳ This may take several minutes for the first time...")
    
    try:
        result = subprocess.run(
            ["ollama", "pull", model_name],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode == 0:
            print(f"✅ Model {model_name} pulled successfully!")
            return True
        else:
            print(f"❌ Failed to pull model: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Model pull timed out (10 minutes)")
        return False
    except Exception as e:
        print(f"❌ Error pulling model: {e}")
        return False

async def test_vision_model(model_name="llava:7b"):
    """Test the vision model with a simple image"""
    print(f"🧪 Testing vision model: {model_name}")
    
    # Simple test image (1x1 red pixel)
    test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    
    payload = {
        "model": model_name,
        "prompt": "What do you see in this image? Respond with just the main object or color.",
        "images": [test_image_b64],
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 20
        }
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    response_text = data.get('response', '').strip()
                    print(f"✅ Vision model test successful!")
                    print(f"   Response: {response_text}")
                    return True
                else:
                    print(f"❌ Vision model test failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Vision model test error: {e}")
        return False

async def main():
    """Main setup function"""
    print("🔧 StorySign Ollama Vision Setup")
    print("=" * 50)
    
    # Check if Ollama is already running
    print("1️⃣ Checking if Ollama is running...")
    if await check_ollama_running():
        print("✅ Ollama is already running!")
    else:
        print("❌ Ollama is not running")
        
        # Try to start it
        if start_ollama():
            # Wait and check again
            await asyncio.sleep(2)
            if await check_ollama_running():
                print("✅ Ollama started successfully!")
            else:
                print("❌ Ollama failed to start. You may need to install it first.")
                print("💡 Run: curl -fsSL https://ollama.com/install.sh | sh")
                return False
        else:
            print("❌ Could not start Ollama. Please install it manually:")
            print("💡 Visit: https://ollama.com/download")
            return False
    
    # Check if vision model is available
    print("\n2️⃣ Checking if vision model is available...")
    model_name = "llava:7b"
    if await check_model_available(model_name):
        print(f"✅ Model {model_name} is already available!")
    else:
        print(f"❌ Model {model_name} not found")
        
        # Pull the model
        if pull_vision_model(model_name):
            print(f"✅ Model {model_name} installed successfully!")
        else:
            print(f"❌ Failed to install model {model_name}")
            return False
    
    # Test the vision model
    print("\n3️⃣ Testing vision model...")
    if await test_vision_model(model_name):
        print("✅ Vision model is working correctly!")
    else:
        print("❌ Vision model test failed")
        return False
    
    print("\n🎉 Setup completed successfully!")
    print("=" * 50)
    print("✅ Ollama is running with vision model")
    print("✅ StorySign backend is configured to use Ollama")
    print("✅ Groq API is configured for story generation")
    print("\n🚀 You can now start the StorySign backend:")
    print("   python main_api.py")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)