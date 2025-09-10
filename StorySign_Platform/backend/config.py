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
        supported_formats = ['MJPG', 'YUYV', 'H264', 'JPEG']
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


class LocalVisionConfig(BaseModel):
    """Configuration for local vision service integration"""

    service_url: str = Field(default="http://localhost:1234", description="Local vision service URL")
    model_name: str = Field(default="google/gemma-3-4b", description="Vision model name")
    service_type: str = Field(default="lm_studio", description="Service type (ollama, lm_studio, or groq)")
    timeout_seconds: int = Field(default=30, ge=5, le=120, description="Request timeout in seconds")
    max_retries: int = Field(default=3, ge=1, le=10, description="Maximum retry attempts")
    enabled: bool = Field(default=True, description="Enable/disable local vision service")

    @field_validator('service_type')
    @classmethod
    def validate_service_type(cls, v):
        """Validate service type is supported"""
        supported_types = ['ollama', 'lm_studio', 'groq']
        if v not in supported_types:
            raise ValueError(f"Service type must be one of {supported_types}")
        return v


class GroqConfig(BaseModel):
    """Configuration for Groq Vision API integration"""

    api_key: Optional[str] = Field(default=None, description="Groq API key (required for production)")
    base_url: str = Field(default="https://api.groq.com/openai/v1", description="Groq API base URL")
    model_name: str = Field(default="llava-v1.5-7b-4096-preview", description="Groq vision model name")
    timeout_seconds: int = Field(default=30, ge=5, le=120, description="Request timeout in seconds")
    max_retries: int = Field(default=3, ge=1, le=10, description="Maximum retry attempts")
    max_tokens: int = Field(default=1000, ge=100, le=4000, description="Maximum tokens for generation")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Generation temperature")
    enabled: bool = Field(default=False, description="Enable/disable Groq API service")

    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v):
        """Validate API key format if provided"""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Groq API key cannot be empty if provided")
        return v.strip() if v else None

    @field_validator('model_name')
    @classmethod
    def validate_model_name(cls, v):
        """Validate model name is not empty"""
        if not v or not v.strip():
            raise ValueError("Groq model name cannot be empty")
        return v.strip()

    def is_configured(self) -> bool:
        """Check if Groq API is properly configured"""
        return self.enabled and self.api_key is not None and len(self.api_key.strip()) > 0


class OllamaConfig(BaseModel):
    """Configuration for Ollama LLM service integration"""

    service_url: str = Field(default="https://ollama.com", description="Ollama Cloud API URL")
    api_key: Optional[str] = Field(default="f945208978394c218ef31ed075c6c232.ap5HadPbSpSHwURc6anBVAbz", description="API key for Ollama Cloud")
    story_model: str = Field(default="gpt-oss:20b", description="Model name for story generation")
    analysis_model: str = Field(default="gpt-oss:20b", description="Model name for signing analysis")
    timeout_seconds: int = Field(default=60, ge=10, le=300, description="Request timeout in seconds")
    max_tokens: int = Field(default=1000, ge=100, le=4000, description="Maximum tokens for generation")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Generation temperature")
    max_retries: int = Field(default=3, ge=1, le=10, description="Maximum retry attempts")
    enabled: bool = Field(default=True, description="Enable/disable Ollama service")

    @field_validator('story_model', 'analysis_model')
    @classmethod
    def validate_model_name(cls, v):
        """Validate model name is not empty"""
        if not v or not v.strip():
            raise ValueError("Model name cannot be empty")
        return v.strip()


class GestureDetectionConfig(BaseModel):
    """Configuration for gesture detection and analysis"""

    velocity_threshold: float = Field(default=0.02, ge=0.001, le=0.1, description="Minimum hand movement velocity to detect gesture start")
    pause_duration_ms: int = Field(default=1000, ge=500, le=3000, description="Duration of pause to detect gesture end (milliseconds)")
    min_gesture_duration_ms: int = Field(default=500, ge=200, le=2000, description="Minimum gesture duration to be considered valid (milliseconds)")
    landmark_buffer_size: int = Field(default=100, ge=30, le=300, description="Maximum number of landmark frames to buffer during gesture")
    smoothing_window: int = Field(default=5, ge=3, le=15, description="Number of frames for velocity smoothing")
    enabled: bool = Field(default=True, description="Enable/disable gesture detection")

    @field_validator('velocity_threshold')
    @classmethod
    def validate_velocity_threshold(cls, v):
        """Validate velocity threshold is reasonable"""
        if v <= 0:
            raise ValueError("Velocity threshold must be positive")
        return v


class DatabaseConfig(BaseModel):
    """Configuration for TiDB database connection and settings"""

    # Connection settings
    host: str = Field(default="localhost", description="TiDB server host")
    port: int = Field(default=4000, ge=1, le=65535, description="TiDB server port")
    database: str = Field(default="storysign", description="Database name")
    username: str = Field(default="root", description="Database username")
    password: str = Field(default="", description="Database password")
    
    # Connection pool settings
    pool_size: int = Field(default=10, ge=1, le=100, description="Connection pool size")
    max_overflow: int = Field(default=20, ge=0, le=100, description="Maximum pool overflow")
    pool_timeout: int = Field(default=30, ge=5, le=300, description="Pool timeout in seconds")
    pool_recycle: int = Field(default=3600, ge=300, le=86400, description="Pool recycle time in seconds")
    
    # SSL settings
    ssl_disabled: bool = Field(default=True, description="Disable SSL for local development")
    ssl_ca: Optional[str] = Field(default=None, description="SSL CA certificate path")
    ssl_cert: Optional[str] = Field(default=None, description="SSL certificate path")
    ssl_key: Optional[str] = Field(default=None, description="SSL private key path")
    
    # Query settings
    query_timeout: int = Field(default=30, ge=5, le=300, description="Query timeout in seconds")
    echo_queries: bool = Field(default=False, description="Echo SQL queries for debugging")
    
    # Health check settings
    health_check_interval: int = Field(default=30, ge=10, le=300, description="Health check interval in seconds")
    max_retries: int = Field(default=3, ge=1, le=10, description="Maximum connection retry attempts")
    retry_delay: float = Field(default=1.0, ge=0.1, le=10.0, description="Delay between retries in seconds")
    
    @field_validator('host')
    @classmethod
    def validate_host(cls, v):
        """Validate host is not empty"""
        if not v or not v.strip():
            raise ValueError("Database host cannot be empty")
        return v.strip()
    
    @field_validator('database', 'username')
    @classmethod
    def validate_required_fields(cls, v):
        """Validate required fields are not empty"""
        if not v or not v.strip():
            raise ValueError("Database name and username cannot be empty")
        return v.strip()
    
    def get_connection_url(self, async_driver: bool = True) -> str:
        """
        Generate database connection URL
        
        Args:
            async_driver: Whether to use async driver (asyncmy) or sync (pymysql)
            
        Returns:
            Database connection URL
        """
        driver = "mysql+asyncmy" if async_driver else "mysql+pymysql"
        
        # Build connection URL
        url_parts = [f"{driver}://{self.username}"]
        
        if self.password:
            url_parts.append(f":{self.password}")
        
        url_parts.extend([
            f"@{self.host}:{self.port}",
            f"/{self.database}"
        ])
        
        # Add SSL parameter for TiDB Cloud
        if not self.ssl_disabled:
            url_parts.append("?ssl=true")
        
        return "".join(url_parts)
    
    def get_connect_args(self) -> dict:
        """
        Get connection arguments for SQLAlchemy engine
        
        Returns:
            Dictionary of connection arguments
        """
        connect_args = {
            "charset": "utf8mb4",
            "autocommit": False,
        }
        
        # For TiDB Cloud, add SSL configuration that works
        if not self.ssl_disabled:
            connect_args["ssl"] = {
                "ssl_disabled": False,
                "ssl_verify_cert": True,
                "ssl_verify_identity": True,
            }
        
        return connect_args


class CacheConfig(BaseModel):
    """Configuration for Redis caching"""
    
    host: str = Field(default="localhost", description="Redis server host")
    port: int = Field(default=6379, ge=1, le=65535, description="Redis server port")
    db: int = Field(default=0, ge=0, le=15, description="Redis database number")
    password: Optional[str] = Field(default=None, description="Redis password")
    max_connections: int = Field(default=20, ge=1, le=100, description="Maximum Redis connections")
    default_ttl: int = Field(default=3600, ge=60, le=86400, description="Default TTL in seconds")
    key_prefix: str = Field(default="storysign:", description="Cache key prefix")
    enabled: bool = Field(default=True, description="Enable/disable Redis caching")
    
    @field_validator('host')
    @classmethod
    def validate_host(cls, v):
        """Validate host is not empty"""
        if not v or not v.strip():
            raise ValueError("Redis host cannot be empty")
        return v.strip()


class OptimizationConfig(BaseModel):
    """Configuration for database optimization"""
    
    monitoring_interval: int = Field(default=300, ge=60, le=3600, description="Monitoring interval in seconds")
    slow_query_threshold: float = Field(default=1.0, ge=0.1, le=60.0, description="Slow query threshold in seconds")
    max_metrics_history: int = Field(default=10000, ge=1000, le=100000, description="Maximum metrics to keep in memory")
    retention_hours: int = Field(default=24, ge=1, le=168, description="Metric retention in hours")
    auto_optimize: bool = Field(default=True, description="Enable automatic optimization")
    index_recommendations: bool = Field(default=True, description="Enable index recommendations")
    
    # Alert thresholds
    connection_warning_threshold: int = Field(default=50, ge=10, le=1000, description="Connection count warning threshold")
    connection_error_threshold: int = Field(default=80, ge=20, le=1000, description="Connection count error threshold")
    connection_critical_threshold: int = Field(default=100, ge=30, le=1000, description="Connection count critical threshold")
    
    query_time_warning_threshold: float = Field(default=1.0, ge=0.1, le=60.0, description="Query time warning threshold")
    query_time_error_threshold: float = Field(default=5.0, ge=1.0, le=60.0, description="Query time error threshold")
    query_time_critical_threshold: float = Field(default=10.0, ge=5.0, le=60.0, description="Query time critical threshold")


class AppConfig(BaseModel):
    """Main application configuration containing all sub-configurations"""

    video: VideoConfig = Field(default_factory=VideoConfig)
    mediapipe: MediaPipeConfig = Field(default_factory=MediaPipeConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    local_vision: LocalVisionConfig = Field(default_factory=LocalVisionConfig)
    groq: GroqConfig = Field(default_factory=GroqConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    gesture_detection: GestureDetectionConfig = Field(default_factory=GestureDetectionConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    optimization: OptimizationConfig = Field(default_factory=OptimizationConfig)

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

        # Local vision configuration from environment
        if os.getenv('STORYSIGN_LOCAL_VISION__SERVICE_URL'):
            env_vars.setdefault('local_vision', {})['service_url'] = os.getenv('STORYSIGN_LOCAL_VISION__SERVICE_URL')
        if os.getenv('STORYSIGN_LOCAL_VISION__MODEL_NAME'):
            env_vars.setdefault('local_vision', {})['model_name'] = os.getenv('STORYSIGN_LOCAL_VISION__MODEL_NAME')
        if os.getenv('STORYSIGN_LOCAL_VISION__SERVICE_TYPE'):
            env_vars.setdefault('local_vision', {})['service_type'] = os.getenv('STORYSIGN_LOCAL_VISION__SERVICE_TYPE')
        if os.getenv('STORYSIGN_LOCAL_VISION__TIMEOUT_SECONDS'):
            env_vars.setdefault('local_vision', {})['timeout_seconds'] = int(os.getenv('STORYSIGN_LOCAL_VISION__TIMEOUT_SECONDS'))
        if os.getenv('STORYSIGN_LOCAL_VISION__MAX_RETRIES'):
            env_vars.setdefault('local_vision', {})['max_retries'] = int(os.getenv('STORYSIGN_LOCAL_VISION__MAX_RETRIES'))
        if os.getenv('STORYSIGN_LOCAL_VISION__ENABLED'):
            env_vars.setdefault('local_vision', {})['enabled'] = os.getenv('STORYSIGN_LOCAL_VISION__ENABLED').lower() == 'true'

        # Groq configuration from environment
        if os.getenv('GROQ_API_KEY'):
            env_vars.setdefault('groq', {})['api_key'] = os.getenv('GROQ_API_KEY')
        if os.getenv('STORYSIGN_GROQ__API_KEY'):
            env_vars.setdefault('groq', {})['api_key'] = os.getenv('STORYSIGN_GROQ__API_KEY')
        if os.getenv('STORYSIGN_GROQ__BASE_URL'):
            env_vars.setdefault('groq', {})['base_url'] = os.getenv('STORYSIGN_GROQ__BASE_URL')
        if os.getenv('STORYSIGN_GROQ__MODEL_NAME'):
            env_vars.setdefault('groq', {})['model_name'] = os.getenv('STORYSIGN_GROQ__MODEL_NAME')
        if os.getenv('STORYSIGN_GROQ__TIMEOUT_SECONDS'):
            env_vars.setdefault('groq', {})['timeout_seconds'] = int(os.getenv('STORYSIGN_GROQ__TIMEOUT_SECONDS'))
        if os.getenv('STORYSIGN_GROQ__MAX_RETRIES'):
            env_vars.setdefault('groq', {})['max_retries'] = int(os.getenv('STORYSIGN_GROQ__MAX_RETRIES'))
        if os.getenv('STORYSIGN_GROQ__MAX_TOKENS'):
            env_vars.setdefault('groq', {})['max_tokens'] = int(os.getenv('STORYSIGN_GROQ__MAX_TOKENS'))
        if os.getenv('STORYSIGN_GROQ__TEMPERATURE'):
            env_vars.setdefault('groq', {})['temperature'] = float(os.getenv('STORYSIGN_GROQ__TEMPERATURE'))
        if os.getenv('STORYSIGN_GROQ__ENABLED'):
            env_vars.setdefault('groq', {})['enabled'] = os.getenv('STORYSIGN_GROQ__ENABLED').lower() == 'true'

        # Ollama configuration from environment
        if os.getenv('STORYSIGN_OLLAMA__SERVICE_URL'):
            env_vars.setdefault('ollama', {})['service_url'] = os.getenv('STORYSIGN_OLLAMA__SERVICE_URL')
        if os.getenv('STORYSIGN_OLLAMA__STORY_MODEL'):
            env_vars.setdefault('ollama', {})['story_model'] = os.getenv('STORYSIGN_OLLAMA__STORY_MODEL')
        if os.getenv('STORYSIGN_OLLAMA__ANALYSIS_MODEL'):
            env_vars.setdefault('ollama', {})['analysis_model'] = os.getenv('STORYSIGN_OLLAMA__ANALYSIS_MODEL')
        if os.getenv('STORYSIGN_OLLAMA__TIMEOUT_SECONDS'):
            env_vars.setdefault('ollama', {})['timeout_seconds'] = int(os.getenv('STORYSIGN_OLLAMA__TIMEOUT_SECONDS'))
        if os.getenv('STORYSIGN_OLLAMA__MAX_TOKENS'):
            env_vars.setdefault('ollama', {})['max_tokens'] = int(os.getenv('STORYSIGN_OLLAMA__MAX_TOKENS'))
        if os.getenv('STORYSIGN_OLLAMA__TEMPERATURE'):
            env_vars.setdefault('ollama', {})['temperature'] = float(os.getenv('STORYSIGN_OLLAMA__TEMPERATURE'))
        if os.getenv('STORYSIGN_OLLAMA__MAX_RETRIES'):
            env_vars.setdefault('ollama', {})['max_retries'] = int(os.getenv('STORYSIGN_OLLAMA__MAX_RETRIES'))
        if os.getenv('STORYSIGN_OLLAMA__ENABLED'):
            env_vars.setdefault('ollama', {})['enabled'] = os.getenv('STORYSIGN_OLLAMA__ENABLED').lower() == 'true'

        # Gesture detection configuration from environment
        if os.getenv('STORYSIGN_GESTURE_DETECTION__VELOCITY_THRESHOLD'):
            env_vars.setdefault('gesture_detection', {})['velocity_threshold'] = float(os.getenv('STORYSIGN_GESTURE_DETECTION__VELOCITY_THRESHOLD'))
        if os.getenv('STORYSIGN_GESTURE_DETECTION__PAUSE_DURATION_MS'):
            env_vars.setdefault('gesture_detection', {})['pause_duration_ms'] = int(os.getenv('STORYSIGN_GESTURE_DETECTION__PAUSE_DURATION_MS'))
        if os.getenv('STORYSIGN_GESTURE_DETECTION__MIN_GESTURE_DURATION_MS'):
            env_vars.setdefault('gesture_detection', {})['min_gesture_duration_ms'] = int(os.getenv('STORYSIGN_GESTURE_DETECTION__MIN_GESTURE_DURATION_MS'))
        if os.getenv('STORYSIGN_GESTURE_DETECTION__LANDMARK_BUFFER_SIZE'):
            env_vars.setdefault('gesture_detection', {})['landmark_buffer_size'] = int(os.getenv('STORYSIGN_GESTURE_DETECTION__LANDMARK_BUFFER_SIZE'))
        if os.getenv('STORYSIGN_GESTURE_DETECTION__SMOOTHING_WINDOW'):
            env_vars.setdefault('gesture_detection', {})['smoothing_window'] = int(os.getenv('STORYSIGN_GESTURE_DETECTION__SMOOTHING_WINDOW'))
        if os.getenv('STORYSIGN_GESTURE_DETECTION__ENABLED'):
            env_vars.setdefault('gesture_detection', {})['enabled'] = os.getenv('STORYSIGN_GESTURE_DETECTION__ENABLED').lower() == 'true'

        # Database configuration from environment
        if os.getenv('STORYSIGN_DATABASE__HOST'):
            env_vars.setdefault('database', {})['host'] = os.getenv('STORYSIGN_DATABASE__HOST')
        if os.getenv('STORYSIGN_DATABASE__PORT'):
            env_vars.setdefault('database', {})['port'] = int(os.getenv('STORYSIGN_DATABASE__PORT'))
        if os.getenv('STORYSIGN_DATABASE__DATABASE'):
            env_vars.setdefault('database', {})['database'] = os.getenv('STORYSIGN_DATABASE__DATABASE')
        if os.getenv('STORYSIGN_DATABASE__USERNAME'):
            env_vars.setdefault('database', {})['username'] = os.getenv('STORYSIGN_DATABASE__USERNAME')
        if os.getenv('STORYSIGN_DATABASE__PASSWORD'):
            env_vars.setdefault('database', {})['password'] = os.getenv('STORYSIGN_DATABASE__PASSWORD')
        if os.getenv('STORYSIGN_DATABASE__POOL_SIZE'):
            env_vars.setdefault('database', {})['pool_size'] = int(os.getenv('STORYSIGN_DATABASE__POOL_SIZE'))
        if os.getenv('STORYSIGN_DATABASE__MAX_OVERFLOW'):
            env_vars.setdefault('database', {})['max_overflow'] = int(os.getenv('STORYSIGN_DATABASE__MAX_OVERFLOW'))
        if os.getenv('STORYSIGN_DATABASE__POOL_TIMEOUT'):
            env_vars.setdefault('database', {})['pool_timeout'] = int(os.getenv('STORYSIGN_DATABASE__POOL_TIMEOUT'))
        if os.getenv('STORYSIGN_DATABASE__POOL_RECYCLE'):
            env_vars.setdefault('database', {})['pool_recycle'] = int(os.getenv('STORYSIGN_DATABASE__POOL_RECYCLE'))
        if os.getenv('STORYSIGN_DATABASE__SSL_DISABLED'):
            env_vars.setdefault('database', {})['ssl_disabled'] = os.getenv('STORYSIGN_DATABASE__SSL_DISABLED').lower() == 'true'
        if os.getenv('STORYSIGN_DATABASE__SSL_CA'):
            env_vars.setdefault('database', {})['ssl_ca'] = os.getenv('STORYSIGN_DATABASE__SSL_CA')
        if os.getenv('STORYSIGN_DATABASE__SSL_CERT'):
            env_vars.setdefault('database', {})['ssl_cert'] = os.getenv('STORYSIGN_DATABASE__SSL_CERT')
        if os.getenv('STORYSIGN_DATABASE__SSL_KEY'):
            env_vars.setdefault('database', {})['ssl_key'] = os.getenv('STORYSIGN_DATABASE__SSL_KEY')
        if os.getenv('STORYSIGN_DATABASE__QUERY_TIMEOUT'):
            env_vars.setdefault('database', {})['query_timeout'] = int(os.getenv('STORYSIGN_DATABASE__QUERY_TIMEOUT'))
        if os.getenv('STORYSIGN_DATABASE__ECHO_QUERIES'):
            env_vars.setdefault('database', {})['echo_queries'] = os.getenv('STORYSIGN_DATABASE__ECHO_QUERIES').lower() == 'true'
        if os.getenv('STORYSIGN_DATABASE__HEALTH_CHECK_INTERVAL'):
            env_vars.setdefault('database', {})['health_check_interval'] = int(os.getenv('STORYSIGN_DATABASE__HEALTH_CHECK_INTERVAL'))
        if os.getenv('STORYSIGN_DATABASE__MAX_RETRIES'):
            env_vars.setdefault('database', {})['max_retries'] = int(os.getenv('STORYSIGN_DATABASE__MAX_RETRIES'))
        if os.getenv('STORYSIGN_DATABASE__RETRY_DELAY'):
            env_vars.setdefault('database', {})['retry_delay'] = float(os.getenv('STORYSIGN_DATABASE__RETRY_DELAY'))

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
            logger.debug(f"Local vision config: {self._config.local_vision}")
            logger.debug(f"Groq config: enabled={self._config.groq.enabled}, configured={self._config.groq.is_configured()}")
            logger.debug(f"Ollama config: {self._config.ollama}")
            logger.debug(f"Gesture detection config: {self._config.gesture_detection}")
            logger.debug(f"Database config: host={self._config.database.host}, port={self._config.database.port}, database={self._config.database.database}")

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
