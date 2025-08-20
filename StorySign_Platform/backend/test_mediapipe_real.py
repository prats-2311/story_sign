#!/usr/bin/env python3
"""
Test real MediaPipe installation
"""

import numpy as np
import cv2

def test_mediapipe_import():
    """Test MediaPipe import and basic functionality"""
    try:
        import mediapipe as mp
        print(f"✅ MediaPipe imported successfully - Version: {mp.__version__}")
        
        # Test MediaPipe Holistic initialization
        mp_holistic = mp.solutions.holistic
        mp_drawing = mp.solutions.drawing_utils
        
        holistic = mp_holistic.Holistic(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1
        )
        
        print("✅ MediaPipe Holistic model initialized successfully")
        
        # Test with a dummy frame
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        rgb_frame = cv2.cvtColor(test_frame, cv2.COLOR_BGR2RGB)
        
        results = holistic.process(rgb_frame)
        print("✅ MediaPipe processing test completed")
        
        # Check results structure
        has_pose = hasattr(results, 'pose_landmarks')
        has_hands = hasattr(results, 'left_hand_landmarks') and hasattr(results, 'right_hand_landmarks')
        has_face = hasattr(results, 'face_landmarks')
        
        print(f"✅ Results structure - Pose: {has_pose}, Hands: {has_hands}, Face: {has_face}")
        
        holistic.close()
        print("✅ MediaPipe Holistic model closed successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ MediaPipe import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ MediaPipe test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_mediapipe_import()
    if success:
        print("\n🎉 MediaPipe is working perfectly!")
    else:
        print("\n❌ MediaPipe test failed")