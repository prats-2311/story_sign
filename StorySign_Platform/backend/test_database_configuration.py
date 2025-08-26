#!/usr/bin/env python3
"""
Test database configuration and connectivity
Tests TiDB connection, pooling, and basic operations
"""

import asyncio
import pytest
import logging
from typing import Dict, Any

from config import DatabaseConfig, get_config
from core.db import DatabaseManager, get_database_manager, cleanup_database_manager
from core.database_service import DatabaseService

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestDatabaseConfiguration:
    """Test database configuration and validation"""
    
    def test_database_config_defaults(self):
        """Test database configuration with default values"""
        config = DatabaseConfig()
        
        assert config.host == "localhost"
        assert config.port == 4000
        assert config.database == "storysign"
        assert config.username == "root"
        assert config.password == ""
        assert config.pool_size == 10
        assert config.max_overflow == 20
        assert config.ssl_disabled is True
        
    def test_database_config_validation(self):
        """Test database configuration validation"""
        # Test valid configuration
        config = DatabaseConfig(
            host="tidb.example.com",
            port=4000,
            database="test_db",
            username="test_user",
            password="test_pass"
        )
        
        assert config.host == "tidb.example.com"
        assert config.database == "test_db"
        assert config.username == "test_user"
        
        # Test invalid configurations
        with pytest.raises(ValueError):
            DatabaseConfig(host="")  # Empty host
            
        with pytest.raises(ValueError):
            DatabaseConfig(database="")  # Empty database name
            
        with pytest.raises(ValueError):
            DatabaseConfig(username="")  # Empty username
    
    def test_connection_url_generation(self):
        """Test database connection URL generation"""
        config = DatabaseConfig(
            host="localhost",
            port=4000,
            database="storysign",
            username="root",
            password="secret123"
        )
        
        # Test async URL
        async_url = config.get_connection_url(async_driver=True)
        assert "mysql+asyncmy://root:secret123@localhost:4000/storysign" in async_url
        assert "ssl_disabled=true" in async_url
        
        # Test sync URL
        sync_url = config.get_connection_url(async_driver=False)
        assert "mysql+pymysql://root:secret123@localhost:4000/storysign" in sync_url
        
        # Test URL without password
        config_no_pass = DatabaseConfig(
            host="localhost",
            port=4000,
            database="storysign",
            username="root",
            password=""
        )
        
        url_no_pass = config_no_pass.get_connection_url()
        assert "mysql+asyncmy://root@localhost:4000/storysign" in url_no_pass
    
    def test_ssl_configuration(self):
        """Test SSL configuration in connection URL"""
        config = DatabaseConfig(
            host="secure.tidb.com",
            ssl_disabled=False,
            ssl_ca="/path/to/ca.pem",
            ssl_cert="/path/to/cert.pem",
            ssl_key="/path/to/key.pem"
        )
        
        url = config.get_connection_url()
        assert "ssl_ca=/path/to/ca.pem" in url
        assert "ssl_cert=/path/to/cert.pem" in url
        assert "ssl_key=/path/to/key.pem" in url
        assert "ssl_disabled=true" not in url


class TestDatabaseManager:
    """Test database manager functionality"""
    
    @pytest.fixture
    def db_config(self):
        """Provide test database configuration"""
        return DatabaseConfig(
            host="localhost",
            port=4000,
            database="storysign_test",
            username="root",
            password="",
            pool_size=5,
            max_overflow=10,
            health_check_interval=60  # Longer interval for tests
        )
    
    async def test_database_manager_initialization(self, db_config):
        """Test database manager initialization"""
        db_manager = DatabaseManager(db_config)
        
        assert not db_manager.is_connected
        assert db_manager.config == db_config
        
        # Note: We can't test actual connection without a running TiDB instance
        # This test verifies the manager can be created with proper configuration
        
    async def test_database_manager_connection_info(self, db_config):
        """Test database manager connection info"""
        db_manager = DatabaseManager(db_config)
        
        info = db_manager.get_connection_info()
        
        assert info["is_connected"] is False
        assert info["host"] == "localhost"
        assert info["port"] == 4000
        assert info["database"] == "storysign_test"
        assert info["username"] == "root"
        assert info["pool_size"] == 5
        assert info["max_overflow"] == 10
    
    async def test_database_manager_health_check_disconnected(self, db_config):
        """Test health check when disconnected"""
        db_manager = DatabaseManager(db_config)
        
        health = await db_manager.health_check()
        
        assert health["status"] == "disconnected"
        assert "error" in health


class TestDatabaseService:
    """Test database service integration"""
    
    @pytest.fixture
    def service_config(self):
        """Provide test service configuration"""
        return {
            "database": {
                "host": "localhost",
                "port": 4000,
                "database": "storysign_test",
                "username": "root",
                "password": "",
                "pool_size": 5
            }
        }
    
    async def test_database_service_initialization(self, service_config):
        """Test database service initialization"""
        service = DatabaseService(config=service_config)
        
        assert not service.is_connected()
        
        # Note: We can't test actual initialization without a running TiDB instance
        # This test verifies the service can be created with proper configuration
    
    async def test_database_service_connection_info(self, service_config):
        """Test database service connection info"""
        service = DatabaseService(config=service_config)
        
        info = service.get_connection_info()
        
        assert info["is_connected"] is False
        assert "error" in info


class TestDatabaseIntegration:
    """Integration tests for database functionality"""
    
    async def test_global_config_integration(self):
        """Test integration with global configuration"""
        try:
            # Get global configuration
            app_config = get_config()
            
            # Verify database configuration is present
            assert hasattr(app_config, 'database')
            assert isinstance(app_config.database, DatabaseConfig)
            
            # Test configuration values
            db_config = app_config.database
            assert db_config.host is not None
            assert db_config.port > 0
            assert db_config.database is not None
            assert db_config.username is not None
            
            logger.info(f"Database config: {db_config.host}:{db_config.port}/{db_config.database}")
            
        except Exception as e:
            logger.error(f"Global config integration test failed: {e}")
            raise
    
    async def test_service_container_integration(self):
        """Test integration with service container"""
        try:
            from core.service_container import ServiceContainer
            
            # Create service container
            container = ServiceContainer()
            
            # Register database service
            db_service = DatabaseService()
            container.register_service("database", db_service)
            
            # Verify service is registered
            assert container.has_service("database")
            retrieved_service = container.get_service("database")
            assert isinstance(retrieved_service, DatabaseService)
            
            logger.info("Service container integration successful")
            
        except Exception as e:
            logger.error(f"Service container integration test failed: {e}")
            raise


async def test_database_configuration_comprehensive():
    """Comprehensive test of database configuration and setup"""
    logger.info("Starting comprehensive database configuration test...")
    
    try:
        # Test 1: Configuration validation
        logger.info("Testing configuration validation...")
        config = DatabaseConfig(
            host="localhost",
            port=4000,
            database="storysign_test",
            username="root",
            password="test123",
            pool_size=5,
            max_overflow=10
        )
        
        assert config.host == "localhost"
        assert config.port == 4000
        assert config.pool_size == 5
        logger.info("✓ Configuration validation passed")
        
        # Test 2: Connection URL generation
        logger.info("Testing connection URL generation...")
        url = config.get_connection_url()
        assert "mysql+asyncmy" in url
        assert "localhost:4000" in url
        assert "storysign_test" in url
        logger.info("✓ Connection URL generation passed")
        
        # Test 3: Database manager creation
        logger.info("Testing database manager creation...")
        db_manager = DatabaseManager(config)
        assert not db_manager.is_connected
        assert db_manager.config == config
        logger.info("✓ Database manager creation passed")
        
        # Test 4: Database service creation
        logger.info("Testing database service creation...")
        service_config = {"database": config.model_dump()}
        db_service = DatabaseService(config=service_config)
        assert not db_service.is_connected()
        logger.info("✓ Database service creation passed")
        
        # Test 5: Global configuration integration
        logger.info("Testing global configuration integration...")
        app_config = get_config()
        assert hasattr(app_config, 'database')
        assert isinstance(app_config.database, DatabaseConfig)
        logger.info("✓ Global configuration integration passed")
        
        logger.info("All database configuration tests passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database configuration test failed: {e}")
        return False


async def test_database_mock_operations():
    """Test database operations with mock/placeholder functionality"""
    logger.info("Testing database operations (mock mode)...")
    
    try:
        # Create database service with test configuration
        config = {
            "database": {
                "host": "localhost",
                "port": 4000,
                "database": "storysign_test",
                "username": "root",
                "password": "",
                "pool_size": 3
            }
        }
        
        db_service = DatabaseService(config=config)
        
        # Test connection info
        info = db_service.get_connection_info()
        assert "is_connected" in info
        assert info["is_connected"] is False
        logger.info("✓ Connection info test passed")
        
        # Test health check
        health = await db_service.health_check()
        assert "status" in health
        logger.info("✓ Health check test passed")
        
        logger.info("Database operations test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database operations test failed: {e}")
        return False


if __name__ == "__main__":
    """Run database configuration tests"""
    async def main():
        logger.info("Running database configuration tests...")
        
        # Run comprehensive configuration test
        config_result = await test_database_configuration_comprehensive()
        
        # Run mock operations test
        operations_result = await test_database_mock_operations()
        
        # Cleanup
        await cleanup_database_manager()
        
        if config_result and operations_result:
            logger.info("🎉 All database tests passed!")
            return 0
        else:
            logger.error("❌ Some database tests failed!")
            return 1
    
    import sys
    sys.exit(asyncio.run(main()))