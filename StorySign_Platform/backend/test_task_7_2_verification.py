#!/usr/bin/env python3
"""
Test verification for Task 7.2: Frame encoding and streaming response
Tests frame re-encoding, metadata generation, WebSocket message formatting, and error handling
"""

import pytest
import numpy as np
import cv2
import base64
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from video_processor import FrameProcessor, MediaPipeProcessor
from config import VideoConfig, MediaPipeConfig


class TestFrameEncodingAndStreaming:
    """Test suite for frame encoding and streaming response functionality"""
    
    @pytest.fixture
    def video_config(self):
        """Create test video configuration"""
        return VideoConfig(
            width=640,
            height=480,
            fps=30,
            quality=85
        )
    
    @pytest.fixture
    def mediapipe_config(self):
        """Create test MediaPipe configuration"""
        return MediaPipeConfig(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1
        )
    
    @pytest.fixture
    def frame_processor(self, video_config, mediapipe_config):
        """Create frame processor instance"""
        return FrameProcessor(video_config, mediapipe_config)
    
    @pytest.fixture
    def test_frame(self):
        """Create test frame"""
        return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    def test_enhanced_frame_encoding_with_metadata(self, frame_processor, test_frame):
        """Test enhanced frame encoding with metadata generation"""
        # Test encoding with metadata
        result = frame_processor.encode_frame_to_base64(test_frame, include_metadata=True)
        
        # Verify result structure
        assert result is not None
        assert isinstance(result, dict)
        assert "frame_data" in result
        assert "encoding_success" in result
        assert result["encoding_success"] is True
        
        # Verify metadata is included
        assert "encoding_metadata" in result
        metadata = result["encoding_metadata"]
        assert "encoding_time_ms" in metadata
        assert "compressed_size_bytes" in metadata
        assert "original_size_bytes" in metadata
        assert "compression_ratio" in metadata
        assert "quality" in metadata
        assert "format" in metadata
        
        # Verify frame data format
        frame_data = result["frame_data"]
        assert frame_data.startswith("data:image/jpeg;base64,")
        
        # Verify metadata values are reasonable
        assert metadata["encoding_time_ms"] >= 0
        assert metadata["compressed_size_bytes"] > 0
        assert metadata["original_size_bytes"] > 0
        assert metadata["compression_ratio"] > 0
        assert metadata["quality"] == 85
        assert metadata["format"] == "JPEG"
    
    def test_enhanced_frame_encoding_without_metadata(self, frame_processor, test_frame):
        """Test frame encoding without metadata"""
        result = frame_processor.encode_frame_to_base64(test_frame, include_metadata=False)
        
        # Verify result structure
        assert result is not None
        assert isinstance(result, dict)
        assert "frame_data" in result
        assert "encoding_success" in result
        assert result["encoding_success"] is True
        
        # Verify metadata is not included
        assert "encoding_metadata" not in result
    
    def test_frame_encoding_error_handling(self, frame_processor):
        """Test frame encoding error handling"""
        # Test with invalid frame
        invalid_frame = None
        result = frame_processor.encode_frame_to_base64(invalid_frame)
        
        # Verify error response
        assert result is not None
        assert isinstance(result, dict)
        assert "encoding_success" in result
        assert result["encoding_success"] is False
        assert "error" in result
    
    def test_enhanced_frame_processing_pipeline(self, frame_processor, test_frame):
        """Test enhanced frame processing pipeline with comprehensive metadata"""
        # Create base64 test data
        _, buffer = cv2.imencode('.jpg', test_frame)
        base64_data = base64.b64encode(buffer).decode('utf-8')
        data_url = f"data:image/jpeg;base64,{base64_data}"
        
        # Process frame
        result = frame_processor.process_base64_frame(data_url, frame_number=42)
        
        # Verify result structure
        assert result is not None
        assert isinstance(result, dict)
        assert "success" in result
        
        if result["success"]:
            # Verify successful processing structure
            assert "frame_data" in result
            assert "landmarks_detected" in result
            assert "processing_metadata" in result
            assert "quality_metrics" in result
            
            # Verify processing metadata
            metadata = result["processing_metadata"]
            assert "frame_number" in metadata
            assert metadata["frame_number"] == 42
            assert "mediapipe_processing_time_ms" in metadata
            assert "total_pipeline_time_ms" in metadata
            assert "timestamp" in metadata
            
            # Verify quality metrics
            quality = result["quality_metrics"]
            assert "landmarks_confidence" in quality
            assert "processing_efficiency" in quality
            assert 0.0 <= quality["landmarks_confidence"] <= 1.0
            assert 0.0 <= quality["processing_efficiency"] <= 1.0
        else:
            # Verify error handling structure
            assert "error" in result
            assert "landmarks_detected" in result
            assert result["landmarks_detected"] == {"hands": False, "face": False, "pose": False}
    
    def test_graceful_degradation_on_processing_failure(self, frame_processor):
        """Test graceful degradation when processing fails"""
        # Test with invalid base64 data
        invalid_data = "invalid_base64_data"
        result = frame_processor.process_base64_frame(invalid_data, frame_number=1)
        
        # Verify graceful degradation
        assert result is not None
        assert isinstance(result, dict)
        assert "success" in result
        assert result["success"] is False
        assert "error" in result
        assert "landmarks_detected" in result
        assert result["landmarks_detected"] == {"hands": False, "face": False, "pose": False}
    
    def test_landmarks_confidence_calculation(self, frame_processor):
        """Test landmarks confidence calculation"""
        # Test all landmarks detected
        all_detected = {"hands": True, "face": True, "pose": True}
        confidence = frame_processor._calculate_landmarks_confidence(all_detected)
        assert confidence == 1.0
        
        # Test partial detection
        partial_detected = {"hands": True, "face": False, "pose": True}
        confidence = frame_processor._calculate_landmarks_confidence(partial_detected)
        assert confidence == 2.0 / 3.0
        
        # Test no detection
        none_detected = {"hands": False, "face": False, "pose": False}
        confidence = frame_processor._calculate_landmarks_confidence(none_detected)
        assert confidence == 0.0
    
    def test_processing_efficiency_calculation(self, frame_processor):
        """Test processing efficiency calculation"""
        # Test optimal performance (16.67ms or less)
        efficiency = frame_processor._calculate_processing_efficiency(10.0)
        assert efficiency == 1.0
        
        # Test acceptable performance (within 2x target)
        efficiency = frame_processor._calculate_processing_efficiency(25.0)
        assert 0.1 < efficiency < 1.0
        
        # Test poor performance (over 2x target)
        efficiency = frame_processor._calculate_processing_efficiency(50.0)
        assert efficiency == 0.1
    
    def test_error_response_creation(self, frame_processor):
        """Test error response creation"""
        error_response = frame_processor._create_error_response("Test error", 123)
        
        # Verify error response structure
        assert error_response is not None
        assert isinstance(error_response, dict)
        assert "success" in error_response
        assert error_response["success"] is False
        assert "error" in error_response
        assert error_response["error"] == "Test error"
        assert "frame_data" in error_response
        assert error_response["frame_data"] is None
        assert "landmarks_detected" in error_response
        assert "processing_metadata" in error_response
        assert error_response["processing_metadata"]["frame_number"] == 123


class TestWebSocketStreamingResponse:
    """Test WebSocket streaming response functionality"""
    
    def test_streaming_response_format(self):
        """Test WebSocket streaming response message format"""
        # Mock processing result
        processing_result = {
            "success": True,
            "frame_data": "data:image/jpeg;base64,test_data",
            "landmarks_detected": {"hands": True, "face": False, "pose": True},
            "processing_metadata": {
                "mediapipe_processing_time_ms": 15.5,
                "total_pipeline_time_ms": 18.2,
                "encoding_metadata": {
                    "compression_ratio": 8.5,
                    "quality": 85
                }
            },
            "quality_metrics": {
                "landmarks_confidence": 0.67,
                "processing_efficiency": 0.95
            }
        }
        
        # Mock VideoProcessingService
        from main import VideoProcessingService
        from config import get_config
        
        config = get_config()
        service = VideoProcessingService("test_client", config)
        service.frame_count = 42
        
        # Test successful streaming response
        client_metadata = {"frame_number": 41}
        response = service._create_successful_streaming_response(processing_result, client_metadata)
        
        # Verify response structure
        assert response["type"] == "processed_frame"
        assert "timestamp" in response
        assert "frame_data" in response
        assert response["frame_data"] == "data:image/jpeg;base64,test_data"
        
        # Verify metadata structure
        metadata = response["metadata"]
        assert metadata["client_id"] == "test_client"
        assert metadata["server_frame_number"] == 42
        assert metadata["client_frame_number"] == 41
        assert metadata["success"] is True
        assert "landmarks_detected" in metadata
        assert "quality_metrics" in metadata
        assert "encoding_info" in metadata
    
    def test_degraded_streaming_response(self):
        """Test degraded streaming response for error handling"""
        # Mock failed processing result
        processing_result = {
            "success": False,
            "error": "MediaPipe processing failed",
            "landmarks_detected": {"hands": False, "face": False, "pose": False}
        }
        
        # Mock VideoProcessingService
        from main import VideoProcessingService
        from config import get_config
        
        config = get_config()
        service = VideoProcessingService("test_client", config)
        service.frame_count = 42
        
        # Test degraded streaming response
        client_metadata = {"frame_number": 41}
        response = service._create_degraded_streaming_response(processing_result, client_metadata)
        
        # Verify degraded response structure
        assert response["type"] == "processed_frame"
        assert response["frame_data"] is None
        
        # Verify metadata indicates failure
        metadata = response["metadata"]
        assert metadata["success"] is False
        assert metadata["degraded_mode"] is True
        assert "error" in metadata
        assert metadata["landmarks_detected"] == {"hands": False, "face": False, "pose": False}


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])