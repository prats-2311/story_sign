"""
Security audit logging service for compliance and monitoring
"""

import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import logging
from pathlib import Path

from core.base_service import BaseService


class AuditEventType(Enum):
    """Audit event types"""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    
    # Authorization events
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    ROLE_CHANGE = "role_change"
    
    # Data events
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    DATA_EXPORT = "data_export"
    
    # System events
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    PLUGIN_INSTALLED = "plugin_installed"
    PLUGIN_REMOVED = "plugin_removed"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    
    # Security events
    THREAT_DETECTED = "threat_detected"
    IP_BLOCKED = "ip_blocked"
    SECURITY_SCAN = "security_scan"
    VULNERABILITY_DETECTED = "vulnerability_detected"
    
    # Administrative events
    USER_CREATED = "user_created"
    USER_DELETED = "user_deleted"
    USER_SUSPENDED = "user_suspended"
    USER_REACTIVATED = "user_reactivated"


class AuditSeverity(Enum):
    """Audit event severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SecurityAuditService(BaseService):
    """
    Service for security audit logging and compliance monitoring
    """
    
    def __init__(self, service_name: str = "SecurityAuditService", config: Optional[Dict[str, Any]] = None):
        super().__init__(service_name, config)
        
        # Configuration
        self.audit_log_path = Path(config.get("audit_log_path", "logs/security_audit.log") if config else "logs/security_audit.log")
        self.max_log_size = config.get("max_log_size", 100 * 1024 * 1024) if config else 100 * 1024 * 1024  # 100MB
        self.retention_days = config.get("retention_days", 365) if config else 365  # 1 year
        self.enable_real_time_alerts = config.get("enable_real_time_alerts", True) if config else True
        
        # Ensure log directory exists
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # In-memory buffer for real-time monitoring
        self.recent_events = []
        self.max_buffer_size = 1000
        
        # Alert thresholds
        self.alert_thresholds = {
            AuditEventType.LOGIN_FAILED: {"count": 5, "window": 300},  # 5 failures in 5 minutes
            AuditEventType.ACCESS_DENIED: {"count": 10, "window": 600},  # 10 denials in 10 minutes
            AuditEventType.THREAT_DETECTED: {"count": 1, "window": 60},  # Any threat detection
            AuditEventType.VULNERABILITY_DETECTED: {"count": 1, "window": 60}  # Any vulnerability
        }
        
    async def initialize(self) -> None:
        """Initialize security audit service"""
        self.logger.info("Security audit service initialized")
        
        # Start background tasks
        asyncio.create_task(self._rotate_logs())
        asyncio.create_task(self._monitor_alerts())
        
        # Log service startup
        await self.log_event(
            event_type=AuditEventType.SYSTEM_CONFIG_CHANGE,
            severity=AuditSeverity.INFO,
            message="Security audit service started",
            details={"service": "SecurityAuditService", "action": "startup"}
        )
    
    async def cleanup(self) -> None:
        """Clean up security audit service"""
        await self.log_event(
            event_type=AuditEventType.SYSTEM_CONFIG_CHANGE,
            severity=AuditSeverity.INFO,
            message="Security audit service stopped",
            details={"service": "SecurityAuditService", "action": "shutdown"}
        )
    
    async def log_event(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity,
        message: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a security audit event
        
        Args:
            event_type: Type of audit event
            severity: Severity level
            message: Human-readable message
            user_id: User ID associated with event
            ip_address: Client IP address
            user_agent: User agent string
            session_id: Session ID
            resource: Resource being accessed/modified
            details: Additional event details
        """
        try:
            timestamp = datetime.utcnow()
            
            # Create audit event
            audit_event = {
                "timestamp": timestamp.isoformat() + "Z",
                "event_type": event_type.value,
                "severity": severity.value,
                "message": message,
                "user_id": user_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "session_id": session_id,
                "resource": resource,
                "details": details or {},
                "event_id": self._generate_event_id(timestamp)
            }
            
            # Add to in-memory buffer
            self.recent_events.append(audit_event)
            if len(self.recent_events) > self.max_buffer_size:
                self.recent_events.pop(0)
            
            # Write to audit log file
            await self._write_to_log(audit_event)
            
            # Check for real-time alerts
            if self.enable_real_time_alerts:
                await self._check_alert_conditions(event_type, audit_event)
            
            # Log to application logger for critical events
            if severity in [AuditSeverity.ERROR, AuditSeverity.CRITICAL]:
                self.logger.warning(f"Security audit: {message} (Type: {event_type.value})")
            
        except Exception as e:
            self.logger.error(f"Failed to log audit event: {e}")
    
    async def log_authentication_event(
        self,
        event_type: AuditEventType,
        user_identifier: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log authentication-related audit event
        
        Args:
            event_type: Authentication event type
            user_identifier: Username or email
            success: Whether authentication was successful
            ip_address: Client IP address
            user_agent: User agent string
            details: Additional details
        """
        severity = AuditSeverity.INFO if success else AuditSeverity.WARNING
        message = f"Authentication {'successful' if success else 'failed'} for user: {user_identifier}"
        
        event_details = {
            "user_identifier": user_identifier,
            "success": success,
            **(details or {})
        }
        
        await self.log_event(
            event_type=event_type,
            severity=severity,
            message=message,
            ip_address=ip_address,
            user_agent=user_agent,
            details=event_details
        )
    
    async def log_data_access(
        self,
        user_id: str,
        resource: str,
        action: str,
        success: bool,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log data access audit event
        
        Args:
            user_id: User ID
            resource: Resource being accessed
            action: Action performed (read, write, delete, etc.)
            success: Whether access was successful
            ip_address: Client IP address
            details: Additional details
        """
        event_type = AuditEventType.DATA_ACCESS if success else AuditEventType.ACCESS_DENIED
        severity = AuditSeverity.INFO if success else AuditSeverity.WARNING
        message = f"Data {action} {'successful' if success else 'denied'} for resource: {resource}"
        
        event_details = {
            "action": action,
            "success": success,
            **(details or {})
        }
        
        await self.log_event(
            event_type=event_type,
            severity=severity,
            message=message,
            user_id=user_id,
            ip_address=ip_address,
            resource=resource,
            details=event_details
        )
    
    async def log_security_event(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity,
        message: str,
        ip_address: Optional[str] = None,
        user_id: Optional[str] = None,
        threat_details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log security-related audit event
        
        Args:
            event_type: Security event type
            severity: Event severity
            message: Event message
            ip_address: Source IP address
            user_id: Associated user ID
            threat_details: Threat-specific details
        """
        await self.log_event(
            event_type=event_type,
            severity=severity,
            message=message,
            user_id=user_id,
            ip_address=ip_address,
            details=threat_details
        )
    
    async def log_administrative_action(
        self,
        admin_user_id: str,
        action: str,
        target_resource: str,
        success: bool,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log administrative action audit event
        
        Args:
            admin_user_id: Administrator user ID
            action: Administrative action performed
            target_resource: Target of the action
            success: Whether action was successful
            ip_address: Administrator IP address
            details: Additional details
        """
        severity = AuditSeverity.INFO if success else AuditSeverity.ERROR
        message = f"Administrative action '{action}' {'completed' if success else 'failed'} on {target_resource}"
        
        event_details = {
            "admin_action": action,
            "target": target_resource,
            "success": success,
            **(details or {})
        }
        
        await self.log_event(
            event_type=AuditEventType.SYSTEM_CONFIG_CHANGE,
            severity=severity,
            message=message,
            user_id=admin_user_id,
            ip_address=ip_address,
            resource=target_resource,
            details=event_details
        )
    
    async def search_audit_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        severity: Optional[AuditSeverity] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search audit logs with filters
        
        Args:
            start_time: Start time for search
            end_time: End time for search
            event_types: Event types to filter by
            user_id: User ID to filter by
            ip_address: IP address to filter by
            severity: Severity level to filter by
            limit: Maximum number of results
            
        Returns:
            List of matching audit events
        """
        try:
            # For now, search in-memory buffer
            # In production, this would search log files or database
            
            results = []
            
            for event in reversed(self.recent_events):  # Most recent first
                if len(results) >= limit:
                    break
                
                # Apply filters
                event_time = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
                
                if start_time and event_time < start_time:
                    continue
                if end_time and event_time > end_time:
                    continue
                if event_types and AuditEventType(event["event_type"]) not in event_types:
                    continue
                if user_id and event.get("user_id") != user_id:
                    continue
                if ip_address and event.get("ip_address") != ip_address:
                    continue
                if severity and AuditSeverity(event["severity"]) != severity:
                    continue
                
                results.append(event)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Audit log search error: {e}")
            return []
    
    async def get_audit_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get audit log statistics
        
        Args:
            start_time: Start time for statistics
            end_time: End time for statistics
            
        Returns:
            Audit statistics
        """
        try:
            if not start_time:
                start_time = datetime.utcnow() - timedelta(days=7)  # Last 7 days
            if not end_time:
                end_time = datetime.utcnow()
            
            # Filter events by time range
            filtered_events = []
            for event in self.recent_events:
                event_time = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
                if start_time <= event_time <= end_time:
                    filtered_events.append(event)
            
            # Calculate statistics
            total_events = len(filtered_events)
            
            # Group by event type
            event_type_counts = {}
            for event in filtered_events:
                event_type = event["event_type"]
                event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
            
            # Group by severity
            severity_counts = {}
            for event in filtered_events:
                severity = event["severity"]
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Group by user
            user_activity = {}
            for event in filtered_events:
                user_id = event.get("user_id")
                if user_id:
                    user_activity[user_id] = user_activity.get(user_id, 0) + 1
            
            # Group by IP address
            ip_activity = {}
            for event in filtered_events:
                ip_address = event.get("ip_address")
                if ip_address:
                    ip_activity[ip_address] = ip_activity.get(ip_address, 0) + 1
            
            return {
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "total_events": total_events,
                "event_types": event_type_counts,
                "severity_levels": severity_counts,
                "top_users": sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:10],
                "top_ips": sorted(ip_activity.items(), key=lambda x: x[1], reverse=True)[:10],
                "critical_events": len([e for e in filtered_events if e["severity"] == "critical"]),
                "failed_authentications": len([
                    e for e in filtered_events 
                    if e["event_type"] == "login_failed"
                ])
            }
            
        except Exception as e:
            self.logger.error(f"Audit statistics error: {e}")
            return {}
    
    def _generate_event_id(self, timestamp: datetime) -> str:
        """Generate unique event ID"""
        import hashlib
        
        # Create unique ID based on timestamp and random component
        unique_string = f"{timestamp.isoformat()}-{id(self)}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:16]
    
    async def _write_to_log(self, audit_event: Dict[str, Any]) -> None:
        """Write audit event to log file"""
        try:
            log_line = json.dumps(audit_event, separators=(',', ':')) + '\n'
            
            # Write to audit log file
            with open(self.audit_log_path, 'a', encoding='utf-8') as f:
                f.write(log_line)
            
        except Exception as e:
            self.logger.error(f"Failed to write audit log: {e}")
    
    async def _check_alert_conditions(self, event_type: AuditEventType, event: Dict[str, Any]) -> None:
        """Check if event triggers any alert conditions"""
        try:
            if event_type not in self.alert_thresholds:
                return
            
            threshold = self.alert_thresholds[event_type]
            current_time = datetime.utcnow()
            window_start = current_time - timedelta(seconds=threshold["window"])
            
            # Count recent events of this type
            recent_count = 0
            for recent_event in self.recent_events:
                event_time = datetime.fromisoformat(recent_event["timestamp"].replace("Z", "+00:00"))
                if (event_time >= window_start and 
                    recent_event["event_type"] == event_type.value):
                    recent_count += 1
            
            # Trigger alert if threshold exceeded
            if recent_count >= threshold["count"]:
                await self._trigger_alert(event_type, recent_count, threshold, event)
            
        except Exception as e:
            self.logger.error(f"Alert condition check error: {e}")
    
    async def _trigger_alert(
        self,
        event_type: AuditEventType,
        count: int,
        threshold: Dict[str, int],
        triggering_event: Dict[str, Any]
    ) -> None:
        """Trigger security alert"""
        try:
            alert_message = (
                f"Security alert: {count} {event_type.value} events "
                f"in {threshold['window']} seconds (threshold: {threshold['count']})"
            )
            
            # Log the alert
            await self.log_event(
                event_type=AuditEventType.THREAT_DETECTED,
                severity=AuditSeverity.CRITICAL,
                message=alert_message,
                details={
                    "alert_type": "threshold_exceeded",
                    "triggering_event_type": event_type.value,
                    "event_count": count,
                    "threshold": threshold,
                    "triggering_event": triggering_event
                }
            )
            
            # In production, you would also:
            # - Send email/SMS notifications
            # - Integrate with SIEM systems
            # - Trigger automated responses
            
            self.logger.critical(alert_message)
            
        except Exception as e:
            self.logger.error(f"Alert trigger error: {e}")
    
    async def _rotate_logs(self) -> None:
        """Rotate audit logs when they get too large"""
        while True:
            try:
                await asyncio.sleep(3600)  # Check every hour
                
                if self.audit_log_path.exists():
                    file_size = self.audit_log_path.stat().st_size
                    
                    if file_size > self.max_log_size:
                        # Rotate log file
                        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                        rotated_path = self.audit_log_path.with_suffix(f".{timestamp}.log")
                        
                        self.audit_log_path.rename(rotated_path)
                        
                        # Log rotation event
                        await self.log_event(
                            event_type=AuditEventType.SYSTEM_CONFIG_CHANGE,
                            severity=AuditSeverity.INFO,
                            message=f"Audit log rotated: {rotated_path.name}",
                            details={"old_size": file_size, "rotated_file": str(rotated_path)}
                        )
                
                # Clean up old log files
                await self._cleanup_old_logs()
                
            except Exception as e:
                self.logger.error(f"Log rotation error: {e}")
    
    async def _cleanup_old_logs(self) -> None:
        """Clean up old audit log files"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
            log_dir = self.audit_log_path.parent
            
            for log_file in log_dir.glob("security_audit.*.log"):
                if log_file.stat().st_mtime < cutoff_date.timestamp():
                    log_file.unlink()
                    self.logger.info(f"Deleted old audit log: {log_file.name}")
            
        except Exception as e:
            self.logger.error(f"Log cleanup error: {e}")
    
    async def _monitor_alerts(self) -> None:
        """Monitor for security alerts"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Monitor for suspicious patterns
                current_time = datetime.utcnow()
                recent_window = current_time - timedelta(minutes=10)
                
                recent_events = [
                    event for event in self.recent_events
                    if datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00")) >= recent_window
                ]
                
                # Check for multiple failed logins from same IP
                ip_failures = {}
                for event in recent_events:
                    if event["event_type"] == "login_failed":
                        ip = event.get("ip_address")
                        if ip:
                            ip_failures[ip] = ip_failures.get(ip, 0) + 1
                
                for ip, count in ip_failures.items():
                    if count >= 5:  # 5 failures in 10 minutes
                        await self.log_event(
                            event_type=AuditEventType.THREAT_DETECTED,
                            severity=AuditSeverity.WARNING,
                            message=f"Multiple login failures detected from IP: {ip}",
                            ip_address=ip,
                            details={"failure_count": count, "time_window": "10_minutes"}
                        )
                
            except Exception as e:
                self.logger.error(f"Alert monitoring error: {e}")