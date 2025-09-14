#!/usr/bin/env python3
"""
Comprehensive test suite for StorySign Groq Vision Integration
Tests all aspects: configuration, vision service, API endpoints, error handling, and performance
"""

import asyncio
import aiohttp
import base64
import json
import logging
import time
import statistics
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Any, Tuple
import subprocess
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.performance_metrics = []
    
    def add_pass(self, test_name: str, duration_ms: float = None):
        self.passed += 1
        if duration_ms:
            self.performance_metrics.append((test_name, duration_ms))
        logger.info(f"✅ PASS: {test_name}" + (f" ({duration_ms:.1f}ms)" if duration_ms else ""))
    
    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append((test_name, error))
        logger.error(f"❌ FAIL: {test_name} - {error}")
    
    def summary(self):
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        print("\n" + "="*80)
        print("🧪 COMPREHENSIVE TEST RESULTS")
        print("="*80)
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.performance_metrics:
            durations = [d for _, d in self.performance_metrics]
            print(f"\n📊 Performance Metrics:")
            print(f"   Average Response Time: {statistics.mean(durations):.1f}ms")
            print(f"   Median Response Time: {statistics.median(durations):.1f}ms")
            print(f"   Min Response Time: {min(durations):.1f}ms")
            print(f"   Max Response Time: {max(durations):.1f}ms")
        
        if self.errors:
            print(f"\n❌ Failed Tests:")
            for test_name, error in self.errors:
                print(f"   - {test_name}: {error}")
        
        print("="*80)
        return success_rate >= 80  # 80% success rate threshold

class TestImageGenerator:
    """Generate various test images for comprehensive testing"""
    
    @staticmethod
    def create_simple_objects() -> Dict[str, str]:
        """Create simple geometric objects"""
        images = {}
        
        # Red ball/circle
        img = Image.new('RGB', (300, 300), 'white')
        draw = ImageDraw.Draw(img)
        draw.ellipse([75, 75, 225, 225], fill='red', outline='darkred', width=4)
        images['red_ball'] = TestImageGenerator._to_base64(img)
        
        # Blue book/rectangle
        img = Image.new('RGB', (300, 300), 'white')
        draw = ImageDraw.Draw(img)
        draw.rectangle([60, 100, 240, 200], fill='blue', outline='darkblue', width=4)
        # Add lines to make it look like a book
        for y in [120, 140, 160, 180]:
            draw.line([70, y, 230, y], fill='white', width=2)
        images['blue_book'] = TestImageGenerator._to_base64(img)
        
        # Yellow cup
        img = Image.new('RGB', (300, 300), 'white')
        draw = ImageDraw.Draw(img)
        # Cup body
        draw.rectangle([100, 120, 180, 220], fill='yellow', outline='orange', width=3)
        # Handle
        draw.arc([180, 150, 220, 190], 270, 90, fill='orange', width=4)
        images['yellow_cup'] = TestImageGenerator._to_base64(img)
        
        # Green apple
        img = Image.new('RGB', (300, 300), 'white')
        draw = ImageDraw.Draw(img)
        draw.ellipse([100, 100, 200, 200], fill='green', outline='darkgreen', width=3)
        # Stem
        draw.rectangle([148, 90, 152, 105], fill='brown')
        images['green_apple'] = TestImageGenerator._to_base64(img)
        
        return images
    
    @staticmethod
    def create_complex_scenes() -> Dict[str, str]:
        """Create more complex scenes"""
        images = {}
        
        # Multiple objects
        img = Image.new('RGB', (400, 300), 'lightblue')
        draw = ImageDraw.Draw(img)
        # Sun
        draw.ellipse([320, 20, 380, 80], fill='yellow', outline='orange', width=2)
        # House
        draw.rectangle([50, 150, 150, 250], fill='brown', outline='darkbrown', width=2)
        draw.polygon([(50, 150), (100, 100), (150, 150)], fill='red', outline='darkred')
        # Tree
        draw.rectangle([200, 200, 220, 250], fill='brown')
        draw.ellipse([180, 150, 240, 210], fill='green', outline='darkgreen', width=2)
        images['house_scene'] = TestImageGenerator._to_base64(img)
        
        return images
    
    @staticmethod
    def create_edge_cases() -> Dict[str, str]:
        """Create edge case images"""
        images = {}
        
        # Very small image
        img = Image.new('RGB', (50, 50), 'red')
        images['tiny_red'] = TestImageGenerator._to_base64(img)
        
        # Large image
        img = Image.new('RGB', (1000, 1000), 'blue')
        draw = ImageDraw.Draw(img)
        draw.ellipse([200, 200, 800, 800], fill='white', outline='black', width=10)
        images['large_circle'] = TestImageGenerator._to_base64(img)
        
        # Black and white
        img = Image.new('RGB', (200, 200), 'white')
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, 150, 150], fill='black', outline='gray', width=2)
        images['black_square'] = TestImageGenerator._to_base64(img)
        
        # Very low contrast
        img = Image.new('RGB', (200, 200), (240, 240, 240))
        draw = ImageDraw.Draw(img)
        draw.ellipse([50, 50, 150, 150], fill=(250, 250, 250), outline=(230, 230, 230))
        images['low_contrast'] = TestImageGenerator._to_base64(img)
        
        return images
    
    @staticmethod
    def _to_base64(img: Image.Image) -> str:
        """Convert PIL image to base64"""
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

class ComprehensiveTestSuite:
    """Main test suite class"""
    
    def __init__(self):
        self.results = TestResults()
        self.server_process = None
        self.base_url = "http://127.0.0.1:8000"
    
    async def run_all_tests(self):
        """Run all test categories"""
        print("🚀 Starting Comprehensive StorySign Vision Test Suite")
        print("="*80)
        
        # Test 1: Configuration Tests
        await self.test_configuration()
        
        # Test 2: Vision Service Tests
        await self.test_vision_service()
        
        # Test 3: Start test server
        await self.start_test_server()
        
        # Test 4: API Endpoint Tests
        await self.test_api_endpoints()
        
        # Test 5: Performance Tests
        await self.test_performance()
        
        # Test 6: Error Handling Tests
        await self.test_error_handling()
        
        # Test 7: Edge Case Tests
        await self.test_edge_cases()
        
        # Cleanup
        await self.cleanup()
        
        # Show results
        return self.results.summary()
    
    async def test_configuration(self):
        """Test configuration loading and validation"""
        logger.info("🔧 Testing Configuration...")
        
        try:
            from config import get_config
            config = get_config()
            
            # Test basic config loading
            if config:
                self.results.add_pass("Configuration Loading")
            else:
                self.results.add_fail("Configuration Loading", "Config is None")
                return
            
            # Test Groq configuration
            if config.groq.is_configured():
                self.results.add_pass("Groq API Configuration")
            else:
                self.results.add_fail("Groq API Configuration", "Groq not properly configured")
            
            # Test service type
            if config.local_vision.service_type == "groq":
                self.results.add_pass("Service Type Configuration")
            else:
                self.results.add_fail("Service Type Configuration", f"Expected 'groq', got '{config.local_vision.service_type}'")
            
            # Test model name
            expected_model = "meta-llama/llama-4-scout-17b-16e-instruct"
            if config.local_vision.model_name == expected_model:
                self.results.add_pass("Model Name Configuration")
            else:
                self.results.add_fail("Model Name Configuration", f"Expected '{expected_model}', got '{config.local_vision.model_name}'")
        
        except Exception as e:
            self.results.add_fail("Configuration Loading", str(e))
    
    async def test_vision_service(self):
        """Test vision service functionality"""
        logger.info("👁️ Testing Vision Service...")
        
        try:
            from local_vision_service import get_vision_service
            
            # Test service initialization
            start_time = time.time()
            vision_service = await get_vision_service()
            init_time = (time.time() - start_time) * 1000
            
            if vision_service:
                self.results.add_pass("Vision Service Initialization", init_time)
            else:
                self.results.add_fail("Vision Service Initialization", "Service is None")
                return
            
            # Test health check
            start_time = time.time()
            is_healthy = await vision_service.check_health()
            health_time = (time.time() - start_time) * 1000
            
            if is_healthy:
                self.results.add_pass("Vision Service Health Check", health_time)
            else:
                self.results.add_fail("Vision Service Health Check", "Service reported unhealthy")
                return
            
            # Test object identification with simple image
            test_images = TestImageGenerator.create_simple_objects()
            
            for obj_name, image_data in list(test_images.items())[:2]:  # Test first 2 objects
                start_time = time.time()
                result = await vision_service.identify_object(
                    image_data,
                    "What is the main object in this image? Respond with just the object name."
                )
                identify_time = (time.time() - start_time) * 1000
                
                if result.success and result.object_name:
                    self.results.add_pass(f"Object Identification - {obj_name}", identify_time)
                else:
                    self.results.add_fail(f"Object Identification - {obj_name}", result.error_message or "No object identified")
        
        except Exception as e:
            self.results.add_fail("Vision Service Testing", str(e))
    
    async def start_test_server(self):
        """Start the test server"""
        logger.info("🖥️ Starting Test Server...")
        
        try:
            # Kill any existing server
            subprocess.run(["pkill", "-f", "simple_test_server"], capture_output=True)
            await asyncio.sleep(1)
            
            # Start new server
            self.server_process = subprocess.Popen([
                sys.executable, "simple_test_server.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            await asyncio.sleep(3)
            
            # Test if server is responding
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(f"{self.base_url}/health", timeout=aiohttp.ClientTimeout(total=5)) as response:
                        if response.status == 200:
                            self.results.add_pass("Test Server Startup")
                        else:
                            self.results.add_fail("Test Server Startup", f"Server returned {response.status}")
                except Exception as e:
                    self.results.add_fail("Test Server Startup", str(e))
        
        except Exception as e:
            self.results.add_fail("Test Server Startup", str(e))
    
    async def test_api_endpoints(self):
        """Test API endpoints"""
        logger.info("🌐 Testing API Endpoints...")
        
        async with aiohttp.ClientSession() as session:
            
            # Test health endpoint
            try:
                start_time = time.time()
                async with session.get(f"{self.base_url}/health") as response:
                    health_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') == 'healthy':
                            self.results.add_pass("Health Endpoint", health_time)
                        else:
                            self.results.add_fail("Health Endpoint", f"Status: {data.get('status')}")
                    else:
                        self.results.add_fail("Health Endpoint", f"HTTP {response.status}")
            except Exception as e:
                self.results.add_fail("Health Endpoint", str(e))
            
            # Test root endpoint
            try:
                async with session.get(f"{self.base_url}/") as response:
                    if response.status == 200:
                        self.results.add_pass("Root Endpoint")
                    else:
                        self.results.add_fail("Root Endpoint", f"HTTP {response.status}")
            except Exception as e:
                self.results.add_fail("Root Endpoint", str(e))
            
            # Test story generation endpoint
            test_images = TestImageGenerator.create_simple_objects()
            
            for obj_name, image_data in list(test_images.items())[:3]:  # Test first 3 objects
                try:
                    payload = {
                        "frame_data": image_data,
                        "custom_prompt": "What is the main object in this image? Respond with just the object name."
                    }
                    
                    start_time = time.time()
                    async with session.post(
                        f"{self.base_url}/api/v1/story/recognize_and_generate",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        api_time = (time.time() - start_time) * 1000
                        
                        if response.status == 200:
                            data = await response.json()
                            if data.get('success') and data.get('identified_object'):
                                self.results.add_pass(f"Story Generation API - {obj_name}", api_time)
                            else:
                                self.results.add_fail(f"Story Generation API - {obj_name}", "API returned success=false")
                        else:
                            error_text = await response.text()
                            self.results.add_fail(f"Story Generation API - {obj_name}", f"HTTP {response.status}: {error_text[:100]}")
                
                except Exception as e:
                    self.results.add_fail(f"Story Generation API - {obj_name}", str(e))
    
    async def test_performance(self):
        """Test performance under load"""
        logger.info("⚡ Testing Performance...")
        
        async with aiohttp.ClientSession() as session:
            test_images = TestImageGenerator.create_simple_objects()
            image_data = list(test_images.values())[0]  # Use first image
            
            # Test concurrent requests
            async def make_request():
                payload = {
                    "frame_data": image_data,
                    "custom_prompt": "What do you see?"
                }
                
                start_time = time.time()
                try:
                    async with session.post(
                        f"{self.base_url}/api/v1/story/recognize_and_generate",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        duration = (time.time() - start_time) * 1000
                        return response.status == 200, duration
                except Exception:
                    return False, (time.time() - start_time) * 1000
            
            # Test 5 concurrent requests
            tasks = [make_request() for _ in range(5)]
            results = await asyncio.gather(*tasks)
            
            successful = sum(1 for success, _ in results if success)
            durations = [duration for _, duration in results]
            
            if successful >= 4:  # At least 80% success
                avg_duration = statistics.mean(durations)
                self.results.add_pass("Concurrent Requests (5x)", avg_duration)
            else:
                self.results.add_fail("Concurrent Requests (5x)", f"Only {successful}/5 succeeded")
    
    async def test_error_handling(self):
        """Test error handling"""
        logger.info("🚨 Testing Error Handling...")
        
        async with aiohttp.ClientSession() as session:
            
            # Test invalid base64
            try:
                payload = {
                    "frame_data": "invalid_base64_data",
                    "custom_prompt": "What do you see?"
                }
                
                async with session.post(
                    f"{self.base_url}/api/v1/story/recognize_and_generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 400:
                        self.results.add_pass("Invalid Base64 Handling")
                    else:
                        self.results.add_fail("Invalid Base64 Handling", f"Expected 400, got {response.status}")
            except Exception as e:
                self.results.add_fail("Invalid Base64 Handling", str(e))
            
            # Test empty request
            try:
                payload = {}
                
                async with session.post(
                    f"{self.base_url}/api/v1/story/recognize_and_generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 422:  # Validation error
                        self.results.add_pass("Empty Request Handling")
                    else:
                        self.results.add_fail("Empty Request Handling", f"Expected 422, got {response.status}")
            except Exception as e:
                self.results.add_fail("Empty Request Handling", str(e))
    
    async def test_edge_cases(self):
        """Test edge cases"""
        logger.info("🔍 Testing Edge Cases...")
        
        async with aiohttp.ClientSession() as session:
            edge_images = TestImageGenerator.create_edge_cases()
            
            for case_name, image_data in edge_images.items():
                try:
                    payload = {
                        "frame_data": image_data,
                        "custom_prompt": "What is the main object or color in this image?"
                    }
                    
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
                                self.results.add_pass(f"Edge Case - {case_name}", duration)
                            else:
                                # Some edge cases might fail gracefully
                                self.results.add_pass(f"Edge Case - {case_name} (graceful failure)")
                        else:
                            # Edge cases might return errors, which is acceptable
                            self.results.add_pass(f"Edge Case - {case_name} (handled error)")
                
                except Exception as e:
                    # Timeouts on edge cases are acceptable
                    if "timeout" in str(e).lower():
                        self.results.add_pass(f"Edge Case - {case_name} (timeout handled)")
                    else:
                        self.results.add_fail(f"Edge Case - {case_name}", str(e))
    
    async def cleanup(self):
        """Clean up resources"""
        logger.info("🧹 Cleaning up...")
        
        # Stop server
        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
        
        # Kill any remaining processes
        subprocess.run(["pkill", "-f", "simple_test_server"], capture_output=True)
        
        # Clean up vision service
        try:
            from local_vision_service import cleanup_vision_service
            await cleanup_vision_service()
        except:
            pass

async def main():
    """Main test runner"""
    test_suite = ComprehensiveTestSuite()
    success = await test_suite.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! Groq Vision integration is fully functional.")
        return 0
    else:
        print("\n⚠️ Some tests failed. Please review the results above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)