"""
Service registry for registering and configuring all platform services
"""

from typing import Dict, Any
import logging

from .service_container import ServiceContainer
from .config_service import ConfigService
from .database_service import DatabaseService
from services.user_service import UserService
from services.content_service import ContentService
from services.session_service import SessionService
from services.analytics_service import AnalyticsService


logger = logging.getLogger(__name__)


def register_core_services(container: ServiceContainer, app_config: Any = None) -> None:
    """
    Register all core platform services with the container
    
    Args:
        container: Service container instance
        app_config: Application configuration object
    """
    logger.info("Registering core platform services")
    
    # Register configuration service
    config_service_config = {
        "config_file": "config.yaml"
    }
    if app_config:
        # Extract relevant config sections for services
        config_service_config.update({
            "database": getattr(app_config, 'database', {}),
            "redis": getattr(app_config, 'redis', {}),
            "services": getattr(app_config, 'services', {})
        })
    
    container.register_service(
        ConfigService,
        config=config_service_config
    )
    
    # Register database service
    database_config = {}
    if app_config and hasattr(app_config, 'database'):
        database_config = {"database": app_config.database}
    
    container.register_service(
        DatabaseService,
        config=database_config
    )
    
    # Register business logic services
    container.register_service(UserService)
    container.register_service(ContentService)
    container.register_service(SessionService)
    container.register_service(AnalyticsService)
    
    logger.info("Core services registered successfully")


def get_service_health_status(container: ServiceContainer) -> Dict[str, Any]:
    """
    Get health status of all registered services
    
    Args:
        container: Service container instance
        
    Returns:
        Health status information
    """
    try:
        status = container.get_service_status()
        
        # Add additional health checks
        health_status = {
            "overall_status": "healthy" if len(status["initialized_services"]) > 0 else "unhealthy",
            "services": status,
            "timestamp": "2024-01-01T00:00:00Z"  # TODO: Use actual timestamp
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Failed to get service health status: {e}")
        return {
            "overall_status": "unhealthy",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }


async def initialize_platform_services(app_config: Any = None) -> ServiceContainer:
    """
    Initialize all platform services
    
    Args:
        app_config: Application configuration object
        
    Returns:
        Initialized service container
    """
    logger.info("Initializing platform services")
    
    try:
        # Get or create service container
        from .service_container import get_service_container
        container = get_service_container()
        
        # Register all services
        register_core_services(container, app_config)
        
        # Initialize all services
        await container.initialize_all_services()
        
        logger.info("Platform services initialized successfully")
        return container
        
    except Exception as e:
        logger.error(f"Failed to initialize platform services: {e}")
        raise


async def shutdown_platform_services(container: ServiceContainer) -> None:
    """
    Shutdown all platform services
    
    Args:
        container: Service container instance
    """
    logger.info("Shutting down platform services")
    
    try:
        await container.shutdown_all_services()
        logger.info("Platform services shut down successfully")
        
    except Exception as e:
        logger.error(f"Failed to shutdown platform services: {e}")
        raise