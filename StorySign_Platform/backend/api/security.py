"""
Security management API endpoints
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from pydantic import BaseModel, Field
import logging

# Import with error handling
try:
    from services.threat_detection_service import ThreatDetectionService
    THREAT_SERVICE_AVAILABLE = True
except ImportError:
    THREAT_SERVICE_AVAILABLE = False

try:
    from services.security_audit_service import SecurityAuditService, AuditEventType, AuditSeverity
    AUDIT_SERVICE_AVAILABLE = True
except ImportError:
    AUDIT_SERVICE_AVAILABLE = False

try:
    from services.vulnerability_scanner import VulnerabilityScanner
    VULN_SCANNER_AVAILABLE = True
except ImportError:
    VULN_SCANNER_AVAILABLE = False

try:
    from .auth import get_current_user
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/security", tags=["security"])


# Request/Response Models
class SecurityScanRequest(BaseModel):
    """Security scan request"""
    scan_types: Optional[List[str]] = Field(
        default=["dependencies", "configurations", "network", "web_application"],
        description="Types of scans to run"
    )
    force_rescan: bool = Field(default=False, description="Force rescan even if recent scan exists")


class ThreatAnalysisRequest(BaseModel):
    """Threat analysis request"""
    ip_address: Optional[str] = Field(None, description="IP address to analyze")
    user_id: Optional[str] = Field(None, description="User ID to analyze")
    time_range_hours: int = Field(default=24, description="Time range for analysis in hours")


class SecurityEventResponse(BaseModel):
    """Security event response"""
    success: bool
    events: List[Dict[str, Any]]
    total_count: int
    summary: Dict[str, Any]


# Dependency injection
async def get_threat_detection_service():
    """Get threat detection service instance"""
    if not THREAT_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Threat detection service not available")
    
    service = ThreatDetectionService()
    await service.initialize()
    return service


async def get_audit_service():
    """Get security audit service instance"""
    if not AUDIT_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Security audit service not available")
    
    config = {
        "audit_log_path": "logs/security_audit.log"
    }
    service = SecurityAuditService(config=config)
    await service.initialize()
    return service


async def get_vulnerability_scanner():
    """Get vulnerability scanner instance"""
    if not VULN_SCANNER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Vulnerability scanner not available")
    
    config = {
        "scan_interval": 86400,  # 24 hours
        "enable_dependency_scan": True,
        "enable_config_scan": True,
        "enable_network_scan": True,
        "enable_web_scan": True
    }
    scanner = VulnerabilityScanner(config=config)
    await scanner.initialize()
    return scanner


async def require_admin_user(current_user = Depends(get_current_user)):
    """Require admin user for security endpoints"""
    if not AUTH_AVAILABLE:
        raise HTTPException(status_code=503, detail="Authentication not available")
    
    if not current_user or current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return current_user


# API Endpoints

@router.get("/dashboard")
async def get_security_dashboard(
    current_user = Depends(require_admin_user),
    threat_service = Depends(get_threat_detection_service),
    audit_service = Depends(get_audit_service),
    vuln_scanner = Depends(get_vulnerability_scanner)
):
    """
    Get security dashboard overview
    
    Args:
        current_user: Current admin user
        threat_service: Threat detection service
        audit_service: Security audit service
        vuln_scanner: Vulnerability scanner
        
    Returns:
        Security dashboard data
    """
    try:
        # Get threat detection summary
        threat_summary = await threat_service.get_security_summary()
        
        # Get audit statistics
        audit_stats = await audit_service.get_audit_statistics()
        
        # Get vulnerability report
        vuln_report = await vuln_scanner.get_vulnerability_report()
        
        return {
            "success": True,
            "dashboard": {
                "threats": threat_summary,
                "audit": audit_stats,
                "vulnerabilities": vuln_report,
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Security dashboard error: {e}")
        raise HTTPException(status_code=500, detail="Failed to load security dashboard")


@router.post("/scan")
async def run_security_scan(
    request: SecurityScanRequest,
    current_user = Depends(require_admin_user),
    vuln_scanner = Depends(get_vulnerability_scanner),
    audit_service = Depends(get_audit_service)
):
    """
    Run security vulnerability scan
    
    Args:
        request: Scan configuration
        current_user: Current admin user
        vuln_scanner: Vulnerability scanner
        audit_service: Security audit service
        
    Returns:
        Scan results
    """
    try:
        # Log scan initiation
        await audit_service.log_event(
            event_type=AuditEventType.SECURITY_SCAN,
            severity=AuditSeverity.INFO,
            message="Security vulnerability scan initiated",
            user_id=current_user.id,
            details={"scan_types": request.scan_types, "force_rescan": request.force_rescan}
        )
        
        # Run vulnerability scan
        scan_results = await vuln_scanner.run_full_scan()
        
        # Log scan completion
        await audit_service.log_event(
            event_type=AuditEventType.SECURITY_SCAN,
            severity=AuditSeverity.INFO,
            message=f"Security scan completed: {scan_results.get('vulnerabilities_found', 0)} vulnerabilities found",
            user_id=current_user.id,
            details={"scan_results": scan_results.get("summary", {})}
        )
        
        return {
            "success": True,
            "scan_results": scan_results
        }
        
    except Exception as e:
        logger.error(f"Security scan error: {e}")
        raise HTTPException(status_code=500, detail="Security scan failed")


@router.get("/threats")
async def get_threat_analysis(
    ip_address: Optional[str] = Query(None, description="Filter by IP address"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    hours: int = Query(24, description="Time range in hours"),
    current_user = Depends(require_admin_user),
    threat_service = Depends(get_threat_detection_service)
):
    """
    Get threat analysis and detection results
    
    Args:
        ip_address: IP address filter
        user_id: User ID filter
        hours: Time range in hours
        current_user: Current admin user
        threat_service: Threat detection service
        
    Returns:
        Threat analysis results
    """
    try:
        # Get threat summary
        threat_summary = await threat_service.get_security_summary()
        
        return {
            "success": True,
            "threat_analysis": threat_summary,
            "filters": {
                "ip_address": ip_address,
                "user_id": user_id,
                "time_range_hours": hours
            }
        }
        
    except Exception as e:
        logger.error(f"Threat analysis error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get threat analysis")


@router.get("/audit/events", response_model=SecurityEventResponse)
async def get_audit_events(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    ip_address: Optional[str] = Query(None, description="Filter by IP address"),
    hours: int = Query(24, description="Time range in hours"),
    limit: int = Query(100, description="Maximum number of events"),
    current_user = Depends(require_admin_user),
    audit_service = Depends(get_audit_service)
):
    """
    Get security audit events
    
    Args:
        event_type: Event type filter
        severity: Severity filter
        user_id: User ID filter
        ip_address: IP address filter
        hours: Time range in hours
        limit: Maximum results
        current_user: Current admin user
        audit_service: Security audit service
        
    Returns:
        Security audit events
    """
    try:
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Convert filters
        event_types = [AuditEventType(event_type)] if event_type else None
        severity_filter = AuditSeverity(severity) if severity else None
        
        # Search audit logs
        events = await audit_service.search_audit_logs(
            start_time=start_time,
            end_time=end_time,
            event_types=event_types,
            user_id=user_id,
            ip_address=ip_address,
            severity=severity_filter,
            limit=limit
        )
        
        # Get statistics
        stats = await audit_service.get_audit_statistics(start_time, end_time)
        
        return SecurityEventResponse(
            success=True,
            events=events,
            total_count=len(events),
            summary=stats
        )
        
    except Exception as e:
        logger.error(f"Audit events error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get audit events")


@router.get("/vulnerabilities")
async def get_vulnerabilities(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    vuln_type: Optional[str] = Query(None, description="Filter by vulnerability type"),
    current_user = Depends(require_admin_user),
    vuln_scanner = Depends(get_vulnerability_scanner)
):
    """
    Get current vulnerability report
    
    Args:
        severity: Severity filter
        vuln_type: Vulnerability type filter
        current_user: Current admin user
        vuln_scanner: Vulnerability scanner
        
    Returns:
        Vulnerability report
    """
    try:
        # Get vulnerability report
        report = await vuln_scanner.get_vulnerability_report()
        
        # Apply filters
        vulnerabilities = report.get("vulnerabilities", [])
        
        if severity:
            vulnerabilities = [v for v in vulnerabilities if v.get("severity") == severity]
        
        if vuln_type:
            vulnerabilities = [v for v in vulnerabilities if v.get("type") == vuln_type]
        
        # Update report with filtered results
        report["vulnerabilities"] = vulnerabilities
        report["filtered_count"] = len(vulnerabilities)
        
        return {
            "success": True,
            "vulnerability_report": report
        }
        
    except Exception as e:
        logger.error(f"Vulnerabilities error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get vulnerabilities")


@router.post("/block-ip")
async def block_ip_address(
    ip_address: str = Field(..., description="IP address to block"),
    reason: str = Field(..., description="Reason for blocking"),
    current_user = Depends(require_admin_user),
    threat_service = Depends(get_threat_detection_service),
    audit_service = Depends(get_audit_service)
):
    """
    Block an IP address
    
    Args:
        ip_address: IP address to block
        reason: Reason for blocking
        current_user: Current admin user
        threat_service: Threat detection service
        audit_service: Security audit service
        
    Returns:
        Block confirmation
    """
    try:
        # Add IP to blocked list
        threat_service.blocked_ips.add(ip_address)
        
        # Log IP blocking
        await audit_service.log_event(
            event_type=AuditEventType.IP_BLOCKED,
            severity=AuditSeverity.WARNING,
            message=f"IP address blocked: {ip_address}",
            user_id=current_user.id,
            ip_address=ip_address,
            details={"reason": reason, "blocked_by": current_user.id}
        )
        
        return {
            "success": True,
            "message": f"IP address {ip_address} has been blocked",
            "reason": reason
        }
        
    except Exception as e:
        logger.error(f"Block IP error: {e}")
        raise HTTPException(status_code=500, detail="Failed to block IP address")


@router.delete("/unblock-ip")
async def unblock_ip_address(
    ip_address: str = Field(..., description="IP address to unblock"),
    current_user = Depends(require_admin_user),
    threat_service = Depends(get_threat_detection_service),
    audit_service = Depends(get_audit_service)
):
    """
    Unblock an IP address
    
    Args:
        ip_address: IP address to unblock
        current_user: Current admin user
        threat_service: Threat detection service
        audit_service: Security audit service
        
    Returns:
        Unblock confirmation
    """
    try:
        # Remove IP from blocked list
        threat_service.blocked_ips.discard(ip_address)
        
        # Log IP unblocking
        await audit_service.log_event(
            event_type=AuditEventType.SYSTEM_CONFIG_CHANGE,
            severity=AuditSeverity.INFO,
            message=f"IP address unblocked: {ip_address}",
            user_id=current_user.id,
            ip_address=ip_address,
            details={"action": "unblock", "unblocked_by": current_user.id}
        )
        
        return {
            "success": True,
            "message": f"IP address {ip_address} has been unblocked"
        }
        
    except Exception as e:
        logger.error(f"Unblock IP error: {e}")
        raise HTTPException(status_code=500, detail="Failed to unblock IP address")


@router.get("/blocked-ips")
async def get_blocked_ips(
    current_user = Depends(require_admin_user),
    threat_service = Depends(get_threat_detection_service)
):
    """
    Get list of blocked IP addresses
    
    Args:
        current_user: Current admin user
        threat_service: Threat detection service
        
    Returns:
        List of blocked IPs
    """
    try:
        return {
            "success": True,
            "blocked_ips": list(threat_service.blocked_ips),
            "suspicious_ips": list(threat_service.suspicious_ips),
            "total_blocked": len(threat_service.blocked_ips)
        }
        
    except Exception as e:
        logger.error(f"Get blocked IPs error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get blocked IPs")


@router.get("/health")
async def security_health_check():
    """
    Security services health check
    
    Returns:
        Health status of security services
    """
    try:
        health_status = {
            "threat_detection": THREAT_SERVICE_AVAILABLE,
            "audit_logging": AUDIT_SERVICE_AVAILABLE,
            "vulnerability_scanner": VULN_SCANNER_AVAILABLE,
            "authentication": AUTH_AVAILABLE,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        all_healthy = all(health_status.values())
        
        return {
            "success": True,
            "healthy": all_healthy,
            "services": health_status
        }
        
    except Exception as e:
        logger.error(f"Security health check error: {e}")
        return {
            "success": False,
            "healthy": False,
            "error": str(e)
        }