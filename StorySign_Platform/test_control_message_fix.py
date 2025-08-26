#!/usr/bin/env python3
"""
Test control message handling fix
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_control_messages():
    """Test control message handling"""
    
    uri = "ws://localhost:8000/ws/video"
    
    try:
        logger.info("🔌 Testing control message handling...")
        
        async with websockets.connect(uri) as websocket:
            logger.info("✅ Connected to WebSocket")
            
            # Wait for initial messages
            initial_msg = await websocket.recv()
            logger.info(f"📨 Initial message: {json.loads(initial_msg)['type']}")
            
            # Test 1: Send start_session control message
            logger.info("🎭 Testing start_session control message...")
            start_session_msg = {
                "type": "control",
                "action": "start_session",
                "data": {
                    "story_sentences": ["Dog run fast.", "Dog bring ball back."],
                    "session_id": "test_session_123",
                    "story_title": "Dog Story"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await websocket.send(json.dumps(start_session_msg))
            logger.info("📤 Start session message sent")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                logger.info(f"📨 Response type: {response_data.get('type')}")
                logger.info(f"📨 Response: {response_data}")
                
                if response_data.get("type") == "practice_session_response":
                    logger.info("✅ Start session control message handled correctly")
                else:
                    logger.warning(f"⚠️ Unexpected response type: {response_data.get('type')}")
                    
            except asyncio.TimeoutError:
                logger.warning("⚠️ No response to start session message")
            
            # Test 2: Send next_sentence control message
            logger.info("🎭 Testing next_sentence control message...")
            next_sentence_msg = {
                "type": "control",
                "action": "next_sentence",
                "data": {
                    "sentence_index": 1,
                    "target_sentence": "Dog bring ball back."
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await websocket.send(json.dumps(next_sentence_msg))
            logger.info("📤 Next sentence message sent")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                logger.info(f"📨 Response type: {response_data.get('type')}")
                
                if response_data.get("type") == "control_response":
                    logger.info("✅ Next sentence control message handled correctly")
                else:
                    logger.warning(f"⚠️ Unexpected response type: {response_data.get('type')}")
                    
            except asyncio.TimeoutError:
                logger.warning("⚠️ No response to next sentence message")
            
            logger.info("✅ Control message test completed!")
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_control_messages())