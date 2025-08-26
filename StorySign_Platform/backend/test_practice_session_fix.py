#!/usr/bin/env python3
"""
Test the practice session fix for the AI feedback modal issue
"""

import asyncio
import logging
from video_processor import PracticeSessionManager, GestureDetectionConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_practice_session_start():
    """Test that practice session can be started properly"""
    logger.info("Testing practice session start functionality...")
    
    try:
        # Create gesture detection config
        gesture_config = GestureDetectionConfig()
        
        # Create practice session manager
        practice_manager = PracticeSessionManager(gesture_config)
        
        # Test data similar to what comes from frontend
        test_control_data = {
            'story_sentences': ['Boy hold phone screen.', 'Phone screen bright.', 'Boy watch screen.'],
            'session_id': 'test_session_123',
            'story_title': 'The Phone Screen Story'
        }
        
        # Test 1: Direct method call (should work)
        logger.info("Test 1: Direct start_practice_session method")
        result1 = practice_manager.start_practice_session(
            test_control_data['story_sentences'], 
            test_control_data['session_id']
        )
        logger.info(f"Direct method result: {result1}")
        assert result1['success'] == True, "Direct method should succeed"
        
        # Reset for next test
        practice_manager.is_active = False
        
        # Test 2: Control message handler (should work after fix)
        logger.info("Test 2: handle_control_message method")
        result2 = practice_manager.handle_control_message("start_session", test_control_data)
        logger.info(f"Control message result: {result2}")
        assert result2['success'] == True, "Control message handler should succeed"
        
        # Test 3: Verify session state
        logger.info("Test 3: Session state verification")
        session_state = practice_manager.get_session_state()
        logger.info(f"Session state: {session_state}")
        assert session_state['is_active'] == True, "Session should be active"
        assert session_state['current_sentence'] == 'Boy hold phone screen.', "First sentence should be current"
        assert session_state['practice_mode'] == 'listening', "Should be in listening mode"
        
        # Test 4: Control actions
        logger.info("Test 4: Control actions")
        
        # Test try_again
        try_again_result = practice_manager.handle_control_message("try_again", {})
        logger.info(f"Try again result: {try_again_result}")
        assert try_again_result['success'] == True, "Try again should succeed"
        
        # Test next_sentence
        next_result = practice_manager.handle_control_message("next_sentence", {})
        logger.info(f"Next sentence result: {next_result}")
        assert next_result['success'] == True, "Next sentence should succeed"
        assert next_result['current_sentence'] == 'Phone screen bright.', "Should move to second sentence"
        
        # Test stop_session
        stop_result = practice_manager.handle_control_message("stop_session", {})
        logger.info(f"Stop session result: {stop_result}")
        assert stop_result['success'] == True, "Stop session should succeed"
        
        logger.info("✅ All practice session tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Practice session test failed: {e}")
        return False


async def test_gesture_detection_workflow():
    """Test the gesture detection workflow"""
    logger.info("Testing gesture detection workflow...")
    
    try:
        # Create gesture detection config
        gesture_config = GestureDetectionConfig()
        
        # Create practice session manager
        practice_manager = PracticeSessionManager(gesture_config)
        
        # Start a session
        test_control_data = {
            'story_sentences': ['Test sentence'],
            'session_id': 'test_workflow_123'
        }
        
        start_result = practice_manager.handle_control_message("start_session", test_control_data)
        assert start_result['success'] == True, "Session should start"
        
        # Test initial state
        state = practice_manager.get_session_state()
        assert state['practice_mode'] == 'listening', "Should start in listening mode"
        
        # Test mock frame processing
        mock_landmarks = {
            'hand_landmarks': None,  # No hands detected initially
            'pose_landmarks': None,
            'face_landmarks': None
        }
        
        mock_frame_metadata = {
            'timestamp': 1234567890,
            'frame_number': 1
        }
        
        # Process frame (should remain in listening mode with no hands)
        frame_result = practice_manager.process_frame_for_practice(mock_landmarks, mock_frame_metadata)
        logger.info(f"Frame processing result: {frame_result}")
        
        assert frame_result['practice_active'] == True, "Practice should be active"
        assert frame_result['practice_mode'] == 'listening', "Should remain in listening mode"
        
        logger.info("✅ Gesture detection workflow test passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Gesture detection workflow test failed: {e}")
        return False


async def main():
    """Run all practice session tests"""
    logger.info("🚀 Starting practice session fix tests...")
    
    tests = [
        ("Practice Session Start", test_practice_session_start),
        ("Gesture Detection Workflow", test_gesture_detection_workflow),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} ---")
        try:
            if await test_func():
                logger.info(f"✅ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} FAILED")
                failed += 1
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {e}")
            failed += 1
    
    logger.info(f"\n🏁 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("🎉 Practice session fix verified successfully!")
        logger.info("\n📋 Summary:")
        logger.info("✅ Practice session can be started via control messages")
        logger.info("✅ All control actions work properly")
        logger.info("✅ Session state management is functional")
        logger.info("✅ Gesture detection workflow is ready")
        logger.info("\n🔧 The AI feedback modal should now appear after signing!")
        return 0
    else:
        logger.error("💥 Some tests failed!")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))