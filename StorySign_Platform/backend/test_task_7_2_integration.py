#!/usr/bin/env python3
"""
Integration test for Task 7.2: Frame encoding and streaming response
Tests the complete WebSocket streaming functionality
"""

import pytest
import asyncio
import json
import base64
import cv2
import numpy as np
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from video_processor import FrameProcessor
from config import get_config


class TestTask72Integration:
    """Integration tests for Task 7.2 functionality"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def test_frame_data(self):
        """Create test frame data"""
        # Create a simple test frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.circle(frame, (320, 240), 50, (255, 100, 100), -1)  # Red circle
        
        # Encode as JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        base64_data = base64.b64encode(buffer).decode('utf-8')
        
        return f"data:image/jpeg;base64,{base64_data}"
    
    def test_health_endpoint_includes_streaming_info(self, client):
        """Test that health endpoint includes streaming-related information"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "services" in data
        assert "websocket" in data["services"]
        assert data["services"]["websocket"] == "active"
        assert "active_connections" in data["services"]
    
    def test_frame_processor_initialization(self):
        """Test frame processor initialization with config"""
        config = get_config()
        processor = FrameProcessor(config.video, config.mediapipe)
        
        # Verify processor is properly initialized
        assert processor is not None
        assert hasattr(processor, 'video_config')
        assert hasattr(processor, 'mediapipe_config')
        assert hasattr(processor, 'mediapipe_processor')
    
    def test_enhanced_frame_encoding_functionality(self, test_frame_data):
        """Test enhanced frame encoding with metadata"""
        config = get_config()
        processor = FrameProcessor(config.video, config.mediapipe)
        
        # Process the test frame
        result = processor.process_base64_frame(test_frame_data, frame_number=1)
        
        # Verify result structure matches Task 7.2 requirements
        assert result is not None
        assert isinstance(result, dict)
        assert "success" in result
        
        if result["success"]:
            # Verify successful processing includes all required metadata
            assert "frame_data" in result
            assert "landmarks_detected" in result
            assert "processing_metadata" in result
            assert "quality_metrics" in result
            
            # Verify processing metadata structure
            metadata = result["processing_metadata"]
            assert "frame_number" in metadata
            assert "mediapipe_processing_time_ms" in metadata
            assert "total_pipeline_time_ms" in metadata
            assert "timestamp" in metadata
            
            # Verify quality metrics
            quality = result["quality_metrics"]
            assert "landmarks_confidence" in quality
            assert "processing_efficiency" in quality
        else:
            # Verify graceful degradation
            assert "error" in result
            assert result["landmarks_detected"] == {"hands": False, "face": False, "pose": False}
    
    def test_websocket_message_format_compliance(self):
        """Test WebSocket message format compliance with design spec"""
        from main import VideoProcessingService
        
        config = get_config()
        service = VideoProcessingService("test_client", config)
        
        # Mock successful processing result
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
        
        # Test successful streaming response format
        client_metadata = {"frame_number": 42}
        response = service._create_successful_streaming_response(processing_result, client_metadata)
        
        # Verify response matches design specification
        assert response["type"] == "processed_frame"
        assert "timestamp" in response
        assert "frame_data" in response
        assert "metadata" in response
        
        # Verify metadata structure matches spec
        metadata = response["metadata"]
        required_fields = [
            "client_id", "server_frame_number", "client_frame_number",
            "processing_time_ms", "total_pipeline_time_ms", "landmarks_detected",
            "quality_metrics", "encoding_info", "success"
        ]
        for field in required_fields:
            assert field in metadata, f"Missing required field: {field}"
    
    def test_error_handling_graceful_degradation(self):
        """Test graceful degradation on MediaPipe processing failures"""
        config = get_config()
        processor = FrameProcessor(config.video, config.mediapipe)
        
        # Test with invalid frame data
        invalid_data = "invalid_base64_data"
        result = processor.process_base64_frame(invalid_data, frame_number=1)
        
        # Verify graceful degradation (never returns None)
        assert result is not None
        assert isinstance(result, dict)
        assert "success" in result
        assert result["success"] is False
        
        # Verify error response structure
        assert "error" in result
        assert "landmarks_detected" in result
        assert result["landmarks_detected"] == {"hands": False, "face": False, "pose": False}
        assert "processing_metadata" in result
        assert result["processing_metadata"]["error_occurred"] is True
    
    def test_streaming_response_metadata_generation(self):
        """Test comprehensive metadata generation for streaming responses"""
        config = get_config()
        processor = FrameProcessor(config.video, config.mediapipe)
        
        # Create test frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Test encoding with metadata
        encoding_result = processor.encode_frame_to_base64(frame, include_metadata=True)
        
        # Verify encoding metadata is comprehensive
        assert encoding_result is not None
        assert "encoding_success" in encoding_result
        
        if encoding_result["encoding_success"]:
            assert "encoding_metadata" in encoding_result
            metadata = encoding_result["encoding_metadata"]
            
            # Verify all required metadata fields
            required_fields = [
                "encoding_time_ms", "compressed_size_bytes", "original_size_bytes",
                "compression_ratio", "quality", "format"
            ]
            for field in required_fields:
                assert field in metadata, f"Missing encoding metadata field: {field}"
    
    def test_performance_metrics_calculation(self):
        """Test performance metrics calculation"""
        config = get_config()
        processor = FrameProcessor(config.video, config.mediapipe)
        
        # Test landmarks confidence calculation
        all_detected = {"hands": True, "face": True, "pose": True}
        confidence = processor._calculate_landmarks_confidence(all_detected)
        assert confidence == 1.0
        
        partial_detected = {"hands": True, "face": False, "pose": False}
        confidence = processor._calculate_landmarks_confidence(partial_detected)
        assert confidence == 1.0 / 3.0
        
        # Test processing efficiency calculation
        optimal_efficiency = processor._calculate_processing_efficiency(10.0)  # Under 16.67ms
        assert optimal_efficiency == 1.0
        
        poor_efficiency = processor._calculate_processing_efficiency(50.0)  # Over 33.34ms
        assert poor_efficiency == 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--no-cov"])