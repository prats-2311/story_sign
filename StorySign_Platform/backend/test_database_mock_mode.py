#!/usr/bin/env python3
"""
Test database service in mock mode (without SQLAlchemy)
"""

import asyncio
import logging
from core.database_service import DatabaseService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_database_mock_mode():
    """Test database service functionality in mock mode"""
    logger.info("Testing database service in mock mode...")
    
    try:
        # Create database service
        db_service = DatabaseService()
        
        # Test initialization
        await db_service.initialize()
        logger.info("✓ Database service initialized in mock mode")
        
        # Test connection status
        is_connected = db_service.is_connected()
        logger.info(f"✓ Connection status: {is_connected}")
        
        # Test health check
        health = await db_service.health_check()
        logger.info(f"✓ Health check: {health}")
        
        # Test connection info
        info = db_service.get_connection_info()
        logger.info(f"✓ Connection info: {info}")
        
        # Test session (mock)
        async with db_service.get_session() as session:
            logger.info(f"✓ Mock session: {session}")
        
        # Test query execution (mock)
        result = await db_service.execute_query("SELECT 1", {"param": "value"})
        logger.info(f"✓ Mock query result: {result}")
        
        # Test cleanup
        await db_service.cleanup()
        logger.info("✓ Database service cleaned up")
        
        logger.info("🎉 All database mock mode tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database mock mode test failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_database_mock_mode())
    exit(0 if success else 1)