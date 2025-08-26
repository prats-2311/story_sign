#!/usr/bin/env python3
"""
Test WebSocket dependencies directly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import logging
from api import websocket

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_websocket_dependencies():
    """Test if WebSocket dependencies are set"""
    
    try:
        logger.info("Testing WebSocket dependencies...")
        
        # Check if connection_manager is set
        conn_mgr = websocket.connection_manager
        logger.info(f"Connection manager: {conn_mgr}")
        
        # Check if VideoProcessingService is set
        video_service_class = websocket.VideoProcessingService
        logger.info(f"VideoProcessingService: {video_service_class}")
        
        if conn_mgr is None:
            logger.error("❌ connection_manager is None")
        else:
            logger.info("✅ connection_manager is set")
            
        if video_service_class is None:
            logger.error("❌ VideoProcessingService is None")
        else:
            logger.info("✅ VideoProcessingService is set")
            
    except Exception as e:
        logger.error(f"❌ Error testing WebSocket dependencies: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_websocket_dependencies()