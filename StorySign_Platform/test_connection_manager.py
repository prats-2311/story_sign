#!/usr/bin/env python3
"""
Test connection manager directly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import asyncio
import logging
from main import ConnectionManager, VideoProcessingService
from config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_connection_manager():
    """Test connection manager initialization"""
    
    try:
        logger.info("Testing connection manager initialization...")
        
        # Create connection manager
        conn_mgr = ConnectionManager()
        logger.info(f"✅ Connection manager created: {conn_mgr}")
        
        # Test basic methods
        count = conn_mgr.get_connection_count()
        logger.info(f"✅ Connection count: {count}")
        
        # Test config loading
        config = get_config()
        logger.info(f"✅ Config loaded: {config.server.host}:{config.server.port}")
        
        # Test VideoProcessingService creation
        video_service = VideoProcessingService("test_client", config)
        logger.info(f"✅ VideoProcessingService created: {video_service}")
        
        logger.info("✅ All components initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Error testing components: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_connection_manager())