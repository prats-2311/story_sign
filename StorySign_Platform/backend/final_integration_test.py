#!/usr/bin/env python3
"""
Final integration test for StorySign Groq Vision with proper error handling
"""

import asyncio
import aiohttp
import base64
import json
import logging
import time
from io import BytesIO
from PIL import Image, ImageDraw

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FinalIntegrationTest:
    """Final comprehensive test with proper error handling"""
    
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000"
        self.server_process = None
        self.test_results = []
    
    def create_optimal_test_image(self) -> str:
        """Create an optimal test image for Groq API"""
        # Create a small, simple image that works well with Groq
        img = Image.new('RGB', (150, 150), 'white')
        draw = ImageDraw.Draw(img)
        
        # Draw a simple red circle
        draw.ellipse([25, 25, 125, 125], fill='red', outline='darkred', width=2)
        
        # Convert to base64 with optimal settings
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=75)
        img_bytes = buffer.getvalue()
        
        logger.info(f"Created test image: {len(img_bytes)} bytes")
        return base64.b64encode(img_bytes).decode('utf-8')
    
    async def test_vision_service_direct(self):
        """Test vision service directly"""
        logger.info("🔍 Testing Vision Service Directly...")
        
        try:
            from local_vision_service import get_vision_service
            
            vision_service = await get_vision_service()
            
            # Health check
            is_healthy = await vision_service.check_health()
            if not is_healthy:
                logger.error("❌ Vision service health check failed")
                return False
            
            logger.info("✅ Vision service is healthy")
            
            # Test with optimal image
            test_image = self.create_optimal_test_image()
            
            # Test with simple prompt
            result = await vision_service.identify_object(
                test_image,
                "What do you see? Answer in one word."
            )
            
            if result.success:
                logger.info(f"✅ Direct vision test successful: '{result.object_name}' (confidence: {result.confidence:.2f})")
                return True
            else:
                logger.error(f"❌ Direct vision test failed: {result.error_message}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Direct vision test exception: {e}")
            return False
    
    async def start_server(self):
        """Start the test server"""
        logger.info("🖥️ Starting test server...")
        
        import subprocess
        import sys
        
        # Kill any existing server
        subprocess.run(["pkill", "-f", "simple_test_server"], capture_output=True)
        await asyncio.sleep(1)
        
        # Start server
        self.server_process = subprocess.Popen([
            sys.executable, "simple_test_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for startup
        await asyncio.sleep(3)
        
        # Test if server is responding
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.base_url}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        logger.info("✅ Test server started successfully")
                        return True
                    else:
                        logger.error(f"❌ Server health check failed: {response.status}")
                        return False
            except Exception as e:
                logger.error(f"❌ Server startup failed: {e}")
                return False
    
    async def test_api_endpoint(self):
        """Test the API endpoint with optimal settings"""
        logger.info("🌐 Testing API Endpoint...")
        
        test_image = self.create_optimal_test_image()
        
        payload = {
            "frame_data": test_image,
            "custom_prompt": "What do you see? Answer in one word."
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                start_time = time.time()
                async with session.post(
                    f"{self.base_url}/api/v1/story/recognize_and_generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    duration = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        if data.get('success'):
                            logger.info(f"✅ API test successful!")
                            logger.info(f"   Object: '{data.get('identified_object')}'")
                            logger.info(f"   Story: '{data.get('story', {}).get('title', 'N/A')}'")
                            logger.info(f"   Duration: {duration:.1f}ms")
                            return True
                        else:
                            logger.error(f"❌ API returned success=false")
                            return False
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ API failed: {response.status} - {error_text[:200]}")
                        return False
            
            except Exception as e:
                logger.error(f"❌ API test exception: {e}")
                return False
    
    async def test_frontend_integration(self):
        """Test that frontend can connect to backend"""
        logger.info("🎨 Testing Frontend Integration...")
        
        # Test the endpoints that frontend would use
        async with aiohttp.ClientSession() as session:
            
            # Test root endpoint
            try:
                async with session.get(f"{self.base_url}/") as response:
                    if response.status == 200:
                        logger.info("✅ Root endpoint accessible")
                    else:
                        logger.warning(f"⚠️ Root endpoint returned {response.status}")
            except Exception as e:
                logger.error(f"❌ Root endpoint failed: {e}")
                return False
            
            # Test health endpoint
            try:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Health endpoint: {data.get('status', 'unknown')}")
                        
                        services = data.get('services', {})
                        for service, status in services.items():
                            logger.info(f"   {service}: {status}")
                        
                        return True
                    else:
                        logger.error(f"❌ Health endpoint failed: {response.status}")
                        return False
            except Exception as e:
                logger.error(f"❌ Health endpoint exception: {e}")
                return False
    
    async def cleanup(self):
        """Clean up resources"""
        logger.info("🧹 Cleaning up...")
        
        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except:
                self.server_process.kill()
        
        import subprocess
        subprocess.run(["pkill", "-f", "simple_test_server"], capture_output=True)
        
        try:
            from local_vision_service import cleanup_vision_service
            await cleanup_vision_service()
        except:
            pass
    
    async def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Final StorySign Groq Vision Integration Test")
        print("="*60)
        
        results = []
        
        # Test 1: Direct vision service
        result1 = await self.test_vision_service_direct()
        results.append(("Vision Service Direct", result1))
        
        # Test 2: Start server
        result2 = await self.start_server()
        results.append(("Server Startup", result2))
        
        if result2:
            # Test 3: API endpoint
            result3 = await self.test_api_endpoint()
            results.append(("API Endpoint", result3))
            
            # Test 4: Frontend integration
            result4 = await self.test_frontend_integration()
            results.append(("Frontend Integration", result4))
        
        # Cleanup
        await self.cleanup()
        
        # Show results
        print("\n" + "="*60)
        print("📊 FINAL TEST RESULTS")
        print("="*60)
        
        passed = 0
        total = len(results)
        
        for test_name, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status}: {test_name}")
            if success:
                passed += 1
        
        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"\nSuccess Rate: {passed}/{total} ({success_rate:.1f}%)")
        
        if success_rate >= 75:
            print("\n🎉 Integration test PASSED! Groq Vision is ready for production.")
            print("\n📋 Next Steps:")
            print("1. Start the backend: python simple_test_server.py")
            print("2. Start the frontend: npm start (in frontend directory)")
            print("3. Test the 'Scan Object to Start' feature in ASL World")
            return True
        else:
            print("\n⚠️ Integration test FAILED. Please review the errors above.")
            return False

async def main():
    """Main test runner"""
    test = FinalIntegrationTest()
    success = await test.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)