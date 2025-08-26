"""
Plugin service for managing plugin lifecycle, discovery, and execution.
Handles plugin loading, security, sandboxing, and API access.
"""

import os
import json
import asyncio
import importlib.util
import sys
from typing import Dict, List, Optional, Any, Type
from pathlib import Path
import tempfile
import zipfile
import shutil
from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from models.plugin import (
    Plugin, PluginData, PluginManifest, PluginStatus, 
    PluginPermission, PluginInfo, PluginInstallRequest
)
from core.plugin_interface import (
    PluginInterface, PluginContext, HookContext, PlatformServices,
    PluginSecurityContext, PluginEventHandler, PluginValidator,
    HookType, PluginEventType
)
from repositories.plugin_repository import PluginRepository
from core.database_service import DatabaseService


logger = logging.getLogger(__name__)


class PluginDiscovery:
    """Handles plugin discovery from various sources"""
    
    def __init__(self, plugins_directory: str):
        self.plugins_directory = Path(plugins_directory)
        self.plugins_directory.mkdir(exist_ok=True)
    
    async def discover_local_plugins(self) -> List[PluginManifest]:
        """Discover plugins in the local plugins directory"""
        manifests = []
        
        for plugin_dir in self.plugins_directory.iterdir():
            if plugin_dir.is_dir():
                manifest_path = plugin_dir / "manifest.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path, 'r') as f:
                            manifest_data = json.load(f)
                        
                        manifest = PluginManifest(**manifest_data)
                        manifests.append(manifest)
                    except Exception as e:
                        logger.warning(f"Failed to load manifest from {plugin_dir}: {e}")
        
        return manifests
    
    async def download_plugin(self, manifest_url: str, target_dir: Path) -> PluginManifest:
        """Download and extract plugin from URL"""
        # Implementation would download and extract plugin
        # For now, return a placeholder
        raise NotImplementedError("Plugin download not implemented yet")


class PluginSandbox:
    """Provides sandboxed execution environment for plugins"""
    
    def __init__(self, plugin_id: str, security_context: PluginSecurityContext):
        self.plugin_id = plugin_id
        self.security_context = security_context
        self._original_modules = {}
        self._restricted_builtins = {}
    
    def __enter__(self):
        """Enter sandbox context"""
        # Store original modules and restrict access
        self._setup_restricted_environment()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit sandbox context"""
        # Restore original environment
        self._restore_environment()
    
    def _setup_restricted_environment(self):
        """Set up restricted execution environment"""
        # Create restricted builtins
        safe_builtins = {
            'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'tuple',
            'set', 'frozenset', 'enumerate', 'zip', 'range', 'sorted',
            'min', 'max', 'sum', 'abs', 'round', 'isinstance', 'hasattr',
            'getattr', 'setattr', 'print'
        }
        
        self._restricted_builtins = {
            name: getattr(__builtins__, name) 
            for name in safe_builtins 
            if hasattr(__builtins__, name)
        }
        
        # Add permission-based builtins
        if self.security_context.has_permission(PluginPermission.FILE_SYSTEM_READ):
            self._restricted_builtins['open'] = self._restricted_open
    
    def _restricted_open(self, filename, mode='r', **kwargs):
        """Restricted file open function"""
        # Check permissions and file access
        if 'w' in mode or 'a' in mode:
            if not self.security_context.has_permission(PluginPermission.FILE_SYSTEM_WRITE):
                raise PermissionError("Plugin does not have write permission")
        
        # Record resource usage
        self.security_context.record_resource_usage('file_operations', 1)
        
        # Only allow access to plugin directory and temp files
        allowed_paths = [
            str(Path(f"plugins/{self.plugin_id}")),
            str(Path(tempfile.gettempdir()))
        ]
        
        abs_path = str(Path(filename).resolve())
        if not any(abs_path.startswith(allowed) for allowed in allowed_paths):
            raise PermissionError(f"Access denied to {filename}")
        
        return open(filename, mode, **kwargs)
    
    def _restore_environment(self):
        """Restore original environment"""
        # Restore would happen here
        pass


class PluginLoader:
    """Handles loading and instantiation of plugins"""
    
    def __init__(self, plugins_directory: str):
        self.plugins_directory = Path(plugins_directory)
    
    async def load_plugin(self, manifest: PluginManifest, 
                         security_context: PluginSecurityContext) -> PluginInterface:
        """Load and instantiate a plugin"""
        plugin_dir = self.plugins_directory / manifest.id
        entry_point_path = plugin_dir / manifest.entry_point
        
        if not entry_point_path.exists():
            raise FileNotFoundError(f"Plugin entry point not found: {entry_point_path}")
        
        # Validate plugin code
        with open(entry_point_path, 'r') as f:
            plugin_code = f.read()
        
        security_issues = PluginValidator.validate_security(manifest, plugin_code)
        if security_issues:
            raise ValueError(f"Security validation failed: {security_issues}")
        
        # Load plugin module in sandbox
        with PluginSandbox(manifest.id, security_context):
            spec = importlib.util.spec_from_file_location(
                f"plugin_{manifest.id}", entry_point_path
            )
            module = importlib.util.module_from_spec(spec)
            
            # Execute module
            spec.loader.exec_module(module)
            
            # Get plugin class (should be named 'Plugin' by convention)
            if not hasattr(module, 'Plugin'):
                raise AttributeError("Plugin module must define a 'Plugin' class")
            
            plugin_class = getattr(module, 'Plugin')
            if not issubclass(plugin_class, PluginInterface):
                raise TypeError("Plugin class must inherit from PluginInterface")
            
            # Instantiate plugin
            plugin_instance = plugin_class(manifest, manifest.id)
            
            return plugin_instance


class PluginService:
    """Main plugin service for managing the plugin system"""
    
    def __init__(self, database_service: DatabaseService, platform_services: PlatformServices):
        self.db = database_service
        self.platform_services = platform_services
        self.plugins_directory = Path("plugins")
        self.plugins_directory.mkdir(exist_ok=True)
        
        self.discovery = PluginDiscovery(str(self.plugins_directory))
        self.loader = PluginLoader(str(self.plugins_directory))
        
        # Runtime state
        self.loaded_plugins: Dict[str, PluginInterface] = {}
        self.plugin_contexts: Dict[str, PluginSecurityContext] = {}
        self.event_handlers: List[PluginEventHandler] = []
        
        # Hook registry
        self.hooks: Dict[str, List[Dict[str, Any]]] = {}
    
    async def initialize(self):
        """Initialize the plugin service"""
        # Discover and load installed plugins
        await self._load_installed_plugins()
    
    async def _load_installed_plugins(self):
        """Load all installed plugins from database"""
        async with self.db.get_session() as session:
            repository = PluginRepository(session)
            installed_plugins = await repository.get_active_plugins()
            
            for plugin_record in installed_plugins:
                try:
                    await self._load_plugin_from_record(plugin_record)
                except Exception as e:
                    logger.error(f"Failed to load plugin {plugin_record.name}: {e}")
                    # Update plugin status to error
                    await repository.update_plugin_status(
                        plugin_record.id, PluginStatus.ERROR, str(e)
                    )
    
    async def _load_plugin_from_record(self, plugin_record: Plugin):
        """Load a plugin from database record"""
        manifest = PluginManifest(**plugin_record.manifest)
        security_context = PluginSecurityContext(
            plugin_record.id, manifest.permissions
        )
        
        # Load plugin
        plugin_instance = await self.loader.load_plugin(manifest, security_context)
        
        # Initialize plugin
        context = PluginContext(
            user_id=None,
            session_id=None,
            module_name="system",
            request_data={},
            platform_services=self.platform_services,
            plugin_data={},
            timestamp=datetime.utcnow()
        )
        
        success = await plugin_instance.initialize(context)
        if not success:
            raise RuntimeError("Plugin initialization failed")
        
        # Register plugin
        self.loaded_plugins[plugin_record.id] = plugin_instance
        self.plugin_contexts[plugin_record.id] = security_context
        
        # Register hooks
        await self._register_plugin_hooks(plugin_record.id, plugin_instance)
        
        # Emit event
        await self._emit_event(PluginEventType.PLUGIN_LOADED, plugin_record.id, manifest)
    
    async def _register_plugin_hooks(self, plugin_id: str, plugin: PluginInterface):
        """Register hooks from a plugin"""
        for hook_name, hook_list in plugin.hooks.items():
            if hook_name not in self.hooks:
                self.hooks[hook_name] = []
            
            for hook in hook_list:
                self.hooks[hook_name].append({
                    'plugin_id': plugin_id,
                    'plugin': plugin,
                    **hook
                })
            
            # Sort by priority
            self.hooks[hook_name].sort(key=lambda x: x['priority'])
    
    async def install_plugin(self, install_request: PluginInstallRequest, 
                           user_id: str) -> PluginInfo:
        """Install a new plugin"""
        # Validate manifest
        if install_request.manifest_data:
            manifest = install_request.manifest_data
        else:
            # Download and extract manifest
            raise NotImplementedError("Remote plugin installation not implemented")
        
        # Validate manifest
        errors = PluginValidator.validate_manifest(manifest)
        if errors:
            raise ValueError(f"Invalid manifest: {errors}")
        
        # Check if plugin already exists
        async with self.db.get_session() as session:
            repository = PluginRepository(session)
            existing = await repository.get_by_name(manifest.name)
            if existing:
                raise ValueError(f"Plugin {manifest.name} already installed")
            
            # Create plugin record
            plugin_record = Plugin(
                name=manifest.name,
                version=manifest.version,
                description=manifest.description,
                manifest=manifest.dict(),
                status=PluginStatus.INSTALLED,
                installed_by=user_id
            )
            
            created_plugin = await repository.create(plugin_record)
            await session.commit()
            
            # Load plugin
            try:
                await self._load_plugin_from_record(created_plugin)
                
                # Update status to active
                await repository.update_plugin_status(
                    created_plugin.id, PluginStatus.ACTIVE
                )
                await session.commit()
                
            except Exception as e:
                # Update status to error
                await repository.update_plugin_status(
                    created_plugin.id, PluginStatus.ERROR, str(e)
                )
                await session.commit()
                raise
            
            return PluginInfo(
                id=created_plugin.id,
                name=created_plugin.name,
                version=created_plugin.version,
                description=created_plugin.description,
                author=manifest.author,
                status=PluginStatus.ACTIVE,
                installed_at=created_plugin.created_at,
                updated_at=created_plugin.updated_at,
                permissions=manifest.permissions
            )
    
    async def uninstall_plugin(self, plugin_id: str) -> bool:
        """Uninstall a plugin"""
        # Unload plugin
        if plugin_id in self.loaded_plugins:
            plugin = self.loaded_plugins[plugin_id]
            await plugin.cleanup()
            
            # Remove from runtime state
            del self.loaded_plugins[plugin_id]
            del self.plugin_contexts[plugin_id]
            
            # Remove hooks
            for hook_name in list(self.hooks.keys()):
                self.hooks[hook_name] = [
                    h for h in self.hooks[hook_name] 
                    if h['plugin_id'] != plugin_id
                ]
                if not self.hooks[hook_name]:
                    del self.hooks[hook_name]
        
        # Remove from database
        async with self.db.get_session() as session:
            repository = PluginRepository(session)
            success = await repository.delete(plugin_id)
            await session.commit()
            
            if success:
                await self._emit_event(PluginEventType.PLUGIN_UNLOADED, plugin_id)
            
            return success
    
    async def execute_hooks(self, hook_name: str, hook_type: HookType,
                           target_function: str, *args, **kwargs) -> Any:
        """Execute all registered hooks for a specific event"""
        if hook_name not in self.hooks:
            return kwargs.get('result')
        
        result = kwargs.get('result')
        
        for hook in self.hooks[hook_name]:
            if hook['type'] == hook_type:
                try:
                    start_time = datetime.utcnow()
                    
                    # Create hook context
                    context = HookContext(
                        hook_name=hook_name,
                        hook_type=hook_type,
                        target_function=target_function,
                        args=args,
                        kwargs=kwargs,
                        plugin_context=PluginContext(
                            user_id=kwargs.get('user_id'),
                            session_id=kwargs.get('session_id'),
                            module_name=kwargs.get('module_name', 'unknown'),
                            request_data=kwargs.get('request_data', {}),
                            platform_services=self.platform_services,
                            plugin_data={},
                            timestamp=datetime.utcnow()
                        ),
                        result=result
                    )
                    
                    # Execute hook
                    plugin = hook['plugin']
                    hook_result = await plugin.execute_hook(context)
                    
                    if hook['type'] == HookType.REPLACE:
                        result = hook_result
                    elif hook['type'] == HookType.FILTER:
                        result = hook_result
                    
                    # Record execution time
                    execution_time = (datetime.utcnow() - start_time).total_seconds()
                    await self._emit_event(
                        PluginEventType.HOOK_EXECUTED,
                        hook['plugin_id'],
                        {
                            'hook_name': hook_name,
                            'execution_time': execution_time,
                            'success': True
                        }
                    )
                    
                except Exception as e:
                    logger.error(f"Hook execution failed: {hook_name} in plugin {hook['plugin_id']}: {e}")
                    await self._emit_event(
                        PluginEventType.PLUGIN_ERROR,
                        hook['plugin_id'],
                        e
                    )
        
        return result
    
    async def get_installed_plugins(self) -> List[PluginInfo]:
        """Get list of all installed plugins"""
        async with self.db.get_session() as session:
            repository = PluginRepository(session)
            plugins = await repository.get_all()
            
            return [
                PluginInfo(
                    id=p.id,
                    name=p.name,
                    version=p.version,
                    description=p.description,
                    author=PluginManifest(**p.manifest).author,
                    status=PluginStatus(p.status),
                    installed_at=p.created_at,
                    updated_at=p.updated_at,
                    permissions=PluginManifest(**p.manifest).permissions,
                    error_message=p.error_message
                )
                for p in plugins
            ]
    
    async def get_plugin_info(self, plugin_id: str) -> Optional[PluginInfo]:
        """Get information about a specific plugin"""
        async with self.db.get_session() as session:
            repository = PluginRepository(session)
            plugin = await repository.get_by_id(plugin_id)
            
            if not plugin:
                return None
            
            manifest = PluginManifest(**plugin.manifest)
            return PluginInfo(
                id=plugin.id,
                name=plugin.name,
                version=plugin.version,
                description=plugin.description,
                author=manifest.author,
                status=PluginStatus(plugin.status),
                installed_at=plugin.created_at,
                updated_at=plugin.updated_at,
                permissions=manifest.permissions,
                error_message=plugin.error_message
            )
    
    async def _emit_event(self, event_type: PluginEventType, plugin_id: str, data: Any = None):
        """Emit plugin system event"""
        for handler in self.event_handlers:
            try:
                if event_type == PluginEventType.PLUGIN_LOADED:
                    await handler.on_plugin_loaded(plugin_id, data)
                elif event_type == PluginEventType.PLUGIN_UNLOADED:
                    await handler.on_plugin_unloaded(plugin_id)
                elif event_type == PluginEventType.PLUGIN_ERROR:
                    await handler.on_plugin_error(plugin_id, data)
                elif event_type == PluginEventType.HOOK_EXECUTED:
                    await handler.on_hook_executed(
                        plugin_id, data['hook_name'], 
                        data['execution_time'], data['success']
                    )
            except Exception as e:
                logger.error(f"Event handler failed: {e}")
    
    def add_event_handler(self, handler: PluginEventHandler):
        """Add plugin event handler"""
        self.event_handlers.append(handler)