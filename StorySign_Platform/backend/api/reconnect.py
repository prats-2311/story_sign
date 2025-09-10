"""
Reconnect module API router
Contains endpoints for therapeutic movement analysis and pose tracking
"""

import logging
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from services.reconnect_service import ReconnectService

logger = logging.getLogger(__name__)

# Create router for Reconnect endpoints
router = APIRouter(prefix="/api/reconnect", tags=["reconnect"])

# Request models for API endpoints
class TherapySessionRequest(BaseModel):
    """Request model for creating therapy session"""
    exercise_type: str = Field(..., description="Type of therapeutic exercise")
    difficulty_level: Optional[str] = Field("normal", description="Difficulty level: beginner, intermediate, advanced")
    session_duration: Optional[int] = Field(None, description="Expected session duration in seconds")
    target_areas: Optional[List[str]] = Field(None, description="Target body areas for therapy")

class MovementAnalysisRequest(BaseModel):
    """Request model for movement analysis"""
    frame_data: str = Field(..., description="Base64 encoded image data")
    session_id: str = Field(..., description="Session ID for tracking")
    timestamp: Optional[str] = Field(None, description="Timestamp of the frame")

class SessionUpdateRequest(BaseModel):
    """Request model for updating session data"""
    session_id: str = Field(..., description="Session ID")
    movement_data: List[Dict[str, Any]] = Field(..., description="Movement landmarks data")
    joint_angles: Dict[str, List[float]] = Field(..., description="Joint angle measurements")
    range_of_motion: Dict[str, Dict[str, float]] = Field(..., description="Range of motion data")
    session_duration: int = Field(..., description="Total session duration in milliseconds")
    metrics: List[Dict[str, Any]] = Field(..., description="Movement quality metrics")

# Response models
class MovementAnalysisResponse(BaseModel):
    """Response model for movement analysis"""
    success: bool
    pose_landmarks: Optional[List[Dict[str, Any]]] = None
    joint_angles: Optional[Dict[str, float]] = None
    range_of_motion: Optional[Dict[str, float]] = None
    movement_metrics: Optional[Dict[str, Any]] = None
    feedback_message: Optional[str] = None
    timestamp: str

class SessionResponse(BaseModel):
    """Response model for session operations"""
    success: bool
    session_id: Optional[str] = None
    message: Optional[str] = None
    session_data: Optional[Dict[str, Any]] = None

class TherapyStatsResponse(BaseModel):
    """Response model for therapy statistics"""
    success: bool
    total_sessions: int
    average_quality: float
    favorite_exercises: List[Dict[str, Any]]
    recent_sessions: List[Dict[str, Any]]
    progress_trend: List[Dict[str, Any]]
    joint_improvements: Dict[str, Dict[str, Any]]

# Dependency to get reconnect service
async def get_reconnect_service() -> ReconnectService:
    """Get reconnect service instance"""
    return ReconnectService()

@router.post("/sessions", response_model=SessionResponse)
async def create_therapy_session(
    request: TherapySessionRequest,
    reconnect_service: ReconnectService = Depends(get_reconnect_service)
):
    """
    Create a new therapeutic movement session
    
    Args:
        request: Session creation request
        reconnect_service: Reconnect service instance
        
    Returns:
        Session creation response with session ID
    """
    try:
        logger.info(f"Creating therapy session for exercise: {request.exercise_type}")
        
        # Validate exercise type
        valid_exercises = [
            "shoulder_flexion", "arm_circles", "neck_stretches", 
            "torso_twists", "leg_raises", "balance_training"
        ]
        if request.exercise_type not in valid_exercises:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_exercise",
                    "message": f"Invalid exercise type: {request.exercise_type}",
                    "valid_exercises": valid_exercises
                }
            )
        
        # Create session
        session_data = await reconnect_service.create_therapy_session(
            exercise_type=request.exercise_type,
            difficulty_level=request.difficulty_level,
            expected_duration=request.session_duration,
            target_areas=request.target_areas
        )
        
        return SessionResponse(
            success=True,
            session_id=session_data["session_id"],
            message="Therapy session created successfully",
            session_data=session_data
        )
        
    except Exception as e:
        logger.error(f"Error creating therapy session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "session_creation_failed",
                "message": "Failed to create therapy session",
                "technical_error": str(e)
            }
        )

@router.post("/analyze", response_model=MovementAnalysisResponse)
async def analyze_movement(
    request: MovementAnalysisRequest,
    reconnect_service: ReconnectService = Depends(get_reconnect_service)
):
    """
    Analyze movement from pose image
    
    Args:
        request: Movement analysis request
        reconnect_service: Reconnect service instance
        
    Returns:
        Movement analysis results
    """
    try:
        logger.debug(f"Processing movement analysis for session: {request.session_id}")
        
        # Validate frame data
        if not request.frame_data or not request.frame_data.strip():
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "invalid_frame_data",
                    "message": "Frame data is required for movement analysis"
                }
            )
        
        # Process movement analysis
        analysis_result = await reconnect_service.analyze_movement_from_frame(
            frame_data=request.frame_data,
            session_id=request.session_id
        )
        
        if not analysis_result["success"]:
            return MovementAnalysisResponse(
                success=False,
                feedback_message=analysis_result.get("error", "Movement analysis failed"),
                timestamp=datetime.utcnow().isoformat()
            )
        
        return MovementAnalysisResponse(
            success=True,
            pose_landmarks=analysis_result["pose_landmarks"],
            joint_angles=analysis_result["joint_angles"],
            range_of_motion=analysis_result["range_of_motion"],
            movement_metrics=analysis_result["movement_metrics"],
            feedback_message=analysis_result.get("feedback_message"),
            timestamp=datetime.utcnow().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in movement analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "analysis_failed",
                "message": "Failed to process movement analysis",
                "technical_error": str(e)
            }
        )

@router.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    request: SessionUpdateRequest,
    reconnect_service: ReconnectService = Depends(get_reconnect_service)
):
    """
    Update session with final data and calculate results
    
    Args:
        session_id: Session ID to update
        request: Session update request
        reconnect_service: Reconnect service instance
        
    Returns:
        Session update response
    """
    try:
        logger.info(f"Updating therapy session: {session_id}")
        
        # Validate session exists
        session_exists = await reconnect_service.session_exists(session_id)
        if not session_exists:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "session_not_found",
                    "message": f"Session {session_id} not found"
                }
            )
        
        # Update session with final data
        update_result = await reconnect_service.update_session_data(
            session_id=session_id,
            movement_data=request.movement_data,
            joint_angles=request.joint_angles,
            range_of_motion=request.range_of_motion,
            session_duration=request.session_duration,
            metrics=request.metrics
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
    reconnect_service: ReconnectService = Depends(get_reconnect_service)
):
    """
    Get session data and results
    
    Args:
        session_id: Session ID to retrieve
        reconnect_service: Reconnect service instance
        
    Returns:
        Session data response
    """
    try:
        logger.debug(f"Retrieving therapy session: {session_id}")
        
        session_data = await reconnect_service.get_session_data(session_id)
        
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
    reconnect_service: ReconnectService = Depends(get_reconnect_service)
):
    """
    Delete a therapy session
    
    Args:
        session_id: Session ID to delete
        reconnect_service: Reconnect service instance
        
    Returns:
        Deletion response
    """
    try:
        logger.info(f"Deleting therapy session: {session_id}")
        
        success = await reconnect_service.delete_session(session_id)
        
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

@router.get("/stats", response_model=TherapyStatsResponse)
async def get_user_stats(
    user_id: Optional[str] = None,
    reconnect_service: ReconnectService = Depends(get_reconnect_service)
):
    """
    Get user statistics for therapy sessions
    
    Args:
        user_id: User ID (optional, defaults to current user)
        reconnect_service: Reconnect service instance
        
    Returns:
        User statistics response
    """
    try:
        logger.debug(f"Retrieving therapy stats for user: {user_id}")
        
        stats = await reconnect_service.get_user_statistics(user_id)
        
        return TherapyStatsResponse(
            success=True,
            total_sessions=stats["total_sessions"],
            average_quality=stats["average_quality"],
            favorite_exercises=stats["favorite_exercises"],
            recent_sessions=stats["recent_sessions"],
            progress_trend=stats["progress_trend"],
            joint_improvements=stats["joint_improvements"]
        )
        
    except Exception as e:
        logger.error(f"Error retrieving therapy stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "stats_retrieval_failed",
                "message": "Failed to retrieve therapy statistics",
                "technical_error": str(e)
            }
        )

@router.get("/exercises", response_model=Dict[str, Any])
async def get_available_exercises():
    """
    Get list of available therapeutic exercises
    
    Returns:
        Dictionary of available exercises with metadata
    """
    try:
        exercises = {
            "shoulder_flexion": {
                "name": "Shoulder Flexion",
                "description": "Forward arm raises for shoulder mobility",
                "icon": "🤲",
                "difficulty": "beginner",
                "duration": "5-10 minutes",
                "target_areas": ["Shoulders", "Upper Arms"],
                "instructions": [
                    "Stand with feet shoulder-width apart",
                    "Keep arms straight at your sides",
                    "Slowly raise both arms forward to shoulder height",
                    "Hold for 2 seconds, then lower slowly",
                    "Repeat 10-15 times"
                ],
                "benefits": [
                    "Improves shoulder flexibility",
                    "Reduces stiffness",
                    "Enhances range of motion",
                    "Strengthens shoulder muscles"
                ]
            },
            "arm_circles": {
                "name": "Arm Circles",
                "description": "Circular arm movements for joint mobility",
                "icon": "🔄",
                "difficulty": "beginner",
                "duration": "3-5 minutes",
                "target_areas": ["Shoulders", "Arms"],
                "instructions": [
                    "Stand with arms extended to the sides",
                    "Make small circles with your arms",
                    "Gradually increase circle size",
                    "Reverse direction after 10 circles",
                    "Keep movements smooth and controlled"
                ],
                "benefits": [
                    "Improves joint mobility",
                    "Warms up shoulder muscles",
                    "Enhances circulation",
                    "Reduces joint stiffness"
                ]
            },
            "neck_stretches": {
                "name": "Neck Stretches",
                "description": "Gentle neck movements for cervical mobility",
                "icon": "🦢",
                "difficulty": "beginner",
                "duration": "5-8 minutes",
                "target_areas": ["Neck", "Upper Spine"],
                "instructions": [
                    "Sit or stand with good posture",
                    "Slowly turn head to the right",
                    "Hold for 5 seconds",
                    "Return to center and repeat left",
                    "Perform gentle up and down movements"
                ],
                "benefits": [
                    "Relieves neck tension",
                    "Improves cervical mobility",
                    "Reduces headaches",
                    "Enhances posture"
                ]
            },
            "torso_twists": {
                "name": "Torso Twists",
                "description": "Spinal rotation exercises for core mobility",
                "icon": "🌪️",
                "difficulty": "intermediate",
                "duration": "8-12 minutes",
                "target_areas": ["Spine", "Core", "Hips"],
                "instructions": [
                    "Stand with feet hip-width apart",
                    "Place hands on hips or cross arms",
                    "Slowly rotate torso to the right",
                    "Return to center and rotate left",
                    "Keep hips facing forward"
                ],
                "benefits": [
                    "Improves spinal mobility",
                    "Strengthens core muscles",
                    "Enhances balance",
                    "Reduces back stiffness"
                ]
            },
            "leg_raises": {
                "name": "Leg Raises",
                "description": "Hip flexion exercises for lower body strength",
                "icon": "🦵",
                "difficulty": "intermediate",
                "duration": "10-15 minutes",
                "target_areas": ["Hips", "Thighs", "Core"],
                "instructions": [
                    "Stand behind a chair for support",
                    "Keep one leg planted firmly",
                    "Slowly raise the other leg forward",
                    "Hold for 2 seconds at the top",
                    "Lower slowly and repeat"
                ],
                "benefits": [
                    "Strengthens hip flexors",
                    "Improves balance",
                    "Enhances core stability",
                    "Increases leg strength"
                ]
            },
            "balance_training": {
                "name": "Balance Training",
                "description": "Static and dynamic balance exercises",
                "icon": "⚖️",
                "difficulty": "advanced",
                "duration": "15-20 minutes",
                "target_areas": ["Full Body", "Core", "Legs"],
                "instructions": [
                    "Start with single-leg stands",
                    "Progress to eyes-closed balance",
                    "Add arm movements while balancing",
                    "Try heel-to-toe walking",
                    "Use support as needed"
                ],
                "benefits": [
                    "Improves proprioception",
                    "Reduces fall risk",
                    "Enhances coordination",
                    "Strengthens stabilizing muscles"
                ]
            }
        }
        
        return {
            "success": True,
            "exercises": exercises,
            "total_count": len(exercises)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving exercises list: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "exercises_retrieval_failed",
                "message": "Failed to retrieve exercises list",
                "technical_error": str(e)
            }
        )

@router.websocket("/ws/{session_id}")
async def websocket_movement_analysis(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time movement analysis
    
    Args:
        websocket: WebSocket connection
        session_id: Session ID for tracking
    """
    await websocket.accept()
    reconnect_service = await get_reconnect_service()
    
    try:
        logger.info(f"WebSocket connection established for therapy session: {session_id}")
        
        while True:
            # Receive frame data from client
            data = await websocket.receive_json()
            
            if data.get("type") == "frame":
                # Process movement analysis
                analysis_result = await reconnect_service.analyze_movement_from_frame(
                    frame_data=data["frame_data"],
                    session_id=session_id
                )
                
                # Send result back to client
                await websocket.send_json({
                    "type": "reconnect_movement_analysis",
                    "session_id": session_id,
                    "success": analysis_result["success"],
                    "pose_landmarks": analysis_result.get("pose_landmarks"),
                    "joint_angles": analysis_result.get("joint_angles"),
                    "range_of_motion": analysis_result.get("range_of_motion"),
                    "movement_metrics": analysis_result.get("movement_metrics"),
                    "feedback_message": analysis_result.get("feedback_message"),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            elif data.get("type") == "session_end":
                # Handle session end
                logger.info(f"Therapy session ended: {session_id}")
                await websocket.send_json({
                    "type": "session_ended",
                    "session_id": session_id,
                    "message": "Therapy session ended successfully"
                })
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for therapy session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "error",
                "message": "An error occurred during movement analysis",
                "error": str(e)
            })
        except:
            pass  # Connection might be closed
    finally:
        try:
            await websocket.close()
        except:
            pass