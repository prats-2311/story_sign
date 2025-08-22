#!/usr/bin/env python3
"""
Video processing module for MediaPipe integration
Handles frame decoding, MediaPipe processing, and landmark drawing
"""

import base64
import cv2
import numpy as np
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
import time

from config import MediaPipeConfig, VideoConfig, GestureDetectionConfig

# Initialize logger first
logger = logging.getLogger(__name__)

# Try to import MediaPipe, fall back to mock if not available
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
    logger.info("✅ Real MediaPipe imported successfully")
except ImportError:
    logger.warning("⚠️ MediaPipe not available, importing mock implementation")
    try:
        import mock_mediapipe
        import mediapipe as mp
        MEDIAPIPE_AVAILABLE = False
        logger.info("✅ Mock MediaPipe imported successfully")
    except ImportError:
        logger.error("❌ Failed to import mock MediaPipe")
        MEDIAPIPE_AVAILABLE = False
        # Create minimal mock MediaPipe classes for compatibility
        class MockMediaPipe:
            class solutions:
                class holistic:
                    class Holistic:
                        def __init__(self, **kwargs):
                            pass
                        def process(self, image):
                            # Return mock results with no landmarks
                            class MockResults:
                                left_hand_landmarks = None
                                right_hand_landmarks = None
                                face_landmarks = None
                                pose_landmarks = None
                            return MockResults()
                        def close(self):
                            pass
                    
                    FACEMESH_CONTOURS = []
                    FACEMESH_TESSELATION = []
                    POSE_CONNECTIONS = []
                    HAND_CONNECTIONS = []
                
                class drawing_utils:
                    @staticmethod
                    def draw_landmarks(*args, **kwargs):
                        pass
                
                class drawing_styles:
                    @staticmethod
                    def get_default_face_mesh_contours_style():
                        return None
                    @staticmethod
                    def get_default_face_mesh_tesselation_style():
                        return None
                    @staticmethod
                    def get_default_pose_landmarks_style():
                        return None
                    @staticmethod
                    def get_default_pose_connections_style():
                        return None
                    @staticmethod
                    def get_default_hand_landmarks_style():
                        return None
                    @staticmethod
                    def get_default_hand_connections_style():
                        return None
        
        mp = MockMediaPipe()


class MediaPipeProcessor:
    """
    MediaPipe processor for holistic landmark detection
    Handles hands, face, and pose detection with drawing utilities
    """
    
    def __init__(self, mediapipe_config: MediaPipeConfig):
        """
        Initialize MediaPipe processor with configuration
        
        Args:
            mediapipe_config: MediaPipe configuration settings
        """
        self.config = mediapipe_config
        self.logger = logging.getLogger(f"{__name__}.MediaPipeProcessor")
        
        # Debug logging
        self.logger.info(f"🔍 MEDIAPIPE_AVAILABLE flag: {MEDIAPIPE_AVAILABLE}")
        
        # Initialize MediaPipe components
        self.mp_holistic = mp.solutions.holistic
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Initialize holistic model with maximum speed optimization (complexity 0)
        self.holistic = self.mp_holistic.Holistic(
            min_detection_confidence=0.3,  # Lowered for maximum speed
            min_tracking_confidence=0.3,   # Lowered for maximum speed
            model_complexity=0,  # Use fastest "Lite" model for maximum speed
            enable_segmentation=False,  # Disable segmentation for speed
            refine_face_landmarks=False  # Disable face refinement for speed
        )
        
        if MEDIAPIPE_AVAILABLE:
            self.logger.info(f"✅ MediaPipe Holistic initialized with complexity {self.config.model_complexity}")
        else:
            self.logger.warning("❌ MediaPipe not available - using mock implementation for compatibility")
        
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict[str, bool]]:
        """
        Process frame through MediaPipe Holistic model optimized for low latency
        
        Args:
            frame: Input frame as numpy array (BGR format)
            
        Returns:
            Tuple of (processed_frame, landmarks_detected_dict)
        """
        processing_attempts = 0
        max_attempts = 2  # Reduced from 3 for faster failure recovery
        
        while processing_attempts < max_attempts:
            try:
                processing_attempts += 1
                
                # Validate input frame
                if frame is None or frame.size == 0:
                    self.logger.warning("Invalid input frame received")
                    return self._create_fallback_frame(frame), {"hands": False, "face": False, "pose": False}
                
                # Check if MediaPipe is available
                if not MEDIAPIPE_AVAILABLE:
                    self.logger.debug("MediaPipe not available, returning original frame")
                    return frame, {"hands": False, "face": False, "pose": False}
                
                # Convert BGR to RGB for MediaPipe with error handling
                try:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                except cv2.error as e:
                    self.logger.error(f"Color conversion failed (attempt {processing_attempts}): {e}")
                    if processing_attempts >= max_attempts:
                        return frame, {"hands": False, "face": False, "pose": False}
                    continue
                
                # Process frame through MediaPipe with optimized settings
                try:
                    # Skip memory check for speed (comment out for production if needed)
                    # if hasattr(self, '_check_memory_usage'):
                    #     if not self._check_memory_usage():
                    #         self.logger.warning("Memory usage too high, skipping MediaPipe processing")
                    #         return frame, {"hands": False, "face": False, "pose": False}
                    
                    # Process with MediaPipe (optimized for speed)
                    results = self.holistic.process(rgb_frame)
                    
                    # Validate results
                    if results is None:
                        self.logger.warning(f"MediaPipe returned None results (attempt {processing_attempts})")
                        if processing_attempts >= max_attempts:
                            return frame, {"hands": False, "face": False, "pose": False}
                        continue
                        
                except Exception as e:
                    self.logger.error(f"MediaPipe processing failed (attempt {processing_attempts}): {e}")
                    if processing_attempts >= max_attempts:
                        # Final fallback - return original frame
                        return frame, {"hands": False, "face": False, "pose": False}
                    continue
                
                # Convert back to BGR for OpenCV drawing
                try:
                    processed_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
                except cv2.error as e:
                    self.logger.error(f"Color conversion back to BGR failed (attempt {processing_attempts}): {e}")
                    if processing_attempts >= max_attempts:
                        return frame, {"hands": False, "face": False, "pose": False}
                    continue
                
                # Track which landmarks were detected with enhanced null safety
                landmarks_detected = self._extract_landmarks_safely(results)
                
                # Draw landmarks on the frame with error handling
                try:
                    processed_frame = self._draw_landmarks(processed_frame, results)
                except Exception as e:
                    self.logger.warning(f"Landmark drawing failed (attempt {processing_attempts}), using frame without overlays: {e}")
                    # Continue with processed frame even if drawing fails
                
                # Success - return processed frame
                if processing_attempts > 1:
                    self.logger.info(f"MediaPipe processing succeeded on attempt {processing_attempts}")
                
                return processed_frame, landmarks_detected
                
            except Exception as e:
                self.logger.error(f"Critical error in MediaPipe frame processing (attempt {processing_attempts}): {e}", exc_info=True)
                if processing_attempts >= max_attempts:
                    # Final fallback - return original frame or create safe fallback
                    return self._create_fallback_frame(frame), {"hands": False, "face": False, "pose": False}
        
        # Should not reach here, but safety fallback
        self.logger.error("All MediaPipe processing attempts failed, using fallback frame")
        return self._create_fallback_frame(frame), {"hands": False, "face": False, "pose": False}
    
    def _extract_landmarks_safely(self, results) -> Dict[str, bool]:
        """
        Safely extract landmark detection status from MediaPipe results
        
        Args:
            results: MediaPipe holistic results
            
        Returns:
            Dictionary indicating which landmark types were detected
        """
        try:
            landmarks_detected = {
                "hands": False,
                "face": False,
                "pose": False
            }
            
            # Check hands landmarks with enhanced safety
            try:
                left_hand = getattr(results, 'left_hand_landmarks', None)
                right_hand = getattr(results, 'right_hand_landmarks', None)
                landmarks_detected["hands"] = bool(left_hand or right_hand)
            except Exception as e:
                self.logger.debug(f"Error checking hand landmarks: {e}")
            
            # Check face landmarks with enhanced safety
            try:
                face_landmarks = getattr(results, 'face_landmarks', None)
                landmarks_detected["face"] = bool(face_landmarks)
            except Exception as e:
                self.logger.debug(f"Error checking face landmarks: {e}")
            
            # Check pose landmarks with enhanced safety
            try:
                pose_landmarks = getattr(results, 'pose_landmarks', None)
                landmarks_detected["pose"] = bool(pose_landmarks)
            except Exception as e:
                self.logger.debug(f"Error checking pose landmarks: {e}")
            
            return landmarks_detected
            
        except Exception as e:
            self.logger.error(f"Error extracting landmarks safely: {e}")
            return {"hands": False, "face": False, "pose": False}
    
    def _check_memory_usage(self) -> bool:
        """
        Check if memory usage is within acceptable limits for processing
        
        Returns:
            True if memory usage is acceptable, False if too high
        """
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            # Limit to 1GB per process
            memory_limit_mb = 1024
            
            if memory_mb > memory_limit_mb:
                self.logger.warning(f"Memory usage too high: {memory_mb:.1f}MB (limit: {memory_limit_mb}MB)")
                return False
            
            return True
            
        except Exception as e:
            self.logger.debug(f"Memory check failed: {e}")
            return True  # Allow processing if check fails
    
    def _create_fallback_frame(self, original_frame: np.ndarray) -> np.ndarray:
        """
        Create fallback frame when processing fails
        
        Args:
            original_frame: Original input frame
            
        Returns:
            Fallback frame (original or blank if original is invalid)
        """
        try:
            if original_frame is not None and original_frame.size > 0:
                return original_frame.copy()
            else:
                # Create blank frame as last resort
                self.logger.warning("Creating blank fallback frame")
                return np.zeros((480, 640, 3), dtype=np.uint8)
        except Exception as e:
            self.logger.error(f"Failed to create fallback frame: {e}")
            # Return minimal valid frame
            return np.zeros((480, 640, 3), dtype=np.uint8)
    
    def _draw_landmarks(self, frame: np.ndarray, results) -> np.ndarray:
        """
        Draw MediaPipe landmarks on the frame with enhanced error handling
        
        Args:
            frame: Frame to draw on (BGR format)
            results: MediaPipe holistic results
            
        Returns:
            Frame with landmarks drawn (gracefully handles drawing failures)
        """
        if not MEDIAPIPE_AVAILABLE:
            # Skip drawing if MediaPipe is not available
            return frame
            
        try:
            # Validate frame before drawing
            if frame is None or frame.size == 0:
                self.logger.warning("Invalid frame for landmark drawing")
                return frame
            
            # Draw face landmarks with individual error handling
            try:
                if hasattr(results, 'face_landmarks') and results.face_landmarks:
                    self.mp_drawing.draw_landmarks(
                        frame,
                        results.face_landmarks,
                        self.mp_holistic.FACEMESH_CONTOURS,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=self.mp_drawing_styles
                        .get_default_face_mesh_contours_style()
                    )
            except Exception as e:
                self.logger.debug(f"Face landmark drawing failed: {e}")
            
            # Draw pose landmarks with individual error handling
            try:
                if hasattr(results, 'pose_landmarks') and results.pose_landmarks:
                    self.mp_drawing.draw_landmarks(
                        frame,
                        results.pose_landmarks,
                        self.mp_holistic.POSE_CONNECTIONS,
                        landmark_drawing_spec=self.mp_drawing_styles
                        .get_default_pose_landmarks_style(),
                        connection_drawing_spec=self.mp_drawing_styles
                        .get_default_pose_connections_style()
                    )
            except Exception as e:
                self.logger.debug(f"Pose landmark drawing failed: {e}")
            
            # Draw left hand landmarks with individual error handling
            try:
                if hasattr(results, 'left_hand_landmarks') and results.left_hand_landmarks:
                    self.mp_drawing.draw_landmarks(
                        frame,
                        results.left_hand_landmarks,
                        self.mp_holistic.HAND_CONNECTIONS,
                        landmark_drawing_spec=self.mp_drawing_styles
                        .get_default_hand_landmarks_style(),
                        connection_drawing_spec=self.mp_drawing_styles
                        .get_default_hand_connections_style()
                    )
            except Exception as e:
                self.logger.debug(f"Left hand landmark drawing failed: {e}")
            
            # Draw right hand landmarks with individual error handling
            try:
                if hasattr(results, 'right_hand_landmarks') and results.right_hand_landmarks:
                    self.mp_drawing.draw_landmarks(
                        frame,
                        results.right_hand_landmarks,
                        self.mp_holistic.HAND_CONNECTIONS,
                        landmark_drawing_spec=self.mp_drawing_styles
                        .get_default_hand_landmarks_style(),
                        connection_drawing_spec=self.mp_drawing_styles
                        .get_default_hand_connections_style()
                    )
            except Exception as e:
                self.logger.debug(f"Right hand landmark drawing failed: {e}")
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Critical error in landmark drawing: {e}", exc_info=True)
            # Return original frame if all drawing fails
            return frame
    
    def close(self):
        """Clean up MediaPipe resources"""
        if hasattr(self, 'holistic'):
            self.holistic.close()
            self.logger.info("MediaPipe Holistic model closed")


class FrameProcessor:
    """
    Frame processing utilities for encoding/decoding and MediaPipe integration
    Enhanced with gesture detection capabilities for ASL practice sessions
    """
    
    def __init__(self, video_config: VideoConfig, mediapipe_config: MediaPipeConfig, gesture_config: GestureDetectionConfig = None):
        """
        Initialize frame processor
        
        Args:
            video_config: Video configuration settings
            mediapipe_config: MediaPipe configuration settings
            gesture_config: Optional gesture detection configuration
        """
        self.video_config = video_config
        self.mediapipe_config = mediapipe_config
        self.gesture_config = gesture_config
        self.logger = logging.getLogger(f"{__name__}.FrameProcessor")
        
        # Initialize MediaPipe processor
        self.mediapipe_processor = MediaPipeProcessor(mediapipe_config)
        
        # Initialize practice session manager if gesture detection is enabled
        self.practice_session_manager = None
        if gesture_config and gesture_config.enabled:
            self.practice_session_manager = PracticeSessionManager(gesture_config)
            self.logger.info("Frame processor initialized with gesture detection enabled")
        else:
            self.logger.info("Frame processor initialized without gesture detection")
        
        self.logger.info("Frame processor initialized")
    
    def decode_base64_frame(self, base64_data: str) -> Optional[np.ndarray]:
        """
        Decode base64 JPEG data to OpenCV frame
        
        Args:
            base64_data: Base64 encoded JPEG image data (with or without data URL prefix)
            
        Returns:
            Decoded frame as numpy array (BGR format) or None if decoding fails
        """
        try:
            # Remove data URL prefix if present
            if base64_data.startswith('data:image/jpeg;base64,'):
                base64_data = base64_data.split(',', 1)[1]
            elif base64_data.startswith('data:image/jpg;base64,'):
                base64_data = base64_data.split(',', 1)[1]
            
            # Decode base64 to bytes
            image_bytes = base64.b64decode(base64_data)
            
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            
            # Decode JPEG to OpenCV frame
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                self.logger.error("Failed to decode JPEG data")
                return None
            
            self.logger.debug(f"Decoded frame: {frame.shape}")
            return frame
            
        except Exception as e:
            self.logger.error(f"Error decoding base64 frame: {e}", exc_info=True)
            return None
    
    def encode_frame_to_base64(self, frame: np.ndarray, include_metadata: bool = False) -> Optional[Dict[str, Any]]:
        """
        Encode OpenCV frame to base64 JPEG data optimized for low latency
        
        Args:
            frame: OpenCV frame as numpy array (BGR format)
            include_metadata: Whether to include encoding metadata in response
            
        Returns:
            Dictionary with encoded frame data and metadata, or None if encoding fails
        """
        start_time = time.time()
        
        try:
            # Aggressive JPEG compression for maximum speed (as per latency solution)
            quality = 50  # Fixed at 50 for optimal speed/quality balance
            encode_params = [
                cv2.IMWRITE_JPEG_QUALITY, quality,
                cv2.IMWRITE_JPEG_OPTIMIZE, 0,  # Disable optimization for speed
                cv2.IMWRITE_JPEG_PROGRESSIVE, 0  # Disable progressive for speed
            ]
            success, buffer = cv2.imencode('.jpg', frame, encode_params)
            
            if not success:
                self.logger.error("Failed to encode frame as JPEG")
                return None
            
            # Convert to base64
            base64_data = base64.b64encode(buffer).decode('utf-8')
            
            # Add data URL prefix for web compatibility
            data_url = f"data:image/jpeg;base64,{base64_data}"
            
            # Calculate encoding metrics
            encoding_time_ms = (time.time() - start_time) * 1000
            compressed_size = len(buffer)
            original_size = frame.nbytes if hasattr(frame, 'nbytes') else frame.size * frame.itemsize
            compression_ratio = original_size / compressed_size if compressed_size > 0 else 0
            
            result = {
                "frame_data": data_url,
                "encoding_success": True
            }
            
            # Add metadata if requested
            if include_metadata:
                result["encoding_metadata"] = {
                    "encoding_time_ms": round(encoding_time_ms, 2),
                    "compressed_size_bytes": compressed_size,
                    "original_size_bytes": original_size,
                    "compression_ratio": round(compression_ratio, 2),
                    "quality": self.video_config.quality,
                    "format": "JPEG"
                }
            
            self.logger.debug(f"Encoded frame to base64: {len(data_url)} characters, "
                            f"compression: {compression_ratio:.2f}x, time: {encoding_time_ms:.2f}ms")
            return result
            
        except Exception as e:
            self.logger.error(f"Error encoding frame to base64: {e}", exc_info=True)
            return {
                "frame_data": None,
                "encoding_success": False,
                "error": str(e)
            }
    
    def process_frame_with_mediapipe(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict[str, bool], float]:
        """
        Process frame through MediaPipe and return processed frame with metadata
        
        Args:
            frame: Input frame as numpy array (BGR format)
            
        Returns:
            Tuple of (processed_frame, landmarks_detected, processing_time_ms)
        """
        start_time = time.time()
        
        try:
            # Process frame through MediaPipe
            processed_frame, landmarks_detected = self.mediapipe_processor.process_frame(frame)
            
            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000
            
            self.logger.debug(f"MediaPipe processing completed in {processing_time_ms:.2f}ms")
            return processed_frame, landmarks_detected, processing_time_ms
            
        except Exception as e:
            self.logger.error(f"Error in MediaPipe processing: {e}", exc_info=True)
            processing_time_ms = (time.time() - start_time) * 1000
            return frame, {"hands": False, "face": False, "pose": False}, processing_time_ms
    
    def process_base64_frame(self, base64_data: str, frame_number: int = 0, skip_processing: bool = False) -> Dict[str, Any]:
        """
        Complete pipeline: decode base64 frame, process with MediaPipe, encode result
        Enhanced with gesture detection for ASL practice sessions
        
        Args:
            base64_data: Base64 encoded JPEG image data
            frame_number: Frame sequence number for tracking
            skip_processing: If True, skip MediaPipe processing for speed
            
        Returns:
            Dictionary with processed frame data and metadata (never None for graceful degradation)
        """
        pipeline_start_time = time.time()
        
        try:
            # Decode input frame
            frame = self.decode_base64_frame(base64_data)
            if frame is None:
                self.logger.warning("Frame decoding failed, returning error response")
                return self._create_error_response("Frame decoding failed", frame_number)
            
            # Optional processing skip for ultra-low latency mode
            if skip_processing:
                # Skip MediaPipe processing, just return the frame
                encoding_result = self.encode_frame_to_base64(frame, include_metadata=False)
                if encoding_result is None or not encoding_result.get("encoding_success", False):
                    return self._create_error_response("Frame encoding failed", frame_number)
                
                total_pipeline_time_ms = (time.time() - pipeline_start_time) * 1000
                return {
                    "success": True,
                    "frame_data": encoding_result["frame_data"],
                    "landmarks_detected": {"hands": False, "face": False, "pose": False},
                    "processing_metadata": {
                        "frame_number": frame_number,
                        "mediapipe_processing_time_ms": 0.0,
                        "total_pipeline_time_ms": round(total_pipeline_time_ms, 2),
                        "timestamp": datetime.utcnow().isoformat(),
                        "processing_skipped": True
                    },
                    "quality_metrics": {
                        "landmarks_confidence": 0.0,
                        "processing_efficiency": 1.0  # Max efficiency when skipping
                    }
                }
            
            # Process with MediaPipe (with graceful degradation)
            processed_frame, landmarks_detected, processing_time_ms = self.process_frame_with_mediapipe(frame)
            
            # Process frame for gesture detection if practice session is active
            practice_data = None
            if self.practice_session_manager and self.practice_session_manager.is_active:
                frame_metadata = {
                    "frame_number": frame_number,
                    "processing_time_ms": processing_time_ms,
                    "timestamp": datetime.utcnow().isoformat()
                }
                practice_data = self.practice_session_manager.process_frame_for_practice(landmarks_detected, frame_metadata)
            
            # Encode processed frame with metadata
            encoding_result = self.encode_frame_to_base64(processed_frame, include_metadata=True)
            if encoding_result is None or not encoding_result.get("encoding_success", False):
                self.logger.warning("Frame encoding failed, returning error response")
                return self._create_error_response("Frame encoding failed", frame_number)
            
            # Calculate total pipeline time
            total_pipeline_time_ms = (time.time() - pipeline_start_time) * 1000
            
            # Build comprehensive response with all metadata
            result = {
                "success": True,
                "frame_data": encoding_result["frame_data"],
                "landmarks_detected": landmarks_detected,
                "processing_metadata": {
                    "frame_number": frame_number,
                    "mediapipe_processing_time_ms": round(processing_time_ms, 2),
                    "total_pipeline_time_ms": round(total_pipeline_time_ms, 2),
                    "encoding_metadata": encoding_result.get("encoding_metadata", {}),
                    "timestamp": datetime.utcnow().isoformat()
                },
                "quality_metrics": {
                    "landmarks_confidence": self._calculate_landmarks_confidence(landmarks_detected),
                    "processing_efficiency": self._calculate_processing_efficiency(processing_time_ms)
                }
            }
            
            # Add practice session data if available
            if practice_data:
                result["practice_session"] = practice_data
            
            self.logger.debug(f"Frame {frame_number} processing pipeline completed successfully - "
                            f"Total time: {total_pipeline_time_ms:.2f}ms, "
                            f"Landmarks: {landmarks_detected}")
            return result
            
        except Exception as e:
            self.logger.error(f"Critical error in frame processing pipeline: {e}", exc_info=True)
            return self._create_error_response(f"Pipeline error: {str(e)}", frame_number)
    
    def _create_error_response(self, error_message: str, frame_number: int = 0) -> Dict[str, Any]:
        """
        Create standardized error response for graceful degradation
        
        Args:
            error_message: Description of the error
            frame_number: Frame sequence number
            
        Returns:
            Standardized error response dictionary
        """
        return {
            "success": False,
            "frame_data": None,
            "error": error_message,
            "landmarks_detected": {"hands": False, "face": False, "pose": False},
            "processing_metadata": {
                "frame_number": frame_number,
                "mediapipe_processing_time_ms": 0.0,
                "total_pipeline_time_ms": 0.0,
                "timestamp": datetime.utcnow().isoformat(),
                "error_occurred": True
            },
            "quality_metrics": {
                "landmarks_confidence": 0.0,
                "processing_efficiency": 0.0
            }
        }
    
    def _calculate_landmarks_confidence(self, landmarks_detected: Dict[str, bool]) -> float:
        """
        Calculate overall landmarks detection confidence score
        
        Args:
            landmarks_detected: Dictionary of detected landmark types
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        detected_count = sum(1 for detected in landmarks_detected.values() if detected)
        total_types = len(landmarks_detected)
        return detected_count / total_types if total_types > 0 else 0.0
    
    def _calculate_processing_efficiency(self, processing_time_ms: float) -> float:
        """
        Calculate processing efficiency score based on target performance
        
        Args:
            processing_time_ms: Processing time in milliseconds
            
        Returns:
            Efficiency score between 0.0 and 1.0 (1.0 = optimal performance)
        """
        # Target processing time is 16.67ms (60 FPS)
        target_time_ms = 16.67
        if processing_time_ms <= target_time_ms:
            return 1.0
        elif processing_time_ms <= target_time_ms * 2:
            # Linear degradation up to 2x target time
            return 1.0 - ((processing_time_ms - target_time_ms) / target_time_ms)
        else:
            # Minimum efficiency for very slow processing
            return 0.1
    
    def start_practice_session(self, story_sentences: list, session_id: str = None) -> Dict[str, Any]:
        """
        Start a new ASL practice session
        
        Args:
            story_sentences: List of sentences to practice
            session_id: Optional session identifier
            
        Returns:
            Dictionary containing session start result
        """
        if not self.practice_session_manager:
            return {
                "success": False,
                "error": "Gesture detection not enabled"
            }
        
        return self.practice_session_manager.start_practice_session(story_sentences, session_id)
    
    def handle_practice_control(self, action: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle practice session control messages
        
        Args:
            action: Control action ("next_sentence", "try_again", "stop_session", "set_feedback")
            data: Optional action data
            
        Returns:
            Dictionary containing action result
        """
        if not self.practice_session_manager:
            return {
                "success": False,
                "error": "Gesture detection not enabled"
            }
        
        return self.practice_session_manager.handle_control_message(action, data)
    
    def get_gesture_buffer_for_analysis(self) -> list:
        """
        Get the current gesture buffer for AI analysis
        
        Returns:
            List of landmark data for the completed gesture
        """
        if not self.practice_session_manager:
            return []
        
        return self.practice_session_manager.get_gesture_buffer_for_analysis()
    
    def get_practice_session_state(self) -> Dict[str, Any]:
        """
        Get current practice session state
        
        Returns:
            Dictionary containing session state information
        """
        if not self.practice_session_manager:
            return {"gesture_detection_enabled": False}
        
        state = self.practice_session_manager.get_session_state()
        state["gesture_detection_enabled"] = True
        return state
    
    def get_pending_analysis_task(self) -> Optional[Dict[str, Any]]:
        """
        Get pending analysis task from practice session manager
        
        Returns:
            Pending analysis task or None
        """
        if not self.practice_session_manager:
            return None
        
        return self.practice_session_manager.get_pending_analysis_task()
    
    def set_analysis_result(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set analysis result in practice session manager
        
        Args:
            analysis_result: Result from signing analysis
            
        Returns:
            Dictionary containing result status
        """
        if not self.practice_session_manager:
            return {
                "success": False,
                "error": "Gesture detection not enabled"
            }
        
        return self.practice_session_manager.set_analysis_result(analysis_result)
    
    def close(self):
        """Clean up resources"""
        if hasattr(self, 'mediapipe_processor'):
            self.mediapipe_processor.close()
            self.logger.info("Frame processor closed")


class GestureDetector:
    """
    Gesture detection system for ASL practice sessions
    Detects gesture start/end using hand movement velocity and manages landmark buffering
    """
    
    def __init__(self, gesture_config: GestureDetectionConfig):
        """
        Initialize gesture detector
        
        Args:
            gesture_config: Gesture detection configuration settings
        """
        self.config = gesture_config
        self.logger = logging.getLogger(f"{__name__}.GestureDetector")
        
        # Gesture detection state
        self.is_detecting = False
        self.gesture_start_time = None
        self.gesture_end_time = None
        self.last_movement_time = None
        
        # Landmark data buffering
        self.landmark_buffer = []
        self.velocity_history = []
        
        # Hand position tracking for velocity calculation
        self.previous_hand_positions = None
        self.frame_timestamps = []
        
        self.logger.info(f"Gesture detector initialized with velocity threshold: {self.config.velocity_threshold}")
    
    def calculate_hand_velocity(self, landmarks_data: Dict[str, Any]) -> float:
        """
        Calculate hand movement velocity from landmark data
        
        Args:
            landmarks_data: Dictionary containing hand landmarks from MediaPipe
            
        Returns:
            Average velocity of both hands (normalized units per second)
        """
        try:
            current_time = time.time()
            current_positions = []
            
            # Extract hand positions from landmarks - simplified approach for gesture detection
            # In practice, this would extract actual landmark coordinates from MediaPipe results
            # For now, we use the detection status as a proxy for movement
            if landmarks_data.get("hands", False):
                # Simulate hand center positions based on detection
                # In real implementation, calculate center of hand landmarks
                current_positions = [0.5, 0.5]  # Normalized coordinates [x, y]
                
                # Add some variation to simulate movement when hands are detected
                import random
                if random.random() > 0.7:  # 30% chance of movement simulation
                    current_positions[0] += random.uniform(-0.1, 0.1)
                    current_positions[1] += random.uniform(-0.1, 0.1)
            
            if not current_positions:
                # No hands detected, reset tracking
                self.previous_hand_positions = None
                return 0.0
            
            # Calculate velocity if we have previous positions
            if self.previous_hand_positions is not None and len(self.frame_timestamps) > 0:
                time_delta = current_time - self.frame_timestamps[-1]
                if time_delta > 0:
                    # Calculate Euclidean distance moved
                    distance = sum((curr - prev) ** 2 for curr, prev in zip(current_positions, self.previous_hand_positions)) ** 0.5
                    velocity = distance / time_delta
                    
                    # Add to velocity history for smoothing
                    self.velocity_history.append(velocity)
                    if len(self.velocity_history) > self.config.smoothing_window:
                        self.velocity_history.pop(0)
                    
                    # Return smoothed velocity
                    smoothed_velocity = sum(self.velocity_history) / len(self.velocity_history)
                    
                    self.logger.debug(f"Hand velocity: {smoothed_velocity:.4f} (raw: {velocity:.4f})")
                    return smoothed_velocity
            
            # Update tracking data
            self.previous_hand_positions = current_positions
            self.frame_timestamps.append(current_time)
            if len(self.frame_timestamps) > self.config.smoothing_window:
                self.frame_timestamps.pop(0)
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating hand velocity: {e}")
            return 0.0
    
    def detect_gesture_start(self, landmarks_data: Dict[str, Any]) -> bool:
        """
        Detect the start of a gesture based on hand movement velocity
        
        Args:
            landmarks_data: Dictionary containing landmarks from MediaPipe
            
        Returns:
            True if gesture start is detected, False otherwise
        """
        if not self.config.enabled or self.is_detecting:
            return False
        
        try:
            velocity = self.calculate_hand_velocity(landmarks_data)
            
            # Check if velocity exceeds threshold
            if velocity > self.config.velocity_threshold:
                self.is_detecting = True
                self.gesture_start_time = time.time()
                self.last_movement_time = time.time()
                self.landmark_buffer = []
                
                self.logger.info(f"Gesture start detected - velocity: {velocity:.4f}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error detecting gesture start: {e}")
            return False
    
    def detect_gesture_end(self, landmarks_data: Dict[str, Any]) -> bool:
        """
        Detect the end of a gesture based on movement pause
        
        Args:
            landmarks_data: Dictionary containing landmarks from MediaPipe
            
        Returns:
            True if gesture end is detected, False otherwise
        """
        if not self.config.enabled or not self.is_detecting:
            return False
        
        try:
            current_time = time.time()
            velocity = self.calculate_hand_velocity(landmarks_data)
            
            # Update last movement time if still moving
            if velocity > self.config.velocity_threshold:
                self.last_movement_time = current_time
                return False
            
            # Check if pause duration exceeded
            if self.last_movement_time is not None:
                pause_duration_ms = (current_time - self.last_movement_time) * 1000
                
                if pause_duration_ms >= self.config.pause_duration_ms:
                    # Check minimum gesture duration
                    if self.gesture_start_time is not None:
                        gesture_duration_ms = (current_time - self.gesture_start_time) * 1000
                        
                        if gesture_duration_ms >= self.config.min_gesture_duration_ms:
                            self.gesture_end_time = current_time
                            self.is_detecting = False
                            
                            self.logger.info(f"Gesture end detected - duration: {gesture_duration_ms:.0f}ms, "
                                           f"pause: {pause_duration_ms:.0f}ms")
                            return True
                        else:
                            # Gesture too short, reset detection
                            self.logger.debug(f"Gesture too short ({gesture_duration_ms:.0f}ms), resetting")
                            self.reset_detection()
                            return False
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error detecting gesture end: {e}")
            return False
    
    def collect_landmark_data(self, landmarks_data: Dict[str, Any], frame_metadata: Dict[str, Any]) -> None:
        """
        Buffer landmark data during gesture detection
        
        Args:
            landmarks_data: Dictionary containing landmarks from MediaPipe
            frame_metadata: Frame processing metadata
        """
        if not self.config.enabled or not self.is_detecting:
            return
        
        try:
            # Create landmark entry with timestamp
            landmark_entry = {
                "timestamp": time.time(),
                "landmarks": landmarks_data.copy(),
                "metadata": frame_metadata.copy()
            }
            
            # Add to buffer
            self.landmark_buffer.append(landmark_entry)
            
            # Limit buffer size
            if len(self.landmark_buffer) > self.config.landmark_buffer_size:
                self.landmark_buffer.pop(0)
            
            self.logger.debug(f"Landmark data collected - buffer size: {len(self.landmark_buffer)}")
            
        except Exception as e:
            self.logger.error(f"Error collecting landmark data: {e}")
    
    def get_gesture_buffer(self) -> list:
        """
        Get the current landmark buffer for analysis
        
        Returns:
            List of landmark data entries collected during the gesture
        """
        return self.landmark_buffer.copy()
    
    def reset_detection(self) -> None:
        """Reset gesture detection state"""
        self.is_detecting = False
        self.gesture_start_time = None
        self.gesture_end_time = None
        self.last_movement_time = None
        self.landmark_buffer = []
        
        self.logger.debug("Gesture detection state reset")
    
    def get_detection_state(self) -> Dict[str, Any]:
        """
        Get current gesture detection state
        
        Returns:
            Dictionary containing detection state information
        """
        current_time = time.time()
        
        state = {
            "is_detecting": self.is_detecting,
            "buffer_size": len(self.landmark_buffer),
            "enabled": self.config.enabled
        }
        
        if self.is_detecting and self.gesture_start_time is not None:
            state["gesture_duration_ms"] = (current_time - self.gesture_start_time) * 1000
            
            if self.last_movement_time is not None:
                state["pause_duration_ms"] = (current_time - self.last_movement_time) * 1000
            else:
                state["pause_duration_ms"] = 0
        
        return state


class PracticeSessionManager:
    """
    Manages practice session state for ASL learning
    Coordinates gesture detection with target sentences and feedback
    """
    
    def __init__(self, gesture_config: GestureDetectionConfig):
        """
        Initialize practice session manager
        
        Args:
            gesture_config: Gesture detection configuration
        """
        self.gesture_config = gesture_config
        self.logger = logging.getLogger(f"{__name__}.PracticeSessionManager")
        
        # Session state
        self.is_active = False
        self.current_sentence = None
        self.current_sentence_index = 0
        self.story_sentences = []
        self.session_id = None
        
        # Gesture detection
        self.gesture_detector = GestureDetector(gesture_config)
        
        # Practice mode state
        self.practice_mode = "listening"  # "listening", "detecting", "analyzing", "feedback"
        self.last_feedback = None
        
        # Analysis state
        self.analysis_in_progress = False
        self.pending_analysis_task = None
        
        self.logger.info("Practice session manager initialized")
    
    def start_practice_session(self, story_sentences: list, session_id: str = None) -> Dict[str, Any]:
        """
        Start a new practice session with story sentences
        
        Args:
            story_sentences: List of sentences to practice
            session_id: Optional session identifier
            
        Returns:
            Dictionary containing session start information
        """
        try:
            self.is_active = True
            self.story_sentences = story_sentences.copy()
            self.current_sentence_index = 0
            self.current_sentence = story_sentences[0] if story_sentences else None
            self.session_id = session_id or f"session_{int(time.time())}"
            self.practice_mode = "listening"
            self.last_feedback = None
            
            # Reset gesture detection
            self.gesture_detector.reset_detection()
            
            self.logger.info(f"Practice session started - ID: {self.session_id}, "
                           f"sentences: {len(self.story_sentences)}")
            
            return {
                "success": True,
                "session_id": self.session_id,
                "total_sentences": len(self.story_sentences),
                "current_sentence_index": self.current_sentence_index,
                "current_sentence": self.current_sentence,
                "practice_mode": self.practice_mode
            }
            
        except Exception as e:
            self.logger.error(f"Error starting practice session: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def process_frame_for_practice(self, landmarks_data: Dict[str, Any], frame_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process frame data for practice session gesture detection
        
        Args:
            landmarks_data: Dictionary containing landmarks from MediaPipe
            frame_metadata: Frame processing metadata
            
        Returns:
            Dictionary containing practice session updates
        """
        if not self.is_active:
            return {"practice_active": False}
        
        try:
            result = {
                "practice_active": True,
                "session_id": self.session_id,
                "current_sentence": self.current_sentence,
                "current_sentence_index": self.current_sentence_index,
                "practice_mode": self.practice_mode,
                "gesture_state": self.gesture_detector.get_detection_state(),
                "analysis_in_progress": self.analysis_in_progress
            }
            
            # Handle gesture detection based on current mode
            if self.practice_mode == "listening":
                # Check for gesture start
                if self.gesture_detector.detect_gesture_start(landmarks_data):
                    self.practice_mode = "detecting"
                    result["practice_mode"] = self.practice_mode
                    result["gesture_started"] = True
                    self.logger.info(f"Gesture detection started for sentence: '{self.current_sentence}'")
                    
            elif self.practice_mode == "detecting":
                # Collect landmark data during gesture
                self.gesture_detector.collect_landmark_data(landmarks_data, frame_metadata)
                
                # Check for gesture end
                if self.gesture_detector.detect_gesture_end(landmarks_data):
                    self.practice_mode = "analyzing"
                    result["practice_mode"] = self.practice_mode
                    result["gesture_completed"] = True
                    result["landmark_buffer_size"] = len(self.gesture_detector.get_gesture_buffer())
                    
                    # Trigger analysis workflow
                    self._trigger_signing_analysis()
                    result["analysis_triggered"] = True
                    self.logger.info(f"Gesture completed, analysis triggered for sentence: '{self.current_sentence}'")
            
            elif self.practice_mode == "analyzing":
                # Show analyzing state while waiting for results
                result["analyzing"] = True
                
            elif self.practice_mode == "feedback":
                # Include feedback in result
                if self.last_feedback:
                    result["feedback"] = self.last_feedback
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing frame for practice: {e}")
            return {
                "practice_active": True,
                "error": str(e)
            }
    
    def _trigger_signing_analysis(self) -> None:
        """
        Trigger asynchronous signing analysis for the completed gesture
        """
        try:
            if self.analysis_in_progress:
                self.logger.warning("Analysis already in progress, skipping new analysis")
                return
            
            # Get the landmark buffer for analysis
            landmark_buffer = self.gesture_detector.get_gesture_buffer()
            
            if not landmark_buffer:
                self.logger.warning("No landmark data available for analysis")
                self._set_analysis_error("No gesture data captured")
                return
            
            if not self.current_sentence:
                self.logger.warning("No target sentence available for analysis")
                self._set_analysis_error("No target sentence available")
                return
            
            # Mark analysis as in progress
            self.analysis_in_progress = True
            
            # Create analysis task (this will be handled by the WebSocket handler)
            self.pending_analysis_task = {
                "landmark_buffer": landmark_buffer.copy(),
                "target_sentence": self.current_sentence,
                "timestamp": time.time()
            }
            
            self.logger.info(f"Analysis task created for {len(landmark_buffer)} frames")
            
        except Exception as e:
            self.logger.error(f"Error triggering signing analysis: {e}")
            self._set_analysis_error(f"Analysis error: {str(e)}")
    
    def _set_analysis_error(self, error_message: str) -> None:
        """
        Set analysis error and return to listening mode
        
        Args:
            error_message: Error message to display
        """
        self.analysis_in_progress = False
        self.practice_mode = "feedback"
        self.last_feedback = {
            "feedback": f"Analysis error: {error_message}. Please try signing again.",
            "confidence_score": 0.0,
            "suggestions": ["Try signing again with clear movements", "Ensure good lighting"],
            "analysis_summary": "Analysis failed",
            "error": True
        }
        self.logger.warning(f"Analysis error set: {error_message}")
    
    def set_analysis_result(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set the result of signing analysis and transition to feedback mode
        
        Args:
            analysis_result: Result from Ollama signing analysis
            
        Returns:
            Dictionary containing the result status
        """
        try:
            self.analysis_in_progress = False
            self.pending_analysis_task = None
            
            if analysis_result and analysis_result.get("feedback"):
                self.practice_mode = "feedback"
                self.last_feedback = analysis_result
                
                self.logger.info(f"Analysis result set with confidence: {analysis_result.get('confidence_score', 'N/A')}")
                
                return {
                    "success": True,
                    "practice_mode": self.practice_mode,
                    "feedback": self.last_feedback
                }
            else:
                # Analysis failed, set error feedback
                self._set_analysis_error("Analysis service returned no feedback")
                return {
                    "success": False,
                    "error": "Analysis failed",
                    "practice_mode": self.practice_mode,
                    "feedback": self.last_feedback
                }
                
        except Exception as e:
            self.logger.error(f"Error setting analysis result: {e}")
            self._set_analysis_error(f"Error processing analysis result: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "practice_mode": self.practice_mode,
                "feedback": self.last_feedback
            }
    
    def get_pending_analysis_task(self) -> Optional[Dict[str, Any]]:
        """
        Get and clear the pending analysis task
        
        Returns:
            Pending analysis task data or None
        """
        task = self.pending_analysis_task
        self.pending_analysis_task = None
        return task
    
    def handle_control_message(self, action: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle practice session control messages
        
        Args:
            action: Control action ("next_sentence", "try_again", "stop_session")
            data: Optional action data
            
        Returns:
            Dictionary containing action result
        """
        try:
            if action == "next_sentence":
                return self._next_sentence()
            elif action == "try_again":
                return self._try_again()
            elif action == "stop_session":
                return self._stop_session()
            elif action == "complete_story":
                return self._complete_story()
            elif action == "set_feedback":
                return self._set_feedback(data)
            elif action == "start_session":
                # Handle session start through control message
                return self._handle_session_start(data)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
                
        except Exception as e:
            self.logger.error(f"Error handling control message: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _next_sentence(self) -> Dict[str, Any]:
        """Move to the next sentence in the story"""
        if self.current_sentence_index < len(self.story_sentences) - 1:
            self.current_sentence_index += 1
            self.current_sentence = self.story_sentences[self.current_sentence_index]
            self.practice_mode = "listening"
            self.last_feedback = None
            self.gesture_detector.reset_detection()
            
            self.logger.info(f"Moved to next sentence: {self.current_sentence_index}")
            
            return {
                "success": True,
                "action": "next_sentence",
                "current_sentence_index": self.current_sentence_index,
                "current_sentence": self.current_sentence,
                "practice_mode": self.practice_mode,
                "is_last_sentence": self.current_sentence_index == len(self.story_sentences) - 1
            }
        else:
            # Story completed
            self.logger.info("Story practice completed")
            return {
                "success": True,
                "action": "story_completed",
                "total_sentences": len(self.story_sentences)
            }
    
    def _try_again(self) -> Dict[str, Any]:
        """Reset current sentence for another attempt"""
        self.practice_mode = "listening"
        self.last_feedback = None
        self.gesture_detector.reset_detection()
        
        self.logger.info(f"Trying again with sentence: {self.current_sentence_index}")
        
        return {
            "success": True,
            "action": "try_again",
            "current_sentence_index": self.current_sentence_index,
            "current_sentence": self.current_sentence,
            "practice_mode": self.practice_mode
        }
    
    def _stop_session(self) -> Dict[str, Any]:
        """Stop the current practice session"""
        self.is_active = False
        self.gesture_detector.reset_detection()
        
        self.logger.info(f"Practice session stopped: {self.session_id}")
        
        return {
            "success": True,
            "action": "session_stopped",
            "session_id": self.session_id
        }
    
    def _set_feedback(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Set feedback for the current gesture attempt"""
        if data and "feedback" in data:
            self.last_feedback = data["feedback"]
            self.practice_mode = "feedback"
            
            self.logger.info("Feedback set for current gesture")
            
            return {
                "success": True,
                "action": "feedback_set",
                "practice_mode": self.practice_mode,
                "feedback": self.last_feedback
            }
        else:
            return {
                "success": False,
                "error": "No feedback data provided"
            }
    
    def _complete_story(self) -> Dict[str, Any]:
        """Complete the current story practice session"""
        self.practice_mode = "completed"
        self.last_feedback = None
        
        self.logger.info(f"Story practice completed: {self.session_id}")
        
        return {
            "success": True,
            "action": "story_completed",
            "session_id": self.session_id,
            "total_sentences": len(self.story_sentences),
            "practice_mode": self.practice_mode
        }
    
    def _handle_session_start(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle session start through control message"""
        if not data:
            return {
                "success": False,
                "error": "No session data provided"
            }
        
        story_sentences = data.get("story_sentences", [])
        session_id = data.get("session_id")
        
        if not story_sentences:
            return {
                "success": False,
                "error": "No story sentences provided"
            }
        
        return self.start_practice_session(story_sentences, session_id)
    
    def get_gesture_buffer_for_analysis(self) -> list:
        """
        Get the current gesture buffer for AI analysis
        
        Returns:
            List of landmark data for the completed gesture
        """
        return self.gesture_detector.get_gesture_buffer()
    
    def get_session_state(self) -> Dict[str, Any]:
        """
        Get complete session state information
        
        Returns:
            Dictionary containing full session state
        """
        return {
            "is_active": self.is_active,
            "session_id": self.session_id,
            "current_sentence": self.current_sentence,
            "current_sentence_index": self.current_sentence_index,
            "total_sentences": len(self.story_sentences),
            "practice_mode": self.practice_mode,
            "last_feedback": self.last_feedback,
            "gesture_state": self.gesture_detector.get_detection_state() if self.is_active else None
        }