"""
WebSocket API for real-time collaborative sessions
Handles multi-user synchronized practice sessions with peer feedback
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Set, Any, Optional, List
from uuid import uuid4

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_db_session
from services.collaborative_service import CollaborativeService
from models.collaborative import SessionStatus

logger = logging.getLogger(__name__)

router = APIRouter()


class CollaborativeConnectionManager:
    """Manages WebSocket connections for collaborative sessions"""
    
    def __init__(self):
        # Session ID -> Set of WebSocket connections
        self.session_connections: Dict[str, Set[WebSocket]] = {}
        # WebSocket -> User info
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
        # Session ID -> Session state
        self.session_states: Dict[str, Dict[str, Any]] = {}
        # User ID -> WebSocket connections (for direct messaging)
        self.user_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect_to_session(
        self, 
        websocket: WebSocket, 
        session_id: str, 
        user_id: str, 
        username: str
    ):
        """Connect a user to a collaborative session"""
        await websocket.accept()
        
        # Initialize session connections if needed
        if session_id not in self.session_connections:
            self.session_connections[session_id] = set()
            self.session_states[session_id] = {
                "participants": {},
                "current_sentence": 0,
                "session_status": "waiting",
                "story_content": None,
                "practice_data": {},
                "chat_messages": [],
                "peer_feedback": {}
            }
        
        # Add connection
        self.session_connections[session_id].add(websocket)
        self.connection_info[websocket] = {
            "session_id": session_id,
            "user_id": user_id,
            "username": username,
            "connected_at": datetime.utcnow()
        }
        
        # Add to user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)
        
        # Update session state
        self.session_states[session_id]["participants"][user_id] = {
            "username": username,
            "connected_at": datetime.utcnow().isoformat(),
            "status": "connected",
            "current_sentence": 0,
            "performance": {}
        }
        
        # Notify other participants
        await self.broadcast_to_session(session_id, {
            "type": "participant_joined",
            "user_id": user_id,
            "username": username,
            "timestamp": datetime.utcnow().isoformat(),
            "participant_count": len(self.session_states[session_id]["participants"])
        }, exclude_websocket=websocket)
        
        # Send current session state to new participant
        await self.send_to_websocket(websocket, {
            "type": "session_state",
            "session_id": session_id,
            "state": self.session_states[session_id],
            "your_user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(f"User {user_id} connected to collaborative session {session_id}")
    
    async def disconnect_from_session(self, websocket: WebSocket):
        """Disconnect a user from their collaborative session"""
        if websocket not in self.connection_info:
            return
        
        connection_info = self.connection_info[websocket]
        session_id = connection_info["session_id"]
        user_id = connection_info["user_id"]
        username = connection_info["username"]
        
        # Remove from session connections
        if session_id in self.session_connections:
            self.session_connections[session_id].discard(websocket)
            
            # Remove participant from session state
            if user_id in self.session_states[session_id]["participants"]:
                del self.session_states[session_id]["participants"][user_id]
            
            # Clean up empty sessions
            if not self.session_connections[session_id]:
                del self.session_connections[session_id]
                del self.session_states[session_id]
            else:
                # Notify remaining participants
                await self.broadcast_to_session(session_id, {
                    "type": "participant_left",
                    "user_id": user_id,
                    "username": username,
                    "timestamp": datetime.utcnow().isoformat(),
                    "participant_count": len(self.session_states[session_id]["participants"])
                })
        
        # Remove from user connections
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # Remove connection info
        del self.connection_info[websocket]
        
        logger.info(f"User {user_id} disconnected from collaborative session {session_id}")
    
    async def broadcast_to_session(
        self, 
        session_id: str, 
        message: Dict[str, Any], 
        exclude_websocket: Optional[WebSocket] = None
    ):
        """Broadcast a message to all participants in a session"""
        if session_id not in self.session_connections:
            return
        
        message_text = json.dumps(message)
        disconnected_websockets = []
        
        for websocket in self.session_connections[session_id]:
            if websocket == exclude_websocket:
                continue
            
            try:
                await websocket.send_text(message_text)
            except Exception as e:
                logger.warning(f"Failed to send message to websocket in session {session_id}: {e}")
                disconnected_websockets.append(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected_websockets:
            await self.disconnect_from_session(websocket)
    
    async def send_to_websocket(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send a message to a specific websocket"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.warning(f"Failed to send message to websocket: {e}")
            await self.disconnect_from_session(websocket)
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send a message to all connections of a specific user"""
        if user_id not in self.user_connections:
            return
        
        message_text = json.dumps(message)
        disconnected_websockets = []
        
        for websocket in self.user_connections[user_id]:
            try:
                await websocket.send_text(message_text)
            except Exception as e:
                logger.warning(f"Failed to send message to user {user_id}: {e}")
                disconnected_websockets.append(websocket)
        
        # Clean up disconnected websockets
        for websocket in disconnected_websockets:
            await self.disconnect_from_session(websocket)
    
    def get_session_participants(self, session_id: str) -> List[Dict[str, Any]]:
        """Get list of participants in a session"""
        if session_id not in self.session_states:
            return []
        
        return [
            {
                "user_id": user_id,
                **participant_data
            }
            for user_id, participant_data in self.session_states[session_id]["participants"].items()
        ]
    
    def update_session_state(self, session_id: str, updates: Dict[str, Any]):
        """Update session state"""
        if session_id in self.session_states:
            self.session_states[session_id].update(updates)


# Global connection manager instance
collaborative_manager = CollaborativeConnectionManager()


async def get_current_user_id() -> str:
    """Get current user ID - placeholder for auth integration"""
    return "user_123"


@router.websocket("/ws/collaborative/{session_id}")
async def collaborative_websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    user_id: str = "user_123",  # Would come from auth
    username: str = "TestUser"  # Would come from user profile
):
    """
    WebSocket endpoint for collaborative sessions
    Handles real-time synchronization, peer feedback, and session coordination
    """
    try:
        # Connect to session
        await collaborative_manager.connect_to_session(
            websocket, session_id, user_id, username
        )
        
        # Main message processing loop
        while True:
            try:
                # Receive message from client
                message_text = await websocket.receive_text()
                message_data = json.loads(message_text)
                
                await handle_collaborative_message(
                    websocket, session_id, user_id, message_data
                )
                
            except WebSocketDisconnect:
                logger.info(f"User {user_id} disconnected from session {session_id}")
                break
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON from user {user_id} in session {session_id}: {e}")
                await collaborative_manager.send_to_websocket(websocket, {
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"Error processing message from user {user_id} in session {session_id}: {e}")
                await collaborative_manager.send_to_websocket(websocket, {
                    "type": "error",
                    "message": "Error processing message",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except Exception as e:
        logger.error(f"Critical error in collaborative websocket for user {user_id}, session {session_id}: {e}")
    
    finally:
        # Cleanup on disconnect
        await collaborative_manager.disconnect_from_session(websocket)


async def handle_collaborative_message(
    websocket: WebSocket,
    session_id: str,
    user_id: str,
    message_data: Dict[str, Any]
):
    """Handle different types of collaborative messages"""
    message_type = message_data.get("type", "unknown")
    timestamp = datetime.utcnow().isoformat()
    
    if message_type == "start_practice":
        # Host starts the practice session
        await handle_start_practice(session_id, user_id, message_data)
    
    elif message_type == "sentence_progress":
        # User completes a sentence
        await handle_sentence_progress(session_id, user_id, message_data)
    
    elif message_type == "gesture_analysis":
        # Share gesture analysis results with peers
        await handle_gesture_analysis(session_id, user_id, message_data)
    
    elif message_type == "peer_feedback":
        # Send feedback to another participant
        await handle_peer_feedback(session_id, user_id, message_data)
    
    elif message_type == "chat_message":
        # Send chat message to session
        await handle_chat_message(session_id, user_id, message_data)
    
    elif message_type == "sync_request":
        # Request session synchronization
        await handle_sync_request(websocket, session_id, user_id)
    
    elif message_type == "session_control":
        # Session control (pause, resume, next sentence, etc.)
        await handle_session_control(session_id, user_id, message_data)
    
    else:
        logger.warning(f"Unknown message type '{message_type}' from user {user_id} in session {session_id}")
        await collaborative_manager.send_to_websocket(websocket, {
            "type": "error",
            "message": f"Unknown message type: {message_type}",
            "timestamp": timestamp
        })


async def handle_start_practice(session_id: str, user_id: str, message_data: Dict[str, Any]):
    """Handle starting a practice session"""
    story_content = message_data.get("story_content")
    if not story_content:
        return
    
    # Update session state
    collaborative_manager.update_session_state(session_id, {
        "session_status": "active",
        "story_content": story_content,
        "current_sentence": 0,
        "started_by": user_id,
        "started_at": datetime.utcnow().isoformat()
    })
    
    # Broadcast to all participants
    await collaborative_manager.broadcast_to_session(session_id, {
        "type": "practice_started",
        "story_content": story_content,
        "started_by": user_id,
        "current_sentence": 0,
        "timestamp": datetime.utcnow().isoformat()
    })


async def handle_sentence_progress(session_id: str, user_id: str, message_data: Dict[str, Any]):
    """Handle user completing a sentence"""
    sentence_index = message_data.get("sentence_index", 0)
    performance_data = message_data.get("performance", {})
    
    # Update user's progress in session state
    if session_id in collaborative_manager.session_states:
        session_state = collaborative_manager.session_states[session_id]
        if user_id in session_state["participants"]:
            session_state["participants"][user_id]["current_sentence"] = sentence_index
            session_state["participants"][user_id]["performance"] = performance_data
        
        # Store practice data
        if "practice_data" not in session_state:
            session_state["practice_data"] = {}
        if user_id not in session_state["practice_data"]:
            session_state["practice_data"][user_id] = []
        
        session_state["practice_data"][user_id].append({
            "sentence_index": sentence_index,
            "performance": performance_data,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # Broadcast progress to other participants
    await collaborative_manager.broadcast_to_session(session_id, {
        "type": "participant_progress",
        "user_id": user_id,
        "sentence_index": sentence_index,
        "performance": performance_data,
        "timestamp": datetime.utcnow().isoformat()
    }, exclude_websocket=None)


async def handle_gesture_analysis(session_id: str, user_id: str, message_data: Dict[str, Any]):
    """Handle sharing gesture analysis results"""
    analysis_data = message_data.get("analysis", {})
    sentence_index = message_data.get("sentence_index", 0)
    
    # Broadcast gesture analysis to peers (if they have permission to see it)
    await collaborative_manager.broadcast_to_session(session_id, {
        "type": "peer_gesture_analysis",
        "from_user_id": user_id,
        "sentence_index": sentence_index,
        "analysis": analysis_data,
        "timestamp": datetime.utcnow().isoformat()
    })


async def handle_peer_feedback(session_id: str, user_id: str, message_data: Dict[str, Any]):
    """Handle peer feedback between participants"""
    target_user_id = message_data.get("target_user_id")
    feedback_type = message_data.get("feedback_type", "encouragement")
    feedback_message = message_data.get("message", "")
    sentence_index = message_data.get("sentence_index")
    
    if not target_user_id:
        return
    
    feedback_data = {
        "type": "peer_feedback_received",
        "from_user_id": user_id,
        "feedback_type": feedback_type,
        "message": feedback_message,
        "sentence_index": sentence_index,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Store feedback in session state
    if session_id in collaborative_manager.session_states:
        session_state = collaborative_manager.session_states[session_id]
        if "peer_feedback" not in session_state:
            session_state["peer_feedback"] = {}
        if target_user_id not in session_state["peer_feedback"]:
            session_state["peer_feedback"][target_user_id] = []
        
        session_state["peer_feedback"][target_user_id].append({
            "from_user_id": user_id,
            "feedback_type": feedback_type,
            "message": feedback_message,
            "sentence_index": sentence_index,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    # Send feedback to target user
    await collaborative_manager.send_to_user(target_user_id, feedback_data)
    
    # Optionally broadcast to session (depending on feedback type)
    if feedback_type in ["encouragement", "celebration"]:
        await collaborative_manager.broadcast_to_session(session_id, {
            "type": "peer_feedback_shared",
            "from_user_id": user_id,
            "target_user_id": target_user_id,
            "feedback_type": feedback_type,
            "message": feedback_message,
            "timestamp": datetime.utcnow().isoformat()
        })


async def handle_chat_message(session_id: str, user_id: str, message_data: Dict[str, Any]):
    """Handle chat messages in the session"""
    message_text = message_data.get("message", "")
    if not message_text.strip():
        return
    
    chat_message = {
        "type": "chat_message",
        "from_user_id": user_id,
        "message": message_text,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Store in session state
    if session_id in collaborative_manager.session_states:
        session_state = collaborative_manager.session_states[session_id]
        if "chat_messages" not in session_state:
            session_state["chat_messages"] = []
        session_state["chat_messages"].append(chat_message)
        
        # Keep only last 100 messages
        if len(session_state["chat_messages"]) > 100:
            session_state["chat_messages"] = session_state["chat_messages"][-100:]
    
    # Broadcast to all participants
    await collaborative_manager.broadcast_to_session(session_id, chat_message)


async def handle_sync_request(websocket: WebSocket, session_id: str, user_id: str):
    """Handle request for session synchronization"""
    if session_id in collaborative_manager.session_states:
        await collaborative_manager.send_to_websocket(websocket, {
            "type": "session_sync",
            "session_id": session_id,
            "state": collaborative_manager.session_states[session_id],
            "participants": collaborative_manager.get_session_participants(session_id),
            "timestamp": datetime.utcnow().isoformat()
        })


async def handle_session_control(session_id: str, user_id: str, message_data: Dict[str, Any]):
    """Handle session control commands"""
    control_action = message_data.get("action")
    
    if control_action == "pause_session":
        collaborative_manager.update_session_state(session_id, {
            "session_status": "paused",
            "paused_by": user_id,
            "paused_at": datetime.utcnow().isoformat()
        })
        
        await collaborative_manager.broadcast_to_session(session_id, {
            "type": "session_paused",
            "paused_by": user_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    elif control_action == "resume_session":
        collaborative_manager.update_session_state(session_id, {
            "session_status": "active",
            "resumed_by": user_id,
            "resumed_at": datetime.utcnow().isoformat()
        })
        
        await collaborative_manager.broadcast_to_session(session_id, {
            "type": "session_resumed",
            "resumed_by": user_id,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    elif control_action == "next_sentence":
        # Move all participants to next sentence
        if session_id in collaborative_manager.session_states:
            session_state = collaborative_manager.session_states[session_id]
            current_sentence = session_state.get("current_sentence", 0)
            new_sentence = current_sentence + 1
            
            session_state["current_sentence"] = new_sentence
            
            await collaborative_manager.broadcast_to_session(session_id, {
                "type": "sentence_changed",
                "new_sentence_index": new_sentence,
                "changed_by": user_id,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    elif control_action == "end_session":
        collaborative_manager.update_session_state(session_id, {
            "session_status": "completed",
            "ended_by": user_id,
            "ended_at": datetime.utcnow().isoformat()
        })
        
        await collaborative_manager.broadcast_to_session(session_id, {
            "type": "session_ended",
            "ended_by": user_id,
            "final_state": collaborative_manager.session_states[session_id],
            "timestamp": datetime.utcnow().isoformat()
        })


# Additional utility endpoints for session management

@router.get("/sessions/{session_id}/participants")
async def get_session_participants(session_id: str):
    """Get current participants in a collaborative session"""
    participants = collaborative_manager.get_session_participants(session_id)
    return {
        "session_id": session_id,
        "participants": participants,
        "participant_count": len(participants)
    }


@router.get("/sessions/{session_id}/state")
async def get_session_state(session_id: str):
    """Get current state of a collaborative session"""
    if session_id in collaborative_manager.session_states:
        return {
            "session_id": session_id,
            "state": collaborative_manager.session_states[session_id],
            "participants": collaborative_manager.get_session_participants(session_id)
        }
    else:
        return {
            "session_id": session_id,
            "state": None,
            "participants": []
        }