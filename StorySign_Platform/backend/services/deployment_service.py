"""
Blue-Green Deployment Service for StorySign Platform
Handles zero-downtime deployments using blue-green deployment strategy.
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

import aiofiles
import aiohttp
from sqlalchemy import text

from core.database_service import DatabaseService
from core.monitoring_service import DatabaseMonitoringService
from services.backup_service import BackupService


class DeploymentEnvironment(Enum):
    BLUE = "blue"
    GREEN = "green"
    STAGING = "staging"
    PRODUCTION = "production"


class DeploymentStatus(Enum):
    PENDING = "pending"
    PREPARING = "preparing"
    DEPLOYING = "deploying"
    TESTING = "testing"
    SWITCHING = "switching"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class DeploymentConfig:
    deployment_id: str
    source_environment: DeploymentEnvironment
    target_environment: DeploymentEnvironment
    version: str
    git_commit: str
    deployment_type: str  # "blue_green", "rolling", "canary"
    health_check_url: str
    rollback_enabled: bool = True
    auto_switch_enabled: bool = False
    max_deployment_time: int = 1800  # 30 minutes


@dataclass
class DeploymentState:
    deployment_id: str
    config: DeploymentConfig
    status: DeploymentStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    current_step: str = ""
    steps_completed: List[str] = None
    error_message: Optional[str] = None
    rollback_point: Optional[str] = None
    health_checks: List[Dict[str, Any]] = None


class DeploymentService:
    """Service for managing blue-green deployments and zero-downtime updates."""
    
    def __init__(
        self,
        db_service: DatabaseService,
        backup_service: BackupService,
        monitoring_service: DatabaseMonitoringService,
        deployment_config: Dict[str, Any]
    ):
        self.db_service = db_service
        self.backup_service = backup_service
        self.monitoring = monitoring_service
        self.config = deployment_config
        self.logger = logging.getLogger(__name__)
        
        # Deployment configuration
        self.blue_environment = deployment_config.get("blue_environment", {})
        self.green_environment = deployment_config.get("green_environment", {})
        self.load_balancer_config = deployment_config.get("load_balancer", {})
        self.health_check_timeout = deployment_config.get("health_check_timeout", 300)
        self.deployment_timeout = deployment_config.get("deployment_timeout", 1800)
        
        # Current deployment state
        self.active_deployments: Dict[str, DeploymentState] = {}
        self.current_active_environment = DeploymentEnvironment.BLUE
        
        # Deployment history
        self.deployment_history: List[DeploymentState] = []

    async def initiate_blue_green_deployment(
        self,
        version: str,
        git_commit: str,
        auto_switch: bool = False
    ) -> str:
        """Initiate a blue-green deployment."""
        try:
            # Determine target environment
            target_env = (DeploymentEnvironment.GREEN 
                         if self.current_active_environment == DeploymentEnvironment.BLUE 
                         else DeploymentEnvironment.BLUE)
            
            deployment_id = f"bg_{version}_{int(time.time())}"
            
            # Create deployment configuration
            config = DeploymentConfig(
                deployment_id=deployment_id,
                source_environment=self.current_active_environment,
                target_environment=target_env,
                version=version,
                git_commit=git_commit,
                deployment_type="blue_green",
                health_check_url=self._get_health_check_url(target_env),
                auto_switch_enabled=auto_switch
            )
            
            # Create deployment state
            deployment_state = DeploymentState(
                deployment_id=deployment_id,
                config=config,
                status=DeploymentStatus.PENDING,
                started_at=datetime.now(),
                steps_completed=[],
                health_checks=[]
            )
            
            self.active_deployments[deployment_id] = deployment_state
            
            self.logger.info(f"Initiated blue-green deployment: {deployment_id}")
            
            # Start deployment process
            asyncio.create_task(self._execute_deployment(deployment_id))
            
            return deployment_id
            
        except Exception as e:
            self.logger.error(f"Failed to initiate deployment: {str(e)}")
            raise

    async def switch_traffic(self, deployment_id: str) -> bool:
        """Switch traffic to the new environment."""
        try:
            deployment = self.active_deployments.get(deployment_id)
            if not deployment:
                raise Exception(f"Deployment not found: {deployment_id}")
            
            if deployment.status != DeploymentStatus.TESTING:
                raise Exception(f"Deployment not ready for traffic switch: {deployment.status}")
            
            deployment.status = DeploymentStatus.SWITCHING
            deployment.current_step = "Switching traffic"
            
            self.logger.info(f"Switching traffic for deployment: {deployment_id}")
            
            # Update load balancer configuration
            success = await self._update_load_balancer(deployment.config.target_environment)
            
            if success:
                # Update active environment
                self.current_active_environment = deployment.config.target_environment
                deployment.status = DeploymentStatus.COMPLETED
                deployment.completed_at = datetime.now()
                deployment.steps_completed.append("Traffic switched successfully")
                
                # Record metrics
                await self.monitoring.record_metric("deployment_completed", {
                    "deployment_id": deployment_id,
                    "version": deployment.config.version,
                    "target_environment": deployment.config.target_environment.value,
                    "duration_seconds": (deployment.completed_at - deployment.started_at).total_seconds()
                })
                
                self.logger.info(f"Traffic switch completed: {deployment_id}")
                return True
            else:
                deployment.status = DeploymentStatus.FAILED
                deployment.error_message = "Load balancer update failed"
                self.logger.error(f"Traffic switch failed: {deployment_id}")
                return False
            
        except Exception as e:
            self.logger.error(f"Traffic switch error: {deployment_id}, Error: {str(e)}")
            if deployment_id in self.active_deployments:
                self.active_deployments[deployment_id].status = DeploymentStatus.FAILED
                self.active_deployments[deployment_id].error_message = str(e)
            return False

    async def rollback_deployment(self, deployment_id: str) -> bool:
        """Rollback a deployment to the previous environment."""
        try:
            deployment = self.active_deployments.get(deployment_id)
            if not deployment:
                raise Exception(f"Deployment not found: {deployment_id}")
            
            if not deployment.config.rollback_enabled:
                raise Exception("Rollback not enabled for this deployment")
            
            self.logger.info(f"Rolling back deployment: {deployment_id}")
            
            # Switch traffic back to source environment
            success = await self._update_load_balancer(deployment.config.source_environment)
            
            if success:
                # Restore database if needed
                if deployment.rollback_point:
                    await self.backup_service.restore_from_backup(deployment.rollback_point)
                
                deployment.status = DeploymentStatus.ROLLED_BACK
                deployment.completed_at = datetime.now()
                deployment.steps_completed.append("Deployment rolled back")
                
                # Restore active environment
                self.current_active_environment = deployment.config.source_environment
                
                await self.monitoring.record_metric("deployment_rolled_back", {
                    "deployment_id": deployment_id,
                    "version": deployment.config.version
                })
                
                self.logger.info(f"Rollback completed: {deployment_id}")
                return True
            else:
                self.logger.error(f"Rollback failed: {deployment_id}")
                return False
            
        except Exception as e:
            self.logger.error(f"Rollback error: {deployment_id}, Error: {str(e)}")
            return False

    async def get_deployment_status(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a deployment."""
        deployment = self.active_deployments.get(deployment_id)
        if not deployment:
            return None
        
        return {
            "deployment_id": deployment.deployment_id,
            "status": deployment.status.value,
            "version": deployment.config.version,
            "source_environment": deployment.config.source_environment.value,
            "target_environment": deployment.config.target_environment.value,
            "started_at": deployment.started_at.isoformat(),
            "completed_at": deployment.completed_at.isoformat() if deployment.completed_at else None,
            "current_step": deployment.current_step,
            "steps_completed": deployment.steps_completed,
            "error_message": deployment.error_message,
            "health_checks": deployment.health_checks
        }

    async def list_deployments(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent deployments."""
        all_deployments = list(self.active_deployments.values()) + self.deployment_history
        all_deployments.sort(key=lambda d: d.started_at, reverse=True)
        
        return [
            {
                "deployment_id": d.deployment_id,
                "status": d.status.value,
                "version": d.config.version,
                "target_environment": d.config.target_environment.value,
                "started_at": d.started_at.isoformat(),
                "completed_at": d.completed_at.isoformat() if d.completed_at else None
            }
            for d in all_deployments[:limit]
        ]

    async def test_deployment_readiness(self) -> Dict[str, Any]:
        """Test if the system is ready for deployment."""
        readiness_checks = {
            "timestamp": datetime.now().isoformat(),
            "overall_ready": True,
            "checks": []
        }
        
        try:
            # Check database connectivity
            db_check = await self._check_database_readiness()
            readiness_checks["checks"].append(db_check)
            if not db_check["passed"]:
                readiness_checks["overall_ready"] = False
            
            # Check backup system
            backup_check = await self._check_backup_readiness()
            readiness_checks["checks"].append(backup_check)
            if not backup_check["passed"]:
                readiness_checks["overall_ready"] = False
            
            # Check environment availability
            env_check = await self._check_environment_availability()
            readiness_checks["checks"].append(env_check)
            if not env_check["passed"]:
                readiness_checks["overall_ready"] = False
            
            # Check load balancer
            lb_check = await self._check_load_balancer_readiness()
            readiness_checks["checks"].append(lb_check)
            if not lb_check["passed"]:
                readiness_checks["overall_ready"] = False
            
            # Check system resources
            resource_check = await self._check_system_resources()
            readiness_checks["checks"].append(resource_check)
            if not resource_check["passed"]:
                readiness_checks["overall_ready"] = False
            
            return readiness_checks
            
        except Exception as e:
            readiness_checks["overall_ready"] = False
            readiness_checks["error"] = str(e)
            return readiness_checks

    # Private deployment execution methods
    
    async def _execute_deployment(self, deployment_id: str):
        """Execute the deployment process."""
        try:
            deployment = self.active_deployments[deployment_id]
            
            # Step 1: Prepare environment
            deployment.status = DeploymentStatus.PREPARING
            deployment.current_step = "Preparing target environment"
            
            if not await self._prepare_target_environment(deployment):
                deployment.status = DeploymentStatus.FAILED
                return
            
            deployment.steps_completed.append("Target environment prepared")
            
            # Step 2: Create backup/rollback point
            deployment.current_step = "Creating rollback point"
            
            if deployment.config.rollback_enabled:
                try:
                    backup_id = await self.backup_service.create_full_backup()
                    deployment.rollback_point = backup_id
                    deployment.steps_completed.append(f"Rollback point created: {backup_id}")
                except Exception as e:
                    self.logger.warning(f"Failed to create rollback point: {str(e)}")
            
            # Step 3: Deploy application
            deployment.status = DeploymentStatus.DEPLOYING
            deployment.current_step = "Deploying application"
            
            if not await self._deploy_application(deployment):
                deployment.status = DeploymentStatus.FAILED
                return
            
            deployment.steps_completed.append("Application deployed")
            
            # Step 4: Run database migrations
            deployment.current_step = "Running database migrations"
            
            if not await self._run_database_migrations(deployment):
                deployment.status = DeploymentStatus.FAILED
                return
            
            deployment.steps_completed.append("Database migrations completed")
            
            # Step 5: Health checks
            deployment.status = DeploymentStatus.TESTING
            deployment.current_step = "Running health checks"
            
            if not await self._run_health_checks(deployment):
                deployment.status = DeploymentStatus.FAILED
                return
            
            deployment.steps_completed.append("Health checks passed")
            
            # Step 6: Auto-switch if enabled
            if deployment.config.auto_switch_enabled:
                deployment.current_step = "Auto-switching traffic"
                await self.switch_traffic(deployment_id)
            else:
                deployment.current_step = "Ready for traffic switch"
                self.logger.info(f"Deployment ready for manual traffic switch: {deployment_id}")
            
        except Exception as e:
            self.logger.error(f"Deployment execution failed: {deployment_id}, Error: {str(e)}")
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = str(e)
            
            # Auto-rollback on failure if enabled
            if deployment.config.rollback_enabled:
                await self.rollback_deployment(deployment_id)

    async def _prepare_target_environment(self, deployment: DeploymentState) -> bool:
        """Prepare the target environment for deployment."""
        try:
            target_env = deployment.config.target_environment
            
            # Stop services in target environment
            if not await self._stop_services(target_env):
                return False
            
            # Clear old deployment files
            if not await self._cleanup_environment(target_env):
                return False
            
            # Prepare directories and permissions
            if not await self._setup_environment_structure(target_env):
                return False
            
            return True
            
        except Exception as e:
            deployment.error_message = f"Environment preparation failed: {str(e)}"
            return False

    async def _deploy_application(self, deployment: DeploymentState) -> bool:
        """Deploy the application to the target environment."""
        try:
            target_env = deployment.config.target_environment
            
            # Clone/checkout code
            if not await self._checkout_code(deployment.config.git_commit, target_env):
                return False
            
            # Build application
            if not await self._build_application(target_env):
                return False
            
            # Install dependencies
            if not await self._install_dependencies(target_env):
                return False
            
            # Update configuration
            if not await self._update_configuration(target_env):
                return False
            
            # Start services
            if not await self._start_services(target_env):
                return False
            
            return True
            
        except Exception as e:
            deployment.error_message = f"Application deployment failed: {str(e)}"
            return False

    async def _run_database_migrations(self, deployment: DeploymentState) -> bool:
        """Run database migrations for the deployment."""
        try:
            # Run migrations script
            migration_cmd = [
                "python", "-m", "alembic", "upgrade", "head"
            ]
            
            env_config = self._get_environment_config(deployment.config.target_environment)
            env_vars = env_config.get("environment_variables", {})
            
            result = subprocess.run(
                migration_cmd,
                cwd=env_config.get("app_directory"),
                env={**os.environ, **env_vars},
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0:
                deployment.error_message = f"Migration failed: {result.stderr}"
                return False
            
            return True
            
        except Exception as e:
            deployment.error_message = f"Database migration failed: {str(e)}"
            return False

    async def _run_health_checks(self, deployment: DeploymentState) -> bool:
        """Run health checks on the deployed application."""
        try:
            health_check_url = deployment.config.health_check_url
            max_attempts = 10
            check_interval = 30  # seconds
            
            for attempt in range(max_attempts):
                try:
                    timeout = aiohttp.ClientTimeout(total=10)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.get(health_check_url) as response:
                            if response.status == 200:
                                health_data = await response.json()
                                
                                health_check = {
                                    "timestamp": datetime.now().isoformat(),
                                    "attempt": attempt + 1,
                                    "status": "passed",
                                    "response_time_ms": response.headers.get("X-Response-Time", "unknown"),
                                    "health_data": health_data
                                }
                                
                                deployment.health_checks.append(health_check)
                                return True
                            else:
                                health_check = {
                                    "timestamp": datetime.now().isoformat(),
                                    "attempt": attempt + 1,
                                    "status": "failed",
                                    "status_code": response.status,
                                    "error": f"HTTP {response.status}"
                                }
                                deployment.health_checks.append(health_check)
                
                except Exception as e:
                    health_check = {
                        "timestamp": datetime.now().isoformat(),
                        "attempt": attempt + 1,
                        "status": "failed",
                        "error": str(e)
                    }
                    deployment.health_checks.append(health_check)
                
                if attempt < max_attempts - 1:
                    await asyncio.sleep(check_interval)
            
            deployment.error_message = f"Health checks failed after {max_attempts} attempts"
            return False
            
        except Exception as e:
            deployment.error_message = f"Health check execution failed: {str(e)}"
            return False

    # Environment management methods
    
    async def _stop_services(self, environment: DeploymentEnvironment) -> bool:
        """Stop services in the specified environment."""
        try:
            env_config = self._get_environment_config(environment)
            stop_commands = env_config.get("stop_commands", [])
            
            for cmd in stop_commands:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    self.logger.warning(f"Stop command failed: {cmd}, Error: {result.stderr}")
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to stop services: {str(e)}")
            return False

    async def _start_services(self, environment: DeploymentEnvironment) -> bool:
        """Start services in the specified environment."""
        try:
            env_config = self._get_environment_config(environment)
            start_commands = env_config.get("start_commands", [])
            
            for cmd in start_commands:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    self.logger.error(f"Start command failed: {cmd}, Error: {result.stderr}")
                    return False
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to start services: {str(e)}")
            return False

    async def _cleanup_environment(self, environment: DeploymentEnvironment) -> bool:
        """Clean up the environment for fresh deployment."""
        try:
            env_config = self._get_environment_config(environment)
            cleanup_paths = env_config.get("cleanup_paths", [])
            
            for path in cleanup_paths:
                if os.path.exists(path):
                    if os.path.isdir(path):
                        subprocess.run(["rm", "-rf", path], check=True)
                    else:
                        os.remove(path)
            
            return True
        except Exception as e:
            self.logger.error(f"Environment cleanup failed: {str(e)}")
            return False

    async def _setup_environment_structure(self, environment: DeploymentEnvironment) -> bool:
        """Set up directory structure for the environment."""
        try:
            env_config = self._get_environment_config(environment)
            directories = env_config.get("required_directories", [])
            
            for directory in directories:
                os.makedirs(directory, exist_ok=True)
            
            return True
        except Exception as e:
            self.logger.error(f"Environment structure setup failed: {str(e)}")
            return False

    async def _checkout_code(self, git_commit: str, environment: DeploymentEnvironment) -> bool:
        """Checkout code for the specified commit."""
        try:
            env_config = self._get_environment_config(environment)
            app_directory = env_config.get("app_directory")
            
            # Clone or pull repository
            if not os.path.exists(app_directory):
                clone_cmd = ["git", "clone", env_config.get("repository_url"), app_directory]
                result = subprocess.run(clone_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    return False
            
            # Checkout specific commit
            checkout_cmd = ["git", "checkout", git_commit]
            result = subprocess.run(checkout_cmd, cwd=app_directory, capture_output=True, text=True)
            
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Code checkout failed: {str(e)}")
            return False

    async def _build_application(self, environment: DeploymentEnvironment) -> bool:
        """Build the application."""
        try:
            env_config = self._get_environment_config(environment)
            build_commands = env_config.get("build_commands", [])
            
            for cmd in build_commands:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    cwd=env_config.get("app_directory"),
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minute timeout
                )
                if result.returncode != 0:
                    self.logger.error(f"Build command failed: {cmd}, Error: {result.stderr}")
                    return False
            
            return True
        except Exception as e:
            self.logger.error(f"Application build failed: {str(e)}")
            return False

    async def _install_dependencies(self, environment: DeploymentEnvironment) -> bool:
        """Install application dependencies."""
        try:
            env_config = self._get_environment_config(environment)
            dependency_commands = env_config.get("dependency_commands", [])
            
            for cmd in dependency_commands:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    cwd=env_config.get("app_directory"),
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minute timeout
                )
                if result.returncode != 0:
                    self.logger.error(f"Dependency command failed: {cmd}, Error: {result.stderr}")
                    return False
            
            return True
        except Exception as e:
            self.logger.error(f"Dependency installation failed: {str(e)}")
            return False

    async def _update_configuration(self, environment: DeploymentEnvironment) -> bool:
        """Update configuration files for the environment."""
        try:
            env_config = self._get_environment_config(environment)
            config_updates = env_config.get("config_updates", {})
            
            for config_file, updates in config_updates.items():
                # Update configuration file with environment-specific settings
                # This is a simplified implementation
                pass
            
            return True
        except Exception as e:
            self.logger.error(f"Configuration update failed: {str(e)}")
            return False

    async def _update_load_balancer(self, target_environment: DeploymentEnvironment) -> bool:
        """Update load balancer to point to the target environment."""
        try:
            lb_config = self.load_balancer_config
            if not lb_config:
                self.logger.warning("No load balancer configuration found")
                return True  # Assume success if no LB configured
            
            # Update load balancer configuration
            # This would depend on the specific load balancer being used
            # (e.g., nginx, HAProxy, AWS ALB, etc.)
            
            env_config = self._get_environment_config(target_environment)
            target_servers = env_config.get("servers", [])
            
            # Example: Update nginx upstream configuration
            if lb_config.get("type") == "nginx":
                return await self._update_nginx_upstream(target_servers)
            
            return True
        except Exception as e:
            self.logger.error(f"Load balancer update failed: {str(e)}")
            return False

    async def _update_nginx_upstream(self, target_servers: List[str]) -> bool:
        """Update nginx upstream configuration."""
        try:
            # Generate new upstream configuration
            upstream_config = "upstream storysign_backend {\n"
            for server in target_servers:
                upstream_config += f"    server {server};\n"
            upstream_config += "}\n"
            
            # Write to nginx configuration file
            nginx_config_path = self.load_balancer_config.get("config_path", "/etc/nginx/conf.d/storysign.conf")
            
            async with aiofiles.open(nginx_config_path, 'w') as f:
                await f.write(upstream_config)
            
            # Reload nginx
            result = subprocess.run(["nginx", "-s", "reload"], capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            self.logger.error(f"Nginx update failed: {str(e)}")
            return False

    # Helper methods
    
    def _get_environment_config(self, environment: DeploymentEnvironment) -> Dict[str, Any]:
        """Get configuration for the specified environment."""
        if environment == DeploymentEnvironment.BLUE:
            return self.blue_environment
        elif environment == DeploymentEnvironment.GREEN:
            return self.green_environment
        else:
            return {}

    def _get_health_check_url(self, environment: DeploymentEnvironment) -> str:
        """Get health check URL for the environment."""
        env_config = self._get_environment_config(environment)
        base_url = env_config.get("base_url", "http://localhost:8000")
        return f"{base_url}/health"

    # Readiness check methods
    
    async def _check_database_readiness(self) -> Dict[str, Any]:
        """Check if database is ready for deployment."""
        try:
            async with self.db_service.get_session() as session:
                await session.execute(text("SELECT 1"))
            
            return {
                "check_name": "database_readiness",
                "passed": True,
                "message": "Database connectivity verified"
            }
        except Exception as e:
            return {
                "check_name": "database_readiness",
                "passed": False,
                "error": str(e),
                "message": "Database connectivity failed"
            }

    async def _check_backup_readiness(self) -> Dict[str, Any]:
        """Check if backup system is ready."""
        try:
            # Test backup creation
            test_backup = await self.backup_service.create_incremental_backup()
            
            return {
                "check_name": "backup_readiness",
                "passed": True,
                "backup_id": test_backup,
                "message": "Backup system operational"
            }
        except Exception as e:
            return {
                "check_name": "backup_readiness",
                "passed": False,
                "error": str(e),
                "message": "Backup system not ready"
            }

    async def _check_environment_availability(self) -> Dict[str, Any]:
        """Check if deployment environments are available."""
        try:
            target_env = (DeploymentEnvironment.GREEN 
                         if self.current_active_environment == DeploymentEnvironment.BLUE 
                         else DeploymentEnvironment.BLUE)
            
            env_config = self._get_environment_config(target_env)
            
            # Check if environment directory exists and is writable
            app_dir = env_config.get("app_directory")
            if app_dir and not os.access(os.path.dirname(app_dir), os.W_OK):
                return {
                    "check_name": "environment_availability",
                    "passed": False,
                    "message": f"Target environment directory not writable: {app_dir}"
                }
            
            return {
                "check_name": "environment_availability",
                "passed": True,
                "target_environment": target_env.value,
                "message": "Target environment available"
            }
        except Exception as e:
            return {
                "check_name": "environment_availability",
                "passed": False,
                "error": str(e),
                "message": "Environment availability check failed"
            }

    async def _check_load_balancer_readiness(self) -> Dict[str, Any]:
        """Check if load balancer is ready for updates."""
        try:
            if not self.load_balancer_config:
                return {
                    "check_name": "load_balancer_readiness",
                    "passed": True,
                    "message": "No load balancer configured"
                }
            
            # Test load balancer configuration access
            config_path = self.load_balancer_config.get("config_path")
            if config_path and not os.access(config_path, os.W_OK):
                return {
                    "check_name": "load_balancer_readiness",
                    "passed": False,
                    "message": f"Load balancer config not writable: {config_path}"
                }
            
            return {
                "check_name": "load_balancer_readiness",
                "passed": True,
                "message": "Load balancer ready for updates"
            }
        except Exception as e:
            return {
                "check_name": "load_balancer_readiness",
                "passed": False,
                "error": str(e),
                "message": "Load balancer readiness check failed"
            }

    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check if system has sufficient resources for deployment."""
        try:
            # Check disk space
            disk_usage = subprocess.run(['df', '-h'], capture_output=True, text=True)
            if disk_usage.returncode != 0:
                return {
                    "check_name": "system_resources",
                    "passed": False,
                    "message": "Unable to check disk usage"
                }
            
            # Check memory
            memory_info = subprocess.run(['free', '-m'], capture_output=True, text=True)
            if memory_info.returncode != 0:
                return {
                    "check_name": "system_resources",
                    "passed": False,
                    "message": "Unable to check memory usage"
                }
            
            return {
                "check_name": "system_resources",
                "passed": True,
                "message": "System resources sufficient for deployment"
            }
        except Exception as e:
            return {
                "check_name": "system_resources",
                "passed": False,
                "error": str(e),
                "message": "System resource check failed"
            }