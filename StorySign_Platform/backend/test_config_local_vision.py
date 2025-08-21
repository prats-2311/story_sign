#!/usr/bin/env python3
"""
Test script for Local Vision Service Configuration Integration
Tests that the configuration system properly loads local vision settings
"""

import sys
import logging
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config, ConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_config_loading():
    """Test that local vision configuration loads correctly"""
    logger.info("Testing configuration loading...")
    
    try:
        config = get_config()
        
        # Test that local_vision config exists
        assert hasattr(config, 'local_vision'), "local_vision configuration not found"
        logger.info("✓ local_vision configuration exists")
        
        # Test configuration values
        lv_config = config.local_vision
        
        logger.info(f"Service URL: {lv_config.service_url}")
        logger.info(f"Model name: {lv_config.model_name}")
        logger.info(f"Timeout: {lv_config.timeout_seconds}s")
        logger.info(f"Max retries: {lv_config.max_retries}")
        logger.info(f"Enabled: {lv_config.enabled}")
        
        # Validate expected values
        assert lv_config.service_url == "http://localhost:11434", f"Unexpected service URL: {lv_config.service_url}"
        assert lv_config.model_name == "moondream2", f"Unexpected model name: {lv_config.model_name}"
        assert lv_config.timeout_seconds == 30, f"Unexpected timeout: {lv_config.timeout_seconds}"
        assert lv_config.max_retries == 3, f"Unexpected max retries: {lv_config.max_retries}"
        assert lv_config.enabled == True, f"Unexpected enabled state: {lv_config.enabled}"
        
        logger.info("✓ All configuration values are correct")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Configuration test failed: {e}")
        return False


def test_config_validation():
    """Test configuration validation"""
    logger.info("Testing configuration validation...")
    
    try:
        # Test valid model names
        from config import LocalVisionConfig
        
        valid_models = ['moondream2', 'phi3:vision', 'llava', 'bakllava']
        
        for model in valid_models:
            config = LocalVisionConfig(model_name=model)
            assert config.model_name == model
            logger.info(f"✓ Model '{model}' validated successfully")
        
        # Test invalid model name
        try:
            invalid_config = LocalVisionConfig(model_name="invalid_model")
            logger.error("✗ Invalid model name should have been rejected")
            return False
        except ValueError as e:
            logger.info(f"✓ Invalid model name properly rejected: {e}")
        
        # Test timeout validation
        config = LocalVisionConfig(timeout_seconds=60)
        assert config.timeout_seconds == 60
        logger.info("✓ Timeout validation works")
        
        # Test retry validation
        config = LocalVisionConfig(max_retries=5)
        assert config.max_retries == 5
        logger.info("✓ Max retries validation works")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Validation test failed: {e}")
        return False


def test_environment_override():
    """Test environment variable override"""
    logger.info("Testing environment variable override...")
    
    import os
    
    try:
        # Set environment variables
        os.environ['STORYSIGN_LOCAL_VISION__SERVICE_URL'] = 'http://test:8080'
        os.environ['STORYSIGN_LOCAL_VISION__MODEL_NAME'] = 'llava'
        os.environ['STORYSIGN_LOCAL_VISION__ENABLED'] = 'false'
        
        # Create new config manager to reload configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Check that environment variables override file values
        lv_config = config.local_vision
        
        assert lv_config.service_url == 'http://test:8080', f"Environment override failed for service_url: {lv_config.service_url}"
        assert lv_config.model_name == 'llava', f"Environment override failed for model_name: {lv_config.model_name}"
        assert lv_config.enabled == False, f"Environment override failed for enabled: {lv_config.enabled}"
        
        logger.info("✓ Environment variable overrides work correctly")
        
        # Clean up environment variables
        del os.environ['STORYSIGN_LOCAL_VISION__SERVICE_URL']
        del os.environ['STORYSIGN_LOCAL_VISION__MODEL_NAME']
        del os.environ['STORYSIGN_LOCAL_VISION__ENABLED']
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Environment override test failed: {e}")
        return False


def main():
    """Main test function"""
    logger.info("Starting Local Vision Configuration tests...")
    
    tests = [
        test_config_loading,
        test_config_validation,
        test_environment_override
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
                logger.info(f"✓ {test.__name__} PASSED")
            else:
                failed += 1
                logger.error(f"✗ {test.__name__} FAILED")
        except Exception as e:
            failed += 1
            logger.error(f"✗ {test.__name__} FAILED with exception: {e}")
    
    logger.info(f"Test results: {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("All tests passed! ✓")
        return 0
    else:
        logger.error("Some tests failed! ✗")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)