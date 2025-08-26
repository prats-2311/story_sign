"""
Plugin interface definitions for the StorySign platform.
Defines the contracts and APIs that plugins must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime

from models.plugin import PluginManifest, PluginPermission


class HookType(str, Enum):
    """Types of plugin hooks"""
    BEFORE = "before"
    AFTER = "after"
    REPLACE = "replace"
    FILTER = "filter"


class PluginEventType(str, Enum):
    """Plugin system events"""
    PLUGIN_LOADED = "plugin_loaded"
    PLUGIN_UNLOADED = "plugin_unloaded"
    PLUGIN_ERROR = "plugin_error"
    HOOK_EXECUTED = "hook_executed"


@dataclass
class PluginContext:
    """Context provided to plugins during execution"""
    user_id: Optional[str]
    session_id: Optional[str]
    module_name: str
    request_data: Dict[str, Any]
    platform_services: 'PlatformServices'
    plugin_data: Dict[str, Any]
    timestamp: datetime


@dataclass
class HookContext:
    """Context for hook execution"""
    hook_name: str
    hook_type: HookType
    target_function: str
    args: tuple
    kwargs: Dict[str, Any]
    plugin_context: PluginContext
    result: Any = None  # For AFTER hooks


class PlatformServices:
    """Platform services available to plugins"""
    
    def __init__(self, database_service, user_service, content_service, 
                 analytics_service, ai_service, websocket_manager):
        self.database = database_service
        self.user = user_service
        self.content = content_service
        self.analytics = analytics_service
        self.ai = ai_service
        self.websocket = websocket_manager
    
    async def get_user_data(self, user_id: str, data_key: str) -> Any:
        """Get user-specific data"""
        pass
    
    async def set_user_data(self, user_id: str, data_key: str, data_value: Any) -> bool:
        """Set user-specific data"""
        pass
    
    async def send_notification(self, user_id: str, message: str, type: str = "info") -> bool:
        """Send notification to user"""
        pass
    
    async def log_event(self, event_type: str, data: Dict[str, Any]) -> bool:
        """Log analytics event"""
        pass


class PluginInterface(ABC):
    """Base interface that all plugins must implement"""
    
    def __init__(self, manifest: PluginManifest, plugin_id: str):
        self.manifest = manifest
        self.plugin_id = plugin_id
        self._hooks: Dict[str, List[Callable]] = {}
        self._ui_components: Dict[str, Any] = {}
        self._api_endpoints: Dict[str, Any] = {}
        self._is_initialized = False
    
    @abstractmethod
    async def initialize(self, context: PluginContext) -> bool:
        """Initialize the plugin"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> bool:
        """Cleanup plugin resources"""
        pass
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Get plugin status information"""
        pass
    
    def register_hook(self, hook_name: str, hook_type: HookType, 
                     target: str, handler: Callable, priority: int = 100):
        """Register a plugin hook"""
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        
        self._hooks[hook_name].append({
            'type': hook_type,
            'target': target,
            'handler': handler,
            'priority': priority
        })
        
        # Sort by priority
        self._hooks[hook_name].sort(key=lambda x: x['priority'])
    
    def register_ui_component(self, component_name: str, component_config: Dict[str, Any]):
        """Register a UI component"""
        self._ui_components[component_name] = component_config
    
    def register_api_endpoint(self, endpoint_name: str, endpoint_config: Dict[str, Any]):
        """Register an API endpoint"""
        self._api_endpoints[endpoint_name] = endpoint_config
    
    async def execute_hook(self, hook_context: HookContext) -> Any:
        """Execute plugin hooks"""
        hook_name = hook_context.hook_name
        if hook_name not in self._hooks:
            return hook_context.result
        
        for hook in self._hooks[hook_name]:
            if hook['type'] == hook_context.hook_type:
                try:
                    if asyncio.iscoroutinefunction(hook['handler']):
                        result = await hook['handler'](hook_context)
                    else:
                        result = hook['handler'](hook_context)
                    
                    if hook['type'] == HookType.REPLACE:
                        return result
                    elif hook['type'] == HookType.FILTER:
                        hook_context.result = result
                
                except Exception as e:
                    # Log error but continue with other hooks
                    await self._log_hook_error(hook_name, hook, e)
        
        return hook_context.result
    
    async def _log_hook_error(self, hook_name: str, hook: Dict[str, Any], error: Exception):
        """Log hook execution error"""
        # Implementation would log to platform logging system
        pass
    
    @property
    def hooks(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get registered hooks"""
        return self._hooks
    
    @property
    def ui_components(self) -> Dict[str, Any]:
        """Get registered UI components"""
        return self._ui_components
    
    @property
    def api_endpoints(self) -> Dict[str, Any]:
        """Get registered API endpoints"""
        return self._api_endpoints


class PluginSecurityContext:
    """Security context for plugin execution"""
    
    def __init__(self, plugin_id: str, permissions: List[PluginPermission]):
        self.plugin_id = plugin_id
        self.permissions = permissions
        self._resource_usage = {
            'memory': 0,
            'cpu_time': 0,
            'network_requests': 0,
            'file_operations': 0
        }
    
    def has_permission(self, permission: PluginPermission) -> bool:
        """Check if plugin has specific permission"""
        return permission in self.permissions
    
    def check_resource_limit(self, resource: str, usage: float) -> bool:
        """Check if resource usage is within limits"""
        # Implementation would check against configured limits
        return True
    
    def record_resource_usage(self, resource: str, amount: float):
        """Record resource usage"""
        self._resource_usage[resource] += amount
    
    @property
    def resource_usage(self) -> Dict[str, float]:
        """Get current resource usage"""
        return self._resource_usage.copy()


class PluginEventHandler(ABC):
    """Interface for handling plugin system events"""
    
    @abstractmethod
    async def on_plugin_loaded(self, plugin_id: str, manifest: PluginManifest):
        """Handle plugin loaded event"""
        pass
    
    @abstractmethod
    async def on_plugin_unloaded(self, plugin_id: str):
        """Handle plugin unloaded event"""
        pass
    
    @abstractmethod
    async def on_plugin_error(self, plugin_id: str, error: Exception):
        """Handle plugin error event"""
        pass
    
    @abstractmethod
    async def on_hook_executed(self, plugin_id: str, hook_name: str, 
                              execution_time: float, success: bool):
        """Handle hook execution event"""
        pass


class PluginValidator:
    """Validates plugin manifests and code"""
    
    @staticmethod
    def validate_manifest(manifest: PluginManifest) -> List[str]:
        """Validate plugin manifest, return list of errors"""
        errors = []
        
        # Basic validation
        if not manifest.id or not manifest.id.strip():
            errors.append("Plugin ID is required")
        
        if not manifest.name or not manifest.name.strip():
            errors.append("Plugin name is required")
        
        if not manifest.version or not manifest.version.strip():
            errors.append("Plugin version is required")
        
        if not manifest.entry_point or not manifest.entry_point.strip():
            errors.append("Plugin entry point is required")
        
        # Version format validation (basic semver check)
        try:
            version_parts = manifest.version.split('.')
            if len(version_parts) != 3:
                errors.append("Version must be in semver format (x.y.z)")
            else:
                for part in version_parts:
                    int(part)  # Will raise ValueError if not numeric
        except ValueError:
            errors.append("Version must contain only numeric components")
        
        # Permission validation
        for permission in manifest.permissions:
            if permission not in PluginPermission:
                errors.append(f"Invalid permission: {permission}")
        
        return errors
    
    @staticmethod
    def validate_security(manifest: PluginManifest, plugin_code: str) -> List[str]:
        """Validate plugin security, return list of security issues"""
        issues = []
        
        # Check for dangerous imports or operations
        dangerous_patterns = [
            'import os',
            'import subprocess',
            'import sys',
            'eval(',
            'exec(',
            '__import__',
            'open(',
        ]
        
        for pattern in dangerous_patterns:
            if pattern in plugin_code:
                issues.append(f"Potentially dangerous operation detected: {pattern}")
        
        # Check permissions vs code usage
        if 'open(' in plugin_code and PluginPermission.FILE_SYSTEM_READ not in manifest.permissions:
            issues.append("File operations detected but file system permission not requested")
        
        return issues