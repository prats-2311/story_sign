#!/usr/bin/env python3
"""
Unit tests for video processing module including MediaPipe integration
"""

import pytest
import numpy as np
import cv2
import base64
from unittest.mock import Mock, patch, MagicMock
import json

from video_processor import FrameProcessor, MediaPipeProcessor
from config import VideoConfig, MediaPipeConfig


class TestFrameProcessor:
    """Test cases for FrameProcessor class"""
    
    def setup_method(self):
        """Set up test configuration and processor"""
        self.video_config = VideoConfig(
            width=640,
            height=480,
            fps=30,
            quality=80
        )
        self.mediapipe_config = MediaPipeConfig(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1
        )
        self.processor = FrameProcessor(self.video_config, self.mediapipe_config)
        
    def test_processor_initialization(self):
        """Test FrameProcessor initialization"""
        assert self.processor.video_config == self.video_config
        assert self.processor.mediapipe_config == self.mediapipe_config
        assert self.processor.mediapipe_processor is not None
        
    def test_decode_base64_frame_valid_data(self):
        """Test decoding valid base64 JPEG data"""
        # Create a simple test image
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        test_image[:, :] = [255, 0, 0]  # Red image
        
        # Encode to JPEG then base64
        _, buffer = cv2.imencode('.jpg', test_image)
        base64_data = base64.b64encode(buffer).decode('utf-8')
        data_url = f"data:image/jpeg;base64,{base64_data}"
        
        # Test decoding
        decoded_frame = self.processor.decode_base64_frame(data_url)
        
        assert decoded_frame is not None
        assert isinstance(decoded_frame, np.ndarray)
        assert len(decoded_frame.shape) == 3  # Height, Width, Channels
        assert decoded_frame.shape[2] == 3  # BGR channels
        
    def test_decode_base64_frame_without_prefix(self):
        """Test decoding base64 data without data URL prefix"""
        # Create test image and encode
        test_image = np.zeros((50, 50, 3), dtype=np.uint8)
        _, buffer = cv2.imencode('.jpg', test_image)
        base64_data = base64.b64encode(buffer).decode('utf-8')
        
        # Test decoding without prefix
        decoded_frame = self.processor.decode_base64_frame(base64_data)
        
        assert decoded_frame is not None
        assert isinstance(decoded_frame, np.ndarray)
        
    def test_decode_base64_frame_invalid_data(self):
        """Test decoding invalid base64 data"""
        invalid_data = "invalid_base64_data"
        
        decoded_frame = self.processor.decode_base64_frame(invalid_data)
        
        assert decoded_frame is None
        
    def test_decode_base64_frame_empty_data(self):
        """Test decoding empty base64 data"""
        empty_data = ""
        
        decoded_frame = self.processor.decode_base64_frame(empty_data)
        
        assert decoded_frame is None
        
    def test_encode_frame_to_base64_valid_frame(self):
        """Test encoding valid frame to base64"""
        # Create test frame
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        result = self.processor.encode_frame_to_base64(test_frame, include_metadata=True)
        
        assert result is not None
        assert result["encoding_success"] == True
        assert "frame_data" in result
        assert result["frame_data"].startswith("data:image/jpeg;base64,")
        assert "encoding_metadata" in result
        
        metadata = result["encoding_metadata"]
        assert "encoding_time_ms" in metadata
        assert "compressed_size_bytes" in metadata
        assert "compression_ratio" in metadata
        
    def test_encode_frame_to_base64_without_metadata(self):
        """Test encoding frame without metadata"""
        test_frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        result = self.processor.encode_frame_to_base64(test_frame, include_metadata=False)
        
        assert result is not None
        assert result["encoding_success"] == True
        assert "frame_data" in result
        assert "encoding_metadata" not in result
        
    def test_encode_frame_to_base64_invalid_frame(self):
        """Test encoding invalid frame"""
        invalid_frame = None
        
        result = self.processor.encode_frame_to_base64(invalid_frame)
        
        assert result is not None
        assert result["encoding_success"] == False
        assert "error" in result
        
    @patch('video_processor.MediaPipeProcessor')
    def test_process_frame_with_mediapipe_success(self, mock_mediapipe):
        """Test successful MediaPipe frame processing"""
        # Mock MediaPipe processor
        mock_processor = Mock()
        mock_processor.process_frame.return_value = (
            np.zeros((480, 640, 3), dtype=np.uint8),  # processed frame
            {"hands": True, "face": True, "pose": False},  # landmarks detected
        )
        mock_mediapipe.return_value = mock_processor
        
        # Create new processor with mocked MediaPipe
        processor = FrameProcessor(self.video_config, self.mediapipe_config)
        processor.mediapipe_processor = mock_processor
        
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        processed_frame, landmarks_detected, processing_time = processor.process_frame_with_mediapipe(test_frame)
        
        assert processed_frame is not None
        assert isinstance(landmarks_detected, dict)
        assert "hands" in landmarks_detected
        assert "face" in landmarks_detected
        assert "pose" in landmarks_detected
        assert isinstance(processing_time, float)
        assert processing_time >= 0
        
    @patch('video_processor.MediaPipeProcessor')
    def test_process_frame_with_mediapipe_error(self, mock_mediapipe):
        """Test MediaPipe frame processing with error"""
        # Mock MediaPipe processor to raise exception
        mock_processor = Mock()
        mock_processor.process_frame.side_effect = Exception("MediaPipe error")
        mock_mediapipe.return_value = mock_processor
        
        processor = FrameProcessor(self.video_config, self.mediapipe_config)
        processor.mediapipe_processor = mock_processor
        
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        processed_frame, landmarks_detected, processing_time = processor.process_frame_with_mediapipe(test_frame)
        
        # Should return original frame and empty landmarks on error
        assert np.array_equal(processed_frame, test_frame)
        assert landmarks_detected == {"hands": False, "face": False, "pose": False}
        assert isinstance(processing_time, float)
        
    def test_process_base64_frame_complete_pipeline(self):
        """Test complete base64 frame processing pipeline"""
        # Create test image and encode to base64
        test_image = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
        _, buffer = cv2.imencode('.jpg', test_image)
        base64_data = base64.b64encode(buffer).decode('utf-8')
        data_url = f"data:image/jpeg;base64,{base64_data}"
        
        # Mock MediaPipe processor for predictable results
        with patch.object(self.processor.mediapipe_processor, 'process_frame') as mock_process:
            mock_process.return_value = (
                test_image,  # Return same image
                {"hands": True, "face": False, "pose": True}
            )
            
            result = self.processor.process_base64_frame(data_url, frame_number=1)
            
            assert result["success"] == True
            assert "frame_data" in result
            assert "landmarks_detected" in result
            assert "processing_metadata" in result
            assert "quality_metrics" in result
            
            # Verify landmarks
            landmarks = result["landmarks_detected"]
            assert landmarks["hands"] == True
            assert landmarks["face"] == False
            assert landmarks["pose"] == True
            
            # Verify metadata
            metadata = result["processing_metadata"]
            assert metadata["frame_number"] == 1
            assert "mediapipe_processing_time_ms" in metadata
            assert "total_pipeline_time_ms" in metadata
            assert "timestamp" in metadata
            
    def test_process_base64_frame_skip_processing(self):
        """Test base64 frame processing with MediaPipe processing skipped"""
        # Create test image
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        _, buffer = cv2.imencode('.jpg', test_image)
        base64_data = base64.b64encode(buffer).decode('utf-8')
        data_url = f"data:image/jpeg;base64,{base64_data}"
        
        result = self.processor.process_base64_frame(data_url, frame_number=5, skip_processing=True)
        
        assert result["success"] == True
        assert result["landmarks_detected"] == {"hands": False, "face": False, "pose": False}
        assert result["processing_metadata"]["processing_skipped"] == True
        assert result["processing_metadata"]["mediapipe_processing_time_ms"] == 0.0
        
    def test_process_base64_frame_invalid_input(self):
        """Test base64 frame processing with invalid input"""
        invalid_data = "invalid_base64_data"
        
        result = self.processor.process_base64_frame(invalid_data, frame_number=1)
        
        assert result["success"] == False
        assert "error" in result
        assert result["landmarks_detected"] == {"hands": False, "face": False, "pose": False}
        
    def test_calculate_landmarks_confidence(self):
        """Test landmarks confidence calculation"""
        # All landmarks detected
        all_detected = {"hands": True, "face": True, "pose": True}
        confidence = self.processor._calculate_landmarks_confidence(all_detected)
        assert confidence == 1.0
        
        # Partial detection
        partial_detected = {"hands": True, "face": False, "pose": True}
        confidence = self.processor._calculate_landmarks_confidence(partial_detected)
        assert confidence == 2.0 / 3.0
        
        # No detection
        none_detected = {"hands": False, "face": False, "pose": False}
        confidence = self.processor._calculate_landmarks_confidence(none_detected)
        assert confidence == 0.0
        
    def test_calculate_processing_efficiency(self):
        """Test processing efficiency calculation"""
        # Fast processing (under target)
        fast_time = 10.0  # 10ms
        efficiency = self.processor._calculate_processing_efficiency(fast_time)
        assert efficiency > 0.8  # Should be high efficiency
        
        # Slow processing (over target)
        slow_time = 100.0  # 100ms
        efficiency = self.processor._calculate_processing_efficiency(slow_time)
        assert efficiency < 0.5  # Should be low efficiency
        
        # Target processing time
        target_time = 33.3  # ~30 FPS target
        efficiency = self.processor._calculate_processing_efficiency(target_time)
        assert 0.5 <= efficiency <= 1.0


class TestMediaPipeProcessor:
    """Test cases for MediaPipeProcessor class"""
    
    def setup_method(self):
        """Set up MediaPipe processor"""
        self.config = MediaPipeConfig(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1
        )
        
    @patch('video_processor.MEDIAPIPE_AVAILABLE', True)
    @patch('video_processor.mp')
    def test_mediapipe_processor_initialization(self, mock_mp):
        """Test MediaPipeProcessor initialization with MediaPipe available"""
        # Mock MediaPipe components
        mock_holistic_class = Mock()
        mock_holistic_instance = Mock()
        mock_holistic_class.return_value = mock_holistic_instance
        
        mock_mp.solutions.holistic.Holistic = mock_holistic_class
        mock_mp.solutions.drawing_utils = Mock()
        mock_mp.solutions.drawing_styles = Mock()
        
        processor = MediaPipeProcessor(self.config)
        
        assert processor.config == self.config
        assert processor.holistic == mock_holistic_instance
        
        # Verify holistic model was initialized with correct parameters
        mock_holistic_class.assert_called_once()
        call_args = mock_holistic_class.call_args[1]
        assert call_args['model_complexity'] <= 1  # Should be optimized for speed
        assert call_args['enable_segmentation'] == False
        assert call_args['refine_face_landmarks'] == False
        
    @patch('video_processor.MEDIAPIPE_AVAILABLE', False)
    def test_mediapipe_processor_initialization_unavailable(self):
        """Test MediaPipeProcessor initialization when MediaPipe unavailable"""
        processor = MediaPipeProcessor(self.config)
        
        assert processor.config == self.config
        # Should still initialize without crashing
        
    @patch('video_processor.MEDIAPIPE_AVAILABLE', True)
    @patch('video_processor.mp')
    def test_process_frame_success(self, mock_mp):
        """Test successful frame processing with MediaPipe"""
        # Mock MediaPipe results
        mock_results = Mock()
        mock_results.left_hand_landmarks = Mock()  # Hands detected
        mock_results.right_hand_landmarks = None
        mock_results.face_landmarks = Mock()  # Face detected
        mock_results.pose_landmarks = None  # No pose
        
        # Mock holistic processor
        mock_holistic = Mock()
        mock_holistic.process.return_value = mock_results
        
        mock_mp.solutions.holistic.Holistic.return_value = mock_holistic
        mock_mp.solutions.drawing_utils = Mock()
        mock_mp.solutions.drawing_styles = Mock()
        
        processor = MediaPipeProcessor(self.config)
        
        # Create test frame
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        processed_frame, landmarks_detected = processor.process_frame(test_frame)
        
        assert processed_frame is not None
        assert isinstance(processed_frame, np.ndarray)
        assert landmarks_detected["hands"] == True  # Left hand detected
        assert landmarks_detected["face"] == True   # Face detected
        assert landmarks_detected["pose"] == False  # No pose detected
        
    @patch('video_processor.MEDIAPIPE_AVAILABLE', False)
    def test_process_frame_mediapipe_unavailable(self):
        """Test frame processing when MediaPipe is unavailable"""
        processor = MediaPipeProcessor(self.config)
        
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        processed_frame, landmarks_detected = processor.process_frame(test_frame)
        
        # Should return original frame and no landmarks
        assert np.array_equal(processed_frame, test_frame)
        assert landmarks_detected == {"hands": False, "face": False, "pose": False}
        
    @patch('video_processor.MEDIAPIPE_AVAILABLE', True)
    @patch('video_processor.mp')
    def test_process_frame_with_processing_error(self, mock_mp):
        """Test frame processing with MediaPipe processing error"""
        # Mock holistic processor to raise exception
        mock_holistic = Mock()
        mock_holistic.process.side_effect = Exception("MediaPipe processing error")
        
        mock_mp.solutions.holistic.Holistic.return_value = mock_holistic
        
        processor = MediaPipeProcessor(self.config)
        
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        processed_frame, landmarks_detected = processor.process_frame(test_frame)
        
        # Should handle error gracefully and return fallback
        assert processed_frame is not None
        assert landmarks_detected == {"hands": False, "face": False, "pose": False}
        
    def test_process_frame_invalid_input(self):
        """Test frame processing with invalid input"""
        processor = MediaPipeProcessor(self.config)
        
        # Test with None frame
        processed_frame, landmarks_detected = processor.process_frame(None)
        
        assert processed_frame is not None  # Should return fallback frame
        assert landmarks_detected == {"hands": False, "face": False, "pose": False}
        
        # Test with empty frame
        empty_frame = np.array([])
        processed_frame, landmarks_detected = processor.process_frame(empty_frame)
        
        assert processed_frame is not None
        assert landmarks_detected == {"hands": False, "face": False, "pose": False}
        
    def test_extract_landmarks_safely(self):
        """Test safe landmark extraction from MediaPipe results"""
        processor = MediaPipeProcessor(self.config)
        
        # Mock results with various landmark combinations
        mock_results = Mock()
        mock_results.left_hand_landmarks = Mock()
        mock_results.right_hand_landmarks = None
        mock_results.face_landmarks = Mock()
        mock_results.pose_landmarks = Mock()
        
        landmarks = processor._extract_landmarks_safely(mock_results)
        
        assert landmarks["hands"] == True  # At least one hand detected
        assert landmarks["face"] == True
        assert landmarks["pose"] == True
        
        # Test with no landmarks
        mock_results_empty = Mock()
        mock_results_empty.left_hand_landmarks = None
        mock_results_empty.right_hand_landmarks = None
        mock_results_empty.face_landmarks = None
        mock_results_empty.pose_landmarks = None
        
        landmarks_empty = processor._extract_landmarks_safely(mock_results_empty)
        
        assert landmarks_empty == {"hands": False, "face": False, "pose": False}
        
    def test_extract_landmarks_safely_with_errors(self):
        """Test landmark extraction with attribute errors"""
        processor = MediaPipeProcessor(self.config)
        
        # Mock results that raise AttributeError
        mock_results = Mock()
        del mock_results.left_hand_landmarks  # Remove attribute to cause AttributeError
        
        landmarks = processor._extract_landmarks_safely(mock_results)
        
        # Should handle errors gracefully
        assert isinstance(landmarks, dict)
        assert "hands" in landmarks
        assert "face" in landmarks
        assert "pose" in landmarks
        
    def test_create_fallback_frame(self):
        """Test fallback frame creation"""
        processor = MediaPipeProcessor(self.config)
        
        # Test with valid original frame
        original_frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        fallback_frame = processor._create_fallback_frame(original_frame)
        
        assert fallback_frame is not None
        assert isinstance(fallback_frame, np.ndarray)
        assert fallback_frame.shape == original_frame.shape
        
        # Test with None frame
        fallback_frame_none = processor._create_fallback_frame(None)
        
        assert fallback_frame_none is not None
        assert isinstance(fallback_frame_none, np.ndarray)
        assert len(fallback_frame_none.shape) == 3
        
    def test_processor_cleanup(self):
        """Test MediaPipe processor cleanup"""
        processor = MediaPipeProcessor(self.config)
        
        # Mock holistic model
        mock_holistic = Mock()
        processor.holistic = mock_holistic
        
        processor.close()
        
        mock_holistic.close.assert_called_once()


class TestIntegrationScenarios:
    """Integration test scenarios for video processing pipeline"""
    
    def setup_method(self):
        """Set up integration test environment"""
        self.video_config = VideoConfig(width=320, height=240, quality=60)
        self.mediapipe_config = MediaPipeConfig(model_complexity=0)  # Fastest model
        self.processor = FrameProcessor(self.video_config, self.mediapipe_config)
        
    def test_end_to_end_processing_pipeline(self):
        """Test complete end-to-end processing pipeline"""
        # Create realistic test image (person-like shape)
        test_image = np.zeros((240, 320, 3), dtype=np.uint8)
        # Add some colored regions to simulate a person
        test_image[50:150, 100:220] = [128, 64, 32]  # Body region
        test_image[30:80, 130:190] = [255, 220, 177]  # Face region
        test_image[80:120, 80:140] = [255, 220, 177]  # Left hand
        test_image[80:120, 180:240] = [255, 220, 177]  # Right hand
        
        # Encode to base64
        _, buffer = cv2.imencode('.jpg', test_image)
        base64_data = base64.b64encode(buffer).decode('utf-8')
        data_url = f"data:image/jpeg;base64,{base64_data}"
        
        # Process through complete pipeline
        result = self.processor.process_base64_frame(data_url, frame_number=1)
        
        # Verify result structure
        assert result["success"] == True
        assert "frame_data" in result
        assert "landmarks_detected" in result
        assert "processing_metadata" in result
        assert "quality_metrics" in result
        
        # Verify frame data is valid base64
        frame_data = result["frame_data"]
        assert frame_data.startswith("data:image/jpeg;base64,")
        
        # Verify processing metadata
        metadata = result["processing_metadata"]
        assert metadata["frame_number"] == 1
        assert metadata["mediapipe_processing_time_ms"] >= 0
        assert metadata["total_pipeline_time_ms"] >= metadata["mediapipe_processing_time_ms"]
        
    def test_high_throughput_processing(self):
        """Test processing multiple frames in sequence"""
        # Create multiple test frames
        frames = []
        for i in range(5):
            test_image = np.random.randint(0, 255, (120, 160, 3), dtype=np.uint8)
            _, buffer = cv2.imencode('.jpg', test_image)
            base64_data = base64.b64encode(buffer).decode('utf-8')
            data_url = f"data:image/jpeg;base64,{base64_data}"
            frames.append(data_url)
        
        # Process all frames
        results = []
        for i, frame_data in enumerate(frames):
            result = self.processor.process_base64_frame(frame_data, frame_number=i+1)
            results.append(result)
        
        # Verify all frames processed successfully
        assert len(results) == 5
        for i, result in enumerate(results):
            assert result["success"] == True
            assert result["processing_metadata"]["frame_number"] == i + 1
            
    def test_error_recovery_scenarios(self):
        """Test error recovery in various failure scenarios"""
        # Test with corrupted base64 data
        corrupted_data = "data:image/jpeg;base64,corrupted_base64_data"
        result = self.processor.process_base64_frame(corrupted_data, frame_number=1)
        
        assert result["success"] == False
        assert "error" in result
        
        # Test with empty data
        empty_result = self.processor.process_base64_frame("", frame_number=2)
        
        assert empty_result["success"] == False
        
        # Test with very small image
        tiny_image = np.ones((1, 1, 3), dtype=np.uint8)
        _, buffer = cv2.imencode('.jpg', tiny_image)
        base64_data = base64.b64encode(buffer).decode('utf-8')
        data_url = f"data:image/jpeg;base64,{base64_data}"
        
        tiny_result = self.processor.process_base64_frame(data_url, frame_number=3)
        
        # Should handle gracefully (may succeed or fail, but shouldn't crash)
        assert "success" in tiny_result
        
    def test_performance_under_load(self):
        """Test performance characteristics under load"""
        import time
        
        # Create test frame
        test_image = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
        _, buffer = cv2.imencode('.jpg', test_image)
        base64_data = base64.b64encode(buffer).decode('utf-8')
        data_url = f"data:image/jpeg;base64,{base64_data}"
        
        # Measure processing time for multiple frames
        processing_times = []
        num_frames = 10
        
        for i in range(num_frames):
            start_time = time.time()
            result = self.processor.process_base64_frame(data_url, frame_number=i+1)
            end_time = time.time()
            
            processing_time = (end_time - start_time) * 1000  # Convert to ms
            processing_times.append(processing_time)
            
            assert result["success"] == True
        
        # Verify reasonable performance
        avg_processing_time = sum(processing_times) / len(processing_times)
        max_processing_time = max(processing_times)
        
        # Should process frames in reasonable time (adjust thresholds as needed)
        assert avg_processing_time < 200.0  # Average under 200ms
        assert max_processing_time < 500.0  # Max under 500ms
        
        print(f"Average processing time: {avg_processing_time:.2f}ms")
        print(f"Max processing time: {max_processing_time:.2f}ms")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])