"""
Redis caching service for StorySign platform
Provides distributed caching with Redis for improved performance
"""

import json
import logging
import asyncio
from typing import Any, Dict, Optional, Union, List
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

try:
    import redis.asyncio as redis
    from redis.asyncio import Redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    Redis = None
    REDIS_AVAILABLE = False

from .base_service import BaseService


class CacheService(BaseService):
    """
    Redis-based caching service for improved database performance
    Provides async caching operations with automatic serialization
    """
    
    def __init__(self, service_name: str = "CacheService", config: Optional[Dict[str, Any]] = None):
        super().__init__(service_name, config)
        self._redis_client: Optional[Redis] = None
        self._connection_pool: Optional[redis.ConnectionPool] = None
        self._is_connected = False
        
        # Default cache configuration
        self.default_ttl = 3600  # 1 hour default TTL
        self.key_prefix = "storysign:"
        
        # Cache configuration from config
        if self.config:
            cache_config = self.config.get("cache", {})
            self.redis_host = cache_config.get("host", "localhost")
            self.redis_port = cache_config.get("port", 6379)
            self.redis_db = cache_config.get("db", 0)
            self.redis_password = cache_config.get("password", None)
            self.max_connections = cache_config.get("max_connections", 20)
            self.default_ttl = cache_config.get("default_ttl", 3600)
            self.key_prefix = cache_config.get("key_prefix", "storysign:")
        else:
            self.redis_host = "localhost"
            self.redis_port = 6379
            self.redis_db = 0
            self.redis_password = None
            self.max_connections = 20
    
    async def initialize(self) -> None:
        """
        Initialize Redis connection and connection pool
        """
        if not REDIS_AVAILABLE:
            self.logger.warning("Redis not available - cache service running in mock mode")
            self.logger.info("To enable Redis caching, install: pip install redis[hiredis]")
            return
        
        try:
            self.logger.info(f"Initializing Redis cache service at {self.redis_host}:{self.redis_port}")
            
            # Create connection pool
            self._connection_pool = redis.ConnectionPool(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                password=self.redis_password,
                max_connections=self.max_connections,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Create Redis client
            self._redis_client = Redis(connection_pool=self._connection_pool)
            
            # Test connection
            await self._test_connection()
            
            self._is_connected = True
            self.logger.info("Redis cache service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Redis cache service: {e}")
            self.logger.warning("Cache service will run in mock mode")
            # Don't raise exception - allow service to run without Redis
    
    async def _test_connection(self) -> None:
        """
        Test Redis connection
        
        Raises:
            RuntimeError: If connection test fails
        """
        if not self._redis_client:
            raise RuntimeError("Redis client not initialized")
        
        try:
            await self._redis_client.ping()
            self.logger.debug("Redis connection test successful")
        except Exception as e:
            raise RuntimeError(f"Redis connection test failed: {e}")
    
    async def cleanup(self) -> None:
        """
        Clean up Redis connections
        """
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None
        
        if self._connection_pool:
            await self._connection_pool.disconnect()
            self._connection_pool = None
        
        self._is_connected = False
        self.logger.info("Redis cache service cleaned up")
    
    def _make_key(self, key: str) -> str:
        """
        Create prefixed cache key
        
        Args:
            key: Base key name
            
        Returns:
            Prefixed key
        """
        return f"{self.key_prefix}{key}"
    
    def _serialize_value(self, value: Any) -> str:
        """
        Serialize value for Redis storage
        
        Args:
            value: Value to serialize
            
        Returns:
            Serialized string
        """
        if isinstance(value, (str, int, float, bool)):
            return json.dumps({"type": type(value).__name__, "value": value})
        else:
            return json.dumps({"type": "json", "value": value})
    
    def _deserialize_value(self, serialized: str) -> Any:
        """
        Deserialize value from Redis storage
        
        Args:
            serialized: Serialized string
            
        Returns:
            Deserialized value
        """
        try:
            data = json.loads(serialized)
            value_type = data.get("type", "json")
            value = data.get("value")
            
            if value_type == "str":
                return str(value)
            elif value_type == "int":
                return int(value)
            elif value_type == "float":
                return float(value)
            elif value_type == "bool":
                return bool(value)
            else:
                return value
        except (json.JSONDecodeError, KeyError):
            # Fallback for simple string values
            return serialized
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        if not REDIS_AVAILABLE or not self._is_connected:
            self.logger.debug(f"Cache miss (Redis unavailable): {key}")
            return default
        
        try:
            cache_key = self._make_key(key)
            serialized = await self._redis_client.get(cache_key)
            
            if serialized is None:
                self.logger.debug(f"Cache miss: {key}")
                return default
            
            value = self._deserialize_value(serialized)
            self.logger.debug(f"Cache hit: {key}")
            return value
            
        except Exception as e:
            self.logger.error(f"Cache get error for key {key}: {e}")
            return default
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None for default TTL)
            nx: Only set if key doesn't exist
            xx: Only set if key exists
            
        Returns:
            True if value was set, False otherwise
        """
        if not REDIS_AVAILABLE or not self._is_connected:
            self.logger.debug(f"Cache set skipped (Redis unavailable): {key}")
            return False
        
        try:
            cache_key = self._make_key(key)
            serialized = self._serialize_value(value)
            ttl_seconds = ttl or self.default_ttl
            
            result = await self._redis_client.set(
                cache_key,
                serialized,
                ex=ttl_seconds,
                nx=nx,
                xx=xx
            )
            
            if result:
                self.logger.debug(f"Cache set: {key} (TTL: {ttl_seconds}s)")
            else:
                self.logger.debug(f"Cache set failed: {key}")
            
            return bool(result)
            
        except Exception as e:
            self.logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted, False otherwise
        """
        if not REDIS_AVAILABLE or not self._is_connected:
            return False
        
        try:
            cache_key = self._make_key(key)
            result = await self._redis_client.delete(cache_key)
            
            if result:
                self.logger.debug(f"Cache delete: {key}")
            
            return bool(result)
            
        except Exception as e:
            self.logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists, False otherwise
        """
        if not REDIS_AVAILABLE or not self._is_connected:
            return False
        
        try:
            cache_key = self._make_key(key)
            result = await self._redis_client.exists(cache_key)
            return bool(result)
            
        except Exception as e:
            self.logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration time for key
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
            
        Returns:
            True if expiration was set, False otherwise
        """
        if not REDIS_AVAILABLE or not self._is_connected:
            return False
        
        try:
            cache_key = self._make_key(key)
            result = await self._redis_client.expire(cache_key, ttl)
            return bool(result)
            
        except Exception as e:
            self.logger.error(f"Cache expire error for key {key}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment numeric value in cache
        
        Args:
            key: Cache key
            amount: Amount to increment by
            
        Returns:
            New value after increment, or None if error
        """
        if not REDIS_AVAILABLE or not self._is_connected:
            return None
        
        try:
            cache_key = self._make_key(key)
            result = await self._redis_client.incrby(cache_key, amount)
            return int(result)
            
        except Exception as e:
            self.logger.error(f"Cache increment error for key {key}: {e}")
            return None
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple values from cache
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dictionary of key-value pairs
        """
        if not REDIS_AVAILABLE or not self._is_connected:
            return {}
        
        try:
            cache_keys = [self._make_key(key) for key in keys]
            values = await self._redis_client.mget(cache_keys)
            
            result = {}
            for i, (original_key, serialized) in enumerate(zip(keys, values)):
                if serialized is not None:
                    result[original_key] = self._deserialize_value(serialized)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Cache get_many error: {e}")
            return {}
    
    async def set_many(
        self,
        mapping: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set multiple values in cache
        
        Args:
            mapping: Dictionary of key-value pairs
            ttl: Time to live in seconds
            
        Returns:
            True if all values were set, False otherwise
        """
        if not REDIS_AVAILABLE or not self._is_connected:
            return False
        
        try:
            # Prepare data for mset
            cache_mapping = {}
            for key, value in mapping.items():
                cache_key = self._make_key(key)
                cache_mapping[cache_key] = self._serialize_value(value)
            
            # Set all values
            await self._redis_client.mset(cache_mapping)
            
            # Set TTL for all keys if specified
            if ttl:
                ttl_seconds = ttl or self.default_ttl
                for cache_key in cache_mapping.keys():
                    await self._redis_client.expire(cache_key, ttl_seconds)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Cache set_many error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern
        
        Args:
            pattern: Key pattern (supports wildcards)
            
        Returns:
            Number of keys deleted
        """
        if not REDIS_AVAILABLE or not self._is_connected:
            return 0
        
        try:
            cache_pattern = self._make_key(pattern)
            keys = await self._redis_client.keys(cache_pattern)
            
            if keys:
                deleted = await self._redis_client.delete(*keys)
                self.logger.info(f"Cleared {deleted} cache keys matching pattern: {pattern}")
                return deleted
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Cache clear_pattern error for pattern {pattern}: {e}")
            return 0
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform cache service health check
        
        Returns:
            Health check results
        """
        if not REDIS_AVAILABLE:
            return {
                "status": "mock",
                "note": "Redis not available - running in mock mode",
                "suggestion": "Install Redis dependencies: pip install redis[hiredis]"
            }
        
        if not self._is_connected:
            return {
                "status": "disconnected",
                "error": "Redis cache service is not connected"
            }
        
        try:
            # Test basic operations
            start_time = datetime.now()
            await self._redis_client.ping()
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Get Redis info
            info = await self._redis_client.info()
            
            return {
                "status": "healthy",
                "response_time_seconds": response_time,
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def is_connected(self) -> bool:
        """Check if cache service is connected"""
        return REDIS_AVAILABLE and self._is_connected


# Cache decorators for easy use
def cache_result(key_template: str, ttl: int = 3600):
    """
    Decorator to cache function results
    
    Args:
        key_template: Cache key template (can use function args)
        ttl: Time to live in seconds
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get cache service from service container
            from .service_container import get_service
            cache_service = get_service("CacheService")
            
            if not cache_service or not cache_service.is_connected():
                # No caching available, call function directly
                return await func(*args, **kwargs)
            
            # Generate cache key
            try:
                cache_key = key_template.format(*args, **kwargs)
            except (IndexError, KeyError):
                # Fallback to function name if template fails
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            await cache_service.set(cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator


# Global cache service instance
_cache_service: Optional[CacheService] = None


async def get_cache_service(config: Optional[Dict[str, Any]] = None) -> CacheService:
    """
    Get or create global cache service instance
    
    Args:
        config: Optional cache configuration
        
    Returns:
        CacheService instance
    """
    global _cache_service
    
    if _cache_service is None:
        _cache_service = CacheService(config=config)
        await _cache_service.initialize()
    
    return _cache_service


async def cleanup_cache_service() -> None:
    """Clean up global cache service"""
    global _cache_service
    
    if _cache_service:
        await _cache_service.cleanup()
        _cache_service = None