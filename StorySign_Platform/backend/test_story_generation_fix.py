#!/usr/bin/env python3
"""
Test script to verify story generation is working with all input methods
"""

import asyncio
import aiohttp
import json
import base64
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
ENDPOINT = "/api/asl-world/story/recognize_and_generate"

async def test_simple_word():
    """Test story generation with simple word"""
    logger.info("Testing story generation with simple word...")
    
    payload = {"simple_word": "cat"}
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{BASE_URL}{ENDPOINT}",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success") and data.get("stories"):
                        logger.info("✅ Simple word test PASSED")
                        logger.info(f"Generated story titles: {[story['title'] for story in data['stories'].values()]}")
                        return True
                    else:
                        logger.error(f"❌ Simple word test FAILED: {data}")
                        return False
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Simple word test FAILED: {response.status} - {error_text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Simple word test FAILED with exception: {e}")
            return False

async def test_custom_prompt():
    """Test story generation with custom prompt"""
    logger.info("Testing story generation with custom prompt...")
    
    payload = {"custom_prompt": "a magical adventure in the forest"}
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{BASE_URL}{ENDPOINT}",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success") and data.get("stories"):
                        logger.info("✅ Custom prompt test PASSED")
                        logger.info(f"Generated story titles: {[story['title'] for story in data['stories'].values()]}")
                        return True
                    else:
                        logger.error(f"❌ Custom prompt test FAILED: {data}")
                        return False
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Custom prompt test FAILED: {response.status} - {error_text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Custom prompt test FAILED with exception: {e}")
            return False

async def test_frame_data():
    """Test story generation with frame data (will use fallback)"""
    logger.info("Testing story generation with frame data...")
    
    # Create a larger dummy base64 image (100x100 pixel PNG with some content)
    # This is a simple 100x100 red square PNG
    dummy_image_b64 = "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
    
    payload = {"frame_data": dummy_image_b64}
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{BASE_URL}{ENDPOINT}",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success") and data.get("stories"):
                        logger.info("✅ Frame data test PASSED (using fallback)")
                        logger.info(f"Generated story titles: {[story['title'] for story in data['stories'].values()]}")
                        return True
                    else:
                        logger.error(f"❌ Frame data test FAILED: {data}")
                        return False
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Frame data test FAILED: {response.status} - {error_text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Frame data test FAILED with exception: {e}")
            return False

async def test_validation_errors():
    """Test that validation errors are handled properly"""
    logger.info("Testing validation error handling...")
    
    # Test empty request
    payload = {}
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{BASE_URL}{ENDPOINT}",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 400:
                    data = await response.json()
                    if "validation_error" in data.get("detail", {}).get("error_type", ""):
                        logger.info("✅ Validation error test PASSED")
                        return True
                    else:
                        logger.error(f"❌ Validation error test FAILED: unexpected error format {data}")
                        return False
                else:
                    logger.error(f"❌ Validation error test FAILED: expected 400, got {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Validation error test FAILED with exception: {e}")
            return False

async def main():
    """Run all tests"""
    logger.info("🧪 Starting story generation API tests...")
    
    tests = [
        ("Simple Word", test_simple_word),
        ("Custom Prompt", test_custom_prompt),
        ("Frame Data", test_frame_data),
        ("Validation Errors", test_validation_errors)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Story generation is working correctly.")
        return True
    else:
        logger.error(f"💥 {total - passed} tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)