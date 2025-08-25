"""
Dependency injection container for managing services
Provides service registration, resolution, and lifecycle management
"""

from typing import Dict, Type, Any, Optional, TypeVar, Generic
import logging
from contextlib import asynccontextmanager
import asyncio

from .base_service import BaseService

T = TypeVar('T', bound=BaseService)


class ServiceContainer:
    """
    Dependency injection container for managing platform services
    """
    
    def __init__(self):
        self._services: Dict[str, BaseService] = {}
        self._service_types: Dict[str, Type[BaseService]] = {}
        self._service_configs: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger("core.ServiceContainer")
        self._initialization_lock = asyncio.Lock()
        
    def register_service(
        self, 
        service_type: Type[T], 
        service_name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        singleton: bool = True
    ) -> None:
        """
        Register a service type with the container
        
        Args:
            service_type: The service class to register
            service_name: Optional service name (defaults to class name)
            config: Optional configuration for the service
            singleton: Whether to create a singleton instance
        """
        name = service_name or service_type.__name__
        
        if name in self._service_types:
            self.logger.warning(f"Service {name} is already registered, overwriting")
            
        self._service_types[name] = service_type
        self._service_configs[name] = config or {}
        
        self.logger.info(f"Registered service: {name} ({service_type.__name__})")
    
    async def get_service(self, service_name: str) -> BaseService:
        """
        Get a service instance by name
        Creates and initializes the service if it doesn't exist
        
        Args:
            service_name: Name of the service to retrieve
            
        Returns:
            The service instance
            
        Raises:
            ValueError: If service is not registered
        """
        if service_name not in self._service_types:
            raise ValueError(f"Service {service_name} is not registered")
            
        # Return existing instance if available
        if service_name in self._services:
            return self._services[service_name]
            
        # Create and initialize new instance
        async with self._initialization_lock:
            # Double-check pattern
            if service_name in self._services:
                return self._services[service_name]
                
            service_type = self._service_types[service_name]
            service_config = self._service_configs[service_name]
            
            # Create service instance
            service = service_type(service_name, service_config)
            
            # Initialize the service
            await service.start()
            
            # Store in container
            self._services[service_name] = service
            
            self.logger.info(f"Created and initialized service: {service_name}")
            return service
    
    async def get_service_typed(self, service_type: Type[T]) -> T:
        """
        Get a service instance by type
        
        Args:
            service_type: The service class type
            
        Returns:
            The service instance cast to the correct type
        """
        service_name = service_type.__name__
        service = await self.get_service(service_name)
        return service  # type: ignore
    
    def is_service_registered(self, service_name: str) -> bool:
        """
        Check if a service is registered
        """
        return service_name in self._service_types
    
    def is_service_initialized(self, service_name: str) -> bool:
        """
        Check if a service is initialized
        """
        return service_name in self._services and self._services[service_name].is_initialized
    
    async def initialize_all_services(self) -> None:
        """
        Initialize all registered services
        """
        self.logger.info("Initializing all registered services")
        
        for service_name in self._service_types.keys():
            try:
                await self.get_service(service_name)
            except Exception as e:
                self.logger.error(f"Failed to initialize service {service_name}: {e}")
                raise
                
        self.logger.info("All services initialized successfully")
    
    async def shutdown_all_services(self) -> None:
        """
        Shutdown all initialized services
        """
        self.logger.info("Shutting down all services")
        
        # Shutdown in reverse order of initialization
        service_names = list(self._services.keys())
        service_names.reverse()
        
        for service_name in service_names:
            try:
                service = self._services[service_name]
                await service.stop()
            except Exception as e:
                self.logger.error(f"Failed to shutdown service {service_name}: {e}")
                
        # Clear all services
        self._services.clear()
        self.logger.info("All services shut down")
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get status of all services
        """
        return {
            "registered_services": list(self._service_types.keys()),
            "initialized_services": [
                name for name, service in self._services.items() 
                if service.is_initialized
            ],
            "service_details": {
                name: service.get_status() 
                for name, service in self._services.items()
            }
        }
    
    @asynccontextmanager
    async def service_lifecycle(self):
        """
        Context manager for service lifecycle management
        """
        try:
            await self.initialize_all_services()
            yield self
        finally:
            await self.shutdown_all_services()


# Global service container instance
_service_container: Optional[ServiceContainer] = None


def get_service_container() -> ServiceContainer:
    """
    Get the global service container instance
    """
    global _service_container
    if _service_container is None:
        _service_container = ServiceContainer()
    return _service_container


async def get_service(service_name: str) -> BaseService:
    """
    Convenience function to get a service from the global container
    """
    container = get_service_container()
    return await container.get_service(service_name)


async def get_service_typed(service_type: Type[T]) -> T:
    """
    Convenience function to get a typed service from the global container
    """
    container = get_service_container()
    return await container.get_service_typed(service_type)