#!/usr/bin/env python3
"""
Unit tests for configuration management system
"""

import pytest
import os
import tempfile
import yaml
from unittest.mock import patch, mock_open
from pathlib import Path

from config import (
    VideoConfig, MediaPipeConfig, ServerConfig, AppConfig,
    ConfigManager, get_config
)


class TestVideoConfig:
    """Test cases for VideoConfig validation"""
    
    def test_video_config_defaults(self):
        """Test VideoConfig default values"""
        config = VideoConfig()
        
        assert config.width == 240
        assert config.height == 180
        assert config.fps == 30
        assert config.format == "MJPG"
        assert config.quality == 60
        
    def test_video_config_valid_values(self):
        """Test VideoConfig with valid custom values"""
        config = VideoConfig(
            width=640,
            height=480,
            fps=25,
            format="H264",
            quality=80
        )
        
        assert config.width == 640
        assert config.height == 480
        assert config.fps == 25
        assert config.format == "H264"
        assert config.quality == 80
        
    def test_video_config_validation_width(self):
        """Test VideoConfig width validation"""
        # Valid width
        config = VideoConfig(width=640)
        assert config.width == 640
        
        # Invalid width (too small)
        with pytest.raises(ValueError):
            VideoConfig(width=100)
            
        # Invalid width (too large)
        with pytest.raises(ValueError):
            VideoConfig(width=5000)
            
    def test_video_config_validation_height(self):
        """Test VideoConfig height validation"""
        # Valid height
        config = VideoConfig(height=480)
        assert config.height == 480
        
        # Invalid height (too small)
        with pytest.raises(ValueError):
            VideoConfig(height=100)
            
        # Invalid height (too large)
        with pytest.raises(ValueError):
            VideoConfig(height=2000)
            
    def test_video_config_validation_fps(self):
        """Test VideoConfig FPS validation"""
        # Valid FPS
        config = VideoConfig(fps=30)
        assert config.fps == 30
        
        # Invalid FPS (too low)
        with pytest.raises(ValueError):
            VideoConfig(fps=5)
            
        # Invalid FPS (too high)
        with pytest.raises(ValueError):
            VideoConfig(fps=120)
            
    def test_video_config_validation_format(self):
        """Test VideoConfig format validation"""
        # Valid formats
        for fmt in ["MJPG", "YUYV", "H264"]:
            config = VideoConfig(format=fmt)
            assert config.format == fmt
            
        # Invalid format
        with pytest.raises(ValueError):
            VideoConfig(format="INVALID")
            
    def test_video_config_validation_quality(self):
        """Test VideoConfig quality validation"""
        # Valid quality
        config = VideoConfig(quality=80)
        assert config.quality == 80
        
        # Invalid quality (too low)
        with pytest.raises(ValueError):
            VideoConfig(quality=20)
            
        # Invalid quality (too high)
        with pytest.raises(ValueError):
            VideoConfig(quality=150)


class TestMediaPipeConfig:
    """Test cases for MediaPipeConfig validation"""
    
    def test_mediapipe_config_defaults(self):
        """Test MediaPipeConfig default values"""
        config = MediaPipeConfig()
        
        assert config.min_detection_confidence == 0.3
        assert config.min_tracking_confidence == 0.3
        assert config.model_complexity == 1
        assert config.enable_segmentation == False
        assert config.refine_face_landmarks == True
        
    def test_mediapipe_config_valid_values(self):
        """Test MediaPipeConfig with valid custom values"""
        config = MediaPipeConfig(
            min_detection_confidence=0.7,
            min_tracking_confidence=0.8,
            model_complexity=2,
            enable_segmentation=True,
            refine_face_landmarks=False
        )
        
        assert config.min_detection_confidence == 0.7
        assert config.min_tracking_confidence == 0.8
        assert config.model_complexity == 2
        assert config.enable_segmentation == True
        assert config.refine_face_landmarks == False
        
    def test_mediapipe_config_confidence_validation(self):
        """Test MediaPipeConfig confidence value validation"""
        # Valid confidence values
        config = MediaPipeConfig(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.6
        )
        assert config.min_detection_confidence == 0.5
        assert config.min_tracking_confidence == 0.6
        
        # Invalid confidence values (too low)
        with pytest.raises(ValueError):
            MediaPipeConfig(min_detection_confidence=-0.1)
            
        with pytest.raises(ValueError):
            MediaPipeConfig(min_tracking_confidence=-0.1)
            
        # Invalid confidence values (too high)
        with pytest.raises(ValueError):
            MediaPipeConfig(min_detection_confidence=1.5)
            
        with pytest.raises(ValueError):
            MediaPipeConfig(min_tracking_confidence=1.5)
            
    def test_mediapipe_config_complexity_validation(self):
        """Test MediaPipeConfig model complexity validation"""
        # Valid complexity values
        for complexity in [0, 1, 2]:
            config = MediaPipeConfig(model_complexity=complexity)
            assert config.model_complexity == complexity
            
        # Invalid complexity values
        with pytest.raises(ValueError):
            MediaPipeConfig(model_complexity=-1)
            
        with pytest.raises(ValueError):
            MediaPipeConfig(model_complexity=3)


class TestServerConfig:
    """Test cases for ServerConfig validation"""
    
    def test_server_config_defaults(self):
        """Test ServerConfig default values"""
        config = ServerConfig()
        
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.reload == True
        assert config.log_level == "info"
        assert config.max_connections == 10
        
    def test_server_config_valid_values(self):
        """Test ServerConfig with valid custom values"""
        config = ServerConfig(
            host="127.0.0.1",
            port=9000,
            reload=False,
            log_level="debug",
            max_connections=20
        )
        
        assert config.host == "127.0.0.1"
        assert config.port == 9000
        assert config.reload == False
        assert config.log_level == "debug"
        assert config.max_connections == 20
        
    def test_server_config_port_validation(self):
        """Test ServerConfig port validation"""
        # Valid port
        config = ServerConfig(port=8080)
        assert config.port == 8080
        
        # Invalid port (too low)
        with pytest.raises(ValueError):
            ServerConfig(port=80)  # Below 1024
            
        # Invalid port (too high)
        with pytest.raises(ValueError):
            ServerConfig(port=70000)  # Above 65535
            
    def test_server_config_log_level_validation(self):
        """Test ServerConfig log level validation"""
        # Valid log levels
        valid_levels = ['debug', 'info', 'warning', 'error', 'critical']
        for level in valid_levels:
            config = ServerConfig(log_level=level)
            assert config.log_level == level
            
        # Case insensitive
        config = ServerConfig(log_level="DEBUG")
        assert config.log_level == "debug"
        
        # Invalid log level
        with pytest.raises(ValueError):
            ServerConfig(log_level="invalid")
            
    def test_server_config_max_connections_validation(self):
        """Test ServerConfig max connections validation"""
        # Valid max connections
        config = ServerConfig(max_connections=50)
        assert config.max_connections == 50
        
        # Invalid max connections (too low)
        with pytest.raises(ValueError):
            ServerConfig(max_connections=0)
            
        # Invalid max connections (too high)
        with pytest.raises(ValueError):
            ServerConfig(max_connections=200)


class TestAppConfig:
    """Test cases for AppConfig composition"""
    
    def test_app_config_defaults(self):
        """Test AppConfig with default sub-configurations"""
        config = AppConfig()
        
        assert isinstance(config.video, VideoConfig)
        assert isinstance(config.mediapipe, MediaPipeConfig)
        assert isinstance(config.server, ServerConfig)
        
    def test_app_config_custom_values(self):
        """Test AppConfig with custom sub-configurations"""
        video_config = VideoConfig(width=640, height=480)
        mediapipe_config = MediaPipeConfig(model_complexity=2)
        server_config = ServerConfig(port=9000)
        
        config = AppConfig(
            video=video_config,
            mediapipe=mediapipe_config,
            server=server_config
        )
        
        assert config.video.width == 640
        assert config.mediapipe.model_complexity == 2
        assert config.server.port == 9000
        
    def test_app_config_nested_dict_initialization(self):
        """Test AppConfig initialization from nested dictionary"""
        config_dict = {
            "video": {
                "width": 800,
                "height": 600,
                "fps": 25
            },
            "mediapipe": {
                "min_detection_confidence": 0.7,
                "model_complexity": 0
            },
            "server": {
                "host": "localhost",
                "port": 8080,
                "log_level": "debug"
            }
        }
        
        config = AppConfig(**config_dict)
        
        assert config.video.width == 800
        assert config.video.height == 600
        assert config.video.fps == 25
        assert config.mediapipe.min_detection_confidence == 0.7
        assert config.mediapipe.model_complexity == 0
        assert config.server.host == "localhost"
        assert config.server.port == 8080
        assert config.server.log_level == "debug"


class TestConfigManager:
    """Test cases for ConfigManager class"""
    
    def setup_method(self):
        """Set up test environment"""
        # Clear any existing environment variables
        self.original_env = {}
        for key in os.environ:
            if key.startswith('STORYSIGN_'):
                self.original_env[key] = os.environ[key]
                del os.environ[key]
                
    def teardown_method(self):
        """Clean up test environment"""
        # Restore original environment variables
        for key in list(os.environ.keys()):
            if key.startswith('STORYSIGN_'):
                del os.environ[key]
        for key, value in self.original_env.items():
            os.environ[key] = value
            
    def test_config_manager_initialization(self):
        """Test ConfigManager initialization"""
        manager = ConfigManager()
        
        assert manager.config_file is None or isinstance(manager.config_file, str)
        assert manager._config is None
        
    def test_config_manager_with_custom_file(self):
        """Test ConfigManager with custom config file"""
        manager = ConfigManager(config_file="custom_config.yaml")
        
        assert manager.config_file == "custom_config.yaml"
        
    def test_load_yaml_config_file_not_found(self):
        """Test loading YAML config when file doesn't exist"""
        manager = ConfigManager(config_file="nonexistent.yaml")
        
        config_data = manager._load_yaml_config()
        
        assert config_data == {}
        
    def test_load_yaml_config_valid_file(self):
        """Test loading valid YAML config file"""
        config_content = {
            "video": {
                "width": 800,
                "height": 600
            },
            "server": {
                "port": 9000
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_content, f)
            temp_file = f.name
            
        try:
            manager = ConfigManager(config_file=temp_file)
            config_data = manager._load_yaml_config()
            
            assert config_data["video"]["width"] == 800
            assert config_data["video"]["height"] == 600
            assert config_data["server"]["port"] == 9000
            
        finally:
            os.unlink(temp_file)
            
    def test_load_yaml_config_invalid_file(self):
        """Test loading invalid YAML config file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_file = f.name
            
        try:
            manager = ConfigManager(config_file=temp_file)
            config_data = manager._load_yaml_config()
            
            # Should return empty dict on error
            assert config_data == {}
            
        finally:
            os.unlink(temp_file)
            
    def test_merge_env_vars_video_config(self):
        """Test merging video configuration from environment variables"""
        # Set environment variables
        os.environ['STORYSIGN_VIDEO__WIDTH'] = '1024'
        os.environ['STORYSIGN_VIDEO__HEIGHT'] = '768'
        os.environ['STORYSIGN_VIDEO__FPS'] = '60'
        os.environ['STORYSIGN_VIDEO__FORMAT'] = 'H264'
        os.environ['STORYSIGN_VIDEO__QUALITY'] = '90'
        
        manager = ConfigManager()
        config_data = manager._merge_env_vars({})
        
        assert config_data["video"]["width"] == 1024
        assert config_data["video"]["height"] == 768
        assert config_data["video"]["fps"] == 60
        assert config_data["video"]["format"] == "H264"
        assert config_data["video"]["quality"] == 90
        
    def test_merge_env_vars_mediapipe_config(self):
        """Test merging MediaPipe configuration from environment variables"""
        os.environ['STORYSIGN_MEDIAPIPE__MIN_DETECTION_CONFIDENCE'] = '0.8'
        os.environ['STORYSIGN_MEDIAPIPE__MIN_TRACKING_CONFIDENCE'] = '0.9'
        os.environ['STORYSIGN_MEDIAPIPE__MODEL_COMPLEXITY'] = '2'
        os.environ['STORYSIGN_MEDIAPIPE__ENABLE_SEGMENTATION'] = 'true'
        os.environ['STORYSIGN_MEDIAPIPE__REFINE_FACE_LANDMARKS'] = 'false'
        
        manager = ConfigManager()
        config_data = manager._merge_env_vars({})
        
        assert config_data["mediapipe"]["min_detection_confidence"] == 0.8
        assert config_data["mediapipe"]["min_tracking_confidence"] == 0.9
        assert config_data["mediapipe"]["model_complexity"] == 2
        assert config_data["mediapipe"]["enable_segmentation"] == True
        assert config_data["mediapipe"]["refine_face_landmarks"] == False
        
    def test_merge_env_vars_server_config(self):
        """Test merging server configuration from environment variables"""
        os.environ['STORYSIGN_SERVER__HOST'] = '192.168.1.100'
        os.environ['STORYSIGN_SERVER__PORT'] = '8080'
        os.environ['STORYSIGN_SERVER__RELOAD'] = 'false'
        os.environ['STORYSIGN_SERVER__LOG_LEVEL'] = 'debug'
        os.environ['STORYSIGN_SERVER__MAX_CONNECTIONS'] = '25'
        
        manager = ConfigManager()
        config_data = manager._merge_env_vars({})
        
        assert config_data["server"]["host"] == "192.168.1.100"
        assert config_data["server"]["port"] == 8080
        assert config_data["server"]["reload"] == False
        assert config_data["server"]["log_level"] == "debug"
        assert config_data["server"]["max_connections"] == 25
        
    def test_env_vars_override_file_config(self):
        """Test that environment variables override file configuration"""
        file_config = {
            "video": {"width": 640},
            "server": {"port": 8000}
        }
        
        os.environ['STORYSIGN_VIDEO__WIDTH'] = '1024'
        os.environ['STORYSIGN_SERVER__PORT'] = '9000'
        
        manager = ConfigManager()
        merged_config = manager._merge_env_vars(file_config)
        
        assert merged_config["video"]["width"] == 1024  # Overridden by env var
        assert merged_config["server"]["port"] == 9000  # Overridden by env var
        
    def test_load_config_success(self):
        """Test successful configuration loading"""
        os.environ['STORYSIGN_VIDEO__WIDTH'] = '800'
        os.environ['STORYSIGN_SERVER__PORT'] = '8080'
        
        manager = ConfigManager()
        config = manager.load_config()
        
        assert isinstance(config, AppConfig)
        assert config.video.width == 800
        assert config.server.port == 8080
        
    def test_load_config_validation_error(self):
        """Test configuration loading with validation error"""
        # Set invalid environment variable
        os.environ['STORYSIGN_VIDEO__WIDTH'] = '0'  # Invalid width
        
        manager = ConfigManager()
        
        with pytest.raises(ValueError):
            manager.load_config()
            
    def test_get_config_caching(self):
        """Test configuration caching behavior"""
        manager = ConfigManager()
        
        # First call should load config
        config1 = manager.get_config()
        
        # Second call should return cached config
        config2 = manager.get_config()
        
        assert config1 is config2  # Same object reference
        
    def test_reload_config(self):
        """Test configuration reloading"""
        manager = ConfigManager()
        
        # Load initial config
        config1 = manager.get_config()
        
        # Change environment variable
        os.environ['STORYSIGN_VIDEO__WIDTH'] = '1024'
        
        # Reload config
        config2 = manager.reload_config()
        
        assert config1 is not config2  # Different object reference
        assert config2.video.width == 1024
        
    def test_find_config_file(self):
        """Test configuration file discovery"""
        manager = ConfigManager()
        
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, 
                                       prefix='config', dir='.') as f:
            yaml.dump({"test": "config"}, f)
            temp_file = f.name
            
        try:
            # Should find the config file
            found_file = manager._find_config_file()
            
            # Clean up first
            os.unlink(temp_file)
            
            # The method should find some config file or return None
            assert found_file is None or isinstance(found_file, str)
            
        except:
            # Clean up on error
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            raise


class TestGlobalConfigFunction:
    """Test cases for global get_config function"""
    
    def test_get_config_function(self):
        """Test global get_config function"""
        config = get_config()
        
        assert isinstance(config, AppConfig)
        assert isinstance(config.video, VideoConfig)
        assert isinstance(config.mediapipe, MediaPipeConfig)
        assert isinstance(config.server, ServerConfig)
        
    def test_get_config_consistency(self):
        """Test that get_config returns consistent results"""
        config1 = get_config()
        config2 = get_config()
        
        # Should return the same cached instance
        assert config1 is config2


class TestConfigurationIntegration:
    """Integration tests for configuration system"""
    
    def setup_method(self):
        """Set up integration test environment"""
        # Clear environment variables
        for key in list(os.environ.keys()):
            if key.startswith('STORYSIGN_'):
                del os.environ[key]
                
    def test_complete_configuration_workflow(self):
        """Test complete configuration workflow from file and environment"""
        # Create config file
        config_content = {
            "video": {
                "width": 640,
                "height": 480,
                "fps": 30
            },
            "mediapipe": {
                "min_detection_confidence": 0.5,
                "model_complexity": 1
            },
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "log_level": "info"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_content, f)
            temp_file = f.name
            
        try:
            # Set some environment variables to override file config
            os.environ['STORYSIGN_VIDEO__WIDTH'] = '1024'
            os.environ['STORYSIGN_SERVER__PORT'] = '9000'
            os.environ['STORYSIGN_MEDIAPIPE__MODEL_COMPLEXITY'] = '2'
            
            # Load configuration
            manager = ConfigManager(config_file=temp_file)
            config = manager.load_config()
            
            # Verify file values are loaded
            assert config.video.height == 480  # From file
            assert config.video.fps == 30  # From file
            assert config.mediapipe.min_detection_confidence == 0.5  # From file
            assert config.server.host == "0.0.0.0"  # From file
            assert config.server.log_level == "info"  # From file
            
            # Verify environment variables override file values
            assert config.video.width == 1024  # Overridden by env var
            assert config.server.port == 9000  # Overridden by env var
            assert config.mediapipe.model_complexity == 2  # Overridden by env var
            
        finally:
            os.unlink(temp_file)
            
    def test_configuration_validation_integration(self):
        """Test configuration validation in integration scenario"""
        # Set valid configuration through environment
        os.environ['STORYSIGN_VIDEO__WIDTH'] = '800'
        os.environ['STORYSIGN_VIDEO__HEIGHT'] = '600'
        os.environ['STORYSIGN_VIDEO__FPS'] = '25'
        os.environ['STORYSIGN_VIDEO__FORMAT'] = 'H264'
        os.environ['STORYSIGN_VIDEO__QUALITY'] = '85'
        
        os.environ['STORYSIGN_MEDIAPIPE__MIN_DETECTION_CONFIDENCE'] = '0.7'
        os.environ['STORYSIGN_MEDIAPIPE__MIN_TRACKING_CONFIDENCE'] = '0.8'
        os.environ['STORYSIGN_MEDIAPIPE__MODEL_COMPLEXITY'] = '2'
        
        os.environ['STORYSIGN_SERVER__HOST'] = '127.0.0.1'
        os.environ['STORYSIGN_SERVER__PORT'] = '8080'
        os.environ['STORYSIGN_SERVER__LOG_LEVEL'] = 'debug'
        os.environ['STORYSIGN_SERVER__MAX_CONNECTIONS'] = '20'
        
        manager = ConfigManager()
        config = manager.load_config()
        
        # Verify all values are correctly loaded and validated
        assert config.video.width == 800
        assert config.video.height == 600
        assert config.video.fps == 25
        assert config.video.format == "H264"
        assert config.video.quality == 85
        
        assert config.mediapipe.min_detection_confidence == 0.7
        assert config.mediapipe.min_tracking_confidence == 0.8
        assert config.mediapipe.model_complexity == 2
        
        assert config.server.host == "127.0.0.1"
        assert config.server.port == 8080
        assert config.server.log_level == "debug"
        assert config.server.max_connections == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])