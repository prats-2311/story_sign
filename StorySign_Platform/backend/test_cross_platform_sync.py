"""
Test cross-platform synchronization functionality
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from services.sync_service import SyncService, SyncStatus, ConflictResolution
from models.sync import DeviceSession, SyncOperation, SyncConflict, OfflineChange


class TestSyncService:
    """Test cases for SyncService"""
    
    @pytest.fixture
    async def sync_service(self):
        """Create a SyncService instance for testing"""
        service = SyncService()
        await service.initialize()
        return service
    
    @pytest.fixture
    def device_info(self):
        """Sample device information"""
        return {
            "platform": "web",
            "browser": "chrome",
            "version": "91.0",
            "user_agent": "Mozilla/5.0...",
            "screen_resolution": "1920x1080",
            "connection": {
                "effectiveType": "4g",
                "downlink": 10,
                "rtt": 50
            }
        }
    
    @pytest.fixture
    def session_data(self):
        """Sample session data"""
        return {
            "current_story": "story-123",
            "progress": {
                "sentences_completed": 3,
                "overall_score": 85.5
            },
            "preferences": {
                "difficulty": "medium",
                "feedback_level": "detailed"
            }
        }

    async def test_create_device_session(self, sync_service, device_info, session_data):
        """Test creating a device-agnostic session"""
        user_id = "user-123"
        
        session = await sync_service.create_device_session(
            user_id=user_id,
            device_info=device_info,
            session_data=session_data
        )
        
        assert session["user_id"] == user_id
        assert session["device_info"] == device_info
        assert session["session_data"] == session_data
        assert session["sync_version"] == 1
        assert session["is_active"] is True
        assert "session_id" in session
        assert "device_id" in session
        assert "bandwidth_profile" in session

    async def test_sync_session_data_no_conflicts(self, sync_service):
        """Test synchronizing session data without conflicts"""
        # Mock session data
        session_id = "session-123"
        sync_service._get_session_data = AsyncMock(return_value={
            "session_id": session_id,
            "user_id": "user-123",
            "session_data": {"current_story": "story-1"},
            "sync_version": 1,
            "last_sync": datetime.utcnow().isoformat()
        })
        
        sync_service._store_session_data = AsyncMock()
        sync_service._notify_other_devices = AsyncMock()
        
        data_updates = {"current_story": "story-2", "progress": {"score": 90}}
        client_version = 1
        
        result = await sync_service.sync_session_data(
            session_id=session_id,
            data_updates=data_updates,
            client_version=client_version
        )
        
        assert result["status"] == SyncStatus.COMPLETED.value
        assert result["sync_version"] == 2
        assert "merged_data" in result
        assert result["conflicts"] == []

    async def test_sync_session_data_with_conflicts(self, sync_service):
        """Test synchronizing session data with conflicts"""
        session_id = "session-123"
        
        # Mock session with conflicting data
        sync_service._get_session_data = AsyncMock(return_value={
            "session_id": session_id,
            "user_id": "user-123",
            "session_data": {"current_story": "story-1", "score": 80},
            "sync_version": 2,  # Higher than client version
            "last_sync": datetime.utcnow().isoformat()
        })
        
        sync_service._detect_conflicts = AsyncMock(return_value=[
            {
                "field": "current_story",
                "server_value": "story-1",
                "client_value": "story-2",
                "conflict_type": "value_conflict"
            }
        ])
        
        sync_service._handle_conflicts = AsyncMock(return_value={
            "status": SyncStatus.CONFLICT.value,
            "resolved_data": {"current_story": "story-2"},
            "conflicts": []
        })
        
        data_updates = {"current_story": "story-2"}
        client_version = 1  # Behind server version
        
        result = await sync_service.sync_session_data(
            session_id=session_id,
            data_updates=data_updates,
            client_version=client_version
        )
        
        assert result["status"] == SyncStatus.CONFLICT.value

    async def test_queue_sync_operation(self, sync_service):
        """Test queuing synchronization operations"""
        user_id = "user-123"
        operation_type = "practice_session"
        data = {"session_id": "session-123", "score": 85}
        priority = 1
        
        operation_id = await sync_service.queue_sync_operation(
            user_id=user_id,
            operation_type=operation_type,
            data=data,
            priority=priority
        )
        
        assert operation_id is not None
        assert user_id in sync_service.sync_queue
        assert len(sync_service.sync_queue[user_id]) == 1
        
        operation = sync_service.sync_queue[user_id][0]
        assert operation["operation_id"] == operation_id
        assert operation["operation_type"] == operation_type
        assert operation["data"] == data
        assert operation["priority"] == priority

    async def test_process_offline_changes(self, sync_service):
        """Test processing offline changes"""
        user_id = "user-123"
        offline_changes = [
            {
                "id": "change-1",
                "type": "practice_session",
                "data": {"session_id": "session-1", "score": 85},
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "id": "change-2",
                "type": "progress_update",
                "data": {"skill_level": 2.5},
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
        
        # Mock conflict checking
        sync_service._check_offline_conflicts = AsyncMock(return_value=[])
        sync_service._apply_offline_change = AsyncMock()
        
        result = await sync_service.process_offline_changes(
            user_id=user_id,
            offline_changes=offline_changes
        )
        
        assert result["processed"] == 2
        assert result["conflicts"] == 0
        assert result["failed"] == 0

    async def test_bandwidth_optimization(self, sync_service):
        """Test bandwidth optimization for different profiles"""
        # Test data with landmark information
        data = {
            "landmark_data": {
                "hand_landmarks": [0.123456789, 0.987654321, 0.555555555],
                "pose_landmarks": [0.111111111, 0.222222222, 0.333333333]
            },
            "performance_metrics": {
                "confidence_score": 0.85,
                "accuracy": 0.92,
                "detailed_analysis": "Very detailed analysis...",
                "frame_rate": 30,
                "processing_time": 150
            }
        }
        
        # Test low bandwidth optimization
        optimized_low = await sync_service.optimize_sync_data(data, "low")
        
        # Should have reduced precision landmarks
        assert "landmark_data" in optimized_low
        assert "performance_metrics" in optimized_low
        
        # Test high bandwidth (no optimization)
        optimized_high = await sync_service.optimize_sync_data(data, "high")
        assert optimized_high == data

    def test_device_id_generation(self, sync_service, device_info):
        """Test device ID generation consistency"""
        device_id_1 = sync_service._generate_device_id(device_info)
        device_id_2 = sync_service._generate_device_id(device_info)
        
        # Same device info should generate same ID
        assert device_id_1 == device_id_2
        assert len(device_id_1) == 16
        
        # Different device info should generate different ID
        different_device_info = device_info.copy()
        different_device_info["platform"] = "mobile"
        device_id_3 = sync_service._generate_device_id(different_device_info)
        
        assert device_id_1 != device_id_3

    def test_bandwidth_profile_detection(self, sync_service):
        """Test bandwidth profile detection"""
        # Mobile device
        mobile_info = {"platform": "android", "connection": {"effectiveType": "3g"}}
        profile = sync_service._detect_bandwidth_profile(mobile_info)
        assert profile == "low"
        
        # Desktop with good connection
        desktop_info = {"platform": "web", "connection": {"effectiveType": "4g"}}
        profile = sync_service._detect_bandwidth_profile(desktop_info)
        assert profile == "high"
        
        # Slow connection
        slow_info = {"platform": "web", "connection": {"effectiveType": "2g"}}
        profile = sync_service._detect_bandwidth_profile(slow_info)
        assert profile == "low"

    async def test_conflict_resolution_strategies(self, sync_service):
        """Test different conflict resolution strategies"""
        # Test latest wins strategy
        server_value = "old_value"
        client_value = "new_value"
        
        merged = await sync_service._merge_values(server_value, client_value)
        assert merged == client_value
        
        # Test object merge
        server_obj = {"a": 1, "b": 2}
        client_obj = {"b": 3, "c": 4}
        
        merged_obj = await sync_service._merge_values(server_obj, client_obj)
        assert merged_obj == {"a": 1, "b": 3, "c": 4}
        
        # Test array merge
        server_array = [1, 2, 3]
        client_array = [3, 4, 5]
        
        merged_array = await sync_service._merge_values(server_array, client_array)
        assert set(merged_array) == {1, 2, 3, 4, 5}

    def test_checksum_calculation(self, sync_service):
        """Test data checksum calculation"""
        data1 = {"key": "value", "number": 123}
        data2 = {"key": "value", "number": 123}
        data3 = {"key": "different", "number": 123}
        
        checksum1 = sync_service._calculate_checksum(data1)
        checksum2 = sync_service._calculate_checksum(data2)
        checksum3 = sync_service._calculate_checksum(data3)
        
        # Same data should have same checksum
        assert checksum1 == checksum2
        
        # Different data should have different checksum
        assert checksum1 != checksum3

    async def test_landmark_precision_reduction(self, sync_service):
        """Test landmark precision reduction for bandwidth optimization"""
        landmark_data = {
            "x": 0.123456789,
            "y": 0.987654321,
            "z": 0.555555555,
            "landmarks": [0.111111111, 0.222222222, 0.333333333]
        }
        
        reduced = sync_service._reduce_landmark_precision(landmark_data)
        
        assert reduced["x"] == 0.123
        assert reduced["y"] == 0.988
        assert reduced["z"] == 0.556
        assert reduced["landmarks"] == [0.111, 0.222, 0.333]

    async def test_essential_metrics_filtering(self, sync_service):
        """Test filtering to essential metrics only"""
        metrics = {
            "confidence_score": 0.85,
            "overall_score": 90,
            "completion_time": 300,
            "accuracy": 0.92,
            "attempts_count": 3,
            "detailed_analysis": "Very long analysis...",
            "debug_info": {"frames": 1000, "processing_times": [1, 2, 3]},
            "extra_data": "not essential"
        }
        
        essential = sync_service._filter_essential_metrics(metrics)
        
        expected_keys = {
            "confidence_score", "overall_score", "completion_time", 
            "accuracy", "attempts_count"
        }
        
        assert set(essential.keys()) == expected_keys
        assert "detailed_analysis" not in essential
        assert "debug_info" not in essential

    def test_conflict_type_determination(self, sync_service):
        """Test conflict type determination"""
        # Value conflict
        conflict_type = sync_service._determine_conflict_type("value1", "value2")
        assert conflict_type == "value_conflict"
        
        # Object merge
        conflict_type = sync_service._determine_conflict_type({"a": 1}, {"b": 2})
        assert conflict_type == "object_merge"
        
        # Array merge
        conflict_type = sync_service._determine_conflict_type([1, 2], [3, 4])
        assert conflict_type == "array_merge"

    def test_resolution_strategy_selection(self, sync_service):
        """Test resolution strategy selection based on conflict type"""
        # Object merge should use MERGE strategy
        strategy = sync_service._get_resolution_strategy("object_merge")
        assert strategy == ConflictResolution.MERGE
        
        # Array merge should use MERGE strategy
        strategy = sync_service._get_resolution_strategy("array_merge")
        assert strategy == ConflictResolution.MERGE
        
        # Value conflict should use LATEST_WINS strategy
        strategy = sync_service._get_resolution_strategy("value_conflict")
        assert strategy == ConflictResolution.LATEST_WINS
        
        # Unknown type should require user choice
        strategy = sync_service._get_resolution_strategy("unknown_type")
        assert strategy == ConflictResolution.USER_CHOICE


class TestSyncIntegration:
    """Integration tests for synchronization functionality"""
    
    @pytest.fixture
    async def sync_service_with_mocks(self):
        """Create sync service with mocked dependencies"""
        service = SyncService()
        
        # Mock database service
        mock_db = AsyncMock()
        service._get_database_service = AsyncMock(return_value=mock_db)
        
        # Mock Redis client
        mock_redis = AsyncMock()
        service._get_redis_client = AsyncMock(return_value=mock_redis)
        
        await service.initialize()
        return service, mock_db, mock_redis

    async def test_end_to_end_sync_workflow(self, sync_service_with_mocks):
        """Test complete synchronization workflow"""
        sync_service, mock_db, mock_redis = sync_service_with_mocks
        
        # 1. Create device session
        user_id = "user-123"
        device_info = {
            "platform": "web",
            "browser": "chrome",
            "connection": {"effectiveType": "4g"}
        }
        
        session = await sync_service.create_device_session(
            user_id=user_id,
            device_info=device_info
        )
        
        assert session["user_id"] == user_id
        session_id = session["session_id"]
        
        # 2. Queue some operations
        op1_id = await sync_service.queue_sync_operation(
            user_id=user_id,
            operation_type="practice_session",
            data={"session_id": session_id, "score": 85},
            priority=1
        )
        
        op2_id = await sync_service.queue_sync_operation(
            user_id=user_id,
            operation_type="progress_update",
            data={"skill_level": 2.0},
            priority=2
        )
        
        assert op1_id != op2_id
        assert len(sync_service.sync_queue[user_id]) == 2
        
        # Higher priority operation should be first
        assert sync_service.sync_queue[user_id][0]["priority"] == 1
        assert sync_service.sync_queue[user_id][1]["priority"] == 2
        
        # 3. Test offline changes
        offline_changes = [
            {
                "id": "offline-1",
                "type": "practice_session",
                "data": {"session_id": session_id, "offline_score": 90},
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
        
        # Mock offline processing
        sync_service._check_offline_conflicts = AsyncMock(return_value=[])
        sync_service._apply_offline_change = AsyncMock()
        
        result = await sync_service.process_offline_changes(
            user_id=user_id,
            offline_changes=offline_changes
        )
        
        assert result["processed"] == 1
        assert result["conflicts"] == 0

    async def test_multi_device_sync_scenario(self, sync_service_with_mocks):
        """Test synchronization across multiple devices"""
        sync_service, mock_db, mock_redis = sync_service_with_mocks
        
        user_id = "user-123"
        
        # Create sessions for different devices
        web_session = await sync_service.create_device_session(
            user_id=user_id,
            device_info={"platform": "web", "browser": "chrome"}
        )
        
        mobile_session = await sync_service.create_device_session(
            user_id=user_id,
            device_info={"platform": "android", "connection": {"effectiveType": "3g"}}
        )
        
        # Different devices should have different IDs
        assert web_session["device_id"] != mobile_session["device_id"]
        
        # Both should have same user ID
        assert web_session["user_id"] == mobile_session["user_id"] == user_id
        
        # Mobile should have lower bandwidth profile
        assert mobile_session["bandwidth_profile"] == "low"
        assert web_session["bandwidth_profile"] == "high"

    async def test_conflict_resolution_workflow(self, sync_service_with_mocks):
        """Test conflict detection and resolution workflow"""
        sync_service, mock_db, mock_redis = sync_service_with_mocks
        
        # Mock session with existing data
        session_data = {
            "session_id": "session-123",
            "user_id": "user-123",
            "session_data": {
                "current_story": "story-1",
                "progress": {"score": 80, "completed": 2}
            },
            "sync_version": 2
        }
        
        sync_service._get_session_data = AsyncMock(return_value=session_data)
        
        # Client updates with conflicts
        client_updates = {
            "current_story": "story-2",  # Conflict: different story
            "progress": {"score": 85, "completed": 3}  # Conflict: different progress
        }
        
        # Test conflict detection
        conflicts = await sync_service._detect_conflicts(session_data, client_updates)
        
        assert len(conflicts) == 2
        assert any(c["field"] == "current_story" for c in conflicts)
        assert any(c["field"] == "progress" for c in conflicts)
        
        # Test conflict resolution
        resolution = await sync_service._handle_conflicts(
            "session-123", conflicts, client_updates
        )
        
        # Should resolve conflicts automatically
        assert "resolved_data" in resolution


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])