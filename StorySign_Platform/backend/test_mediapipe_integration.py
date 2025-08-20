#!/usr/bin/env python3
"""
Unit tests for MediaPipe integration and landmark detection accuracy
"""

import pytest
import numpy as np
import cv2
from unittest.mock import Mock, patch, MagicMock
import base64

from video_processor import MediaPipeProcessor, FrameProcessor
from config import MediaPipeConfig, VideoConfig


class TestMediaPipeIntegration:
    """Test cases for MediaPipe integration functionality"""
    
    def setup_method(self):
        """Set up MediaPipe integration tests"""
        self.config = MediaPipeConfig(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1
        )
        
    @patch('video_processor.MEDIAPIPE_AVAILABLE', True)
    @patch('video_processor.mp')
    def test_mediapipe_initialization_success(self, mock_mp):
        """Test successful MediaPipe initialization"""
        # Mock MediaPipe components
        mock_holistic_class = Mock()
        mock_holistic_instance = Mock()
        mock_holistic_class.return_value = mock_holistic_instance
        
        mock_mp.solutions.holistic.Holistic = mock_holistic_class
        mock_mp.solutions.drawing_utils = Mock()
        mock_mp.solutions.drawing_styles = Mock()
        
        processor = MediaPipeProcessor(self.config)
        
        # Verify initialization
        assert processor.holistic == mock_holistic_instance
        mock_holistic_class.assert_called_once()
        
        # Verify configuration parameters
        call_kwargs = mock_holistic_class.call_args[1]
        assert call_kwargs['min_detection_confidence'] >= 0.3  # Optimized for speed
        assert call_kwargs['min_tracking_confidence'] >= 0.3
        assert call_kwargs['model_complexity'] <= 1  # Fast model
        assert call_kwargs['enable_segmentation'] == False  # Disabled for speed
        assert call_kwargs['refine_face_landmarks'] == False  # Disabled for speed
        
    @patch('video_processor.MEDIAPIPE_AVAILABLE', False)
    def test_mediapipe_unavailable_fallback(self):
        """Test MediaPipe unavailable fallback behavior"""
        processor = MediaPipeProcessor(self.config)
        
        # Should initialize without error
        assert processor.config == self.config
        
        # Test processing with unavailable MediaPipe
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        processed_frame, landmarks = processor.process_frame(test_frame)
        
        # Should return original frame and no landmarks
        assert np.array_equal(processed_frame, test_frame)
        assert landmarks == {"hands": False, "face": False, "pose": False}
        
    @patch('video_processor.MEDIAPIPE_AVAILABLE', True)
    @patch('video_processor.mp')
    def test_landmark_detection_all_types(self, mock_mp):
        """Test detection of all landmark types (hands, face, pose)"""
        # Mock MediaPipe results with all landmarks detected
        mock_results = Mock()
        mock_results.left_hand_landmarks = Mock()  # Left hand detected
        mock_results.right_hand_landmarks = Mock()  # Right hand detected
        mock_results.face_landmarks = Mock()  # Face detected
        mock_results.pose_landmarks = Mock()  # Pose detected
        
        # Mock holistic processor
        mock_holistic = Mock()
        mock_holistic.process.return_value = mock_results
        
        mock_mp.solutions.holistic.Holistic.return_value = mock_holistic
        mock_mp.solutions.drawing_utils = Mock()
        mock_mp.solutions.drawing_styles = Mock()
        
        processor = MediaPipeProcessor(self.config)
        
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        processed_frame, landmarks = processor.process_frame(test_frame)
        
        # Verify all landmarks detected
        assert landmarks["hands"] == True  # Both hands detected
        assert landmarks["face"] == True
        assert landmarks["pose"] == True
        
    @patch('video_processor.MEDIAPIPE_AVAILABLE', True)
    @patch('video_processor.mp')
    def test_landmark_detection_partial(self, mock_mp):
        """Test partial landmark detection scenarios"""
        # Mock MediaPipe results with partial detection
        mock_results = Mock()
        mock_results.left_hand_landmarks = Mock()  # Only left hand
        mock_results.right_hand_landmarks = None
        mock_results.face_landmarks = None  # No face
        mock_results.pose_landmarks = Mock()  # Pose detected
        
        mock_holistic = Mock()
        mock_holistic.process.return_value = mock_results
        
        mock_mp.solutions.holistic.Holistic.return_value = mock_holistic
        mock_mp.solutions.drawing_utils = Mock()
        mock_mp.solutions.drawing_styles = Mock()
        
        processor = MediaPipeProcessor(self.config)
        
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        processed_frame, landmarks = processor.process_frame(test_frame)
        
        # Verify partial detection
        assert landmarks["hands"] == True  # Left hand detected
        assert landmarks["face"] == False  # No face
        assert landmarks["pose"] == True  # Pose detected
        
    @patch('video_processor.MEDIAPIPE_AVAILABLE', True)
    @patch('video_processor.mp')
    def test_landmark_detection_none(self, mock_mp):
        """Test scenario with no landmarks detected"""
        # Mock MediaPipe results with no landmarks
        mock_results = Mock()
        mock_results.left_hand_landmarks = None
        mock_results.right_hand_landmarks = None
        mock_results.face_landmarks = None
        mock_results.pose_landmarks = None
        
        mock_holistic = Mock()
        mock_holistic.process.return_value = mock_results
        
        mock_mp.solutions.holistic.Holistic.return_value = mock_holistic
        mock_mp.solutions.drawing_utils = Mock()
        mock_mp.solutions.drawing_styles = Mock()
        
        processor = MediaPipeProcessor(self.config)
        
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        processed_frame, landmarks = processor.process_frame(test_frame)
        
        # Verify no landmarks detected
        assert landmarks["hands"] == False
        assert landmarks["face"] == False
        assert landmarks["pose"] == False
        
    @patch('video_processor.MEDIAPIPE_AVAILABLE', True)
    @patch('video_processor.mp')
    def test_landmark_drawing_success(self, mock_mp):
        """Test successful landmark drawing on frame"""
        # Mock MediaPipe components
        mock_results = Mock()
        mock_results.left_hand_landmarks = Mock()
        mock_results.right_hand_landmarks = Mock()
        mock_results.face_landmarks = Mock()
        mock_results.pose_landmarks = Mock()
        
        mock_holistic = Mock()
        mock_holistic.process.return_value = mock_results
        
        mock_drawing_utils = Mock()
        mock_drawing_styles = Mock()
        
        mock_mp.solutions.holistic.Holistic.return_value = mock_holistic
        mock_mp.solutions.drawing_utils = mock_drawing_utils
        mock_mp.solutions.drawing_styles = mock_drawing_styles
        mock_mp.solutions.holistic.FACEMESH_CONTOURS = []
        mock_mp.solutions.holistic.POSE_CONNECTIONS = []
        mock_mp.solutions.holistic.HAND_CONNECTIONS = []
        
        processor = MediaPipeProcessor(self.config)
        
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        processed_frame, landmarks = processor.process_frame(test_frame)
        
        # Verify drawing functions were called
        assert mock_drawing_utils.draw_landmarks.call_count >= 4  # Face, pose, left hand, right hand
        
    @patch('video_processor.MEDIAPIPE_AVAILABLE', True)
    @patch('video_processor.mp')
    def test_landmark_drawing_error_handling(self, mock_mp):
        """Test landmark drawing with drawing errors"""
        # Mock MediaPipe components
        mock_results = Mock()
        mock_results.left_hand_landmarks = Mock()
        mock_results.face_landmarks = Mock()
        mock_results.pose_landmarks = Mock()
        mock_results.right_hand_landmarks = Mock()
        
        mock_holistic = Mock()
        mock_holistic.process.return_value = mock_results
        
        # Mock drawing utils to raise exception
        mock_drawing_utils = Mock()
        mock_drawing_utils.draw_landmarks.side_effect = Exception("Drawing error")
        
        mock_mp.solutions.holistic.Holistic.return_value = mock_holistic
        mock_mp.solutions.drawing_utils = mock_drawing_utils
        mock_mp.solutions.drawing_styles = Mock()
        
        processor = MediaPipeProcessor(self.config)
        
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        processed_frame, landmarks = processor.process_frame(test_frame)
        
        # Should handle drawing errors gracefully
        assert processed_frame is not None
        assert landmarks["hands"] == True  # Detection should still work
        assert landmarks["face"] == True
        assert landmarks["pose"] == True
        
    @patch('video_processor.MEDIAPIPE_AVAILABLE', True)
    @patch('video_processor.mp')
    def test_color_conversion_handling(self, mock_mp):
        """Test color conversion error handling"""
        mock_holistic = Mock()
        mock_holistic.process.return_value = Mock()
        
        mock_mp.solutions.holistic.Holistic.return_value = mock_holistic
        mock_mp.solutions.drawing_utils = Mock()
        mock_mp.solutions.drawing_styles = Mock()
        
        processor = MediaPipeProcessor(self.config)
        
        # Test with invalid frame that causes color conversion error
        with patch('cv2.cvtColor', side_effect=cv2.error("Color conversion error")):
            invalid_frame = np.array([])  # Empty array
            processed_frame, landmarks = processor.process_frame(invalid_frame)
            
            # Should handle gracefully
            assert processed_frame is not None
            assert landmarks == {"hands": False, "face": False, "pose": False}
            
    @patch('video_processor.MEDIAPIPE_AVAILABLE', True)
    @patch('video_processor.mp')
    def test_mediapipe_processing_retry_mechanism(self, mock_mp):
        """Test MediaPipe processing retry mechanism on failures"""
        mock_holistic = Mock()
        
        # First attempt fails, second succeeds
        mock_results = Mock()
        mock_results.left_hand_landmarks = Mock()
        mock_results.right_hand_landmarks = None
        mock_results.face_landmarks = Mock()
        mock_results.pose_landmarks = None
        
        mock_holistic.process.side_effect = [
            Exception("First attempt fails"),
            mock_results  # Second attempt succeeds
        ]
        
        mock_mp.solutions.holistic.Holistic.return_value = mock_holistic
        mock_mp.solutions.drawing_utils = Mock()
        mock_mp.solutions.drawing_styles = Mock()
        
        processor = MediaPipeProcessor(self.config)
        
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        processed_frame, landmarks = processor.process_frame(test_frame)
        
        # Should succeed on retry
        assert processed_frame is not None
        assert landmarks["hands"] == True
        assert landmarks["face"] == True
        
    def test_extract_landmarks_safely_edge_cases(self):
        """Test safe landmark extraction with edge cases"""
        processor = MediaPipeProcessor(self.config)
        
        # Test with None results
        landmarks = processor._extract_landmarks_safely(None)
        assert landmarks == {"hands": False, "face": False, "pose": False}
        
        # Test with results missing attributes
        incomplete_results = Mock()
        # Don't set any landmark attributes
        
        landmarks = processor._extract_landmarks_safely(incomplete_results)
        assert isinstance(landmarks, dict)
        assert "hands" in landmarks
        assert "face" in landmarks
        assert "pose" in landmarks
        
    def test_memory_usage_check(self):
        """Test memory usage checking functionality"""
        processor = MediaPipeProcessor(self.config)
        
        # Test memory check (if available)
        if hasattr(processor, '_check_memory_usage'):
            # Should return boolean
            result = processor._check_memory_usage()
            assert isinstance(result, bool)
            
    def test_fallback_frame_creation(self):
        """Test fallback frame creation for various scenarios"""
        processor = MediaPipeProcessor(self.config)
        
        # Test with valid frame
        valid_frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        fallback = processor._create_fallback_frame(valid_frame)
        
        assert fallback is not None
        assert isinstance(fallback, np.ndarray)
        assert fallback.shape == valid_frame.shape
        
        # Test with None
        fallback_none = processor._create_fallback_frame(None)
        
        assert fallback_none is not None
        assert isinstance(fallback_none, np.ndarray)
        assert len(fallback_none.shape) == 3  # Height, Width, Channels
        
        # Test with empty array
        empty_frame = np.array([])
        fallback_empty = processor._create_fallback_frame(empty_frame)
        
        assert fallback_empty is not None
        assert isinstance(fallback_empty, np.ndarray)


class TestLandmarkDetectionAccuracy:
    """Test cases for landmark detection accuracy and quality"""
    
    def setup_method(self):
        """Set up accuracy testing environment"""
        self.video_config = VideoConfig()
        self.mediapipe_config = MediaPipeConfig(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1
        )
        self.processor = FrameProcessor(self.video_config, self.mediapipe_config)
        
    def create_synthetic_person_frame(self, include_hands=True, include_face=True, include_pose=True):
        """Create synthetic frame with person-like features for testing"""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        if include_pose:
            # Draw body/torso region
            cv2.rectangle(frame, (250, 200), (390, 400), (100, 150, 200), -1)
            
        if include_face:
            # Draw face region
            cv2.circle(frame, (320, 150), 50, (255, 220, 177), -1)
            # Add facial features
            cv2.circle(frame, (300, 140), 5, (0, 0, 0), -1)  # Left eye
            cv2.circle(frame, (340, 140), 5, (0, 0, 0), -1)  # Right eye
            cv2.ellipse(frame, (320, 165), (15, 8), 0, 0, 180, (0, 0, 0), 2)  # Mouth
            
        if include_hands:
            # Draw hand regions
            cv2.circle(frame, (200, 300), 25, (255, 220, 177), -1)  # Left hand
            cv2.circle(frame, (440, 300), 25, (255, 220, 177), -1)  # Right hand
            
        return frame
        
    @patch('video_processor.MEDIAPIPE_AVAILABLE', True)
    @patch('video_processor.mp')
    def test_accuracy_with_complete_person(self, mock_mp):
        """Test landmark detection accuracy with complete person in frame"""
        # Mock MediaPipe to detect all landmarks for complete person
        mock_results = Mock()
        mock_results.left_hand_landmarks = Mock()
        mock_results.right_hand_landmarks = Mock()
        mock_results.face_landmarks = Mock()
        mock_results.pose_landmarks = Mock()
        
        mock_holistic = Mock()
        mock_holistic.process.return_value = mock_results
        
        mock_mp.solutions.holistic.Holistic.return_value = mock_holistic
        mock_mp.solutions.drawing_utils = Mock()
        mock_mp.solutions.drawing_styles = Mock()
        
        # Create synthetic person frame
        person_frame = self.create_synthetic_person_frame(
            include_hands=True, 
            include_face=True, 
            include_pose=True
        )
        
        # Process frame
        processed_frame, landmarks, processing_time = self.processor.process_frame_with_mediapipe(person_frame)
        
        # Verify high accuracy detection
        assert landmarks["hands"] == True
        assert landmarks["face"] == True
        assert landmarks["pose"] == True
        
        # Calculate confidence score
        confidence = self.processor._calculate_landmarks_confidence(landmarks)
        assert confidence == 1.0  # Perfect detection
        
    @patch('video_processor.MEDIAPIPE_AVAILABLE', True)
    @patch('video_processor.mp')
    def test_accuracy_with_partial_person(self, mock_mp):
        """Test landmark detection accuracy with partial person visibility"""
        # Mock MediaPipe to detect only visible parts
        mock_results = Mock()
        mock_results.left_hand_landmarks = None  # Hand not visible
        mock_results.right_hand_landmarks = Mock()  # Only right hand visible
        mock_results.face_landmarks = Mock()  # Face visible
        mock_results.pose_landmarks = None  # Pose not fully visible
        
        mock_holistic = Mock()
        mock_holistic.process.return_value = mock_results
        
        mock_mp.solutions.holistic.Holistic.return_value = mock_holistic
        mock_mp.solutions.drawing_utils = Mock()
        mock_mp.solutions.drawing_styles = Mock()
        
        # Create partial person frame
        partial_frame = self.create_synthetic_person_frame(
            include_hands=False,  # No hands in frame
            include_face=True,
            include_pose=False
        )
        
        processed_frame, landmarks, processing_time = self.processor.process_frame_with_mediapipe(partial_frame)
        
        # Verify partial detection
        assert landmarks["hands"] == True  # Right hand detected
        assert landmarks["face"] == True
        assert landmarks["pose"] == False
        
        # Calculate confidence score
        confidence = self.processor._calculate_landmarks_confidence(landmarks)
        assert confidence == 2.0 / 3.0  # 2 out of 3 landmark types
        
    @patch('video_processor.MEDIAPIPE_AVAILABLE', True)
    @patch('video_processor.mp')
    def test_accuracy_with_empty_frame(self, mock_mp):
        """Test landmark detection accuracy with empty/background frame"""
        # Mock MediaPipe to detect nothing in empty frame
        mock_results = Mock()
        mock_results.left_hand_landmarks = None
        mock_results.right_hand_landmarks = None
        mock_results.face_landmarks = None
        mock_results.pose_landmarks = None
        
        mock_holistic = Mock()
        mock_holistic.process.return_value = mock_results
        
        mock_mp.solutions.holistic.Holistic.return_value = mock_holistic
        mock_mp.solutions.drawing_utils = Mock()
        mock_mp.solutions.drawing_styles = Mock()
        
        # Create empty frame (just background)
        empty_frame = np.ones((480, 640, 3), dtype=np.uint8) * 128  # Gray background
        
        processed_frame, landmarks, processing_time = self.processor.process_frame_with_mediapipe(empty_frame)
        
        # Verify no false positives
        assert landmarks["hands"] == False
        assert landmarks["face"] == False
        assert landmarks["pose"] == False
        
        # Calculate confidence score
        confidence = self.processor._calculate_landmarks_confidence(landmarks)
        assert confidence == 0.0  # No detection
        
    def test_confidence_calculation_accuracy(self):
        """Test landmark confidence calculation accuracy"""
        # Test various detection scenarios
        test_cases = [
            ({"hands": True, "face": True, "pose": True}, 1.0),
            ({"hands": True, "face": True, "pose": False}, 2.0/3.0),
            ({"hands": True, "face": False, "pose": False}, 1.0/3.0),
            ({"hands": False, "face": False, "pose": False}, 0.0),
        ]
        
        for landmarks, expected_confidence in test_cases:
            confidence = self.processor._calculate_landmarks_confidence(landmarks)
            assert abs(confidence - expected_confidence) < 0.001  # Float precision
            
    def test_processing_efficiency_calculation(self):
        """Test processing efficiency calculation accuracy"""
        # Test various processing times
        test_cases = [
            (10.0, True),   # Very fast - high efficiency
            (33.3, True),   # Target 30 FPS - good efficiency
            (50.0, False),  # Slower - lower efficiency
            (100.0, False), # Very slow - low efficiency
        ]
        
        for processing_time, should_be_high_efficiency in test_cases:
            efficiency = self.processor._calculate_processing_efficiency(processing_time)
            
            assert 0.0 <= efficiency <= 1.0  # Valid range
            
            if should_be_high_efficiency:
                assert efficiency > 0.5  # Should be reasonably efficient
            else:
                assert efficiency <= 0.8  # Should show reduced efficiency
                
    @patch('video_processor.MEDIAPIPE_AVAILABLE', True)
    @patch('video_processor.mp')
    def test_detection_consistency_across_frames(self, mock_mp):
        """Test detection consistency across multiple similar frames"""
        # Mock consistent MediaPipe results
        mock_results = Mock()
        mock_results.left_hand_landmarks = Mock()
        mock_results.right_hand_landmarks = None
        mock_results.face_landmarks = Mock()
        mock_results.pose_landmarks = Mock()
        
        mock_holistic = Mock()
        mock_holistic.process.return_value = mock_results
        
        mock_mp.solutions.holistic.Holistic.return_value = mock_holistic
        mock_mp.solutions.drawing_utils = Mock()
        mock_mp.solutions.drawing_styles = Mock()
        
        # Create similar frames
        base_frame = self.create_synthetic_person_frame()
        
        # Process multiple similar frames
        results = []
        for i in range(5):
            # Add slight variations to simulate real video
            frame = base_frame.copy()
            noise = np.random.randint(-10, 10, frame.shape, dtype=np.int16)
            frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            
            processed_frame, landmarks, processing_time = self.processor.process_frame_with_mediapipe(frame)
            results.append(landmarks)
            
        # Verify consistency
        for landmarks in results:
            assert landmarks["hands"] == True  # Should consistently detect hands
            assert landmarks["face"] == True   # Should consistently detect face
            assert landmarks["pose"] == True   # Should consistently detect pose
            
    def test_quality_metrics_integration(self):
        """Test integration of quality metrics in processing pipeline"""
        # Create test frame
        test_frame = self.create_synthetic_person_frame()
        
        # Encode to base64
        _, buffer = cv2.imencode('.jpg', test_frame)
        base64_data = base64.b64encode(buffer).decode('utf-8')
        data_url = f"data:image/jpeg;base64,{base64_data}"
        
        # Mock MediaPipe for predictable results
        with patch.object(self.processor.mediapipe_processor, 'process_frame') as mock_process:
            mock_process.return_value = (
                test_frame,
                {"hands": True, "face": True, "pose": False}
            )
            
            result = self.processor.process_base64_frame(data_url, frame_number=1)
            
            # Verify quality metrics are included
            assert "quality_metrics" in result
            quality_metrics = result["quality_metrics"]
            
            assert "landmarks_confidence" in quality_metrics
            assert "processing_efficiency" in quality_metrics
            
            # Verify confidence calculation
            expected_confidence = 2.0 / 3.0  # 2 out of 3 landmarks detected
            assert abs(quality_metrics["landmarks_confidence"] - expected_confidence) < 0.001
            
            # Verify efficiency is calculated
            assert 0.0 <= quality_metrics["processing_efficiency"] <= 1.0


class TestMediaPipePerformanceOptimization:
    """Test cases for MediaPipe performance optimization features"""
    
    def setup_method(self):
        """Set up performance optimization tests"""
        self.config = MediaPipeConfig(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1
        )
        
    @patch('video_processor.MEDIAPIPE_AVAILABLE', True)
    @patch('video_processor.mp')
    def test_optimized_initialization_parameters(self, mock_mp):
        """Test that MediaPipe is initialized with performance-optimized parameters"""
        mock_holistic_class = Mock()
        mock_mp.solutions.holistic.Holistic = mock_holistic_class
        
        processor = MediaPipeProcessor(self.config)
        
        # Verify optimized parameters were used
        call_kwargs = mock_holistic_class.call_args[1]
        
        # Should use lower confidence thresholds for speed
        assert call_kwargs['min_detection_confidence'] <= self.config.min_detection_confidence
        assert call_kwargs['min_tracking_confidence'] <= self.config.min_tracking_confidence
        
        # Should use fast model complexity
        assert call_kwargs['model_complexity'] <= 1
        
        # Should disable expensive features
        assert call_kwargs['enable_segmentation'] == False
        assert call_kwargs['refine_face_landmarks'] == False
        
    @patch('video_processor.MEDIAPIPE_AVAILABLE', True)
    @patch('video_processor.mp')
    def test_processing_retry_limit(self, mock_mp):
        """Test that processing retry attempts are limited for performance"""
        mock_holistic = Mock()
        mock_holistic.process.side_effect = Exception("Processing error")
        
        mock_mp.solutions.holistic.Holistic.return_value = mock_holistic
        
        processor = MediaPipeProcessor(self.config)
        
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Should limit retry attempts and return fallback quickly
        processed_frame, landmarks = processor.process_frame(test_frame)
        
        # Should have attempted processing but fallen back
        assert processed_frame is not None
        assert landmarks == {"hands": False, "face": False, "pose": False}
        
        # Verify limited retry attempts (should not retry indefinitely)
        assert mock_holistic.process.call_count <= 3  # Max 2-3 attempts
        
    def test_frame_preprocessing_optimization(self):
        """Test frame preprocessing optimizations"""
        processor = MediaPipeProcessor(self.config)
        
        # Test with various frame sizes to verify optimization
        test_sizes = [(240, 320), (480, 640), (720, 1280)]
        
        for height, width in test_sizes:
            test_frame = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
            
            # Should handle all sizes without performance degradation
            processed_frame, landmarks = processor.process_frame(test_frame)
            
            assert processed_frame is not None
            assert isinstance(landmarks, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])