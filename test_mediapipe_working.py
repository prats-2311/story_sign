#!/usr/bin/env python3
"""
Test script to verify MediaPipe is working in the backend
"""

import asyncio
import websockets
import json
import base64
import cv2
import numpy as np

async def test_mediapipe_processing():
    """Test MediaPipe processing through WebSocket"""
    
    # Create a simple test image with a person-like shape
    test_image = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Draw a simple stick figure to trigger MediaPipe detection
    # Head (circle)
    cv2.circle(test_image, (320, 100), 30, (255, 255, 255), -1)
    
    # Body (line)
    cv2.line(test_image, (320, 130), (320, 300), (255, 255, 255), 10)
    
    # Arms
    cv2.line(test_image, (320, 180), (250, 220), (255, 255, 255), 8)
    cv2.line(test_image, (320, 180), (390, 220), (255, 255, 255), 8)
    
    # Legs
    cv2.line(test_image, (320, 300), (280, 400), (255, 255, 255), 8)
    cv2.line(test_image, (320, 300), (360, 400), (255, 255, 255), 8)
    
    # Encode image to base64
    _, buffer = cv2.imencode('.jpg', test_image)
    base64_data = base64.b64encode(buffer).decode('utf-8')
    data_url = f"data:image/jpeg;base64,{base64_data}"
    
    # Create test message
    test_message = {
        "type": "raw_frame",
        "frame_data": data_url,
        "metadata": {
            "frame_number": 1,
            "timestamp": "2025-08-20T14:19:00.000Z"
        }
    }
    
    try:
        # Connect to WebSocket
        print("🔌 Connecting to WebSocket...")
        async with websockets.connect("ws://localhost:8000/ws/video") as websocket:
            print("✅ Connected to WebSocket")
            
            # Send test frame
            print("📤 Sending test frame...")
            await websocket.send(json.dumps(test_message))
            
            # Wait for response
            print("⏳ Waiting for response...")
            response = await websocket.recv()
            response_data = json.loads(response)
            
            print("📥 Received response:")
            print(f"  Type: {response_data.get('type')}")
            print(f"  Success: {response_data.get('metadata', {}).get('success', 'N/A')}")
            print(f"  Landmarks detected: {response_data.get('metadata', {}).get('landmarks_detected', 'N/A')}")
            print(f"  Processing time: {response_data.get('metadata', {}).get('processing_time_ms', 'N/A')}ms")
            
            # Check if we got processed frame data
            if response_data.get('frame_data'):
                print("✅ Received processed frame data - MediaPipe is working!")
                
                # Decode and save the processed frame for inspection
                frame_data = response_data['frame_data']
                if frame_data.startswith('data:image/jpeg;base64,'):
                    base64_part = frame_data.split(',', 1)[1]
                    image_bytes = base64.b64decode(base64_part)
                    
                    with open('processed_frame_test.jpg', 'wb') as f:
                        f.write(image_bytes)
                    print("💾 Saved processed frame as 'processed_frame_test.jpg'")
                
            else:
                print("❌ No processed frame data received")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_mediapipe_processing())