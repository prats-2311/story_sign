#!/usr/bin/env python3
"""
Configuration management for StorySign ASL Platform Backend
Handles video processing and MediaPipe configuration settings
"""

import os
import yaml
import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from pathlib import Path

logger = logging.getLogger(__name__)


class VideoConfig(BaseModel):
    """Configuration for video capture and processing settings"""
    
    width: int = Field(default=640, ge=240, le=1920, description="Video frame width in pixels")
    height: int = Field(default=480, ge=180, le=1080, description="Video frame height in pixels")
    fps: int = Field(default=30, ge=10, le=60, description="Target frames per second")
    format: str = Field(default="MJPG", description="Video format codec")
    quality: int = Field(default=50, ge=30, le=100, description="JPEG compression quality (optimized for low latency)")
    
    @field_validator('format')
    @classmethod
    def validate_format(cls, v):
        """Validate video format is supported"""
        supported_formats = ['MJPG', 'YUYV', 'H264']
        if v not in supported_formats:
            raise ValueError(f"Video format must be one of {supported_formats}")
        return v


class MediaPipeConfig(BaseModel):
    """Configuration for MediaPipe Holistic model settings (optimized for low latency)"""
    
    min_detection_confidence: float = Field(
        default=0.3, 
        ge=0.0, 
        le=1.0, 
        description="Minimum confidence for person detection (optimized for speed)"
    )
    min_tracking_confidence: float = Field(
        default=0.3, 
        ge=0.0, 
        le=1.0, 
        description="Minimum confidence for landmark tracking (optimized for speed)"
    )
    model_complexity: int = Field(
        default=0, 
        ge=0, 
        le=2, 
        description="Model complexity (0=lite/fastest, 1=full, 2=heavy) - optimized for speed"
    )
    enable_segmentation: bool = Field(
        default=False, 
        description="Enable pose segmentation mask"
    )
    refine_face_landmarks: bool = Field(
        default=True, 
        description="Enable refined face landmark detection"
    )
    
    @field_validator('model_complexity')
    @classmethod
    def validate_complexity(cls, v):
        """Validate model complexity is within supported range"""
        if v not in [0, 1, 2]:
            raise ValueError("Model complexity must be 0 (lite), 1 (full), or 2 (heavy)")
        return v


class ServerConfig(BaseModel):
    """Configuration for server settings"""
    
    host: str = Field(default="0.0.0.0", description="Server host address")
    port: int = Field(default=8000, ge=1024, le=65535, description="Server port number")
    reload: bool = Field(default=True, description="Enable auto-reload in development")
    log_level: str = Field(default="info", description="Logging level")
    max_connections: int = Field(default=10, ge=1, le=100, description="Maximum WebSocket connections")
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level is supported"""
        valid_levels = ['debug', 'info', 'warning', 'error', 'critical']
        if v.lower() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.lower()


class AppConfig(BaseModel):
    """Main application configuration containing all sub-configurations"""
    
    video: VideoConfig = Field(default_factory=VideoConfig)
    mediapipe: MediaPipeConfig = Field(default_factory=MediaPipeConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    
    class Config:
        """Pydantic configuration"""
        env_prefix = "STORYSIGN_"
        env_nested_delimiter = "__"


class ConfigManager:
    """Configuration manager for loading and validating application settings"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_file: Optional path to YAML configuration file
        """
        self.config_file = config_file or self._find_config_file()
        self._config: Optional[AppConfig] = None
    
    def _find_config_file(self) -> Optional[str]:
        """Find configuration file in standard locations"""
        possible_paths = [
            "config.yaml",
            "config.yml", 
            "storysign_config.yaml",
            "storysign_config.yml",
            os.path.expanduser("~/.storysign/config.yaml"),
            "/etc/storysign/config.yaml"
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                logger.info(f"Found configuration file: {path}")
                return path
        
        logger.info("No configuration file found, using defaults and environment variables")
        return None
    
    def _load_yaml_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_file or not Path(self.config_file).exists():
            return {}
        
        try:
            with open(self.config_file, 'r') as f:
                config_data = yaml.safe_load(f) or {}
            logger.info(f"Loaded configuration from {self.config_file}")
            return config_data
        except Exception as e:
            logger.error(f"Failed to load configuration file {self.config_file}: {e}")
            return {}
    
    def _merge_env_vars(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge environment variables into configuration data"""
        # Environment variables take precedence over file configuration
        env_vars = {}
        
        # Video configuration from environment
        if os.getenv('STORYSIGN_VIDEO__WIDTH'):
            env_vars.setdefault('video', {})['width'] = int(os.getenv('STORYSIGN_VIDEO__WIDTH'))
        if os.getenv('STORYSIGN_VIDEO__HEIGHT'):
            env_vars.setdefault('video', {})['height'] = int(os.getenv('STORYSIGN_VIDEO__HEIGHT'))
        if os.getenv('STORYSIGN_VIDEO__FPS'):
            env_vars.setdefault('video', {})['fps'] = int(os.getenv('STORYSIGN_VIDEO__FPS'))
        if os.getenv('STORYSIGN_VIDEO__FORMAT'):
            env_vars.setdefault('video', {})['format'] = os.getenv('STORYSIGN_VIDEO__FORMAT')
        if os.getenv('STORYSIGN_VIDEO__QUALITY'):
            env_vars.setdefault('video', {})['quality'] = int(os.getenv('STORYSIGN_VIDEO__QUALITY'))
        
        # MediaPipe configuration from environment
        if os.getenv('STORYSIGN_MEDIAPIPE__MIN_DETECTION_CONFIDENCE'):
            env_vars.setdefault('mediapipe', {})['min_detection_confidence'] = float(os.getenv('STORYSIGN_MEDIAPIPE__MIN_DETECTION_CONFIDENCE'))
        if os.getenv('STORYSIGN_MEDIAPIPE__MIN_TRACKING_CONFIDENCE'):
            env_vars.setdefault('mediapipe', {})['min_tracking_confidence'] = float(os.getenv('STORYSIGN_MEDIAPIPE__MIN_TRACKING_CONFIDENCE'))
        if os.getenv('STORYSIGN_MEDIAPIPE__MODEL_COMPLEXITY'):
            env_vars.setdefault('mediapipe', {})['model_complexity'] = int(os.getenv('STORYSIGN_MEDIAPIPE__MODEL_COMPLEXITY'))
        if os.getenv('STORYSIGN_MEDIAPIPE__ENABLE_SEGMENTATION'):
            env_vars.setdefault('mediapipe', {})['enable_segmentation'] = os.getenv('STORYSIGN_MEDIAPIPE__ENABLE_SEGMENTATION').lower() == 'true'
        if os.getenv('STORYSIGN_MEDIAPIPE__REFINE_FACE_LANDMARKS'):
            env_vars.setdefault('mediapipe', {})['refine_face_landmarks'] = os.getenv('STORYSIGN_MEDIAPIPE__REFINE_FACE_LANDMARKS').lower() == 'true'
        
        # Server configuration from environment
        if os.getenv('STORYSIGN_SERVER__HOST'):
            env_vars.setdefault('server', {})['host'] = os.getenv('STORYSIGN_SERVER__HOST')
        if os.getenv('STORYSIGN_SERVER__PORT'):
            env_vars.setdefault('server', {})['port'] = int(os.getenv('STORYSIGN_SERVER__PORT'))
        if os.getenv('STORYSIGN_SERVER__RELOAD'):
            env_vars.setdefault('server', {})['reload'] = os.getenv('STORYSIGN_SERVER__RELOAD').lower() == 'true'
        if os.getenv('STORYSIGN_SERVER__LOG_LEVEL'):
            env_vars.setdefault('server', {})['log_level'] = os.getenv('STORYSIGN_SERVER__LOG_LEVEL')
        if os.getenv('STORYSIGN_SERVER__MAX_CONNECTIONS'):
            env_vars.setdefault('server', {})['max_connections'] = int(os.getenv('STORYSIGN_SERVER__MAX_CONNECTIONS'))
        
        # Merge environment variables with file configuration (env vars take precedence)
        for section, values in env_vars.items():
            if section in config_data:
                config_data[section].update(values)
            else:
                config_data[section] = values
        
        return config_data
    
    def load_config(self) -> AppConfig:
        """
        Load and validate application configuration
        
        Returns:
            AppConfig: Validated configuration object
            
        Raises:
            ValueError: If configuration validation fails
        """
        if self._config is not None:
            return self._config
        
        try:
            # Load from YAML file
            config_data = self._load_yaml_config()
            
            # Merge environment variables
            config_data = self._merge_env_vars(config_data)
            
            # Create and validate configuration
            self._config = AppConfig(**config_data)
            
            logger.info("Configuration loaded and validated successfully")
            logger.debug(f"Video config: {self._config.video}")
            logger.debug(f"MediaPipe config: {self._config.mediapipe}")
            logger.debug(f"Server config: {self._config.server}")
            
            return self._config
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise ValueError(f"Invalid configuration: {e}")
    
    def get_config(self) -> AppConfig:
        """Get current configuration, loading if necessary"""
        if self._config is None:
            return self.load_config()
        return self._config
    
    def reload_config(self) -> AppConfig:
        """Reload configuration from file and environment"""
        self._config = None
        return self.load_config()


# Global configuration manager instance
config_manager = ConfigManager()


def get_config() -> AppConfig:
    """Get application configuration"""
    return config_manager.get_config()