#!/usr/bin/env python3
"""
Real-Time Performance Testing Suite
Tests WebSocket connection pooling, message queuing, and adaptive quality under load
"""

import asyncio
import logging
import time
import json
import statistics
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import websockets
import base64
import cv2
import numpy as np
import concurrent.futures
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TestMetrics:
    """Performance test metrics"""
    test_name: str
    duration_seconds: float
    total_messages: int
    messages_per_second: float
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    error_rate_percent: float
    cpu_usage_percent: float
    memory_usage_mb: float
    success: bool
    errors: List[str]


class PerformanceTestClient:
    """
    High-performance test client for WebSocket connections
    """
    
    def __init__(self, client_id: str, server_url: str = "ws://localhost:8000/ws/video"):
        self.client_id = client_id
        self.server_url = server_url
        self.logger = logging.getLogger(f"{__name__}.TestClient.{client_id}")
        
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.connected = False
        
        # Metrics
        self.messages_sent = 0
        self.messages_received = 0
        self.latency_samples = []
        self.errors = []
        
        # Test frame data
        self.test_frame_data = self._generate_test_frame()
    
    def _generate_test_frame(self) -> str:
        """Generate test frame data"""
        try:
            # Create a simple test image
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, f"Test Frame {self.client_id}", (50, 240), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Encode as JPEG
            success, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not success:
                raise ValueError("Failed to encode test frame")
            
            # Convert to base64
            base64_data = base64.b64encode(buffer).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_data}"
        
        except Exception as e:
            self.logger.error(f"Failed to generate test frame: {e}")
            return ""
    
    async def connect(self) -> bool:
        """Connect to WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.server_url)
            self.connected = True
            
            # Wait for connection confirmation
            response = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
            message = json.loads(response)
            
            if message.get("type") == "connection_established":
                self.logger.debug(f"Client {self.client_id} connected successfully")
                return True
            else:
                self.logger.error(f"Unexpected connection response: {message}")
                return False
        
        except Exception as e:
            self.logger.error(f"Connection failed for {self.client_id}: {e}")
            self.errors.append(f"Connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket server"""
        if self.websocket and self.connected:
            try:
                await self.websocket.close()
            except Exception as e:
                self.logger.debug(f"Disconnect error for {self.client_id}: {e}")
            
            self.connected = False
    
    async def send_frame(self, frame_number: int) -> Optional[float]:
        """
        Send a test frame and measure latency
        
        Returns:
            Latency in milliseconds or None if failed
        """
        if not self.connected or not self.websocket:
            return None
        
        try:
            start_time = time.time()
            
            message = {
                "type": "raw_frame",
                "frame_data": self.test_frame_data,
                "metadata": {
                    "frame_number": frame_number,
                    "client_id": self.client_id,
                    "timestamp": start_time,
                    "test_mode": True
                }
            }
            
            await self.websocket.send(json.dumps(message))
            self.messages_sent += 1
            
            # Wait for response
            response = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
            end_time = time.time()
            
            latency_ms = (end_time - start_time) * 1000
            self.latency_samples.append(latency_ms)
            self.messages_received += 1
            
            return latency_ms
        
        except asyncio.TimeoutError:
            self.errors.append(f"Timeout waiting for response to frame {frame_number}")
            return None
        except Exception as e:
            self.errors.append(f"Send frame error: {e}")
            return None
    
    async def send_ping(self) -> Optional[float]:
        """Send ping and measure response time"""
        if not self.connected or not self.websocket:
            return None
        
        try:
            start_time = time.time()
            
            ping_message = {
                "type": "ping",
                "timestamp": start_time
            }
            
            await self.websocket.send(json.dumps(ping_message))
            
            # Wait for pong
            response = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
            end_time = time.time()
            
            message = json.loads(response)
            if message.get("type") == "pong":
                return (end_time - start_time) * 1000
            
            return None
        
        except Exception as e:
            self.errors.append(f"Ping error: {e}")
            return None
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get client metrics"""
        return {
            "client_id": self.client_id,
            "connected": self.connected,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "avg_latency_ms": statistics.mean(self.latency_samples) if self.latency_samples else 0.0,
            "p95_latency_ms": statistics.quantiles(self.latency_samples, n=20)[18] if len(self.latency_samples) >= 20 else 0.0,
            "p99_latency_ms": statistics.quantiles(self.latency_samples, n=100)[98] if len(self.latency_samples) >= 100 else 0.0,
            "error_count": len(self.errors),
            "errors": self.errors[-5:]  # Last 5 errors
        }


class RealTimePerformanceTester:
    """
    Comprehensive real-time performance testing suite
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.PerformanceTester")
        self.test_results: List[TestMetrics] = []
    
    async def test_connection_pool_capacity(self, max_connections: int = 100) -> TestMetrics:
        """Test WebSocket connection pool capacity"""
        self.logger.info(f"Testing connection pool capacity with {max_connections} connections")
        
        start_time = time.time()
        clients = []
        connected_clients = 0
        errors = []
        
        try:
            # Create and connect clients
            for i in range(max_connections):
                client = PerformanceTestClient(f"pool_test_{i}")
                clients.append(client)
                
                try:
                    if await client.connect():
                        connected_clients += 1
                    else:
                        errors.extend(client.errors)
                except Exception as e:
                    errors.append(f"Client {i} connection error: {e}")
                
                # Small delay to avoid overwhelming the server
                await asyncio.sleep(0.01)
            
            # Test basic communication
            ping_latencies = []
            for client in clients:
                if client.connected:
                    latency = await client.send_ping()
                    if latency:
                        ping_latencies.append(latency)
            
            # Disconnect all clients
            disconnect_tasks = [client.disconnect() for client in clients]
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)
            
            duration = time.time() - start_time
            
            return TestMetrics(
                test_name="connection_pool_capacity",
                duration_seconds=duration,
                total_messages=connected_clients,
                messages_per_second=connected_clients / duration if duration > 0 else 0,
                avg_latency_ms=statistics.mean(ping_latencies) if ping_latencies else 0.0,
                p95_latency_ms=statistics.quantiles(ping_latencies, n=20)[18] if len(ping_latencies) >= 20 else 0.0,
                p99_latency_ms=statistics.quantiles(ping_latencies, n=100)[98] if len(ping_latencies) >= 100 else 0.0,
                error_rate_percent=(len(errors) / max_connections) * 100,
                cpu_usage_percent=psutil.cpu_percent(),
                memory_usage_mb=psutil.virtual_memory().used / 1024 / 1024,
                success=connected_clients >= max_connections * 0.9,  # 90% success rate
                errors=errors[:10]  # First 10 errors
            )
        
        except Exception as e:
            self.logger.error(f"Connection pool test error: {e}")
            return TestMetrics(
                test_name="connection_pool_capacity",
                duration_seconds=time.time() - start_time,
                total_messages=0,
                messages_per_second=0,
                avg_latency_ms=0,
                p95_latency_ms=0,
                p99_latency_ms=0,
                error_rate_percent=100,
                cpu_usage_percent=psutil.cpu_percent(),
                memory_usage_mb=psutil.virtual_memory().used / 1024 / 1024,
                success=False,
                errors=[str(e)]
            )
    
    async def test_high_throughput_messaging(
        self, 
        num_clients: int = 10, 
        messages_per_client: int = 100,
        concurrent_sends: bool = True
    ) -> TestMetrics:
        """Test high-throughput message processing"""
        self.logger.info(f"Testing high-throughput messaging: {num_clients} clients, "
                        f"{messages_per_client} messages each")
        
        start_time = time.time()
        clients = []
        errors = []
        all_latencies = []
        
        try:
            # Create and connect clients
            for i in range(num_clients):
                client = PerformanceTestClient(f"throughput_test_{i}")
                if await client.connect():
                    clients.append(client)
                else:
                    errors.extend(client.errors)
            
            if not clients:
                raise RuntimeError("No clients connected successfully")
            
            # Send messages
            if concurrent_sends:
                # Concurrent sending
                tasks = []
                for client in clients:
                    for msg_num in range(messages_per_client):
                        task = asyncio.create_task(client.send_frame(msg_num))
                        tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Collect latencies
                for result in results:
                    if isinstance(result, (int, float)) and result > 0:
                        all_latencies.append(result)
            else:
                # Sequential sending
                for client in clients:
                    for msg_num in range(messages_per_client):
                        latency = await client.send_frame(msg_num)
                        if latency:
                            all_latencies.append(latency)
            
            # Collect client metrics
            total_sent = sum(client.messages_sent for client in clients)
            total_received = sum(client.messages_received for client in clients)
            
            for client in clients:
                errors.extend(client.errors)
            
            # Disconnect clients
            disconnect_tasks = [client.disconnect() for client in clients]
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)
            
            duration = time.time() - start_time
            
            return TestMetrics(
                test_name="high_throughput_messaging",
                duration_seconds=duration,
                total_messages=total_sent,
                messages_per_second=total_sent / duration if duration > 0 else 0,
                avg_latency_ms=statistics.mean(all_latencies) if all_latencies else 0.0,
                p95_latency_ms=statistics.quantiles(all_latencies, n=20)[18] if len(all_latencies) >= 20 else 0.0,
                p99_latency_ms=statistics.quantiles(all_latencies, n=100)[98] if len(all_latencies) >= 100 else 0.0,
                error_rate_percent=((total_sent - total_received) / total_sent * 100) if total_sent > 0 else 0,
                cpu_usage_percent=psutil.cpu_percent(),
                memory_usage_mb=psutil.virtual_memory().used / 1024 / 1024,
                success=total_received >= total_sent * 0.95,  # 95% success rate
                errors=errors[:10]
            )
        
        except Exception as e:
            self.logger.error(f"High throughput test error: {e}")
            return TestMetrics(
                test_name="high_throughput_messaging",
                duration_seconds=time.time() - start_time,
                total_messages=0,
                messages_per_second=0,
                avg_latency_ms=0,
                p95_latency_ms=0,
                p99_latency_ms=0,
                error_rate_percent=100,
                cpu_usage_percent=psutil.cpu_percent(),
                memory_usage_mb=psutil.virtual_memory().used / 1024 / 1024,
                success=False,
                errors=[str(e)]
            )
    
    async def test_sustained_load(
        self, 
        num_clients: int = 5, 
        duration_seconds: int = 60,
        frames_per_second: int = 10
    ) -> TestMetrics:
        """Test sustained load over time"""
        self.logger.info(f"Testing sustained load: {num_clients} clients for {duration_seconds}s "
                        f"at {frames_per_second} FPS")
        
        start_time = time.time()
        clients = []
        errors = []
        all_latencies = []
        
        try:
            # Create and connect clients
            for i in range(num_clients):
                client = PerformanceTestClient(f"sustained_test_{i}")
                if await client.connect():
                    clients.append(client)
                else:
                    errors.extend(client.errors)
            
            if not clients:
                raise RuntimeError("No clients connected successfully")
            
            # Calculate frame interval
            frame_interval = 1.0 / frames_per_second
            
            # Send frames continuously
            frame_number = 0
            end_time = start_time + duration_seconds
            
            while time.time() < end_time:
                frame_start = time.time()
                
                # Send frame from each client
                tasks = []
                for client in clients:
                    task = asyncio.create_task(client.send_frame(frame_number))
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Collect latencies
                for result in results:
                    if isinstance(result, (int, float)) and result > 0:
                        all_latencies.append(result)
                
                frame_number += 1
                
                # Wait for next frame interval
                elapsed = time.time() - frame_start
                if elapsed < frame_interval:
                    await asyncio.sleep(frame_interval - elapsed)
            
            # Collect final metrics
            total_sent = sum(client.messages_sent for client in clients)
            total_received = sum(client.messages_received for client in clients)
            
            for client in clients:
                errors.extend(client.errors)
            
            # Disconnect clients
            disconnect_tasks = [client.disconnect() for client in clients]
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)
            
            actual_duration = time.time() - start_time
            
            return TestMetrics(
                test_name="sustained_load",
                duration_seconds=actual_duration,
                total_messages=total_sent,
                messages_per_second=total_sent / actual_duration if actual_duration > 0 else 0,
                avg_latency_ms=statistics.mean(all_latencies) if all_latencies else 0.0,
                p95_latency_ms=statistics.quantiles(all_latencies, n=20)[18] if len(all_latencies) >= 20 else 0.0,
                p99_latency_ms=statistics.quantiles(all_latencies, n=100)[98] if len(all_latencies) >= 100 else 0.0,
                error_rate_percent=((total_sent - total_received) / total_sent * 100) if total_sent > 0 else 0,
                cpu_usage_percent=psutil.cpu_percent(),
                memory_usage_mb=psutil.virtual_memory().used / 1024 / 1024,
                success=total_received >= total_sent * 0.9,  # 90% success rate for sustained load
                errors=errors[:10]
            )
        
        except Exception as e:
            self.logger.error(f"Sustained load test error: {e}")
            return TestMetrics(
                test_name="sustained_load",
                duration_seconds=time.time() - start_time,
                total_messages=0,
                messages_per_second=0,
                avg_latency_ms=0,
                p95_latency_ms=0,
                p99_latency_ms=0,
                error_rate_percent=100,
                cpu_usage_percent=psutil.cpu_percent(),
                memory_usage_mb=psutil.virtual_memory().used / 1024 / 1024,
                success=False,
                errors=[str(e)]
            )
    
    async def test_adaptive_quality_response(self, num_clients: int = 3) -> TestMetrics:
        """Test adaptive quality system response to load"""
        self.logger.info(f"Testing adaptive quality response with {num_clients} clients")
        
        start_time = time.time()
        clients = []
        errors = []
        quality_changes = []
        
        try:
            # Create and connect clients
            for i in range(num_clients):
                client = PerformanceTestClient(f"adaptive_test_{i}")
                if await client.connect():
                    clients.append(client)
                else:
                    errors.extend(client.errors)
            
            if not clients:
                raise RuntimeError("No clients connected successfully")
            
            # Phase 1: Low load (should maintain high quality)
            self.logger.info("Phase 1: Low load testing")
            for _ in range(10):
                for client in clients:
                    await client.send_frame(_)
                await asyncio.sleep(0.5)  # 2 FPS
            
            # Phase 2: Medium load (should adapt quality)
            self.logger.info("Phase 2: Medium load testing")
            for _ in range(20):
                tasks = [client.send_frame(_) for client in clients]
                await asyncio.gather(*tasks, return_exceptions=True)
                await asyncio.sleep(0.1)  # 10 FPS
            
            # Phase 3: High load (should reduce quality significantly)
            self.logger.info("Phase 3: High load testing")
            for _ in range(30):
                tasks = [client.send_frame(_) for client in clients]
                await asyncio.gather(*tasks, return_exceptions=True)
                await asyncio.sleep(0.033)  # 30 FPS
            
            # Collect metrics
            total_sent = sum(client.messages_sent for client in clients)
            total_received = sum(client.messages_received for client in clients)
            
            all_latencies = []
            for client in clients:
                all_latencies.extend(client.latency_samples)
                errors.extend(client.errors)
            
            # Disconnect clients
            disconnect_tasks = [client.disconnect() for client in clients]
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)
            
            duration = time.time() - start_time
            
            return TestMetrics(
                test_name="adaptive_quality_response",
                duration_seconds=duration,
                total_messages=total_sent,
                messages_per_second=total_sent / duration if duration > 0 else 0,
                avg_latency_ms=statistics.mean(all_latencies) if all_latencies else 0.0,
                p95_latency_ms=statistics.quantiles(all_latencies, n=20)[18] if len(all_latencies) >= 20 else 0.0,
                p99_latency_ms=statistics.quantiles(all_latencies, n=100)[98] if len(all_latencies) >= 100 else 0.0,
                error_rate_percent=((total_sent - total_received) / total_sent * 100) if total_sent > 0 else 0,
                cpu_usage_percent=psutil.cpu_percent(),
                memory_usage_mb=psutil.virtual_memory().used / 1024 / 1024,
                success=total_received >= total_sent * 0.85,  # 85% success rate under varying load
                errors=errors[:10]
            )
        
        except Exception as e:
            self.logger.error(f"Adaptive quality test error: {e}")
            return TestMetrics(
                test_name="adaptive_quality_response",
                duration_seconds=time.time() - start_time,
                total_messages=0,
                messages_per_second=0,
                avg_latency_ms=0,
                p95_latency_ms=0,
                p99_latency_ms=0,
                error_rate_percent=100,
                cpu_usage_percent=psutil.cpu_percent(),
                memory_usage_mb=psutil.virtual_memory().used / 1024 / 1024,
                success=False,
                errors=[str(e)]
            )
    
    async def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run comprehensive performance test suite"""
        self.logger.info("Starting comprehensive real-time performance test suite")
        
        test_suite_start = time.time()
        
        # Test 1: Connection Pool Capacity
        self.logger.info("=" * 60)
        self.logger.info("TEST 1: Connection Pool Capacity")
        pool_test = await self.test_connection_pool_capacity(max_connections=50)
        self.test_results.append(pool_test)
        
        # Wait between tests
        await asyncio.sleep(5)
        
        # Test 2: High Throughput Messaging
        self.logger.info("=" * 60)
        self.logger.info("TEST 2: High Throughput Messaging")
        throughput_test = await self.test_high_throughput_messaging(
            num_clients=10, 
            messages_per_client=50
        )
        self.test_results.append(throughput_test)
        
        # Wait between tests
        await asyncio.sleep(5)
        
        # Test 3: Sustained Load
        self.logger.info("=" * 60)
        self.logger.info("TEST 3: Sustained Load")
        sustained_test = await self.test_sustained_load(
            num_clients=5, 
            duration_seconds=30,
            frames_per_second=15
        )
        self.test_results.append(sustained_test)
        
        # Wait between tests
        await asyncio.sleep(5)
        
        # Test 4: Adaptive Quality Response
        self.logger.info("=" * 60)
        self.logger.info("TEST 4: Adaptive Quality Response")
        adaptive_test = await self.test_adaptive_quality_response(num_clients=3)
        self.test_results.append(adaptive_test)
        
        total_duration = time.time() - test_suite_start
        
        # Generate summary report
        summary = self._generate_test_summary(total_duration)
        
        self.logger.info("=" * 60)
        self.logger.info("COMPREHENSIVE TEST SUITE COMPLETED")
        self.logger.info(f"Total Duration: {total_duration:.2f} seconds")
        self.logger.info(f"Tests Passed: {summary['tests_passed']}/{summary['total_tests']}")
        self.logger.info(f"Overall Success Rate: {summary['overall_success_rate']:.1f}%")
        
        return summary
    
    def _generate_test_summary(self, total_duration: float) -> Dict[str, Any]:
        """Generate comprehensive test summary"""
        tests_passed = sum(1 for test in self.test_results if test.success)
        total_tests = len(self.test_results)
        
        # Calculate aggregate metrics
        total_messages = sum(test.total_messages for test in self.test_results)
        avg_throughput = sum(test.messages_per_second for test in self.test_results) / total_tests if total_tests > 0 else 0
        avg_latency = sum(test.avg_latency_ms for test in self.test_results) / total_tests if total_tests > 0 else 0
        avg_error_rate = sum(test.error_rate_percent for test in self.test_results) / total_tests if total_tests > 0 else 0
        
        return {
            "test_suite_duration": total_duration,
            "total_tests": total_tests,
            "tests_passed": tests_passed,
            "tests_failed": total_tests - tests_passed,
            "overall_success_rate": (tests_passed / total_tests * 100) if total_tests > 0 else 0,
            "aggregate_metrics": {
                "total_messages_processed": total_messages,
                "avg_throughput_msg_per_sec": avg_throughput,
                "avg_latency_ms": avg_latency,
                "avg_error_rate_percent": avg_error_rate
            },
            "individual_test_results": [
                {
                    "test_name": test.test_name,
                    "success": test.success,
                    "duration_seconds": test.duration_seconds,
                    "messages_per_second": test.messages_per_second,
                    "avg_latency_ms": test.avg_latency_ms,
                    "p95_latency_ms": test.p95_latency_ms,
                    "p99_latency_ms": test.p99_latency_ms,
                    "error_rate_percent": test.error_rate_percent,
                    "cpu_usage_percent": test.cpu_usage_percent,
                    "memory_usage_mb": test.memory_usage_mb
                }
                for test in self.test_results
            ],
            "performance_benchmarks": {
                "connection_capacity_target": 50,
                "throughput_target_msg_per_sec": 100,
                "latency_target_p95_ms": 100,
                "error_rate_target_percent": 5.0,
                "benchmarks_met": self._check_performance_benchmarks()
            }
        }
    
    def _check_performance_benchmarks(self) -> Dict[str, bool]:
        """Check if performance benchmarks are met"""
        benchmarks = {}
        
        for test in self.test_results:
            if test.test_name == "connection_pool_capacity":
                benchmarks["connection_capacity"] = test.success and test.total_messages >= 45  # 90% of 50
            elif test.test_name == "high_throughput_messaging":
                benchmarks["throughput"] = test.success and test.messages_per_second >= 80  # 80% of 100
            elif test.test_name == "sustained_load":
                benchmarks["sustained_performance"] = test.success and test.p95_latency_ms <= 150  # 150ms P95
            elif test.test_name == "adaptive_quality_response":
                benchmarks["adaptive_quality"] = test.success and test.error_rate_percent <= 15  # 15% error rate
        
        return benchmarks


async def main():
    """Main test execution"""
    logger.info("Starting Real-Time Performance Test Suite")
    
    # Check if server is running
    try:
        import websockets
        async with websockets.connect("ws://localhost:8000/ws/video") as websocket:
            await websocket.close()
        logger.info("WebSocket server is accessible")
    except Exception as e:
        logger.error(f"Cannot connect to WebSocket server: {e}")
        logger.error("Please ensure the StorySign backend is running on localhost:8000")
        return
    
    # Run performance tests
    tester = RealTimePerformanceTester()
    
    try:
        results = await tester.run_comprehensive_test_suite()
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"performance_test_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Test results saved to {results_file}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("REAL-TIME PERFORMANCE TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {results['total_tests']}")
        print(f"Tests Passed: {results['tests_passed']}")
        print(f"Overall Success Rate: {results['overall_success_rate']:.1f}%")
        print(f"Total Messages Processed: {results['aggregate_metrics']['total_messages_processed']}")
        print(f"Average Throughput: {results['aggregate_metrics']['avg_throughput_msg_per_sec']:.1f} msg/sec")
        print(f"Average Latency: {results['aggregate_metrics']['avg_latency_ms']:.1f} ms")
        print(f"Average Error Rate: {results['aggregate_metrics']['avg_error_rate_percent']:.1f}%")
        
        print("\nBenchmark Results:")
        for benchmark, passed in results['performance_benchmarks']['benchmarks_met'].items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {benchmark}: {status}")
        
        print("\nIndividual Test Results:")
        for test in results['individual_test_results']:
            status = "✓ PASS" if test['success'] else "✗ FAIL"
            print(f"  {test['test_name']}: {status} "
                  f"({test['messages_per_second']:.1f} msg/sec, "
                  f"{test['avg_latency_ms']:.1f}ms avg latency)")
        
        print("=" * 80)
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())