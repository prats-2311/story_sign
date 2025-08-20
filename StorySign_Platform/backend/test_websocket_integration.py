#!/usr/bin/env python3
"""
Test WebSocket integration with MediaPipe processing
"""

import asyncio
import websockets
import json
import base64
import cv2
import numpy as np
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_test_frame() -> str:
    """Create a test frame and encode it as base64"""
    # Create a simple test frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add some colored shapes
    cv2.circle(frame, (320, 240), 50, (255, 100, 100), -1)  # Red circle
    cv2.rectangle(frame, (200, 200), (440, 280), (100, 255, 100), 2)  # Green rectangle
    
    # Encode as JPEG
    _, buffer = cv2.imencode('.jpg', frame)
    base64_data = base64.b64encode(buffer).decode('utf-8')
    
    return f"data:image/jpeg;base64,{base64_data}"


async def test_websocket_connection():
    """Test WebSocket connection and frame processing"""
    uri = "ws://localhost:8000/ws/video"
    
    try:
        logger.info("Connecting to WebSocket...")
        async with websockets.connect(uri) as websocket:
            logger.info("✅ WebSocket connection established")
            
            # Create test frame
            test_frame_data = create_test_frame()
            logger.info(f"Created test frame: {len(test_frame_data)} characters")
            
            # Send frame processing message
            message = {
                "type": "raw_frame",
                "frame_data": test_frame_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info("Sending frame processing message...")
            await websocket.send(json.dumps(message))
            
            # Wait for response
            logger.info("Waiting for response...")
            response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            
            # Parse response
            response_data = json.loads(response)
            logger.info(f"Received response type: {response_data.get('type')}")
            
            if response_data.get('type') == 'processed_frame':
                metadata = response_data.get('metadata', {})
                logger.info(f"✅ Frame processed successfully!")
                logger.info(f"   Processing time: {metadata.get('processing_time_ms', 'N/A')}ms")
                logger.info(f"   Landmarks detected: {metadata.get('landmarks_detected', 'N/A')}")
                logger.info(f"   Frame number: {metadata.get('frame_number', 'N/A')}")
                logger.info(f"   Output frame size: {len(response_data.get('frame_data', ''))} characters")
                return True
            elif response_data.get('type') == 'error':
                logger.error(f"❌ Server returned error: {response_data.get('message')}")
                return False
            else:
                logger.error(f"❌ Unexpected response type: {response_data.get('type')}")
                return False
                
    except asyncio.TimeoutError:
        logger.error("❌ Timeout waiting for response")
        return False
    except websockets.exceptions.ConnectionRefused:
        logger.error("❌ Connection refused - is the server running?")
        return False
    except Exception as e:
        logger.error(f"❌ WebSocket test failed: {e}")
        return False


async def main():
    """Run WebSocket integration test"""
    logger.info("Starting WebSocket integration test...")
    logger.info("Make sure the backend server is running on localhost:8000")
    
    success = await test_websocket_connection()
    
    if success:
        logger.info("🎉 WebSocket integration test passed!")
        return 0
    else:
        logger.error("❌ WebSocket integration test failed!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)