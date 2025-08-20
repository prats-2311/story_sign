#!/usr/bin/env python3
"""
Latency Testing Script for StorySign Platform
Tests end-to-end latency improvements after optimization
"""

import asyncio
import websockets
import json
import time
import base64
import cv2
import numpy as np
from datetime import datetime
import statistics
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LatencyTester:
    """Test latency improvements in the StorySign platform"""
    
    def __init__(self, websocket_url="ws://localhost:8000/ws/video"):
        self.websocket_url = websocket_url
        self.test_results = []
        
    def create_test_frame(self, frame_number: int) -> str:
        """Create a test frame with timestamp for latency measurement"""
        # Create a simple test image
        img = np.zeros((180, 240, 3), dtype=np.uint8)
        
        # Add frame number and timestamp
        cv2.putText(img, f"Frame {frame_number}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(img, f"{int(time.time() * 1000)}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Encode as JPEG
        _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 40])
        base64_data = base64.b64encode(buffer).decode('utf-8')
        
        return f"data:image/jpeg;base64,{base64_data}"
    
    async def test_single_frame_latency(self) -> dict:
        """Test latency for a single frame"""
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                # Create test frame
                frame_data = self.create_test_frame(1)
                
                # Create message
                message = {
                    "type": "raw_frame",
                    "timestamp": datetime.utcnow().isoformat(),
                    "frame_data": frame_data,
                    "metadata": {
                        "frame_number": 1,
                        "client_id": "latency_test",
                        "width": 240,
                        "height": 180,
                        "test_timestamp": time.time() * 1000  # For latency calculation
                    }
                }
                
                # Send frame and measure latency
                send_time = time.time() * 1000
                await websocket.send(json.dumps(message))
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                receive_time = time.time() * 1000
                
                # Calculate latency
                latency_ms = receive_time - send_time
                
                # Parse response
                response_data = json.loads(response)
                
                return {
                    "success": True,
                    "latency_ms": latency_ms,
                    "send_time": send_time,
                    "receive_time": receive_time,
                    "response_type": response_data.get("type"),
                    "processing_time": response_data.get("metadata", {}).get("processing_time_ms", 0),
                    "server_frame_number": response_data.get("metadata", {}).get("server_frame_number", 0)
                }
                
        except Exception as e:
            logger.error(f"Single frame test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "latency_ms": float('inf')
            }
    
    async def test_continuous_latency(self, duration_seconds: int = 30, target_fps: int = 20) -> dict:
        """Test latency over continuous frame streaming"""
        results = []
        frame_interval = 1.0 / target_fps
        
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                logger.info(f"Starting continuous latency test for {duration_seconds}s at {target_fps} FPS")
                
                start_time = time.time()
                frame_number = 0
                
                while time.time() - start_time < duration_seconds:
                    frame_number += 1
                    
                    # Create and send frame
                    frame_data = self.create_test_frame(frame_number)
                    message = {
                        "type": "raw_frame",
                        "timestamp": datetime.utcnow().isoformat(),
                        "frame_data": frame_data,
                        "metadata": {
                            "frame_number": frame_number,
                            "client_id": "latency_test_continuous",
                            "width": 240,
                            "height": 180,
                            "test_timestamp": time.time() * 1000
                        }
                    }
                    
                    send_time = time.time() * 1000
                    await websocket.send(json.dumps(message))
                    
                    # Try to receive response (non-blocking)
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                        receive_time = time.time() * 1000
                        
                        response_data = json.loads(response)
                        latency_ms = receive_time - send_time
                        
                        results.append({
                            "frame_number": frame_number,
                            "latency_ms": latency_ms,
                            "processing_time": response_data.get("metadata", {}).get("processing_time_ms", 0),
                            "success": True
                        })
                        
                    except asyncio.TimeoutError:
                        # No response yet, continue
                        results.append({
                            "frame_number": frame_number,
                            "latency_ms": None,
                            "success": False,
                            "error": "timeout"
                        })
                    
                    # Wait for next frame
                    await asyncio.sleep(frame_interval)
                
                # Collect any remaining responses
                logger.info("Collecting remaining responses...")
                remaining_timeout = 2.0
                while remaining_timeout > 0:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                        receive_time = time.time() * 1000
                        response_data = json.loads(response)
                        
                        # Try to match with sent frame (simplified)
                        for result in results:
                            if result["latency_ms"] is None:
                                result["latency_ms"] = receive_time - (start_time * 1000 + result["frame_number"] * frame_interval * 1000)
                                result["success"] = True
                                break
                                
                        remaining_timeout -= 0.1
                    except asyncio.TimeoutError:
                        remaining_timeout -= 0.1
                
        except Exception as e:
            logger.error(f"Continuous test failed: {e}")
            return {"success": False, "error": str(e)}
        
        # Calculate statistics
        successful_results = [r for r in results if r["success"] and r["latency_ms"] is not None]
        latencies = [r["latency_ms"] for r in successful_results]
        
        if latencies:
            return {
                "success": True,
                "total_frames": len(results),
                "successful_frames": len(successful_results),
                "success_rate": len(successful_results) / len(results),
                "avg_latency_ms": statistics.mean(latencies),
                "median_latency_ms": statistics.median(latencies),
                "min_latency_ms": min(latencies),
                "max_latency_ms": max(latencies),
                "std_latency_ms": statistics.stdev(latencies) if len(latencies) > 1 else 0,
                "target_fps": target_fps,
                "actual_fps": len(successful_results) / duration_seconds,
                "detailed_results": results[:10]  # First 10 results for debugging
            }
        else:
            return {
                "success": False,
                "error": "No successful frames processed",
                "total_frames": len(results)
            }
    
    async def run_comprehensive_test(self) -> dict:
        """Run comprehensive latency testing suite"""
        logger.info("Starting comprehensive latency testing...")
        
        test_results = {
            "test_timestamp": datetime.utcnow().isoformat(),
            "tests": {}
        }
        
        # Test 1: Single frame latency
        logger.info("Test 1: Single frame latency")
        single_frame_result = await self.test_single_frame_latency()
        test_results["tests"]["single_frame"] = single_frame_result
        
        if single_frame_result["success"]:
            logger.info(f"✅ Single frame latency: {single_frame_result['latency_ms']:.2f}ms")
        else:
            logger.error(f"❌ Single frame test failed: {single_frame_result.get('error')}")
        
        # Test 2: Continuous streaming at different FPS
        fps_tests = [10, 20, 30]
        for fps in fps_tests:
            logger.info(f"Test 2.{fps}: Continuous streaming at {fps} FPS")
            continuous_result = await self.test_continuous_latency(duration_seconds=15, target_fps=fps)
            test_results["tests"][f"continuous_{fps}fps"] = continuous_result
            
            if continuous_result["success"]:
                logger.info(f"✅ {fps} FPS - Avg latency: {continuous_result['avg_latency_ms']:.2f}ms, "
                           f"Success rate: {continuous_result['success_rate']*100:.1f}%")
            else:
                logger.error(f"❌ {fps} FPS test failed: {continuous_result.get('error')}")
        
        # Generate summary
        test_results["summary"] = self._generate_test_summary(test_results["tests"])
        
        return test_results
    
    def _generate_test_summary(self, tests: dict) -> dict:
        """Generate summary of test results"""
        summary = {
            "overall_success": True,
            "best_latency_ms": float('inf'),
            "worst_latency_ms": 0,
            "recommended_fps": 20,
            "latency_target_met": False,
            "issues": []
        }
        
        # Analyze single frame test
        if tests.get("single_frame", {}).get("success"):
            single_latency = tests["single_frame"]["latency_ms"]
            summary["best_latency_ms"] = min(summary["best_latency_ms"], single_latency)
            summary["worst_latency_ms"] = max(summary["worst_latency_ms"], single_latency)
        else:
            summary["overall_success"] = False
            summary["issues"].append("Single frame test failed")
        
        # Analyze continuous tests
        best_fps_result = None
        for test_name, result in tests.items():
            if test_name.startswith("continuous_") and result.get("success"):
                avg_latency = result["avg_latency_ms"]
                success_rate = result["success_rate"]
                
                summary["best_latency_ms"] = min(summary["best_latency_ms"], avg_latency)
                summary["worst_latency_ms"] = max(summary["worst_latency_ms"], avg_latency)
                
                # Find best performing FPS
                if (best_fps_result is None or 
                    (avg_latency < best_fps_result["avg_latency_ms"] and success_rate > 0.8)):
                    best_fps_result = result
                    summary["recommended_fps"] = result["target_fps"]
                
                # Check for issues
                if success_rate < 0.9:
                    summary["issues"].append(f"Low success rate at {result['target_fps']} FPS: {success_rate*100:.1f}%")
                if avg_latency > 200:
                    summary["issues"].append(f"High latency at {result['target_fps']} FPS: {avg_latency:.1f}ms")
        
        # Check if latency target is met
        if summary["best_latency_ms"] < 100:
            summary["latency_target_met"] = True
        
        # Overall assessment
        if summary["best_latency_ms"] == float('inf'):
            summary["overall_success"] = False
            summary["issues"].append("No successful latency measurements")
        
        return summary
    
    def print_results(self, results: dict):
        """Print formatted test results"""
        print("\n" + "="*60)
        print("STORYSIGN LATENCY TEST RESULTS")
        print("="*60)
        
        summary = results.get("summary", {})
        
        # Overall status
        if summary.get("overall_success"):
            print("✅ OVERALL STATUS: PASSED")
        else:
            print("❌ OVERALL STATUS: FAILED")
        
        # Key metrics
        print(f"\n📊 KEY METRICS:")
        print(f"   Best Latency:     {summary.get('best_latency_ms', 'N/A'):.2f}ms")
        print(f"   Worst Latency:    {summary.get('worst_latency_ms', 'N/A'):.2f}ms")
        print(f"   Target Met:       {'✅ YES' if summary.get('latency_target_met') else '❌ NO'} (<100ms)")
        print(f"   Recommended FPS:  {summary.get('recommended_fps', 'N/A')}")
        
        # Issues
        issues = summary.get("issues", [])
        if issues:
            print(f"\n⚠️  ISSUES FOUND:")
            for issue in issues:
                print(f"   • {issue}")
        else:
            print(f"\n✅ NO ISSUES FOUND")
        
        # Detailed results
        print(f"\n📋 DETAILED RESULTS:")
        tests = results.get("tests", {})
        
        for test_name, test_result in tests.items():
            if test_result.get("success"):
                if test_name == "single_frame":
                    print(f"   {test_name:20}: {test_result['latency_ms']:6.2f}ms")
                else:
                    print(f"   {test_name:20}: {test_result['avg_latency_ms']:6.2f}ms avg "
                          f"({test_result['success_rate']*100:4.1f}% success)")
            else:
                print(f"   {test_name:20}: FAILED - {test_result.get('error', 'Unknown error')}")
        
        print("="*60)

async def main():
    """Main test execution"""
    tester = LatencyTester()
    
    try:
        print("🚀 Starting StorySign Latency Optimization Tests...")
        print("📡 Testing connection to ws://localhost:8000/ws/video")
        
        results = await tester.run_comprehensive_test()
        tester.print_results(results)
        
        # Save results to file
        import json
        with open("latency_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: latency_test_results.json")
        
        # Return appropriate exit code
        if results.get("summary", {}).get("overall_success"):
            print("🎉 All tests passed! Latency optimizations are working.")
            return 0
        else:
            print("⚠️  Some tests failed. Check the issues above.")
            return 1
            
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        print(f"❌ Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)