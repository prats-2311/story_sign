"""
Advanced threat detection service for security monitoring
"""

import asyncio
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass
import ipaddress
import re
import logging

from core.base_service import BaseService


@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_type: str
    severity: str  # low, medium, high, critical
    user_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    details: Dict[str, Any]
    timestamp: datetime
    session_id: Optional[str] = None


@dataclass
class ThreatRule:
    """Threat detection rule"""
    rule_id: str
    name: str
    description: str
    event_types: List[str]
    conditions: Dict[str, Any]
    severity: str
    action: str  # log, alert, block, quarantine
    enabled: bool = True


class ThreatDetectionService(BaseService):
    """
    Service for detecting and responding to security threats
    """
    
    def __init__(self, service_name: str = "ThreatDetectionService", config: Optional[Dict[str, Any]] = None):
        super().__init__(service_name, config)
        
        # Rate limiting tracking
        self.login_attempts = defaultdict(lambda: deque(maxlen=100))
        self.api_requests = defaultdict(lambda: deque(maxlen=1000))
        self.failed_requests = defaultdict(lambda: deque(maxlen=100))
        
        # Suspicious activity tracking
        self.suspicious_ips = set()
        self.blocked_ips = set()
        self.user_sessions = defaultdict(list)
        
        # Security events buffer
        self.security_events = deque(maxlen=10000)
        
        # Threat detection rules
        self.threat_rules = self._initialize_threat_rules()
        
        # Known malicious patterns
        self.malicious_patterns = self._initialize_malicious_patterns()
        
    async def initialize(self) -> None:
        """Initialize threat detection service"""
        self.logger.info("Threat detection service initialized")
        
        # Start background monitoring tasks
        asyncio.create_task(self._cleanup_old_data())
        asyncio.create_task(self._analyze_patterns())
    
    async def cleanup(self) -> None:
        """Clean up threat detection service"""
        pass
    
    def _initialize_threat_rules(self) -> List[ThreatRule]:
        """Initialize default threat detection rules"""
        return [
            ThreatRule(
                rule_id="brute_force_login",
                name="Brute Force Login Attack",
                description="Multiple failed login attempts from same IP",
                event_types=["login_failed"],
                conditions={
                    "max_attempts": 5,
                    "time_window": 300,  # 5 minutes
                    "same_ip": True
                },
                severity="high",
                action="block"
            ),
            ThreatRule(
                rule_id="credential_stuffing",
                name="Credential Stuffing Attack",
                description="Multiple failed logins across different accounts from same IP",
                event_types=["login_failed"],
                conditions={
                    "max_attempts": 10,
                    "time_window": 600,  # 10 minutes
                    "different_users": True
                },
                severity="high",
                action="block"
            ),
            ThreatRule(
                rule_id="suspicious_user_agent",
                name="Suspicious User Agent",
                description="Request from known malicious user agent",
                event_types=["api_request", "login_attempt"],
                conditions={
                    "malicious_user_agent": True
                },
                severity="medium",
                action="alert"
            ),
            ThreatRule(
                rule_id="rapid_api_requests",
                name="API Rate Limit Exceeded",
                description="Excessive API requests from single source",
                event_types=["api_request"],
                conditions={
                    "max_requests": 1000,
                    "time_window": 3600,  # 1 hour
                    "same_ip": True
                },
                severity="medium",
                action="alert"
            ),
            ThreatRule(
                rule_id="geo_anomaly",
                name="Geographic Anomaly",
                description="Login from unusual geographic location",
                event_types=["login_success"],
                conditions={
                    "geo_distance_km": 1000,
                    "time_window": 3600  # 1 hour
                },
                severity="medium",
                action="alert"
            ),
            ThreatRule(
                rule_id="privilege_escalation",
                name="Privilege Escalation Attempt",
                description="Attempt to access unauthorized resources",
                event_types=["authorization_failed"],
                conditions={
                    "max_attempts": 3,
                    "time_window": 300,  # 5 minutes
                    "same_user": True
                },
                severity="high",
                action="alert"
            ),
            ThreatRule(
                rule_id="sql_injection",
                name="SQL Injection Attempt",
                description="Potential SQL injection in request parameters",
                event_types=["api_request"],
                conditions={
                    "sql_injection_pattern": True
                },
                severity="critical",
                action="block"
            ),
            ThreatRule(
                rule_id="xss_attempt",
                name="Cross-Site Scripting Attempt",
                description="Potential XSS attack in request data",
                event_types=["api_request"],
                conditions={
                    "xss_pattern": True
                },
                severity="high",
                action="block"
            )
        ]
    
    def _initialize_malicious_patterns(self) -> Dict[str, List[str]]:
        """Initialize known malicious patterns"""
        return {
            "sql_injection": [
                r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
                r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
                r"(\b(OR|AND)\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",
                r"(--|#|/\*|\*/)",
                r"(\bUNION\s+SELECT\b)",
                r"(\b(INFORMATION_SCHEMA|SYSOBJECTS|SYSCOLUMNS)\b)"
            ],
            "xss": [
                r"(<script[^>]*>.*?</script>)",
                r"(javascript:)",
                r"(on\w+\s*=)",
                r"(<iframe[^>]*>)",
                r"(<object[^>]*>)",
                r"(<embed[^>]*>)",
                r"(eval\s*\()",
                r"(document\.cookie)",
                r"(document\.write)"
            ],
            "malicious_user_agents": [
                r"(sqlmap|nikto|nmap|masscan|zap|burp)",
                r"(bot|crawler|spider|scraper)",
                r"(curl|wget|python-requests|go-http-client)",
                r"(scanner|exploit|hack|attack)"
            ],
            "suspicious_paths": [
                r"(\.\.\/|\.\.\\)",  # Directory traversal
                r"(\/etc\/passwd|\/etc\/shadow)",  # System files
                r"(wp-admin|wp-login|phpmyadmin)",  # Common CMS paths
                r"(\.php|\.asp|\.jsp|\.cgi)",  # Script files
                r"(shell|cmd|exec|system)"  # Command execution
            ]
        }
    
    async def analyze_request(
        self,
        request_data: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze incoming request for threats
        
        Args:
            request_data: Request data to analyze
            user_id: User ID if authenticated
            session_id: Session ID
            
        Returns:
            Analysis result with threat level and actions
        """
        try:
            ip_address = request_data.get("ip_address")
            user_agent = request_data.get("user_agent", "")
            path = request_data.get("path", "")
            method = request_data.get("method", "GET")
            params = request_data.get("params", {})
            headers = request_data.get("headers", {})
            
            threats_detected = []
            max_severity = "low"
            actions = []
            
            # Check if IP is already blocked
            if ip_address in self.blocked_ips:
                return {
                    "blocked": True,
                    "reason": "IP address is blocked",
                    "severity": "critical"
                }
            
            # Analyze for various threat patterns
            
            # 1. Check for malicious user agent
            if self._is_malicious_user_agent(user_agent):
                threats_detected.append("malicious_user_agent")
                max_severity = self._update_max_severity(max_severity, "medium")
                actions.append("alert")
            
            # 2. Check for SQL injection
            if self._check_sql_injection(params, path):
                threats_detected.append("sql_injection")
                max_severity = self._update_max_severity(max_severity, "critical")
                actions.append("block")
            
            # 3. Check for XSS attempts
            if self._check_xss_attempt(params, path):
                threats_detected.append("xss_attempt")
                max_severity = self._update_max_severity(max_severity, "high")
                actions.append("block")
            
            # 4. Check for suspicious paths
            if self._check_suspicious_path(path):
                threats_detected.append("suspicious_path")
                max_severity = self._update_max_severity(max_severity, "medium")
                actions.append("alert")
            
            # 5. Check rate limiting
            rate_limit_result = self._check_rate_limiting(ip_address, user_id)
            if rate_limit_result["exceeded"]:
                threats_detected.append("rate_limit_exceeded")
                max_severity = self._update_max_severity(max_severity, "medium")
                actions.append("alert")
            
            # Record security event
            if threats_detected:
                event = SecurityEvent(
                    event_type="threat_detected",
                    severity=max_severity,
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    details={
                        "threats": threats_detected,
                        "path": path,
                        "method": method,
                        "params": self._sanitize_params(params)
                    },
                    timestamp=datetime.utcnow(),
                    session_id=session_id
                )
                await self._record_security_event(event)
            
            # Execute actions
            blocked = "block" in actions
            if blocked and ip_address:
                self.blocked_ips.add(ip_address)
                self.logger.warning(f"Blocked IP {ip_address} due to threats: {threats_detected}")
            
            return {
                "blocked": blocked,
                "threats": threats_detected,
                "severity": max_severity,
                "actions": actions,
                "rate_limit": rate_limit_result
            }
            
        except Exception as e:
            self.logger.error(f"Request analysis error: {e}")
            return {
                "blocked": False,
                "threats": [],
                "severity": "low",
                "actions": [],
                "error": str(e)
            }
    
    async def analyze_login_attempt(
        self,
        ip_address: str,
        user_identifier: str,
        success: bool,
        user_agent: Optional[str] = None,
        geo_location: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze login attempt for threats
        
        Args:
            ip_address: Client IP address
            user_identifier: Username or email
            success: Whether login was successful
            user_agent: User agent string
            geo_location: Geographic location data
            
        Returns:
            Analysis result
        """
        try:
            current_time = datetime.utcnow()
            threats_detected = []
            max_severity = "low"
            actions = []
            
            # Record login attempt
            self.login_attempts[ip_address].append({
                "user": user_identifier,
                "success": success,
                "timestamp": current_time,
                "user_agent": user_agent,
                "geo_location": geo_location
            })
            
            if not success:
                # Check for brute force attack
                recent_failures = [
                    attempt for attempt in self.login_attempts[ip_address]
                    if not attempt["success"] and 
                    (current_time - attempt["timestamp"]).total_seconds() < 300  # 5 minutes
                ]
                
                if len(recent_failures) >= 5:
                    threats_detected.append("brute_force_attack")
                    max_severity = self._update_max_severity(max_severity, "high")
                    actions.append("block")
                
                # Check for credential stuffing
                unique_users = set(attempt["user"] for attempt in recent_failures)
                if len(unique_users) >= 5:
                    threats_detected.append("credential_stuffing")
                    max_severity = self._update_max_severity(max_severity, "high")
                    actions.append("block")
            
            else:
                # Successful login - check for geographic anomaly
                if geo_location and user_identifier:
                    geo_anomaly = await self._check_geographic_anomaly(
                        user_identifier, geo_location
                    )
                    if geo_anomaly:
                        threats_detected.append("geographic_anomaly")
                        max_severity = self._update_max_severity(max_severity, "medium")
                        actions.append("alert")
            
            # Record security event
            if threats_detected or not success:
                event = SecurityEvent(
                    event_type="login_failed" if not success else "login_success",
                    severity=max_severity if threats_detected else "low",
                    user_id=user_identifier if success else None,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    details={
                        "threats": threats_detected,
                        "user_identifier": user_identifier,
                        "geo_location": geo_location,
                        "recent_failures": len([
                            a for a in self.login_attempts[ip_address]
                            if not a["success"] and 
                            (current_time - a["timestamp"]).total_seconds() < 300
                        ])
                    },
                    timestamp=current_time
                )
                await self._record_security_event(event)
            
            # Execute actions
            blocked = "block" in actions
            if blocked:
                self.blocked_ips.add(ip_address)
                self.logger.warning(f"Blocked IP {ip_address} due to login threats: {threats_detected}")
            
            return {
                "blocked": blocked,
                "threats": threats_detected,
                "severity": max_severity,
                "actions": actions
            }
            
        except Exception as e:
            self.logger.error(f"Login analysis error: {e}")
            return {
                "blocked": False,
                "threats": [],
                "severity": "low",
                "actions": [],
                "error": str(e)
            }
    
    def _is_malicious_user_agent(self, user_agent: str) -> bool:
        """Check if user agent matches malicious patterns"""
        if not user_agent:
            return False
        
        user_agent_lower = user_agent.lower()
        for pattern in self.malicious_patterns["malicious_user_agents"]:
            if re.search(pattern, user_agent_lower, re.IGNORECASE):
                return True
        
        return False
    
    def _check_sql_injection(self, params: Dict[str, Any], path: str) -> bool:
        """Check for SQL injection patterns"""
        # Check URL path
        for pattern in self.malicious_patterns["sql_injection"]:
            if re.search(pattern, path, re.IGNORECASE):
                return True
        
        # Check parameters
        for key, value in params.items():
            if isinstance(value, str):
                for pattern in self.malicious_patterns["sql_injection"]:
                    if re.search(pattern, value, re.IGNORECASE):
                        return True
        
        return False
    
    def _check_xss_attempt(self, params: Dict[str, Any], path: str) -> bool:
        """Check for XSS attack patterns"""
        # Check URL path
        for pattern in self.malicious_patterns["xss"]:
            if re.search(pattern, path, re.IGNORECASE):
                return True
        
        # Check parameters
        for key, value in params.items():
            if isinstance(value, str):
                for pattern in self.malicious_patterns["xss"]:
                    if re.search(pattern, value, re.IGNORECASE):
                        return True
        
        return False
    
    def _check_suspicious_path(self, path: str) -> bool:
        """Check for suspicious URL paths"""
        for pattern in self.malicious_patterns["suspicious_paths"]:
            if re.search(pattern, path, re.IGNORECASE):
                return True
        
        return False
    
    def _check_rate_limiting(self, ip_address: str, user_id: Optional[str]) -> Dict[str, Any]:
        """Check rate limiting for IP and user"""
        current_time = datetime.utcnow()
        
        # Check IP-based rate limiting
        ip_requests = [
            req for req in self.api_requests[ip_address]
            if (current_time - req).total_seconds() < 3600  # 1 hour
        ]
        
        ip_exceeded = len(ip_requests) > 1000
        
        # Check user-based rate limiting
        user_exceeded = False
        if user_id:
            user_requests = [
                req for req in self.api_requests[f"user:{user_id}"]
                if (current_time - req).total_seconds() < 3600  # 1 hour
            ]
            user_exceeded = len(user_requests) > 500
        
        # Record current request
        self.api_requests[ip_address].append(current_time)
        if user_id:
            self.api_requests[f"user:{user_id}"].append(current_time)
        
        return {
            "exceeded": ip_exceeded or user_exceeded,
            "ip_requests": len(ip_requests),
            "user_requests": len(self.api_requests[f"user:{user_id}"]) if user_id else 0,
            "limits": {
                "ip_hourly": 1000,
                "user_hourly": 500
            }
        }
    
    async def _check_geographic_anomaly(
        self,
        user_identifier: str,
        current_location: Dict[str, Any]
    ) -> bool:
        """Check for geographic anomalies in login location"""
        # This is a simplified implementation
        # In production, you would store and compare user's typical locations
        
        # For now, just check if location data seems suspicious
        if not current_location:
            return False
        
        # Check for impossible travel (placeholder logic)
        # In real implementation, compare with user's recent locations
        return False
    
    def _update_max_severity(self, current: str, new: str) -> str:
        """Update maximum severity level"""
        severity_levels = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        
        current_level = severity_levels.get(current, 0)
        new_level = severity_levels.get(new, 0)
        
        if new_level > current_level:
            return new
        return current
    
    def _sanitize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize parameters for logging (remove sensitive data)"""
        sanitized = {}
        sensitive_keys = {"password", "token", "secret", "key", "auth"}
        
        for key, value in params.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = str(value)[:100]  # Truncate long values
        
        return sanitized
    
    async def _record_security_event(self, event: SecurityEvent) -> None:
        """Record security event for analysis"""
        self.security_events.append(event)
        
        # Log high severity events immediately
        if event.severity in ["high", "critical"]:
            self.logger.warning(
                f"Security threat detected: {event.event_type} "
                f"(severity: {event.severity}) from {event.ip_address}"
            )
    
    async def _cleanup_old_data(self) -> None:
        """Clean up old tracking data"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                current_time = datetime.utcnow()
                cutoff_time = current_time - timedelta(hours=24)
                
                # Clean up login attempts
                for ip in list(self.login_attempts.keys()):
                    self.login_attempts[ip] = deque([
                        attempt for attempt in self.login_attempts[ip]
                        if attempt["timestamp"] > cutoff_time
                    ], maxlen=100)
                    
                    if not self.login_attempts[ip]:
                        del self.login_attempts[ip]
                
                # Clean up API requests
                for key in list(self.api_requests.keys()):
                    self.api_requests[key] = deque([
                        req for req in self.api_requests[key]
                        if req > cutoff_time
                    ], maxlen=1000)
                    
                    if not self.api_requests[key]:
                        del self.api_requests[key]
                
                self.logger.debug("Cleaned up old threat detection data")
                
            except Exception as e:
                self.logger.error(f"Cleanup error: {e}")
    
    async def _analyze_patterns(self) -> None:
        """Analyze security event patterns for advanced threats"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                # Analyze recent events for patterns
                recent_events = [
                    event for event in self.security_events
                    if (datetime.utcnow() - event.timestamp).total_seconds() < 3600
                ]
                
                # Group events by IP
                ip_events = defaultdict(list)
                for event in recent_events:
                    if event.ip_address:
                        ip_events[event.ip_address].append(event)
                
                # Look for coordinated attacks
                for ip, events in ip_events.items():
                    if len(events) > 10:  # Many events from single IP
                        self.suspicious_ips.add(ip)
                        self.logger.warning(f"Suspicious activity detected from IP: {ip}")
                
                self.logger.debug("Completed security pattern analysis")
                
            except Exception as e:
                self.logger.error(f"Pattern analysis error: {e}")
    
    async def get_security_summary(self) -> Dict[str, Any]:
        """Get security summary and statistics"""
        current_time = datetime.utcnow()
        
        # Recent events (last 24 hours)
        recent_events = [
            event for event in self.security_events
            if (current_time - event.timestamp).total_seconds() < 86400
        ]
        
        # Group by severity
        severity_counts = defaultdict(int)
        for event in recent_events:
            severity_counts[event.severity] += 1
        
        # Group by event type
        event_type_counts = defaultdict(int)
        for event in recent_events:
            event_type_counts[event.event_type] += 1
        
        return {
            "summary": {
                "total_events_24h": len(recent_events),
                "blocked_ips": len(self.blocked_ips),
                "suspicious_ips": len(self.suspicious_ips),
                "active_rules": len([rule for rule in self.threat_rules if rule.enabled])
            },
            "severity_breakdown": dict(severity_counts),
            "event_types": dict(event_type_counts),
            "top_threat_ips": self._get_top_threat_ips(recent_events),
            "recent_critical_events": [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "type": event.event_type,
                    "severity": event.severity,
                    "ip": event.ip_address,
                    "details": event.details
                }
                for event in recent_events
                if event.severity == "critical"
            ][-10:]  # Last 10 critical events
        }
    
    def _get_top_threat_ips(self, events: List[SecurityEvent]) -> List[Dict[str, Any]]:
        """Get top threat IPs from recent events"""
        ip_counts = defaultdict(int)
        ip_severities = defaultdict(list)
        
        for event in events:
            if event.ip_address:
                ip_counts[event.ip_address] += 1
                ip_severities[event.ip_address].append(event.severity)
        
        # Sort by count and severity
        top_ips = sorted(
            ip_counts.items(),
            key=lambda x: (x[1], len([s for s in ip_severities[x[0]] if s in ["high", "critical"]])),
            reverse=True
        )[:10]
        
        return [
            {
                "ip": ip,
                "event_count": count,
                "severities": list(set(ip_severities[ip])),
                "blocked": ip in self.blocked_ips
            }
            for ip, count in top_ips
        ]