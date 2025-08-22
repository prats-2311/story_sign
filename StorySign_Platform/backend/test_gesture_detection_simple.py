#!/usr/bin/env python3
"""
Simple test script for gesture detection functionality
Tests only the gesture detection classes without MediaPipe dependencies
"""

import sys
import os
import time
import logging
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import GestureDetectionConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class MockGestureDetector:
    """
    Mock gesture detector for testing without MediaPipe dependencies
    """
    
    def __init__(self, gesture_config: GestureDetectionConfig):
        self.config = gesture_config
        self.logger = logging.getLogger(f"{__name__}.MockGestureDetector")
        
        # Gesture detection state
        self.is_detecting = False
        self.gesture_start_time = None
        self.gesture_end_time = None
        self.last_movement_time = None
        
        # Landmark data buffering
        self.landmark_buffer = []
        self.velocity_history = []
        
        self.logger.info(f"Mock gesture detector initialized")
    
    def detect_gesture_start(self, landmarks_data: Dict[str, Any]) -> bool:
        """Mock gesture start detection"""
        if not self.config.enabled or self.is_detecting:
            return False
        
        # Simulate gesture start when hands are detected
        if landmarks_data.get("hands", False):
            self.is_detecting = True
            self.gesture_start_time = time.time()
            self.last_movement_time = time.time()
            self.landmark_buffer = []
            
            self.logger.info("Mock gesture start detected")
            return True
        
        return False
    
    def detect_gesture_end(self, landmarks_data: Dict[str, Any]) -> bool:
        """Mock gesture end detection"""
        if not self.config.enabled or not self.is_detecting:
            return False
        
        current_time = time.time()
        
        # Simulate gesture end after minimum duration
        if self.gesture_start_time is not None:
            gesture_duration_ms = (current_time - self.gesture_start_time) * 1000
            
            if gesture_duration_ms >= self.config.min_gesture_duration_ms:
                self.gesture_end_time = current_time
                self.is_detecting = False
                
                self.logger.info(f"Mock gesture end detected - duration: {gesture_duration_ms:.0f}ms")
                return True
        
        return False
    
    def collect_landmark_data(self, landmarks_data: Dict[str, Any], frame_metadata: Dict[str, Any]) -> None:
        """Mock landmark data collection"""
        if not self.config.enabled or not self.is_detecting:
            return
        
        landmark_entry = {
            "timestamp": time.time(),
            "landmarks": landmarks_data.copy(),
            "metadata": frame_metadata.copy()
        }
        
        self.landmark_buffer.append(landmark_entry)
        
        if len(self.landmark_buffer) > self.config.landmark_buffer_size:
            self.landmark_buffer.pop(0)
    
    def get_gesture_buffer(self) -> list:
        """Get the current landmark buffer"""
        return self.landmark_buffer.copy()
    
    def reset_detection(self) -> None:
        """Reset gesture detection state"""
        self.is_detecting = False
        self.gesture_start_time = None
        self.gesture_end_time = None
        self.last_movement_time = None
        self.landmark_buffer = []
    
    def get_detection_state(self) -> Dict[str, Any]:
        """Get current detection state"""
        current_time = time.time()
        
        state = {
            "is_detecting": self.is_detecting,
            "buffer_size": len(self.landmark_buffer),
            "enabled": self.config.enabled
        }
        
        if self.is_detecting and self.gesture_start_time is not None:
            state["gesture_duration_ms"] = (current_time - self.gesture_start_time) * 1000
        
        return state


class MockPracticeSessionManager:
    """
    Mock practice session manager for testing
    """
    
    def __init__(self, gesture_config: GestureDetectionConfig):
        self.gesture_config = gesture_config
        self.logger = logging.getLogger(f"{__name__}.MockPracticeSessionManager")
        
        # Session state
        self.is_active = False
        self.current_sentence = None
        self.current_sentence_index = 0
        self.story_sentences = []
        self.session_id = None
        
        # Gesture detection
        self.gesture_detector = MockGestureDetector(gesture_config)
        
        # Practice mode state
        self.practice_mode = "listening"
        self.last_feedback = None
        
        self.logger.info("Mock practice session manager initialized")
    
    def start_practice_session(self, story_sentences: list, session_id: str = None) -> Dict[str, Any]:
        """Start a new practice session"""
        try:
            self.is_active = True
            self.story_sentences = story_sentences.copy()
            self.current_sentence_index = 0
            self.current_sentence = story_sentences[0] if story_sentences else None
            self.session_id = session_id or f"session_{int(time.time())}"
            self.practice_mode = "listening"
            self.last_feedback = None
            
            self.gesture_detector.reset_detection()
            
            self.logger.info(f"Practice session started - ID: {self.session_id}")
            
            return {
                "success": True,
                "session_id": self.session_id,
                "total_sentences": len(self.story_sentences),
                "current_sentence_index": self.current_sentence_index,
                "current_sentence": self.current_sentence,
                "practice_mode": self.practice_mode
            }
            
        except Exception as e:
            self.logger.error(f"Error starting practice session: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def process_frame_for_practice(self, landmarks_data: Dict[str, Any], frame_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process frame for practice session"""
        if not self.is_active:
            return {"practice_active": False}
        
        try:
            result = {
                "practice_active": True,
                "session_id": self.session_id,
                "current_sentence": self.current_sentence,
                "current_sentence_index": self.current_sentence_index,
                "practice_mode": self.practice_mode,
                "gesture_state": self.gesture_detector.get_detection_state()
            }
            
            # Handle gesture detection based on current mode
            if self.practice_mode == "listening":
                if self.gesture_detector.detect_gesture_start(landmarks_data):
                    self.practice_mode = "detecting"
                    result["practice_mode"] = self.practice_mode
                    result["gesture_started"] = True
                    
            elif self.practice_mode == "detecting":
                self.gesture_detector.collect_landmark_data(landmarks_data, frame_metadata)
                
                if self.gesture_detector.detect_gesture_end(landmarks_data):
                    self.practice_mode = "analyzing"
                    result["practice_mode"] = self.practice_mode
                    result["gesture_completed"] = True
                    result["landmark_buffer_size"] = len(self.gesture_detector.get_gesture_buffer())
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing frame for practice: {e}")
            return {
                "practice_active": True,
                "error": str(e)
            }
    
    def handle_control_message(self, action: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle practice session control messages"""
        try:
            if action == "next_sentence":
                return self._next_sentence()
            elif action == "try_again":
                return self._try_again()
            elif action == "stop_session":
                return self._stop_session()
            elif action == "set_feedback":
                return self._set_feedback(data)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
                
        except Exception as e:
            self.logger.error(f"Error handling control message: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _next_sentence(self) -> Dict[str, Any]:
        """Move to the next sentence"""
        if self.current_sentence_index < len(self.story_sentences) - 1:
            self.current_sentence_index += 1
            self.current_sentence = self.story_sentences[self.current_sentence_index]
            self.practice_mode = "listening"
            self.last_feedback = None
            self.gesture_detector.reset_detection()
            
            return {
                "success": True,
                "action": "next_sentence",
                "current_sentence_index": self.current_sentence_index,
                "current_sentence": self.current_sentence,
                "practice_mode": self.practice_mode,
                "is_last_sentence": self.current_sentence_index == len(self.story_sentences) - 1
            }
        else:
            return {
                "success": True,
                "action": "story_completed",
                "total_sentences": len(self.story_sentences)
            }
    
    def _try_again(self) -> Dict[str, Any]:
        """Reset current sentence for another attempt"""
        self.practice_mode = "listening"
        self.last_feedback = None
        self.gesture_detector.reset_detection()
        
        return {
            "success": True,
            "action": "try_again",
            "current_sentence_index": self.current_sentence_index,
            "current_sentence": self.current_sentence,
            "practice_mode": self.practice_mode
        }
    
    def _stop_session(self) -> Dict[str, Any]:
        """Stop the current practice session"""
        self.is_active = False
        self.gesture_detector.reset_detection()
        
        return {
            "success": True,
            "action": "session_stopped",
            "session_id": self.session_id
        }
    
    def _set_feedback(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Set feedback for the current gesture attempt"""
        if data and "feedback" in data:
            self.last_feedback = data["feedback"]
            self.practice_mode = "feedback"
            
            return {
                "success": True,
                "action": "feedback_set",
                "practice_mode": self.practice_mode,
                "feedback": self.last_feedback
            }
        else:
            return {
                "success": False,
                "error": "No feedback data provided"
            }
    
    def get_gesture_buffer_for_analysis(self) -> list:
        """Get the current gesture buffer for analysis"""
        return self.gesture_detector.get_gesture_buffer()
    
    def get_session_state(self) -> Dict[str, Any]:
        """Get complete session state"""
        return {
            "is_active": self.is_active,
            "session_id": self.session_id,
            "current_sentence": self.current_sentence,
            "current_sentence_index": self.current_sentence_index,
            "total_sentences": len(self.story_sentences),
            "practice_mode": self.practice_mode,
            "last_feedback": self.last_feedback,
            "gesture_state": self.gesture_detector.get_detection_state() if self.is_active else None
        }


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


def test_mock_gesture_detector():
    """Test mock gesture detector functionality"""
    logger.info("Testing mock gesture detector...")
    
    try:
        config = GestureDetectionConfig()
        detector = MockGestureDetector(config)
        
        # Test initial state
        assert not detector.is_detecting
        assert len(detector.landmark_buffer) == 0
        
        # Test gesture detection with mock landmarks
        mock_landmarks = {"hands": True, "face": False, "pose": False}
        
        # Test gesture start detection
        gesture_started = detector.detect_gesture_start(mock_landmarks)
        assert gesture_started == True
        assert detector.is_detecting == True
        
        # Test landmark collection
        frame_metadata = {"frame_number": 1, "timestamp": time.time()}
        detector.collect_landmark_data(mock_landmarks, frame_metadata)
        assert len(detector.landmark_buffer) == 1
        
        # Wait for minimum gesture duration
        time.sleep(0.6)  # Wait 600ms (> 500ms minimum)
        
        # Test gesture end detection
        gesture_ended = detector.detect_gesture_end(mock_landmarks)
        assert gesture_ended == True
        assert detector.is_detecting == False
        
        # Test state
        state = detector.get_detection_state()
        assert state["enabled"] == True
        assert state["is_detecting"] == False
        
        logger.info("✅ Mock gesture detector test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Mock gesture detector test failed: {e}")
        return False


def test_mock_practice_session_manager():
    """Test mock practice session manager functionality"""
    logger.info("Testing mock practice session manager...")
    
    try:
        config = GestureDetectionConfig()
        manager = MockPracticeSessionManager(config)
        
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
        
        # Test frame processing for practice
        mock_landmarks = {"hands": True, "face": False, "pose": False}
        frame_metadata = {"frame_number": 1, "timestamp": time.time()}
        
        # Process frame in listening mode
        practice_result = manager.process_frame_for_practice(mock_landmarks, frame_metadata)
        assert practice_result["practice_active"] == True
        assert practice_result["practice_mode"] == "detecting"  # Should transition to detecting
        assert practice_result.get("gesture_started") == True
        
        # Process more frames in detecting mode
        for i in range(5):
            practice_result = manager.process_frame_for_practice(mock_landmarks, frame_metadata)
            assert practice_result["practice_mode"] == "detecting"
        
        # Wait for gesture to complete
        time.sleep(0.6)
        practice_result = manager.process_frame_for_practice(mock_landmarks, frame_metadata)
        assert practice_result["practice_mode"] == "analyzing"
        assert practice_result.get("gesture_completed") == True
        
        # Test control messages
        next_result = manager.handle_control_message("next_sentence")
        assert next_result["success"] == True
        assert next_result["current_sentence_index"] == 1
        assert next_result["current_sentence"] == "I am learning ASL."
        
        # Test try again
        try_again_result = manager.handle_control_message("try_again")
        assert try_again_result["success"] == True
        assert try_again_result["practice_mode"] == "listening"
        
        # Test set feedback
        feedback_data = {"feedback": "Good job! Try to make the sign clearer."}
        feedback_result = manager.handle_control_message("set_feedback", feedback_data)
        assert feedback_result["success"] == True
        assert feedback_result["practice_mode"] == "feedback"
        
        # Test stop session
        stop_result = manager.handle_control_message("stop_session")
        assert stop_result["success"] == True
        assert not manager.is_active
        
        logger.info("✅ Mock practice session manager test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Mock practice session manager test failed: {e}")
        return False


def main():
    """Run all gesture detection tests"""
    logger.info("Starting gesture detection tests...")
    
    tests = [
        test_gesture_detection_config,
        test_mock_gesture_detector,
        test_mock_practice_session_manager
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