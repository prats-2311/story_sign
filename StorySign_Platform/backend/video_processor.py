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

from config import MediaPipeConfig, VideoConfig

# Try to import MediaPipe, fall back to mock if not available
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    # Create mock MediaPipe classes for compatibility
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
        
        # Initialize holistic model with optimized settings for low latency
        self.holistic = self.mp_holistic.Holistic(
            min_detection_confidence=max(0.3, self.config.min_detection_confidence - 0.2),  # Lower for speed
            min_tracking_confidence=max(0.3, self.config.min_tracking_confidence - 0.2),   # Lower for speed
            model_complexity=min(1, self.config.model_complexity),  # Use faster model (0 or 1)
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
    """
    
    def __init__(self, video_config: VideoConfig, mediapipe_config: MediaPipeConfig):
        """
        Initialize frame processor
        
        Args:
            video_config: Video configuration settings
            mediapipe_config: MediaPipe configuration settings
        """
        self.video_config = video_config
        self.mediapipe_config = mediapipe_config
        self.logger = logging.getLogger(f"{__name__}.FrameProcessor")
        
        # Initialize MediaPipe processor
        self.mediapipe_processor = MediaPipeProcessor(mediapipe_config)
        
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
            # Optimized JPEG encoding for speed over quality
            quality = min(60, self.video_config.quality)  # Cap quality for speed
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
        Optimized for low latency with optional processing skip
        
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
    
    def close(self):
        """Clean up resources"""
        if hasattr(self, 'mediapipe_processor'):
            self.mediapipe_processor.close()
            self.logger.info("Frame processor closed")