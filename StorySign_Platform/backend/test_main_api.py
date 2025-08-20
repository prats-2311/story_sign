#!/usr/bin/env python3
"""
Unit tests for main FastAPI application endpoints and WebSocket functionality
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
import websockets

# Import the main application
from main import app, VideoProcessingService, ResourceMonitor, PerformanceOptimizer
from config import AppConfig, VideoConfig, MediaPipeConfig, ServerConfig


class TestMainAPI:
    """Test cases for main FastAPI application"""
    
    def setup_method(self):
        """Set up test client and mocks"""
        self.client = TestClient(app)
        
    def test_health_endpoint_success(self):
        """Test GET / health check endpoint returns correct response"""
        response = self.client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "message" in data
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "services" in data
        
        # Verify response content
        assert data["status"] == "healthy"
        assert "StorySign Backend" in data["message"]
        assert data["services"]["mediapipe"] in ["ready", "unavailable"]
        assert data["services"]["websocket"] == "active"
        assert isinstance(data["services"]["active_connections"], int)
        
    def test_health_endpoint_response_format(self):
        """Test health endpoint returns properly formatted JSON"""
        response = self.client.get("/")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        
        data = response.json()
        
        # Verify timestamp format (ISO 8601)
        import datetime
        try:
            datetime.datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
        except ValueError:
            pytest.fail("Timestamp is not in valid ISO format")
            
    def test_cors_headers_present(self):
        """Test that CORS headers are properly configured"""
        response = self.client.get("/")
        
        # CORS headers should be present for cross-origin requests
        assert response.status_code == 200
        
        # Test preflight request
        options_response = self.client.options("/")
        assert options_response.status_code == 200
        
    def test_invalid_endpoint_returns_404(self):
        """Test that invalid endpoints return 404"""
        response = self.client.get("/invalid-endpoint")
        assert response.status_code == 404
        
    def test_health_endpoint_under_load(self):
        """Test health endpoint performance under multiple requests"""
        import concurrent.futures
        import time
        
        def make_request():
            return self.client.get("/")
        
        start_time = time.time()
        
        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in futures]
        
        end_time = time.time()
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            
        # Should complete within reasonable time (5 seconds)
        assert end_time - start_time < 5.0


class TestWebSocketEndpoint:
    """Test cases for WebSocket video streaming endpoint"""
    
    def setup_method(self):
        """Set up test client"""
        self.client = TestClient(app)
        
    def test_websocket_connection_success(self):
        """Test successful WebSocket connection to /ws/video"""
        with self.client.websocket_connect("/ws/video") as websocket:
            # Connection should be established
            assert websocket is not None
            
    def test_websocket_connection_url_validation(self):
        """Test WebSocket connection with invalid URL"""
        try:
            with self.client.websocket_connect("/ws/invalid"):
                pytest.fail("Should not connect to invalid WebSocket URL")
        except Exception:
            # Expected to fail
            pass
            
    @patch('main.VideoProcessingService')
    def test_websocket_message_handling(self, mock_service_class):
        """Test WebSocket message handling with mocked service"""
        mock_service = Mock()
        mock_service.start_processing = AsyncMock()
        mock_service.stop_processing = AsyncMock()
        mock_service.add_frame_to_queue = AsyncMock()
        mock_service_class.return_value = mock_service
        
        with self.client.websocket_connect("/ws/video") as websocket:
            # Send test frame message
            test_message = {
                "type": "raw_frame",
                "timestamp": "2024-08-20T10:30:00.000Z",
                "frame_data": "data:image/jpeg;base64,dGVzdGRhdGE=",  # base64 "testdata"
                "metadata": {
                    "frame_number": 1,
                    "client_id": "test_client"
                }
            }
            
            websocket.send_json(test_message)
            
            # Service should be called to process frame
            mock_service.add_frame_to_queue.assert_called_once()
            
    def test_websocket_invalid_json_handling(self):
        """Test WebSocket handling of invalid JSON messages"""
        with self.client.websocket_connect("/ws/video") as websocket:
            # Send invalid JSON
            websocket.send_text("invalid json {")
            
            # Connection should remain open and handle gracefully
            # Send valid message after invalid one
            test_message = {
                "type": "raw_frame",
                "timestamp": "2024-08-20T10:30:00.000Z",
                "frame_data": "data:image/jpeg;base64,dGVzdGRhdGE=",
                "metadata": {"frame_number": 1}
            }
            
            websocket.send_json(test_message)
            
    def test_websocket_connection_cleanup(self):
        """Test WebSocket connection cleanup on disconnect"""
        with patch('main.VideoProcessingService') as mock_service_class:
            mock_service = Mock()
            mock_service.start_processing = AsyncMock()
            mock_service.stop_processing = AsyncMock()
            mock_service_class.return_value = mock_service
            
            with self.client.websocket_connect("/ws/video") as websocket:
                pass  # Connection established and closed
                
            # Service should be stopped on disconnect
            mock_service.stop_processing.assert_called_once()


class TestVideoProcessingService:
    """Test cases for VideoProcessingService class"""
    
    def setup_method(self):
        """Set up test configuration and service"""
        self.config = AppConfig(
            video=VideoConfig(),
            mediapipe=MediaPipeConfig(),
            server=ServerConfig()
        )
        self.client_id = "test_client_123"
        
    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test VideoProcessingService initialization"""
        service = VideoProcessingService(self.client_id, self.config)
        
        assert service.client_id == self.client_id
        assert service.config == self.config
        assert service.is_active == False
        assert service.frame_count == 0
        assert service.frame_processor is not None
        
    @pytest.mark.asyncio
    async def test_service_start_stop_processing(self):
        """Test starting and stopping video processing"""
        service = VideoProcessingService(self.client_id, self.config)
        mock_websocket = Mock()
        
        # Start processing
        await service.start_processing(mock_websocket)
        
        assert service.is_active == True
        assert service.websocket == mock_websocket
        assert service.processing_loop_task is not None
        
        # Stop processing
        await service.stop_processing()
        
        assert service.is_active == False
        
    @pytest.mark.asyncio
    async def test_frame_queue_management(self):
        """Test frame queue operations"""
        service = VideoProcessingService(self.client_id, self.config)
        
        test_frame = {
            "type": "raw_frame",
            "frame_data": "data:image/jpeg;base64,dGVzdGRhdGE=",
            "metadata": {"frame_number": 1}
        }
        
        # Add frame to queue
        await service.add_frame_to_queue(test_frame)
        
        assert not service.frame_queue.empty()
        
        # Get frame from queue
        queued_frame = await service.frame_queue.get()
        assert queued_frame == test_frame
        
    @pytest.mark.asyncio
    async def test_frame_queue_overflow_handling(self):
        """Test frame queue overflow handling"""
        service = VideoProcessingService(self.client_id, self.config)
        
        # Fill queue to capacity
        for i in range(service.frame_queue.maxsize + 2):
            test_frame = {
                "type": "raw_frame",
                "frame_data": f"data:image/jpeg;base64,dGVzdGRhdGE{i}=",
                "metadata": {"frame_number": i}
            }
            
            await service.add_frame_to_queue(test_frame)
            
        # Queue should handle overflow gracefully
        assert service.frame_queue.qsize() <= service.frame_queue.maxsize
        
    @pytest.mark.asyncio
    async def test_processing_stats_tracking(self):
        """Test processing statistics tracking"""
        service = VideoProcessingService(self.client_id, self.config)
        
        # Initial stats
        assert service.processing_stats['frames_processed'] == 0
        assert service.processing_stats['frames_dropped'] == 0
        
        # Update stats
        service._update_processing_stats(25.5)  # 25.5ms processing time
        
        assert service.processing_stats['frames_processed'] == 1
        assert service.processing_stats['total_processing_time'] == 25.5
        assert service.processing_stats['average_processing_time'] == 25.5
        
        # Update with second frame
        service._update_processing_stats(15.0)
        
        assert service.processing_stats['frames_processed'] == 2
        assert service.processing_stats['average_processing_time'] == 20.25  # (25.5 + 15.0) / 2


class TestResourceMonitor:
    """Test cases for ResourceMonitor class"""
    
    def setup_method(self):
        """Set up resource monitor"""
        self.client_id = "test_client_monitor"
        
    @pytest.mark.asyncio
    async def test_monitor_initialization(self):
        """Test ResourceMonitor initialization"""
        monitor = ResourceMonitor(self.client_id)
        
        assert monitor.client_id == self.client_id
        assert monitor.monitoring_active == False
        assert monitor.memory_limit_mb == 512
        assert monitor.cpu_limit_percent == 80
        
    @pytest.mark.asyncio
    async def test_monitor_start_stop(self):
        """Test starting and stopping resource monitoring"""
        monitor = ResourceMonitor(self.client_id)
        
        # Start monitoring
        await monitor.start_monitoring()
        
        assert monitor.monitoring_active == True
        assert monitor.monitoring_task is not None
        
        # Stop monitoring
        await monitor.stop_monitoring()
        
        assert monitor.monitoring_active == False
        
    @pytest.mark.asyncio
    @patch('psutil.Process')
    async def test_resource_stats_collection(self, mock_process):
        """Test resource statistics collection"""
        # Mock psutil.Process
        mock_proc = Mock()
        mock_proc.cpu_percent.return_value = 45.5
        mock_proc.memory_percent.return_value = 60.2
        mock_proc.memory_info.return_value = Mock(rss=512 * 1024 * 1024)  # 512MB
        mock_process.return_value = mock_proc
        
        monitor = ResourceMonitor(self.client_id)
        
        stats = await monitor._collect_resource_stats()
        
        assert stats['cpu_percent'] == 45.5
        assert stats['memory_percent'] == 60.2
        assert stats['memory_mb'] == 512.0
        assert 'timestamp' in stats
        
    @pytest.mark.asyncio
    async def test_resource_limit_violation_detection(self):
        """Test resource limit violation detection"""
        monitor = ResourceMonitor(self.client_id)
        
        # Normal usage - no violation
        normal_stats = {
            'cpu_percent': 50.0,
            'memory_mb': 256.0,
            'timestamp': 1000000
        }
        
        violation = await monitor._check_resource_limits(normal_stats)
        assert violation == False
        assert monitor.consecutive_violations == 0
        
        # High usage - violation
        high_stats = {
            'cpu_percent': 90.0,  # Above 80% limit
            'memory_mb': 600.0,   # Above 512MB limit
            'timestamp': 1000001
        }
        
        # Multiple violations needed to trigger enforcement
        for i in range(monitor.max_violations):
            violation = await monitor._check_resource_limits(high_stats)
            
        assert monitor.consecutive_violations == monitor.max_violations
        assert violation == True  # Should trigger enforcement
        
    @pytest.mark.asyncio
    async def test_average_stats_calculation(self):
        """Test average statistics calculation over time window"""
        monitor = ResourceMonitor(self.client_id)
        
        # Add some sample stats
        import time
        current_time = time.time()
        
        for i in range(5):
            stats = {
                'cpu_percent': 40.0 + i * 10,  # 40, 50, 60, 70, 80
                'memory_percent': 30.0 + i * 5,  # 30, 35, 40, 45, 50
                'memory_mb': 200.0 + i * 50,     # 200, 250, 300, 350, 400
                'timestamp': current_time - (4 - i)  # Recent timestamps
            }
            monitor.stats_history.append(stats)
            
        avg_stats = monitor.get_average_stats(window_seconds=10)
        
        assert avg_stats['cpu_percent'] == 60.0  # Average of 40,50,60,70,80
        assert avg_stats['memory_percent'] == 40.0  # Average of 30,35,40,45,50
        assert avg_stats['memory_mb'] == 300.0  # Average of 200,250,300,350,400
        assert avg_stats['sample_count'] == 5


class TestPerformanceOptimizer:
    """Test cases for PerformanceOptimizer class"""
    
    def setup_method(self):
        """Set up performance optimizer"""
        self.config = AppConfig()
        
    @pytest.mark.asyncio
    async def test_optimizer_initialization(self):
        """Test PerformanceOptimizer initialization"""
        optimizer = PerformanceOptimizer(self.config)
        
        assert optimizer.config == self.config
        assert optimizer.optimization_level == 0
        assert optimizer.optimization_cooldown == 5.0
        
    @pytest.mark.asyncio
    async def test_optimization_trigger_conditions(self):
        """Test conditions that trigger performance optimization"""
        optimizer = PerformanceOptimizer(self.config)
        
        # Normal performance - no optimization needed
        normal_resource_stats = {
            'cpu_percent': 50.0,
            'memory_percent': 60.0
        }
        normal_processing_stats = {
            'average_processing_time': 20.0,
            'frames_dropped': 0
        }
        
        optimized = await optimizer.optimize_if_needed(
            normal_resource_stats, 
            normal_processing_stats
        )
        
        assert optimized == False
        assert optimizer.optimization_level == 0
        
        # High resource usage - should trigger optimization
        high_resource_stats = {
            'cpu_percent': 85.0,  # Above 75% threshold
            'memory_percent': 85.0  # Above 80% threshold
        }
        high_processing_stats = {
            'average_processing_time': 60.0,  # Above 50ms threshold
            'frames_dropped': 15  # Above 10 frame threshold
        }
        
        optimized = await optimizer.optimize_if_needed(
            high_resource_stats,
            high_processing_stats
        )
        
        assert optimized == True
        assert optimizer.optimization_level == 1
        
    @pytest.mark.asyncio
    async def test_optimization_cooldown(self):
        """Test optimization cooldown period"""
        optimizer = PerformanceOptimizer(self.config)
        
        high_stats = {
            'cpu_percent': 85.0,
            'memory_percent': 85.0
        }
        processing_stats = {
            'average_processing_time': 60.0,
            'frames_dropped': 15
        }
        
        # First optimization should work
        optimized1 = await optimizer.optimize_if_needed(high_stats, processing_stats)
        assert optimized1 == True
        
        # Immediate second optimization should be blocked by cooldown
        optimized2 = await optimizer.optimize_if_needed(high_stats, processing_stats)
        assert optimized2 == False
        
    @pytest.mark.asyncio
    async def test_optimization_level_progression(self):
        """Test optimization level increases and decreases appropriately"""
        optimizer = PerformanceOptimizer(self.config)
        
        # Simulate increasing load
        high_stats = {'cpu_percent': 85.0, 'memory_percent': 85.0}
        high_processing = {'average_processing_time': 60.0, 'frames_dropped': 15}
        
        # First optimization
        optimizer.last_optimization_time = 0  # Reset cooldown
        await optimizer.optimize_if_needed(high_stats, high_processing)
        assert optimizer.optimization_level == 1
        
        # Second optimization (even higher load)
        optimizer.last_optimization_time = 0
        await optimizer.optimize_if_needed(high_stats, high_processing)
        assert optimizer.optimization_level == 2
        
        # Should not exceed level 2
        optimizer.last_optimization_time = 0
        await optimizer.optimize_if_needed(high_stats, high_processing)
        assert optimizer.optimization_level == 2
        
        # Reduce load - should decrease optimization
        low_stats = {'cpu_percent': 40.0, 'memory_percent': 50.0}
        low_processing = {'average_processing_time': 15.0, 'frames_dropped': 0}
        
        optimizer.last_optimization_time = 0
        await optimizer.optimize_if_needed(low_stats, low_processing)
        assert optimizer.optimization_level == 1
        
        optimizer.last_optimization_time = 0
        await optimizer.optimize_if_needed(low_stats, low_processing)
        assert optimizer.optimization_level == 0


class TestErrorHandling:
    """Test cases for error handling and edge cases"""
    
    def setup_method(self):
        """Set up test client"""
        self.client = TestClient(app)
        
    def test_health_endpoint_exception_handling(self):
        """Test health endpoint handles internal exceptions gracefully"""
        with patch('main.datetime') as mock_datetime:
            # Simulate datetime error
            mock_datetime.utcnow.side_effect = Exception("Time error")
            
            response = self.client.get("/")
            
            # Should still return a response (may be 500, but shouldn't crash)
            assert response.status_code in [200, 500]
            
    @pytest.mark.asyncio
    async def test_websocket_processing_exception_handling(self):
        """Test WebSocket processing handles exceptions gracefully"""
        config = AppConfig()
        service = VideoProcessingService("test_client", config)
        
        # Test with invalid frame data
        invalid_frame = {
            "type": "raw_frame",
            "frame_data": "invalid_base64_data",
            "metadata": {"frame_number": 1}
        }
        
        # Should handle gracefully without crashing
        try:
            await service.add_frame_to_queue(invalid_frame)
        except Exception as e:
            pytest.fail(f"Should handle invalid frame gracefully: {e}")
            
    def test_configuration_validation_errors(self):
        """Test configuration validation error handling"""
        from config import VideoConfig
        
        # Test invalid video configuration
        with pytest.raises(ValueError):
            VideoConfig(width=0)  # Invalid width
            
        with pytest.raises(ValueError):
            VideoConfig(fps=0)  # Invalid FPS
            
        with pytest.raises(ValueError):
            VideoConfig(format="INVALID")  # Invalid format


if __name__ == "__main__":
    pytest.main([__file__, "-v"])