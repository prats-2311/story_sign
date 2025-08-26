#!/usr/bin/env python3
"""
Simple test for database configuration without SQLAlchemy dependencies
Tests configuration validation and URL generation
"""

import sys
import os
import logging

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DatabaseConfig, get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_database_config_creation():
    """Test database configuration creation and validation"""
    logger.info("Testing database configuration creation...")
    
    try:
        # Test with default values
        config = DatabaseConfig()
        
        assert config.host == "localhost"
        assert config.port == 4000
        assert config.database == "storysign"
        assert config.username == "root"
        assert config.password == ""
        assert config.pool_size == 10
        assert config.max_overflow == 20
        assert config.ssl_disabled is True
        
        logger.info("✓ Default configuration test passed")
        
        # Test with custom values
        custom_config = DatabaseConfig(
            host="tidb.example.com",
            port=4000,
            database="test_db",
            username="test_user",
            password="test_pass",
            pool_size=5,
            max_overflow=15,
            ssl_disabled=False
        )
        
        assert custom_config.host == "tidb.example.com"
        assert custom_config.database == "test_db"
        assert custom_config.username == "test_user"
        assert custom_config.pool_size == 5
        assert custom_config.ssl_disabled is False
        
        logger.info("✓ Custom configuration test passed")
        
        return True
        
    except Exception as e:
        logger.error(f"Database configuration creation test failed: {e}")
        return False


def test_connection_url_generation():
    """Test database connection URL generation"""
    logger.info("Testing connection URL generation...")
    
    try:
        # Test basic URL generation
        config = DatabaseConfig(
            host="localhost",
            port=4000,
            database="storysign",
            username="root",
            password="secret123"
        )
        
        # Test async URL
        async_url = config.get_connection_url(async_driver=True)
        expected_parts = [
            "mysql+asyncmy://root:secret123@localhost:4000/storysign",
            "ssl_disabled=true"
        ]
        
        for part in expected_parts:
            assert part in async_url, f"Expected '{part}' in URL: {async_url}"
        
        logger.info(f"✓ Async URL: {async_url}")
        
        # Test sync URL
        sync_url = config.get_connection_url(async_driver=False)
        assert "mysql+pymysql://root:secret123@localhost:4000/storysign" in sync_url
        logger.info(f"✓ Sync URL: {sync_url}")
        
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
        assert ":@" not in url_no_pass  # Should not have empty password
        logger.info(f"✓ URL without password: {url_no_pass}")
        
        return True
        
    except Exception as e:
        logger.error(f"Connection URL generation test failed: {e}")
        return False


def test_ssl_configuration():
    """Test SSL configuration in connection URLs"""
    logger.info("Testing SSL configuration...")
    
    try:
        # Test SSL enabled with certificates
        ssl_config = DatabaseConfig(
            host="secure.tidb.com",
            ssl_disabled=False,
            ssl_ca="/path/to/ca.pem",
            ssl_cert="/path/to/cert.pem",
            ssl_key="/path/to/key.pem"
        )
        
        ssl_url = ssl_config.get_connection_url()
        
        # Should not contain ssl_disabled=true
        assert "ssl_disabled=true" not in ssl_url
        
        # Should contain SSL certificate paths
        assert "ssl_ca=/path/to/ca.pem" in ssl_url
        assert "ssl_cert=/path/to/cert.pem" in ssl_url
        assert "ssl_key=/path/to/key.pem" in ssl_url
        
        logger.info(f"✓ SSL URL: {ssl_url}")
        
        return True
        
    except Exception as e:
        logger.error(f"SSL configuration test failed: {e}")
        return False


def test_config_validation():
    """Test configuration validation"""
    logger.info("Testing configuration validation...")
    
    try:
        # Test valid configurations pass
        valid_config = DatabaseConfig(
            host="valid.host.com",
            database="valid_db",
            username="valid_user"
        )
        assert valid_config.host == "valid.host.com"
        logger.info("✓ Valid configuration accepted")
        
        # Test invalid configurations are rejected
        try:
            DatabaseConfig(host="")  # Empty host should fail
            assert False, "Empty host should have been rejected"
        except ValueError:
            logger.info("✓ Empty host correctly rejected")
        
        try:
            DatabaseConfig(database="")  # Empty database should fail
            assert False, "Empty database should have been rejected"
        except ValueError:
            logger.info("✓ Empty database correctly rejected")
        
        try:
            DatabaseConfig(username="")  # Empty username should fail
            assert False, "Empty username should have been rejected"
        except ValueError:
            logger.info("✓ Empty username correctly rejected")
        
        return True
        
    except Exception as e:
        logger.error(f"Configuration validation test failed: {e}")
        return False


def test_global_config_integration():
    """Test integration with global configuration"""
    logger.info("Testing global configuration integration...")
    
    try:
        # Get global configuration
        app_config = get_config()
        
        # Verify database configuration is present
        assert hasattr(app_config, 'database'), "Global config should have database section"
        assert isinstance(app_config.database, DatabaseConfig), "Database config should be DatabaseConfig instance"
        
        # Test configuration values
        db_config = app_config.database
        assert db_config.host is not None, "Database host should not be None"
        assert db_config.port > 0, "Database port should be positive"
        assert db_config.database is not None, "Database name should not be None"
        assert db_config.username is not None, "Database username should not be None"
        
        logger.info(f"✓ Global database config: {db_config.host}:{db_config.port}/{db_config.database}")
        
        # Test connection URL generation from global config
        url = db_config.get_connection_url()
        assert "mysql+asyncmy" in url, "URL should use async MySQL driver"
        logger.info(f"✓ Global config URL: {url}")
        
        return True
        
    except Exception as e:
        logger.error(f"Global config integration test failed: {e}")
        return False


def main():
    """Run all database configuration tests"""
    logger.info("🚀 Starting database configuration tests...")
    
    tests = [
        ("Database Config Creation", test_database_config_creation),
        ("Connection URL Generation", test_connection_url_generation),
        ("SSL Configuration", test_ssl_configuration),
        ("Config Validation", test_config_validation),
        ("Global Config Integration", test_global_config_integration),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} ---")
        try:
            if test_func():
                logger.info(f"✅ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} FAILED")
                failed += 1
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {e}")
            failed += 1
    
    logger.info(f"\n🏁 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("🎉 All database configuration tests passed!")
        return 0
    else:
        logger.error("💥 Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())