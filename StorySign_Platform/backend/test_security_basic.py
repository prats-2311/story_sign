"""
Basic security functionality tests
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path


def test_security_config_exists():
    """Test that security configuration file exists"""
    config_path = Path("config/security.yaml")
    assert config_path.exists(), "Security configuration file should exist"


def test_mfa_service_import():
    """Test MFA service can be imported"""
    try:
        from services.mfa_service import MFAService
        assert MFAService is not None
    except ImportError as e:
        pytest.skip(f"MFA service not available: {e}")


def test_threat_detection_service_import():
    """Test threat detection service can be imported"""
    try:
        from services.threat_detection_service import ThreatDetectionService
        assert ThreatDetectionService is not None
    except ImportError as e:
        pytest.skip(f"Threat detection service not available: {e}")


def test_audit_service_import():
    """Test audit service can be imported"""
    try:
        from services.security_audit_service import SecurityAuditService
        assert SecurityAuditService is not None
    except ImportError as e:
        pytest.skip(f"Audit service not available: {e}")


def test_vulnerability_scanner_import():
    """Test vulnerability scanner can be imported"""
    try:
        from services.vulnerability_scanner import VulnerabilityScanner
        assert VulnerabilityScanner is not None
    except ImportError as e:
        pytest.skip(f"Vulnerability scanner not available: {e}")


def test_security_api_import():
    """Test security API can be imported"""
    try:
        from api.security import router
        assert router is not None
    except ImportError as e:
        pytest.skip(f"Security API not available: {e}")


@pytest.mark.asyncio
async def test_mfa_basic_functionality():
    """Test basic MFA functionality"""
    try:
        from services.mfa_service import MFAService
        
        config = {"issuer_name": "Test StorySign"}
        service = MFAService(config=config)
        await service.initialize()
        
        # Test secret generation
        secret = service.generate_secret_key()
        assert secret is not None
        assert len(secret) == 32
        
        # Test backup codes
        backup_codes = service.generate_backup_codes()
        assert len(backup_codes) == 10
        
        # Test phone validation
        assert service.validate_phone_number("+1234567890") is True
        assert service.validate_phone_number("invalid") is False
        
    except ImportError:
        pytest.skip("MFA service not available")


@pytest.mark.asyncio
async def test_threat_detection_basic():
    """Test basic threat detection functionality"""
    try:
        from services.threat_detection_service import ThreatDetectionService
        
        service = ThreatDetectionService()
        await service.initialize()
        
        # Test malicious user agent detection
        assert service._is_malicious_user_agent("sqlmap/1.0") is True
        assert service._is_malicious_user_agent("Mozilla/5.0") is False
        
        # Test SQL injection detection
        assert service._check_sql_injection({"q": "SELECT * FROM users"}, "") is True
        assert service._check_sql_injection({"q": "normal search"}, "") is False
        
        # Test XSS detection
        assert service._check_xss_attempt({"content": "<script>alert(1)</script>"}, "") is True
        assert service._check_xss_attempt({"content": "normal content"}, "") is False
        
    except ImportError:
        pytest.skip("Threat detection service not available")


@pytest.mark.asyncio
async def test_audit_service_basic():
    """Test basic audit service functionality"""
    try:
        from services.security_audit_service import SecurityAuditService, AuditEventType, AuditSeverity
        
        # Use temporary file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            temp_log = f.name
        
        try:
            config = {"audit_log_path": temp_log}
            service = SecurityAuditService(config=config)
            await service.initialize()
            
            # Test event logging
            await service.log_event(
                event_type=AuditEventType.LOGIN_SUCCESS,
                severity=AuditSeverity.INFO,
                message="Test event",
                user_id="test_user"
            )
            
            # Should have at least 1 event (may have startup event too)
            assert len(service.recent_events) >= 1
            
            # Find our test event
            test_event = None
            for event in service.recent_events:
                if event.get("user_id") == "test_user":
                    test_event = event
                    break
            
            assert test_event is not None
            assert test_event["event_type"] == "login_success"
            assert test_event["user_id"] == "test_user"
            
        finally:
            os.unlink(temp_log)
            
    except ImportError:
        pytest.skip("Audit service not available")


def test_security_patterns():
    """Test security pattern detection"""
    try:
        from services.threat_detection_service import ThreatDetectionService
        
        service = ThreatDetectionService()
        
        # Test SQL injection patterns
        sql_patterns = service.malicious_patterns["sql_injection"]
        assert len(sql_patterns) > 0
        
        # Test XSS patterns
        xss_patterns = service.malicious_patterns["xss"]
        assert len(xss_patterns) > 0
        
        # Test malicious user agents
        malicious_agents = service.malicious_patterns["malicious_user_agents"]
        assert len(malicious_agents) > 0
        
    except ImportError:
        pytest.skip("Threat detection service not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])