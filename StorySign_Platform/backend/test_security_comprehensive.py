"""
Comprehensive security testing suite for StorySign ASL Platform
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
from fastapi.testclient import TestClient

# Import security services
try:
    from services.mfa_service import MFAService
    from services.threat_detection_service import ThreatDetectionService, SecurityEvent
    from services.security_audit_service import SecurityAuditService, AuditEventType, AuditSeverity
    from services.vulnerability_scanner import VulnerabilityScanner
    from api.security import router as security_router
    from middleware.auth_middleware import AuthenticationMiddleware
    SECURITY_SERVICES_AVAILABLE = True
except ImportError as e:
    print(f"Security services not available: {e}")
    SECURITY_SERVICES_AVAILABLE = False


@pytest.mark.skipif(not SECURITY_SERVICES_AVAILABLE, reason="Security services not available")
class TestMFAService:
    """Test Multi-Factor Authentication service"""
    
    @pytest.fixture
    async def mfa_service(self):
        """Create MFA service instance"""
        config = {"issuer_name": "Test StorySign"}
        service = MFAService(config=config)
        await service.initialize()
        return service
    
    @pytest.mark.asyncio
    async def test_generate_secret_key(self, mfa_service):
        """Test TOTP secret key generation"""
        secret = mfa_service.generate_secret_key()
        
        assert secret is not None
        assert len(secret) == 32  # Base32 encoded
        assert secret.isalnum()
    
    @pytest.mark.asyncio
    async def test_generate_qr_code(self, mfa_service):
        """Test QR code generation"""
        secret = mfa_service.generate_secret_key()
        qr_code = mfa_service.generate_qr_code("test@example.com", secret)
        
        assert qr_code is not None
        assert len(qr_code) > 100  # Base64 encoded image should be substantial
    
    @pytest.mark.asyncio
    async def test_verify_totp_code(self, mfa_service):
        """Test TOTP code verification"""
        secret = mfa_service.generate_secret_key()
        
        # Generate current TOTP code
        import pyotp
        totp = pyotp.TOTP(secret)
        current_code = totp.now()
        
        # Verify the code
        is_valid = mfa_service.verify_totp_code(secret, current_code)
        assert is_valid is True
        
        # Test invalid code
        is_valid = mfa_service.verify_totp_code(secret, "000000")
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_generate_backup_codes(self, mfa_service):
        """Test backup code generation"""
        backup_codes = mfa_service.generate_backup_codes()
        
        assert len(backup_codes) == 10
        assert all(len(code) == 8 for code in backup_codes)
        assert all(code.isalnum() for code in backup_codes)
        assert len(set(backup_codes)) == 10  # All unique
    
    @pytest.mark.asyncio
    async def test_backup_code_verification(self, mfa_service):
        """Test backup code verification"""
        backup_codes = mfa_service.generate_backup_codes()
        hashed_codes = mfa_service.hash_backup_codes(backup_codes)
        
        # Test valid backup code
        is_valid, used_hash = mfa_service.verify_backup_code(hashed_codes, backup_codes[0])
        assert is_valid is True
        assert used_hash is not None
        
        # Test invalid backup code
        is_valid, used_hash = mfa_service.verify_backup_code(hashed_codes, "INVALID1")
        assert is_valid is False
        assert used_hash is None
    
    @pytest.mark.asyncio
    async def test_phone_number_validation(self, mfa_service):
        """Test phone number validation"""
        # Valid phone numbers
        assert mfa_service.validate_phone_number("+1234567890") is True
        assert mfa_service.validate_phone_number("+44 20 7946 0958") is True
        
        # Invalid phone numbers
        assert mfa_service.validate_phone_number("123") is False
        assert mfa_service.validate_phone_number("abc") is False
        assert mfa_service.validate_phone_number("") is False


@pytest.mark.skipif(not SECURITY_SERVICES_AVAILABLE, reason="Security services not available")
class TestThreatDetectionService:
    """Test threat detection service"""
    
    @pytest.fixture
    async def threat_service(self):
        """Create threat detection service instance"""
        service = ThreatDetectionService()
        await service.initialize()
        return service
    
    @pytest.mark.asyncio
    async def test_malicious_user_agent_detection(self, threat_service):
        """Test malicious user agent detection"""
        # Test malicious user agents
        malicious_agents = [
            "sqlmap/1.0",
            "Nikto/2.1.6",
            "python-requests/2.25.1",
            "curl/7.68.0"
        ]
        
        for agent in malicious_agents:
            is_malicious = threat_service._is_malicious_user_agent(agent)
            assert is_malicious is True, f"Should detect {agent} as malicious"
        
        # Test legitimate user agents
        legitimate_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        ]
        
        for agent in legitimate_agents:
            is_malicious = threat_service._is_malicious_user_agent(agent)
            assert is_malicious is False, f"Should not detect {agent} as malicious"
    
    @pytest.mark.asyncio
    async def test_sql_injection_detection(self, threat_service):
        """Test SQL injection pattern detection"""
        # Test SQL injection patterns
        sql_patterns = [
            "SELECT * FROM users WHERE id = 1 OR 1=1",
            "'; DROP TABLE users; --",
            "UNION SELECT password FROM users",
            "admin'--"
        ]
        
        for pattern in sql_patterns:
            params = {"query": pattern}
            is_sql_injection = threat_service._check_sql_injection(params, "")
            assert is_sql_injection is True, f"Should detect SQL injection in: {pattern}"
        
        # Test legitimate queries
        legitimate_queries = [
            "search for ASL tutorials",
            "user@example.com",
            "normal search term"
        ]
        
        for query in legitimate_queries:
            params = {"query": query}
            is_sql_injection = threat_service._check_sql_injection(params, "")
            assert is_sql_injection is False, f"Should not detect SQL injection in: {query}"
    
    @pytest.mark.asyncio
    async def test_xss_detection(self, threat_service):
        """Test XSS attack detection"""
        # Test XSS patterns
        xss_patterns = [
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "<img src=x onerror=alert(1)>",
            "eval('malicious code')"
        ]
        
        for pattern in xss_patterns:
            params = {"content": pattern}
            is_xss = threat_service._check_xss_attempt(params, "")
            assert is_xss is True, f"Should detect XSS in: {pattern}"
        
        # Test legitimate content
        legitimate_content = [
            "This is normal text content",
            "<p>Valid HTML paragraph</p>",
            "user@example.com"
        ]
        
        for content in legitimate_content:
            params = {"content": content}
            is_xss = threat_service._check_xss_attempt(params, "")
            assert is_xss is False, f"Should not detect XSS in: {content}"
    
    @pytest.mark.asyncio
    async def test_request_analysis(self, threat_service):
        """Test comprehensive request analysis"""
        # Test malicious request
        malicious_request = {
            "ip_address": "192.168.1.100",
            "user_agent": "sqlmap/1.0",
            "path": "/api/users",
            "method": "GET",
            "params": {"id": "1 OR 1=1"},
            "headers": {}
        }
        
        result = await threat_service.analyze_request(malicious_request)
        
        assert "malicious_user_agent" in result["threats"]
        assert "sql_injection" in result["threats"]
        assert result["blocked"] is True
        assert result["severity"] == "critical"
    
    @pytest.mark.asyncio
    async def test_login_analysis(self, threat_service):
        """Test login attempt analysis"""
        ip_address = "192.168.1.100"
        user_identifier = "test@example.com"
        
        # Simulate multiple failed login attempts
        for i in range(6):
            result = await threat_service.analyze_login_attempt(
                ip_address=ip_address,
                user_identifier=user_identifier,
                success=False,
                user_agent="Mozilla/5.0"
            )
        
        # Should detect brute force attack
        assert "brute_force_attack" in result["threats"]
        assert result["blocked"] is True
        assert result["severity"] == "high"
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, threat_service):
        """Test rate limiting functionality"""
        ip_address = "192.168.1.100"
        
        # Simulate many requests
        for i in range(1001):
            threat_service.api_requests[ip_address].append(datetime.utcnow())
        
        rate_limit_result = threat_service._check_rate_limiting(ip_address, None)
        
        assert rate_limit_result["exceeded"] is True
        assert rate_limit_result["ip_requests"] > 1000


@pytest.mark.skipif(not SECURITY_SERVICES_AVAILABLE, reason="Security services not available")
class TestSecurityAuditService:
    """Test security audit service"""
    
    @pytest.fixture
    async def audit_service(self):
        """Create audit service instance"""
        config = {
            "audit_log_path": "test_audit.log",
            "retention_days": 30
        }
        service = SecurityAuditService(config=config)
        await service.initialize()
        return service
    
    @pytest.mark.asyncio
    async def test_log_event(self, audit_service):
        """Test audit event logging"""
        await audit_service.log_event(
            event_type=AuditEventType.LOGIN_SUCCESS,
            severity=AuditSeverity.INFO,
            message="Test login event",
            user_id="test_user_123",
            ip_address="192.168.1.100",
            details={"test": "data"}
        )
        
        # Check that event was added to buffer
        assert len(audit_service.recent_events) == 1
        
        event = audit_service.recent_events[0]
        assert event["event_type"] == "login_success"
        assert event["severity"] == "info"
        assert event["user_id"] == "test_user_123"
        assert event["ip_address"] == "192.168.1.100"
    
    @pytest.mark.asyncio
    async def test_authentication_event_logging(self, audit_service):
        """Test authentication event logging"""
        await audit_service.log_authentication_event(
            event_type=AuditEventType.LOGIN_FAILED,
            user_identifier="test@example.com",
            success=False,
            ip_address="192.168.1.100",
            details={"reason": "invalid_password"}
        )
        
        event = audit_service.recent_events[0]
        assert event["event_type"] == "login_failed"
        assert event["severity"] == "warning"
        assert event["details"]["user_identifier"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_search_audit_logs(self, audit_service):
        """Test audit log searching"""
        # Add test events
        await audit_service.log_event(
            event_type=AuditEventType.LOGIN_SUCCESS,
            severity=AuditSeverity.INFO,
            message="Login 1",
            user_id="user1"
        )
        
        await audit_service.log_event(
            event_type=AuditEventType.LOGIN_FAILED,
            severity=AuditSeverity.WARNING,
            message="Login 2",
            user_id="user2"
        )
        
        # Search by event type
        results = await audit_service.search_audit_logs(
            event_types=[AuditEventType.LOGIN_SUCCESS]
        )
        
        assert len(results) == 1
        assert results[0]["event_type"] == "login_success"
        
        # Search by user ID
        results = await audit_service.search_audit_logs(user_id="user1")
        
        assert len(results) == 1
        assert results[0]["user_id"] == "user1"
    
    @pytest.mark.asyncio
    async def test_audit_statistics(self, audit_service):
        """Test audit statistics generation"""
        # Add test events
        for i in range(5):
            await audit_service.log_event(
                event_type=AuditEventType.LOGIN_SUCCESS,
                severity=AuditSeverity.INFO,
                message=f"Login {i}",
                user_id=f"user{i}"
            )
        
        for i in range(3):
            await audit_service.log_event(
                event_type=AuditEventType.LOGIN_FAILED,
                severity=AuditSeverity.WARNING,
                message=f"Failed login {i}",
                user_id=f"user{i}"
            )
        
        stats = await audit_service.get_audit_statistics()
        
        assert stats["total_events"] == 8
        assert stats["event_types"]["login_success"] == 5
        assert stats["event_types"]["login_failed"] == 3
        assert stats["severity_levels"]["info"] == 5
        assert stats["severity_levels"]["warning"] == 3


@pytest.mark.skipif(not SECURITY_SERVICES_AVAILABLE, reason="Security services not available")
class TestVulnerabilityScanner:
    """Test vulnerability scanner"""
    
    @pytest.fixture
    async def vuln_scanner(self):
        """Create vulnerability scanner instance"""
        config = {
            "scan_interval": 3600,
            "enable_dependency_scan": True,
            "enable_config_scan": True,
            "enable_network_scan": False,  # Disable for testing
            "enable_web_scan": False  # Disable for testing
        }
        scanner = VulnerabilityScanner(config=config)
        await scanner.initialize()
        return scanner
    
    @pytest.mark.asyncio
    async def test_config_file_scanning(self, vuln_scanner):
        """Test configuration file vulnerability scanning"""
        # Create temporary config file with vulnerabilities
        import tempfile
        import os
        
        config_content = """
        debug = true
        password = admin
        secret_key = "hardcoded_secret_123"
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(config_content)
            temp_file = f.name
        
        try:
            from pathlib import Path
            vulnerabilities = await vuln_scanner._scan_config_file(Path(temp_file))
            
            # Should detect debug mode and weak credentials
            assert len(vulnerabilities) >= 2
            
            vuln_types = [v["type"] for v in vulnerabilities]
            assert "insecure_config" in vuln_types
            
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_port_scanning(self, vuln_scanner):
        """Test network port scanning"""
        # Test if port is open (this will likely fail in test environment)
        is_open = await vuln_scanner._is_port_open("localhost", 80, timeout=0.1)
        
        # Just verify the method works without error
        assert isinstance(is_open, bool)
    
    @pytest.mark.asyncio
    async def test_vulnerability_report_generation(self, vuln_scanner):
        """Test vulnerability report generation"""
        # Add some test vulnerabilities
        vuln_scanner.vulnerabilities = [
            {
                "type": "outdated_dependency",
                "severity": "high",
                "title": "Test vulnerability",
                "description": "Test description"
            },
            {
                "type": "insecure_config",
                "severity": "medium",
                "title": "Test config issue",
                "description": "Test config description"
            }
        ]
        
        report = await vuln_scanner.get_vulnerability_report()
        
        assert report["total_vulnerabilities"] == 2
        assert report["summary"]["total"] == 2
        assert report["summary"]["by_severity"]["high"] == 1
        assert report["summary"]["by_severity"]["medium"] == 1


@pytest.mark.skipif(not SECURITY_SERVICES_AVAILABLE, reason="Security services not available")
class TestSecurityIntegration:
    """Test security service integration"""
    
    @pytest.mark.asyncio
    async def test_middleware_threat_detection(self):
        """Test middleware integration with threat detection"""
        from fastapi import FastAPI, Request
        from fastapi.responses import JSONResponse
        
        app = FastAPI()
        
        # Add security middleware
        middleware = AuthenticationMiddleware(app)
        
        # Mock request with malicious content
        mock_request = Mock(spec=Request)
        mock_request.url.path = "/api/test"
        mock_request.method = "GET"
        mock_request.client.host = "192.168.1.100"
        mock_request.headers = {"user-agent": "sqlmap/1.0"}
        mock_request.query_params = {"id": "1 OR 1=1"}
        
        # Mock call_next
        async def mock_call_next(request):
            return JSONResponse({"message": "success"})
        
        # Test that malicious request is blocked
        with patch.object(middleware, '_get_threat_detection_service') as mock_threat_service:
            mock_service = AsyncMock()
            mock_service.analyze_request.return_value = {
                "blocked": True,
                "threats": ["sql_injection", "malicious_user_agent"],
                "severity": "critical"
            }
            mock_threat_service.return_value = mock_service
            
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_security_api_endpoints(self):
        """Test security API endpoints"""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        
        app = FastAPI()
        app.include_router(security_router)
        
        client = TestClient(app)
        
        # Test health check endpoint (should work without auth)
        response = client.get("/api/v1/security/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "healthy" in data
        assert "services" in data
    
    def test_security_configuration_loading(self):
        """Test security configuration loading"""
        import yaml
        from pathlib import Path
        
        config_path = Path("config/security.yaml")
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Verify key configuration sections exist
            assert "mfa" in config
            assert "threat_detection" in config
            assert "audit" in config
            assert "vulnerability_scanner" in config
            assert "password_policy" in config
            
            # Verify MFA configuration
            assert config["mfa"]["enabled"] is True
            assert "totp" in config["mfa"]
            assert "sms" in config["mfa"]
            assert "email" in config["mfa"]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])