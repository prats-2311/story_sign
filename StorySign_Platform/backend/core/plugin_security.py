"""
Plugin security and sandboxing system.
Provides secure execution environment and resource management for plugins.
"""

import os
import sys
import time
import threading
import resource
import signal
from typing import Dict, Any, List, Optional, Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import tempfile
import shutil
from pathlib import Path

from models.plugin import PluginPermission


logger = logging.getLogger(__name__)


class SecurityLevel(str, Enum):
    """Security levels for plugin execution"""
    MINIMAL = "minimal"      # Basic restrictions
    STANDARD = "standard"    # Standard security
    STRICT = "strict"        # Maximum security
    ISOLATED = "isolated"    # Complete isolation


@dataclass
class ResourceLimits:
    """Resource limits for plugin execution"""
    max_memory_mb: int = 100
    max_cpu_time_seconds: float = 5.0
    max_file_operations: int = 100
    max_network_requests: int = 50
    max_execution_time_seconds: float = 10.0
    max_threads: int = 2
    max_file_size_mb: int = 10
    allowed_file_extensions: List[str] = field(default_factory=lambda: ['.txt', '.json', '.csv'])


@dataclass
class SecurityPolicy:
    """Security policy for plugin execution"""
    security_level: SecurityLevel = SecurityLevel.STANDARD
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    allowed_modules: List[str] = field(default_factory=lambda: [
        'json', 'datetime', 'math', 'random', 'string', 'collections',
        'itertools', 'functools', 'operator', 'typing', 're'
    ])
    blocked_modules: List[str] = field(default_factory=lambda: [
        'os', 'sys', 'subprocess', 'socket', 'urllib', 'requests',
        'importlib', '__builtin__', 'builtins'
    ])
    allowed_builtins: List[str] = field(default_factory=lambda: [
        'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'tuple',
        'set', 'frozenset', 'enumerate', 'zip', 'range', 'sorted',
        'min', 'max', 'sum', 'abs', 'round', 'isinstance', 'hasattr',
        'getattr', 'setattr', 'print', 'type', 'id', 'hash'
    ])
    blocked_builtins: List[str] = field(default_factory=lambda: [
        'eval', 'exec', 'compile', '__import__', 'open', 'input',
        'raw_input', 'file', 'reload', 'vars', 'locals', 'globals'
    ])


class ResourceMonitor:
    """Monitors resource usage during plugin execution"""
    
    def __init__(self, limits: ResourceLimits):
        self.limits = limits
        self.start_time = None
        self.memory_usage = 0
        self.cpu_time = 0
        self.file_operations = 0
        self.network_requests = 0
        self.active_threads = 0
        self._monitoring = False
        self._monitor_thread = None
    
    def start_monitoring(self):
        """Start resource monitoring"""
        self.start_time = time.time()
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop resource monitoring"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self._monitoring:
            try:
                # Check execution time
                if self.start_time:
                    elapsed = time.time() - self.start_time
                    if elapsed > self.limits.max_execution_time_seconds:
                        raise ResourceExceededError(
                            f"Execution time limit exceeded: {elapsed:.2f}s > {self.limits.max_execution_time_seconds}s"
                        )
                
                # Check memory usage
                try:
                    import psutil
                    process = psutil.Process()
                    memory_mb = process.memory_info().rss / 1024 / 1024
                    self.memory_usage = memory_mb
                    
                    if memory_mb > self.limits.max_memory_mb:
                        raise ResourceExceededError(
                            f"Memory limit exceeded: {memory_mb:.2f}MB > {self.limits.max_memory_mb}MB"
                        )
                except ImportError:
                    # psutil not available, use basic resource module
                    memory_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                    memory_mb = memory_kb / 1024  # On Linux, ru_maxrss is in KB
                    self.memory_usage = memory_mb
                
                # Check CPU time
                cpu_time = resource.getrusage(resource.RUSAGE_SELF).ru_utime
                self.cpu_time = cpu_time
                
                if cpu_time > self.limits.max_cpu_time_seconds:
                    raise ResourceExceededError(
                        f"CPU time limit exceeded: {cpu_time:.2f}s > {self.limits.max_cpu_time_seconds}s"
                    )
                
                time.sleep(0.1)  # Check every 100ms
                
            except ResourceExceededError:
                # Kill the process if limits exceeded
                os.kill(os.getpid(), signal.SIGTERM)
                break
            except Exception as e:
                logger.warning(f"Resource monitoring error: {e}")
    
    def record_file_operation(self):
        """Record a file operation"""
        self.file_operations += 1
        if self.file_operations > self.limits.max_file_operations:
            raise ResourceExceededError(
                f"File operations limit exceeded: {self.file_operations} > {self.limits.max_file_operations}"
            )
    
    def record_network_request(self):
        """Record a network request"""
        self.network_requests += 1
        if self.network_requests > self.limits.max_network_requests:
            raise ResourceExceededError(
                f"Network requests limit exceeded: {self.network_requests} > {self.limits.max_network_requests}"
            )
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current resource usage statistics"""
        elapsed_time = time.time() - self.start_time if self.start_time else 0
        return {
            'elapsed_time': elapsed_time,
            'memory_usage_mb': self.memory_usage,
            'cpu_time': self.cpu_time,
            'file_operations': self.file_operations,
            'network_requests': self.network_requests,
            'active_threads': self.active_threads
        }


class ResourceExceededError(Exception):
    """Raised when resource limits are exceeded"""
    pass


class SecurityViolationError(Exception):
    """Raised when security policy is violated"""
    pass


class PluginSandboxManager:
    """Manages sandboxed execution of plugins"""
    
    def __init__(self, plugin_id: str, permissions: List[PluginPermission], 
                 security_policy: Optional[SecurityPolicy] = None):
        self.plugin_id = plugin_id
        self.permissions = permissions
        self.policy = security_policy or SecurityPolicy()
        self.resource_monitor = ResourceMonitor(self.policy.resource_limits)
        self.temp_dir = None
        self.original_modules = {}
        self.original_builtins = {}
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix=f"plugin-{plugin_id}")
    
    @contextmanager
    def secure_execution_context(self):
        """Context manager for secure plugin execution"""
        try:
            self._setup_sandbox()
            self.resource_monitor.start_monitoring()
            yield self
        finally:
            self.resource_monitor.stop_monitoring()
            self._cleanup_sandbox()
    
    def _setup_sandbox(self):
        """Set up the sandbox environment"""
        # Create temporary directory for plugin files
        self.temp_dir = Path(tempfile.mkdtemp(prefix=f"plugin_{self.plugin_id}_"))
        
        # Restrict built-in functions
        self._restrict_builtins()
        
        # Restrict module imports
        self._restrict_imports()
        
        # Set up file system restrictions
        self._setup_filesystem_restrictions()
    
    def _restrict_builtins(self):
        """Restrict access to built-in functions"""
        import builtins
        
        # Store original builtins
        self.original_builtins = {
            name: getattr(builtins, name, None)
            for name in self.policy.blocked_builtins
            if hasattr(builtins, name)
        }
        
        # Remove dangerous builtins
        for name in self.policy.blocked_builtins:
            if hasattr(builtins, name):
                delattr(builtins, name)
        
        # Add restricted versions of some functions
        if PluginPermission.FILE_SYSTEM_READ in self.permissions:
            builtins.open = self._restricted_open
    
    def _restrict_imports(self):
        """Restrict module imports"""
        # Store original import function
        original_import = __builtins__['__import__']
        
        def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
            # Check if module is allowed
            if name in self.policy.blocked_modules:
                raise SecurityViolationError(f"Import of module '{name}' is not allowed")
            
            if self.policy.allowed_modules and name not in self.policy.allowed_modules:
                # Check if it's a submodule of an allowed module
                allowed = any(
                    name.startswith(allowed_mod + '.') 
                    for allowed_mod in self.policy.allowed_modules
                )
                if not allowed:
                    raise SecurityViolationError(f"Import of module '{name}' is not allowed")
            
            return original_import(name, globals, locals, fromlist, level)
        
        __builtins__['__import__'] = restricted_import
    
    def _setup_filesystem_restrictions(self):
        """Set up file system access restrictions"""
        # Plugin can only access its temporary directory
        self.allowed_paths = [str(self.temp_dir)]
        
        # Add additional paths based on permissions
        if PluginPermission.FILE_SYSTEM_READ in self.permissions:
            # Allow read access to plugin directory
            plugin_dir = Path(f"plugins/{self.plugin_id}")
            if plugin_dir.exists():
                self.allowed_paths.append(str(plugin_dir))
    
    def _restricted_open(self, filename, mode='r', **kwargs):
        """Restricted file open function"""
        self.resource_monitor.record_file_operation()
        
        # Check file permissions
        if 'w' in mode or 'a' in mode or '+' in mode:
            if PluginPermission.FILE_SYSTEM_WRITE not in self.permissions:
                raise SecurityViolationError("Plugin does not have write permission")
        
        # Check file path
        abs_path = str(Path(filename).resolve())
        allowed = any(abs_path.startswith(allowed_path) for allowed_path in self.allowed_paths)
        
        if not allowed:
            raise SecurityViolationError(f"Access denied to file: {filename}")
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext and file_ext not in self.policy.resource_limits.allowed_file_extensions:
            raise SecurityViolationError(f"File extension '{file_ext}' not allowed")
        
        # Check file size for write operations
        if 'w' in mode or 'a' in mode:
            try:
                if Path(filename).exists():
                    size_mb = Path(filename).stat().st_size / 1024 / 1024
                    if size_mb > self.policy.resource_limits.max_file_size_mb:
                        raise SecurityViolationError(
                            f"File size {size_mb:.2f}MB exceeds limit of {self.policy.resource_limits.max_file_size_mb}MB"
                        )
            except OSError:
                pass  # File doesn't exist yet
        
        return open(filename, mode, **kwargs)
    
    def _cleanup_sandbox(self):
        """Clean up sandbox environment"""
        # Restore original builtins
        import builtins
        for name, original_func in self.original_builtins.items():
            if original_func is not None:
                setattr(builtins, name, original_func)
            elif hasattr(builtins, name):
                delattr(builtins, name)
        
        # Clean up temporary directory
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory {self.temp_dir}: {e}")
        
        # Shutdown executor
        self.executor.shutdown(wait=False)
    
    async def execute_plugin_function(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a plugin function in the sandbox"""
        def wrapped_execution():
            with self.secure_execution_context():
                return func(*args, **kwargs)
        
        try:
            # Execute in thread pool with timeout
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(self.executor, wrapped_execution),
                timeout=self.policy.resource_limits.max_execution_time_seconds
            )
            return result
            
        except asyncio.TimeoutError:
            raise ResourceExceededError(
                f"Plugin execution timed out after {self.policy.resource_limits.max_execution_time_seconds}s"
            )
        except Exception as e:
            if isinstance(e, (ResourceExceededError, SecurityViolationError)):
                raise
            else:
                # Wrap other exceptions
                raise SecurityViolationError(f"Plugin execution failed: {str(e)}")
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage statistics"""
        return self.resource_monitor.get_usage_stats()


class PluginSecurityManager:
    """Manages security policies and validation for plugins"""
    
    def __init__(self):
        self.security_policies: Dict[str, SecurityPolicy] = {}
        self.default_policy = SecurityPolicy()
    
    def set_plugin_policy(self, plugin_id: str, policy: SecurityPolicy):
        """Set security policy for a specific plugin"""
        self.security_policies[plugin_id] = policy
    
    def get_plugin_policy(self, plugin_id: str) -> SecurityPolicy:
        """Get security policy for a plugin"""
        return self.security_policies.get(plugin_id, self.default_policy)
    
    def validate_plugin_permissions(self, plugin_id: str, 
                                   requested_permissions: List[PluginPermission]) -> List[str]:
        """Validate plugin permissions against security policy"""
        policy = self.get_plugin_policy(plugin_id)
        violations = []
        
        # Check for dangerous permission combinations
        if (PluginPermission.FILE_SYSTEM_WRITE in requested_permissions and 
            PluginPermission.NETWORK_ACCESS in requested_permissions):
            if policy.security_level in [SecurityLevel.STRICT, SecurityLevel.ISOLATED]:
                violations.append("Combination of file write and network access not allowed in strict mode")
        
        # Check individual permissions against policy
        dangerous_permissions = [
            PluginPermission.FILE_SYSTEM_WRITE,
            PluginPermission.NETWORK_ACCESS,
            PluginPermission.DATABASE_WRITE
        ]
        
        for perm in requested_permissions:
            if perm in dangerous_permissions and policy.security_level == SecurityLevel.ISOLATED:
                violations.append(f"Permission {perm} not allowed in isolated mode")
        
        return violations
    
    def create_sandbox_manager(self, plugin_id: str, 
                              permissions: List[PluginPermission]) -> PluginSandboxManager:
        """Create a sandbox manager for a plugin"""
        policy = self.get_plugin_policy(plugin_id)
        return PluginSandboxManager(plugin_id, permissions, policy)