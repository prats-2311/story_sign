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
from datetime import datetime

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
    """Enhanced sandbox manager with comprehensive isolation and error handling"""
    
    def __init__(self, plugin_id: str, permissions: List[PluginPermission], 
                 security_policy: Optional[SecurityPolicy] = None):
        self.plugin_id = plugin_id
        self.permissions = permissions
        self.policy = security_policy or SecurityPolicy()
        self.resource_monitor = ResourceMonitor(self.policy.resource_limits)
        self.isolation_manager = PluginIsolationManager(plugin_id, self.policy.resource_limits)
        self.temp_dir = None
        self.original_modules = {}
        self.original_builtins = {}
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix=f"plugin-{plugin_id}")
        self.execution_errors = []
        self.security_violations = []
    
    @contextmanager
    def secure_execution_context(self):
        """Enhanced context manager for secure plugin execution"""
        try:
            self._setup_sandbox()
            self.resource_monitor.start_monitoring()
            self.isolation_manager.start_monitoring()
            yield self
        except Exception as e:
            self._handle_sandbox_error(e)
            raise
        finally:
            self.resource_monitor.stop_monitoring()
            self.isolation_manager.stop_monitoring()
            self._cleanup_sandbox()
    
    def _setup_sandbox(self):
        """Enhanced sandbox setup with comprehensive restrictions"""
        # Create temporary directory for plugin files
        self.temp_dir = Path(tempfile.mkdtemp(prefix=f"plugin_{self.plugin_id}_"))
        
        # Set directory permissions (read-only for plugin directory)
        try:
            os.chmod(self.temp_dir, 0o755)
        except OSError as e:
            logger.warning(f"Failed to set directory permissions: {e}")
        
        # Restrict built-in functions
        self._restrict_builtins()
        
        # Restrict module imports
        self._restrict_imports()
        
        # Set up file system restrictions
        self._setup_filesystem_restrictions()
        
        # Set up network restrictions
        self._setup_network_restrictions()
        
        # Set up signal handlers for resource limits
        self._setup_signal_handlers()
    
    def _restrict_builtins(self):
        """Enhanced builtin function restrictions"""
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
        
        # Add restricted versions of allowed functions
        if PluginPermission.FILE_SYSTEM_READ in self.permissions:
            builtins.open = self._restricted_open
        
        # Add monitoring wrappers for other functions
        original_print = builtins.print
        def monitored_print(*args, **kwargs):
            # Limit print output
            if len(str(args)) > 1000:  # Limit output size
                raise SecurityViolationError("Print output too large")
            return original_print(*args, **kwargs)
        
        builtins.print = monitored_print
    
    def _restrict_imports(self):
        """Enhanced import restrictions with monitoring"""
        # Store original import function
        original_import = __builtins__['__import__']
        
        def restricted_import(name, globals=None, locals=None, fromlist=(), level=0):
            # Record import attempt
            self.isolation_manager.record_operation('imports', 1)
            
            # Check if module is blocked
            if name in self.policy.blocked_modules:
                violation = f"Attempted to import blocked module: {name}"
                self.security_violations.append(violation)
                raise SecurityViolationError(violation)
            
            # Check if module is in allowed list (if specified)
            if self.policy.allowed_modules and name not in self.policy.allowed_modules:
                # Check if it's a submodule of an allowed module
                allowed = any(
                    name.startswith(allowed_mod + '.') 
                    for allowed_mod in self.policy.allowed_modules
                )
                if not allowed:
                    violation = f"Attempted to import non-allowed module: {name}"
                    self.security_violations.append(violation)
                    raise SecurityViolationError(violation)
            
            # Check for suspicious module patterns
            suspicious_patterns = ['ctypes', 'subprocess', 'socket', 'urllib', 'requests']
            for pattern in suspicious_patterns:
                if pattern in name.lower():
                    if not self._check_module_permission(pattern):
                        violation = f"Attempted to import suspicious module without permission: {name}"
                        self.security_violations.append(violation)
                        raise SecurityViolationError(violation)
            
            return original_import(name, globals, locals, fromlist, level)
        
        __builtins__['__import__'] = restricted_import
    
    def _check_module_permission(self, module_pattern: str) -> bool:
        """Check if plugin has permission for specific module patterns"""
        permission_map = {
            'socket': PluginPermission.NETWORK_ACCESS,
            'urllib': PluginPermission.NETWORK_ACCESS,
            'requests': PluginPermission.NETWORK_ACCESS,
            'subprocess': None,  # Never allowed
            'ctypes': None,  # Never allowed
        }
        
        required_permission = permission_map.get(module_pattern)
        if required_permission is None:
            return False  # Module never allowed
        
        return required_permission in self.permissions
    
    def _setup_filesystem_restrictions(self):
        """Enhanced file system access restrictions"""
        # Plugin can only access its temporary directory
        self.allowed_paths = [str(self.temp_dir)]
        
        # Add additional paths based on permissions
        if PluginPermission.FILE_SYSTEM_READ in self.permissions:
            # Allow read access to plugin directory
            plugin_dir = Path(f"plugins/{self.plugin_id}")
            if plugin_dir.exists():
                self.allowed_paths.append(str(plugin_dir))
            
            # Allow read access to common data directories
            data_dirs = ['/tmp', '/var/tmp']  # Only temporary directories
            for data_dir in data_dirs:
                if Path(data_dir).exists():
                    self.allowed_paths.append(data_dir)
    
    def _setup_network_restrictions(self):
        """Set up network access restrictions"""
        if PluginPermission.NETWORK_ACCESS not in self.permissions:
            # Block network access by monkey-patching socket
            import socket
            
            original_socket = socket.socket
            def blocked_socket(*args, **kwargs):
                violation = "Attempted network access without permission"
                self.security_violations.append(violation)
                raise SecurityViolationError(violation)
            
            socket.socket = blocked_socket
    
    def _setup_signal_handlers(self):
        """Set up signal handlers for resource limit enforcement"""
        def timeout_handler(signum, frame):
            raise ResourceExceededError(f"Plugin {self.plugin_id} execution timed out")
        
        def memory_handler(signum, frame):
            raise ResourceExceededError(f"Plugin {self.plugin_id} memory limit exceeded")
        
        # Set up timeout signal
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(self.policy.resource_limits.max_execution_time_seconds))
    
    def _restricted_open(self, filename, mode='r', **kwargs):
        """Enhanced restricted file open function"""
        self.resource_monitor.record_file_operation()
        self.isolation_manager.record_operation('file_operations', 1)
        
        # Check file permissions
        if 'w' in mode or 'a' in mode or '+' in mode:
            if PluginPermission.FILE_SYSTEM_WRITE not in self.permissions:
                violation = f"Attempted file write without permission: {filename}"
                self.security_violations.append(violation)
                raise SecurityViolationError(violation)
        
        # Resolve and validate file path
        try:
            abs_path = str(Path(filename).resolve())
        except (OSError, ValueError) as e:
            violation = f"Invalid file path: {filename} - {e}"
            self.security_violations.append(violation)
            raise SecurityViolationError(violation)
        
        # Check if path is allowed
        allowed = any(abs_path.startswith(allowed_path) for allowed_path in self.allowed_paths)
        if not allowed:
            violation = f"Access denied to file outside allowed paths: {filename}"
            self.security_violations.append(violation)
            raise SecurityViolationError(violation)
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext and file_ext not in self.policy.resource_limits.allowed_file_extensions:
            violation = f"File extension not allowed: {file_ext}"
            self.security_violations.append(violation)
            raise SecurityViolationError(violation)
        
        # Check file size for existing files
        try:
            if Path(filename).exists():
                size_mb = Path(filename).stat().st_size / 1024 / 1024
                if size_mb > self.policy.resource_limits.max_file_size_mb:
                    violation = f"File size exceeds limit: {size_mb:.2f}MB > {self.policy.resource_limits.max_file_size_mb}MB"
                    self.security_violations.append(violation)
                    raise SecurityViolationError(violation)
        except OSError as e:
            logger.warning(f"Failed to check file size for {filename}: {e}")
        
        # Check for suspicious file operations
        suspicious_paths = ['/etc/', '/proc/', '/sys/', '/dev/', '/root/', '/home/']
        for suspicious_path in suspicious_paths:
            if abs_path.startswith(suspicious_path):
                violation = f"Attempted access to sensitive system path: {abs_path}"
                self.security_violations.append(violation)
                raise SecurityViolationError(violation)
        
        try:
            return open(filename, mode, **kwargs)
        except Exception as e:
            self.execution_errors.append(f"File operation failed: {e}")
            raise
    
    def _handle_sandbox_error(self, error: Exception):
        """Handle sandbox execution errors"""
        error_info = {
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'plugin_id': self.plugin_id
        }
        
        self.execution_errors.append(error_info)
        
        # Log the error
        logger.error(f"Sandbox error in plugin {self.plugin_id}: {error}")
        
        # Record security violation if applicable
        if isinstance(error, SecurityViolationError):
            self.security_violations.append(str(error))
    
    def _cleanup_sandbox(self):
        """Enhanced sandbox cleanup"""
        try:
            # Cancel any pending alarms
            signal.alarm(0)
            
            # Restore original builtins
            import builtins
            for name, original_func in self.original_builtins.items():
                if original_func is not None:
                    setattr(builtins, name, original_func)
                elif hasattr(builtins, name):
                    delattr(builtins, name)
            
            # Restore original import
            if hasattr(self, '_original_import'):
                __builtins__['__import__'] = self._original_import
            
            # Clean up temporary directory
            if self.temp_dir and self.temp_dir.exists():
                try:
                    shutil.rmtree(self.temp_dir)
                except Exception as e:
                    logger.warning(f"Failed to clean up temp directory {self.temp_dir}: {e}")
            
            # Shutdown executor
            self.executor.shutdown(wait=False)
            
        except Exception as e:
            logger.error(f"Error during sandbox cleanup for plugin {self.plugin_id}: {e}")
    
    async def execute_plugin_function(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a plugin function with comprehensive error handling and isolation"""
        def wrapped_execution():
            try:
                with self.secure_execution_context():
                    # Check execution time before starting
                    self.isolation_manager.check_execution_time()
                    
                    # Execute the function
                    result = func(*args, **kwargs)
                    
                    # Check execution time after completion
                    self.isolation_manager.check_execution_time()
                    
                    return result
            except Exception as e:
                self._handle_sandbox_error(e)
                raise
        
        try:
            # Execute in thread pool with timeout
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(self.executor, wrapped_execution),
                timeout=self.policy.resource_limits.max_execution_time_seconds
            )
            return result
            
        except asyncio.TimeoutError:
            error = ResourceExceededError(
                f"Plugin {self.plugin_id} execution timed out after {self.policy.resource_limits.max_execution_time_seconds}s"
            )
            self._handle_sandbox_error(error)
            raise error
        except Exception as e:
            if isinstance(e, (ResourceExceededError, SecurityViolationError)):
                raise
            else:
                # Wrap other exceptions
                wrapped_error = SecurityViolationError(f"Plugin execution failed: {str(e)}")
                self._handle_sandbox_error(wrapped_error)
                raise wrapped_error
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get comprehensive resource usage and security statistics"""
        base_usage = self.resource_monitor.get_usage_stats()
        isolation_report = self.isolation_manager.get_usage_report()
        
        return {
            **base_usage,
            'isolation_report': isolation_report,
            'execution_errors': self.execution_errors.copy(),
            'security_violations': self.security_violations.copy(),
            'violation_count': len(self.security_violations),
            'error_count': len(self.execution_errors)
        }
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get security summary for the plugin execution"""
        return {
            'plugin_id': self.plugin_id,
            'security_level': self.policy.security_level,
            'permissions': [str(p) for p in self.permissions],
            'violations': self.security_violations.copy(),
            'errors': self.execution_errors.copy(),
            'resource_usage': self.isolation_manager.get_usage_report(),
            'sandbox_active': self.resource_monitor._monitoring
        }


class PluginValidator:
    """Enhanced plugin validation with security scanning"""
    
    @staticmethod
    def validate_plugin_code(plugin_code: str, manifest: 'PluginManifest') -> List[str]:
        """Comprehensive security validation of plugin code"""
        issues = []
        
        # Check for dangerous imports
        dangerous_imports = [
            'import os', 'from os import', 'import sys', 'from sys import',
            'import subprocess', 'from subprocess import', 'import socket',
            'from socket import', 'import urllib', 'from urllib import',
            'import requests', 'from requests import', 'import http',
            'from http import', 'import ftplib', 'from ftplib import',
            'import smtplib', 'from smtplib import', 'import telnetlib',
            'from telnetlib import', 'import paramiko', 'from paramiko import'
        ]
        
        for dangerous_import in dangerous_imports:
            if dangerous_import in plugin_code:
                issues.append(f"Dangerous import detected: {dangerous_import}")
        
        # Check for dangerous function calls
        dangerous_functions = [
            'eval(', 'exec(', 'compile(', '__import__(', 'globals()',
            'locals(', 'vars(', 'dir(', 'getattr(', 'setattr(',
            'delattr(', 'hasattr(', 'callable(', 'isinstance(',
            'open(', 'file(', 'input(', 'raw_input('
        ]
        
        for func in dangerous_functions:
            if func in plugin_code:
                # Check if plugin has appropriate permissions
                if func == 'open(' and PluginPermission.FILE_SYSTEM_READ not in manifest.permissions:
                    issues.append(f"File operations detected but file system permission not requested: {func}")
                elif func in ['eval(', 'exec(', 'compile(']:
                    issues.append(f"Code execution function not allowed: {func}")
                elif func == '__import__(':
                    issues.append(f"Dynamic import not allowed: {func}")
        
        # Check for network operations
        network_patterns = [
            'urllib.request', 'urllib.parse', 'urllib.error',
            'http.client', 'http.server', 'requests.get',
            'requests.post', 'socket.socket', 'socket.connect'
        ]
        
        for pattern in network_patterns:
            if pattern in plugin_code:
                if PluginPermission.NETWORK_ACCESS not in manifest.permissions:
                    issues.append(f"Network operation detected but network permission not requested: {pattern}")
        
        # Check for file system operations
        file_patterns = [
            'open(', 'file(', 'os.path', 'pathlib.Path',
            'shutil.', 'tempfile.', 'glob.glob'
        ]
        
        for pattern in file_patterns:
            if pattern in plugin_code:
                if (PluginPermission.FILE_SYSTEM_READ not in manifest.permissions and 
                    PluginPermission.FILE_SYSTEM_WRITE not in manifest.permissions):
                    issues.append(f"File system operation detected but file system permission not requested: {pattern}")
        
        # Check for database operations
        db_patterns = [
            'sqlalchemy', 'sqlite3', 'mysql', 'postgresql',
            'pymongo', 'redis', 'CREATE TABLE', 'DROP TABLE',
            'INSERT INTO', 'DELETE FROM', 'UPDATE SET'
        ]
        
        for pattern in db_patterns:
            if pattern.lower() in plugin_code.lower():
                if (PluginPermission.DATABASE_READ not in manifest.permissions and 
                    PluginPermission.DATABASE_WRITE not in manifest.permissions):
                    issues.append(f"Database operation detected but database permission not requested: {pattern}")
        
        # Check for threading and multiprocessing
        threading_patterns = [
            'threading.Thread', 'multiprocessing.Process',
            'concurrent.futures', 'asyncio.create_task'
        ]
        
        for pattern in threading_patterns:
            if pattern in plugin_code:
                issues.append(f"Threading/multiprocessing detected (may bypass resource limits): {pattern}")
        
        # Check for system calls
        system_patterns = [
            'os.system', 'os.popen', 'os.spawn', 'os.exec',
            'subprocess.call', 'subprocess.run', 'subprocess.Popen'
        ]
        
        for pattern in system_patterns:
            if pattern in plugin_code:
                issues.append(f"System call detected (not allowed): {pattern}")
        
        return issues
    
    @staticmethod
    def scan_for_malicious_patterns(plugin_code: str) -> List[str]:
        """Scan for potentially malicious code patterns"""
        issues = []
        
        # Check for obfuscation attempts
        obfuscation_patterns = [
            'base64.b64decode', 'codecs.decode', 'bytes.fromhex',
            'chr(', 'ord(', '\\x', '\\u', '\\N'
        ]
        
        for pattern in obfuscation_patterns:
            if pattern in plugin_code:
                issues.append(f"Potential code obfuscation detected: {pattern}")
        
        # Check for data exfiltration patterns
        exfiltration_patterns = [
            'urllib.request.urlopen', 'requests.post', 'smtplib.SMTP',
            'socket.sendto', 'ftplib.FTP'
        ]
        
        for pattern in exfiltration_patterns:
            if pattern in plugin_code:
                issues.append(f"Potential data exfiltration pattern: {pattern}")
        
        # Check for privilege escalation attempts
        privilege_patterns = [
            'os.setuid', 'os.setgid', 'os.seteuid', 'os.setegid',
            'ctypes.windll', 'ctypes.cdll'
        ]
        
        for pattern in privilege_patterns:
            if pattern in plugin_code:
                issues.append(f"Privilege escalation attempt detected: {pattern}")
        
        # Check for anti-debugging/analysis
        anti_debug_patterns = [
            'sys.settrace', 'sys.setprofile', 'pdb.set_trace',
            'debugger', 'ptrace'
        ]
        
        for pattern in anti_debug_patterns:
            if pattern in plugin_code:
                issues.append(f"Anti-debugging pattern detected: {pattern}")
        
        return issues


class PluginIsolationManager:
    """Manages plugin isolation and resource monitoring"""
    
    def __init__(self, plugin_id: str, resource_limits: ResourceLimits):
        self.plugin_id = plugin_id
        self.resource_limits = resource_limits
        self.start_time = None
        self.resource_usage = {
            'memory_mb': 0,
            'cpu_time': 0,
            'file_operations': 0,
            'network_requests': 0,
            'database_queries': 0
        }
        self._monitoring = False
        self._violations = []
    
    def start_monitoring(self):
        """Start resource monitoring"""
        self.start_time = time.time()
        self._monitoring = True
        
        # Set resource limits using resource module
        try:
            # Set memory limit (in bytes)
            memory_limit = self.resource_limits.max_memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
            
            # Set CPU time limit
            cpu_limit = int(self.resource_limits.max_cpu_time_seconds)
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))
            
        except (OSError, ValueError) as e:
            logger.warning(f"Failed to set resource limits for plugin {self.plugin_id}: {e}")
    
    def stop_monitoring(self):
        """Stop resource monitoring"""
        self._monitoring = False
    
    def check_execution_time(self):
        """Check if execution time limit is exceeded"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            if elapsed > self.resource_limits.max_execution_time_seconds:
                raise ResourceExceededError(
                    f"Plugin {self.plugin_id} execution time limit exceeded: "
                    f"{elapsed:.2f}s > {self.resource_limits.max_execution_time_seconds}s"
                )
    
    def record_operation(self, operation_type: str, count: int = 1):
        """Record an operation and check limits"""
        self.resource_usage[operation_type] += count
        
        # Check limits
        if operation_type == 'file_operations':
            if self.resource_usage[operation_type] > self.resource_limits.max_file_operations:
                raise ResourceExceededError(
                    f"Plugin {self.plugin_id} file operations limit exceeded: "
                    f"{self.resource_usage[operation_type]} > {self.resource_limits.max_file_operations}"
                )
        elif operation_type == 'network_requests':
            if self.resource_usage[operation_type] > self.resource_limits.max_network_requests:
                raise ResourceExceededError(
                    f"Plugin {self.plugin_id} network requests limit exceeded: "
                    f"{self.resource_usage[operation_type]} > {self.resource_limits.max_network_requests}"
                )
    
    def get_usage_report(self) -> Dict[str, Any]:
        """Get detailed usage report"""
        elapsed_time = time.time() - self.start_time if self.start_time else 0
        
        return {
            'plugin_id': self.plugin_id,
            'elapsed_time': elapsed_time,
            'resource_usage': self.resource_usage.copy(),
            'resource_limits': {
                'max_memory_mb': self.resource_limits.max_memory_mb,
                'max_cpu_time_seconds': self.resource_limits.max_cpu_time_seconds,
                'max_execution_time_seconds': self.resource_limits.max_execution_time_seconds,
                'max_file_operations': self.resource_limits.max_file_operations,
                'max_network_requests': self.resource_limits.max_network_requests
            },
            'violations': self._violations.copy()
        }


class PluginSecurityManager:
    """Enhanced security manager with comprehensive validation and isolation"""
    
    def __init__(self):
        self.security_policies: Dict[str, SecurityPolicy] = {}
        self.default_policy = SecurityPolicy()
        self.isolation_managers: Dict[str, PluginIsolationManager] = {}
        self.security_violations: Dict[str, List[Dict[str, Any]]] = {}
    
    def set_plugin_policy(self, plugin_id: str, policy: SecurityPolicy):
        """Set security policy for a specific plugin"""
        self.security_policies[plugin_id] = policy
    
    def get_plugin_policy(self, plugin_id: str) -> SecurityPolicy:
        """Get security policy for a plugin"""
        return self.security_policies.get(plugin_id, self.default_policy)
    
    def validate_plugin_manifest(self, manifest: 'PluginManifest') -> List[str]:
        """Validate plugin manifest for security issues"""
        from core.plugin_interface import PluginValidator as InterfaceValidator
        
        # Basic manifest validation
        errors = InterfaceValidator.validate_manifest(manifest)
        
        # Additional security validation
        security_issues = []
        
        # Check for suspicious plugin names or descriptions
        suspicious_keywords = [
            'hack', 'crack', 'exploit', 'backdoor', 'trojan',
            'virus', 'malware', 'keylog', 'steal', 'bypass'
        ]
        
        for keyword in suspicious_keywords:
            if (keyword in manifest.name.lower() or 
                keyword in manifest.description.lower()):
                security_issues.append(f"Suspicious keyword in plugin metadata: {keyword}")
        
        # Check permission combinations
        dangerous_combinations = [
            (PluginPermission.FILE_SYSTEM_WRITE, PluginPermission.NETWORK_ACCESS),
            (PluginPermission.DATABASE_WRITE, PluginPermission.NETWORK_ACCESS),
            (PluginPermission.ACCESS_AI_SERVICES, PluginPermission.NETWORK_ACCESS)
        ]
        
        for perm1, perm2 in dangerous_combinations:
            if perm1 in manifest.permissions and perm2 in manifest.permissions:
                security_issues.append(
                    f"Dangerous permission combination: {perm1} + {perm2}"
                )
        
        return errors + security_issues
    
    def validate_plugin_code(self, plugin_code: str, manifest: 'PluginManifest') -> List[str]:
        """Comprehensive plugin code validation"""
        issues = []
        
        # Basic security validation
        issues.extend(PluginValidator.validate_plugin_code(plugin_code, manifest))
        
        # Malicious pattern scanning
        issues.extend(PluginValidator.scan_for_malicious_patterns(plugin_code))
        
        return issues
    
    def validate_plugin_permissions(self, plugin_id: str, 
                                   requested_permissions: List[PluginPermission]) -> List[str]:
        """Enhanced permission validation"""
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
        
        # Check for excessive permissions
        if len(requested_permissions) > 5:
            violations.append(f"Plugin requests excessive permissions: {len(requested_permissions)}")
        
        return violations
    
    def create_isolation_manager(self, plugin_id: str) -> PluginIsolationManager:
        """Create isolation manager for a plugin"""
        policy = self.get_plugin_policy(plugin_id)
        isolation_manager = PluginIsolationManager(plugin_id, policy.resource_limits)
        self.isolation_managers[plugin_id] = isolation_manager
        return isolation_manager
    
    def create_sandbox_manager(self, plugin_id: str, 
                              permissions: List[PluginPermission]) -> PluginSandboxManager:
        """Create a sandbox manager for a plugin"""
        policy = self.get_plugin_policy(plugin_id)
        return PluginSandboxManager(plugin_id, permissions, policy)
    
    def record_security_violation(self, plugin_id: str, violation_type: str, 
                                 details: str, severity: str = "medium"):
        """Record a security violation"""
        if plugin_id not in self.security_violations:
            self.security_violations[plugin_id] = []
        
        violation = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': violation_type,
            'details': details,
            'severity': severity
        }
        
        self.security_violations[plugin_id].append(violation)
        
        # Log the violation
        logger.warning(
            f"Security violation in plugin {plugin_id}: {violation_type} - {details}"
        )
        
        # Take action based on severity
        if severity == "critical":
            self._handle_critical_violation(plugin_id, violation)
    
    def _handle_critical_violation(self, plugin_id: str, violation: Dict[str, Any]):
        """Handle critical security violations"""
        # Disable plugin immediately
        logger.critical(f"Critical security violation in plugin {plugin_id}: {violation}")
        
        # Could trigger plugin shutdown here
        # This would be implemented by the plugin service
    
    def get_security_report(self, plugin_id: str) -> Dict[str, Any]:
        """Get comprehensive security report for a plugin"""
        policy = self.get_plugin_policy(plugin_id)
        violations = self.security_violations.get(plugin_id, [])
        
        # Get isolation manager report if available
        isolation_report = None
        if plugin_id in self.isolation_managers:
            isolation_report = self.isolation_managers[plugin_id].get_usage_report()
        
        return {
            'plugin_id': plugin_id,
            'security_policy': {
                'security_level': policy.security_level,
                'resource_limits': {
                    'max_memory_mb': policy.resource_limits.max_memory_mb,
                    'max_cpu_time_seconds': policy.resource_limits.max_cpu_time_seconds,
                    'max_execution_time_seconds': policy.resource_limits.max_execution_time_seconds
                }
            },
            'violations': violations,
            'violation_count': len(violations),
            'critical_violations': len([v for v in violations if v['severity'] == 'critical']),
            'isolation_report': isolation_report,
            'last_check': datetime.utcnow().isoformat()
        }
    
    def cleanup_plugin_security(self, plugin_id: str):
        """Clean up security resources for a plugin"""
        if plugin_id in self.isolation_managers:
            self.isolation_managers[plugin_id].stop_monitoring()
            del self.isolation_managers[plugin_id]
        
        # Keep violation history for audit purposes
        # Don't delete security_violations[plugin_id]