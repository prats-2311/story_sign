"""
Base service class for all platform services
Provides common functionality and lifecycle management
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from datetime import datetime


class BaseService(ABC):
    """
    Abstract base class for all platform services
    Provides common functionality and lifecycle management
    """
    
    def __init__(self, service_name: str, config: Optional[Dict[str, Any]] = None):
        self.service_name = service_name
        self.config = config or {}
        self.logger = logging.getLogger(f"services.{service_name}")
        self.is_initialized = False
        self.initialization_time: Optional[datetime] = None
        
    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the service
        Must be implemented by all services
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """
        Clean up service resources
        Must be implemented by all services
        """
        pass
    
    async def start(self) -> None:
        """
        Start the service (calls initialize and marks as initialized)
        """
        if self.is_initialized:
            self.logger.warning(f"Service {self.service_name} is already initialized")
            return
            
        try:
            await self.initialize()
            self.is_initialized = True
            self.initialization_time = datetime.utcnow()
            self.logger.info(f"Service {self.service_name} initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize service {self.service_name}: {e}")
            raise
    
    async def stop(self) -> None:
        """
        Stop the service (calls cleanup and marks as uninitialized)
        """
        if not self.is_initialized:
            self.logger.warning(f"Service {self.service_name} is not initialized")
            return
            
        try:
            await self.cleanup()
            self.is_initialized = False
            self.initialization_time = None
            self.logger.info(f"Service {self.service_name} stopped successfully")
        except Exception as e:
            self.logger.error(f"Failed to stop service {self.service_name}: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get service status information
        """
        return {
            "service_name": self.service_name,
            "is_initialized": self.is_initialized,
            "initialization_time": self.initialization_time.isoformat() if self.initialization_time else None,
            "config_keys": list(self.config.keys()) if self.config else []
        }
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        Update service configuration
        """
        self.config.update(new_config)
        self.logger.info(f"Configuration updated for service {self.service_name}")