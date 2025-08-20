#!/usr/bin/env python3
"""
Simple WebSocket test script to verify the video streaming endpoint
"""

import asyncio
import websockets
import json
import base64
from datetime import datetime

async def test_websocket():
    """Test WebSocket connection and frame sending"""
    uri = "ws://localhost:8000/ws/video"
    
    try:
        print("Connecting to WebSocket...")
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            
            # Send a test frame
            test_message = {
                "type": "raw_frame",
                "timestamp": datetime.utcnow().isoformat(),
                "frame_data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A==",  # 1x1 pixel JPEG
                "metadata": {
                    "frame_number": 1,
                    "client_id": "test_client"
                }
            }
            
            print("Sending test frame...")
            await websocket.send(json.dumps(test_message))
            print("✅ Frame sent successfully!")
            
            # Wait for response
            print("Waiting for response...")
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            response_data = json.loads(response)
            
            print("✅ Received response:")
            print(f"  Type: {response_data.get('type')}")
            print(f"  Frame Number: {response_data.get('metadata', {}).get('frame_number')}")
            print(f"  Processing Time: {response_data.get('metadata', {}).get('processing_time_ms')}ms")
            
            # Send another frame to test continuous operation
            test_message["metadata"]["frame_number"] = 2
            test_message["timestamp"] = datetime.utcnow().isoformat()
            
            print("\nSending second test frame...")
            await websocket.send(json.dumps(test_message))
            
            response2 = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            response_data2 = json.loads(response2)
            
            print("✅ Received second response:")
            print(f"  Frame Number: {response_data2.get('metadata', {}).get('frame_number')}")
            
            print("\n🎉 WebSocket test completed successfully!")
            
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ Connection closed: {e}")
    except asyncio.TimeoutError:
        print("❌ Timeout waiting for response")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("WebSocket Video Streaming Test")
    print("=" * 40)
    asyncio.run(test_websocket())