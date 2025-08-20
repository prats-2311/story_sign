#!/usr/bin/env python3
"""
Test script for MediaPipe integration
Tests frame decoding, MediaPipe processing, and landmark detection
"""

import cv2
import numpy as np
import base64
import logging
import sys
from pathlib import Path

# Add backend directory to path for imports
sys.path.append(str(Path(__file__).parent))

from config import get_config
from video_processor import FrameProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_test_frame() -> np.ndarray:
    """Create a simple test frame with basic shapes"""
    # Create a 640x480 frame with some basic shapes
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add some colored rectangles and circles to simulate a person
    # Head (circle)
    cv2.circle(frame, (320, 120), 50, (255, 200, 150), -1)
    
    # Body (rectangle)
    cv2.rectangle(frame, (280, 170), (360, 350), (100, 150, 200), -1)
    
    # Arms (rectangles)
    cv2.rectangle(frame, (200, 200), (280, 230), (150, 100, 100), -1)  # Left arm
    cv2.rectangle(frame, (360, 200), (440, 230), (150, 100, 100), -1)  # Right arm
    
    # Hands (circles)
    cv2.circle(frame, (180, 215), 15, (200, 150, 100), -1)  # Left hand
    cv2.circle(frame, (460, 215), 15, (200, 150, 100), -1)  # Right hand
    
    return frame


def frame_to_base64(frame: np.ndarray) -> str:
    """Convert frame to base64 string"""
    _, buffer = cv2.imencode('.jpg', frame)
    base64_data = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/jpeg;base64,{base64_data}"


def test_frame_decoding():
    """Test base64 frame decoding functionality"""
    logger.info("Testing frame decoding...")
    
    try:
        # Load configuration
        config = get_config()
        
        # Create frame processor
        processor = FrameProcessor(config.video, config.mediapipe)
        
        # Create test frame
        test_frame = create_test_frame()
        logger.info(f"Created test frame: {test_frame.shape}")
        
        # Encode to base64
        base64_frame = frame_to_base64(test_frame)
        logger.info(f"Encoded frame to base64: {len(base64_frame)} characters")
        
        # Decode back
        decoded_frame = processor.decode_base64_frame(base64_frame)
        
        if decoded_frame is not None:
            logger.info(f"Successfully decoded frame: {decoded_frame.shape}")
            return True
        else:
            logger.error("Failed to decode frame")
            return False
            
    except Exception as e:
        logger.error(f"Frame decoding test failed: {e}", exc_info=True)
        return False


def test_mediapipe_processing():
    """Test MediaPipe processing functionality"""
    logger.info("Testing MediaPipe processing...")
    
    try:
        # Load configuration
        config = get_config()
        
        # Create frame processor
        processor = FrameProcessor(config.video, config.mediapipe)
        
        # Create test frame
        test_frame = create_test_frame()
        
        # Process through MediaPipe
        processed_frame, landmarks_detected, processing_time = processor.process_frame_with_mediapipe(test_frame)
        
        logger.info(f"MediaPipe processing completed in {processing_time:.2f}ms")
        logger.info(f"Landmarks detected: {landmarks_detected}")
        logger.info(f"Processed frame shape: {processed_frame.shape}")
        
        # Clean up
        processor.close()
        
        return True
        
    except Exception as e:
        logger.error(f"MediaPipe processing test failed: {e}", exc_info=True)
        return False


def test_full_pipeline():
    """Test complete processing pipeline"""
    logger.info("Testing full processing pipeline...")
    
    try:
        # Load configuration
        config = get_config()
        
        # Create frame processor
        processor = FrameProcessor(config.video, config.mediapipe)
        
        # Create test frame and encode to base64
        test_frame = create_test_frame()
        base64_frame = frame_to_base64(test_frame)
        
        # Process through full pipeline
        result = processor.process_base64_frame(base64_frame)
        
        if result is not None:
            logger.info("Full pipeline processing successful!")
            logger.info(f"Processing time: {result['processing_time_ms']:.2f}ms")
            logger.info(f"Landmarks detected: {result['landmarks_detected']}")
            logger.info(f"Output frame data length: {len(result['frame_data'])} characters")
            
            # Clean up
            processor.close()
            return True
        else:
            logger.error("Full pipeline processing failed")
            return False
            
    except Exception as e:
        logger.error(f"Full pipeline test failed: {e}", exc_info=True)
        return False


def main():
    """Run all MediaPipe integration tests"""
    logger.info("Starting MediaPipe integration tests...")
    
    tests = [
        ("Frame Decoding", test_frame_decoding),
        ("MediaPipe Processing", test_mediapipe_processing),
        ("Full Pipeline", test_full_pipeline)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running test: {test_name}")
        logger.info(f"{'='*50}")
        
        success = test_func()
        results.append((test_name, success))
        
        if success:
            logger.info(f"✅ {test_name} PASSED")
        else:
            logger.error(f"❌ {test_name} FAILED")
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "PASSED" if success else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All MediaPipe integration tests passed!")
        return 0
    else:
        logger.error("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)