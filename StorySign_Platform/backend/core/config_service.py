"""
Configuration service for managing modular service configurations
Provides centralized configuration management with environment overrides
"""

from typing import Dict, Any, Optional, Union
import os
import yaml
import json
from pathlib import Path

from .base_service import BaseService


class ConfigService(BaseService):
    """
    Service for managing application configuration
    Supports YAML, JSON, and environment variable overrides
    """
    
    def __init__(self, service_name: str = "ConfigService", config: Optional[Dict[str, Any]] = None):
        super().__init__(service_name, config)
        self._config_data: Dict[str, Any] = {}
        self._config_file_path: Optional[Path] = None
        
    async def initialize(self) -> None:
        """
        Initialize the configuration service
        """
        # Load configuration from file if specified
        config_file = self.config.get("config_file", "config.yaml")
        if config_file:
            await self.load_config_file(config_file)
            
        # Apply environment variable overrides
        self._apply_environment_overrides()
        
        self.logger.info(f"Configuration service initialized with {len(self._config_data)} config sections")
    
    async def cleanup(self) -> None:
        """
        Clean up configuration service
        """
        self._config_data.clear()
        self._config_file_path = None
        
    async def load_config_file(self, file_path: Union[str, Path]) -> None:
        """
        Load configuration from a file (YAML or JSON)
        
        Args:
            file_path: Path to the configuration file
        """
        file_path = Path(file_path)
        self._config_file_path = file_path
        
        if not file_path.exists():
            self.logger.warning(f"Configuration file not found: {file_path}")
            return
            
        try:
            with open(file_path, 'r') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    self._config_data = yaml.safe_load(f) or {}
                elif file_path.suffix.lower() == '.json':
                    self._config_data = json.load(f)
                else:
                    raise ValueError(f"Unsupported configuration file format: {file_path.suffix}")
                    
            self.logger.info(f"Loaded configuration from {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration file {file_path}: {e}")
            raise
    
    def _apply_environment_overrides(self) -> None:
        """
        Apply environment variable overrides to configuration
        Environment variables in format: STORYSIGN_SECTION_KEY=value
        """
        env_prefix = "STORYSIGN_"
        overrides_applied = 0
        
        for env_key, env_value in os.environ.items():
            if not env_key.startswith(env_prefix):
                continue
                
            # Parse environment variable key
            config_path = env_key[len(env_prefix):].lower().split('_')
            
            if len(config_path) < 2:
                continue
                
            # Apply override to configuration
            try:
                self._set_nested_config(config_path, self._parse_env_value(env_value))
                overrides_applied += 1
                self.logger.debug(f"Applied environment override: {env_key} = {env_value}")
            except Exception as e:
                self.logger.warning(f"Failed to apply environment override {env_key}: {e}")
                
        if overrides_applied > 0:
            self.logger.info(f"Applied {overrides_applied} environment variable overrides")
    
    def _set_nested_config(self, path: list, value: Any) -> None:
        """
        Set a nested configuration value using a path list
        
        Args:
            path: List of keys representing the nested path
            value: Value to set
        """
        current = self._config_data
        
        # Navigate to the parent of the target key
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
            
        # Set the final value
        current[path[-1]] = value
    
    def _parse_env_value(self, value: str) -> Any:
        """
        Parse environment variable value to appropriate type
        
        Args:
            value: String value from environment variable
            
        Returns:
            Parsed value (bool, int, float, or string)
        """
        # Try boolean
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'
            
        # Try integer
        try:
            return int(value)
        except ValueError:
            pass
            
        # Try float
        try:
            return float(value)
        except ValueError:
            pass
            
        # Try JSON
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            pass
            
        # Return as string
        return value
    
    def get_config(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            section: Configuration section name
            key: Optional key within the section
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        if section not in self._config_data:
            return default
            
        section_data = self._config_data[section]
        
        if key is None:
            return section_data
            
        return section_data.get(key, default)
    
    def set_config(self, section: str, key: str, value: Any) -> None:
        """
        Set configuration value
        
        Args:
            section: Configuration section name
            key: Key within the section
            value: Value to set
        """
        if section not in self._config_data:
            self._config_data[section] = {}
            
        self._config_data[section][key] = value
        self.logger.debug(f"Set configuration: {section}.{key} = {value}")
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific service
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service configuration dictionary
        """
        return self.get_config("services", service_name, {})
    
    def get_database_config(self) -> Dict[str, Any]:
        """
        Get database configuration
        """
        return self.get_config("database", default={})
    
    def get_redis_config(self) -> Dict[str, Any]:
        """
        Get Redis configuration
        """
        return self.get_config("redis", default={})
    
    def get_all_config(self) -> Dict[str, Any]:
        """
        Get all configuration data
        """
        return self._config_data.copy()
    
    def reload_config(self) -> None:
        """
        Reload configuration from file
        """
        if self._config_file_path:
            asyncio.create_task(self.load_config_file(self._config_file_path))
            self._apply_environment_overrides()
            self.logger.info("Configuration reloaded")