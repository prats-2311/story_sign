"""
Database service for managing database connections and operations
Provides async database operations with connection pooling using TiDB
"""

from typing import Dict, Any, Optional, AsyncGenerator
import logging
from contextlib import asynccontextmanager

from .base_service import BaseService
from config import DatabaseConfig, get_config

# Optional imports for database functionality
try:
    from sqlalchemy.ext.asyncio import AsyncSession
    from .db import DatabaseManager, get_database_manager
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    AsyncSession = None
    DatabaseManager = None
    get_database_manager = None
    SQLALCHEMY_AVAILABLE = False


class DatabaseService(BaseService):
    """
    Service for managing database connections and operations
    Integrates with TiDB using SQLAlchemy async sessions
    """
    
    def __init__(self, service_name: str = "DatabaseService", config: Optional[Dict[str, Any]] = None):
        super().__init__(service_name, config)
        self._db_manager: Optional[DatabaseManager] = None
        self._db_config: Optional[DatabaseConfig] = None
        
    async def initialize(self) -> None:
        """
        Initialize database service and connection pool
        """
        if not SQLALCHEMY_AVAILABLE:
            self.logger.warning("SQLAlchemy not available - database service running in mock mode")
            self.logger.info("To enable full database functionality, install: pip install sqlalchemy[asyncio] asyncmy pymysql")
            return
        
        try:
            # Get database configuration
            if self.config and "database" in self.config:
                # Use provided database config
                db_config_dict = self.config["database"]
                self._db_config = DatabaseConfig(**db_config_dict)
            else:
                # Use global configuration
                app_config = get_config()
                self._db_config = app_config.database
            
            self.logger.info(f"Initializing database service with TiDB at {self._db_config.host}:{self._db_config.port}")
            
            # Initialize database manager
            self._db_manager = await get_database_manager(self._db_config)
            
            self.logger.info("Database service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database service: {e}")
            raise RuntimeError(f"Database service initialization failed: {e}")
    
    async def cleanup(self) -> None:
        """
        Clean up database connections
        """
        if self._db_manager:
            await self._db_manager.cleanup()
            self._db_manager = None
            
        self.logger.info("Database service cleaned up")
    
    def is_connected(self) -> bool:
        """
        Check if database is connected
        """
        if not SQLALCHEMY_AVAILABLE:
            return False
        return self._db_manager is not None and self._db_manager.is_connected
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[Any, None]:
        """
        Get database session context manager
        
        Yields:
            AsyncSession: SQLAlchemy async session (or mock session if SQLAlchemy not available)
            
        Raises:
            RuntimeError: If database service is not initialized
        """
        if not SQLALCHEMY_AVAILABLE:
            # Provide mock session for compatibility
            mock_session = {"mock": True, "note": "SQLAlchemy not available"}
            yield mock_session
            return
            
        if not self._db_manager:
            raise RuntimeError("Database service is not initialized")
            
        async with self._db_manager.get_session() as session:
            yield session
    
    async def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        fetch_one: bool = False,
        fetch_all: bool = False
    ) -> Any:
        """
        Execute a database query
        
        Args:
            query: SQL query to execute
            params: Optional query parameters
            fetch_one: Whether to fetch one result
            fetch_all: Whether to fetch all results
            
        Returns:
            Query result based on fetch parameters
            
        Raises:
            RuntimeError: If database service is not initialized
        """
        if not SQLALCHEMY_AVAILABLE:
            self.logger.warning("Database query attempted but SQLAlchemy not available")
            return {"mock": True, "query": query, "params": params}
            
        if not self._db_manager:
            raise RuntimeError("Database service is not initialized")
            
        self.logger.debug(f"Executing query: {query[:100]}...")
        
        return await self._db_manager.execute_query(
            query=query,
            params=params,
            fetch_one=fetch_one,
            fetch_all=fetch_all
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform database health check
        
        Returns:
            Health check results
        """
        try:
            if not SQLALCHEMY_AVAILABLE:
                return {
                    "status": "mock",
                    "note": "SQLAlchemy not available - running in mock mode",
                    "suggestion": "Install database dependencies: pip install sqlalchemy[asyncio] asyncmy pymysql"
                }
                
            if not self._db_manager:
                return {
                    "status": "unhealthy",
                    "error": "Database service is not initialized"
                }
            
            return await self._db_manager.health_check()
            
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get database connection information
        """
        if not SQLALCHEMY_AVAILABLE:
            return {
                "is_connected": False,
                "status": "mock_mode",
                "note": "SQLAlchemy not available",
                "suggestion": "Install: pip install sqlalchemy[asyncio] asyncmy pymysql"
            }
            
        if not self._db_manager:
            return {
                "is_connected": False,
                "error": "Database service is not initialized"
            }
        
        return self._db_manager.get_connection_info()
    
    async def create_tables(self) -> None:
        """
        Create database tables (placeholder for future schema creation)
        This will be implemented when we add SQLAlchemy models
        """
        self.logger.info("Table creation will be implemented with SQLAlchemy models")
        # TODO: Implement table creation when models are added
        pass
    
    async def migrate_schema(self) -> None:
        """
        Migrate database schema (placeholder for future migrations)
        This will be implemented with Alembic or similar migration tool
        """
        self.logger.info("Schema migration will be implemented with migration tools")
        # TODO: Implement schema migrations
        pass