#!/usr/bin/env python3
"""
Test real MediaPipe processing with our implementation
"""

import cv2
import numpy as np
import base64
from video_processor import FrameProcessor
from config import get_config

def test_real_processing():
    """Test real MediaPipe processing"""
    print("🧪 Testing real MediaPipe processing...")
    
    # Initialize processor
    config = get_config()
    processor = FrameProcessor(config.video, config.mediapipe)
    
    # Create test frame with some shapes (simulating a person)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add some colored shapes to simulate body parts
    cv2.circle(frame, (320, 150), 30, (255, 200, 150), -1)  # Head (skin color)
    cv2.rectangle(frame, (290, 180), (350, 300), (100, 100, 255), -1)  # Torso (red shirt)
    cv2.circle(frame, (270, 220), 15, (255, 200, 150), -1)  # Left hand
    cv2.circle(frame, (370, 220), 15, (255, 200, 150), -1)  # Right hand
    
    # Encode as base64
    _, buffer = cv2.imencode('.jpg', frame)
    base64_data = base64.b64encode(buffer).decode('utf-8')
    data_url = f"data:image/jpeg;base64,{base64_data}"
    
    print(f"📸 Created test frame: {frame.shape}")
    
    # Process frame
    result = processor.process_base64_frame(data_url, frame_number=1)
    
    print(f"✅ Processing result: {result['success']}")
    if result['success']:
        landmarks = result['landmarks_detected']
        metadata = result['processing_metadata']
        quality = result['quality_metrics']
        
        print(f"🎯 Landmarks detected: {landmarks}")
        print(f"⏱️  Processing time: {metadata['mediapipe_processing_time_ms']:.2f}ms")
        print(f"📊 Confidence: {quality['landmarks_confidence']:.2f}")
        print(f"🚀 Efficiency: {quality['processing_efficiency']:.2f}")
        
        # Check if we got real landmark detection (not mock)
        any_landmarks = any(landmarks.values())
        if any_landmarks:
            print("🎉 Real MediaPipe landmark detection working!")
        else:
            print("ℹ️  No landmarks detected in test frame (expected for simple shapes)")
    else:
        print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
    
    processor.close()
    return result

if __name__ == "__main__":
    test_real_processing()