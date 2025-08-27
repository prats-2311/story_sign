"""
Error tracking and alerting system
Provides comprehensive error collection, analysis, and alerting capabilities
"""

import asyncio
import logging
import traceback
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import hashlib

from .base_service import BaseService
from .monitoring_service import Alert, AlertSeverity


class ErrorCategory(Enum):
    """Error categories for classification"""
    DATABASE = "database"
    API = "api"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    EXTERNAL_SERVICE = "external_service"
    PLUGIN = "plugin"
    VIDEO_PROCESSING = "video_processing"
    WEBSOCKET = "websocket"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class ErrorEvent:
    """Error event data structure"""
    id: str
    category: ErrorCategory
    error_type: str
    message: str
    stack_trace: Optional[str]
    context: Dict[str, Any]
    user_id: Optional[str]
    session_id: Optional[str]
    request_id: Optional[str]
    timestamp: datetime
    resolved: bool = False
    resolution_notes: Optional[str] = None


@dataclass
class ErrorPattern:
    """Error pattern for detecting recurring issues"""
    pattern_id: str
    error_signature: str
    category: ErrorCategory
    count: int
    first_seen: datetime
    last_seen: datetime
    affected_users: set
    severity: AlertSeverity


class ErrorTrackingService(BaseService):
    """
    Comprehensive error tracking and alerting service
    Collects, analyzes, and alerts on application errors
    """
    
    def __init__(self, service_name: str = "ErrorTrackingService", config: Optional[Dict[str, Any]] = None):
        super().__init__(service_name, config)
        
        self._error_events: deque = deque(maxlen=10000)
        self._error_patterns: Dict[str, ErrorPattern] = {}
        self._error_handlers: List[Callable[[ErrorEvent], None]] = []
        self._pattern_handlers: List[Callable[[ErrorPattern], None]] = []
        
        # Configuration
        self.pattern_detection_window = 300  # 5 minutes
        self.pattern_threshold = 5  # errors to trigger pattern
        self.max_stack_trace_length = 2000
        self.cleanup_interval = 3600  # 1 hour
        self.retention_hours = 168  # 1 week
        
        # Error rate tracking
        self._error_rates: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Load configuration
        if self.config:
            error_config = self.config.get("error_tracking", {})
            self.pattern_detection_window = error_config.get("pattern_window", 300)
            self.pattern_threshold = error_config.get("pattern_threshold", 5)
            self.max_stack_trace_length = error_config.get("max_stack_trace", 2000)
            self.cleanup_interval = error_config.get("cleanup_interval", 3600)
            self.retention_hours = error_config.get("retention_hours", 168)
        
        # Start cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> None:
        """Initialize error tracking service"""
        try:
            # Start cleanup task
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            self.logger.info("Error tracking service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize error tracking service: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up error tracking resources"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Error tracking service cleaned up")
    
    async def track_error(
        self,
        error: Exception,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> str:
        """
        Track an error event
        
        Args:
            error: The exception that occurred
            category: Error category for classification
            context: Additional context information
            user_id: ID of affected user (if applicable)
            session_id: Session ID (if applicable)
            request_id: Request ID for tracing
            
        Returns:
            Error event ID
        """
        try:
            # Generate error ID
            error_id = self._generate_error_id(error, context)
            
            # Create error event
            error_event = ErrorEvent(
                id=error_id,
                category=category,
                error_type=type(error).__name__,
                message=str(error),
                stack_trace=self._format_stack_trace(error),
                context=context or {},
                user_id=user_id,
                session_id=session_id,
                request_id=request_id,
                timestamp=datetime.now()
            )
            
            # Store error event
            self._error_events.append(error_event)
            
            # Update error rates
            self._update_error_rates(category, error_event.timestamp)
            
            # Detect patterns
            await self._detect_error_patterns(error_event)
            
            # Notify error handlers
            for handler in self._error_handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(error_event)
                    else:
                        handler(error_event)
                except Exception as e:
                    self.logger.error(f"Error handler failed: {e}")
            
            # Log error
            self.logger.error(
                f"Error tracked: {error_event.error_type} - {error_event.message}",
                extra={
                    "error_id": error_id,
                    "category": category.value,
                    "user_id": user_id,
                    "context": context
                }
            )
            
            return error_id
            
        except Exception as e:
            self.logger.error(f"Failed to track error: {e}")
            return "unknown"
    
    def _generate_error_id(self, error: Exception, context: Optional[Dict[str, Any]]) -> str:
        """Generate unique error ID"""
        error_signature = f"{type(error).__name__}:{str(error)}"
        if context:
            error_signature += f":{json.dumps(context, sort_keys=True)}"
        
        return hashlib.md5(error_signature.encode()).hexdigest()[:16]
    
    def _format_stack_trace(self, error: Exception) -> Optional[str]:
        """Format stack trace with length limit"""
        try:
            stack_trace = traceback.format_exception(type(error), error, error.__traceback__)
            full_trace = "".join(stack_trace)
            
            if len(full_trace) > self.max_stack_trace_length:
                return full_trace[:self.max_stack_trace_length] + "... (truncated)"
            
            return full_trace
            
        except Exception:
            return None
    
    def _update_error_rates(self, category: ErrorCategory, timestamp: datetime) -> None:
        """Update error rate tracking"""
        try:
            # Add timestamp to category rate tracking
            self._error_rates[category.value].append(timestamp)
            
            # Add to overall rate tracking
            self._error_rates["total"].append(timestamp)
            
        except Exception as e:
            self.logger.error(f"Failed to update error rates: {e}")
    
    async def _detect_error_patterns(self, error_event: ErrorEvent) -> None:
        """Detect error patterns and create alerts"""
        try:
            # Create error signature for pattern detection
            signature = f"{error_event.category.value}:{error_event.error_type}:{error_event.message[:100]}"
            signature_hash = hashlib.md5(signature.encode()).hexdigest()
            
            # Check if pattern exists
            if signature_hash in self._error_patterns:
                pattern = self._error_patterns[signature_hash]
                pattern.count += 1
                pattern.last_seen = error_event.timestamp
                
                if error_event.user_id:
                    pattern.affected_users.add(error_event.user_id)
                
                # Check if pattern needs alert escalation
                await self._check_pattern_escalation(pattern)
                
            else:
                # Create new pattern
                pattern = ErrorPattern(
                    pattern_id=signature_hash,
                    error_signature=signature,
                    category=error_event.category,
                    count=1,
                    first_seen=error_event.timestamp,
                    last_seen=error_event.timestamp,
                    affected_users=set([error_event.user_id]) if error_event.user_id else set(),
                    severity=AlertSeverity.INFO
                )
                
                self._error_patterns[signature_hash] = pattern
            
            # Check if pattern threshold reached
            if pattern.count >= self.pattern_threshold:
                await self._create_pattern_alert(pattern)
            
        except Exception as e:
            self.logger.error(f"Failed to detect error patterns: {e}")
    
    async def _check_pattern_escalation(self, pattern: ErrorPattern) -> None:
        """Check if error pattern needs severity escalation"""
        try:
            # Calculate escalation based on frequency and user impact
            time_window = timedelta(seconds=self.pattern_detection_window)
            recent_window = pattern.last_seen - time_window
            
            if pattern.first_seen > recent_window:
                # High frequency in short time
                if pattern.count >= 50:
                    pattern.severity = AlertSeverity.CRITICAL
                elif pattern.count >= 20:
                    pattern.severity = AlertSeverity.ERROR
                elif pattern.count >= 10:
                    pattern.severity = AlertSeverity.WARNING
            
            # Escalate based on user impact
            if len(pattern.affected_users) >= 10:
                if pattern.severity == AlertSeverity.WARNING:
                    pattern.severity = AlertSeverity.ERROR
                elif pattern.severity == AlertSeverity.INFO:
                    pattern.severity = AlertSeverity.WARNING
            
        except Exception as e:
            self.logger.error(f"Failed to check pattern escalation: {e}")
    
    async def _create_pattern_alert(self, pattern: ErrorPattern) -> None:
        """Create alert for error pattern"""
        try:
            # Notify pattern handlers
            for handler in self._pattern_handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(pattern)
                    else:
                        handler(pattern)
                except Exception as e:
                    self.logger.error(f"Pattern handler failed: {e}")
            
            self.logger.warning(
                f"Error pattern detected: {pattern.error_signature} "
                f"(count: {pattern.count}, users: {len(pattern.affected_users)})"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create pattern alert: {e}")
    
    async def _cleanup_loop(self) -> None:
        """Cleanup loop for old error data"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_old_data()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Cleanup loop error: {e}")
    
    async def _cleanup_old_data(self) -> None:
        """Clean up old error events and patterns"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
            
            # Clean up old error events
            initial_count = len(self._error_events)
            self._error_events = deque(
                (event for event in self._error_events if event.timestamp > cutoff_time),
                maxlen=self._error_events.maxlen
            )
            
            cleaned_events = initial_count - len(self._error_events)
            
            # Clean up old error patterns
            patterns_to_remove = []
            for pattern_id, pattern in self._error_patterns.items():
                if pattern.last_seen < cutoff_time:
                    patterns_to_remove.append(pattern_id)
            
            for pattern_id in patterns_to_remove:
                del self._error_patterns[pattern_id]
            
            # Clean up error rates
            for category, rates in self._error_rates.items():
                while rates and rates[0] < cutoff_time:
                    rates.popleft()
            
            if cleaned_events > 0 or patterns_to_remove:
                self.logger.info(
                    f"Cleaned up {cleaned_events} old error events and "
                    f"{len(patterns_to_remove)} old patterns"
                )
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
    
    def add_error_handler(self, handler: Callable[[ErrorEvent], None]) -> None:
        """Add error event handler"""
        self._error_handlers.append(handler)
    
    def add_pattern_handler(self, handler: Callable[[ErrorPattern], None]) -> None:
        """Add error pattern handler"""
        self._pattern_handlers.append(handler)
    
    async def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for specified time period"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # Filter recent errors
            recent_errors = [
                event for event in self._error_events
                if event.timestamp > cutoff_time
            ]
            
            # Calculate statistics
            total_errors = len(recent_errors)
            errors_by_category = defaultdict(int)
            errors_by_type = defaultdict(int)
            affected_users = set()
            
            for error in recent_errors:
                errors_by_category[error.category.value] += 1
                errors_by_type[error.error_type] += 1
                if error.user_id:
                    affected_users.add(error.user_id)
            
            # Get active patterns
            active_patterns = [
                {
                    "pattern_id": pattern.pattern_id,
                    "signature": pattern.error_signature,
                    "category": pattern.category.value,
                    "count": pattern.count,
                    "affected_users": len(pattern.affected_users),
                    "severity": pattern.severity.value,
                    "first_seen": pattern.first_seen.isoformat(),
                    "last_seen": pattern.last_seen.isoformat()
                }
                for pattern in self._error_patterns.values()
                if pattern.last_seen > cutoff_time
            ]
            
            return {
                "period_hours": hours,
                "total_errors": total_errors,
                "affected_users": len(affected_users),
                "errors_by_category": dict(errors_by_category),
                "errors_by_type": dict(errors_by_type),
                "active_patterns": active_patterns,
                "error_rate": total_errors / hours if hours > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get error summary: {e}")
            return {}
    
    async def get_error_details(self, error_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific error"""
        try:
            for event in self._error_events:
                if event.id == error_id:
                    return {
                        "id": event.id,
                        "category": event.category.value,
                        "error_type": event.error_type,
                        "message": event.message,
                        "stack_trace": event.stack_trace,
                        "context": event.context,
                        "user_id": event.user_id,
                        "session_id": event.session_id,
                        "request_id": event.request_id,
                        "timestamp": event.timestamp.isoformat(),
                        "resolved": event.resolved,
                        "resolution_notes": event.resolution_notes
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get error details: {e}")
            return None
    
    async def resolve_error(self, error_id: str, resolution_notes: str) -> bool:
        """Mark an error as resolved"""
        try:
            for event in self._error_events:
                if event.id == error_id:
                    event.resolved = True
                    event.resolution_notes = resolution_notes
                    
                    self.logger.info(f"Error {error_id} marked as resolved: {resolution_notes}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to resolve error: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform error tracking service health check"""
        try:
            recent_errors = await self.get_error_summary(hours=1)
            
            return {
                "status": "healthy",
                "total_events": len(self._error_events),
                "active_patterns": len(self._error_patterns),
                "error_handlers": len(self._error_handlers),
                "pattern_handlers": len(self._pattern_handlers),
                "recent_error_rate": recent_errors.get("error_rate", 0),
                "cleanup_active": self._cleanup_task is not None and not self._cleanup_task.done()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Global error tracking service instance
_error_tracking_service: Optional[ErrorTrackingService] = None


async def get_error_tracking_service(config: Optional[Dict[str, Any]] = None) -> ErrorTrackingService:
    """Get or create global error tracking service instance"""
    global _error_tracking_service
    
    if _error_tracking_service is None:
        _error_tracking_service = ErrorTrackingService(config=config)
        await _error_tracking_service.initialize()
    
    return _error_tracking_service


async def cleanup_error_tracking_service() -> None:
    """Clean up global error tracking service"""
    global _error_tracking_service
    
    if _error_tracking_service:
        await _error_tracking_service.cleanup()
        _error_tracking_service = None


# Convenience function for tracking errors
async def track_error(
    error: Exception,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None
) -> str:
    """
    Convenience function to track an error
    
    Args:
        error: The exception that occurred
        category: Error category for classification
        context: Additional context information
        user_id: ID of affected user (if applicable)
        session_id: Session ID (if applicable)
        request_id: Request ID for tracing
        
    Returns:
        Error event ID
    """
    service = await get_error_tracking_service()
    return await service.track_error(
        error=error,
        category=category,
        context=context,
        user_id=user_id,
        session_id=session_id,
        request_id=request_id
    )