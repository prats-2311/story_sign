"""
Simplified test suite for plugin security features.
Tests security validation without interfering with test runner.
"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime

from models.plugin import PluginManifest, PluginPermission
from core.plugin_security import (
    PluginSecurityManager, PluginValidator, PluginIsolationManager,
    SecurityPolicy, ResourceLimits, SecurityLevel
)


class TestPluginValidator:
    """Test plugin validation functionality"""
    
    def test_validate_plugin_code_basic(self):
        """Test basic plugin code validation"""
        manifest = PluginManifest(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            description="Test",
            author="Test",
            entry_point="main.py",
            min_platform_version="1.0.0",
            permissions=[]
        )
        
        # Test dangerous imports
        dangerous_code = "import os\nimport subprocess"
        issues = PluginValidator.validate_plugin_code(dangerous_code, manifest)
        assert len(issues) > 0
        assert any("import os" in issue for issue in issues)
        
        # Test safe code
        safe_code = "import json\nimport datetime"
        issues = PluginValidator.validate_plugin_code(safe_code, manifest)
        # Should have no issues for basic imports
        dangerous_issues = [issue for issue in issues if "dangerous import" in issue.lower()]
        assert len(dangerous_issues) == 0
    
    def test_scan_malicious_patterns(self):
        """Test malicious pattern detection"""
        malicious_code = """
import base64
encoded = base64.b64decode('test')
exec(encoded)
"""
        
        issues = PluginValidator.scan_for_malicious_patterns(malicious_code)
        assert len(issues) > 0
        assert any("obfuscation" in issue.lower() for issue in issues)
    
    def test_file_permission_validation(self):
        """Test file permission validation"""
        manifest_no_perms = PluginManifest(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            description="Test",
            author="Test",
            entry_point="main.py",
            min_platform_version="1.0.0",
            permissions=[]
        )
        
        file_code = "with open('test.txt', 'w') as f: f.write('test')"
        issues = PluginValidator.validate_plugin_code(file_code, manifest_no_perms)
        
        # Should detect file operations without permission
        file_issues = [issue for issue in issues if "file system permission" in issue.lower()]
        assert len(file_issues) > 0


class TestPluginSecurityManager:
    """Test plugin security manager"""
    
    def test_security_manager_creation(self):
        """Test security manager creation"""
        manager = PluginSecurityManager()
        
        assert isinstance(manager.security_policies, dict)
        assert isinstance(manager.default_policy, SecurityPolicy)
        assert isinstance(manager.security_violations, dict)
    
    def test_manifest_validation(self):
        """Test manifest validation"""
        manager = PluginSecurityManager()
        
        # Test clean manifest
        clean_manifest = PluginManifest(
            id="clean-plugin",
            name="Clean Plugin",
            version="1.0.0",
            description="A clean plugin",
            author="Test",
            entry_point="main.py",
            min_platform_version="1.0.0",
            permissions=[PluginPermission.READ_USER_DATA]
        )
        
        issues = manager.validate_plugin_manifest(clean_manifest)
        # Should have no security issues
        security_issues = [issue for issue in issues if any(
            keyword in issue.lower() for keyword in ['suspicious', 'dangerous']
        )]
        assert len(security_issues) == 0
        
        # Test suspicious manifest
        suspicious_manifest = PluginManifest(
            id="hack-plugin",
            name="Hack Tool",
            version="1.0.0",
            description="This plugin can hack systems",
            author="Hacker",
            entry_point="main.py",
            min_platform_version="1.0.0",
            permissions=[PluginPermission.FILE_SYSTEM_WRITE, PluginPermission.NETWORK_ACCESS]
        )
        
        issues = manager.validate_plugin_manifest(suspicious_manifest)
        assert len(issues) > 0
        assert any("suspicious keyword" in issue.lower() for issue in issues)
        assert any("dangerous permission combination" in issue.lower() for issue in issues)
    
    def test_permission_validation(self):
        """Test permission validation"""
        manager = PluginSecurityManager()
        
        # Test reasonable permissions
        reasonable_permissions = [PluginPermission.READ_USER_DATA]
        violations = manager.validate_plugin_permissions("test-plugin", reasonable_permissions)
        assert len(violations) == 0
        
        # Test excessive permissions
        excessive_permissions = [
            PluginPermission.READ_USER_DATA,
            PluginPermission.WRITE_USER_DATA,
            PluginPermission.FILE_SYSTEM_READ,
            PluginPermission.FILE_SYSTEM_WRITE,
            PluginPermission.NETWORK_ACCESS,
            PluginPermission.DATABASE_WRITE
        ]
        
        violations = manager.validate_plugin_permissions("test-plugin", excessive_permissions)
        assert len(violations) > 0
        assert any("excessive permissions" in violation.lower() for violation in violations)
    
    def test_security_violation_recording(self):
        """Test security violation recording"""
        manager = PluginSecurityManager()
        
        manager.record_security_violation(
            "test-plugin",
            "test_violation",
            "Test violation details",
            "medium"
        )
        
        assert "test-plugin" in manager.security_violations
        assert len(manager.security_violations["test-plugin"]) == 1
        
        violation = manager.security_violations["test-plugin"][0]
        assert violation['type'] == "test_violation"
        assert violation['severity'] == "medium"
        assert 'timestamp' in violation
    
    def test_security_report_generation(self):
        """Test security report generation"""
        manager = PluginSecurityManager()
        
        # Set up test data
        policy = SecurityPolicy(security_level=SecurityLevel.STRICT)
        manager.set_plugin_policy("test-plugin", policy)
        
        manager.record_security_violation(
            "test-plugin",
            "test_violation",
            "Test violation details",
            "medium"
        )
        
        report = manager.get_security_report("test-plugin")
        
        assert report['plugin_id'] == "test-plugin"
        assert report['security_policy']['security_level'] == SecurityLevel.STRICT
        assert report['violation_count'] == 1
        assert report['critical_violations'] == 0
        assert 'last_check' in report


class TestPluginIsolationManager:
    """Test plugin isolation manager"""
    
    def test_isolation_manager_creation(self):
        """Test isolation manager creation"""
        limits = ResourceLimits(
            max_memory_mb=100,
            max_cpu_time_seconds=5.0,
            max_execution_time_seconds=10.0
        )
        
        manager = PluginIsolationManager("test-plugin", limits)
        
        assert manager.plugin_id == "test-plugin"
        assert manager.resource_limits == limits
        assert manager.resource_usage['memory_mb'] == 0
    
    def test_resource_monitoring(self):
        """Test resource usage monitoring"""
        limits = ResourceLimits(max_file_operations=5)
        manager = PluginIsolationManager("test-plugin", limits)
        
        # Record some operations
        manager.record_operation('file_operations', 3)
        assert manager.resource_usage['file_operations'] == 3
        
        # Should not exceed limit yet
        manager.record_operation('file_operations', 1)
        assert manager.resource_usage['file_operations'] == 4
        
        # Should raise exception when limit exceeded
        from core.plugin_security import ResourceExceededError
        with pytest.raises(ResourceExceededError):
            manager.record_operation('file_operations', 2)
    
    def test_usage_report(self):
        """Test usage report generation"""
        limits = ResourceLimits()
        manager = PluginIsolationManager("test-plugin", limits)
        
        manager.record_operation('file_operations', 2)
        
        report = manager.get_usage_report()
        
        assert report['plugin_id'] == "test-plugin"
        assert report['resource_usage']['file_operations'] == 2
        assert 'resource_limits' in report


class TestSecurityPolicies:
    """Test security policy functionality"""
    
    def test_security_policy_creation(self):
        """Test security policy creation"""
        policy = SecurityPolicy(
            security_level=SecurityLevel.STRICT,
            resource_limits=ResourceLimits(max_memory_mb=50)
        )
        
        assert policy.security_level == SecurityLevel.STRICT
        assert policy.resource_limits.max_memory_mb == 50
        assert 'os' in policy.blocked_modules
        assert 'eval' in policy.blocked_builtins
    
    def test_resource_limits(self):
        """Test resource limits configuration"""
        limits = ResourceLimits(
            max_memory_mb=100,
            max_cpu_time_seconds=5.0,
            max_file_operations=10,
            max_network_requests=5
        )
        
        assert limits.max_memory_mb == 100
        assert limits.max_cpu_time_seconds == 5.0
        assert limits.max_file_operations == 10
        assert limits.max_network_requests == 5


class TestIntegration:
    """Integration tests for security components"""
    
    def test_complete_validation_workflow(self):
        """Test complete validation workflow"""
        # Create security manager
        security_manager = PluginSecurityManager()
        
        # Create manifest
        manifest = PluginManifest(
            id="integration-test",
            name="Integration Test Plugin",
            version="1.0.0",
            description="Integration test",
            author="Test",
            entry_point="main.py",
            min_platform_version="1.0.0",
            permissions=[PluginPermission.READ_USER_DATA]
        )
        
        # Validate manifest
        manifest_issues = security_manager.validate_plugin_manifest(manifest)
        # Should be clean
        security_issues = [issue for issue in manifest_issues if any(
            keyword in issue.lower() for keyword in ['suspicious', 'dangerous']
        )]
        assert len(security_issues) == 0
        
        # Validate code
        safe_code = """
import json
import datetime

def process_data(data):
    return {
        'processed': True,
        'timestamp': datetime.datetime.now().isoformat(),
        'data_length': len(data) if data else 0
    }
"""
        
        code_issues = security_manager.validate_plugin_code(safe_code, manifest)
        # Should have no critical issues
        critical_issues = [
            issue for issue in code_issues 
            if any(keyword in issue.lower() for keyword in ['dangerous', 'malicious'])
        ]
        assert len(critical_issues) == 0
        
        # Check security report
        report = security_manager.get_security_report("integration-test")
        assert report['plugin_id'] == "integration-test"
    
    def test_security_violation_detection(self):
        """Test security violation detection"""
        security_manager = PluginSecurityManager()
        
        manifest = PluginManifest(
            id="violation-test",
            name="Violation Test",
            version="1.0.0",
            description="Test violations",
            author="Test",
            entry_point="main.py",
            min_platform_version="1.0.0",
            permissions=[]  # No permissions
        )
        
        # Test code that should trigger violations
        violating_code = """
import os
import subprocess
with open('/etc/passwd', 'r') as f:
    data = f.read()
os.system('rm -rf /')
"""
        
        issues = security_manager.validate_plugin_code(violating_code, manifest)
        
        # Should detect multiple security issues
        assert len(issues) > 0
        assert any("dangerous import" in issue.lower() for issue in issues)
        assert any("file system permission" in issue.lower() for issue in issues)


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])