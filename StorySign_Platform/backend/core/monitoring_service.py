"""
Database monitoring and alerting service
Provides comprehensive monitoring, alerting, and performance tracking for TiDB
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from .base_service import BaseService
from .database_service import DatabaseService
from .cache_service import CacheService


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    severity: AlertSeverity
    title: str
    message: str
    metric_name: str
    current_value: float
    threshold_value: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class MetricThreshold:
    """Metric threshold configuration"""
    metric_name: str
    warning_threshold: Optional[float] = None
    error_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    comparison: str = "greater_than"  # greater_than, less_than, equals
    enabled: bool = True


@dataclass
class PerformanceMetric:
    """Performance metric data point"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str]


class DatabaseMonitoringService(BaseService):
    """
    Comprehensive database monitoring service for TiDB
    Provides real-time monitoring, alerting, and performance tracking
    """
    
    def __init__(self, service_name: str = "DatabaseMonitoringService", config: Optional[Dict[str, Any]] = None):
        super().__init__(service_name, config)
        
        self.db_service: Optional[DatabaseService] = None
        self.cache_service: Optional[CacheService] = None
        
        self._monitoring_task: Optional[asyncio.Task] = None
        self._alert_handlers: List[Callable[[Alert], None]] = []
        self._active_alerts: Dict[str, Alert] = {}
        self._metric_history: List[PerformanceMetric] = []
        
        # Configuration
        self.monitoring_interval = 60  # 1 minute
        self.metric_retention_hours = 24
        self.max_metric_history = 10000
        
        # Default thresholds
        self.thresholds = [
            MetricThreshold("connection_count", warning_threshold=50, error_threshold=80, critical_threshold=100),
            MetricThreshold("query_response_time", warning_threshold=1.0, error_threshold=5.0, critical_threshold=10.0),
            MetricThreshold("cpu_usage_percent", warning_threshold=70, error_threshold=85, critical_threshold=95),
            MetricThreshold("memory_usage_percent", warning_threshold=80, error_threshold=90, critical_threshold=95),
            MetricThreshold("disk_usage_percent", warning_threshold=80, error_threshold=90, critical_threshold=95),
            MetricThreshold("slow_query_count", warning_threshold=10, error_threshold=50, critical_threshold=100),
            MetricThreshold("error_rate_percent", warning_threshold=1.0, error_threshold=5.0, critical_threshold=10.0),
        ]
        
        # Load configuration
        if self.config:
            monitor_config = self.config.get("monitoring", {})
            self.monitoring_interval = monitor_config.get("interval", 60)
            self.metric_retention_hours = monitor_config.get("retention_hours", 24)
            self.max_metric_history = monitor_config.get("max_history", 10000)
            
            # Load custom thresholds
            custom_thresholds = monitor_config.get("thresholds", [])
            for threshold_config in custom_thresholds:
                threshold = MetricThreshold(**threshold_config)
                # Replace existing threshold or add new one
                for i, existing in enumerate(self.thresholds):
                    if existing.metric_name == threshold.metric_name:
                        self.thresholds[i] = threshold
                        break
                else:
                    self.thresholds.append(threshold)
    
    async def initialize(self) -> None:
        """Initialize monitoring service"""
        try:
            # Get required services
            from .service_container import get_service
            self.db_service = get_service("DatabaseService")
            self.cache_service = get_service("CacheService")
            
            if not self.db_service:
                raise RuntimeError("DatabaseService not available")
            
            # Start monitoring task
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            self.logger.info("Database monitoring service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize monitoring service: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up monitoring resources"""
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Database monitoring service cleaned up")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while True:
            try:
                await asyncio.sleep(self.monitoring_interval)
                
                # Collect metrics
                metrics = await self._collect_all_metrics()
                
                # Store metrics
                await self._store_metrics(metrics)
                
                # Check thresholds and generate alerts
                await self._check_thresholds(metrics)
                
                # Clean up old data
                await self._cleanup_old_data()
                
            except asyncio.CancelledError:
                self.logger.debug("Monitoring loop cancelled")
                break
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
    
    async def _collect_all_metrics(self) -> List[PerformanceMetric]:
        """Collect all performance metrics"""
        metrics = []
        timestamp = datetime.now()
        
        try:
            # Database connection metrics
            if self.db_service and self.db_service.is_connected():
                db_metrics = await self._collect_database_metrics(timestamp)
                metrics.extend(db_metrics)
            
            # System metrics
            system_metrics = await self._collect_system_metrics(timestamp)
            metrics.extend(system_metrics)
            
            # Application metrics
            app_metrics = await self._collect_application_metrics(timestamp)
            metrics.extend(app_metrics)
            
        except Exception as e:
            self.logger.error(f"Failed to collect metrics: {e}")
        
        return metrics
    
    async def _collect_database_metrics(self, timestamp: datetime) -> List[PerformanceMetric]:
        """Collect database-specific metrics"""
        metrics = []
        
        try:
            async with self.db_service.get_session() as session:
                # Connection count
                result = await session.execute(
                    "SELECT COUNT(*) as connection_count FROM information_schema.PROCESSLIST"
                )
                row = result.fetchone()
                if row:
                    metrics.append(PerformanceMetric(
                        name="connection_count",
                        value=float(row.connection_count),
                        unit="count",
                        timestamp=timestamp,
                        tags={"source": "database"}
                    ))
                
                # Query response time (using a simple test query)
                start_time = datetime.now()
                await session.execute("SELECT 1")
                response_time = (datetime.now() - start_time).total_seconds()
                
                metrics.append(PerformanceMetric(
                    name="query_response_time",
                    value=response_time,
                    unit="seconds",
                    timestamp=timestamp,
                    tags={"source": "database", "query_type": "test"}
                ))
                
                # Slow query count (from performance schema)
                try:
                    result = await session.execute("""
                        SELECT COUNT(*) as slow_count
                        FROM performance_schema.events_statements_summary_by_digest
                        WHERE AVG_TIMER_WAIT / 1000000000 > 1.0
                    """)
                    row = result.fetchone()
                    if row:
                        metrics.append(PerformanceMetric(
                            name="slow_query_count",
                            value=float(row.slow_count),
                            unit="count",
                            timestamp=timestamp,
                            tags={"source": "database"}
                        ))
                except Exception:
                    # Performance schema might not be available
                    pass
                
                # Database size metrics
                try:
                    result = await session.execute("""
                        SELECT 
                            SUM(DATA_LENGTH) as data_size,
                            SUM(INDEX_LENGTH) as index_size
                        FROM information_schema.TABLES
                        WHERE TABLE_SCHEMA = DATABASE()
                    """)
                    row = result.fetchone()
                    if row:
                        metrics.append(PerformanceMetric(
                            name="database_data_size",
                            value=float(row.data_size or 0),
                            unit="bytes",
                            timestamp=timestamp,
                            tags={"source": "database"}
                        ))
                        metrics.append(PerformanceMetric(
                            name="database_index_size",
                            value=float(row.index_size or 0),
                            unit="bytes",
                            timestamp=timestamp,
                            tags={"source": "database"}
                        ))
                except Exception:
                    pass
                
        except Exception as e:
            self.logger.error(f"Failed to collect database metrics: {e}")
        
        return metrics
    
    async def _collect_system_metrics(self, timestamp: datetime) -> List[PerformanceMetric]:
        """Collect system-level metrics"""
        metrics = []
        
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics.append(PerformanceMetric(
                name="cpu_usage_percent",
                value=cpu_percent,
                unit="percent",
                timestamp=timestamp,
                tags={"source": "system"}
            ))
            
            # Memory usage
            memory = psutil.virtual_memory()
            metrics.append(PerformanceMetric(
                name="memory_usage_percent",
                value=memory.percent,
                unit="percent",
                timestamp=timestamp,
                tags={"source": "system"}
            ))
            
            metrics.append(PerformanceMetric(
                name="memory_available_bytes",
                value=float(memory.available),
                unit="bytes",
                timestamp=timestamp,
                tags={"source": "system"}
            ))
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            metrics.append(PerformanceMetric(
                name="disk_usage_percent",
                value=disk_percent,
                unit="percent",
                timestamp=timestamp,
                tags={"source": "system"}
            ))
            
            metrics.append(PerformanceMetric(
                name="disk_free_bytes",
                value=float(disk.free),
                unit="bytes",
                timestamp=timestamp,
                tags={"source": "system"}
            ))
            
            # Network I/O
            network = psutil.net_io_counters()
            metrics.extend([
                PerformanceMetric(
                    name="network_bytes_sent",
                    value=float(network.bytes_sent),
                    unit="bytes",
                    timestamp=timestamp,
                    tags={"source": "system"}
                ),
                PerformanceMetric(
                    name="network_bytes_recv",
                    value=float(network.bytes_recv),
                    unit="bytes",
                    timestamp=timestamp,
                    tags={"source": "system"}
                )
            ])
            
        except ImportError:
            self.logger.warning("psutil not available - system metrics disabled")
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
        
        return metrics
    
    async def _collect_application_metrics(self, timestamp: datetime) -> List[PerformanceMetric]:
        """Collect application-specific metrics"""
        metrics = []
        
        try:
            # Cache hit rate (if cache service available)
            if self.cache_service and self.cache_service.is_connected():
                cache_health = await self.cache_service.health_check()
                if cache_health.get("status") == "healthy":
                    hits = cache_health.get("keyspace_hits", 0)
                    misses = cache_health.get("keyspace_misses", 0)
                    total = hits + misses
                    
                    if total > 0:
                        hit_rate = (hits / total) * 100
                        metrics.append(PerformanceMetric(
                            name="cache_hit_rate_percent",
                            value=hit_rate,
                            unit="percent",
                            timestamp=timestamp,
                            tags={"source": "cache"}
                        ))
            
            # Application error rate (placeholder - would be collected from logs)
            # This would typically come from application logs or error tracking
            metrics.append(PerformanceMetric(
                name="error_rate_percent",
                value=0.0,  # Placeholder
                unit="percent",
                timestamp=timestamp,
                tags={"source": "application"}
            ))
            
        except Exception as e:
            self.logger.error(f"Failed to collect application metrics: {e}")
        
        return metrics
    
    async def _store_metrics(self, metrics: List[PerformanceMetric]) -> None:
        """Store metrics in memory and optionally in cache"""
        try:
            # Add to in-memory history
            self._metric_history.extend(metrics)
            
            # Store in cache if available
            if self.cache_service and self.cache_service.is_connected():
                for metric in metrics:
                    cache_key = f"metric:{metric.name}:{int(metric.timestamp.timestamp())}"
                    await self.cache_service.set(
                        cache_key,
                        asdict(metric),
                        ttl=self.metric_retention_hours * 3600
                    )
            
        except Exception as e:
            self.logger.error(f"Failed to store metrics: {e}")
    
    async def _check_thresholds(self, metrics: List[PerformanceMetric]) -> None:
        """Check metrics against thresholds and generate alerts"""
        try:
            for metric in metrics:
                # Find threshold configuration for this metric
                threshold = None
                for t in self.thresholds:
                    if t.metric_name == metric.name and t.enabled:
                        threshold = t
                        break
                
                if not threshold:
                    continue
                
                # Check thresholds
                severity = None
                threshold_value = None
                
                if (threshold.critical_threshold is not None and 
                    self._compare_value(metric.value, threshold.critical_threshold, threshold.comparison)):
                    severity = AlertSeverity.CRITICAL
                    threshold_value = threshold.critical_threshold
                elif (threshold.error_threshold is not None and 
                      self._compare_value(metric.value, threshold.error_threshold, threshold.comparison)):
                    severity = AlertSeverity.ERROR
                    threshold_value = threshold.error_threshold
                elif (threshold.warning_threshold is not None and 
                      self._compare_value(metric.value, threshold.warning_threshold, threshold.comparison)):
                    severity = AlertSeverity.WARNING
                    threshold_value = threshold.warning_threshold
                
                if severity:
                    await self._create_alert(metric, severity, threshold_value)
                else:
                    # Check if we should resolve existing alerts
                    await self._resolve_alert(metric.name)
            
        except Exception as e:
            self.logger.error(f"Failed to check thresholds: {e}")
    
    def _compare_value(self, value: float, threshold: float, comparison: str) -> bool:
        """Compare value against threshold"""
        if comparison == "greater_than":
            return value > threshold
        elif comparison == "less_than":
            return value < threshold
        elif comparison == "equals":
            return abs(value - threshold) < 0.001
        else:
            return False
    
    async def _create_alert(self, metric: PerformanceMetric, severity: AlertSeverity, threshold_value: float) -> None:
        """Create or update an alert"""
        try:
            alert_id = f"{metric.name}_{severity.value}"
            
            # Check if alert already exists
            if alert_id in self._active_alerts:
                # Update existing alert
                self._active_alerts[alert_id].current_value = metric.value
                self._active_alerts[alert_id].timestamp = metric.timestamp
            else:
                # Create new alert
                alert = Alert(
                    id=alert_id,
                    severity=severity,
                    title=f"{metric.name.replace('_', ' ').title()} {severity.value.title()}",
                    message=f"{metric.name} is {metric.value:.2f} {metric.unit}, exceeding {severity.value} threshold of {threshold_value:.2f} {metric.unit}",
                    metric_name=metric.name,
                    current_value=metric.value,
                    threshold_value=threshold_value,
                    timestamp=metric.timestamp
                )
                
                self._active_alerts[alert_id] = alert
                
                # Notify alert handlers
                for handler in self._alert_handlers:
                    try:
                        await handler(alert) if asyncio.iscoroutinefunction(handler) else handler(alert)
                    except Exception as e:
                        self.logger.error(f"Alert handler error: {e}")
                
                self.logger.warning(f"Alert created: {alert.title} - {alert.message}")
        
        except Exception as e:
            self.logger.error(f"Failed to create alert: {e}")
    
    async def _resolve_alert(self, metric_name: str) -> None:
        """Resolve alerts for a metric that's back to normal"""
        try:
            resolved_alerts = []
            
            for alert_id, alert in self._active_alerts.items():
                if alert.metric_name == metric_name and not alert.resolved:
                    alert.resolved = True
                    alert.resolved_at = datetime.now()
                    resolved_alerts.append(alert)
                    
                    self.logger.info(f"Alert resolved: {alert.title}")
            
            # Remove resolved alerts after some time
            for alert in resolved_alerts:
                if alert.resolved_at and datetime.now() - alert.resolved_at > timedelta(hours=1):
                    del self._active_alerts[alert.id]
        
        except Exception as e:
            self.logger.error(f"Failed to resolve alerts: {e}")
    
    async def _cleanup_old_data(self) -> None:
        """Clean up old metrics and resolved alerts"""
        try:
            # Clean up old metrics
            cutoff_time = datetime.now() - timedelta(hours=self.metric_retention_hours)
            self._metric_history = [
                m for m in self._metric_history
                if m.timestamp > cutoff_time
            ]
            
            # Limit history size
            if len(self._metric_history) > self.max_metric_history:
                self._metric_history = self._metric_history[-self.max_metric_history:]
            
            # Clean up old resolved alerts
            cutoff_time = datetime.now() - timedelta(hours=24)
            alerts_to_remove = [
                alert_id for alert_id, alert in self._active_alerts.items()
                if alert.resolved and alert.resolved_at and alert.resolved_at < cutoff_time
            ]
            
            for alert_id in alerts_to_remove:
                del self._active_alerts[alert_id]
        
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
    
    def add_alert_handler(self, handler: Callable[[Alert], None]) -> None:
        """Add an alert handler function"""
        self._alert_handlers.append(handler)
    
    def remove_alert_handler(self, handler: Callable[[Alert], None]) -> None:
        """Remove an alert handler function"""
        if handler in self._alert_handlers:
            self._alert_handlers.remove(handler)
    
    async def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metric values"""
        try:
            # Get latest metrics for each metric name
            latest_metrics = {}
            for metric in reversed(self._metric_history):
                if metric.name not in latest_metrics:
                    latest_metrics[metric.name] = {
                        "value": metric.value,
                        "unit": metric.unit,
                        "timestamp": metric.timestamp.isoformat(),
                        "tags": metric.tags
                    }
            
            return latest_metrics
        
        except Exception as e:
            self.logger.error(f"Failed to get current metrics: {e}")
            return {}
    
    async def get_metric_history(
        self,
        metric_name: str,
        hours: int = 1
    ) -> List[Dict[str, Any]]:
        """Get historical data for a specific metric"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            history = [
                {
                    "value": m.value,
                    "unit": m.unit,
                    "timestamp": m.timestamp.isoformat(),
                    "tags": m.tags
                }
                for m in self._metric_history
                if m.name == metric_name and m.timestamp > cutoff_time
            ]
            
            return sorted(history, key=lambda x: x["timestamp"])
        
        except Exception as e:
            self.logger.error(f"Failed to get metric history: {e}")
            return []
    
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts"""
        try:
            return [
                {
                    "id": alert.id,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "message": alert.message,
                    "metric_name": alert.metric_name,
                    "current_value": alert.current_value,
                    "threshold_value": alert.threshold_value,
                    "timestamp": alert.timestamp.isoformat(),
                    "resolved": alert.resolved,
                    "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
                }
                for alert in self._active_alerts.values()
                if not alert.resolved
            ]
        
        except Exception as e:
            self.logger.error(f"Failed to get active alerts: {e}")
            return []
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform monitoring service health check"""
        try:
            return {
                "status": "healthy",
                "monitoring_active": self._monitoring_task is not None and not self._monitoring_task.done(),
                "metrics_collected": len(self._metric_history),
                "active_alerts": len([a for a in self._active_alerts.values() if not a.resolved]),
                "alert_handlers": len(self._alert_handlers),
                "database_connected": self.db_service.is_connected() if self.db_service else False,
                "cache_connected": self.cache_service.is_connected() if self.cache_service else False
            }
        
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Default alert handlers
async def log_alert_handler(alert: Alert) -> None:
    """Default alert handler that logs alerts"""
    logger = logging.getLogger("AlertHandler")
    
    if alert.severity == AlertSeverity.CRITICAL:
        logger.critical(f"CRITICAL ALERT: {alert.title} - {alert.message}")
    elif alert.severity == AlertSeverity.ERROR:
        logger.error(f"ERROR ALERT: {alert.title} - {alert.message}")
    elif alert.severity == AlertSeverity.WARNING:
        logger.warning(f"WARNING ALERT: {alert.title} - {alert.message}")
    else:
        logger.info(f"INFO ALERT: {alert.title} - {alert.message}")


# Global monitoring service instance
_monitoring_service: Optional[DatabaseMonitoringService] = None


async def get_monitoring_service(config: Optional[Dict[str, Any]] = None) -> DatabaseMonitoringService:
    """
    Get or create global monitoring service instance
    
    Args:
        config: Optional monitoring configuration
        
    Returns:
        DatabaseMonitoringService instance
    """
    global _monitoring_service
    
    if _monitoring_service is None:
        _monitoring_service = DatabaseMonitoringService(config=config)
        await _monitoring_service.initialize()
        
        # Add default alert handler
        _monitoring_service.add_alert_handler(log_alert_handler)
    
    return _monitoring_service


async def cleanup_monitoring_service() -> None:
    """Clean up global monitoring service"""
    global _monitoring_service
    
    if _monitoring_service:
        await _monitoring_service.cleanup()
        _monitoring_service = None