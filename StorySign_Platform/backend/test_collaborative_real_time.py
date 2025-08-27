"""
Test script for real-time collaborative features
Tests WebSocket connections, session management, and peer interactions
"""

import asyncio
import json
import websockets
import requests
import time
from datetime import datetime
from typing import List, Dict, Any

# Test configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"
TEST_USERS = [
    {"user_id": "user_1", "username": "Alice"},
    {"user_id": "user_2", "username": "Bob"},
    {"user_id": "user_3", "username": "Charlie"}
]


class CollaborativeTestClient:
    """Test client for collaborative sessions"""
    
    def __init__(self, user_id: str, username: str):
        self.user_id = user_id
        self.username = username
        self.websocket = None
        self.messages_received = []
        self.connected = False
    
    async def connect_to_session(self, session_id: str):
        """Connect to a collaborative session"""
        ws_url = f"{WS_URL}/api/collaborative/ws/collaborative/{session_id}?user_id={self.user_id}&username={self.username}"
        
        try:
            self.websocket = await websockets.connect(ws_url)
            self.connected = True
            print(f"✓ {self.username} connected to session {session_id}")
            
            # Start listening for messages
            asyncio.create_task(self._listen_for_messages())
            
        except Exception as e:
            print(f"✗ {self.username} failed to connect: {e}")
            self.connected = False
    
    async def _listen_for_messages(self):
        """Listen for incoming WebSocket messages"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                self.messages_received.append(data)
                print(f"📨 {self.username} received: {data['type']}")
                
                # Handle specific message types
                if data['type'] == 'session_state':
                    print(f"   Session state: {data['state']['session_status']}")
                elif data['type'] == 'participant_joined':
                    print(f"   {data['username']} joined the session")
                elif data['type'] == 'practice_started':
                    print(f"   Practice started with story: {data['story_content']['title'] if 'title' in data['story_content'] else 'Untitled'}")
                elif data['type'] == 'peer_feedback_received':
                    print(f"   Received feedback from {data['from_user_id']}: {data['message']}")
                elif data['type'] == 'chat_message':
                    print(f"   Chat from {data['from_user_id']}: {data['message']}")
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"🔌 {self.username} disconnected")
            self.connected = False
        except Exception as e:
            print(f"✗ {self.username} message error: {e}")
    
    async def send_message(self, message: Dict[str, Any]):
        """Send a message to the session"""
        if self.websocket and self.connected:
            try:
                await self.websocket.send(json.dumps(message))
                print(f"📤 {self.username} sent: {message['type']}")
            except Exception as e:
                print(f"✗ {self.username} send error: {e}")
    
    async def start_practice(self, story_content: Dict[str, Any]):
        """Start practice session (host only)"""
        await self.send_message({
            "type": "start_practice",
            "story_content": story_content
        })
    
    async def report_sentence_progress(self, sentence_index: int, performance: Dict[str, Any]):
        """Report progress on a sentence"""
        await self.send_message({
            "type": "sentence_progress",
            "sentence_index": sentence_index,
            "performance": performance
        })
    
    async def send_peer_feedback(self, target_user_id: str, feedback_type: str, message: str):
        """Send feedback to another participant"""
        await self.send_message({
            "type": "peer_feedback",
            "target_user_id": target_user_id,
            "feedback_type": feedback_type,
            "message": message
        })
    
    async def send_chat_message(self, message: str):
        """Send a chat message"""
        await self.send_message({
            "type": "chat_message",
            "message": message
        })
    
    async def control_session(self, action: str):
        """Send session control command"""
        await self.send_message({
            "type": "session_control",
            "action": action
        })
    
    async def disconnect(self):
        """Disconnect from the session"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
    
    def get_messages_by_type(self, message_type: str) -> List[Dict[str, Any]]:
        """Get all received messages of a specific type"""
        return [msg for msg in self.messages_received if msg.get('type') == message_type]


async def test_basic_connection():
    """Test basic WebSocket connection to collaborative session"""
    print("\n🧪 Testing basic WebSocket connection...")
    
    session_id = "test_session_1"
    client = CollaborativeTestClient("user_1", "TestUser")
    
    try:
        await client.connect_to_session(session_id)
        
        if client.connected:
            print("✓ Basic connection test passed")
            
            # Wait a moment to receive initial messages
            await asyncio.sleep(2)
            
            # Check if we received session state
            session_states = client.get_messages_by_type('session_state')
            if session_states:
                print("✓ Received session state")
            else:
                print("✗ No session state received")
        
        await client.disconnect()
        
    except Exception as e:
        print(f"✗ Basic connection test failed: {e}")


async def test_multi_user_session():
    """Test multi-user collaborative session"""
    print("\n🧪 Testing multi-user collaborative session...")
    
    session_id = "test_session_multi"
    clients = []
    
    try:
        # Connect multiple users
        for user in TEST_USERS:
            client = CollaborativeTestClient(user["user_id"], user["username"])
            await client.connect_to_session(session_id)
            clients.append(client)
            await asyncio.sleep(1)  # Stagger connections
        
        # Wait for all connections to stabilize
        await asyncio.sleep(3)
        
        # Check that all users are connected
        connected_count = sum(1 for client in clients if client.connected)
        print(f"✓ {connected_count}/{len(TEST_USERS)} users connected")
        
        # Host (first user) starts practice
        story_content = {
            "title": "Test Story",
            "sentences": [
                "Hello, my name is Alice.",
                "I love learning sign language.",
                "Today is a great day to practice.",
                "Let's work together!"
            ]
        }
        
        await clients[0].start_practice(story_content)
        await asyncio.sleep(2)
        
        # Check if practice started message was received
        for i, client in enumerate(clients):
            practice_messages = client.get_messages_by_type('practice_started')
            if practice_messages:
                print(f"✓ {client.username} received practice start")
            else:
                print(f"✗ {client.username} did not receive practice start")
        
        # Simulate sentence progress from different users
        for i, client in enumerate(clients):
            await client.report_sentence_progress(i, {
                "confidence_score": 0.8 + (i * 0.05),
                "completion_time": 5.2 + i,
                "attempts": 1 + i
            })
            await asyncio.sleep(1)
        
        await asyncio.sleep(2)
        
        # Check progress updates
        for client in clients:
            progress_messages = client.get_messages_by_type('participant_progress')
            print(f"✓ {client.username} received {len(progress_messages)} progress updates")
        
        # Test peer feedback
        await clients[1].send_peer_feedback(clients[0].user_id, "encouragement", "Great job! 👍")
        await asyncio.sleep(1)
        
        # Test chat messages
        await clients[2].send_chat_message("This is working great!")
        await asyncio.sleep(1)
        
        # Check feedback and chat
        feedback_received = clients[0].get_messages_by_type('peer_feedback_received')
        if feedback_received:
            print("✓ Peer feedback system working")
        
        for client in clients:
            chat_messages = client.get_messages_by_type('chat_message')
            if chat_messages:
                print(f"✓ {client.username} received chat messages")
        
        # Test session control (pause/resume)
        await clients[0].control_session("pause_session")
        await asyncio.sleep(1)
        
        await clients[0].control_session("resume_session")
        await asyncio.sleep(1)
        
        # Disconnect all clients
        for client in clients:
            await client.disconnect()
        
        print("✓ Multi-user session test completed")
        
    except Exception as e:
        print(f"✗ Multi-user session test failed: {e}")
        # Cleanup
        for client in clients:
            if client.connected:
                await client.disconnect()


async def test_session_synchronization():
    """Test session state synchronization"""
    print("\n🧪 Testing session synchronization...")
    
    session_id = "test_session_sync"
    
    # Create host client
    host = CollaborativeTestClient("host_user", "Host")
    await host.connect_to_session(session_id)
    await asyncio.sleep(1)
    
    # Start practice
    story_content = {
        "title": "Sync Test Story",
        "sentences": ["First sentence", "Second sentence", "Third sentence"]
    }
    await host.start_practice(story_content)
    await asyncio.sleep(2)
    
    # Create late-joining client
    late_joiner = CollaborativeTestClient("late_user", "LateJoiner")
    await late_joiner.connect_to_session(session_id)
    await asyncio.sleep(2)
    
    # Check if late joiner received current session state
    session_states = late_joiner.get_messages_by_type('session_state')
    if session_states:
        state = session_states[0]['state']
        if state['session_status'] == 'active' and state['story_content']:
            print("✓ Late joiner received current session state")
        else:
            print("✗ Late joiner did not receive proper session state")
    else:
        print("✗ Late joiner did not receive session state")
    
    # Test sentence synchronization
    await host.control_session("next_sentence")
    await asyncio.sleep(1)
    
    sentence_changes = late_joiner.get_messages_by_type('sentence_changed')
    if sentence_changes:
        print("✓ Sentence synchronization working")
    else:
        print("✗ Sentence synchronization failed")
    
    await host.disconnect()
    await late_joiner.disconnect()


async def test_error_handling():
    """Test error handling and reconnection"""
    print("\n🧪 Testing error handling...")
    
    session_id = "test_session_error"
    client = CollaborativeTestClient("error_user", "ErrorUser")
    
    try:
        await client.connect_to_session(session_id)
        await asyncio.sleep(1)
        
        # Send invalid message
        if client.websocket:
            await client.websocket.send("invalid json")
            await asyncio.sleep(1)
            
            # Check if we received an error response
            error_messages = client.get_messages_by_type('error')
            if error_messages:
                print("✓ Error handling working - received error response")
            else:
                print("✗ No error response received for invalid JSON")
        
        # Test unknown message type
        await client.send_message({
            "type": "unknown_message_type",
            "data": "test"
        })
        await asyncio.sleep(1)
        
        error_messages = client.get_messages_by_type('error')
        if len(error_messages) > 1:
            print("✓ Unknown message type handling working")
        
        await client.disconnect()
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")


async def test_performance():
    """Test performance with rapid message sending"""
    print("\n🧪 Testing performance with rapid messages...")
    
    session_id = "test_session_perf"
    client = CollaborativeTestClient("perf_user", "PerfUser")
    
    try:
        await client.connect_to_session(session_id)
        await asyncio.sleep(1)
        
        # Send rapid progress updates
        start_time = time.time()
        message_count = 50
        
        for i in range(message_count):
            await client.report_sentence_progress(i % 4, {
                "confidence_score": 0.5 + (i % 10) * 0.05,
                "completion_time": 3.0 + (i % 5),
                "attempts": 1 + (i % 3)
            })
            # Small delay to avoid overwhelming
            await asyncio.sleep(0.01)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✓ Sent {message_count} messages in {duration:.2f} seconds")
        print(f"✓ Rate: {message_count/duration:.1f} messages/second")
        
        # Wait for processing
        await asyncio.sleep(2)
        
        progress_messages = client.get_messages_by_type('participant_progress')
        print(f"✓ Received {len(progress_messages)} progress confirmations")
        
        await client.disconnect()
        
    except Exception as e:
        print(f"✗ Performance test failed: {e}")


def test_rest_api_endpoints():
    """Test REST API endpoints for session management"""
    print("\n🧪 Testing REST API endpoints...")
    
    try:
        # Test session participants endpoint
        session_id = "test_session_api"
        response = requests.get(f"{BASE_URL}/api/collaborative/sessions/{session_id}/participants")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Participants endpoint working: {data['participant_count']} participants")
        else:
            print(f"✗ Participants endpoint failed: {response.status_code}")
        
        # Test session state endpoint
        response = requests.get(f"{BASE_URL}/api/collaborative/sessions/{session_id}/state")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Session state endpoint working")
        else:
            print(f"✗ Session state endpoint failed: {response.status_code}")
        
    except Exception as e:
        print(f"✗ REST API test failed: {e}")


async def run_all_tests():
    """Run all collaborative tests"""
    print("🚀 Starting Collaborative Real-Time Tests")
    print("=" * 50)
    
    # Test REST API first (doesn't require WebSocket server)
    test_rest_api_endpoints()
    
    # WebSocket tests
    await test_basic_connection()
    await test_multi_user_session()
    await test_session_synchronization()
    await test_error_handling()
    await test_performance()
    
    print("\n" + "=" * 50)
    print("🏁 All collaborative tests completed!")


if __name__ == "__main__":
    print("Real-Time Collaborative Features Test Suite")
    print("Make sure the backend server is running on localhost:8000")
    print()
    
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")