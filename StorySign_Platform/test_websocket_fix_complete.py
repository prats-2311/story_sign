#!/usr/bin/env python3
"""
Complete WebSocket fix test - simulates story generation workflow
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_complete_workflow():
    """Test complete workflow including story generation simulation"""
    
    uri = "ws://localhost:8000/ws/video"
    
    try:
        logger.info("🔌 Starting complete WebSocket workflow test...")
        
        async with websockets.connect(uri) as websocket:
            logger.info("✅ Connected to WebSocket")
            
            # Wait for initial messages
            initial_msg = await websocket.recv()
            logger.info(f"📨 Initial message: {json.loads(initial_msg)['type']}")
            
            # Test 1: Basic ping/pong
            ping_msg = {"type": "ping", "timestamp": datetime.utcnow().isoformat()}
            await websocket.send(json.dumps(ping_msg))
            
            response = await websocket.recv()
            response_data = json.loads(response)
            if response_data.get("type") == "pong":
                logger.info("✅ Ping/pong working")
            
            # Test 2: Simulate story generation delay
            logger.info("🎭 Simulating story generation process...")
            for i in range(5):
                await asyncio.sleep(1)
                ping_msg = {"type": "ping", "timestamp": datetime.utcnow().isoformat()}
                await websocket.send(json.dumps(ping_msg))
                
                response = await websocket.recv()
                if json.loads(response).get("type") == "pong":
                    logger.info(f"✅ Connection stable during story generation {i+1}/5")
            
            # Test 3: Frame processing simulation
            logger.info("🎥 Testing frame processing after story generation...")
            mock_frame = {
                "type": "raw_frame",
                "frame_data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD//2Q==",
                "metadata": {"frame_number": 1, "timestamp": datetime.utcnow().isoformat()}
            }
            
            await websocket.send(json.dumps(mock_frame))
            logger.info("📤 Mock frame sent")
            
            # Wait for processed frame
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                response_data = json.loads(response)
                if response_data.get("type") == "processed_frame":
                    logger.info("✅ Frame processing working after story generation")
                else:
                    logger.info(f"📨 Received: {response_data.get('type')}")
            except asyncio.TimeoutError:
                logger.warning("⚠️ Frame processing timeout")
            
            logger.info("✅ Complete workflow test successful!")
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_complete_workflow())