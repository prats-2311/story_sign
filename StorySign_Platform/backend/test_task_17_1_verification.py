#!/usr/bin/env python3
"""
Test Task 17.1: Practice Session Controls and State Management
Verification test for practice session WebSocket message handling and state synchronization
"""

import asyncio
import json
import logging
import websockets
import pytest
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestPracticeSessionControls:
    """Test practice session control functionality"""
    
    def __init__(self):
        self.websocket_url = "ws://localhost:8000/ws/video"
        self.websocket = None
        
    async def connect_websocket(self):
        """Connect to WebSocket endpoint"""
        try:
            self.websocket = await websockets.connect(self.websocket_url)
            logger.info("✅ Connected to WebSocket")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to WebSocket: {e}")
            return False
    
    async def disconnect_websocket(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            logger.info("✅ Disconnected from WebSocket")
    
    async def send_message(self, message):
        """Send message to WebSocket"""
        try:
            await self.websocket.send(json.dumps(message))
            logger.info(f"📤 Sent message: {message['type']}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
            return False
    
    async def receive_message(self, timeout=5.0):
        """Receive message from WebSocket"""
        try:
            response = await asyncio.wait_for(
                self.websocket.recv(), 
                timeout=timeout
            )
            message = json.loads(response)
            logger.info(f"📥 Received message: {message.get('type', 'unknown')}")
            return message
        except asyncio.TimeoutError:
            logger.warning("⏰ Timeout waiting for message")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to receive message: {e}")
            return None
    
    async def test_practice_session_start(self):
        """Test starting a practice session"""
        logger.info("🧪 Testing practice session start...")
        
        # Send practice session start message
        start_message = {
            "type": "practice_session_start",
            "story_sentences": [
                "The cat sat on the mat.",
                "The dog ran in the park.",
                "The bird flew in the sky."
            ],
            "session_id": f"test_session_{int(datetime.now().timestamp())}"
        }
        
        success = await self.send_message(start_message)
        if not success:
            return False
        
        # Wait for response
        response = await self.receive_message()
        if not response:
            logger.error("❌ No response received for practice session start")
            return False
        
        # Verify response
        if response.get("type") == "practice_session_response":
            if response.get("result", {}).get("success"):
                logger.info("✅ Practice session started successfully")
                return True
            else:
                logger.error(f"❌ Practice session start failed: {response.get('result', {}).get('error')}")
                return False
        else:
            logger.error(f"❌ Unexpected response type: {response.get('type')}")
            return False
    
    async def test_control_messages(self):
        """Test practice control messages"""
        logger.info("🧪 Testing practice control messages...")
        
        # Test "try_again" control
        try_again_message = {
            "type": "control",
            "action": "try_again",
            "data": {
                "sentence_index": 0,
                "target_sentence": "The cat sat on the mat."
            }
        }
        
        success = await self.send_message(try_again_message)
        if not success:
            return False
        
        # Wait for response
        response = await self.receive_message()
        if not response:
            logger.error("❌ No response received for try_again control")
            return False
        
        # Verify response
        if response.get("type") == "control_response":
            if response.get("result", {}).get("success"):
                logger.info("✅ Try again control successful")
            else:
                logger.error(f"❌ Try again control failed: {response.get('result', {}).get('error')}")
                return False
        else:
            logger.error(f"❌ Unexpected response type: {response.get('type')}")
            return False
        
        # Test "next_sentence" control
        next_sentence_message = {
            "type": "control",
            "action": "next_sentence",
            "data": {
                "sentence_index": 0,
                "target_sentence": "The cat sat on the mat."
            }
        }
        
        success = await self.send_message(next_sentence_message)
        if not success:
            return False
        
        # Wait for response
        response = await self.receive_message()
        if not response:
            logger.error("❌ No response received for next_sentence control")
            return False
        
        # Verify response
        if response.get("type") == "control_response":
            if response.get("result", {}).get("success"):
                logger.info("✅ Next sentence control successful")
                return True
            else:
                logger.error(f"❌ Next sentence control failed: {response.get('result', {}).get('error')}")
                return False
        else:
            logger.error(f"❌ Unexpected response type: {response.get('type')}")
            return False
    
    async def test_invalid_control_message(self):
        """Test handling of invalid control messages"""
        logger.info("🧪 Testing invalid control message handling...")
        
        # Send invalid control message (missing action)
        invalid_message = {
            "type": "control",
            "data": {
                "sentence_index": 0
            }
        }
        
        success = await self.send_message(invalid_message)
        if not success:
            return False
        
        # Wait for response
        response = await self.receive_message()
        if not response:
            logger.error("❌ No response received for invalid control")
            return False
        
        # Verify error response
        if response.get("type") == "error":
            logger.info("✅ Invalid control message properly rejected")
            return True
        else:
            logger.error(f"❌ Expected error response, got: {response.get('type')}")
            return False
    
    async def run_all_tests(self):
        """Run all practice session control tests"""
        logger.info("🚀 Starting Task 17.1 verification tests...")
        
        # Connect to WebSocket
        if not await self.connect_websocket():
            return False
        
        try:
            # Run tests
            tests = [
                ("Practice Session Start", self.test_practice_session_start()),
                ("Control Messages", self.test_control_messages()),
                ("Invalid Control Handling", self.test_invalid_control_message())
            ]
            
            results = []
            for test_name, test_coro in tests:
                logger.info(f"\n--- Running {test_name} ---")
                try:
                    result = await test_coro
                    results.append((test_name, result))
                    if result:
                        logger.info(f"✅ {test_name}: PASSED")
                    else:
                        logger.error(f"❌ {test_name}: FAILED")
                except Exception as e:
                    logger.error(f"❌ {test_name}: ERROR - {e}")
                    results.append((test_name, False))
            
            # Summary
            passed = sum(1 for _, result in results if result)
            total = len(results)
            
            logger.info(f"\n📊 Test Results: {passed}/{total} tests passed")
            
            if passed == total:
                logger.info("🎉 All Task 17.1 tests PASSED!")
                return True
            else:
                logger.error("❌ Some Task 17.1 tests FAILED!")
                return False
                
        finally:
            await self.disconnect_websocket()

async def main():
    """Main test function"""
    tester = TestPracticeSessionControls()
    success = await tester.run_all_tests()
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        exit(1)
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        exit(1)