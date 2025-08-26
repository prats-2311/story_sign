"""
Core services package for StorySign Platform
Provides shared services and dependency injection infrastructure
"""

from .service_container import ServiceContainer, get_service_container
from .base_service import BaseService
from .config_service import ConfigService

# Optional database service import
try:
    from .database_service import DatabaseService
    DATABASE_SERVICE_AVAILABLE = True
except ImportError:
    DatabaseService = None
    DATABASE_SERVICE_AVAILABLE = False

__all__ = [
    "ServiceContainer",
    "get_service_container", 
    "BaseService",
    "ConfigService",
]

# Add DatabaseService to exports only if available
if DATABASE_SERVICE_AVAILABLE:
    __all__.append("DatabaseService")