#!/usr/bin/env python3
"""
Quick Integration Test Verification
Task 11.2: Create integration and performance tests

A simplified test to verify the integration test framework is working
"""

import asyncio
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_backend_integration_import():
    """Test that backend integration tests can be imported and run"""
    try:
        # Add backend to path
        backend_path = os.path.join(os.path.dirname(__file__), "backend")
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        
        # Try to import the test suite
        from test_integration_performance import IntegrationPerformanceTestSuite
        
        # Create test instance
        tester = IntegrationPerformanceTestSuite()
        
        # Test basic functionality (without server)
        frame_data = tester.create_test_frame(1)
        assert frame_data.startswith("data:image/jpeg;base64,"), "Frame data should be base64 encoded"
        
        logger.info("✅ Backend integration test framework working")
        return True
        
    except Exception as e:
        logger.error(f"❌ Backend integration test import failed: {e}")
        return False


def test_frontend_integration_files():
    """Test that frontend integration test files exist and are valid"""
    try:
        frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
        test_file = os.path.join(frontend_dir, "test_integration_performance.js")
        
        if not os.path.exists(test_file):
            logger.error("❌ Frontend integration test file not found")
            return False
        
        # Check file content
        with open(test_file, 'r') as f:
            content = f.read()
        
        required_classes = ["FrontendIntegrationTestSuite", "testWebSocketClientIntegration"]
        for class_name in required_classes:
            if class_name not in content:
                logger.error(f"❌ Required class/method {class_name} not found in frontend test")
                return False
        
        logger.info("✅ Frontend integration test files valid")
        return True
        
    except Exception as e:
        logger.error(f"❌ Frontend integration test validation failed: {e}")
        return False


async def test_multi_client_stress_import():
    """Test that multi-client stress tests can be imported"""
    try:
        from test_multi_client_stress import MultiClientStressTest
        
        # Create test instance
        tester = MultiClientStressTest()
        
        # Test basic functionality
        frame_data = tester.create_test_frame(0, 1)
        assert frame_data.startswith("data:image/jpeg;base64,"), "Frame data should be base64 encoded"
        
        logger.info("✅ Multi-client stress test framework working")
        return True
        
    except Exception as e:
        logger.error(f"❌ Multi-client stress test import failed: {e}")
        return False


def test_test_runner_import():
    """Test that the comprehensive test runner can be imported"""
    try:
        from run_integration_performance_tests import IntegrationPerformanceTestRunner
        
        # Create runner instance
        runner = IntegrationPerformanceTestRunner()
        
        # Test basic functionality
        assert hasattr(runner, 'run_comprehensive_test_suite'), "Runner should have run_comprehensive_test_suite method"
        
        logger.info("✅ Test runner framework working")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test runner import failed: {e}")
        return False


async def main():
    """Run quick integration test verification"""
    logger.info("🚀 Running Quick Integration Test Verification...")
    logger.info("="*60)
    
    tests = [
        ("Backend Integration Framework", test_backend_integration_import()),
        ("Frontend Integration Files", test_frontend_integration_files()),
        ("Multi-Client Stress Framework", test_multi_client_stress_import()),
        ("Test Runner Framework", test_test_runner_import())
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_coro in tests:
        logger.info(f"\nTesting: {test_name}")
        try:
            if asyncio.iscoroutine(test_coro):
                result = await test_coro
            else:
                result = test_coro
            
            if result:
                passed += 1
        except Exception as e:
            logger.error(f"❌ {test_name} failed: {e}")
    
    logger.info("="*60)
    logger.info(f"Quick Verification Complete: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("✅ All integration test frameworks are working correctly!")
        logger.info("🎯 Ready to run comprehensive integration and performance tests")
        return 0
    else:
        logger.error(f"❌ {total - passed} framework tests failed")
        logger.error("🔧 Fix the issues above before running full test suite")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)