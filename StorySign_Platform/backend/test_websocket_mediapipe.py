#!/usr/bin/env python3
"""
Test WebSocket with MediaPipe directly
"""

import asyncio
import websockets
import json
import base64
import cv2
import numpy as np

async def test_websocket_with_mediapipe():
    """Test WebSocket connection with MediaPipe processing"""
    
    # Create a test frame with a person-like shape
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Draw a simple person figure
    # Head
    cv2.circle(frame, (320, 100), 40, (255, 220, 177), -1)  # Skin color head
    
    # Body
    cv2.rectangle(frame, (290, 140), (350, 280), (0, 100, 200), -1)  # Blue shirt
    
    # Arms
    cv2.rectangle(frame, (250, 160), (290, 200), (255, 220, 177), -1)  # Left arm
    cv2.rectangle(frame, (350, 160), (390, 200), (255, 220, 177), -1)  # Right arm
    
    # Hands
    cv2.circle(frame, (270, 180), 15, (255, 220, 177), -1)  # Left hand
    cv2.circle(frame, (370, 180), 15, (255, 220, 177), -1)  # Right hand
    
    # Legs
    cv2.rectangle(frame, (300, 280), (320, 380), (0, 0, 100), -1)  # Left leg
    cv2.rectangle(frame, (320, 280), (340, 380), (0, 0, 100), -1)  # Right leg
    
    # Encode frame
    _, buffer = cv2.imencode('.jpg', frame)
    base64_data = base64.b64encode(buffer).decode('utf-8')
    data_url = f"data:image/jpeg;base64,{base64_data}"
    
    print(f"🎨 Created test frame with person figure")
    
    try:
        uri = "ws://localhost:8000/ws/video"
        print(f"🔌 Connecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected")
            
            # Send frame processing message
            message = {
                "type": "raw_frame",
                "frame_data": data_url,
                "metadata": {
                    "frame_number": 1,
                    "timestamp": "2025-08-20T12:00:00.000Z"
                }
            }
            
            print("📤 Sending frame for processing...")
            await websocket.send(json.dumps(message))
            
            # Wait for response
            print("⏳ Waiting for response...")
            response = await websocket.recv()
            result = json.loads(response)
            
            print(f"📥 Received response:")
            print(f"   Type: {result.get('type')}")
            
            if result.get('type') == 'processed_frame':
                metadata = result.get('metadata', {})
                landmarks = metadata.get('landmarks_detected', {})
                processing_time = metadata.get('processing_time_ms', 0)
                
                print(f"   🎯 Landmarks detected: {landmarks}")
                print(f"   ⏱️  Processing time: {processing_time}ms")
                print(f"   ✅ Success: {metadata.get('success', False)}")
                
                # Check if any landmarks were detected
                any_detected = any(landmarks.values()) if landmarks else False
                if any_detected:
                    print("🎉 MediaPipe is working! Landmarks detected!")
                else:
                    print("ℹ️  No landmarks detected (might be normal for simple shapes)")
                    
            elif result.get('type') == 'error':
                print(f"   ❌ Error: {result.get('message')}")
            
            print("🔌 Closing connection...")
            
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket_with_mediapipe())