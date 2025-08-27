"""
Demonstration script for collaborative features
Shows the implemented functionality without requiring a running server
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

# Import our collaborative components
from api.collaborative_websocket import CollaborativeConnectionManager
from services.collaborative_service import CollaborativeService
from models.collaborative import GroupRole, SessionStatus


class CollaborativeDemo:
    """Demonstration of collaborative features"""
    
    def __init__(self):
        self.connection_manager = CollaborativeConnectionManager()
        print("🚀 Collaborative Features Demo")
        print("=" * 50)
    
    def demo_connection_manager(self):
        """Demonstrate connection manager functionality"""
        print("\n📡 Connection Manager Demo")
        print("-" * 30)
        
        # Simulate session state
        session_id = "demo_session_1"
        
        # Add participants to session state
        self.connection_manager.session_states[session_id] = {
            "participants": {
                "user_1": {
                    "username": "Alice",
                    "connected_at": datetime.utcnow().isoformat(),
                    "status": "connected",
                    "current_sentence": 0,
                    "performance": {}
                },
                "user_2": {
                    "username": "Bob", 
                    "connected_at": datetime.utcnow().isoformat(),
                    "status": "connected",
                    "current_sentence": 1,
                    "performance": {"confidence_score": 0.85}
                }
            },
            "session_status": "active",
            "current_sentence": 1,
            "story_content": {
                "title": "Demo Story",
                "sentences": [
                    "Hello, welcome to our collaborative session!",
                    "Let's practice ASL together.",
                    "This is sentence number three.",
                    "Great job everyone!"
                ]
            },
            "practice_data": {},
            "chat_messages": [
                {
                    "type": "chat",
                    "from_user_id": "user_1",
                    "message": "Hello everyone!",
                    "timestamp": datetime.utcnow().isoformat()
                }
            ],
            "peer_feedback": {
                "user_2": [
                    {
                        "from_user_id": "user_1",
                        "feedback_type": "encouragement",
                        "message": "Great job! 👍",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                ]
            }
        }
        
        # Get participants
        participants = self.connection_manager.get_session_participants(session_id)
        print(f"✓ Session has {len(participants)} participants:")
        for participant in participants:
            print(f"  - {participant['username']} (sentence {participant['current_sentence']})")
        
        # Update session state
        self.connection_manager.update_session_state(session_id, {
            "current_sentence": 2,
            "session_status": "active"
        })
        
        print(f"✓ Updated session to sentence 2")
        print(f"✓ Session status: {self.connection_manager.session_states[session_id]['session_status']}")
    
    def demo_message_types(self):
        """Demonstrate different message types"""
        print("\n💬 Message Types Demo")
        print("-" * 30)
        
        # Practice start message
        practice_start = {
            "type": "start_practice",
            "story_content": {
                "title": "Collaborative Practice Story",
                "sentences": [
                    "Welcome to collaborative ASL practice!",
                    "We will practice together as a group.",
                    "Feel free to give each other feedback.",
                    "Let's improve our signing skills!"
                ]
            }
        }
        print(f"✓ Practice Start Message: {practice_start['story_content']['title']}")
        
        # Sentence progress message
        progress_message = {
            "type": "sentence_progress",
            "sentence_index": 1,
            "performance": {
                "confidence_score": 0.92,
                "completion_time": 4.5,
                "attempts": 1,
                "gesture_accuracy": 0.88
            }
        }
        print(f"✓ Progress Message: Sentence {progress_message['sentence_index']} - Score: {progress_message['performance']['confidence_score']}")
        
        # Peer feedback message
        feedback_message = {
            "type": "peer_feedback",
            "target_user_id": "user_2",
            "feedback_type": "encouragement",
            "message": "Excellent hand positioning! 🙌",
            "sentence_index": 1
        }
        print(f"✓ Peer Feedback: {feedback_message['message']}")
        
        # Chat message
        chat_message = {
            "type": "chat_message",
            "message": "This collaborative feature is amazing!"
        }
        print(f"✓ Chat Message: {chat_message['message']}")
        
        # Session control message
        control_message = {
            "type": "session_control",
            "action": "next_sentence"
        }
        print(f"✓ Session Control: {control_message['action']}")
    
    def demo_session_synchronization(self):
        """Demonstrate session synchronization"""
        print("\n🔄 Session Synchronization Demo")
        print("-" * 30)
        
        session_id = "sync_demo_session"
        
        # Initial session state
        initial_state = {
            "session_status": "waiting",
            "participants": {},
            "current_sentence": 0,
            "story_content": None,
            "practice_data": {},
            "chat_messages": [],
            "peer_feedback": {}
        }
        
        self.connection_manager.session_states[session_id] = initial_state
        print("✓ Created initial session state: waiting")
        
        # Simulate host starting practice
        story_content = {
            "title": "Synchronization Test Story",
            "sentences": [
                "First sentence for sync test",
                "Second sentence for sync test", 
                "Third sentence for sync test"
            ]
        }
        
        self.connection_manager.update_session_state(session_id, {
            "session_status": "active",
            "story_content": story_content,
            "started_by": "host_user",
            "started_at": datetime.utcnow().isoformat()
        })
        
        print("✓ Host started practice - session now active")
        print(f"✓ Story: {story_content['title']}")
        
        # Simulate participants joining and making progress
        participants_progress = [
            {"user_id": "user_1", "username": "Alice", "sentence": 1, "score": 0.85},
            {"user_id": "user_2", "username": "Bob", "sentence": 0, "score": 0.78},
            {"user_id": "user_3", "username": "Charlie", "sentence": 2, "score": 0.91}
        ]
        
        session_state = self.connection_manager.session_states[session_id]
        for participant in participants_progress:
            session_state["participants"][participant["user_id"]] = {
                "username": participant["username"],
                "connected_at": datetime.utcnow().isoformat(),
                "status": "connected",
                "current_sentence": participant["sentence"],
                "performance": {"confidence_score": participant["score"]}
            }
        
        print("✓ Added participant progress:")
        for participant in participants_progress:
            print(f"  - {participant['username']}: sentence {participant['sentence']} (score: {participant['score']})")
        
        # Simulate session control - move to next sentence
        self.connection_manager.update_session_state(session_id, {
            "current_sentence": 2
        })
        
        print("✓ Advanced all participants to sentence 2")
    
    def demo_peer_feedback_system(self):
        """Demonstrate peer feedback system"""
        print("\n🤝 Peer Feedback System Demo")
        print("-" * 30)
        
        session_id = "feedback_demo_session"
        
        # Setup session with participants
        self.connection_manager.session_states[session_id] = {
            "participants": {
                "alice": {"username": "Alice", "status": "connected"},
                "bob": {"username": "Bob", "status": "connected"},
                "charlie": {"username": "Charlie", "status": "connected"}
            },
            "peer_feedback": {},
            "session_status": "active"
        }
        
        # Simulate different types of feedback
        feedback_examples = [
            {
                "from": "alice",
                "to": "bob", 
                "type": "encouragement",
                "message": "Great facial expressions! 😊"
            },
            {
                "from": "bob",
                "to": "charlie",
                "type": "suggestion", 
                "message": "Try slowing down the hand movement a bit"
            },
            {
                "from": "charlie",
                "to": "alice",
                "type": "celebration",
                "message": "Perfect signing! 🎉"
            }
        ]
        
        session_state = self.connection_manager.session_states[session_id]
        
        for feedback in feedback_examples:
            # Add feedback to session state
            if feedback["to"] not in session_state["peer_feedback"]:
                session_state["peer_feedback"][feedback["to"]] = []
            
            session_state["peer_feedback"][feedback["to"]].append({
                "from_user_id": feedback["from"],
                "feedback_type": feedback["type"],
                "message": feedback["message"],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            print(f"✓ {feedback['from']} → {feedback['to']}: {feedback['message']}")
        
        # Show feedback summary
        print(f"\n✓ Total feedback exchanges: {sum(len(fb) for fb in session_state['peer_feedback'].values())}")
    
    def demo_chat_system(self):
        """Demonstrate chat system"""
        print("\n💭 Chat System Demo")
        print("-" * 30)
        
        session_id = "chat_demo_session"
        
        # Setup session
        self.connection_manager.session_states[session_id] = {
            "participants": {
                "alice": {"username": "Alice"},
                "bob": {"username": "Bob"},
                "charlie": {"username": "Charlie"}
            },
            "chat_messages": []
        }
        
        # Simulate chat conversation
        chat_conversation = [
            {"from": "alice", "message": "Hello everyone! Ready to practice?"},
            {"from": "bob", "message": "Yes! This story looks interesting."},
            {"from": "charlie", "message": "I'm excited to learn together!"},
            {"from": "alice", "message": "Let's help each other improve 💪"},
            {"from": "bob", "message": "Great idea! Peer feedback is so helpful."}
        ]
        
        session_state = self.connection_manager.session_states[session_id]
        
        for i, chat in enumerate(chat_conversation):
            message = {
                "type": "chat",
                "from_user_id": chat["from"],
                "message": chat["message"],
                "timestamp": datetime.utcnow().isoformat()
            }
            session_state["chat_messages"].append(message)
            print(f"✓ {chat['from']}: {chat['message']}")
        
        print(f"\n✓ Total chat messages: {len(session_state['chat_messages'])}")
    
    def demo_performance_tracking(self):
        """Demonstrate performance tracking"""
        print("\n📊 Performance Tracking Demo")
        print("-" * 30)
        
        session_id = "performance_demo_session"
        
        # Setup session with practice data
        self.connection_manager.session_states[session_id] = {
            "participants": {
                "alice": {"username": "Alice", "current_sentence": 3},
                "bob": {"username": "Bob", "current_sentence": 2},
                "charlie": {"username": "Charlie", "current_sentence": 4}
            },
            "practice_data": {
                "alice": [
                    {"sentence_index": 0, "performance": {"confidence_score": 0.85, "completion_time": 5.2}},
                    {"sentence_index": 1, "performance": {"confidence_score": 0.91, "completion_time": 4.8}},
                    {"sentence_index": 2, "performance": {"confidence_score": 0.88, "completion_time": 5.1}}
                ],
                "bob": [
                    {"sentence_index": 0, "performance": {"confidence_score": 0.78, "completion_time": 6.1}},
                    {"sentence_index": 1, "performance": {"confidence_score": 0.82, "completion_time": 5.9}}
                ],
                "charlie": [
                    {"sentence_index": 0, "performance": {"confidence_score": 0.93, "completion_time": 4.2}},
                    {"sentence_index": 1, "performance": {"confidence_score": 0.89, "completion_time": 4.5}},
                    {"sentence_index": 2, "performance": {"confidence_score": 0.95, "completion_time": 3.9}},
                    {"sentence_index": 3, "performance": {"confidence_score": 0.87, "completion_time": 4.7}}
                ]
            }
        }
        
        session_state = self.connection_manager.session_states[session_id]
        
        # Calculate and display performance metrics
        for user_id, practice_data in session_state["practice_data"].items():
            username = session_state["participants"][user_id]["username"]
            
            if practice_data:
                avg_confidence = sum(p["performance"]["confidence_score"] for p in practice_data) / len(practice_data)
                avg_time = sum(p["performance"]["completion_time"] for p in practice_data) / len(practice_data)
                sentences_completed = len(practice_data)
                
                print(f"✓ {username}:")
                print(f"  - Sentences completed: {sentences_completed}")
                print(f"  - Average confidence: {avg_confidence:.2f}")
                print(f"  - Average time: {avg_time:.1f}s")
        
        print(f"\n✓ Session has detailed performance data for {len(session_state['practice_data'])} participants")
    
    def demo_session_lifecycle(self):
        """Demonstrate complete session lifecycle"""
        print("\n🔄 Session Lifecycle Demo")
        print("-" * 30)
        
        session_id = "lifecycle_demo_session"
        
        # 1. Session creation (waiting state)
        self.connection_manager.session_states[session_id] = {
            "session_status": "waiting",
            "participants": {},
            "current_sentence": 0,
            "story_content": None
        }
        print("✓ 1. Session created - status: waiting")
        
        # 2. Participants join
        participants = ["alice", "bob", "charlie"]
        for participant in participants:
            self.connection_manager.session_states[session_id]["participants"][participant] = {
                "username": participant.title(),
                "connected_at": datetime.utcnow().isoformat(),
                "status": "connected"
            }
        print(f"✓ 2. {len(participants)} participants joined")
        
        # 3. Host starts practice
        self.connection_manager.update_session_state(session_id, {
            "session_status": "active",
            "story_content": {
                "title": "Lifecycle Demo Story",
                "sentences": ["Sentence 1", "Sentence 2", "Sentence 3"]
            },
            "started_at": datetime.utcnow().isoformat()
        })
        print("✓ 3. Practice started - status: active")
        
        # 4. Practice session (participants make progress)
        print("✓ 4. Practice in progress...")
        
        # 5. Session paused
        self.connection_manager.update_session_state(session_id, {
            "session_status": "paused",
            "paused_at": datetime.utcnow().isoformat()
        })
        print("✓ 5. Session paused")
        
        # 6. Session resumed
        self.connection_manager.update_session_state(session_id, {
            "session_status": "active",
            "resumed_at": datetime.utcnow().isoformat()
        })
        print("✓ 6. Session resumed")
        
        # 7. Session completed
        self.connection_manager.update_session_state(session_id, {
            "session_status": "completed",
            "ended_at": datetime.utcnow().isoformat()
        })
        print("✓ 7. Session completed - status: completed")
        
        final_state = self.connection_manager.session_states[session_id]
        print(f"\n✓ Final session state: {final_state['session_status']}")
    
    def run_demo(self):
        """Run all demonstrations"""
        self.demo_connection_manager()
        self.demo_message_types()
        self.demo_session_synchronization()
        self.demo_peer_feedback_system()
        self.demo_chat_system()
        self.demo_performance_tracking()
        self.demo_session_lifecycle()
        
        print("\n" + "=" * 50)
        print("🎉 Collaborative Features Demo Complete!")
        print("\nImplemented Features:")
        print("✓ Real-time WebSocket communication")
        print("✓ Multi-user session management")
        print("✓ Synchronized practice sessions")
        print("✓ Peer feedback system")
        print("✓ Group chat functionality")
        print("✓ Progress tracking and sharing")
        print("✓ Session control and coordination")
        print("✓ Performance analytics")
        print("\nReady for integration with ASL World! 🚀")


if __name__ == "__main__":
    demo = CollaborativeDemo()
    demo.run_demo()