#!/usr/bin/env python3
"""
Simple Integration Test (No OpenCV Dependencies)
Task 11.2: Create integration and performance tests

A simplified integration test that doesn't require OpenCV/NumPy
to verify the test framework structure is correct
"""

import asyncio
import websockets
import json
import logging
import time
import statistics
from datetime import datetime
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleIntegrationTest:
    """Simple integration test without OpenCV dependencies"""
    
    def __init__(self, websocket_url: str = "ws://localhost:8000/ws/video"):
        self.websocket_url = websocket_url
        
    def create_mock_frame_data(self, frame_number: int) -> str:
        """Create mock base64 frame data for testing"""
        # Simple mock JPEG base64 data (minimal valid JPEG)
        mock_jpeg_base64 = "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
        return f"data:image/jpeg;base64,{mock_jpeg_base64}"

    async def test_websocket_connection(self) -> Dict[str, Any]:
        """Test basic WebSocket connection"""
        logger.info("Testing WebSocket connection...")
        
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                # Test connection established
                logger.info("✅ WebSocket connection established")
                
                # Send ping message
                ping_message = {
                    "type": "ping",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await websocket.send(json.dumps(ping_message))
                logger.info("✅ Ping message sent")
                
                return {
                    "success": True,
                    "connection_established": True,
                    "message_sent": True
                }
                
        except (ConnectionRefusedError, OSError) as e:
            logger.warning("⚠️  WebSocket connection refused - server may not be running")
            return {
                "success": False,
                "error": "Connection refused",
                "server_running": False
            }
        except Exception as e:
            logger.error(f"❌ WebSocket connection failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def test_frame_processing_message(self) -> Dict[str, Any]:
        """Test sending frame processing message"""
        logger.info("Testing frame processing message...")
        
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                # Create mock frame message
                frame_data = self.create_mock_frame_data(1)
                message = {
                    "type": "raw_frame",
                    "timestamp": datetime.utcnow().isoformat(),
                    "frame_data": frame_data,
                    "metadata": {
                        "frame_number": 1,
                        "client_id": "simple_test",
                        "test_timestamp": time.time() * 1000
                    }
                }
                
                # Send message and measure response time
                send_time = time.time() * 1000
                await websocket.send(json.dumps(message))
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    receive_time = time.time() * 1000
                    
                    response_data = json.loads(response)
                    latency = receive_time - send_time
                    
                    logger.info(f"✅ Received response in {latency:.1f}ms")
                    logger.info(f"   Response type: {response_data.get('type')}")
                    
                    return {
                        "success": True,
                        "response_received": True,
                        "latency_ms": latency,
                        "response_type": response_data.get("type"),
                        "latency_target_met": latency < 100.0
                    }
                    
                except asyncio.TimeoutError:
                    logger.warning("⚠️  No response received within timeout")
                    return {
                        "success": False,
                        "error": "Response timeout",
                        "message_sent": True
                    }
                    
        except Exception as e:
            logger.error(f"❌ Frame processing test failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def test_multiple_messages(self, num_messages: int = 5) -> Dict[str, Any]:
        """Test sending multiple messages"""
        logger.info(f"Testing {num_messages} consecutive messages...")
        
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                latencies = []
                successful_messages = 0
                
                for i in range(num_messages):
                    frame_data = self.create_mock_frame_data(i + 1)
                    message = {
                        "type": "raw_frame",
                        "timestamp": datetime.utcnow().isoformat(),
                        "frame_data": frame_data,
                        "metadata": {
                            "frame_number": i + 1,
                            "client_id": "simple_multi_test"
                        }
                    }
                    
                    send_time = time.time() * 1000
                    await websocket.send(json.dumps(message))
                    
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        receive_time = time.time() * 1000
                        
                        latency = receive_time - send_time
                        latencies.append(latency)
                        successful_messages += 1
                        
                    except asyncio.TimeoutError:
                        logger.warning(f"Message {i + 1} timed out")
                        continue
                    
                    # Small delay between messages
                    await asyncio.sleep(0.1)
                
                # Calculate statistics
                if latencies:
                    avg_latency = statistics.mean(latencies)
                    max_latency = max(latencies)
                    min_latency = min(latencies)
                    
                    logger.info(f"✅ {successful_messages}/{num_messages} messages successful")
                    logger.info(f"   Average latency: {avg_latency:.1f}ms")
                    logger.info(f"   Latency range: {min_latency:.1f} - {max_latency:.1f}ms")
                    
                    return {
                        "success": successful_messages > 0,
                        "messages_sent": num_messages,
                        "messages_successful": successful_messages,
                        "success_rate": successful_messages / num_messages,
                        "avg_latency_ms": avg_latency,
                        "max_latency_ms": max_latency,
                        "min_latency_ms": min_latency,
                        "all_under_100ms": all(l < 100.0 for l in latencies)
                    }
                else:
                    return {
                        "success": False,
                        "error": "No successful messages",
                        "messages_sent": num_messages
                    }
                    
        except Exception as e:
            logger.error(f"❌ Multiple messages test failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def test_error_handling(self) -> Dict[str, Any]:
        """Test error handling with invalid messages"""
        logger.info("Testing error handling...")
        
        error_tests = {}
        
        try:
            # Test 1: Invalid JSON
            try:
                async with websockets.connect(self.websocket_url) as websocket:
                    await websocket.send("invalid json")
                    
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                        error_tests["invalid_json"] = {
                            "handled": True,
                            "response_received": True
                        }
                    except asyncio.TimeoutError:
                        error_tests["invalid_json"] = {
                            "handled": True,
                            "no_response": True
                        }
            except websockets.ConnectionClosed:
                error_tests["invalid_json"] = {
                    "handled": True,
                    "connection_closed": True
                }
            
            # Test 2: Invalid frame data
            async with websockets.connect(self.websocket_url) as websocket:
                invalid_message = {
                    "type": "raw_frame",
                    "frame_data": "invalid_base64_data",
                    "metadata": {"frame_number": 1}
                }
                
                await websocket.send(json.dumps(invalid_message))
                
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_data = json.loads(response)
                    
                    error_tests["invalid_frame_data"] = {
                        "handled": True,
                        "response_type": response_data.get("type"),
                        "graceful_degradation": True
                    }
                except asyncio.TimeoutError:
                    error_tests["invalid_frame_data"] = {
                        "handled": False,
                        "timeout": True
                    }
            
            # Analyze error handling
            total_tests = len(error_tests)
            handled_tests = sum(1 for test in error_tests.values() if test.get("handled", False))
            
            return {
                "success": True,
                "total_error_tests": total_tests,
                "handled_errors": handled_tests,
                "error_handling_rate": handled_tests / total_tests if total_tests > 0 else 0,
                "detailed_results": error_tests
            }
            
        except Exception as e:
            logger.error(f"❌ Error handling test failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def run_simple_integration_tests(self) -> Dict[str, Any]:
        """Run all simple integration tests"""
        logger.info("🚀 Starting Simple Integration Tests...")
        logger.info("="*60)
        
        test_results = {}
        
        # Test 1: Basic connection
        logger.info("\n1. Testing WebSocket Connection")
        test_results["connection"] = await self.test_websocket_connection()
        
        # Only continue if connection works
        if test_results["connection"].get("success"):
            
            # Test 2: Frame processing
            logger.info("\n2. Testing Frame Processing")
            test_results["frame_processing"] = await self.test_frame_processing_message()
            
            # Test 3: Multiple messages
            logger.info("\n3. Testing Multiple Messages")
            test_results["multiple_messages"] = await self.test_multiple_messages()
            
            # Test 4: Error handling
            logger.info("\n4. Testing Error Handling")
            test_results["error_handling"] = await self.test_error_handling()
        
        else:
            logger.warning("⚠️  Skipping other tests due to connection failure")
        
        # Generate summary
        summary = self._generate_summary(test_results)
        
        return {
            "test_results": test_results,
            "summary": summary
        }

    def _generate_summary(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test summary"""
        total_tests = len(test_results)
        successful_tests = sum(1 for result in test_results.values() if result.get("success", False))
        
        # Check performance
        performance_ok = True
        avg_latency = 0
        
        if test_results.get("frame_processing", {}).get("success"):
            latency = test_results["frame_processing"].get("latency_ms", 0)
            if latency > 100:
                performance_ok = False
            avg_latency = latency
        
        if test_results.get("multiple_messages", {}).get("success"):
            multi_latency = test_results["multiple_messages"].get("avg_latency_ms", 0)
            if multi_latency > 100:
                performance_ok = False
            avg_latency = (avg_latency + multi_latency) / 2 if avg_latency > 0 else multi_latency
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
            "all_tests_passed": successful_tests == total_tests,
            "performance_target_met": performance_ok,
            "avg_latency_ms": avg_latency,
            "server_responsive": test_results.get("connection", {}).get("success", False)
        }

    def print_results(self, results: Dict[str, Any]):
        """Print formatted results"""
        print("\n" + "="*60)
        print("SIMPLE INTEGRATION TEST RESULTS")
        print("="*60)
        
        summary = results.get("summary", {})
        test_results = results.get("test_results", {})
        
        # Overall status
        if summary.get("all_tests_passed") and summary.get("performance_target_met"):
            print("✅ OVERALL STATUS: ALL TESTS PASSED")
        elif summary.get("server_responsive"):
            print("⚠️  OVERALL STATUS: SERVER RESPONSIVE, SOME ISSUES DETECTED")
        else:
            print("❌ OVERALL STATUS: SERVER NOT RESPONSIVE")
        
        # Summary metrics
        print(f"\n📊 SUMMARY:")
        print(f"   Tests Passed:         {summary.get('successful_tests', 0)}/{summary.get('total_tests', 0)}")
        print(f"   Success Rate:         {summary.get('success_rate', 0)*100:.1f}%")
        print(f"   Server Responsive:    {'✅ YES' if summary.get('server_responsive') else '❌ NO'}")
        print(f"   Performance Target:   {'✅ MET' if summary.get('performance_target_met') else '❌ NOT MET'}")
        if summary.get('avg_latency_ms', 0) > 0:
            print(f"   Average Latency:      {summary.get('avg_latency_ms', 0):.1f}ms")
        
        # Detailed results
        print(f"\n📋 DETAILED RESULTS:")
        for test_name, result in test_results.items():
            status = "✅ PASS" if result.get("success") else "❌ FAIL"
            print(f"   {test_name:20}: {status}")
            
            if result.get("success"):
                if "latency_ms" in result:
                    print(f"     └─ Latency: {result['latency_ms']:.1f}ms")
                if "success_rate" in result:
                    print(f"     └─ Success Rate: {result['success_rate']*100:.1f}%")
            else:
                error = result.get("error", "Unknown error")
                print(f"     └─ Error: {error}")
        
        print("="*60)


async def main():
    """Main test execution"""
    tester = SimpleIntegrationTest()
    
    try:
        results = await tester.run_simple_integration_tests()
        tester.print_results(results)
        
        # Save results
        with open("simple_integration_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: simple_integration_test_results.json")
        
        # Return exit code
        summary = results.get("summary", {})
        if summary.get("all_tests_passed"):
            print("🎉 Simple integration tests passed!")
            return 0
        elif summary.get("server_responsive"):
            print("⚠️  Server is responsive but some tests failed.")
            return 1
        else:
            print("❌ Server is not responsive - check if backend is running.")
            return 2
            
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)