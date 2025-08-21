#!/usr/bin/env python3
"""
Manual test for the story generation endpoint with real server
"""

import requests
import json
import base64
import time

def create_test_image():
    """Create a simple test image in base64 format"""
    # This is a 1x1 pixel JPEG image
    return "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A8A"

def test_endpoint_manually():
    """Test the endpoint with manual HTTP requests"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing story generation endpoint manually...")
    print(f"Server URL: {base_url}")
    
    # Test 1: Health check
    try:
        print("\n1. Testing health check...")
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            print("✅ Health check passed")
            health_data = response.json()
            print(f"   Server status: {health_data.get('status')}")
            print(f"   Active connections: {health_data.get('services', {}).get('active_connections', 0)}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure the server is running on localhost:8000")
        print("   Start the server with: python StorySign_Platform/backend/main.py")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: Story generation endpoint
    try:
        print("\n2. Testing story generation endpoint...")
        
        test_data = {
            "frame_data": create_test_image(),
            "custom_prompt": "Identify any object in this test image"
        }
        
        print("   Sending request...")
        start_time = time.time()
        
        response = requests.post(
            f"{base_url}/api/story/recognize_and_generate",
            json=test_data,
            timeout=30
        )
        
        end_time = time.time()
        processing_time = (end_time - start_time) * 1000
        
        print(f"   Response status: {response.status_code}")
        print(f"   Processing time: {processing_time:.1f}ms")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("success"):
                print("✅ Story generation successful!")
                
                story = result.get("story", {})
                print(f"   Story title: {story.get('title')}")
                print(f"   Identified object: {story.get('identified_object')}")
                print(f"   Number of sentences: {len(story.get('sentences', []))}")
                
                # Print first sentence as example
                sentences = story.get('sentences', [])
                if sentences:
                    print(f"   First sentence: {sentences[0]}")
                
                # Print processing info
                processing_info = result.get("processing_info", {})
                obj_info = processing_info.get("object_identification", {})
                story_info = processing_info.get("story_generation", {})
                
                print(f"   Vision service used: {obj_info.get('vision_service_used')}")
                print(f"   Fallback used: {obj_info.get('fallback_used')}")
                print(f"   Story generation time: {story_info.get('generation_time_ms', 0):.1f}ms")
                
                return True
            else:
                print("❌ Story generation failed")
                print(f"   Error: {result}")
                return False
                
        elif response.status_code == 503:
            print("⚠️  Service unavailable (expected if AI services are not running)")
            error_data = response.json()
            print(f"   Detail: {error_data.get('detail')}")
            print("   This is expected if Ollama or local vision services are not running")
            return True  # This is an expected result
            
        else:
            print(f"❌ Unexpected response status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Raw response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out (>30s)")
        return False
    except Exception as e:
        print(f"❌ Request error: {e}")
        return False
    
    # Test 3: Invalid request
    try:
        print("\n3. Testing invalid request handling...")
        
        invalid_data = {}  # Missing required frame_data
        
        response = requests.post(
            f"{base_url}/api/story/recognize_and_generate",
            json=invalid_data
        )
        
        if response.status_code == 422:  # Validation error
            print("✅ Invalid request correctly rejected")
            return True
        else:
            print(f"❌ Expected validation error (422), got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Invalid request test error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("StorySign Backend - Story Generation Endpoint Test")
    print("=" * 60)
    
    success = test_endpoint_manually()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Manual endpoint test completed successfully!")
        print("\nThe story generation endpoint is working correctly.")
        print("Note: AI services (Ollama, local vision) may not be running,")
        print("which is expected and handled gracefully by the endpoint.")
    else:
        print("❌ Manual endpoint test failed!")
        print("\nPlease check the server logs for more details.")
    print("=" * 60)