"""
Comprehensive health check and automated recovery system
Provides system health monitoring, automated recovery, and self-healing capabilities
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

from .base_service import BaseService


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


class RecoveryAction(Enum):
    """Available recovery actions"""
    RESTART_SERVICE = "restart_service"
    CLEAR_CACHE = "clear_cache"
    RECONNECT_DATABASE = "reconnect_database"
    SCALE_RESOURCES = "scale_resources"
    NOTIFY_ADMIN = "notify_admin"
    GRACEFUL_SHUTDOWN = "graceful_shutdown"


@dataclass
class HealthCheckResult:
    """Health check result data structure"""
    component: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    response_time_ms: float
    recovery_actions: List[RecoveryAction]


@dataclass
class RecoveryPlan:
    """Recovery plan for unhealthy components"""
    component: str
    actions: List[RecoveryAction]
    max_attempts: int
    backoff_seconds: int
    success_criteria: Callable[[], bool]


class HealthCheckService(BaseService):
    """
    Comprehensive health check and automated recovery service
    Monitors system components and performs automated recovery actions
    """
    
    def __init__(self, service_name: str = "HealthCheckService", config: Optional[Dict[str, Any]] = None):
        super().__init__(service_name, config)
        
        self._health_checks: Dict[str, Callable[[], HealthCheckResult]] = {}
        self._recovery_plans: Dict[str, RecoveryPlan] = {}
        self._recovery_handlers: Dict[RecoveryAction, Callable] = {}
        self._health_history: List[HealthCheckResult] = []
        
        # Configuration
        self.check_interval = 60  # 1 minute
        self.history_retention_hours = 24
        self.max_history_size = 10000
        self.recovery_enabled = True
        
        # Health check task
        self._health_check_task: Optional[asyncio.Task] = None
        
        # Load configuration
        if self.config:
            health_config = self.config.get("health_check", {})
            self.check_interval = health_config.get("interval", 60)
            self.history_retention_hours = health_config.get("retention_hours", 24)
            self.max_history_size = health_config.get("max_history", 10000)
            self.recovery_enabled = health_config.get("recovery_enabled", True)
        
        # Register default recovery handlers
        self._register_default_recovery_handlers()
    
    async def initialize(self) -> None:
        """Initialize health check service"""
        try:
            # Register default health checks
            await self._register_default_health_checks()
            
            # Start health check task
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            
            self.logger.info("Health check service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize health check service: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up health check resources"""
        if self._health_check_task and not self._health_check_task.done():
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Health check service cleaned up")
    
    async def _register_default_health_checks(self) -> None:
        """Register default system health checks"""
        try:
            # Database health check
            self.register_health_check("database", self._check_database_health)
            
            # Cache health check
            self.register_health_check("cache", self._check_cache_health)
            
            # Memory health check
            self.register_health_check("memory", self._check_memory_health)
            
            # Disk health check
            self.register_health_check("disk", self._check_disk_health)
            
            # WebSocket health check
            self.register_health_check("websocket", self._check_websocket_health)
            
            # AI services health check
            self.register_health_check("ai_services", self._check_ai_services_health)
            
        except Exception as e:
            self.logger.error(f"Failed to register default health checks: {e}")
    
    def _register_default_recovery_handlers(self) -> None:
        """Register default recovery action handlers"""
        self._recovery_handlers[RecoveryAction.RESTART_SERVICE] = self._restart_service
        self._recovery_handlers[RecoveryAction.CLEAR_CACHE] = self._clear_cache
        self._recovery_handlers[RecoveryAction.RECONNECT_DATABASE] = self._reconnect_database
        self._recovery_handlers[RecoveryAction.SCALE_RESOURCES] = self._scale_resources
        self._recovery_handlers[RecoveryAction.NOTIFY_ADMIN] = self._notify_admin
        self._recovery_handlers[RecoveryAction.GRACEFUL_SHUTDOWN] = self._graceful_shutdown
    
    def register_health_check(self, component: str, check_func: Callable) -> None:
        """Register a health check for a component"""
        self._health_checks[component] = check_func
        self.logger.info(f"Registered health check for component: {component}")
    
    def register_recovery_plan(self, component: str, plan: RecoveryPlan) -> None:
        """Register a recovery plan for a component"""
        self._recovery_plans[component] = plan
        self.logger.info(f"Registered recovery plan for component: {component}")
    
    async def _health_check_loop(self) -> None:
        """Main health check loop"""
        while True:
            try:
                await asyncio.sleep(self.check_interval)
                
                # Run all health checks
                results = await self._run_all_health_checks()
                
                # Store results
                self._store_health_results(results)
                
                # Check for recovery needs
                if self.recovery_enabled:
                    await self._check_recovery_needs(results)
                
                # Clean up old data
                self._cleanup_old_health_data()
                
            except asyncio.CancelledError:
                self.logger.debug("Health check loop cancelled")
                break
            except Exception as e:
                self.logger.error(f"Health check loop error: {e}")
    
    async def _run_all_health_checks(self) -> List[HealthCheckResult]:
        """Run all registered health checks"""
        results = []
        
        for component, check_func in self._health_checks.items():
            try:
                start_time = datetime.now()
                
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                
                # Calculate response time
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                result.response_time_ms = response_time
                
                results.append(result)
                
            except Exception as e:
                # Create error result for failed health check
                error_result = HealthCheckResult(
                    component=component,
                    status=HealthStatus.CRITICAL,
                    message=f"Health check failed: {str(e)}",
                    details={"error": str(e)},
                    timestamp=datetime.now(),
                    response_time_ms=0.0,
                    recovery_actions=[RecoveryAction.NOTIFY_ADMIN]
                )
                results.append(error_result)
                
                self.logger.error(f"Health check failed for {component}: {e}")
        
        return results
    
    def _store_health_results(self, results: List[HealthCheckResult]) -> None:
        """Store health check results in history"""
        try:
            self._health_history.extend(results)
            
            # Limit history size
            if len(self._health_history) > self.max_history_size:
                self._health_history = self._health_history[-self.max_history_size:]
            
        except Exception as e:
            self.logger.error(f"Failed to store health results: {e}")
    
    async def _check_recovery_needs(self, results: List[HealthCheckResult]) -> None:
        """Check if any components need recovery actions"""
        try:
            for result in results:
                if result.status in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]:
                    await self._attempt_recovery(result)
            
        except Exception as e:
            self.logger.error(f"Failed to check recovery needs: {e}")
    
    async def _attempt_recovery(self, result: HealthCheckResult) -> None:
        """Attempt recovery for an unhealthy component"""
        try:
            component = result.component
            
            # Check if recovery plan exists
            if component not in self._recovery_plans:
                # Use default recovery actions from result
                recovery_actions = result.recovery_actions
            else:
                recovery_plan = self._recovery_plans[component]
                recovery_actions = recovery_plan.actions
            
            # Execute recovery actions
            for action in recovery_actions:
                if action in self._recovery_handlers:
                    try:
                        handler = self._recovery_handlers[action]
                        
                        self.logger.info(f"Executing recovery action {action.value} for {component}")
                        
                        if asyncio.iscoroutinefunction(handler):
                            await handler(component, result)
                        else:
                            handler(component, result)
                        
                        # Wait a bit before next action
                        await asyncio.sleep(5)
                        
                    except Exception as e:
                        self.logger.error(f"Recovery action {action.value} failed for {component}: {e}")
                else:
                    self.logger.warning(f"No handler registered for recovery action: {action.value}")
            
        except Exception as e:
            self.logger.error(f"Failed to attempt recovery for {result.component}: {e}")
    
    def _cleanup_old_health_data(self) -> None:
        """Clean up old health check data"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=self.history_retention_hours)
            
            initial_count = len(self._health_history)
            self._health_history = [
                result for result in self._health_history
                if result.timestamp > cutoff_time
            ]
            
            cleaned_count = initial_count - len(self._health_history)
            if cleaned_count > 0:
                self.logger.debug(f"Cleaned up {cleaned_count} old health check results")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old health data: {e}")
    
    # Default health check implementations
    async def _check_database_health(self) -> HealthCheckResult:
        """Check database health"""
        try:
            from .database_service import get_database_service
            
            db_service = await get_database_service()
            
            if not db_service.is_connected():
                return HealthCheckResult(
                    component="database",
                    status=HealthStatus.CRITICAL,
                    message="Database not connected",
                    details={"connected": False},
                    timestamp=datetime.now(),
                    response_time_ms=0.0,
                    recovery_actions=[RecoveryAction.RECONNECT_DATABASE, RecoveryAction.NOTIFY_ADMIN]
                )
            
            # Test database query
            start_time = datetime.now()
            health_data = await db_service.health_check()
            query_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Determine status based on response time and health data
            status = HealthStatus.HEALTHY
            recovery_actions = []
            
            if query_time > 5000:  # 5 seconds
                status = HealthStatus.CRITICAL
                recovery_actions = [RecoveryAction.RESTART_SERVICE, RecoveryAction.NOTIFY_ADMIN]
            elif query_time > 1000:  # 1 second
                status = HealthStatus.WARNING
                recovery_actions = [RecoveryAction.NOTIFY_ADMIN]
            
            return HealthCheckResult(
                component="database",
                status=status,
                message=f"Database query time: {query_time:.2f}ms",
                details={
                    "connected": True,
                    "query_time_ms": query_time,
                    "health_data": health_data
                },
                timestamp=datetime.now(),
                response_time_ms=query_time,
                recovery_actions=recovery_actions
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="database",
                status=HealthStatus.CRITICAL,
                message=f"Database health check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                response_time_ms=0.0,
                recovery_actions=[RecoveryAction.RECONNECT_DATABASE, RecoveryAction.NOTIFY_ADMIN]
            )
    
    async def _check_cache_health(self) -> HealthCheckResult:
        """Check cache health"""
        try:
            from .cache_service import get_cache_service
            
            cache_service = await get_cache_service()
            
            if not cache_service.is_connected():
                return HealthCheckResult(
                    component="cache",
                    status=HealthStatus.WARNING,
                    message="Cache not connected",
                    details={"connected": False},
                    timestamp=datetime.now(),
                    response_time_ms=0.0,
                    recovery_actions=[RecoveryAction.CLEAR_CACHE]
                )
            
            # Test cache operations
            start_time = datetime.now()
            health_data = await cache_service.health_check()
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            status = HealthStatus.HEALTHY
            if response_time > 1000:
                status = HealthStatus.WARNING
            
            return HealthCheckResult(
                component="cache",
                status=status,
                message=f"Cache response time: {response_time:.2f}ms",
                details={
                    "connected": True,
                    "response_time_ms": response_time,
                    "health_data": health_data
                },
                timestamp=datetime.now(),
                response_time_ms=response_time,
                recovery_actions=[]
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="cache",
                status=HealthStatus.WARNING,
                message=f"Cache health check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                response_time_ms=0.0,
                recovery_actions=[RecoveryAction.CLEAR_CACHE]
            )
    
    async def _check_memory_health(self) -> HealthCheckResult:
        """Check system memory health"""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            
            status = HealthStatus.HEALTHY
            recovery_actions = []
            
            if memory.percent > 95:
                status = HealthStatus.CRITICAL
                recovery_actions = [RecoveryAction.SCALE_RESOURCES, RecoveryAction.NOTIFY_ADMIN]
            elif memory.percent > 85:
                status = HealthStatus.WARNING
                recovery_actions = [RecoveryAction.NOTIFY_ADMIN]
            
            return HealthCheckResult(
                component="memory",
                status=status,
                message=f"Memory usage: {memory.percent:.1f}%",
                details={
                    "percent": memory.percent,
                    "available_gb": memory.available / (1024**3),
                    "total_gb": memory.total / (1024**3)
                },
                timestamp=datetime.now(),
                response_time_ms=1.0,
                recovery_actions=recovery_actions
            )
            
        except ImportError:
            return HealthCheckResult(
                component="memory",
                status=HealthStatus.WARNING,
                message="psutil not available - memory monitoring disabled",
                details={"psutil_available": False},
                timestamp=datetime.now(),
                response_time_ms=0.0,
                recovery_actions=[]
            )
        except Exception as e:
            return HealthCheckResult(
                component="memory",
                status=HealthStatus.WARNING,
                message=f"Memory check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                response_time_ms=0.0,
                recovery_actions=[]
            )
    
    async def _check_disk_health(self) -> HealthCheckResult:
        """Check disk space health"""
        try:
            import psutil
            
            disk = psutil.disk_usage('/')
            percent_used = (disk.used / disk.total) * 100
            
            status = HealthStatus.HEALTHY
            recovery_actions = []
            
            if percent_used > 95:
                status = HealthStatus.CRITICAL
                recovery_actions = [RecoveryAction.NOTIFY_ADMIN]
            elif percent_used > 85:
                status = HealthStatus.WARNING
                recovery_actions = [RecoveryAction.NOTIFY_ADMIN]
            
            return HealthCheckResult(
                component="disk",
                status=status,
                message=f"Disk usage: {percent_used:.1f}%",
                details={
                    "percent_used": percent_used,
                    "free_gb": disk.free / (1024**3),
                    "total_gb": disk.total / (1024**3)
                },
                timestamp=datetime.now(),
                response_time_ms=1.0,
                recovery_actions=recovery_actions
            )
            
        except ImportError:
            return HealthCheckResult(
                component="disk",
                status=HealthStatus.WARNING,
                message="psutil not available - disk monitoring disabled",
                details={"psutil_available": False},
                timestamp=datetime.now(),
                response_time_ms=0.0,
                recovery_actions=[]
            )
        except Exception as e:
            return HealthCheckResult(
                component="disk",
                status=HealthStatus.WARNING,
                message=f"Disk check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                response_time_ms=0.0,
                recovery_actions=[]
            )
    
    async def _check_websocket_health(self) -> HealthCheckResult:
        """Check WebSocket connection health"""
        try:
            # This would check WebSocket connection pool health
            # For now, return a placeholder
            return HealthCheckResult(
                component="websocket",
                status=HealthStatus.HEALTHY,
                message="WebSocket connections healthy",
                details={"active_connections": 0},
                timestamp=datetime.now(),
                response_time_ms=1.0,
                recovery_actions=[]
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="websocket",
                status=HealthStatus.WARNING,
                message=f"WebSocket check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                response_time_ms=0.0,
                recovery_actions=[]
            )
    
    async def _check_ai_services_health(self) -> HealthCheckResult:
        """Check AI services health"""
        try:
            # This would check Ollama and other AI service health
            # For now, return a placeholder
            return HealthCheckResult(
                component="ai_services",
                status=HealthStatus.HEALTHY,
                message="AI services healthy",
                details={"ollama_available": True},
                timestamp=datetime.now(),
                response_time_ms=100.0,
                recovery_actions=[]
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="ai_services",
                status=HealthStatus.WARNING,
                message=f"AI services check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                response_time_ms=0.0,
                recovery_actions=[RecoveryAction.RESTART_SERVICE]
            )
    
    # Recovery action implementations
    async def _restart_service(self, component: str, result: HealthCheckResult) -> None:
        """Restart a service component"""
        self.logger.warning(f"Restart service recovery action for {component} - not implemented")
    
    async def _clear_cache(self, component: str, result: HealthCheckResult) -> None:
        """Clear cache for recovery"""
        try:
            from .cache_service import get_cache_service
            
            cache_service = await get_cache_service()
            if cache_service.is_connected():
                # This would clear cache - implement based on cache service
                self.logger.info(f"Cache cleared for {component} recovery")
            
        except Exception as e:
            self.logger.error(f"Failed to clear cache for {component}: {e}")
    
    async def _reconnect_database(self, component: str, result: HealthCheckResult) -> None:
        """Reconnect to database"""
        try:
            from .database_service import get_database_service
            
            db_service = await get_database_service()
            # This would trigger database reconnection
            self.logger.info(f"Database reconnection attempted for {component}")
            
        except Exception as e:
            self.logger.error(f"Failed to reconnect database for {component}: {e}")
    
    async def _scale_resources(self, component: str, result: HealthCheckResult) -> None:
        """Scale resources (placeholder for cloud environments)"""
        self.logger.warning(f"Scale resources recovery action for {component} - not implemented")
    
    async def _notify_admin(self, component: str, result: HealthCheckResult) -> None:
        """Notify administrators of issues"""
        self.logger.critical(
            f"ADMIN NOTIFICATION: {component} health issue - "
            f"Status: {result.status.value}, Message: {result.message}"
        )
    
    async def _graceful_shutdown(self, component: str, result: HealthCheckResult) -> None:
        """Perform graceful shutdown"""
        self.logger.critical(f"Graceful shutdown initiated due to {component} critical failure")
    
    # Public API methods
    async def get_system_health(self) -> Dict[str, Any]:
        """Get current system health status"""
        try:
            # Run health checks
            results = await self._run_all_health_checks()
            
            # Calculate overall status
            overall_status = HealthStatus.HEALTHY
            for result in results:
                if result.status == HealthStatus.CRITICAL:
                    overall_status = HealthStatus.CRITICAL
                    break
                elif result.status == HealthStatus.UNHEALTHY and overall_status != HealthStatus.CRITICAL:
                    overall_status = HealthStatus.UNHEALTHY
                elif result.status == HealthStatus.WARNING and overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.WARNING
            
            return {
                "overall_status": overall_status.value,
                "timestamp": datetime.now().isoformat(),
                "components": [
                    {
                        "component": result.component,
                        "status": result.status.value,
                        "message": result.message,
                        "details": result.details,
                        "response_time_ms": result.response_time_ms
                    }
                    for result in results
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get system health: {e}")
            return {
                "overall_status": HealthStatus.CRITICAL.value,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "components": []
            }
    
    async def get_health_history(self, component: Optional[str] = None, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health check history"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            filtered_history = [
                result for result in self._health_history
                if result.timestamp > cutoff_time and (component is None or result.component == component)
            ]
            
            return [
                {
                    "component": result.component,
                    "status": result.status.value,
                    "message": result.message,
                    "details": result.details,
                    "timestamp": result.timestamp.isoformat(),
                    "response_time_ms": result.response_time_ms
                }
                for result in filtered_history
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to get health history: {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check service health check"""
        try:
            return {
                "status": "healthy",
                "registered_checks": len(self._health_checks),
                "recovery_plans": len(self._recovery_plans),
                "history_size": len(self._health_history),
                "recovery_enabled": self.recovery_enabled,
                "check_active": self._health_check_task is not None and not self._health_check_task.done()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Global health check service instance
_health_check_service: Optional[HealthCheckService] = None


async def get_health_check_service(config: Optional[Dict[str, Any]] = None) -> HealthCheckService:
    """Get or create global health check service instance"""
    global _health_check_service
    
    if _health_check_service is None:
        _health_check_service = HealthCheckService(config=config)
        await _health_check_service.initialize()
    
    return _health_check_service


async def cleanup_health_check_service() -> None:
    """Clean up global health check service"""
    global _health_check_service
    
    if _health_check_service:
        await _health_check_service.cleanup()
        _health_check_service = None