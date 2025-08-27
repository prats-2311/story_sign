"""
Database connection management for TiDB
Provides async SQLAlchemy session handling with connection pooling
"""

import asyncio
import logging
from typing import Optional, AsyncGenerator, Dict, Any
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker
)
# Removed QueuePool import as it's not compatible with async engines
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError
from sqlalchemy import text, event
from sqlalchemy.engine import Engine

from config import DatabaseConfig

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Database connection manager for TiDB with async SQLAlchemy
    Handles connection pooling, health checks, and session management
    """
    
    def __init__(self, config: DatabaseConfig):
        """
        Initialize database manager with configuration
        
        Args:
            config: Database configuration object
        """
        self.config = config
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None
        self._is_connected = False
        self._last_health_check: Optional[datetime] = None
        self._health_check_task: Optional[asyncio.Task] = None
        
    async def initialize(self) -> None:
        """
        Initialize database connection and engine
        
        Raises:
            RuntimeError: If database initialization fails
        """
        try:
            logger.info("Initializing database connection...")
            
            # Create async engine with connection pooling
            connection_url = self.config.get_connection_url(async_driver=True)
            
            # Log connection info (without password)
            safe_url = connection_url.replace(f":{self.config.password}@", ":***@") if self.config.password else connection_url
            logger.info(f"Connecting to database: {safe_url}")
            
            # Prepare connect_args for asyncmy driver
            connect_args = {
                "connect_timeout": self.config.query_timeout,
                "charset": "utf8mb4",
                "autocommit": False,
            }
            
            # Add SSL configuration for asyncmy
            if self.config.ssl_disabled:
                connect_args["ssl"] = False
            else:
                ssl_config = {}
                if self.config.ssl_ca:
                    ssl_config["ca"] = self.config.ssl_ca
                if self.config.ssl_cert:
                    ssl_config["cert"] = self.config.ssl_cert
                if self.config.ssl_key:
                    ssl_config["key"] = self.config.ssl_key
                
                if ssl_config:
                    connect_args["ssl"] = ssl_config
            
            self._engine = create_async_engine(
                connection_url,
                pool_size=self.config.pool_size,
                max_overflow=self.config.max_overflow,
                pool_timeout=self.config.pool_timeout,
                pool_recycle=self.config.pool_recycle,
                echo=self.config.echo_queries,
                future=True,
                connect_args=connect_args
            )
            
            # Add connection event listeners for monitoring
            self._setup_event_listeners()
            
            # Create session factory
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False
            )
            
            # Test initial connection
            await self._test_connection()
            
            self._is_connected = True
            
            # Start health check task
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            
            logger.info("Database connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            await self.cleanup()
            raise RuntimeError(f"Database initialization failed: {e}")
    
    def _setup_event_listeners(self) -> None:
        """Setup SQLAlchemy event listeners for connection monitoring"""
        
        @event.listens_for(self._engine.sync_engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            """Handle new database connections"""
            logger.debug("New database connection established")
            
        @event.listens_for(self._engine.sync_engine, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            """Handle connection checkout from pool"""
            logger.debug("Database connection checked out from pool")
            
        @event.listens_for(self._engine.sync_engine, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            """Handle connection checkin to pool"""
            logger.debug("Database connection checked in to pool")
            
        @event.listens_for(self._engine.sync_engine, "invalidate")
        def on_invalidate(dbapi_connection, connection_record, exception):
            """Handle connection invalidation"""
            logger.warning(f"Database connection invalidated: {exception}")
    
    async def _test_connection(self) -> None:
        """
        Test database connection with a simple query
        
        Raises:
            RuntimeError: If connection test fails
        """
        try:
            async with self._engine.begin() as conn:
                result = await conn.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                if row and row.test == 1:
                    logger.debug("Database connection test successful")
                else:
                    raise RuntimeError("Connection test returned unexpected result")
                    
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise RuntimeError(f"Connection test failed: {e}")
    
    async def _health_check_loop(self) -> None:
        """Background task for periodic health checks"""
        while self._is_connected:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                await self._perform_health_check()
                
            except asyncio.CancelledError:
                logger.debug("Health check loop cancelled")
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                # Continue the loop even if individual health check fails
    
    async def _perform_health_check(self) -> Dict[str, Any]:
        """
        Perform database health check
        
        Returns:
            Health check results
        """
        try:
            start_time = datetime.now()
            
            # Test connection with timeout
            async with asyncio.timeout(self.config.query_timeout):
                async with self._engine.begin() as conn:
                    # Simple query to test connection
                    await conn.execute(text("SELECT 1"))
                    
                    # Get connection pool status
                    pool = self._engine.pool
                    pool_status = {
                        "pool_size": pool.size(),
                        "checked_in": pool.checkedin(),
                        "checked_out": pool.checkedout(),
                        "overflow": pool.overflow(),
                        "invalid": pool.invalid()
                    }
            
            response_time = (datetime.now() - start_time).total_seconds()
            self._last_health_check = datetime.now()
            
            health_result = {
                "status": "healthy",
                "response_time_seconds": response_time,
                "last_check": self._last_health_check.isoformat(),
                "pool_status": pool_status
            }
            
            logger.debug(f"Health check successful: {response_time:.3f}s")
            return health_result
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session context manager
        
        Yields:
            AsyncSession: Database session
            
        Raises:
            RuntimeError: If database is not connected
        """
        if not self._is_connected or not self._session_factory:
            raise RuntimeError("Database is not connected")
        
        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()
    
    async def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        fetch_one: bool = False,
        fetch_all: bool = False
    ) -> Any:
        """
        Execute a raw SQL query
        
        Args:
            query: SQL query to execute
            params: Optional query parameters
            fetch_one: Whether to fetch one result
            fetch_all: Whether to fetch all results
            
        Returns:
            Query result based on fetch parameters
            
        Raises:
            RuntimeError: If database is not connected
            SQLAlchemyError: If query execution fails
        """
        if not self._is_connected:
            raise RuntimeError("Database is not connected")
        
        try:
            async with self.get_session() as session:
                result = await session.execute(text(query), params or {})
                
                if fetch_one:
                    return result.fetchone()
                elif fetch_all:
                    return result.fetchall()
                else:
                    return result
                    
        except SQLAlchemyError as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Get current health status
        
        Returns:
            Health check results
        """
        if not self._is_connected:
            return {
                "status": "disconnected",
                "error": "Database manager is not connected"
            }
        
        # Return cached health check if recent
        if (self._last_health_check and 
            datetime.now() - self._last_health_check < timedelta(seconds=30)):
            return {
                "status": "healthy",
                "last_check": self._last_health_check.isoformat(),
                "note": "Using cached health check result"
            }
        
        # Perform fresh health check
        return await self._perform_health_check()
    
    async def cleanup(self) -> None:
        """
        Clean up database connections and resources
        """
        logger.info("Cleaning up database connections...")
        
        self._is_connected = False
        
        # Cancel health check task
        if self._health_check_task and not self._health_check_task.done():
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Close engine and connections
        if self._engine:
            await self._engine.dispose()
            self._engine = None
        
        self._session_factory = None
        self._last_health_check = None
        
        logger.info("Database cleanup completed")
    
    @property
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self._is_connected
    
    @property
    def engine(self) -> Optional[AsyncEngine]:
        """Get the database engine"""
        return self._engine
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get database connection information
        
        Returns:
            Connection information dictionary
        """
        info = {
            "is_connected": self._is_connected,
            "host": self.config.host,
            "port": self.config.port,
            "database": self.config.database,
            "username": self.config.username,
            "pool_size": self.config.pool_size,
            "max_overflow": self.config.max_overflow,
            "last_health_check": self._last_health_check.isoformat() if self._last_health_check else None
        }
        
        if self._engine and self._engine.pool:
            pool = self._engine.pool
            info["pool_status"] = {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            }
        
        return info


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


async def get_database_manager(config: Optional[DatabaseConfig] = None) -> DatabaseManager:
    """
    Get or create global database manager instance
    
    Args:
        config: Optional database configuration
        
    Returns:
        DatabaseManager instance
    """
    global _db_manager
    
    if _db_manager is None:
        if config is None:
            from config import get_config
            app_config = get_config()
            config = app_config.database
        
        _db_manager = DatabaseManager(config)
        await _db_manager.initialize()
    
    return _db_manager


async def cleanup_database_manager() -> None:
    """Clean up global database manager"""
    global _db_manager
    
    if _db_manager:
        await _db_manager.cleanup()
        _db_manager = None


@asynccontextmanager
async def get_db_session(config: Optional[DatabaseConfig] = None) -> AsyncGenerator[AsyncSession, None]:
    """
    Convenience function to get database session
    
    Args:
        config: Optional database configuration
        
    Yields:
        AsyncSession: Database session
    """
    db_manager = await get_database_manager(config)
    async with db_manager.get_session() as session:
        yield session