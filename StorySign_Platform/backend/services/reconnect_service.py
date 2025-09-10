"""
Reconnect service for therapeutic movement analysis and pose tracking
Handles MediaPipe pose detection and joint angle calculations
"""

import logging
import asyncio
import base64
import io
import uuid
import numpy as np
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image
import cv2

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    logging.warning("MediaPipe not available - using mock movement analysis")

from core.base_service import BaseService


class ReconnectService(BaseService):
    """
    Service for therapeutic movement analysis and pose tracking using MediaPipe
    """
    
    def __init__(self, service_name: str = "ReconnectService", config: Optional[Dict[str, Any]] = None, db_service=None):
        super().__init__(service_name, config)
        self.db_service = db_service
        
        # MediaPipe setup
        if MEDIAPIPE_AVAILABLE:
            self.mp_pose = mp.solutions.pose
            self.mp_drawing = mp.solutions.drawing_utils
            self.pose = self.mp_pose.Pose(
                static_image_mode=True,
                model_complexity=2,
                enable_segmentation=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
        else:
            self.mp_pose = None
            self.pose = None
        
        # Joint angle calculation parameters
        self.joint_connections = {
            "left_shoulder": [11, 13, 15],  # shoulder, elbow, wrist
            "right_shoulder": [12, 14, 16],
            "left_elbow": [11, 13, 15],
            "right_elbow": [12, 14, 16],
            "left_hip": [23, 25, 27],  # hip, knee, ankle
            "right_hip": [24, 26, 28],
            "left_knee": [23, 25, 27],
            "right_knee": [24, 26, 28],
            "spine": [11, 23, 24],  # shoulder center to hip center
            "neck": [0, 11, 12]  # nose to shoulder center
        }
        
        # Normal range of motion thresholds (in degrees)
        self.normal_ranges = {
            "shoulder": {"flexion": 180, "extension": 60, "abduction": 180},
            "elbow": {"flexion": 145, "extension": 0},
            "hip": {"flexion": 120, "extension": 30, "abduction": 45},
            "knee": {"flexion": 135, "extension": 0},
            "spine": {"flexion": 60, "extension": 25, "rotation": 45},
            "neck": {"flexion": 50, "extension": 60, "rotation": 80}
        }
        
        # Session storage (in production, this would be in database)
        self.active_sessions = {}
        
    async def initialize(self) -> None:
        """Initialize reconnect service"""
        self.logger.info("Reconnect service initialized")
        if not MEDIAPIPE_AVAILABLE:
            self.logger.warning("MediaPipe not available - movement analysis will use mock data")
    
    async def cleanup(self) -> None:
        """Clean up reconnect service"""
        if self.pose:
            self.pose.close()
    
    async def create_therapy_session(
        self,
        exercise_type: str,
        difficulty_level: str = "normal",
        expected_duration: Optional[int] = None,
        target_areas: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new therapeutic movement session
        
        Args:
            exercise_type: Type of therapeutic exercise
            difficulty_level: Difficulty level (beginner, intermediate, advanced)
            expected_duration: Expected session duration in seconds
            target_areas: Target body areas for therapy
            user_id: User ID (optional)
            
        Returns:
            Session data dictionary
        """
        session_id = str(uuid.uuid4())
        
        session_data = {
            "session_id": session_id,
            "exercise_type": exercise_type,
            "difficulty_level": difficulty_level,
            "expected_duration": expected_duration,
            "target_areas": target_areas or [],
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "status": "active",
            "movements": [],
            "pose_history": [],
            "joint_measurements": {},
            "statistics": {
                "total_movements": 0,
                "average_quality": 0.0,
                "range_of_motion": {},
                "session_score": 0,
                "joint_angles": {}
            }
        }
        
        # Initialize joint measurements for target areas
        for area in (target_areas or []):
            session_data["joint_measurements"][area.lower()] = []
        
        # Store session (in production, save to database)
        self.active_sessions[session_id] = session_data
        
        self.logger.info(f"Created therapy session: {session_id} for exercise: {exercise_type}")
        return session_data
    
    async def analyze_movement_from_frame(
        self,
        frame_data: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Analyze movement from a single frame
        
        Args:
            frame_data: Base64 encoded image data
            session_id: Session ID for tracking
            
        Returns:
            Movement analysis result dictionary
        """
        try:
            # Decode image
            image = self._decode_base64_image(frame_data)
            if image is None:
                return {
                    "success": False,
                    "error": "Failed to decode image data"
                }
            
            # Convert to RGB for MediaPipe
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect pose landmarks
            pose_result = await self._detect_pose_landmarks(rgb_image)
            
            if not pose_result["success"]:
                return {
                    "success": False,
                    "error": pose_result["error"]
                }
            
            # Calculate joint angles
            joint_angles = await self._calculate_joint_angles(
                pose_result["landmarks"],
                pose_result["image_shape"]
            )
            
            # Calculate range of motion
            range_of_motion = await self._calculate_range_of_motion(
                joint_angles,
                session_id
            )
            
            # Assess movement quality
            movement_metrics = await self._assess_movement_quality(
                pose_result["landmarks"],
                joint_angles,
                range_of_motion,
                session_id
            )
            
            # Update session with movement data
            if session_id in self.active_sessions:
                await self._update_session_movement(
                    session_id,
                    pose_result["landmarks"],
                    joint_angles,
                    range_of_motion,
                    movement_metrics
                )
            
            # Generate feedback message
            feedback_message = self._generate_movement_feedback(
                joint_angles,
                range_of_motion,
                movement_metrics,
                session_id
            )
            
            return {
                "success": True,
                "pose_landmarks": pose_result["landmarks"],
                "joint_angles": joint_angles,
                "range_of_motion": range_of_motion,
                "movement_metrics": movement_metrics,
                "feedback_message": feedback_message,
                "processing_time": pose_result.get("processing_time", 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error in movement analysis: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Movement analysis failed: {str(e)}"
            }
    
    async def _detect_pose_landmarks(self, rgb_image: np.ndarray) -> Dict[str, Any]:
        """
        Detect pose landmarks using MediaPipe
        
        Args:
            rgb_image: RGB image array
            
        Returns:
            Pose landmarks detection result
        """
        if not MEDIAPIPE_AVAILABLE or not self.pose:
            # Mock pose landmarks for testing
            return await self._mock_pose_landmarks(rgb_image.shape)
        
        try:
            # Process image with MediaPipe
            results = self.pose.process(rgb_image)
            
            if not results.pose_landmarks:
                return {
                    "success": False,
                    "error": "No pose detected in image"
                }
            
            # Extract landmarks
            landmarks = []
            for landmark in results.pose_landmarks.landmark:
                landmarks.append({
                    "x": landmark.x,
                    "y": landmark.y,
                    "z": landmark.z,
                    "visibility": landmark.visibility
                })
            
            return {
                "success": True,
                "landmarks": landmarks,
                "image_shape": rgb_image.shape,
                "num_landmarks": len(landmarks)
            }
            
        except Exception as e:
            self.logger.error(f"MediaPipe pose detection error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Pose detection failed: {str(e)}"
            }
    
    async def _mock_pose_landmarks(self, image_shape: Tuple[int, int, int]) -> Dict[str, Any]:
        """
        Generate mock pose landmarks for testing when MediaPipe is not available
        
        Args:
            image_shape: Shape of the input image
            
        Returns:
            Mock pose landmarks result
        """
        # Generate basic pose landmark points (33 landmarks for MediaPipe pose)
        landmarks = []
        
        # Head and face landmarks (0-10)
        head_landmarks = [
            {"x": 0.5, "y": 0.1, "z": 0.0, "visibility": 0.9},  # nose
            {"x": 0.48, "y": 0.08, "z": 0.0, "visibility": 0.8},  # left eye inner
            {"x": 0.45, "y": 0.08, "z": 0.0, "visibility": 0.8},  # left eye
            {"x": 0.42, "y": 0.08, "z": 0.0, "visibility": 0.8},  # left eye outer
            {"x": 0.52, "y": 0.08, "z": 0.0, "visibility": 0.8},  # right eye inner
            {"x": 0.55, "y": 0.08, "z": 0.0, "visibility": 0.8},  # right eye
            {"x": 0.58, "y": 0.08, "z": 0.0, "visibility": 0.8},  # right eye outer
            {"x": 0.4, "y": 0.1, "z": 0.0, "visibility": 0.7},   # left ear
            {"x": 0.6, "y": 0.1, "z": 0.0, "visibility": 0.7},   # right ear
            {"x": 0.47, "y": 0.12, "z": 0.0, "visibility": 0.8}, # mouth left
            {"x": 0.53, "y": 0.12, "z": 0.0, "visibility": 0.8}, # mouth right
        ]
        landmarks.extend(head_landmarks)
        
        # Upper body landmarks (11-16)
        upper_body = [
            {"x": 0.45, "y": 0.25, "z": 0.0, "visibility": 0.9}, # left shoulder
            {"x": 0.55, "y": 0.25, "z": 0.0, "visibility": 0.9}, # right shoulder
            {"x": 0.4, "y": 0.4, "z": 0.0, "visibility": 0.8},  # left elbow
            {"x": 0.6, "y": 0.4, "z": 0.0, "visibility": 0.8},  # right elbow
            {"x": 0.35, "y": 0.55, "z": 0.0, "visibility": 0.7}, # left wrist
            {"x": 0.65, "y": 0.55, "z": 0.0, "visibility": 0.7}, # right wrist
        ]
        landmarks.extend(upper_body)
        
        # Hand landmarks (17-22)
        hand_landmarks = [
            {"x": 0.33, "y": 0.57, "z": 0.0, "visibility": 0.6}, # left pinky
            {"x": 0.32, "y": 0.56, "z": 0.0, "visibility": 0.6}, # left index
            {"x": 0.34, "y": 0.58, "z": 0.0, "visibility": 0.6}, # left thumb
            {"x": 0.67, "y": 0.57, "z": 0.0, "visibility": 0.6}, # right pinky
            {"x": 0.68, "y": 0.56, "z": 0.0, "visibility": 0.6}, # right index
            {"x": 0.66, "y": 0.58, "z": 0.0, "visibility": 0.6}, # right thumb
        ]
        landmarks.extend(hand_landmarks)
        
        # Lower body landmarks (23-32)
        lower_body = [
            {"x": 0.47, "y": 0.6, "z": 0.0, "visibility": 0.9},  # left hip
            {"x": 0.53, "y": 0.6, "z": 0.0, "visibility": 0.9},  # right hip
            {"x": 0.45, "y": 0.8, "z": 0.0, "visibility": 0.8},  # left knee
            {"x": 0.55, "y": 0.8, "z": 0.0, "visibility": 0.8},  # right knee
            {"x": 0.43, "y": 0.95, "z": 0.0, "visibility": 0.7}, # left ankle
            {"x": 0.57, "y": 0.95, "z": 0.0, "visibility": 0.7}, # right ankle
            {"x": 0.41, "y": 0.98, "z": 0.0, "visibility": 0.6}, # left heel
            {"x": 0.59, "y": 0.98, "z": 0.0, "visibility": 0.6}, # right heel
            {"x": 0.4, "y": 0.99, "z": 0.0, "visibility": 0.6},  # left foot index
            {"x": 0.6, "y": 0.99, "z": 0.0, "visibility": 0.6},  # right foot index
        ]
        landmarks.extend(lower_body)
        
        return {
            "success": True,
            "landmarks": landmarks,
            "image_shape": image_shape,
            "num_landmarks": len(landmarks)
        }
    
    async def _calculate_joint_angles(
        self,
        landmarks: List[Dict[str, float]],
        image_shape: Tuple[int, int, int]
    ) -> Dict[str, float]:
        """
        Calculate joint angles from pose landmarks
        
        Args:
            landmarks: List of pose landmark points
            image_shape: Shape of the input image
            
        Returns:
            Dictionary of joint angles in degrees
        """
        joint_angles = {}
        
        try:
            for joint_name, landmark_indices in self.joint_connections.items():
                if len(landmark_indices) >= 3 and all(i < len(landmarks) for i in landmark_indices):
                    # Get the three points for angle calculation
                    p1 = landmarks[landmark_indices[0]]
                    p2 = landmarks[landmark_indices[1]]  # vertex of angle
                    p3 = landmarks[landmark_indices[2]]
                    
                    # Calculate angle
                    angle = self._calculate_angle_between_points(p1, p2, p3)
                    joint_angles[joint_name] = angle
                    
        except Exception as e:
            self.logger.debug(f"Joint angle calculation warning: {e}")
        
        return joint_angles
    
    def _calculate_angle_between_points(
        self,
        p1: Dict[str, float],
        p2: Dict[str, float],
        p3: Dict[str, float]
    ) -> float:
        """
        Calculate angle between three points
        
        Args:
            p1: First point
            p2: Vertex point
            p3: Third point
            
        Returns:
            Angle in degrees
        """
        try:
            # Convert to numpy arrays
            a = np.array([p1["x"], p1["y"]])
            b = np.array([p2["x"], p2["y"]])
            c = np.array([p3["x"], p3["y"]])
            
            # Calculate vectors
            ba = a - b
            bc = c - b
            
            # Calculate angle using dot product
            cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
            
            # Clamp to valid range for arccos
            cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
            
            # Calculate angle in radians then convert to degrees
            angle = np.arccos(cosine_angle)
            angle_degrees = np.degrees(angle)
            
            return float(angle_degrees)
            
        except Exception as e:
            self.logger.debug(f"Angle calculation error: {e}")
            return 90.0  # Default angle
    
    async def _calculate_range_of_motion(
        self,
        joint_angles: Dict[str, float],
        session_id: str
    ) -> Dict[str, float]:
        """
        Calculate range of motion for joints
        
        Args:
            joint_angles: Current joint angles
            session_id: Session ID for historical data
            
        Returns:
            Dictionary of range of motion measurements
        """
        range_of_motion = {}
        
        if session_id not in self.active_sessions:
            return range_of_motion
        
        session = self.active_sessions[session_id]
        
        for joint_name, current_angle in joint_angles.items():
            # Get historical angles for this joint
            if joint_name not in session["statistics"]["joint_angles"]:
                session["statistics"]["joint_angles"][joint_name] = []
            
            joint_history = session["statistics"]["joint_angles"][joint_name]
            joint_history.append(current_angle)
            
            # Keep only recent measurements (last 50)
            if len(joint_history) > 50:
                joint_history = joint_history[-50:]
                session["statistics"]["joint_angles"][joint_name] = joint_history
            
            # Calculate range of motion
            if len(joint_history) >= 2:
                min_angle = min(joint_history)
                max_angle = max(joint_history)
                range_of_motion[joint_name] = max_angle - min_angle
            else:
                range_of_motion[joint_name] = 0.0
        
        return range_of_motion
    
    async def _assess_movement_quality(
        self,
        landmarks: List[Dict[str, float]],
        joint_angles: Dict[str, float],
        range_of_motion: Dict[str, float],
        session_id: str
    ) -> Dict[str, Any]:
        """
        Assess movement quality based on various factors
        
        Args:
            landmarks: Pose landmarks
            joint_angles: Joint angles
            range_of_motion: Range of motion data
            session_id: Session ID
            
        Returns:
            Movement quality metrics
        """
        metrics = {
            "quality": 0.0,
            "smoothness": 0.0,
            "symmetry": 0.0,
            "range_score": 0.0,
            "stability": 0.0
        }
        
        try:
            # Calculate overall visibility score
            visibility_scores = [lm.get("visibility", 0.5) for lm in landmarks]
            avg_visibility = sum(visibility_scores) / len(visibility_scores) if visibility_scores else 0.5
            
            # Range of motion score
            range_scores = []
            for joint_name, rom in range_of_motion.items():
                joint_type = joint_name.split('_')[1] if '_' in joint_name else joint_name
                normal_range = self.normal_ranges.get(joint_type, {}).get("flexion", 90)
                range_score = min(1.0, rom / normal_range)
                range_scores.append(range_score)
            
            metrics["range_score"] = sum(range_scores) / len(range_scores) if range_scores else 0.5
            
            # Symmetry score (compare left and right sides)
            symmetry_scores = []
            left_joints = {k: v for k, v in joint_angles.items() if "left" in k}
            right_joints = {k: v for k, v in joint_angles.items() if "right" in k}
            
            for left_joint, left_angle in left_joints.items():
                right_joint = left_joint.replace("left", "right")
                if right_joint in right_joints:
                    angle_diff = abs(left_angle - right_joints[right_joint])
                    symmetry_score = max(0, 1.0 - angle_diff / 180.0)
                    symmetry_scores.append(symmetry_score)
            
            metrics["symmetry"] = sum(symmetry_scores) / len(symmetry_scores) if symmetry_scores else 0.8
            
            # Smoothness (based on angle changes over time)
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                if len(session["movements"]) > 1:
                    # Calculate smoothness based on recent movements
                    recent_movements = session["movements"][-5:]  # Last 5 movements
                    smoothness_scores = []
                    
                    for joint_name in joint_angles.keys():
                        joint_changes = []
                        for i in range(1, len(recent_movements)):
                            prev_angle = recent_movements[i-1].get("joint_angles", {}).get(joint_name, 0)
                            curr_angle = recent_movements[i].get("joint_angles", {}).get(joint_name, 0)
                            change = abs(curr_angle - prev_angle)
                            joint_changes.append(change)
                        
                        if joint_changes:
                            avg_change = sum(joint_changes) / len(joint_changes)
                            smoothness_score = max(0, 1.0 - avg_change / 45.0)  # Penalize large changes
                            smoothness_scores.append(smoothness_score)
                    
                    metrics["smoothness"] = sum(smoothness_scores) / len(smoothness_scores) if smoothness_scores else 0.7
                else:
                    metrics["smoothness"] = 0.7
            
            # Stability (based on landmark visibility and consistency)
            metrics["stability"] = avg_visibility
            
            # Overall quality score
            metrics["quality"] = (
                metrics["range_score"] * 0.3 +
                metrics["symmetry"] * 0.25 +
                metrics["smoothness"] * 0.25 +
                metrics["stability"] * 0.2
            )
            
        except Exception as e:
            self.logger.debug(f"Movement quality assessment warning: {e}")
            # Return default scores
            metrics = {
                "quality": 0.6,
                "smoothness": 0.6,
                "symmetry": 0.7,
                "range_score": 0.5,
                "stability": 0.6
            }
        
        return metrics
    
    def _decode_base64_image(self, frame_data: str) -> Optional[np.ndarray]:
        """
        Decode base64 image data to OpenCV format
        
        Args:
            frame_data: Base64 encoded image
            
        Returns:
            OpenCV image array or None if failed
        """
        try:
            # Remove data URL prefix if present
            if frame_data.startswith('data:image/'):
                frame_data = frame_data.split(',', 1)[1]
            
            # Decode base64
            image_bytes = base64.b64decode(frame_data)
            
            # Convert to PIL Image
            pil_image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to OpenCV format
            opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            return opencv_image
            
        except Exception as e:
            self.logger.error(f"Image decoding error: {e}")
            return None
    
    async def _update_session_movement(
        self,
        session_id: str,
        landmarks: List[Dict[str, float]],
        joint_angles: Dict[str, float],
        range_of_motion: Dict[str, float],
        movement_metrics: Dict[str, Any]
    ) -> None:
        """
        Update session with new movement data
        
        Args:
            session_id: Session ID
            landmarks: Pose landmarks
            joint_angles: Joint angles
            range_of_motion: Range of motion data
            movement_metrics: Movement quality metrics
        """
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        
        # Add movement record
        movement = {
            "timestamp": datetime.utcnow().isoformat(),
            "landmarks": landmarks,
            "joint_angles": joint_angles,
            "range_of_motion": range_of_motion,
            "metrics": movement_metrics
        }
        
        session["movements"].append(movement)
        session["pose_history"].append(landmarks)
        
        # Update statistics
        stats = session["statistics"]
        stats["total_movements"] += 1
        
        # Update average quality
        quality_scores = [m["metrics"]["quality"] for m in session["movements"]]
        stats["average_quality"] = sum(quality_scores) / len(quality_scores)
        
        # Update range of motion statistics
        for joint_name, rom in range_of_motion.items():
            if joint_name not in stats["range_of_motion"]:
                stats["range_of_motion"][joint_name] = {"min": rom, "max": rom, "current": rom}
            else:
                stats["range_of_motion"][joint_name]["min"] = min(stats["range_of_motion"][joint_name]["min"], rom)
                stats["range_of_motion"][joint_name]["max"] = max(stats["range_of_motion"][joint_name]["max"], rom)
                stats["range_of_motion"][joint_name]["current"] = rom
        
        # Calculate session score
        stats["session_score"] = int(stats["average_quality"] * 100)
    
    def _generate_movement_feedback(
        self,
        joint_angles: Dict[str, float],
        range_of_motion: Dict[str, float],
        movement_metrics: Dict[str, Any],
        session_id: str
    ) -> str:
        """
        Generate feedback message for movement quality
        
        Args:
            joint_angles: Joint angles
            range_of_motion: Range of motion data
            movement_metrics: Movement quality metrics
            session_id: Session ID
            
        Returns:
            Feedback message string
        """
        if session_id not in self.active_sessions:
            return "Keep up the good work with your therapeutic exercises!"
        
        session = self.active_sessions[session_id]
        exercise_type = session["exercise_type"]
        quality = movement_metrics["quality"]
        
        if quality >= 0.8:
            return f"Excellent form! Your {exercise_type} technique is very good."
        elif quality >= 0.6:
            return f"Good movement quality. Try to maintain smooth, controlled motions."
        elif quality >= 0.4:
            return f"Fair technique. Focus on slower, more deliberate movements."
        else:
            return f"Keep practicing! Remember to move slowly and maintain good posture."
    
    async def session_exists(self, session_id: str) -> bool:
        """
        Check if session exists
        
        Args:
            session_id: Session ID to check
            
        Returns:
            True if session exists, False otherwise
        """
        return session_id in self.active_sessions
    
    async def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session data
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None if not found
        """
        return self.active_sessions.get(session_id)
    
    async def update_session_data(
        self,
        session_id: str,
        movement_data: List[Dict[str, Any]],
        joint_angles: Dict[str, List[float]],
        range_of_motion: Dict[str, Dict[str, float]],
        session_duration: int,
        metrics: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Update session with final data
        
        Args:
            session_id: Session ID
            movement_data: Movement landmarks data
            joint_angles: Joint angle measurements
            range_of_motion: Range of motion data
            session_duration: Session duration in milliseconds
            metrics: Movement quality metrics
            
        Returns:
            Updated session data
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        # Update session with final data
        session["final_data"] = {
            "movement_data": movement_data,
            "joint_angles": joint_angles,
            "range_of_motion": range_of_motion,
            "session_duration": session_duration,
            "metrics": metrics,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        session["status"] = "completed"
        
        # Calculate final statistics
        avg_quality = sum(m.get("quality", 0) for m in metrics) / len(metrics) if metrics else 0
        
        # Calculate joint improvements
        joint_improvements = {}
        for joint_name, angles in joint_angles.items():
            if len(angles) >= 2:
                initial_range = max(angles[:len(angles)//2]) - min(angles[:len(angles)//2]) if len(angles) >= 4 else 0
                final_range = max(angles[len(angles)//2:]) - min(angles[len(angles)//2:]) if len(angles) >= 4 else 0
                improvement = final_range - initial_range
                joint_improvements[joint_name] = {
                    "initial_range": initial_range,
                    "final_range": final_range,
                    "improvement": improvement
                }
        
        session["final_statistics"] = {
            "total_movements": len(movement_data),
            "average_quality": round(avg_quality, 3),
            "session_score": int(avg_quality * 100),
            "session_duration_seconds": session_duration / 1000,
            "joint_improvements": joint_improvements,
            "range_of_motion_summary": range_of_motion
        }
        
        return session
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Session ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True
        return False
    
    async def get_user_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get user statistics for therapy sessions
        
        Args:
            user_id: User ID (optional)
            
        Returns:
            User statistics dictionary
        """
        # Filter sessions by user_id if provided
        user_sessions = []
        for session in self.active_sessions.values():
            if user_id is None or session.get("user_id") == user_id:
                user_sessions.append(session)
        
        if not user_sessions:
            return {
                "total_sessions": 0,
                "average_quality": 0.0,
                "favorite_exercises": [],
                "recent_sessions": [],
                "progress_trend": [],
                "joint_improvements": {}
            }
        
        # Calculate statistics
        completed_sessions = [s for s in user_sessions if s.get("status") == "completed"]
        
        total_sessions = len(completed_sessions)
        
        # Average quality
        qualities = [s.get("final_statistics", {}).get("average_quality", 0) for s in completed_sessions]
        average_quality = sum(qualities) / len(qualities) if qualities else 0.0
        
        # Favorite exercises (most practiced)
        exercise_counts = {}
        for session in completed_sessions:
            exercise = session.get("exercise_type")
            if exercise:
                exercise_counts[exercise] = exercise_counts.get(exercise, 0) + 1
        
        favorite_exercises = [
            {"exercise": exercise, "count": count}
            for exercise, count in sorted(exercise_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        ]
        
        # Recent sessions
        recent_sessions = sorted(
            completed_sessions,
            key=lambda x: x.get("final_data", {}).get("completed_at", ""),
            reverse=True
        )[:5]
        
        recent_sessions_data = [
            {
                "session_id": s["session_id"],
                "exercise_type": s["exercise_type"],
                "quality": s.get("final_statistics", {}).get("average_quality", 0),
                "completed_at": s.get("final_data", {}).get("completed_at")
            }
            for s in recent_sessions
        ]
        
        # Progress trend (last 10 sessions)
        progress_trend = [
            {
                "session_number": i + 1,
                "quality": s.get("final_statistics", {}).get("average_quality", 0),
                "date": s.get("final_data", {}).get("completed_at", "")[:10]  # Date only
            }
            for i, s in enumerate(recent_sessions[:10])
        ]
        
        # Joint improvements summary
        joint_improvements = {}
        for session in completed_sessions:
            improvements = session.get("final_statistics", {}).get("joint_improvements", {})
            for joint_name, improvement_data in improvements.items():
                if joint_name not in joint_improvements:
                    joint_improvements[joint_name] = {
                        "total_improvement": 0,
                        "session_count": 0,
                        "average_improvement": 0
                    }
                
                joint_improvements[joint_name]["total_improvement"] += improvement_data.get("improvement", 0)
                joint_improvements[joint_name]["session_count"] += 1
                joint_improvements[joint_name]["average_improvement"] = (
                    joint_improvements[joint_name]["total_improvement"] / 
                    joint_improvements[joint_name]["session_count"]
                )
        
        return {
            "total_sessions": total_sessions,
            "average_quality": round(average_quality, 3),
            "favorite_exercises": favorite_exercises,
            "recent_sessions": recent_sessions_data,
            "progress_trend": progress_trend,
            "joint_improvements": joint_improvements
        }