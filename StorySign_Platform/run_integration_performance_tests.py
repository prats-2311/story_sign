#!/usr/bin/env python3
"""
Integration and Performance Test Runner
Task 11.2: Create integration and performance tests

This script runs the complete suite of integration and performance tests:
- Backend integration and performance tests
- Frontend integration tests  
- Multi-client stress tests
- Comprehensive reporting and analysis
"""

import asyncio
import subprocess
import sys
import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any
import psutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntegrationPerformanceTestRunner:
    """Comprehensive test runner for all integration and performance tests"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.backend_process = None
        
    def check_backend_server(self) -> bool:
        """Check if backend server is running"""
        try:
            import requests
            response = requests.get("http://localhost:8000/", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def start_backend_server(self) -> bool:
        """Start the backend server for testing"""
        logger.info("Starting backend server for testing...")
        
        try:
            # Change to backend directory
            backend_dir = os.path.join(os.path.dirname(__file__), "backend")
            
            # Start the server
            self.backend_process = subprocess.Popen(
                [sys.executable, "main.py"],
                cwd=backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for server to start
            max_wait = 30  # 30 seconds
            wait_time = 0
            
            while wait_time < max_wait:
                if self.check_backend_server():
                    logger.info("✅ Backend server started successfully")
                    return True
                
                time.sleep(1)
                wait_time += 1
                
                # Check if process died
                if self.backend_process.poll() is not None:
                    stdout, stderr = self.backend_process.communicate()
                    logger.error(f"Backend server failed to start:")
                    logger.error(f"STDOUT: {stdout.decode()}")
                    logger.error(f"STDERR: {stderr.decode()}")
                    return False
            
            logger.error("Backend server failed to start within timeout")
            return False
            
        except Exception as e:
            logger.error(f"Failed to start backend server: {e}")
            return False
    
    def stop_backend_server(self):
        """Stop the backend server"""
        if self.backend_process:
            logger.info("Stopping backend server...")
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
                self.backend_process.wait()
            logger.info("Backend server stopped")
    
    async def run_backend_integration_tests(self) -> Dict[str, Any]:
        """Run backend integration and performance tests"""
        logger.info("Running backend integration and performance tests...")
        
        try:
            # Import and run the backend test suite
            from backend.test_integration_performance import IntegrationPerformanceTestSuite
            
            tester = IntegrationPerformanceTestSuite()
            results = await tester.run_comprehensive_test_suite()
            
            return {
                "success": True,
                "results": results,
                "test_type": "backend_integration_performance"
            }
            
        except Exception as e:
            logger.error(f"Backend integration tests failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "test_type": "backend_integration_performance"
            }
    
    def run_frontend_integration_tests(self) -> Dict[str, Any]:
        """Run frontend integration tests"""
        logger.info("Running frontend integration tests...")
        
        try:
            # Run the frontend test suite
            frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
            
            result = subprocess.run(
                ["node", "test_integration_performance.js"],
                cwd=frontend_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            # Try to load the results file
            results_file = os.path.join(frontend_dir, "frontend_integration_test_results.json")
            if os.path.exists(results_file):
                with open(results_file, 'r') as f:
                    test_results = json.load(f)
            else:
                test_results = {"error": "Results file not found"}
            
            return {
                "success": result.returncode == 0,
                "results": test_results,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "test_type": "frontend_integration"
            }
            
        except subprocess.TimeoutExpired:
            logger.error("Frontend integration tests timed out")
            return {
                "success": False,
                "error": "Test timeout",
                "test_type": "frontend_integration"
            }
        except Exception as e:
            logger.error(f"Frontend integration tests failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "test_type": "frontend_integration"
            }
    
    async def run_multi_client_stress_tests(self) -> Dict[str, Any]:
        """Run multi-client stress tests"""
        logger.info("Running multi-client stress tests...")
        
        try:
            # Import and run the stress test suite
            from test_multi_client_stress import MultiClientStressTest
            
            tester = MultiClientStressTest()
            results = await tester.run_stress_test(
                num_clients=3,  # Reduced for CI/testing
                duration_seconds=30,  # Shorter duration for testing
                target_fps=10
            )
            
            return {
                "success": results.get("overall_assessment", {}).get("test_success", False),
                "results": results,
                "test_type": "multi_client_stress"
            }
            
        except Exception as e:
            logger.error(f"Multi-client stress tests failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "test_type": "multi_client_stress"
            }
    
    def run_existing_tests(self) -> Dict[str, Any]:
        """Run existing test suites for comparison"""
        logger.info("Running existing test suites...")
        
        existing_results = {}
        
        # Run backend tests
        try:
            backend_dir = os.path.join(os.path.dirname(__file__), "backend")
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-v", "--tb=short"],
                cwd=backend_dir,
                capture_output=True,
                text=True,
                timeout=180
            )
            
            existing_results["backend_pytest"] = {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except Exception as e:
            existing_results["backend_pytest"] = {
                "success": False,
                "error": str(e)
            }
        
        # Run frontend tests
        try:
            frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
            result = subprocess.run(
                ["npm", "test", "--", "--watchAll=false", "--coverage=false"],
                cwd=frontend_dir,
                capture_output=True,
                text=True,
                timeout=180
            )
            
            existing_results["frontend_jest"] = {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except Exception as e:
            existing_results["frontend_jest"] = {
                "success": False,
                "error": str(e)
            }
        
        return existing_results
    
    async def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run the complete integration and performance test suite"""
        self.start_time = time.time()
        
        logger.info("🚀 Starting comprehensive integration and performance test suite...")
        logger.info("="*80)
        
        # Check if backend is already running
        backend_was_running = self.check_backend_server()
        backend_started = False
        
        if not backend_was_running:
            logger.info("Backend server not detected, starting for tests...")
            backend_started = self.start_backend_server()
            if not backend_started:
                return {
                    "success": False,
                    "error": "Failed to start backend server for testing",
                    "test_results": {}
                }
        else:
            logger.info("✅ Backend server already running")
        
        try:
            # Run all test suites
            test_suite_results = {}
            
            # 1. Backend Integration and Performance Tests
            logger.info("\n📡 Running Backend Integration & Performance Tests...")
            test_suite_results["backend_integration"] = await self.run_backend_integration_tests()
            
            # 2. Frontend Integration Tests
            logger.info("\n🖥️  Running Frontend Integration Tests...")
            test_suite_results["frontend_integration"] = self.run_frontend_integration_tests()
            
            # 3. Multi-Client Stress Tests
            logger.info("\n🔥 Running Multi-Client Stress Tests...")
            test_suite_results["multi_client_stress"] = await self.run_multi_client_stress_tests()
            
            # 4. Existing Test Suites (for comparison)
            logger.info("\n🧪 Running Existing Test Suites...")
            test_suite_results["existing_tests"] = self.run_existing_tests()
            
            # Generate comprehensive analysis
            analysis = self._analyze_comprehensive_results(test_suite_results)
            
            return {
                "success": analysis["overall_success"],
                "test_results": test_suite_results,
                "analysis": analysis,
                "execution_time": time.time() - self.start_time
            }
            
        finally:
            # Clean up - stop backend if we started it
            if backend_started and not backend_was_running:
                self.stop_backend_server()
    
    def _analyze_comprehensive_results(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze comprehensive test results"""
        
        analysis = {
            "overall_success": True,
            "test_summary": {},
            "performance_assessment": {},
            "integration_quality": {},
            "recommendations": [],
            "detailed_metrics": {}
        }
        
        # Analyze each test suite
        for test_name, result in test_results.items():
            success = result.get("success", False)
            analysis["test_summary"][test_name] = {
                "success": success,
                "type": result.get("test_type", test_name)
            }
            
            if not success:
                analysis["overall_success"] = False
                error = result.get("error", "Unknown error")
                analysis["recommendations"].append(f"Fix {test_name}: {error}")
        
        # Performance assessment from backend tests
        backend_results = test_results.get("backend_integration", {}).get("results", {})
        if backend_results:
            tests = backend_results.get("tests", {})
            
            # Latency analysis
            latency_test = tests.get("latency_validation", {})
            if latency_test.get("success"):
                avg_latency = latency_test.get("avg_latency_ms", 0)
                target_met = latency_test.get("target_met", False)
                
                analysis["performance_assessment"]["latency"] = {
                    "avg_latency_ms": avg_latency,
                    "target_met": target_met,
                    "grade": "excellent" if target_met and avg_latency < 50 else "good" if target_met else "needs_improvement"
                }
            
            # Performance benchmarks
            benchmark_test = tests.get("performance_benchmarks", {})
            if benchmark_test.get("success"):
                overall_target_met = benchmark_test.get("overall_target_met", False)
                analysis["performance_assessment"]["benchmarks"] = {
                    "target_met": overall_target_met,
                    "grade": "excellent" if overall_target_met else "needs_improvement"
                }
        
        # Multi-client analysis
        stress_results = test_results.get("multi_client_stress", {}).get("results", {})
        if stress_results:
            overall_assessment = stress_results.get("overall_assessment", {})
            analysis["integration_quality"]["multi_client"] = {
                "connection_success_rate": overall_assessment.get("connection_success_rate", 0),
                "isolation_quality": stress_results.get("isolation_analysis", {}).get("isolation_quality", "unknown"),
                "system_stability": overall_assessment.get("system_stability", "unknown")
            }
        
        # Generate recommendations
        if analysis["overall_success"]:
            analysis["recommendations"].append("All integration and performance tests passed successfully")
        else:
            if not analysis["performance_assessment"].get("latency", {}).get("target_met", True):
                analysis["recommendations"].append("Optimize processing pipeline to meet <100ms latency target")
            
            if analysis["integration_quality"].get("multi_client", {}).get("isolation_quality") == "poor":
                analysis["recommendations"].append("Improve client session isolation and resource management")
        
        return analysis
    
    def print_comprehensive_results(self, results: Dict[str, Any]):
        """Print formatted comprehensive test results"""
        print("\n" + "="*100)
        print("STORYSIGN COMPREHENSIVE INTEGRATION & PERFORMANCE TEST RESULTS")
        print("="*100)
        
        # Overall status
        success = results.get("success", False)
        execution_time = results.get("execution_time", 0)
        
        print(f"\n🎯 OVERALL RESULT: {'✅ ALL TESTS PASSED' if success else '❌ SOME TESTS FAILED'}")
        print(f"⏱️  Total Execution Time: {execution_time:.1f} seconds")
        
        # Test summary
        analysis = results.get("analysis", {})
        test_summary = analysis.get("test_summary", {})
        
        print(f"\n📊 TEST SUITE SUMMARY:")
        for test_name, summary in test_summary.items():
            status = "✅ PASS" if summary.get("success") else "❌ FAIL"
            test_type = summary.get("type", test_name)
            print(f"   {test_name:25}: {status:10} ({test_type})")
        
        # Performance assessment
        perf_assessment = analysis.get("performance_assessment", {})
        if perf_assessment:
            print(f"\n⚡ PERFORMANCE ASSESSMENT:")
            
            latency = perf_assessment.get("latency", {})
            if latency:
                print(f"   Latency Performance:  {latency.get('grade', 'unknown').upper()}")
                print(f"   Average Latency:      {latency.get('avg_latency_ms', 0):.1f}ms")
                print(f"   Target Met (<100ms):  {'✅ YES' if latency.get('target_met') else '❌ NO'}")
            
            benchmarks = perf_assessment.get("benchmarks", {})
            if benchmarks:
                print(f"   Benchmark Grade:      {benchmarks.get('grade', 'unknown').upper()}")
        
        # Integration quality
        integration = analysis.get("integration_quality", {})
        if integration:
            print(f"\n🔗 INTEGRATION QUALITY:")
            
            multi_client = integration.get("multi_client", {})
            if multi_client:
                conn_rate = multi_client.get("connection_success_rate", 0)
                print(f"   Connection Success:   {conn_rate*100:.1f}%")
                print(f"   Client Isolation:     {multi_client.get('isolation_quality', 'unknown').upper()}")
                print(f"   System Stability:     {multi_client.get('system_stability', 'unknown').upper()}")
        
        # Recommendations
        recommendations = analysis.get("recommendations", [])
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        
        # Detailed results summary
        test_results = results.get("test_results", {})
        print(f"\n📋 DETAILED TEST RESULTS:")
        
        for test_name, result in test_results.items():
            print(f"\n   {test_name.upper()}:")
            if result.get("success"):
                print(f"     Status: ✅ PASSED")
                
                # Show key metrics if available
                if test_name == "backend_integration":
                    backend_results = result.get("results", {})
                    summary = backend_results.get("summary", {})
                    if summary:
                        print(f"     Tests Passed: {summary.get('tests_passed', 0)}")
                        print(f"     Performance Targets Met: {'✅' if summary.get('performance_targets_met') else '❌'}")
                
                elif test_name == "multi_client_stress":
                    stress_results = result.get("results", {})
                    overall = stress_results.get("overall_assessment", {})
                    if overall:
                        print(f"     Performance Grade: {overall.get('performance_grade', 'unknown').upper()}")
                        print(f"     Frame Success Rate: {overall.get('overall_frame_success_rate', 0)*100:.1f}%")
            else:
                print(f"     Status: ❌ FAILED")
                error = result.get("error", "Unknown error")
                print(f"     Error: {error}")
        
        print("="*100)


async def main():
    """Main test runner execution"""
    runner = IntegrationPerformanceTestRunner()
    
    try:
        print("🚀 Starting StorySign Comprehensive Integration & Performance Tests...")
        print("📋 This will run all integration and performance test suites")
        
        results = await runner.run_comprehensive_test_suite()
        runner.print_comprehensive_results(results)
        
        # Save comprehensive results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"comprehensive_test_results_{timestamp}.json"
        
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Comprehensive results saved to: {results_file}")
        
        # Return appropriate exit code
        if results.get("success"):
            print("\n🎉 All comprehensive integration and performance tests passed!")
            return 0
        else:
            print("\n⚠️  Some tests failed. Review the results above.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Test runner execution failed: {e}")
        print(f"\n❌ Test runner execution failed: {e}")
        return 1
    finally:
        # Ensure cleanup
        runner.stop_backend_server()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)