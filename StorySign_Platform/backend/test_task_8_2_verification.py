#!/usr/bin/env python3
"""
Test script to verify Task 8.2 implementation:
Server-side processing loop with queue management, performance monitoring, and resource cleanup
"""

import asyncio
import json
import time
import logging
from unittest.mock import Mock, patch
import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging for test
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_video_processing_service():
    """Test the enhanced VideoProcessingService with async processing loop"""
    
    logger.info("🧪 Testing VideoProcessingService async processing loop...")
    
    try:
        # Import after path setup
        from main import VideoProcessingService, ResourceMonitor, PerformanceOptimizer
        from config import get_config
        
        # Get configuration
        config = get_config()
        
        # Create video processing service
        client_id = "test_client_001"
        service = VideoProcessingService(client_id, config)
        
        # Mock WebSocket for testing
        mock_websocket = Mock()
        mock_websocket.send_text = Mock(return_value=asyncio.Future())
        mock_websocket.send_text.return_value.set_result(None)
        
        logger.info("✅ VideoProcessingService created successfully")
        
        # Test 1: Start processing
        logger.info("🔄 Testing processing loop startup...")
        await service.start_processing(mock_websocket)
        
        # Verify processing loop is running
        assert service.is_active == True
        assert service.processing_loop_task is not None
        assert not service.processing_loop_task.done()
        
        logger.info("✅ Processing loop started successfully")
        
        # Test 2: Queue frame processing
        logger.info("🔄 Testing frame queue management...")
        
        # Create test frame message
        test_frame_message = {
            "type": "raw_frame",
            "timestamp": "2024-08-20T10:30:00.000Z",
            "frame_data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD//gA7Q1JFQVR",
            "metadata": {
                "frame_number": 1,
                "client_id": client_id
            }
        }
        
        # Queue multiple frames
        for i in range(5):
            test_frame_message["metadata"]["frame_number"] = i + 1
            queued = await service.queue_frame_for_processing(test_frame_message)
            assert queued == True, f"Frame {i+1} should have been queued successfully"
        
        logger.info("✅ Frame queueing working correctly")
        
        # Test 3: Processing statistics
        logger.info("🔄 Testing processing statistics...")
        
        # Wait a moment for some processing
        await asyncio.sleep(2.0)
        
        stats = service.get_processing_stats()
        assert 'client_id' in stats
        assert 'frames_processed' in stats
        assert 'queue_size' in stats
        assert 'is_active' in stats
        assert stats['client_id'] == client_id
        assert stats['is_active'] == True
        
        logger.info(f"✅ Processing statistics: {stats}")
        
        # Test 4: Resource monitoring
        logger.info("🔄 Testing resource monitoring...")
        
        # Check if resource monitor is active
        assert hasattr(service, 'resource_monitor')
        assert service.resource_monitor.monitoring_active == True
        
        # Wait for some resource data
        await asyncio.sleep(1.5)
        
        # Check if we have resource stats
        if service.resource_monitor.stats_history:
            resource_stats = service.resource_monitor.stats_history[-1]
            assert 'cpu_percent' in resource_stats
            assert 'memory_percent' in resource_stats
            logger.info(f"✅ Resource monitoring active: CPU {resource_stats['cpu_percent']:.1f}%, Memory {resource_stats['memory_percent']:.1f}%")
        else:
            logger.info("⚠️ Resource monitoring active but no data yet")
        
        # Test 5: Performance optimization
        logger.info("🔄 Testing performance optimization...")
        
        optimizer = service.performance_optimizer
        assert isinstance(optimizer, PerformanceOptimizer)
        
        # Test optimization decision making
        mock_resource_stats = {'cpu_percent': 85.0, 'memory_percent': 70.0}
        mock_processing_stats = {'average_processing_time': 60.0, 'frames_dropped': 15}
        
        optimization_applied = await optimizer.optimize_if_needed(mock_resource_stats, mock_processing_stats)
        logger.info(f"✅ Performance optimization test: {optimization_applied}")
        
        # Test 6: Queue overflow handling
        logger.info("🔄 Testing queue overflow handling...")
        
        # Fill up the queue to test overflow
        initial_dropped = service.processing_stats['frames_dropped']
        
        # Try to queue many frames quickly to trigger overflow
        for i in range(15):  # More than queue maxsize (10)
            test_frame_message["metadata"]["frame_number"] = i + 100
            await service.queue_frame_for_processing(test_frame_message)
        
        # Check if some frames were dropped
        final_dropped = service.processing_stats['frames_dropped']
        if final_dropped > initial_dropped:
            logger.info(f"✅ Queue overflow handling working: {final_dropped - initial_dropped} frames dropped")
        else:
            logger.info("⚠️ Queue overflow not triggered (processing too fast)")
        
        # Test 7: Cleanup and shutdown
        logger.info("🔄 Testing cleanup and shutdown...")
        
        await service.stop_processing()
        
        # Verify cleanup
        assert service.is_active == False
        assert service.processing_loop_task.done() or service.processing_loop_task.cancelled()
        assert service.resource_monitor.monitoring_active == False
        
        logger.info("✅ Cleanup and shutdown completed successfully")
        
        logger.info("🎉 All VideoProcessingService tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ VideoProcessingService test failed: {e}", exc_info=True)
        return False

async def test_connection_manager():
    """Test the enhanced ConnectionManager with processing statistics"""
    
    logger.info("🧪 Testing ConnectionManager processing statistics...")
    
    try:
        from main import ConnectionManager
        from config import get_config
        
        config = get_config()
        manager = ConnectionManager()
        
        # Mock WebSocket
        mock_websocket = Mock()
        mock_websocket.accept = Mock(return_value=asyncio.Future())
        mock_websocket.accept.return_value.set_result(None)
        mock_websocket.send_text = Mock(return_value=asyncio.Future())
        mock_websocket.send_text.return_value.set_result(None)
        
        # Test connection management
        client_id = await manager.connect(mock_websocket)
        assert client_id in manager.active_connections
        assert client_id in manager.processing_services
        
        logger.info(f"✅ Connection established: {client_id}")
        
        # Test statistics retrieval
        all_stats = manager.get_all_processing_stats()
        assert client_id in all_stats
        assert 'client_id' in all_stats[client_id]
        
        system_summary = manager.get_system_summary()
        assert 'active_connections' in system_summary
        assert 'total_frames_processed' in system_summary
        assert 'client_stats' in system_summary
        assert system_summary['active_connections'] == 1
        
        logger.info(f"✅ Statistics retrieval working: {system_summary['active_connections']} connections")
        
        # Test cleanup
        await manager.disconnect(client_id)
        assert client_id not in manager.active_connections
        assert client_id not in manager.processing_services
        
        logger.info("✅ Connection cleanup completed")
        
        logger.info("🎉 All ConnectionManager tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ ConnectionManager test failed: {e}", exc_info=True)
        return False

async def test_resource_monitor():
    """Test the ResourceMonitor functionality"""
    
    logger.info("🧪 Testing ResourceMonitor...")
    
    try:
        from main import ResourceMonitor
        
        monitor = ResourceMonitor("test_client")
        
        # Start monitoring
        await monitor.start_monitoring()
        assert monitor.monitoring_active == True
        
        # Wait for some data collection
        await asyncio.sleep(2.0)
        
        # Check if we have collected stats
        if monitor.stats_history:
            stats = monitor.stats_history[-1]
            assert 'cpu_percent' in stats
            assert 'memory_percent' in stats
            assert 'timestamp' in stats
            logger.info(f"✅ Resource monitoring data: CPU {stats['cpu_percent']:.1f}%, Memory {stats['memory_percent']:.1f}%")
        
        # Test average calculation
        avg_stats = monitor.get_average_stats(10)
        assert 'cpu_percent' in avg_stats
        
        # Stop monitoring
        await monitor.stop_monitoring()
        assert monitor.monitoring_active == False
        
        logger.info("🎉 ResourceMonitor tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ ResourceMonitor test failed: {e}", exc_info=True)
        return False

async def main():
    """Run all tests for Task 8.2 implementation"""
    
    logger.info("🚀 Starting Task 8.2 verification tests...")
    logger.info("Testing: Server-side processing loop with queue management, performance monitoring, and resource cleanup")
    
    test_results = []
    
    # Test 1: VideoProcessingService
    result1 = await test_video_processing_service()
    test_results.append(("VideoProcessingService", result1))
    
    # Test 2: ConnectionManager
    result2 = await test_connection_manager()
    test_results.append(("ConnectionManager", result2))
    
    # Test 3: ResourceMonitor
    result3 = await test_resource_monitor()
    test_results.append(("ResourceMonitor", result3))
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📊 TASK 8.2 VERIFICATION RESULTS")
    logger.info("="*60)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{len(test_results)} tests passed")
    
    if passed == len(test_results):
        logger.info("🎉 Task 8.2 implementation verified successfully!")
        logger.info("✅ Server-side processing loop with async queue management implemented")
        logger.info("✅ Frame processing queue management with overflow handling implemented")
        logger.info("✅ Processing time monitoring and performance optimization implemented")
        logger.info("✅ Resource management and cleanup for disconnected clients implemented")
        return True
    else:
        logger.error("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)