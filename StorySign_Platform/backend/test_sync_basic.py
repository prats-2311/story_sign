"""
Basic test for synchronization functionality
"""

import asyncio
import json
from datetime import datetime
from services.sync_service import SyncService


async def test_basic_sync_functionality():
    """Test basic synchronization functionality"""
    print("🧪 Testing basic synchronization functionality...")
    
    # Create sync service
    sync_service = SyncService()
    await sync_service.initialize()
    
    # Test device info
    device_info = {
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
    
    # Test device ID generation
    device_id_1 = sync_service._generate_device_id(device_info)
    device_id_2 = sync_service._generate_device_id(device_info)
    
    assert device_id_1 == device_id_2, "Device ID should be consistent"
    assert len(device_id_1) == 16, "Device ID should be 16 characters"
    print(f"✅ Device ID generation: {device_id_1}")
    
    # Test bandwidth profile detection
    profile = sync_service._detect_bandwidth_profile(device_info)
    assert profile in ["low", "medium", "high"], "Invalid bandwidth profile"
    print(f"✅ Bandwidth profile detection: {profile}")
    
    # Test checksum calculation
    data = {"key": "value", "number": 123}
    checksum = sync_service._calculate_checksum(data)
    assert isinstance(checksum, str), "Checksum should be a string"
    print(f"✅ Checksum calculation: {checksum}")
    
    # Test conflict type determination
    conflict_type = sync_service._determine_conflict_type("value1", "value2")
    assert conflict_type == "value_conflict", "Should detect value conflict"
    print(f"✅ Conflict type determination: {conflict_type}")
    
    # Test landmark precision reduction
    landmark_data = {
        "x": 0.123456789,
        "y": 0.987654321,
        "landmarks": [0.111111111, 0.222222222]
    }
    
    reduced = sync_service._reduce_landmark_precision(landmark_data)
    assert reduced["x"] == 0.123, "Should reduce precision to 3 decimal places"
    assert reduced["y"] == 0.988, "Should round correctly"
    print(f"✅ Landmark precision reduction: {reduced}")
    
    # Test essential metrics filtering
    metrics = {
        "confidence_score": 0.85,
        "overall_score": 90,
        "detailed_analysis": "Very long analysis...",
        "debug_info": {"frames": 1000}
    }
    
    essential = sync_service._filter_essential_metrics(metrics)
    assert "confidence_score" in essential, "Should keep essential metrics"
    assert "detailed_analysis" not in essential, "Should filter non-essential metrics"
    print(f"✅ Essential metrics filtering: {list(essential.keys())}")
    
    # Test value merging
    server_obj = {"a": 1, "b": 2}
    client_obj = {"b": 3, "c": 4}
    merged = await sync_service._merge_values(server_obj, client_obj)
    expected = {"a": 1, "b": 3, "c": 4}
    assert merged == expected, f"Object merge failed: {merged} != {expected}"
    print(f"✅ Value merging: {merged}")
    
    # Test queue operation
    user_id = "test-user-123"
    operation_id = await sync_service.queue_sync_operation(
        user_id=user_id,
        operation_type="practice_session",
        data={"session_id": "session-123", "score": 85},
        priority=1
    )
    
    assert operation_id is not None, "Should return operation ID"
    assert user_id in sync_service.sync_queue, "Should create queue for user"
    assert len(sync_service.sync_queue[user_id]) == 1, "Should have one operation"
    print(f"✅ Queue operation: {operation_id}")
    
    # Test bandwidth optimization
    test_data = {
        "landmark_data": {"x": 0.123456789, "y": 0.987654321},
        "performance_metrics": {
            "confidence_score": 0.85,
            "detailed_analysis": "Long analysis..."
        }
    }
    
    optimized_low = await sync_service.optimize_sync_data(test_data, "low")
    optimized_high = await sync_service.optimize_sync_data(test_data, "high")
    
    assert optimized_high == test_data, "High bandwidth should not optimize"
    print(f"✅ Bandwidth optimization: low={len(str(optimized_low))}, high={len(str(optimized_high))}")
    
    await sync_service.cleanup()
    print("🎉 All basic synchronization tests passed!")


async def test_device_session_creation():
    """Test device session creation"""
    print("🧪 Testing device session creation...")
    
    sync_service = SyncService()
    await sync_service.initialize()
    
    user_id = "test-user-456"
    device_info = {
        "platform": "mobile",
        "connection": {"effectiveType": "3g"}
    }
    session_data = {"current_story": "story-1"}
    
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
    assert session["bandwidth_profile"] == "low"  # Mobile should be low bandwidth
    
    print(f"✅ Device session created: {session['session_id']}")
    print(f"   - Device ID: {session['device_id']}")
    print(f"   - Bandwidth: {session['bandwidth_profile']}")
    
    await sync_service.cleanup()
    print("🎉 Device session creation test passed!")


async def test_offline_changes():
    """Test offline changes processing"""
    print("🧪 Testing offline changes processing...")
    
    sync_service = SyncService()
    await sync_service.initialize()
    
    # Mock the conflict checking and change application
    sync_service._check_offline_conflicts = lambda user_id, change: []
    sync_service._apply_offline_change = lambda user_id, change: None
    
    user_id = "test-user-789"
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
    
    result = await sync_service.process_offline_changes(
        user_id=user_id,
        offline_changes=offline_changes
    )
    
    assert result["processed"] == 2, "Should process all changes"
    assert result["conflicts"] == 0, "Should have no conflicts"
    assert result["failed"] == 0, "Should have no failures"
    
    print(f"✅ Offline changes processed: {result}")
    
    await sync_service.cleanup()
    print("🎉 Offline changes test passed!")


if __name__ == "__main__":
    async def run_all_tests():
        await test_basic_sync_functionality()
        print()
        await test_device_session_creation()
        print()
        await test_offline_changes()
        print("\n🎉 All synchronization tests completed successfully!")
    
    asyncio.run(run_all_tests())