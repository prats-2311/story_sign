"""
Harmony service for facial expression analysis and emotion detection
Handles MediaPipe facial landmark processing and emotion classification
"""

import logging
import asyncio
import base64
import io
import uuid
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image
import cv2

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    logging.warning("MediaPipe not available - using mock emotion detection")

from core.base_service import BaseService


class HarmonyService(BaseService):
    """
    Service for facial expression analysis and emotion detection using MediaPipe
    """
    
    def __init__(self, service_name: str = "HarmonyService", config: Optional[Dict[str, Any]] = None, db_service=None):
        super().__init__(service_name, config)
        self.db_service = db_service
        
        # MediaPipe setup
        if MEDIAPIPE_AVAILABLE:
            self.mp_face_mesh = mp.solutions.face_mesh
            self.mp_drawing = mp.solutions.drawing_utils
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
        else:
            self.mp_face_mesh = None
            self.face_mesh = None
        
        # Emotion classification thresholds and mappings
        self.emotion_thresholds = {
            "happy": {"mouth_curve": 0.02, "eye_crinkle": 0.01},
            "sad": {"mouth_curve": -0.02, "eyebrow_lower": 0.01},
            "surprised": {"eyebrow_raise": 0.03, "mouth_open": 0.02},
            "angry": {"eyebrow_furrow": 0.02, "mouth_tense": 0.01},
            "fearful": {"eyebrow_raise": 0.02, "eye_widen": 0.02},
            "disgusted": {"nose_wrinkle": 0.01, "upper_lip_raise": 0.01},
            "neutral": {"all_features": 0.005}  # Low activity threshold
        }
        
        # Session storage (in production, this would be in database)
        self.active_sessions = {}
        
    async def initialize(self) -> None:
        """Initialize harmony service"""
        self.logger.info("Harmony service initialized")
        if not MEDIAPIPE_AVAILABLE:
            self.logger.warning("MediaPipe not available - emotion detection will use mock data")
    
    async def cleanup(self) -> None:
        """Clean up harmony service"""
        if self.face_mesh:
            self.face_mesh.close()
    
    async def create_emotion_session(
        self,
        target_emotion: str,
        difficulty_level: str = "normal",
        expected_duration: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new emotion practice session
        
        Args:
            target_emotion: Target emotion to practice
            difficulty_level: Difficulty level (easy, normal, hard)
            expected_duration: Expected session duration in seconds
            user_id: User ID (optional)
            
        Returns:
            Session data dictionary
        """
        session_id = str(uuid.uuid4())
        
        session_data = {
            "session_id": session_id,
            "target_emotion": target_emotion,
            "difficulty_level": difficulty_level,
            "expected_duration": expected_duration,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "status": "active",
            "detections": [],
            "landmarks_history": [],
            "statistics": {
                "total_detections": 0,
                "target_matches": 0,
                "average_confidence": 0.0,
                "session_score": 0
            }
        }
        
        # Store session (in production, save to database)
        self.active_sessions[session_id] = session_data
        
        self.logger.info(f"Created emotion session: {session_id} for emotion: {target_emotion}")
        return session_data
    
    async def detect_emotion_from_frame(
        self,
        frame_data: str,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Detect emotion from a single frame
        
        Args:
            frame_data: Base64 encoded image data
            session_id: Session ID for tracking
            
        Returns:
            Detection result dictionary
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
            
            # Detect facial landmarks
            landmarks_result = await self._detect_facial_landmarks(rgb_image)
            
            if not landmarks_result["success"]:
                return {
                    "success": False,
                    "error": landmarks_result["error"]
                }
            
            # Classify emotion from landmarks
            emotion_result = await self._classify_emotion_from_landmarks(
                landmarks_result["landmarks"],
                landmarks_result["image_shape"]
            )
            
            # Update session with detection
            if session_id in self.active_sessions:
                await self._update_session_detection(
                    session_id,
                    emotion_result["detected_emotion"],
                    emotion_result["confidence_score"],
                    landmarks_result["landmarks"]
                )
            
            # Generate feedback message
            feedback_message = self._generate_feedback_message(
                emotion_result["detected_emotion"],
                emotion_result["confidence_score"],
                session_id
            )
            
            return {
                "success": True,
                "detected_emotion": emotion_result["detected_emotion"],
                "confidence_score": emotion_result["confidence_score"],
                "facial_landmarks": landmarks_result["landmarks"],
                "feedback_message": feedback_message,
                "processing_time": emotion_result.get("processing_time", 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error in emotion detection: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Emotion detection failed: {str(e)}"
            }
    
    async def _detect_facial_landmarks(self, rgb_image: np.ndarray) -> Dict[str, Any]:
        """
        Detect facial landmarks using MediaPipe
        
        Args:
            rgb_image: RGB image array
            
        Returns:
            Landmarks detection result
        """
        if not MEDIAPIPE_AVAILABLE or not self.face_mesh:
            # Mock landmarks for testing
            return await self._mock_facial_landmarks(rgb_image.shape)
        
        try:
            # Process image with MediaPipe
            results = self.face_mesh.process(rgb_image)
            
            if not results.multi_face_landmarks:
                return {
                    "success": False,
                    "error": "No face detected in image"
                }
            
            # Extract landmarks from first detected face
            face_landmarks = results.multi_face_landmarks[0]
            
            # Convert landmarks to normalized coordinates
            landmarks = []
            for landmark in face_landmarks.landmark:
                landmarks.append({
                    "x": landmark.x,
                    "y": landmark.y,
                    "z": landmark.z
                })
            
            return {
                "success": True,
                "landmarks": landmarks,
                "image_shape": rgb_image.shape,
                "num_landmarks": len(landmarks)
            }
            
        except Exception as e:
            self.logger.error(f"MediaPipe landmark detection error: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Landmark detection failed: {str(e)}"
            }
    
    async def _mock_facial_landmarks(self, image_shape: Tuple[int, int, int]) -> Dict[str, Any]:
        """
        Generate mock facial landmarks for testing when MediaPipe is not available
        
        Args:
            image_shape: Shape of the input image
            
        Returns:
            Mock landmarks result
        """
        # Generate basic facial landmark points
        landmarks = []
        
        # Face outline (simplified)
        for i in range(17):
            x = 0.2 + (i / 16) * 0.6
            y = 0.3 + 0.1 * np.sin(i * np.pi / 8)
            landmarks.append({"x": x, "y": y, "z": 0.0})
        
        # Eyes (simplified)
        # Left eye
        for i in range(6):
            x = 0.35 + (i / 5) * 0.1
            y = 0.4 + 0.02 * np.sin(i * np.pi / 3)
            landmarks.append({"x": x, "y": y, "z": 0.0})
        
        # Right eye
        for i in range(6):
            x = 0.55 + (i / 5) * 0.1
            y = 0.4 + 0.02 * np.sin(i * np.pi / 3)
            landmarks.append({"x": x, "y": y, "z": 0.0})
        
        # Nose (simplified)
        for i in range(9):
            x = 0.48 + (i / 8) * 0.04
            y = 0.5 + (i / 8) * 0.1
            landmarks.append({"x": x, "y": y, "z": 0.0})
        
        # Mouth (simplified)
        for i in range(20):
            x = 0.4 + (i / 19) * 0.2
            y = 0.65 + 0.03 * np.sin(i * np.pi / 10)
            landmarks.append({"x": x, "y": y, "z": 0.0})
        
        return {
            "success": True,
            "landmarks": landmarks,
            "image_shape": image_shape,
            "num_landmarks": len(landmarks)
        }
    
    async def _classify_emotion_from_landmarks(
        self,
        landmarks: List[Dict[str, float]],
        image_shape: Tuple[int, int, int]
    ) -> Dict[str, Any]:
        """
        Classify emotion based on facial landmarks
        
        Args:
            landmarks: List of facial landmark points
            image_shape: Shape of the input image
            
        Returns:
            Emotion classification result
        """
        try:
            # Extract key facial features
            features = self._extract_facial_features(landmarks)
            
            # Calculate emotion scores
            emotion_scores = {}
            
            for emotion, thresholds in self.emotion_thresholds.items():
                score = self._calculate_emotion_score(emotion, features, thresholds)
                emotion_scores[emotion] = score
            
            # Find best matching emotion
            best_emotion = max(emotion_scores, key=emotion_scores.get)
            confidence = emotion_scores[best_emotion]
            
            # Normalize confidence to 0-1 range
            confidence = min(1.0, max(0.0, confidence))
            
            return {
                "detected_emotion": best_emotion,
                "confidence_score": confidence,
                "all_scores": emotion_scores,
                "features": features
            }
            
        except Exception as e:
            self.logger.error(f"Emotion classification error: {e}", exc_info=True)
            # Return neutral emotion as fallback
            return {
                "detected_emotion": "neutral",
                "confidence_score": 0.5,
                "all_scores": {"neutral": 0.5},
                "features": {}
            }
    
    def _extract_facial_features(self, landmarks: List[Dict[str, float]]) -> Dict[str, float]:
        """
        Extract key facial features from landmarks
        
        Args:
            landmarks: List of facial landmark points
            
        Returns:
            Dictionary of extracted features
        """
        if len(landmarks) < 50:  # Minimum landmarks needed
            return {}
        
        features = {}
        
        try:
            # Mouth curvature (smile/frown detection)
            if len(landmarks) > 60:
                mouth_left = landmarks[48] if len(landmarks) > 48 else landmarks[40]
                mouth_right = landmarks[54] if len(landmarks) > 54 else landmarks[44]
                mouth_center = landmarks[51] if len(landmarks) > 51 else landmarks[42]
                
                mouth_curve = (mouth_left["y"] + mouth_right["y"]) / 2 - mouth_center["y"]
                features["mouth_curve"] = mouth_curve
            
            # Eyebrow position (surprise/anger detection)
            if len(landmarks) > 25:
                eyebrow_left = landmarks[19] if len(landmarks) > 19 else landmarks[15]
                eyebrow_right = landmarks[24] if len(landmarks) > 24 else landmarks[20]
                eye_left = landmarks[37] if len(landmarks) > 37 else landmarks[25]
                eye_right = landmarks[44] if len(landmarks) > 44 else landmarks[30]
                
                eyebrow_height = ((eyebrow_left["y"] + eyebrow_right["y"]) / 2) - ((eye_left["y"] + eye_right["y"]) / 2)
                features["eyebrow_height"] = eyebrow_height
            
            # Eye openness (surprise/sleepy detection)
            if len(landmarks) > 45:
                eye_top = landmarks[37] if len(landmarks) > 37 else landmarks[25]
                eye_bottom = landmarks[41] if len(landmarks) > 41 else landmarks[29]
                
                eye_openness = abs(eye_top["y"] - eye_bottom["y"])
                features["eye_openness"] = eye_openness
            
            # Mouth openness (surprise detection)
            if len(landmarks) > 65:
                mouth_top = landmarks[51] if len(landmarks) > 51 else landmarks[42]
                mouth_bottom = landmarks[57] if len(landmarks) > 57 else landmarks[46]
                
                mouth_openness = abs(mouth_top["y"] - mouth_bottom["y"])
                features["mouth_openness"] = mouth_openness
            
        except (IndexError, KeyError) as e:
            self.logger.debug(f"Feature extraction warning: {e}")
        
        return features
    
    def _calculate_emotion_score(
        self,
        emotion: str,
        features: Dict[str, float],
        thresholds: Dict[str, float]
    ) -> float:
        """
        Calculate emotion score based on features and thresholds
        
        Args:
            emotion: Emotion name
            features: Extracted facial features
            thresholds: Emotion-specific thresholds
            
        Returns:
            Emotion score (0-1)
        """
        if not features:
            return 0.5 if emotion == "neutral" else 0.0
        
        score = 0.0
        feature_count = 0
        
        # Happy: positive mouth curve, eye crinkles
        if emotion == "happy":
            if "mouth_curve" in features:
                mouth_score = max(0, features["mouth_curve"] * 10)  # Scale up
                score += mouth_score
                feature_count += 1
        
        # Sad: negative mouth curve, lowered eyebrows
        elif emotion == "sad":
            if "mouth_curve" in features:
                mouth_score = max(0, -features["mouth_curve"] * 10)  # Negative curve
                score += mouth_score
                feature_count += 1
        
        # Surprised: raised eyebrows, open mouth
        elif emotion == "surprised":
            if "eyebrow_height" in features:
                eyebrow_score = max(0, -features["eyebrow_height"] * 20)  # Raised eyebrows
                score += eyebrow_score
                feature_count += 1
            if "mouth_openness" in features:
                mouth_score = features["mouth_openness"] * 15
                score += mouth_score
                feature_count += 1
        
        # Angry: lowered eyebrows, tense mouth
        elif emotion == "angry":
            if "eyebrow_height" in features:
                eyebrow_score = max(0, features["eyebrow_height"] * 15)  # Lowered eyebrows
                score += eyebrow_score
                feature_count += 1
        
        # Fearful: raised eyebrows, wide eyes
        elif emotion == "fearful":
            if "eyebrow_height" in features:
                eyebrow_score = max(0, -features["eyebrow_height"] * 15)  # Raised eyebrows
                score += eyebrow_score
                feature_count += 1
            if "eye_openness" in features:
                eye_score = features["eye_openness"] * 20
                score += eye_score
                feature_count += 1
        
        # Neutral: low activity in all features
        elif emotion == "neutral":
            total_activity = sum(abs(v) for v in features.values())
            score = max(0, 1.0 - total_activity * 5)  # Higher score for less activity
            feature_count = 1
        
        # Average the scores
        if feature_count > 0:
            score = score / feature_count
        
        # Add some randomness for more realistic mock behavior
        import random
        score += random.uniform(-0.1, 0.1)
        
        return max(0.0, min(1.0, score))
    
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
    
    async def _update_session_detection(
        self,
        session_id: str,
        detected_emotion: str,
        confidence_score: float,
        landmarks: List[Dict[str, float]]
    ) -> None:
        """
        Update session with new detection data
        
        Args:
            session_id: Session ID
            detected_emotion: Detected emotion
            confidence_score: Confidence score
            landmarks: Facial landmarks
        """
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        
        # Add detection
        detection = {
            "timestamp": datetime.utcnow().isoformat(),
            "detected_emotion": detected_emotion,
            "confidence_score": confidence_score,
            "is_target_match": detected_emotion == session["target_emotion"]
        }
        
        session["detections"].append(detection)
        session["landmarks_history"].append(landmarks)
        
        # Update statistics
        stats = session["statistics"]
        stats["total_detections"] += 1
        
        if detection["is_target_match"]:
            stats["target_matches"] += 1
        
        # Calculate average confidence
        total_confidence = sum(d["confidence_score"] for d in session["detections"])
        stats["average_confidence"] = total_confidence / len(session["detections"])
        
        # Calculate session score (accuracy * confidence)
        accuracy = stats["target_matches"] / stats["total_detections"]
        stats["session_score"] = int((accuracy * 0.7 + stats["average_confidence"] * 0.3) * 100)
    
    def _generate_feedback_message(
        self,
        detected_emotion: str,
        confidence_score: float,
        session_id: str
    ) -> str:
        """
        Generate feedback message for the user
        
        Args:
            detected_emotion: Detected emotion
            confidence_score: Confidence score
            session_id: Session ID
            
        Returns:
            Feedback message string
        """
        if session_id not in self.active_sessions:
            return "Keep practicing your facial expressions!"
        
        session = self.active_sessions[session_id]
        target_emotion = session["target_emotion"]
        
        if detected_emotion == target_emotion:
            if confidence_score >= 0.8:
                return f"Excellent {target_emotion} expression! Very clear and natural."
            elif confidence_score >= 0.6:
                return f"Good {target_emotion} expression! Try to make it a bit more distinct."
            else:
                return f"Nice try! Your {target_emotion} expression could be more pronounced."
        else:
            return f"I detected {detected_emotion}, but you're practicing {target_emotion}. Try again!"
    
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
        detected_emotions: List[str],
        confidence_scores: List[float],
        landmarks_data: List[Dict[str, Any]],
        session_duration: int
    ) -> Dict[str, Any]:
        """
        Update session with final data
        
        Args:
            session_id: Session ID
            detected_emotions: List of detected emotions
            confidence_scores: List of confidence scores
            landmarks_data: List of landmarks data
            session_duration: Session duration in milliseconds
            
        Returns:
            Updated session data
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        # Update session with final data
        session["final_data"] = {
            "detected_emotions": detected_emotions,
            "confidence_scores": confidence_scores,
            "landmarks_data": landmarks_data,
            "session_duration": session_duration,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        session["status"] = "completed"
        
        # Calculate final statistics
        target_emotion = session["target_emotion"]
        target_matches = sum(1 for emotion in detected_emotions if emotion == target_emotion)
        accuracy = (target_matches / len(detected_emotions)) * 100 if detected_emotions else 0
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        session["final_statistics"] = {
            "total_detections": len(detected_emotions),
            "target_matches": target_matches,
            "accuracy_percentage": round(accuracy, 1),
            "average_confidence": round(avg_confidence, 3),
            "session_score": int((accuracy * 0.7 + avg_confidence * 100 * 0.3)),
            "session_duration_seconds": session_duration / 1000
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
        Get user statistics for emotion practice
        
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
                "average_accuracy": 0.0,
                "favorite_emotions": [],
                "recent_sessions": [],
                "progress_trend": []
            }
        
        # Calculate statistics
        completed_sessions = [s for s in user_sessions if s.get("status") == "completed"]
        
        total_sessions = len(completed_sessions)
        
        # Average accuracy
        accuracies = [s.get("final_statistics", {}).get("accuracy_percentage", 0) for s in completed_sessions]
        average_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0
        
        # Favorite emotions (most practiced)
        emotion_counts = {}
        for session in completed_sessions:
            emotion = session.get("target_emotion")
            if emotion:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        favorite_emotions = [
            {"emotion": emotion, "count": count}
            for emotion, count in sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)[:3]
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
                "target_emotion": s["target_emotion"],
                "accuracy": s.get("final_statistics", {}).get("accuracy_percentage", 0),
                "completed_at": s.get("final_data", {}).get("completed_at")
            }
            for s in recent_sessions
        ]
        
        # Progress trend (last 10 sessions)
        progress_trend = [
            {
                "session_number": i + 1,
                "accuracy": s.get("final_statistics", {}).get("accuracy_percentage", 0),
                "date": s.get("final_data", {}).get("completed_at", "")[:10]  # Date only
            }
            for i, s in enumerate(recent_sessions[:10])
        ]
        
        return {
            "total_sessions": total_sessions,
            "average_accuracy": round(average_accuracy, 1),
            "favorite_emotions": favorite_emotions,
            "recent_sessions": recent_sessions_data,
            "progress_trend": progress_trend
        }