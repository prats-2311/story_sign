#!/usr/bin/env python3
"""
Test script for gesture detection functionality
Tests the enhanced video processor with gesture detection capabilities
"""

import sys
import os
import time
import logging

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import VideoConfig, MediaPipeConfig, GestureDetectionConfig
from video_processor import FrameProcessor, GestureDetector, PracticeSessionManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_gesture_detection_config():
    """Test gesture detection configuration"""
    logger.info("Testing gesture detection configuration...")
    
    try:
        config = GestureDetectionConfig()
        
        assert config.velocity_threshold == 0.02
        assert config.pause_duration_ms == 1000
        assert config.min_gesture_duration_ms == 500
        assert config.landmark_buffer_size == 100
        assert config.enabled == True
        
        logger.info("✅ Gesture detection configuration test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Gesture detection configuration test failed: {e}")
        return False


def test_gesture_detector():
    """Test gesture detector functionality"""
    logger.info("Testing gesture detector...")
    
    try:
        config = GestureDetectionConfig()
        detector = GestureDetector(config)
        
        # Test initial state
        assert not detector.is_detecting
        assert len(detector.landmark_buffer) == 0
        
        # Test gesture detection with mock landmarks
        mock_landmarks = {"hands": True, "face": False, "pose": False}
        
        # Simulate gesture start detection
        # Note: This is a simplified test - real implementation would need actual landmark data
        state = detector.get_detection_state()
        assert state["is_detecting"] == False
        assert state["enabled"] == True
        
        logger.info("✅ Gesture detector test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Gesture detector test failed: {e}")
        return False


def test_practice_session_manager():
    """Test practice session manager functionality"""
    logger.info("Testing practice session manager...")
    
    try:
        config = GestureDetectionConfig()
        manager = PracticeSessionManager(config)
        
        # Test initial state
        assert not manager.is_active
        assert manager.current_sentence is None
        
        # Test starting a practice session
        story_sentences = [
            "Hello, how are you?",
            "I am learning ASL.",
            "Thank you for helping me."
        ]
        
        result = manager.start_practice_session(story_sentences, "test_session")
        
        assert result["success"] == True
        assert result["session_id"] == "test_session"
        assert result["total_sentences"] == 3
        assert result["current_sentence_index"] == 0
        assert result["current_sentence"] == "Hello, how are you?"
        assert result["practice_mode"] == "listening"
        
        # Test session state
        state = manager.get_session_state()
        assert state["is_active"] == True
        assert state["session_id"] == "test_session"
        
        # Test control messages
        next_result = manager.handle_control_message("next_sentence")
        assert next_result["success"] == True
        assert next_result["current_sentence_index"] == 1
        assert next_result["current_sentence"] == "I am learning ASL."
        
        # Test try again
        try_again_result = manager.handle_control_message("try_again")
        assert try_again_result["success"] == True
        assert try_again_result["practice_mode"] == "listening"
        
        # Test stop session
        stop_result = manager.handle_control_message("stop_session")
        assert stop_result["success"] == True
        assert not manager.is_active
        
        logger.info("✅ Practice session manager test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Practice session manager test failed: {e}")
        return False


def test_enhanced_frame_processor():
    """Test enhanced frame processor with gesture detection"""
    logger.info("Testing enhanced frame processor...")
    
    try:
        video_config = VideoConfig()
        mediapipe_config = MediaPipeConfig()
        gesture_config = GestureDetectionConfig()
        
        processor = FrameProcessor(video_config, mediapipe_config, gesture_config)
        
        # Test that gesture detection is enabled
        assert processor.practice_session_manager is not None
        
        # Test practice session methods
        story_sentences = ["Hello world", "How are you?"]
        session_result = processor.start_practice_session(story_sentences, "test")
        
        assert session_result["success"] == True
        assert session_result["total_sentences"] == 2
        
        # Test getting session state
        state = processor.get_practice_session_state()
        assert state["gesture_detection_enabled"] == True
        assert state["is_active"] == True
        
        # Test control messages
        control_result = processor.handle_practice_control("next_sentence")
        assert control_result["success"] == True
        
        # Test stopping session
        stop_result = processor.handle_practice_control("stop_session")
        assert stop_result["success"] == True
        
        logger.info("✅ Enhanced frame processor test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced frame processor test failed: {e}")
        return False


def test_frame_processor_without_gesture_detection():
    """Test frame processor without gesture detection"""
    logger.info("Testing frame processor without gesture detection...")
    
    try:
        video_config = VideoConfig()
        mediapipe_config = MediaPipeConfig()
        
        # Create processor without gesture config
        processor = FrameProcessor(video_config, mediapipe_config)
        
        # Test that gesture detection is disabled
        assert processor.practice_session_manager is None
        
        # Test that practice session methods return appropriate errors
        session_result = processor.start_practice_session(["test"])
        assert session_result["success"] == False
        assert "not enabled" in session_result["error"]
        
        state = processor.get_practice_session_state()
        assert state["gesture_detection_enabled"] == False
        
        logger.info("✅ Frame processor without gesture detection test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Frame processor without gesture detection test failed: {e}")
        return False


def main():
    """Run all gesture detection tests"""
    logger.info("Starting gesture detection tests...")
    
    tests = [
        test_gesture_detection_config,
        test_gesture_detector,
        test_practice_session_manager,
        test_enhanced_frame_processor,
        test_frame_processor_without_gesture_detection
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"Test {test.__name__} crashed: {e}")
            failed += 1
    
    logger.info(f"\n=== Test Results ===")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total: {passed + failed}")
    
    if failed == 0:
        logger.info("🎉 All gesture detection tests passed!")
        return True
    else:
        logger.error(f"❌ {failed} tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)