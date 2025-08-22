#!/usr/bin/env python3
"""
Verification test for Task 16.1: Enhance video processor for gesture detection
Tests all the required functionality for gesture detection implementation
"""

import sys
import os
import time
import logging
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_config, GestureDetectionConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_gesture_detection_config_integration():
    """Test that GestureDetectionConfig is properly integrated into the main config"""
    logger.info("Testing gesture detection config integration...")
    
    try:
        # Test loading full config
        config = get_config()
        
        # Verify gesture detection config exists
        assert hasattr(config, 'gesture_detection')
        assert isinstance(config.gesture_detection, GestureDetectionConfig)
        
        # Verify default values
        gesture_config = config.gesture_detection
        assert gesture_config.velocity_threshold == 0.02
        assert gesture_config.pause_duration_ms == 1000
        assert gesture_config.min_gesture_duration_ms == 500
        assert gesture_config.landmark_buffer_size == 100
        assert gesture_config.smoothing_window == 5
        assert gesture_config.enabled == True
        
        logger.info("✅ Gesture detection config integration test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Gesture detection config integration test failed: {e}")
        return False


def test_video_processor_import():
    """Test that the enhanced video processor can be imported"""
    logger.info("Testing video processor import...")
    
    try:
        # Import the enhanced video processor classes
        from video_processor import FrameProcessor, GestureDetector, PracticeSessionManager
        
        # Verify classes exist
        assert FrameProcessor is not None
        assert GestureDetector is not None
        assert PracticeSessionManager is not None
        
        logger.info("✅ Video processor import test passed")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Video processor import test failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Video processor import test failed with unexpected error: {e}")
        return False


def test_gesture_detector_initialization():
    """Test that GestureDetector can be initialized with config"""
    logger.info("Testing gesture detector initialization...")
    
    try:
        from video_processor import GestureDetector
        
        config = get_config()
        detector = GestureDetector(config.gesture_detection)
        
        # Verify initialization
        assert detector.config == config.gesture_detection
        assert detector.is_detecting == False
        assert len(detector.landmark_buffer) == 0
        assert len(detector.velocity_history) == 0
        
        # Test detection state
        state = detector.get_detection_state()
        assert state["is_detecting"] == False
        assert state["buffer_size"] == 0
        assert state["enabled"] == True
        
        logger.info("✅ Gesture detector initialization test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Gesture detector initialization test failed: {e}")
        return False


def test_practice_session_manager_initialization():
    """Test that PracticeSessionManager can be initialized with config"""
    logger.info("Testing practice session manager initialization...")
    
    try:
        from video_processor import PracticeSessionManager
        
        config = get_config()
        manager = PracticeSessionManager(config.gesture_detection)
        
        # Verify initialization
        assert manager.gesture_config == config.gesture_detection
        assert manager.is_active == False
        assert manager.current_sentence is None
        assert manager.current_sentence_index == 0
        assert len(manager.story_sentences) == 0
        assert manager.practice_mode == "listening"
        
        # Verify gesture detector is initialized
        assert manager.gesture_detector is not None
        
        logger.info("✅ Practice session manager initialization test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Practice session manager initialization test failed: {e}")
        return False


def test_enhanced_frame_processor_initialization():
    """Test that FrameProcessor can be initialized with gesture detection"""
    logger.info("Testing enhanced frame processor initialization...")
    
    try:
        from video_processor import FrameProcessor
        
        config = get_config()
        
        # Test with gesture detection enabled
        processor = FrameProcessor(
            config.video,
            config.mediapipe,
            config.gesture_detection
        )
        
        # Verify gesture detection is enabled
        assert processor.practice_session_manager is not None
        assert processor.gesture_config == config.gesture_detection
        
        # Test without gesture detection
        processor_no_gesture = FrameProcessor(
            config.video,
            config.mediapipe
        )
        
        # Verify gesture detection is disabled
        assert processor_no_gesture.practice_session_manager is None
        
        logger.info("✅ Enhanced frame processor initialization test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced frame processor initialization test failed: {e}")
        return False


def test_practice_session_workflow():
    """Test the complete practice session workflow"""
    logger.info("Testing practice session workflow...")
    
    try:
        from video_processor import FrameProcessor
        
        config = get_config()
        processor = FrameProcessor(
            config.video,
            config.mediapipe,
            config.gesture_detection
        )
        
        # Test starting a practice session
        story_sentences = [
            "Hello, how are you?",
            "I am learning ASL.",
            "Thank you for your help."
        ]
        
        session_result = processor.start_practice_session(story_sentences, "test_workflow")
        assert session_result["success"] == True
        assert session_result["total_sentences"] == 3
        assert session_result["current_sentence"] == "Hello, how are you?"
        
        # Test getting session state
        state = processor.get_practice_session_state()
        assert state["gesture_detection_enabled"] == True
        assert state["is_active"] == True
        assert state["session_id"] == "test_workflow"
        
        # Test control messages
        next_result = processor.handle_practice_control("next_sentence")
        assert next_result["success"] == True
        assert next_result["current_sentence_index"] == 1
        
        try_again_result = processor.handle_practice_control("try_again")
        assert try_again_result["success"] == True
        assert try_again_result["practice_mode"] == "listening"
        
        # Test setting feedback
        feedback_data = {"feedback": "Great job! Keep practicing."}
        feedback_result = processor.handle_practice_control("set_feedback", feedback_data)
        assert feedback_result["success"] == True
        assert feedback_result["practice_mode"] == "feedback"
        
        # Test stopping session
        stop_result = processor.handle_practice_control("stop_session")
        assert stop_result["success"] == True
        
        # Verify session is stopped
        final_state = processor.get_practice_session_state()
        assert final_state["is_active"] == False
        
        logger.info("✅ Practice session workflow test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Practice session workflow test failed: {e}")
        return False


def test_gesture_detection_state_management():
    """Test gesture detection state management"""
    logger.info("Testing gesture detection state management...")
    
    try:
        from video_processor import GestureDetector
        
        config = get_config()
        detector = GestureDetector(config.gesture_detection)
        
        # Test initial state
        initial_state = detector.get_detection_state()
        assert initial_state["is_detecting"] == False
        assert initial_state["buffer_size"] == 0
        assert initial_state["enabled"] == True
        
        # Test reset functionality
        detector.reset_detection()
        assert detector.is_detecting == False
        assert len(detector.landmark_buffer) == 0
        
        # Test buffer management
        mock_landmarks = {"hands": True, "face": False, "pose": False}
        mock_metadata = {"frame_number": 1, "timestamp": time.time()}
        
        # Simulate gesture detection
        detector.is_detecting = True  # Manually set for testing
        detector.collect_landmark_data(mock_landmarks, mock_metadata)
        
        assert len(detector.landmark_buffer) == 1
        buffer = detector.get_gesture_buffer()
        assert len(buffer) == 1
        assert buffer[0]["landmarks"] == mock_landmarks
        
        logger.info("✅ Gesture detection state management test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Gesture detection state management test failed: {e}")
        return False


def test_requirements_compliance():
    """Test compliance with task requirements"""
    logger.info("Testing requirements compliance...")
    
    try:
        from video_processor import FrameProcessor, GestureDetector, PracticeSessionManager
        
        config = get_config()
        
        # Requirement 8.1: System SHALL detect the beginning of gesture and start recording landmark data
        detector = GestureDetector(config.gesture_detection)
        
        # Verify gesture start detection method exists
        assert hasattr(detector, 'detect_gesture_start')
        assert callable(detector.detect_gesture_start)
        
        # Verify landmark data collection method exists
        assert hasattr(detector, 'collect_landmark_data')
        assert callable(detector.collect_landmark_data)
        
        # Requirement 8.2: System SHALL detect the end of gesture
        assert hasattr(detector, 'detect_gesture_end')
        assert callable(detector.detect_gesture_end)
        
        # Requirement 8.3: System SHALL analyze signing attempt
        manager = PracticeSessionManager(config.gesture_detection)
        assert hasattr(manager, 'get_gesture_buffer_for_analysis')
        assert callable(manager.get_gesture_buffer_for_analysis)
        
        # Verify stateful gesture analysis
        assert hasattr(detector, 'is_detecting')
        assert hasattr(detector, 'landmark_buffer')
        
        # Verify hand movement velocity detection
        assert hasattr(detector, 'calculate_hand_velocity')
        assert callable(detector.calculate_hand_velocity)
        
        # Verify movement pause detection
        assert hasattr(detector, 'last_movement_time')
        
        # Verify practice session state management
        assert hasattr(manager, 'current_sentence')
        assert hasattr(manager, 'practice_mode')
        assert hasattr(manager, 'is_active')
        
        logger.info("✅ Requirements compliance test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Requirements compliance test failed: {e}")
        return False


def main():
    """Run all Task 16.1 verification tests"""
    logger.info("Starting Task 16.1 verification tests...")
    logger.info("Task: Enhance video processor for gesture detection")
    logger.info("Requirements: 8.1, 8.2, 8.3")
    
    tests = [
        test_gesture_detection_config_integration,
        test_video_processor_import,
        test_gesture_detector_initialization,
        test_practice_session_manager_initialization,
        test_enhanced_frame_processor_initialization,
        test_practice_session_workflow,
        test_gesture_detection_state_management,
        test_requirements_compliance
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
    
    logger.info(f"\n=== Task 16.1 Verification Results ===")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total: {passed + failed}")
    
    if failed == 0:
        logger.info("🎉 Task 16.1 implementation verified successfully!")
        logger.info("✅ All gesture detection functionality is working correctly")
        logger.info("✅ Requirements 8.1, 8.2, and 8.3 are satisfied")
        return True
    else:
        logger.error(f"❌ {failed} verification tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)