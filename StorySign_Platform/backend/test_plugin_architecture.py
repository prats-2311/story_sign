"""
Test suite for plugin architecture implementation.
Tests plugin loading, security, API access, and basic execution.
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from models.plugin import (
    PluginManifest, PluginPermission, PluginStatus, Plugin, PluginData
)
from core.plugin_interface import (
    PluginInterface, PluginContext, HookContext, PlatformServices, HookType
)
from core.plugin_security import (
    PluginSandboxManager, SecurityPolicy, ResourceLimits, SecurityLevel,
    PluginSecurityManager, ResourceExceededError, SecurityViolationError
)
from services.plugin_service import PluginService, PluginDiscovery, PluginLoader
from core.plugin_api import PluginAPI, PluginAPIFactory, PermissionDeniedError
from repositories.plugin_repository import PluginRepository


class TestPluginManifest:
    """Test plugin manifest validation and structure"""
    
    def test_valid_manifest_creation(self):
        """Test creating a valid plugin manifest"""
        manifest = PluginManifest(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            entry_point="main.py",
            min_platform_version="1.0.0",
            permissions=[PluginPermission.READ_USER_DATA]
        )
        
        assert manifest.id == "test-plugin"
        assert manifest.name == "Test Plugin"
        assert manifest.version == "1.0.0"
        assert PluginPermission.READ_USER_DATA in manifest.permissions
    
    def test_manifest_validation(self):
        """Test manifest validation"""
        from core.plugin_interface import PluginValidator
        
        # Valid manifest
        valid_manifest = PluginManifest(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            entry_point="main.py",
            min_platform_version="1.0.0"
        )
        
        errors = PluginValidator.validate_manifest(valid_manifest)
        assert len(errors) == 0
        
        # Invalid manifest - missing required fields
        invalid_manifest = PluginManifest(
            id="",
            name="",
            version="invalid-version",
            description="A test plugin",
            author="Test Author",
            entry_point="",
            min_platform_version="1.0.0"
        )
        
        errors = PluginValidator.validate_manifest(invalid_manifest)
        assert len(errors) > 0
        assert any("Plugin ID is required" in error for error in errors)
        assert any("Plugin name is required" in error for error in errors)
        assert any("Plugin entry point is required" in error for error in errors)


class TestPluginSecurity:
    """Test plugin security and sandboxing"""
    
    def test_security_policy_creation(self):
        """Test security policy creation"""
        policy = SecurityPolicy(
            security_level=SecurityLevel.STRICT,
            resource_limits=ResourceLimits(max_memory_mb=50, max_cpu_time_seconds=2.0)
        )
        
        assert policy.security_level == SecurityLevel.STRICT
        assert policy.resource_limits.max_memory_mb == 50
        assert 'os' in policy.blocked_modules
        assert 'eval' in policy.blocked_builtins
    
    def test_plugin_sandbox_manager(self):
        """Test plugin sandbox manager"""
        permissions = [PluginPermission.READ_USER_DATA]
        policy = SecurityPolicy()
        
        sandbox = PluginSandboxManager("test-plugin", permissions, policy)
        
        assert sandbox.plugin_id == "test-plugin"
        assert sandbox.permissions == permissions
        assert sandbox.policy == policy
    
    @pytest.mark.asyncio
    async def test_sandbox_execution(self):
        """Test sandboxed execution"""
        permissions = [PluginPermission.READ_USER_DATA]
        policy = SecurityPolicy(
            resource_limits=ResourceLimits(max_execution_time_seconds=1.0)
        )
        
        sandbox = PluginSandboxManager("test-plugin", permissions, policy)
        
        # Test successful execution
        def safe_function():
            return "Hello, World!"
        
        result = await sandbox.execute_plugin_function(safe_function)
        assert result == "Hello, World!"
    
    def test_security_manager(self):
        """Test plugin security manager"""
        security_manager = PluginSecurityManager()
        
        # Test default policy
        default_policy = security_manager.get_plugin_policy("unknown-plugin")
        assert default_policy.security_level == SecurityLevel.STANDARD
        
        # Test custom policy
        custom_policy = SecurityPolicy(security_level=SecurityLevel.STRICT)
        security_manager.set_plugin_policy("test-plugin", custom_policy)
        
        retrieved_policy = security_manager.get_plugin_policy("test-plugin")
        assert retrieved_policy.security_level == SecurityLevel.STRICT
    
    def test_permission_validation(self):
        """Test permission validation"""
        security_manager = PluginSecurityManager()
        
        # Test safe permissions
        safe_permissions = [PluginPermission.READ_USER_DATA]
        violations = security_manager.validate_plugin_permissions("test-plugin", safe_permissions)
        assert len(violations) == 0
        
        # Test dangerous permissions in strict mode
        strict_policy = SecurityPolicy(security_level=SecurityLevel.ISOLATED)
        security_manager.set_plugin_policy("strict-plugin", strict_policy)
        
        dangerous_permissions = [PluginPermission.FILE_SYSTEM_WRITE, PluginPermission.NETWORK_ACCESS]
        violations = security_manager.validate_plugin_permissions("strict-plugin", dangerous_permissions)
        assert len(violations) > 0


class MockPlugin(PluginInterface):
    """Mock plugin for testing"""
    
    def __init__(self, manifest: PluginManifest, plugin_id: str):
        super().__init__(manifest, plugin_id)
        self.initialized = False
        self.cleaned_up = False
    
    async def initialize(self, context: PluginContext) -> bool:
        """Initialize the mock plugin"""
        self.initialized = True
        
        # Register a test hook
        self.register_hook(
            "test_hook", HookType.FILTER, "test_target", 
            self._test_hook_handler, priority=100
        )
        
        return True
    
    async def cleanup(self) -> bool:
        """Cleanup the mock plugin"""
        self.cleaned_up = True
        return True
    
    async def get_status(self) -> dict:
        """Get plugin status"""
        return {
            'initialized': self.initialized,
            'cleaned_up': self.cleaned_up,
            'hooks_registered': len(self._hooks)
        }
    
    async def _test_hook_handler(self, context: HookContext) -> str:
        """Test hook handler"""
        return f"Hook executed by {self.plugin_id}"


class TestPluginInterface:
    """Test plugin interface and base functionality"""
    
    def test_plugin_creation(self):
        """Test plugin creation"""
        manifest = PluginManifest(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            entry_point="main.py",
            min_platform_version="1.0.0"
        )
        
        plugin = MockPlugin(manifest, "test-plugin")
        
        assert plugin.plugin_id == "test-plugin"
        assert plugin.manifest == manifest
        assert not plugin._is_initialized
    
    @pytest.mark.asyncio
    async def test_plugin_initialization(self):
        """Test plugin initialization"""
        manifest = PluginManifest(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            entry_point="main.py",
            min_platform_version="1.0.0"
        )
        
        plugin = MockPlugin(manifest, "test-plugin")
        
        # Mock platform services
        platform_services = Mock(spec=PlatformServices)
        
        context = PluginContext(
            user_id="test-user",
            session_id="test-session",
            module_name="test",
            request_data={},
            platform_services=platform_services,
            plugin_data={},
            timestamp=datetime.utcnow()
        )
        
        success = await plugin.initialize(context)
        assert success
        assert plugin.initialized
        
        # Check hook registration
        assert "test_hook" in plugin.hooks
        assert len(plugin.hooks["test_hook"]) == 1
    
    @pytest.mark.asyncio
    async def test_hook_execution(self):
        """Test hook execution"""
        manifest = PluginManifest(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            entry_point="main.py",
            min_platform_version="1.0.0"
        )
        
        plugin = MockPlugin(manifest, "test-plugin")
        
        # Initialize plugin
        platform_services = Mock(spec=PlatformServices)
        context = PluginContext(
            user_id="test-user",
            session_id="test-session",
            module_name="test",
            request_data={},
            platform_services=platform_services,
            plugin_data={},
            timestamp=datetime.utcnow()
        )
        
        await plugin.initialize(context)
        
        # Execute hook
        hook_context = HookContext(
            hook_name="test_hook",
            hook_type=HookType.FILTER,
            target_function="test_target",
            args=(),
            kwargs={},
            plugin_context=context,
            result=None
        )
        
        result = await plugin.execute_hook(hook_context)
        assert result == "Hook executed by test-plugin"


class TestPluginDiscovery:
    """Test plugin discovery functionality"""
    
    @pytest.mark.asyncio
    async def test_local_plugin_discovery(self):
        """Test discovering plugins from local directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            plugins_dir = Path(temp_dir)
            
            # Create a test plugin directory
            plugin_dir = plugins_dir / "test-plugin"
            plugin_dir.mkdir()
            
            # Create manifest file
            manifest_data = {
                "id": "test-plugin",
                "name": "Test Plugin",
                "version": "1.0.0",
                "description": "A test plugin",
                "author": "Test Author",
                "entry_point": "main.py",
                "min_platform_version": "1.0.0",
                "permissions": ["read:user_data"]
            }
            
            manifest_file = plugin_dir / "manifest.json"
            with open(manifest_file, 'w') as f:
                json.dump(manifest_data, f)
            
            # Test discovery
            discovery = PluginDiscovery(str(plugins_dir))
            manifests = await discovery.discover_local_plugins()
            
            assert len(manifests) == 1
            assert manifests[0].id == "test-plugin"
            assert manifests[0].name == "Test Plugin"


class TestPluginAPI:
    """Test plugin API functionality"""
    
    def test_plugin_api_creation(self):
        """Test plugin API creation"""
        permissions = [PluginPermission.READ_USER_DATA, PluginPermission.WRITE_USER_DATA]
        platform_services = Mock(spec=PlatformServices)
        security_manager = Mock(spec=PluginSecurityManager)
        
        api = PluginAPI("test-plugin", permissions, platform_services, security_manager)
        
        assert api.plugin_id == "test-plugin"
        assert api.permissions == permissions
        assert hasattr(api, 'user')
        assert hasattr(api, 'content')
        assert hasattr(api, 'analytics')
    
    def test_permission_checking(self):
        """Test permission checking"""
        permissions = [PluginPermission.READ_USER_DATA]
        platform_services = Mock(spec=PlatformServices)
        security_manager = Mock(spec=PluginSecurityManager)
        
        api = PluginAPI("test-plugin", permissions, platform_services, security_manager)
        
        # Should not raise exception for allowed permission
        api._check_permission(PluginPermission.READ_USER_DATA)
        
        # Should raise exception for disallowed permission
        with pytest.raises(PermissionDeniedError):
            api._check_permission(PluginPermission.WRITE_USER_DATA)
    
    @pytest.mark.asyncio
    async def test_user_api(self):
        """Test user API functionality"""
        permissions = [PluginPermission.READ_USER_DATA]
        platform_services = Mock(spec=PlatformServices)
        security_manager = Mock(spec=PluginSecurityManager)
        
        # Mock user service
        mock_user = Mock()
        mock_user.id = "test-user"
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.first_name = "Test"
        mock_user.last_name = "User"
        mock_user.preferences = {"theme": "dark"}
        
        platform_services.user.get_user_by_id = AsyncMock(return_value=mock_user)
        
        api = PluginAPI("test-plugin", permissions, platform_services, security_manager)
        
        user_data = await api.user.get_current_user("test-user")
        
        assert user_data['id'] == "test-user"
        assert user_data['username'] == "testuser"
        assert user_data['preferences']['theme'] == "dark"


class TestPluginService:
    """Test plugin service functionality"""
    
    @pytest.mark.asyncio
    async def test_plugin_service_initialization(self):
        """Test plugin service initialization"""
        # Mock dependencies
        database_service = Mock()
        platform_services = Mock(spec=PlatformServices)
        
        service = PluginService(database_service, platform_services)
        
        assert service.db == database_service
        assert service.platform_services == platform_services
        assert isinstance(service.loaded_plugins, dict)
        assert isinstance(service.hooks, dict)
    
    @pytest.mark.asyncio
    async def test_hook_execution(self):
        """Test hook execution through plugin service"""
        # Mock dependencies
        database_service = Mock()
        platform_services = Mock(spec=PlatformServices)
        
        service = PluginService(database_service, platform_services)
        
        # Create and register a mock plugin
        manifest = PluginManifest(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            entry_point="main.py",
            min_platform_version="1.0.0"
        )
        
        plugin = MockPlugin(manifest, "test-plugin")
        await plugin.initialize(PluginContext(
            user_id="test-user",
            session_id="test-session",
            module_name="test",
            request_data={},
            platform_services=platform_services,
            plugin_data={},
            timestamp=datetime.utcnow()
        ))
        
        # Register plugin manually for testing
        service.loaded_plugins["test-plugin"] = plugin
        await service._register_plugin_hooks("test-plugin", plugin)
        
        # Execute hooks
        result = await service.execute_hooks(
            "test_hook", HookType.FILTER, "test_target",
            user_id="test-user", result="initial"
        )
        
        assert result == "Hook executed by test-plugin"


class TestPluginRepository:
    """Test plugin repository functionality"""
    
    @pytest.mark.asyncio
    async def test_plugin_crud_operations(self):
        """Test basic CRUD operations"""
        # This would require a real database session in practice
        # For now, we'll test the interface
        
        session = Mock()
        repository = PluginRepository(session)
        
        # Test that methods exist and have correct signatures
        assert hasattr(repository, 'get_by_name')
        assert hasattr(repository, 'get_active_plugins')
        assert hasattr(repository, 'update_plugin_status')


def test_plugin_architecture_integration():
    """Integration test for plugin architecture components"""
    # Test that all components can be imported and instantiated
    
    # Test manifest creation
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
    
    # Test security components
    security_manager = PluginSecurityManager()
    policy = security_manager.get_plugin_policy("integration-test")
    
    # Test API factory
    platform_services = Mock(spec=PlatformServices)
    api_factory = PluginAPIFactory(platform_services, security_manager)
    api = api_factory.create_api("integration-test", manifest.permissions)
    
    # Verify all components are properly connected
    assert manifest.id == "integration-test"
    assert policy.security_level == SecurityLevel.STANDARD
    assert api.plugin_id == "integration-test"
    assert PluginPermission.READ_USER_DATA in api.permissions


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])