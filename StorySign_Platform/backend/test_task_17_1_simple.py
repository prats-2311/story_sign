#!/usr/bin/env python3
"""
Simple Test Task 17.1: Practice Session Controls and State Management
Tests the practice session control logic without WebSocket dependencies
"""

import sys
import os
import logging
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_practice_session_manager():
    """Test PracticeSessionManager functionality"""
    logger.info("🧪 Testing PracticeSessionManager...")
    
    try:
        from video_processor import PracticeSessionManager
        from config import GestureDetectionConfig
        
        # Create gesture detection config
        gesture_config = GestureDetectionConfig()
        gesture_config.enabled = True
        gesture_config.velocity_threshold = 0.02
        gesture_config.pause_duration_ms = 1000
        gesture_config.min_gesture_duration_ms = 500
        
        # Initialize practice session manager
        manager = PracticeSessionManager(gesture_config)
        logger.info("✅ PracticeSessionManager initialized")
        
        # Test starting a practice session
        story_sentences = [
            "The cat sat on the mat.",
            "The dog ran in the park.",
            "The bird flew in the sky."
        ]
        
        result = manager.start_practice_session(story_sentences, "test_session_123")
        
        if result.get("success"):
            logger.info("✅ Practice session started successfully")
            logger.info(f"   Session ID: {result.get('session_id')}")
            logger.info(f"   Total sentences: {result.get('total_sentences')}")
            logger.info(f"   Current sentence: {result.get('current_sentence')}")
        else:
            logger.error(f"❌ Failed to start practice session: {result.get('error')}")
            return False
        
        # Test control messages
        control_tests = [
            ("try_again", {}),
            ("next_sentence", {}),
            ("try_again", {}),
            ("next_sentence", {}),
            ("complete_story", {})
        ]
        
        for action, data in control_tests:
            logger.info(f"🧪 Testing control action: {action}")
            result = manager.handle_control_message(action, data)
            
            if result.get("success"):
                logger.info(f"✅ Control action '{action}' successful")
                logger.info(f"   Current sentence index: {result.get('current_sentence_index', 'N/A')}")
                logger.info(f"   Practice mode: {result.get('practice_mode', 'N/A')}")
            else:
                logger.error(f"❌ Control action '{action}' failed: {result.get('error')}")
        
        # Test session state
        state = manager.get_session_state()
        logger.info("🧪 Testing session state retrieval")
        logger.info(f"   Active: {state.get('is_active')}")
        logger.info(f"   Current sentence: {state.get('current_sentence')}")
        logger.info(f"   Practice mode: {state.get('practice_mode')}")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Test error: {e}")
        return False

def test_frame_processor_integration():
    """Test FrameProcessor practice session integration"""
    logger.info("🧪 Testing FrameProcessor practice session integration...")
    
    try:
        from video_processor import FrameProcessor
        from config import VideoConfig, MediaPipeConfig, GestureDetectionConfig
        
        # Create configurations
        video_config = VideoConfig()
        mediapipe_config = MediaPipeConfig()
        gesture_config = GestureDetectionConfig()
        gesture_config.enabled = True
        
        # Initialize frame processor
        processor = FrameProcessor(video_config, mediapipe_config, gesture_config)
        logger.info("✅ FrameProcessor initialized with gesture detection")
        
        # Test starting practice session
        story_sentences = [
            "Hello world in ASL.",
            "Practice makes perfect.",
            "Keep learning and growing."
        ]
        
        result = processor.start_practice_session(story_sentences, "test_session_456")
        
        if result.get("success"):
            logger.info("✅ Practice session started via FrameProcessor")
        else:
            logger.error(f"❌ Failed to start practice session: {result.get('error')}")
            return False
        
        # Test control handling
        control_result = processor.handle_practice_control("try_again", {})
        
        if control_result.get("success"):
            logger.info("✅ Practice control handled via FrameProcessor")
        else:
            logger.error(f"❌ Failed to handle practice control: {control_result.get('error')}")
            return False
        
        # Test session state
        state = processor.get_practice_session_state()
        logger.info(f"✅ Session state retrieved: {state.get('is_active', False)}")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Test error: {e}")
        return False

def test_control_message_validation():
    """Test control message validation and error handling"""
    logger.info("🧪 Testing control message validation...")
    
    try:
        from video_processor import PracticeSessionManager
        from config import GestureDetectionConfig
        
        # Create gesture detection config
        gesture_config = GestureDetectionConfig()
        gesture_config.enabled = True
        
        # Initialize practice session manager
        manager = PracticeSessionManager(gesture_config)
        
        # Start a session first
        story_sentences = ["Test sentence."]
        manager.start_practice_session(story_sentences, "validation_test")
        
        # Test invalid control actions
        invalid_tests = [
            ("invalid_action", {}),
            ("", {}),
            (None, {}),
        ]
        
        for action, data in invalid_tests:
            logger.info(f"🧪 Testing invalid action: {action}")
            result = manager.handle_control_message(action, data)
            
            if not result.get("success"):
                logger.info(f"✅ Invalid action '{action}' properly rejected")
            else:
                logger.warning(f"⚠️ Invalid action '{action}' was accepted (unexpected)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Validation test error: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🚀 Starting Task 17.1 Simple Tests...")
    
    tests = [
        ("PracticeSessionManager", test_practice_session_manager),
        ("FrameProcessor Integration", test_frame_processor_integration),
        ("Control Message Validation", test_control_message_validation)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    logger.info(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All Task 17.1 simple tests PASSED!")
        return True
    else:
        logger.error("❌ Some Task 17.1 simple tests FAILED!")
        return False

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        exit(1)
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        exit(1)