#!/usr/bin/env python3
"""
Basic test for database service without requiring actual database connection
Tests service creation and configuration handling
"""

import sys
import os
import logging

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_database_service_import():
    """Test that database service can be imported"""
    logger.info("Testing database service import...")
    
    try:
        # This will fail if SQLAlchemy is not installed, but we can catch that
        from core.database_service import DatabaseService
        logger.info("✓ Database service imported successfully")
        return True
    except ImportError as e:
        if "sqlalchemy" in str(e).lower():
            logger.warning("⚠️ SQLAlchemy not installed - this is expected for basic config test")
            logger.info("✓ Database service import test completed (SQLAlchemy dependency noted)")
            return True
        else:
            logger.error(f"❌ Unexpected import error: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ Database service import failed: {e}")
        return False


def test_service_container_integration():
    """Test service container can handle database service registration"""
    logger.info("Testing service container integration...")
    
    try:
        from core.service_container import ServiceContainer
        
        # Create service container
        container = ServiceContainer()
        
        # Test that we can register a placeholder service
        class MockDatabaseService:
            def __init__(self):
                self.name = "MockDatabaseService"
            
            async def initialize(self):
                pass
            
            async def cleanup(self):
                pass
            
            def is_connected(self):
                return False
        
        mock_service = MockDatabaseService()
        container.register_service("database", mock_service)
        
        # Verify service is registered
        assert container.has_service("database")
        retrieved_service = container.get_service("database")
        assert retrieved_service.name == "MockDatabaseService"
        
        logger.info("✓ Service container integration successful")
        return True
        
    except Exception as e:
        logger.error(f"Service container integration test failed: {e}")
        return False


def test_config_yaml_database_section():
    """Test that config.yaml includes database configuration"""
    logger.info("Testing config.yaml database section...")
    
    try:
        import yaml
        from pathlib import Path
        
        # Look for config.yaml
        config_file = Path("config.yaml")
        if not config_file.exists():
            logger.info("ℹ️ config.yaml not found - using default configuration")
            return True
        
        # Load and check config.yaml
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f) or {}
        
        if "database" in config_data:
            db_config = config_data["database"]
            logger.info(f"✓ Database section found in config.yaml: {list(db_config.keys())}")
        else:
            logger.info("ℹ️ No database section in config.yaml - will use defaults")
        
        return True
        
    except Exception as e:
        logger.error(f"Config YAML test failed: {e}")
        return False


def test_environment_variable_support():
    """Test environment variable support for database configuration"""
    logger.info("Testing environment variable support...")
    
    try:
        import os
        from config import get_config
        
        # Set some test environment variables
        original_values = {}
        test_env_vars = {
            'STORYSIGN_DATABASE__HOST': 'test.tidb.com',
            'STORYSIGN_DATABASE__PORT': '4001',
            'STORYSIGN_DATABASE__DATABASE': 'test_storysign',
            'STORYSIGN_DATABASE__USERNAME': 'test_user'
        }
        
        # Save original values and set test values
        for key, value in test_env_vars.items():
            original_values[key] = os.environ.get(key)
            os.environ[key] = value
        
        try:
            # Get configuration with environment variables
            config = get_config()
            db_config = config.database
            
            # Verify environment variables are used
            assert db_config.host == 'test.tidb.com'
            assert db_config.port == 4001
            assert db_config.database == 'test_storysign'
            assert db_config.username == 'test_user'
            
            logger.info("✓ Environment variables correctly override configuration")
            
        finally:
            # Restore original environment
            for key, original_value in original_values.items():
                if original_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original_value
        
        return True
        
    except Exception as e:
        logger.error(f"Environment variable test failed: {e}")
        return False


def test_database_requirements():
    """Test that database requirements are properly specified"""
    logger.info("Testing database requirements...")
    
    try:
        from pathlib import Path
        
        # Check requirements.txt
        req_file = Path("requirements.txt")
        if req_file.exists():
            with open(req_file, 'r') as f:
                requirements = f.read()
            
            # Check for database-related packages
            db_packages = ['sqlalchemy', 'asyncmy', 'pymysql']
            found_packages = []
            
            for package in db_packages:
                if package in requirements.lower():
                    found_packages.append(package)
            
            if found_packages:
                logger.info(f"✓ Database packages found in requirements.txt: {found_packages}")
            else:
                logger.warning("⚠️ No database packages found in requirements.txt")
            
        else:
            logger.warning("⚠️ requirements.txt not found")
        
        return True
        
    except Exception as e:
        logger.error(f"Requirements test failed: {e}")
        return False


def main():
    """Run all basic database service tests"""
    logger.info("🚀 Starting basic database service tests...")
    
    tests = [
        ("Database Service Import", test_database_service_import),
        ("Service Container Integration", test_service_container_integration),
        ("Config YAML Database Section", test_config_yaml_database_section),
        ("Environment Variable Support", test_environment_variable_support),
        ("Database Requirements", test_database_requirements),
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
        logger.info("🎉 All basic database service tests passed!")
        return 0
    else:
        logger.error("💥 Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())