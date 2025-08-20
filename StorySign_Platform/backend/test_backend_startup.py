#!/usr/bin/env python3
"""
Test backend startup and basic functionality
"""

import sys
import logging
from pathlib import Path

# Add backend directory to path
sys.path.append(str(Path(__file__).parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_imports():
    """Test that all required modules can be imported"""
    logger.info("Testing imports...")
    
    try:
        from config import get_config
        from video_processor import FrameProcessor
        from main import app, VideoProcessingService, ConnectionManager
        logger.info("✅ All imports successful")
        return True
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        return False


def test_configuration():
    """Test configuration loading"""
    logger.info("Testing configuration...")
    
    try:
        from config import get_config
        config = get_config()
        
        logger.info(f"   Video config: {config.video.width}x{config.video.height}")
        logger.info(f"   MediaPipe complexity: {config.mediapipe.model_complexity}")
        logger.info(f"   Server: {config.server.host}:{config.server.port}")
        logger.info("✅ Configuration loaded successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        return False


def test_video_processing_service():
    """Test VideoProcessingService instantiation"""
    logger.info("Testing VideoProcessingService...")
    
    try:
        from config import get_config
        from main import VideoProcessingService
        
        config = get_config()
        service = VideoProcessingService("test_client", config)
        
        logger.info(f"   Client ID: {service.client_id}")
        logger.info(f"   Frame processor available: {hasattr(service, 'frame_processor')}")
        
        # Clean up
        service.frame_processor.close()
        
        logger.info("✅ VideoProcessingService test passed")
        return True
    except Exception as e:
        logger.error(f"❌ VideoProcessingService test failed: {e}")
        return False


def test_frame_processor():
    """Test FrameProcessor instantiation"""
    logger.info("Testing FrameProcessor...")
    
    try:
        from config import get_config
        from video_processor import FrameProcessor
        
        config = get_config()
        processor = FrameProcessor(config.video, config.mediapipe)
        
        logger.info(f"   Video config: {processor.video_config.width}x{processor.video_config.height}")
        logger.info(f"   MediaPipe config: complexity {processor.mediapipe_config.model_complexity}")
        
        # Clean up
        processor.close()
        
        logger.info("✅ FrameProcessor test passed")
        return True
    except Exception as e:
        logger.error(f"❌ FrameProcessor test failed: {e}")
        return False


def main():
    """Run all backend startup tests"""
    logger.info("Starting backend startup tests...")
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_configuration),
        ("VideoProcessingService", test_video_processing_service),
        ("FrameProcessor", test_frame_processor)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*40}")
        logger.info(f"Running test: {test_name}")
        logger.info(f"{'='*40}")
        
        success = test_func()
        results.append((test_name, success))
        
        if success:
            logger.info(f"✅ {test_name} PASSED")
        else:
            logger.error(f"❌ {test_name} FAILED")
    
    # Summary
    logger.info(f"\n{'='*40}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*40}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "PASSED" if success else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All backend startup tests passed!")
        return 0
    else:
        logger.error("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)