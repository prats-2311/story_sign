#!/usr/bin/env python3
"""
Test script for configuration management system
Validates configuration loading, validation, and environment variable handling
"""

import os
import sys
import tempfile
import yaml
from pathlib import Path

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import ConfigManager, AppConfig, VideoConfig, MediaPipeConfig, ServerConfig


def test_default_configuration():
    """Test loading default configuration without any files or env vars"""
    print("Testing default configuration...")
    
    # Clear any existing environment variables
    env_vars_to_clear = [key for key in os.environ.keys() if key.startswith('STORYSIGN_')]
    for var in env_vars_to_clear:
        del os.environ[var]
    
    # Create config manager without config file
    config_manager = ConfigManager(config_file=None)
    config = config_manager.load_config()
    
    # Verify default values
    assert config.video.width == 640
    assert config.video.height == 480
    assert config.video.fps == 30
    assert config.video.format == "MJPG"
    assert config.video.quality == 85
    
    assert config.mediapipe.min_detection_confidence == 0.5
    assert config.mediapipe.min_tracking_confidence == 0.5
    assert config.mediapipe.model_complexity == 1
    assert config.mediapipe.enable_segmentation == False
    assert config.mediapipe.refine_face_landmarks == True
    
    assert config.server.host == "0.0.0.0"
    assert config.server.port == 8000
    assert config.server.reload == True
    assert config.server.log_level == "info"
    assert config.server.max_connections == 10
    
    print("✓ Default configuration test passed")


def test_yaml_configuration():
    """Test loading configuration from YAML file"""
    print("Testing YAML configuration...")
    
    # Create temporary YAML config file
    config_data = {
        'video': {
            'width': 1280,
            'height': 720,
            'fps': 60,
            'format': 'H264',
            'quality': 95
        },
        'mediapipe': {
            'min_detection_confidence': 0.7,
            'min_tracking_confidence': 0.6,
            'model_complexity': 2,
            'enable_segmentation': True,
            'refine_face_landmarks': False
        },
        'server': {
            'host': '127.0.0.1',
            'port': 9000,
            'reload': False,
            'log_level': 'debug',
            'max_connections': 20
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        temp_config_file = f.name
    
    try:
        # Load configuration from file
        config_manager = ConfigManager(config_file=temp_config_file)
        config = config_manager.load_config()
        
        # Verify YAML values were loaded
        assert config.video.width == 1280
        assert config.video.height == 720
        assert config.video.fps == 60
        assert config.video.format == "H264"
        assert config.video.quality == 95
        
        assert config.mediapipe.min_detection_confidence == 0.7
        assert config.mediapipe.min_tracking_confidence == 0.6
        assert config.mediapipe.model_complexity == 2
        assert config.mediapipe.enable_segmentation == True
        assert config.mediapipe.refine_face_landmarks == False
        
        assert config.server.host == "127.0.0.1"
        assert config.server.port == 9000
        assert config.server.reload == False
        assert config.server.log_level == "debug"
        assert config.server.max_connections == 20
        
        print("✓ YAML configuration test passed")
        
    finally:
        # Clean up temporary file
        Path(temp_config_file).unlink()


def test_environment_variables():
    """Test configuration loading from environment variables"""
    print("Testing environment variable configuration...")
    
    # Set environment variables
    os.environ['STORYSIGN_VIDEO__WIDTH'] = '800'
    os.environ['STORYSIGN_VIDEO__HEIGHT'] = '600'
    os.environ['STORYSIGN_VIDEO__FPS'] = '25'
    os.environ['STORYSIGN_MEDIAPIPE__MIN_DETECTION_CONFIDENCE'] = '0.8'
    os.environ['STORYSIGN_MEDIAPIPE__MODEL_COMPLEXITY'] = '0'
    os.environ['STORYSIGN_SERVER__PORT'] = '7000'
    os.environ['STORYSIGN_SERVER__LOG_LEVEL'] = 'warning'
    
    try:
        # Load configuration with environment variables
        config_manager = ConfigManager(config_file=None)
        config = config_manager.load_config()
        
        # Verify environment values were loaded
        assert config.video.width == 800
        assert config.video.height == 600
        assert config.video.fps == 25
        assert config.mediapipe.min_detection_confidence == 0.8
        assert config.mediapipe.model_complexity == 0
        assert config.server.port == 7000
        assert config.server.log_level == "warning"
        
        # Verify defaults are still used for unset values
        assert config.video.format == "MJPG"  # Default value
        assert config.mediapipe.min_tracking_confidence == 0.5  # Default value
        
        print("✓ Environment variable configuration test passed")
        
    finally:
        # Clean up environment variables
        env_vars_to_clear = [
            'STORYSIGN_VIDEO__WIDTH',
            'STORYSIGN_VIDEO__HEIGHT', 
            'STORYSIGN_VIDEO__FPS',
            'STORYSIGN_MEDIAPIPE__MIN_DETECTION_CONFIDENCE',
            'STORYSIGN_MEDIAPIPE__MODEL_COMPLEXITY',
            'STORYSIGN_SERVER__PORT',
            'STORYSIGN_SERVER__LOG_LEVEL'
        ]
        for var in env_vars_to_clear:
            if var in os.environ:
                del os.environ[var]


def test_configuration_validation():
    """Test configuration validation with invalid values"""
    print("Testing configuration validation...")
    
    # Test invalid video configuration
    try:
        VideoConfig(width=100)  # Too small
        assert False, "Should have raised validation error"
    except ValueError:
        pass  # Expected
    
    try:
        VideoConfig(fps=5)  # Too low
        assert False, "Should have raised validation error"
    except ValueError:
        pass  # Expected
    
    try:
        VideoConfig(format="INVALID")  # Invalid format
        assert False, "Should have raised validation error"
    except ValueError:
        pass  # Expected
    
    # Test invalid MediaPipe configuration
    try:
        MediaPipeConfig(min_detection_confidence=1.5)  # Too high
        assert False, "Should have raised validation error"
    except ValueError:
        pass  # Expected
    
    try:
        MediaPipeConfig(model_complexity=5)  # Invalid complexity
        assert False, "Should have raised validation error"
    except ValueError:
        pass  # Expected
    
    # Test invalid server configuration
    try:
        ServerConfig(port=100)  # Too low
        assert False, "Should have raised validation error"
    except ValueError:
        pass  # Expected
    
    try:
        ServerConfig(log_level="invalid")  # Invalid log level
        assert False, "Should have raised validation error"
    except ValueError:
        pass  # Expected
    
    print("✓ Configuration validation test passed")


def main():
    """Run all configuration tests"""
    print("Running StorySign Configuration System Tests")
    print("=" * 50)
    
    try:
        test_default_configuration()
        test_yaml_configuration()
        test_environment_variables()
        test_configuration_validation()
        
        print("\n" + "=" * 50)
        print("✅ All configuration tests passed!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())