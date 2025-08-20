#!/usr/bin/env python3
"""
Test MediaPipe with real webcam input
"""

import cv2
import numpy as np
from video_processor import FrameProcessor
from config import get_config

def test_webcam_mediapipe():
    """Test MediaPipe with real webcam"""
    print("🎥 Testing MediaPipe with real webcam...")
    
    # Initialize processor
    config = get_config()
    processor = FrameProcessor(config.video, config.mediapipe)
    
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot open webcam")
        return
    
    print("📹 Webcam opened. Press 'q' to quit, 's' to test single frame")
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Cannot read frame")
            break
        
        # Process every 30th frame to avoid spam
        frame_count += 1
        if frame_count % 30 == 0:
            # Process frame through MediaPipe
            processed_frame, landmarks_detected, processing_time = processor.process_frame_with_mediapipe(frame)
            
            print(f"Frame {frame_count}: Landmarks: {landmarks_detected}, Time: {processing_time:.1f}ms")
            
            # Check if any landmarks detected
            any_detected = any(landmarks_detected.values())
            if any_detected:
                print("🎉 LANDMARKS DETECTED! MediaPipe is working with real person!")
        
        # Display frame (optional - comment out if running headless)
        try:
            cv2.imshow('MediaPipe Test', frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                # Test single frame processing
                processed_frame, landmarks_detected, processing_time = processor.process_frame_with_mediapipe(frame)
                print(f"Single frame test: {landmarks_detected}, Time: {processing_time:.1f}ms")
        except:
            # Running headless, just continue
            pass
    
    cap.release()
    cv2.destroyAllWindows()
    processor.close()
    print("🏁 Webcam test completed")

if __name__ == "__main__":
    test_webcam_mediapipe()