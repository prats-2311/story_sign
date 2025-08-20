#!/usr/bin/env python3
"""
Multi-Client Stress Test for StorySign Platform
Task 11.2: Multi-client connection handling and isolation tests

This test simulates multiple concurrent clients to validate:
- Server can handle multiple WebSocket connections simultaneously
- Client sessions are properly isolated
- Performance remains stable under load
- Resource usage is managed effectively
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
import psutil
import gc
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiClientStressTest:
    """Multi-client stress testing for WebSocket video processing"""
    
    def __init__(self, websocket_url: str = "ws://localhost:8000/ws/video"):
        self.websocket_url = websocket_url
        self.client_results = {}
        self.system_metrics = []
        
    def create_test_frame(self, client_id: int, frame_number: int) -> str:
        """Create unique test frame for each client"""
        # Create test image with client-specific content
        img = np.zeros((180, 240, 3), dtype=np.uint8)
        
        # Add client-specific color
        color_map = {
            0: (255, 100, 100),  # Red
            1: (100, 255, 100),  # Green  
            2: (100, 100, 255),  # Blue
            3: (255, 255, 100),  # Yellow
            4: (255, 100, 255),  # Magenta
        }
        color = color_map.get(client_id % 5, (128, 128, 128))
        
        # Draw client-specific shapes
        cv2.circle(img, (120, 90), 40, color, -1)
        cv2.rectangle(img, (20, 20), (220, 160), color, 2)
        
        # Add client and frame info
        cv2.putText(img, f"Client {client_id}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(img, f"Frame {frame_number}", (10, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(img, f"{int(time.time() * 1000)}", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # Encode as JPEG
        _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 60])
        base64_data = base64.b64encode(buffer).decode('utf-8')
        
        return f"data:image/jpeg;base64,{base64_data}"

    async def client_session(self, client_id: int, duration_seconds: int = 30, 
                           target_fps: int = 10) -> Dict[str, Any]:
        """Individual client session for stress testing"""
        logger.info(f"Starting client {client_id} session for {duration_seconds}s at {target_fps} FPS")
        
        session_results = {
            "client_id": client_id,
            "start_time": time.time(),
            "frames_sent": 0,
            "frames_received": 0,
            "latencies": [],
            "processing_times": [],
            "errors": [],
            "connection_established": False,
            "session_completed": False
        }
        
        frame_interval = 1.0 / target_fps
        
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                session_results["connection_established"] = True
                logger.info(f"Client {client_id} connected successfully")
                
                start_time = time.time()
                frame_number = 0
                
                while time.time() - start_time < duration_seconds:
                    frame_number += 1
                    session_results["frames_sent"] += 1
                    
                    try:
                        # Create and send frame
                        frame_data = self.create_test_frame(client_id, frame_number)
                        message = {
                            "type": "raw_frame",
                            "timestamp": datetime.utcnow().isoformat(),
                            "frame_data": frame_data,
                            "metadata": {
                                "frame_number": frame_number,
                                "client_id": f"stress_client_{client_id}",
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
                            if response_data.get("type") == "processed_frame":
                                latency = receive_time - send_time
                                processing_time = response_data.get("metadata", {}).get("processing_time_ms", 0)
                                
                                session_results["latencies"].append(latency)
                                session_results["processing_times"].append(processing_time)
                                session_results["frames_received"] += 1
                            
                        except asyncio.TimeoutError:
                            # No response yet, continue
                            pass
                        except json.JSONDecodeError as e:
                            session_results["errors"].append(f"JSON decode error: {str(e)}")
                        
                        # Wait for next frame
                        await asyncio.sleep(frame_interval)
                        
                    except Exception as e:
                        session_results["errors"].append(f"Frame {frame_number} error: {str(e)}")
                        continue
                
                # Collect any remaining responses
                remaining_timeout = 2.0
                while remaining_timeout > 0:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                        response_data = json.loads(response)
                        if response_data.get("type") == "processed_frame":
                            session_results["frames_received"] += 1
                        remaining_timeout -= 0.1
                    except asyncio.TimeoutError:
                        remaining_timeout -= 0.1
                    except:
                        break
                
                session_results["session_completed"] = True
                logger.info(f"Client {client_id} session completed successfully")
                
        except websockets.exceptions.ConnectionRefused:
            session_results["errors"].append("Connection refused - server not available")
            logger.error(f"Client {client_id} connection refused")
        except Exception as e:
            session_results["errors"].append(f"Session error: {str(e)}")
            logger.error(f"Client {client_id} session failed: {e}")
        
        # Calculate session statistics
        session_results["duration"] = time.time() - session_results["start_time"]
        session_results["success_rate"] = (session_results["frames_received"] / 
                                         session_results["frames_sent"] 
                                         if session_results["frames_sent"] > 0 else 0)
        
        if session_results["latencies"]:
            session_results["avg_latency_ms"] = statistics.mean(session_results["latencies"])
            session_results["max_latency_ms"] = max(session_results["latencies"])
            session_results["min_latency_ms"] = min(session_results["latencies"])
        else:
            session_results["avg_latency_ms"] = 0
            session_results["max_latency_ms"] = 0
            session_results["min_latency_ms"] = 0
        
        if session_results["processing_times"]:
            session_results["avg_processing_time_ms"] = statistics.mean(session_results["processing_times"])
        else:
            session_results["avg_processing_time_ms"] = 0
        
        return session_results

    def monitor_system_resources(self, duration_seconds: int):
        """Monitor system resources during stress test"""
        logger.info(f"Starting system resource monitoring for {duration_seconds}s")
        
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            try:
                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                # Get process-specific metrics
                process = psutil.Process()
                process_memory = process.memory_info().rss / 1024 / 1024  # MB
                process_cpu = process.cpu_percent()
                
                metrics = {
                    "timestamp": time.time(),
                    "system_cpu_percent": cpu_percent,
                    "system_memory_percent": memory.percent,
                    "system_memory_available_gb": memory.available / (1024**3),
                    "process_memory_mb": process_memory,
                    "process_cpu_percent": process_cpu,
                    "active_connections": len(psutil.net_connections())
                }
                
                self.system_metrics.append(metrics)
                
            except Exception as e:
                logger.warning(f"Resource monitoring error: {e}")
            
            time.sleep(1.0)
        
        logger.info("System resource monitoring completed")

    async def run_stress_test(self, num_clients: int = 5, duration_seconds: int = 60, 
                            target_fps: int = 10) -> Dict[str, Any]:
        """Run comprehensive multi-client stress test"""
        logger.info(f"Starting stress test: {num_clients} clients, {duration_seconds}s, {target_fps} FPS each")
        
        # Start system monitoring in background thread
        monitor_thread = threading.Thread(
            target=self.monitor_system_resources, 
            args=(duration_seconds + 10,)
        )
        monitor_thread.start()
        
        # Start all client sessions concurrently
        client_tasks = []
        for client_id in range(num_clients):
            task = asyncio.create_task(
                self.client_session(client_id, duration_seconds, target_fps)
            )
            client_tasks.append(task)
        
        # Wait for all clients to complete
        logger.info("Waiting for all client sessions to complete...")
        client_results = await asyncio.gather(*client_tasks, return_exceptions=True)
        
        # Wait for monitoring to complete
        monitor_thread.join()
        
        # Analyze results
        stress_test_results = self._analyze_stress_test_results(
            client_results, num_clients, duration_seconds, target_fps
        )
        
        return stress_test_results

    def _analyze_stress_test_results(self, client_results: List[Any], 
                                   num_clients: int, duration_seconds: int, 
                                   target_fps: int) -> Dict[str, Any]:
        """Analyze stress test results and generate comprehensive report"""
        
        analysis = {
            "test_parameters": {
                "num_clients": num_clients,
                "duration_seconds": duration_seconds,
                "target_fps": target_fps,
                "expected_total_frames": num_clients * duration_seconds * target_fps
            },
            "client_analysis": {},
            "system_analysis": {},
            "performance_analysis": {},
            "isolation_analysis": {},
            "overall_assessment": {}
        }
        
        # Analyze individual client results
        successful_clients = 0
        total_frames_sent = 0
        total_frames_received = 0
        all_latencies = []
        all_processing_times = []
        client_success_rates = []
        
        for i, result in enumerate(client_results):
            if isinstance(result, dict):
                client_id = result.get("client_id", i)
                analysis["client_analysis"][f"client_{client_id}"] = result
                
                if result.get("connection_established", False):
                    successful_clients += 1
                
                total_frames_sent += result.get("frames_sent", 0)
                total_frames_received += result.get("frames_received", 0)
                
                if result.get("latencies"):
                    all_latencies.extend(result["latencies"])
                
                if result.get("processing_times"):
                    all_processing_times.extend(result["processing_times"])
                
                client_success_rates.append(result.get("success_rate", 0))
            else:
                # Handle exceptions
                analysis["client_analysis"][f"client_{i}"] = {
                    "error": str(result),
                    "connection_established": False
                }
        
        # System resource analysis
        if self.system_metrics:
            cpu_usage = [m["system_cpu_percent"] for m in self.system_metrics]
            memory_usage = [m["system_memory_percent"] for m in self.system_metrics]
            process_memory = [m["process_memory_mb"] for m in self.system_metrics]
            
            analysis["system_analysis"] = {
                "avg_cpu_percent": statistics.mean(cpu_usage),
                "max_cpu_percent": max(cpu_usage),
                "avg_memory_percent": statistics.mean(memory_usage),
                "max_memory_percent": max(memory_usage),
                "avg_process_memory_mb": statistics.mean(process_memory),
                "max_process_memory_mb": max(process_memory),
                "resource_stability": "stable" if max(cpu_usage) < 90 and max(memory_usage) < 90 else "unstable"
            }
        
        # Performance analysis
        if all_latencies:
            analysis["performance_analysis"] = {
                "total_frames_processed": len(all_latencies),
                "avg_latency_ms": statistics.mean(all_latencies),
                "median_latency_ms": statistics.median(all_latencies),
                "min_latency_ms": min(all_latencies),
                "max_latency_ms": max(all_latencies),
                "std_latency_ms": statistics.stdev(all_latencies) if len(all_latencies) > 1 else 0,
                "frames_under_100ms": sum(1 for l in all_latencies if l < 100.0),
                "latency_target_compliance": sum(1 for l in all_latencies if l < 100.0) / len(all_latencies)
            }
        
        if all_processing_times:
            analysis["performance_analysis"]["avg_processing_time_ms"] = statistics.mean(all_processing_times)
            analysis["performance_analysis"]["max_processing_time_ms"] = max(all_processing_times)
        
        # Isolation analysis (check if clients interfere with each other)
        if len(client_success_rates) > 1:
            success_rate_variance = statistics.stdev(client_success_rates)
            client_latencies = []
            
            for client_data in analysis["client_analysis"].values():
                if isinstance(client_data, dict) and client_data.get("avg_latency_ms", 0) > 0:
                    client_latencies.append(client_data["avg_latency_ms"])
            
            latency_variance = statistics.stdev(client_latencies) if len(client_latencies) > 1 else 0
            
            analysis["isolation_analysis"] = {
                "success_rate_variance": success_rate_variance,
                "latency_variance": latency_variance,
                "isolation_quality": "good" if success_rate_variance < 0.1 and latency_variance < 20 else "poor",
                "client_interference": "minimal" if latency_variance < 20 else "significant"
            }
        
        # Overall assessment
        overall_success_rate = total_frames_received / total_frames_sent if total_frames_sent > 0 else 0
        connection_success_rate = successful_clients / num_clients
        
        performance_grade = "excellent"
        if analysis.get("performance_analysis", {}).get("latency_target_compliance", 0) < 0.9:
            performance_grade = "good"
        if analysis.get("performance_analysis", {}).get("avg_latency_ms", 0) > 150:
            performance_grade = "poor"
        
        analysis["overall_assessment"] = {
            "test_success": connection_success_rate > 0.8 and overall_success_rate > 0.7,
            "connection_success_rate": connection_success_rate,
            "overall_frame_success_rate": overall_success_rate,
            "performance_grade": performance_grade,
            "system_stability": analysis.get("system_analysis", {}).get("resource_stability", "unknown"),
            "isolation_quality": analysis.get("isolation_analysis", {}).get("isolation_quality", "unknown"),
            "recommendations": self._generate_recommendations(analysis)
        }
        
        return analysis

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Performance recommendations
        perf = analysis.get("performance_analysis", {})
        if perf.get("avg_latency_ms", 0) > 100:
            recommendations.append("Consider optimizing MediaPipe processing or reducing frame resolution")
        
        if perf.get("latency_target_compliance", 1.0) < 0.9:
            recommendations.append("Improve latency consistency - less than 90% of frames meet <100ms target")
        
        # System recommendations
        system = analysis.get("system_analysis", {})
        if system.get("max_cpu_percent", 0) > 80:
            recommendations.append("High CPU usage detected - consider load balancing or optimization")
        
        if system.get("max_memory_percent", 0) > 80:
            recommendations.append("High memory usage - implement better memory management")
        
        # Isolation recommendations
        isolation = analysis.get("isolation_analysis", {})
        if isolation.get("isolation_quality") == "poor":
            recommendations.append("Poor client isolation - review session management and resource allocation")
        
        # Connection recommendations
        overall = analysis.get("overall_assessment", {})
        if overall.get("connection_success_rate", 0) < 0.9:
            recommendations.append("Connection reliability issues - check WebSocket server configuration")
        
        if not recommendations:
            recommendations.append("System performing well under stress test conditions")
        
        return recommendations

    def print_stress_test_results(self, results: Dict[str, Any]):
        """Print formatted stress test results"""
        print("\n" + "="*80)
        print("STORYSIGN MULTI-CLIENT STRESS TEST RESULTS")
        print("="*80)
        
        # Test parameters
        params = results.get("test_parameters", {})
        print(f"\n📋 TEST PARAMETERS:")
        print(f"   Clients:              {params.get('num_clients', 'N/A')}")
        print(f"   Duration:             {params.get('duration_seconds', 'N/A')}s")
        print(f"   Target FPS per client: {params.get('target_fps', 'N/A')}")
        print(f"   Expected total frames: {params.get('expected_total_frames', 'N/A')}")
        
        # Overall assessment
        overall = results.get("overall_assessment", {})
        success = overall.get("test_success", False)
        print(f"\n🎯 OVERALL ASSESSMENT:")
        print(f"   Test Result:          {'✅ PASSED' if success else '❌ FAILED'}")
        print(f"   Connection Success:   {overall.get('connection_success_rate', 0)*100:.1f}%")
        print(f"   Frame Success Rate:   {overall.get('overall_frame_success_rate', 0)*100:.1f}%")
        print(f"   Performance Grade:    {overall.get('performance_grade', 'unknown').upper()}")
        print(f"   System Stability:     {overall.get('system_stability', 'unknown').upper()}")
        print(f"   Isolation Quality:    {overall.get('isolation_quality', 'unknown').upper()}")
        
        # Performance metrics
        perf = results.get("performance_analysis", {})
        if perf:
            print(f"\n⚡ PERFORMANCE METRICS:")
            print(f"   Avg Latency:          {perf.get('avg_latency_ms', 0):.1f}ms")
            print(f"   Latency Range:        {perf.get('min_latency_ms', 0):.1f} - {perf.get('max_latency_ms', 0):.1f}ms")
            print(f"   Target Compliance:    {perf.get('latency_target_compliance', 0)*100:.1f}% (<100ms)")
            print(f"   Frames Processed:     {perf.get('total_frames_processed', 0)}")
        
        # System resources
        system = results.get("system_analysis", {})
        if system:
            print(f"\n💻 SYSTEM RESOURCES:")
            print(f"   Avg CPU Usage:        {system.get('avg_cpu_percent', 0):.1f}%")
            print(f"   Peak CPU Usage:       {system.get('max_cpu_percent', 0):.1f}%")
            print(f"   Avg Memory Usage:     {system.get('avg_memory_percent', 0):.1f}%")
            print(f"   Peak Process Memory:  {system.get('max_process_memory_mb', 0):.1f}MB")
        
        # Recommendations
        recommendations = overall.get("recommendations", [])
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in recommendations:
                print(f"   • {rec}")
        
        print("="*80)


async def main():
    """Main stress test execution"""
    tester = MultiClientStressTest()
    
    try:
        print("🚀 Starting StorySign Multi-Client Stress Test...")
        print("📡 Testing WebSocket endpoint: ws://localhost:8000/ws/video")
        
        # Run stress test with different configurations
        print("\n🔥 Running stress test: 5 clients, 60 seconds, 10 FPS each")
        results = await tester.run_stress_test(
            num_clients=5, 
            duration_seconds=60, 
            target_fps=10
        )
        
        tester.print_stress_test_results(results)
        
        # Save results to file
        with open("multi_client_stress_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: multi_client_stress_test_results.json")
        
        # Return appropriate exit code
        overall_success = results.get("overall_assessment", {}).get("test_success", False)
        if overall_success:
            print("🎉 Multi-client stress test passed!")
            return 0
        else:
            print("⚠️  Stress test revealed issues that need attention.")
            return 1
            
    except Exception as e:
        logger.error(f"Stress test execution failed: {e}")
        print(f"❌ Stress test execution failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)