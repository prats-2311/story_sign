#!/usr/bin/env python3
"""
Test script for Local Vision Service
Tests object identification functionality and error handling
"""

import asyncio
import base64
import logging
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from local_vision_service import LocalVisionService, get_vision_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_test_image_base64() -> str:
    """
    Create a simple test image in base64 format
    This creates a minimal JPEG header for testing
    """
    # Minimal JPEG header for testing
    jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00'
    jpeg_data = jpeg_header + b'\x00' * 100  # Pad with zeros
    return base64.b64encode(jpeg_data).decode('utf-8')


async def test_service_initialization():
    """Test service initialization and health check"""
    logger.info("Testing service initialization...")
    
    service = LocalVisionService()
    
    try:
        await service.initialize()
        logger.info("✓ Service initialized successfully")
        
        # Test health check
        is_healthy = await service.check_health()
        logger.info(f"Health check result: {is_healthy}")
        
        # Get detailed status
        status = await service.get_service_status()
        logger.info(f"Service status: {status}")
        
        return service, is_healthy
        
    except Exception as e:
        logger.error(f"✗ Service initialization failed: {e}")
        return service, False


async def test_object_identification(service: LocalVisionService):
    """Test object identification functionality"""
    logger.info("Testing object identification...")
    
    # Test with invalid data
    logger.info("Testing with invalid base64 data...")
    result = await service.identify_object("invalid_base64_data")
    logger.info(f"Invalid data result: success={result.success}, error={result.error_message}")
    
    # Test with empty data
    logger.info("Testing with empty data...")
    result = await service.identify_object("")
    logger.info(f"Empty data result: success={result.success}, error={result.error_message}")
    
    # Test with test image (will likely fail with real service but tests the flow)
    logger.info("Testing with test image data...")
    test_image = create_test_image_base64()
    result = await service.identify_object(test_image)
    logger.info(f"Test image result: success={result.success}")
    if result.success:
        logger.info(f"  Object: {result.object_name}")
        logger.info(f"  Confidence: {result.confidence}")
        logger.info(f"  Processing time: {result.processing_time_ms}ms")
    else:
        logger.info(f"  Error: {result.error_message}")


async def test_error_handling(service: LocalVisionService):
    """Test error handling scenarios"""
    logger.info("Testing error handling...")
    
    # Test with service disabled
    original_enabled = service.config.enabled
    service.config.enabled = False
    
    result = await service.identify_object(create_test_image_base64())
    logger.info(f"Disabled service result: success={result.success}, error={result.error_message}")
    
    # Restore original setting
    service.config.enabled = original_enabled


async def test_global_service():
    """Test the global service instance"""
    logger.info("Testing global service instance...")
    
    try:
        service = await get_vision_service()
        logger.info("✓ Global service instance created successfully")
        
        status = await service.get_service_status()
        logger.info(f"Global service status: {status}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Global service test failed: {e}")
        return False


async def main():
    """Main test function"""
    logger.info("Starting Local Vision Service tests...")
    
    try:
        # Test service initialization
        service, is_healthy = await test_service_initialization()
        
        if service:
            # Test object identification
            await test_object_identification(service)
            
            # Test error handling
            await test_error_handling(service)
            
            # Clean up
            await service.cleanup()
            logger.info("✓ Service cleanup completed")
        
        # Test global service
        await test_global_service()
        
        logger.info("All tests completed!")
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)