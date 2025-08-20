#!/usr/bin/env python3
"""
Debug live landmark detection
"""

import asyncio
import websockets
import json
import time

async def monitor_landmarks():
    """Monitor live landmark detection"""
    uri = "ws://localhost:8000/ws/video"
    
    try:
        print("🔌 Connecting to WebSocket for live monitoring...")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected! Monitoring landmark detection...")
            print("📊 Waiting for processed frames...")
            
            frame_count = 0
            while frame_count < 10:  # Monitor 10 frames
                try:
                    # Wait for any message from server
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    result = json.loads(response)
                    
                    if result.get('type') == 'processed_frame':
                        frame_count += 1
                        metadata = result.get('metadata', {})
                        landmarks = metadata.get('landmarks_detected', {})
                        processing_time = metadata.get('processing_time_ms', 0)
                        success = metadata.get('success', False)
                        
                        print(f"\n📊 Frame {frame_count}:")
                        print(f"   ✅ Success: {success}")
                        print(f"   🎯 Landmarks: {landmarks}")
                        print(f"   ⏱️  Time: {processing_time}ms")
                        
                        # Check if any landmarks detected
                        any_detected = any(landmarks.values()) if landmarks else False
                        if any_detected:
                            print("   🎉 LANDMARKS DETECTED!")
                        else:
                            print("   ❌ No landmarks detected")
                            
                except asyncio.TimeoutError:
                    print("⏰ No frames received in 5 seconds")
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")
                    break
            
            print("\n🏁 Monitoring complete")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(monitor_landmarks())