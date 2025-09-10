"""
Harmony module API router
Contains endpoints for facial expression practice and emotion detection
"""

import logging
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from services.harmony_service import HarmonyService
from core.database_service import get_database_service
from repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

# Create router for Harmony endpoints
router = APIRouter(prefix="/api/harmony", tags=["harmony"])

# Request models for API endpoints
class EmotionSessionRequest(BaseModel):
    """Request model for creating emotion practice session"""
    target_emotion: str = Field(..., description="Target emotion to practice")
    session_duration: Optional[int] = Field(None, description="Expected session duration in seconds")
    difficulty_level: Optional[str] = Field("normal", description="Difficulty level: easy, normal, hard")

class EmotionDetectionRequest(BaseModel):
    """Request model for emotion detection"""
    frame_data: str = Field(..., description="Base64 encoded image data")
    session_id: str = Field(..., description="Session ID for tracking")
    timestamp: Optional[str] = Field(None, description="Timestamp of the frame")

class SessionUpdateRequest(BaseModel):
    """Request model for updating session data"""
    session_id: str = Field(..., description="Session ID")
    detected_emotions: List[str] = Field(..., description="List of detected emotions")
    confidence_scores: List[float] = Field(..., description="Confidence scores for detections")
    landmarks_data: List[Dict[str, Any]] = Field(..., description="Facial landmarks data")
    session_duration: int = Field(..., description="Total session duration in milliseconds")

# Response models
class EmotionDetectionResponse(BaseModel):
    """Response model for emotion detection"""
    success: bool
    detected_emotion: Optional[str] = None
    confidence_score: Optional[float] = None
    facial_landmarks: Optional[Dict[str, Any]] = None
    feedback_message: Optional[str] = None
    timestamp: str

class SessionResponse(BaseModel):
    """Response model for session operations"""
    success: bool
    session_id: Optional[str] = None
    message: Optional[str] = None
    session_data: Optional[Dict[str, Any]] = None

class SessionStatsResponse(BaseModel):
    """Response model for session statistics"""
    success: bool
    total_sessions: int
    average_accuracy: float
    favorite_emotions: List[Dict[str, Any]]
    recent_sessions: List[Dict[str, Any]]
    progress_trend: List[Dict[str, Any]]

# Dependency to get harmony service
async def get_harmony_service() -> HarmonyService:
    """Get harmony service instance"""
    db_service = await get_database_service()
    return HarmonyService(db_service=db_service)

@router.post("/sessions", response_model=SessionResponse)
async def create_emotion_session(
    request: EmotionSessionRequest,
    harmony_service: HarmonyService = Depends(get_harmony_service)
):
    """
    Create a new emotion practice session
    
    Args:
        request: Session creation request
        harmony_service: Harmony service instance
        
    Returns:
        Session creation response with session ID
    """
    try:
        logger.info(f"Creating emotion session for target emotion: {request.target_emotion}")
        
        # Validate target emotion
        valid_emotions = ["happy", "sad", "surprised", "angry", "fearful", "disgusted", "neutral"]
        if request.target_emotion not in valid_emotions:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_emotion",
                    "message": f"Invalid target emotion: {request.target_emotion}",
                    "valid_emotions": valid_emotions
                }
            )
        
        # Create session
        session_data = await harmony_service.create_emotion_session(
            target_emotion=request.target_emotion,
            difficulty_level=request.difficulty_level,
            expected_duration=request.session_duration
        )
        
        return SessionResponse(
            success=True,
            session_id=session_data["session_id"],
            message="Session created successfully",
            session_data=session_data
        )
        
    except Exception as e:
        logger.error(f"Error creating emotion session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "session_creation_failed",
                "message": "Failed to create emotion session",
                "technical_error": str(e)
            }
        )

@router.post("/detect", response_model=EmotionDetectionResponse)
async def detect_emotion(
    request: EmotionDetectionRequest,
    harmony_service: HarmonyService = Depends(get_harmony_service)
):
    """
    Detect emotion from facial image
    
    Args:
        request: Emotion detection request
        harmony_service: Harmony service instance
        
    Returns:
        Emotion detection results
    """
    try:
        logger.debug(f"Processing emotion detection for session: {request.session_id}")
        
        # Validate frame data
        if not request.frame_data or not request.frame_data.strip():
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_frame_data",
                    "message": "Frame data is required for emotion detection"
                }
            )
        
        # Process emotion detection
        detection_result = await harmony_service.detect_emotion_from_frame(
            frame_data=request.frame_data,
            session_id=request.session_id
        )
        
        if not detection_result["success"]:
            return EmotionDetectionResponse(
                success=False,
                feedback_message=detection_result.get("error", "Emotion detection failed"),
                timestamp=datetime.utcnow().isoformat()
            )
        
        return EmotionDetectionResponse(
            success=True,
            detected_emotion=detection_result["detected_emotion"],
            confidence_score=detection_result["confidence_score"],
            facial_landmarks=detection_result.get("facial_landmarks"),
            feedback_message=detection_result.get("feedback_message"),
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in emotion detection: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "detection_failed",
                "message": "Failed to process emotion detection",
                "technical_error": str(e)
            }
        )

@router.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    request: SessionUpdateRequest,
    harmony_service: HarmonyService = Depends(get_harmony_service)
):
    """
    Update session with final data and calculate results
    
    Args:
        session_id: Session ID to update
        request: Session update request
        harmony_service: Harmony service instance
        
    Returns:
        Session update response
    """
    try:
        logger.info(f"Updating session: {session_id}")
        
        # Validate session exists
        session_exists = await harmony_service.session_exists(session_id)
        if not session_exists:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "session_not_found",
                    "message": f"Session {session_id} not found"
                }
            )
        
        # Update session with final data
        update_result = await harmony_service.update_session_data(
            session_id=session_id,
            detected_emotions=request.detected_emotions,
            confidence_scores=request.confidence_scores,
            landmarks_data=request.landmarks_data,
            session_duration=request.session_duration
        )
        
        return SessionResponse(
            success=True,
            session_id=session_id,
            message="Session updated successfully",
            session_data=update_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "session_update_failed",
                "message": "Failed to update session",
                "technical_error": str(e)
            }
        )

@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    harmony_service: HarmonyService = Depends(get_harmony_service)
):
    """
    Get session data and results
    
    Args:
        session_id: Session ID to retrieve
        harmony_service: Harmony service instance
        
    Returns:
        Session data response
    """
    try:
        logger.debug(f"Retrieving session: {session_id}")
        
        session_data = await harmony_service.get_session_data(session_id)
        
        if not session_data:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "session_not_found",
                    "message": f"Session {session_id} not found"
                }
            )
        
        return SessionResponse(
            success=True,
            session_id=session_id,
            session_data=session_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "session_retrieval_failed",
                "message": "Failed to retrieve session",
                "technical_error": str(e)
            }
        )

@router.delete("/sessions/{session_id}", response_model=SessionResponse)
async def delete_session(
    session_id: str,
    harmony_service: HarmonyService = Depends(get_harmony_service)
):
    """
    Delete a session
    
    Args:
        session_id: Session ID to delete
        harmony_service: Harmony service instance
        
    Returns:
        Deletion response
    """
    try:
        logger.info(f"Deleting session: {session_id}")
        
        success = await harmony_service.delete_session(session_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "session_not_found",
                    "message": f"Session {session_id} not found"
                }
            )
        
        return SessionResponse(
            success=True,
            message="Session deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "session_deletion_failed",
                "message": "Failed to delete session",
                "technical_error": str(e)
            }
        )

@router.get("/stats", response_model=SessionStatsResponse)
async def get_user_stats(
    user_id: Optional[str] = None,
    harmony_service: HarmonyService = Depends(get_harmony_service)
):
    """
    Get user statistics for emotion practice sessions
    
    Args:
        user_id: User ID (optional, defaults to current user)
        harmony_service: Harmony service instance
        
    Returns:
        User statistics response
    """
    try:
        logger.debug(f"Retrieving stats for user: {user_id}")
        
        stats = await harmony_service.get_user_statistics(user_id)
        
        return SessionStatsResponse(
            success=True,
            total_sessions=stats["total_sessions"],
            average_accuracy=stats["average_accuracy"],
            favorite_emotions=stats["favorite_emotions"],
            recent_sessions=stats["recent_sessions"],
            progress_trend=stats["progress_trend"]
        )
        
    except Exception as e:
        logger.error(f"Error retrieving user stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "stats_retrieval_failed",
                "message": "Failed to retrieve user statistics",
                "technical_error": str(e)
            }
        )

@router.get("/emotions", response_model=Dict[str, Any])
async def get_available_emotions():
    """
    Get list of available emotions for practice
    
    Returns:
        Dictionary of available emotions with metadata
    """
    try:
        emotions = {
            "happy": {
                "name": "Happy",
                "description": "Practice showing joy and happiness",
                "icon": "😊",
                "difficulty": "easy",
                "tips": [
                    "Smile with your eyes (Duchenne smile)",
                    "Raise the corners of your mouth",
                    "Relax your forehead",
                    "Let the joy show naturally"
                ]
            },
            "sad": {
                "name": "Sad",
                "description": "Practice expressing sadness appropriately",
                "icon": "😢",
                "difficulty": "medium",
                "tips": [
                    "Lower the corners of your mouth slightly",
                    "Let your eyes show the emotion",
                    "Relax your facial muscles",
                    "Don't exaggerate the expression"
                ]
            },
            "surprised": {
                "name": "Surprised",
                "description": "Practice showing surprise and wonder",
                "icon": "😮",
                "difficulty": "medium",
                "tips": [
                    "Raise your eyebrows",
                    "Open your eyes wider",
                    "Drop your jaw slightly",
                    "Keep the expression brief and natural"
                ]
            },
            "angry": {
                "name": "Angry",
                "description": "Practice controlled expression of anger",
                "icon": "😠",
                "difficulty": "hard",
                "tips": [
                    "Lower your brow slightly",
                    "Tighten your lips",
                    "Keep control of the intensity",
                    "Practice healthy expression"
                ]
            },
            "fearful": {
                "name": "Fearful",
                "description": "Practice expressing concern or fear",
                "icon": "😨",
                "difficulty": "hard",
                "tips": [
                    "Widen your eyes",
                    "Raise your eyebrows",
                    "Tense your facial muscles slightly",
                    "Keep the expression authentic"
                ]
            },
            "disgusted": {
                "name": "Disgusted",
                "description": "Practice showing distaste appropriately",
                "icon": "🤢",
                "difficulty": "medium",
                "tips": [
                    "Wrinkle your nose slightly",
                    "Raise your upper lip",
                    "Squint your eyes a bit",
                    "Keep it subtle and appropriate"
                ]
            },
            "neutral": {
                "name": "Neutral",
                "description": "Practice maintaining a calm, neutral expression",
                "icon": "😐",
                "difficulty": "easy",
                "tips": [
                    "Relax all facial muscles",
                    "Keep your mouth in a natural position",
                    "Maintain soft, alert eyes",
                    "Practice mindful awareness"
                ]
            }
        }
        
        return {
            "success": True,
            "emotions": emotions,
            "total_count": len(emotions)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving emotions list: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "emotions_retrieval_failed",
                "message": "Failed to retrieve emotions list",
                "technical_error": str(e)
            }
        )

@router.websocket("/ws/{session_id}")
async def websocket_emotion_detection(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time emotion detection
    
    Args:
        websocket: WebSocket connection
        session_id: Session ID for tracking
    """
    await websocket.accept()
    harmony_service = await get_harmony_service()
    
    try:
        logger.info(f"WebSocket connection established for session: {session_id}")
        
        while True:
            # Receive frame data from client
            data = await websocket.receive_json()
            
            if data.get("type") == "frame":
                # Process emotion detection
                detection_result = await harmony_service.detect_emotion_from_frame(
                    frame_data=data["frame_data"],
                    session_id=session_id
                )
                
                # Send result back to client
                await websocket.send_json({
                    "type": "emotion_detection",
                    "session_id": session_id,
                    "success": detection_result["success"],
                    "detected_emotion": detection_result.get("detected_emotion"),
                    "confidence_score": detection_result.get("confidence_score"),
                    "facial_landmarks": detection_result.get("facial_landmarks"),
                    "feedback_message": detection_result.get("feedback_message"),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            elif data.get("type") == "session_end":
                # Handle session end
                logger.info(f"Session ended: {session_id}")
                await websocket.send_json({
                    "type": "session_ended",
                    "session_id": session_id,
                    "message": "Session ended successfully"
                })
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": "An error occurred during emotion detection",
                "error": str(e)
            })
        except:
            pass  # Connection might be closed
    finally:
        try:
            await websocket.close()
        except:
            pass