#!/usr/bin/env python3
"""
Integration and Performance Tests for StorySign ASL Platform
Task 11.2: Create integration and performance tests

This test suite covers:
- End-to-end WebSocket communication tests
- Video pipeline latency and quality metric validation
- Error scenario simulation and recovery testing
- Multi-client connection handling and isolation tests
- Performance benchmarks for <100ms end-to-end processing target
"""

import asyncio
import websockets
import json
import base64
import cv2
import numpy as np
import logging
import time
import statistics
from datetime import datetime
from typing import Dict, List, Any, Optional
import concurrent.futures
import threading
import pytest
import psutil
import gc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntegrationPerformanceTestSuite:
    """Comprehensive integration and performance test suite"""
    
    def __init__(self, websocket_url: str = "ws://localhost:8000/ws/video"):
        self.websocket_url = websocket_url
        self.test_results = {}
        self.performance_metrics = {}
        
    def create_test_frame(self, frame_number: int, width: int = 240, height: int = 180) -> str:
        """Create a test frame with identifiable content"""
        # Create test image with frame number and timestamp
        img = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Add visual elements for MediaPipe detection
        cv2.circle(img, (width//2, height//2), 30, (255, 100, 100), -1)  # Red circle
        cv2.rectangle(img, (20, 20), (width-20, height-20), (100, 255, 100), 2)  # Green border
        
        # Add frame info
        cv2.putText(img, f"Frame {frame_number}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(img, f"{int(time.time() * 1000)}", (10, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # Encode as JPEG
        _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 80])
        base64_data = base64.b64encode(buffer).decode('utf-8')
        
        return f"data:image/jpeg;base64,{base64_data}"

    async def test_websocket_connection_establishment(self) -> Dict[str, Any]:
        """Test WebSocket connection establishment and basic communication"""
        logger.info("Testing WebSocket connection establishment...")
        
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                # Test connection is established
                assert websocket.open, "WebSocket connection should be open"
                
                # Test basic message exchange
                test_message = {
                    "type": "ping",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await websocket.send(json.dumps(test_message))
                
                # Wait for any response (or timeout)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    response_data = json.loads(response)
                except asyncio.TimeoutError:
                    # No response expected for ping, this is normal
                    response_data = None
                
                return {
                    "success": True,
                    "connection_established": True,
                    "message_sent": True,
                    "response_received": response_data is not None
                }
                
        except Exception as e:
            logger.error(f"WebSocket connection test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "connection_established": False
            }

    async def test_end_to_end_frame_processing(self) -> Dict[str, Any]:
        """Test complete end-to-end frame processing pipeline"""
        logger.info("Testing end-to-end frame processing...")
        
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                # Create test frame
                frame_data = self.create_test_frame(1)
                
                # Send frame processing message
                message = {
                    "type": "raw_frame",
                    "timestamp": datetime.utcnow().isoformat(),
                    "frame_data": frame_data,
                    "metadata": {
                        "frame_number": 1,
                        "client_id": "integration_test",
                        "test_timestamp": time.time() * 1000
                    }
                }
                
                # Measure end-to-end latency
                send_time = time.time() * 1000
                await websocket.send(json.dumps(message))
                
                # Wait for processed frame response
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                receive_time = time.time() * 1000
                
                # Parse response
                response_data = json.loads(response)
                
                # Calculate metrics
                end_to_end_latency = receive_time - send_time
                
                # Validate response structure
                assert response_data.get("type") == "processed_frame", "Should receive processed_frame"
                assert "frame_data" in response_data, "Response should contain frame_data"
                assert "metadata" in response_data, "Response should contain metadata"
                
                metadata = response_data["metadata"]
                processing_time = metadata.get("processing_time_ms", 0)
                landmarks_detected = metadata.get("landmarks_detected", {})
                
                return {
                    "success": True,
                    "end_to_end_latency_ms": end_to_end_latency,
                    "processing_time_ms": processing_time,
                    "landmarks_detected": landmarks_detected,
                    "response_type": response_data.get("type"),
                    "frame_processed": True,
                    "latency_target_met": end_to_end_latency < 100.0
                }
                
        except Exception as e:
            logger.error(f"End-to-end processing test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "frame_processed": False
            }

    async def test_video_pipeline_latency_validation(self, num_frames: int = 50) -> Dict[str, Any]:
        """Test video pipeline latency over multiple frames"""
        logger.info(f"Testing video pipeline latency over {num_frames} frames...")
        
        latencies = []
        processing_times = []
        successful_frames = 0
        
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                for frame_num in range(1, num_frames + 1):
                    try:
                        # Create and send frame
                        frame_data = self.create_test_frame(frame_num)
                        message = {
                            "type": "raw_frame",
                            "timestamp": datetime.utcnow().isoformat(),
                            "frame_data": frame_data,
                            "metadata": {
                                "frame_number": frame_num,
                                "client_id": "latency_test",
                                "test_timestamp": time.time() * 1000
                            }
                        }
                        
                        send_time = time.time() * 1000
                        await websocket.send(json.dumps(message))
                        
                        # Wait for response
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        receive_time = time.time() * 1000
                        
                        response_data = json.loads(response)
                        
                        if response_data.get("type") == "processed_frame":
                            latency = receive_time - send_time
                            processing_time = response_data.get("metadata", {}).get("processing_time_ms", 0)
                            
                            latencies.append(latency)
                            processing_times.append(processing_time)
                            successful_frames += 1
                        
                        # Small delay between frames
                        await asyncio.sleep(0.05)  # 20 FPS
                        
                    except asyncio.TimeoutError:
                        logger.warning(f"Frame {frame_num} timed out")
                        continue
                    except Exception as e:
                        logger.warning(f"Frame {frame_num} failed: {e}")
                        continue
                
                # Calculate statistics
                if latencies:
                    avg_latency = statistics.mean(latencies)
                    median_latency = statistics.median(latencies)
                    max_latency = max(latencies)
                    min_latency = min(latencies)
                    std_latency = statistics.stdev(latencies) if len(latencies) > 1 else 0
                    
                    avg_processing = statistics.mean(processing_times)
                    
                    # Check performance targets
                    frames_under_100ms = sum(1 for l in latencies if l < 100.0)
                    target_compliance = frames_under_100ms / len(latencies)
                    
                    return {
                        "success": True,
                        "total_frames": num_frames,
                        "successful_frames": successful_frames,
                        "success_rate": successful_frames / num_frames,
                        "avg_latency_ms": avg_latency,
                        "median_latency_ms": median_latency,
                        "min_latency_ms": min_latency,
                        "max_latency_ms": max_latency,
                        "std_latency_ms": std_latency,
                        "avg_processing_time_ms": avg_processing,
                        "target_compliance_rate": target_compliance,
                        "target_met": target_compliance > 0.9,  # 90% of frames under 100ms
                        "detailed_latencies": latencies[:10]  # First 10 for analysis
                    }
                else:
                    return {
                        "success": False,
                        "error": "No successful frame processing",
                        "total_frames": num_frames,
                        "successful_frames": 0
                    }
                    
        except Exception as e:
            logger.error(f"Latency validation test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_frames": num_frames,
                "successful_frames": successful_frames
            }

    async def test_multi_client_isolation(self, num_clients: int = 3) -> Dict[str, Any]:
        """Test multi-client connection handling and isolation"""
        logger.info(f"Testing multi-client isolation with {num_clients} clients...")
        
        client_results = {}
        
        async def client_session(client_id: int):
            """Individual client session"""
            try:
                async with websockets.connect(self.websocket_url) as websocket:
                    frames_processed = 0
                    latencies = []
                    
                    # Process 10 frames per client
                    for frame_num in range(1, 11):
                        frame_data = self.create_test_frame(frame_num)
                        message = {
                            "type": "raw_frame",
                            "timestamp": datetime.utcnow().isoformat(),
                            "frame_data": frame_data,
                            "metadata": {
                                "frame_number": frame_num,
                                "client_id": f"client_{client_id}",
                                "test_timestamp": time.time() * 1000
                            }
                        }
                        
                        send_time = time.time() * 1000
                        await websocket.send(json.dumps(message))
                        
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                            receive_time = time.time() * 1000
                            
                            response_data = json.loads(response)
                            if response_data.get("type") == "processed_frame":
                                latency = receive_time - send_time
                                latencies.append(latency)
                                frames_processed += 1
                                
                        except asyncio.TimeoutError:
                            continue
                        
                        await asyncio.sleep(0.1)  # 10 FPS per client
                    
                    return {
                        "client_id": client_id,
                        "frames_processed": frames_processed,
                        "avg_latency_ms": statistics.mean(latencies) if latencies else 0,
                        "success": frames_processed > 0
                    }
                    
            except Exception as e:
                logger.error(f"Client {client_id} failed: {e}")
                return {
                    "client_id": client_id,
                    "frames_processed": 0,
                    "error": str(e),
                    "success": False
                }
        
        try:
            # Run multiple clients concurrently
            tasks = [client_session(i) for i in range(num_clients)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Analyze results
            successful_clients = 0
            total_frames = 0
            all_latencies = []
            
            for result in results:
                if isinstance(result, dict) and result.get("success"):
                    successful_clients += 1
                    total_frames += result.get("frames_processed", 0)
                    if result.get("avg_latency_ms", 0) > 0:
                        all_latencies.append(result["avg_latency_ms"])
                
                client_results[f"client_{result.get('client_id', 'unknown')}"] = result
            
            # Check isolation (no client should significantly impact others)
            isolation_good = True
            if all_latencies:
                max_latency = max(all_latencies)
                min_latency = min(all_latencies)
                latency_variance = max_latency - min_latency
                # If variance is too high, isolation might be poor
                if latency_variance > 50.0:  # 50ms variance threshold
                    isolation_good = False
            
            return {
                "success": successful_clients > 0,
                "num_clients": num_clients,
                "successful_clients": successful_clients,
                "total_frames_processed": total_frames,
                "avg_latency_across_clients": statistics.mean(all_latencies) if all_latencies else 0,
                "latency_variance": max(all_latencies) - min(all_latencies) if len(all_latencies) > 1 else 0,
                "isolation_quality": "good" if isolation_good else "poor",
                "client_results": client_results
            }
            
        except Exception as e:
            logger.error(f"Multi-client test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "num_clients": num_clients,
                "successful_clients": 0
            }

    async def test_error_scenario_simulation(self) -> Dict[str, Any]:
        """Test error scenarios and recovery mechanisms"""
        logger.info("Testing error scenarios and recovery...")
        
        error_tests = {}
        
        try:
            # Test 1: Invalid frame data
            async with websockets.connect(self.websocket_url) as websocket:
                invalid_message = {
                    "type": "raw_frame",
                    "timestamp": datetime.utcnow().isoformat(),
                    "frame_data": "invalid_base64_data",
                    "metadata": {"frame_number": 1, "client_id": "error_test"}
                }
                
                await websocket.send(json.dumps(invalid_message))
                
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_data = json.loads(response)
                    
                    # Should receive error response or fallback processing
                    error_tests["invalid_frame_data"] = {
                        "error_handled": True,
                        "response_type": response_data.get("type"),
                        "graceful_degradation": response_data.get("type") in ["error", "processed_frame"]
                    }
                except asyncio.TimeoutError:
                    error_tests["invalid_frame_data"] = {
                        "error_handled": False,
                        "timeout": True
                    }
            
            # Test 2: Malformed JSON
            try:
                async with websockets.connect(self.websocket_url) as websocket:
                    await websocket.send("invalid json data")
                    
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                        error_tests["malformed_json"] = {
                            "error_handled": True,
                            "connection_maintained": True
                        }
                    except asyncio.TimeoutError:
                        error_tests["malformed_json"] = {
                            "error_handled": False,
                            "timeout": True
                        }
            except websockets.exceptions.ConnectionClosed:
                error_tests["malformed_json"] = {
                    "error_handled": True,
                    "connection_closed": True
                }
            
            # Test 3: Connection recovery after disconnect
            websocket_conn = None
            try:
                websocket_conn = await websockets.connect(self.websocket_url)
                await websocket_conn.close()
                
                # Try to reconnect
                await asyncio.sleep(1.0)
                websocket_conn = await websockets.connect(self.websocket_url)
                
                # Send test frame after reconnection
                frame_data = self.create_test_frame(1)
                message = {
                    "type": "raw_frame",
                    "timestamp": datetime.utcnow().isoformat(),
                    "frame_data": frame_data,
                    "metadata": {"frame_number": 1, "client_id": "recovery_test"}
                }
                
                await websocket_conn.send(json.dumps(message))
                response = await asyncio.wait_for(websocket_conn.recv(), timeout=5.0)
                
                error_tests["connection_recovery"] = {
                    "reconnection_successful": True,
                    "processing_after_reconnect": True
                }
                
                await websocket_conn.close()
                
            except Exception as e:
                error_tests["connection_recovery"] = {
                    "reconnection_successful": False,
                    "error": str(e)
                }
                if websocket_conn:
                    await websocket_conn.close()
            
            # Analyze error handling quality
            total_tests = len(error_tests)
            successful_handling = sum(1 for test in error_tests.values() 
                                    if test.get("error_handled") or test.get("reconnection_successful"))
            
            return {
                "success": True,
                "total_error_tests": total_tests,
                "successful_error_handling": successful_handling,
                "error_handling_rate": successful_handling / total_tests if total_tests > 0 else 0,
                "detailed_results": error_tests,
                "recovery_mechanisms_working": error_tests.get("connection_recovery", {}).get("reconnection_successful", False)
            }
            
        except Exception as e:
            logger.error(f"Error scenario testing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_tests_completed": len(error_tests)
            }

    async def test_performance_benchmarks(self) -> Dict[str, Any]:
        """Test performance benchmarks for <100ms target"""
        logger.info("Running performance benchmarks...")
        
        benchmark_results = {}
        
        try:
            # Benchmark 1: Single frame latency (best case)
            single_frame_latencies = []
            for i in range(10):
                async with websockets.connect(self.websocket_url) as websocket:
                    frame_data = self.create_test_frame(i + 1)
                    message = {
                        "type": "raw_frame",
                        "timestamp": datetime.utcnow().isoformat(),
                        "frame_data": frame_data,
                        "metadata": {"frame_number": i + 1, "client_id": "benchmark_single"}
                    }
                    
                    send_time = time.time() * 1000
                    await websocket.send(json.dumps(message))
                    
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        receive_time = time.time() * 1000
                        latency = receive_time - send_time
                        single_frame_latencies.append(latency)
                    except asyncio.TimeoutError:
                        continue
                
                await asyncio.sleep(0.5)  # Cool down between tests
            
            if single_frame_latencies:
                benchmark_results["single_frame"] = {
                    "avg_latency_ms": statistics.mean(single_frame_latencies),
                    "min_latency_ms": min(single_frame_latencies),
                    "max_latency_ms": max(single_frame_latencies),
                    "target_met": all(l < 100.0 for l in single_frame_latencies),
                    "samples": len(single_frame_latencies)
                }
            
            # Benchmark 2: Sustained throughput test
            async with websockets.connect(self.websocket_url) as websocket:
                sustained_latencies = []
                frames_sent = 0
                frames_received = 0
                
                # Send frames at 30 FPS for 10 seconds
                start_time = time.time()
                frame_interval = 1.0 / 30.0  # 30 FPS
                
                while time.time() - start_time < 10.0:
                    frames_sent += 1
                    frame_data = self.create_test_frame(frames_sent)
                    message = {
                        "type": "raw_frame",
                        "timestamp": datetime.utcnow().isoformat(),
                        "frame_data": frame_data,
                        "metadata": {"frame_number": frames_sent, "client_id": "benchmark_sustained"}
                    }
                    
                    send_time = time.time() * 1000
                    await websocket.send(json.dumps(message))
                    
                    # Try to receive response (non-blocking)
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=0.01)
                        receive_time = time.time() * 1000
                        latency = receive_time - send_time
                        sustained_latencies.append(latency)
                        frames_received += 1
                    except asyncio.TimeoutError:
                        pass
                    
                    await asyncio.sleep(frame_interval)
                
                # Collect remaining responses
                remaining_timeout = 2.0
                while remaining_timeout > 0 and frames_received < frames_sent:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                        frames_received += 1
                        remaining_timeout -= 0.1
                    except asyncio.TimeoutError:
                        remaining_timeout -= 0.1
                
                if sustained_latencies:
                    benchmark_results["sustained_throughput"] = {
                        "frames_sent": frames_sent,
                        "frames_received": frames_received,
                        "throughput_fps": frames_received / 10.0,
                        "avg_latency_ms": statistics.mean(sustained_latencies),
                        "target_fps_met": (frames_received / 10.0) >= 25.0,  # At least 25 FPS
                        "latency_target_met": statistics.mean(sustained_latencies) < 100.0
                    }
            
            # Overall benchmark assessment
            single_target_met = benchmark_results.get("single_frame", {}).get("target_met", False)
            sustained_target_met = benchmark_results.get("sustained_throughput", {}).get("latency_target_met", False)
            
            return {
                "success": True,
                "overall_target_met": single_target_met and sustained_target_met,
                "benchmark_results": benchmark_results,
                "performance_grade": "excellent" if single_target_met and sustained_target_met else "needs_improvement"
            }
            
        except Exception as e:
            logger.error(f"Performance benchmark failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "benchmark_results": benchmark_results
            }

    async def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run all integration and performance tests"""
        logger.info("Starting comprehensive integration and performance test suite...")
        
        test_suite_results = {
            "test_timestamp": datetime.utcnow().isoformat(),
            "tests": {}
        }
        
        # Test 1: WebSocket Connection
        logger.info("Running Test 1: WebSocket Connection Establishment")
        test_suite_results["tests"]["websocket_connection"] = await self.test_websocket_connection_establishment()
        
        # Test 2: End-to-End Processing
        logger.info("Running Test 2: End-to-End Frame Processing")
        test_suite_results["tests"]["end_to_end_processing"] = await self.test_end_to_end_frame_processing()
        
        # Test 3: Latency Validation
        logger.info("Running Test 3: Video Pipeline Latency Validation")
        test_suite_results["tests"]["latency_validation"] = await self.test_video_pipeline_latency_validation()
        
        # Test 4: Multi-Client Isolation
        logger.info("Running Test 4: Multi-Client Connection Handling")
        test_suite_results["tests"]["multi_client_isolation"] = await self.test_multi_client_isolation()
        
        # Test 5: Error Scenarios
        logger.info("Running Test 5: Error Scenario Simulation")
        test_suite_results["tests"]["error_scenarios"] = await self.test_error_scenario_simulation()
        
        # Test 6: Performance Benchmarks
        logger.info("Running Test 6: Performance Benchmarks")
        test_suite_results["tests"]["performance_benchmarks"] = await self.test_performance_benchmarks()
        
        # Generate summary
        test_suite_results["summary"] = self._generate_test_summary(test_suite_results["tests"])
        
        return test_suite_results

    def _generate_test_summary(self, tests: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive test summary"""
        summary = {
            "overall_success": True,
            "tests_passed": 0,
            "tests_failed": 0,
            "performance_targets_met": False,
            "integration_quality": "unknown",
            "issues": [],
            "recommendations": []
        }
        
        # Analyze each test
        for test_name, result in tests.items():
            if result.get("success", False):
                summary["tests_passed"] += 1
            else:
                summary["tests_failed"] += 1
                summary["overall_success"] = False
                summary["issues"].append(f"{test_name} failed: {result.get('error', 'Unknown error')}")
        
        # Check performance targets
        latency_test = tests.get("latency_validation", {})
        benchmark_test = tests.get("performance_benchmarks", {})
        
        latency_target_met = latency_test.get("target_met", False)
        benchmark_target_met = benchmark_test.get("overall_target_met", False)
        
        summary["performance_targets_met"] = latency_target_met and benchmark_target_met
        
        if not summary["performance_targets_met"]:
            if not latency_target_met:
                avg_latency = latency_test.get("avg_latency_ms", 0)
                summary["issues"].append(f"Latency target not met: {avg_latency:.1f}ms average (target: <100ms)")
                summary["recommendations"].append("Optimize MediaPipe processing or reduce frame resolution")
            
            if not benchmark_target_met:
                summary["issues"].append("Performance benchmarks not met")
                summary["recommendations"].append("Review system resources and processing efficiency")
        
        # Check integration quality
        connection_ok = tests.get("websocket_connection", {}).get("success", False)
        processing_ok = tests.get("end_to_end_processing", {}).get("success", False)
        multi_client_ok = tests.get("multi_client_isolation", {}).get("success", False)
        error_handling_ok = tests.get("error_scenarios", {}).get("success", False)
        
        if connection_ok and processing_ok and multi_client_ok and error_handling_ok:
            summary["integration_quality"] = "excellent"
        elif connection_ok and processing_ok:
            summary["integration_quality"] = "good"
        else:
            summary["integration_quality"] = "poor"
        
        # Multi-client isolation check
        multi_client_result = tests.get("multi_client_isolation", {})
        if multi_client_result.get("isolation_quality") == "poor":
            summary["issues"].append("Poor multi-client isolation detected")
            summary["recommendations"].append("Review resource management and client session isolation")
        
        return summary

    def print_test_results(self, results: Dict[str, Any]):
        """Print formatted test results"""
        print("\n" + "="*80)
        print("STORYSIGN INTEGRATION & PERFORMANCE TEST RESULTS")
        print("="*80)
        
        summary = results.get("summary", {})
        
        # Overall status
        if summary.get("overall_success") and summary.get("performance_targets_met"):
            print("✅ OVERALL STATUS: ALL TESTS PASSED")
        elif summary.get("overall_success"):
            print("⚠️  OVERALL STATUS: INTEGRATION PASSED, PERFORMANCE NEEDS ATTENTION")
        else:
            print("❌ OVERALL STATUS: TESTS FAILED")
        
        # Test summary
        print(f"\n📊 TEST SUMMARY:")
        print(f"   Tests Passed:         {summary.get('tests_passed', 0)}")
        print(f"   Tests Failed:         {summary.get('tests_failed', 0)}")
        print(f"   Integration Quality:  {summary.get('integration_quality', 'unknown').upper()}")
        print(f"   Performance Targets:  {'✅ MET' if summary.get('performance_targets_met') else '❌ NOT MET'}")
        
        # Detailed results
        print(f"\n📋 DETAILED TEST RESULTS:")
        tests = results.get("tests", {})
        
        for test_name, test_result in tests.items():
            status = "✅ PASS" if test_result.get("success") else "❌ FAIL"
            print(f"   {test_name:25}: {status}")
            
            # Show key metrics for specific tests
            if test_name == "latency_validation" and test_result.get("success"):
                avg_latency = test_result.get("avg_latency_ms", 0)
                target_compliance = test_result.get("target_compliance_rate", 0)
                print(f"     └─ Avg Latency: {avg_latency:.1f}ms, Target Compliance: {target_compliance*100:.1f}%")
            
            elif test_name == "performance_benchmarks" and test_result.get("success"):
                benchmark_results = test_result.get("benchmark_results", {})
                single_frame = benchmark_results.get("single_frame", {})
                if single_frame:
                    print(f"     └─ Single Frame: {single_frame.get('avg_latency_ms', 0):.1f}ms avg")
        
        # Issues and recommendations
        issues = summary.get("issues", [])
        if issues:
            print(f"\n⚠️  ISSUES FOUND:")
            for issue in issues:
                print(f"   • {issue}")
        
        recommendations = summary.get("recommendations", [])
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in recommendations:
                print(f"   • {rec}")
        
        if not issues:
            print(f"\n✅ NO ISSUES FOUND - System performing optimally!")
        
        print("="*80)


async def main():
    """Main test execution"""
    tester = IntegrationPerformanceTestSuite()
    
    try:
        print("🚀 Starting StorySign Integration & Performance Tests...")
        print("📡 Testing WebSocket endpoint: ws://localhost:8000/ws/video")
        print("⏱️  Target: <100ms end-to-end processing latency")
        
        results = await tester.run_comprehensive_test_suite()
        tester.print_test_results(results)
        
        # Save results to file
        with open("integration_performance_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: integration_performance_test_results.json")
        
        # Return appropriate exit code
        summary = results.get("summary", {})
        if summary.get("overall_success") and summary.get("performance_targets_met"):
            print("🎉 All integration and performance tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed or performance targets not met.")
            return 1
            
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        print(f"❌ Test execution failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)