#!/usr/bin/env python3
"""
Initialize and test the backup and disaster recovery system for StorySign Platform.
"""

import asyncio
import json
import logging
import os
import sys
import yaml
from datetime import datetime
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database_service import DatabaseService
from core.monitoring_service import DatabaseMonitoringService
from services.backup_service import BackupService
from services.disaster_recovery_service import DisasterRecoveryService
from services.deployment_service import DeploymentService


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/storysign/backup_recovery_init.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class BackupRecoveryInitializer:
    """Initialize and test backup and disaster recovery systems."""
    
    def __init__(self):
        self.config = self.load_configuration()
        self.db_service = None
        self.monitoring_service = None
        self.backup_service = None
        self.dr_service = None
        self.deployment_service = None

    def load_configuration(self) -> dict:
        """Load configuration from YAML file."""
        try:
            config_path = Path(__file__).parent / "config" / "backup_recovery.yaml"
            
            if not config_path.exists():
                logger.error(f"Configuration file not found: {config_path}")
                sys.exit(1)
            
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Expand environment variables
            config = self._expand_env_vars(config)
            
            logger.info("Configuration loaded successfully")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")
            sys.exit(1)

    def _expand_env_vars(self, obj):
        """Recursively expand environment variables in configuration."""
        if isinstance(obj, dict):
            return {k: self._expand_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._expand_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            return os.path.expandvars(obj)
        else:
            return obj

    async def initialize_services(self):
        """Initialize all backup and disaster recovery services."""
        try:
            logger.info("Initializing services...")
            
            # Initialize database service
            db_config = self.config['backup']['database']
            self.db_service = DatabaseService(db_config)
            await self.db_service.initialize()
            logger.info("Database service initialized")
            
            # Initialize monitoring service
            monitoring_config = self.config.get('monitoring', {})
            self.monitoring_service = DatabaseMonitoringService(config={"monitoring": monitoring_config})
            await self.monitoring_service.initialize()
            logger.info("Monitoring service initialized")
            
            # Initialize backup service
            backup_config = self.config['backup']
            self.backup_service = BackupService(
                self.db_service,
                self.monitoring_service,
                backup_config
            )
            logger.info("Backup service initialized")
            
            # Initialize disaster recovery service
            dr_config = self.config['disaster_recovery']
            self.dr_service = DisasterRecoveryService(
                self.db_service,
                self.backup_service,
                self.monitoring_service,
                dr_config
            )
            logger.info("Disaster recovery service initialized")
            
            # Initialize deployment service
            deployment_config = self.config['deployment']
            self.deployment_service = DeploymentService(
                self.db_service,
                self.backup_service,
                self.monitoring_service,
                deployment_config
            )
            logger.info("Deployment service initialized")
            
            logger.info("All services initialized successfully")
            
        except Exception as e:
            logger.error(f"Service initialization failed: {str(e)}")
            raise

    async def setup_directories(self):
        """Set up required directories and permissions."""
        try:
            logger.info("Setting up directories...")
            
            # Create backup directory
            backup_dir = Path(self.config['backup']['backup_directory'])
            backup_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Backup directory created: {backup_dir}")
            
            # Create log directories
            log_dir = Path("/var/log/storysign")
            log_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Log directory created: {log_dir}")
            
            # Create deployment directories
            for env_name in ['blue_environment', 'green_environment']:
                if env_name in self.config['deployment']:
                    env_config = self.config['deployment'][env_name]
                    app_dir = Path(env_config.get('app_directory', ''))
                    if app_dir:
                        app_dir.mkdir(parents=True, exist_ok=True)
                        logger.info(f"Deployment directory created: {app_dir}")
                        
                        # Create required subdirectories
                        for subdir in env_config.get('required_directories', []):
                            Path(subdir).mkdir(parents=True, exist_ok=True)
            
            logger.info("Directory setup completed")
            
        except Exception as e:
            logger.error(f"Directory setup failed: {str(e)}")
            raise

    async def test_backup_system(self):
        """Test the backup system functionality."""
        try:
            logger.info("Testing backup system...")
            
            # Test full backup creation
            logger.info("Creating test full backup...")
            backup_id = await self.backup_service.create_full_backup()
            logger.info(f"Full backup created: {backup_id}")
            
            # Test backup verification
            logger.info("Verifying backup integrity...")
            is_valid = await self.backup_service.verify_backup_integrity(backup_id)
            if is_valid:
                logger.info("Backup integrity verification passed")
            else:
                logger.error("Backup integrity verification failed")
                return False
            
            # Test incremental backup
            logger.info("Creating test incremental backup...")
            incr_backup_id = await self.backup_service.create_incremental_backup(backup_id)
            logger.info(f"Incremental backup created: {incr_backup_id}")
            
            # Test data corruption detection
            logger.info("Testing data corruption detection...")
            corruption_issues = await self.backup_service.detect_data_corruption()
            logger.info(f"Data corruption check completed: {len(corruption_issues)} issues found")
            
            logger.info("Backup system tests completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Backup system test failed: {str(e)}")
            return False

    async def test_disaster_recovery_system(self):
        """Test the disaster recovery system functionality."""
        try:
            logger.info("Testing disaster recovery system...")
            
            # Test disaster detection
            logger.info("Testing disaster detection...")
            disasters = await self.dr_service.detect_disasters()
            logger.info(f"Disaster detection completed: {len(disasters)} disasters detected")
            
            # Test DR procedures
            logger.info("Testing disaster recovery procedures...")
            test_results = await self.dr_service.test_disaster_recovery()
            
            if test_results.get('overall_success', False):
                logger.info("Disaster recovery tests passed")
                logger.info(f"Tests passed: {test_results.get('tests_passed', 0)}")
                logger.info(f"Tests failed: {test_results.get('tests_failed', 0)}")
            else:
                logger.error("Disaster recovery tests failed")
                return False
            
            # Start monitoring
            logger.info("Starting disaster recovery monitoring...")
            await self.dr_service.start_monitoring()
            logger.info("Disaster recovery monitoring started")
            
            logger.info("Disaster recovery system tests completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Disaster recovery system test failed: {str(e)}")
            return False

    async def test_deployment_system(self):
        """Test the deployment system functionality."""
        try:
            logger.info("Testing deployment system...")
            
            # Test deployment readiness
            logger.info("Testing deployment readiness...")
            readiness = await self.deployment_service.test_deployment_readiness()
            
            if readiness.get('overall_ready', False):
                logger.info("Deployment readiness check passed")
            else:
                logger.warning("Deployment readiness check failed")
                logger.warning(f"Failed checks: {[check for check in readiness.get('checks', []) if not check.get('passed', False)]}")
            
            logger.info("Deployment system tests completed")
            return True
            
        except Exception as e:
            logger.error(f"Deployment system test failed: {str(e)}")
            return False

    async def create_initial_backup(self):
        """Create an initial full backup."""
        try:
            logger.info("Creating initial system backup...")
            
            backup_id = await self.backup_service.create_full_backup()
            
            logger.info(f"Initial backup created successfully: {backup_id}")
            
            # Save backup info for reference
            backup_info = {
                "initial_backup_id": backup_id,
                "created_at": datetime.now().isoformat(),
                "backup_type": "full",
                "purpose": "initial_system_backup"
            }
            
            backup_info_file = Path(self.config['backup']['backup_directory']) / "initial_backup_info.json"
            with open(backup_info_file, 'w') as f:
                json.dump(backup_info, f, indent=2)
            
            logger.info(f"Backup information saved to: {backup_info_file}")
            return backup_id
            
        except Exception as e:
            logger.error(f"Initial backup creation failed: {str(e)}")
            raise

    async def setup_monitoring_and_alerting(self):
        """Set up monitoring and alerting."""
        try:
            logger.info("Setting up monitoring and alerting...")
            
            # Configure monitoring metrics
            await self.monitoring_service.configure_metrics([
                "backup_completed",
                "backup_failed",
                "disaster_detected",
                "recovery_initiated",
                "deployment_started",
                "deployment_completed"
            ])
            
            # Set up alerting rules
            alerting_config = self.config.get('monitoring', {}).get('alerts', {})
            for alert_name, alert_config in alerting_config.items():
                if alert_config.get('enabled', False):
                    await self.monitoring_service.create_alert_rule(
                        name=alert_name,
                        severity=alert_config.get('severity', 'medium'),
                        conditions=alert_config.get('conditions', {})
                    )
            
            logger.info("Monitoring and alerting setup completed")
            
        except Exception as e:
            logger.error(f"Monitoring setup failed: {str(e)}")
            raise

    async def generate_system_report(self):
        """Generate a system status report."""
        try:
            logger.info("Generating system status report...")
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "system_status": "operational",
                "services": {
                    "backup_service": "initialized",
                    "disaster_recovery_service": "initialized",
                    "deployment_service": "initialized",
                    "monitoring_service": "initialized"
                },
                "backup_system": {
                    "backup_directory": self.config['backup']['backup_directory'],
                    "retention_days": self.config['backup']['retention_days'],
                    "compression_enabled": self.config['backup']['compression']
                },
                "disaster_recovery": {
                    "auto_recovery_enabled": self.config['disaster_recovery']['auto_recovery_enabled'],
                    "monitoring_active": True,
                    "notification_endpoints": len(self.config['disaster_recovery']['notification_endpoints'])
                },
                "deployment": {
                    "blue_green_enabled": True,
                    "environments_configured": 2,
                    "load_balancer_type": self.config['deployment']['load_balancer'].get('type', 'none')
                }
            }
            
            report_file = Path("/var/log/storysign/system_status_report.json")
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"System status report generated: {report_file}")
            
            # Print summary
            print("\n" + "="*60)
            print("STORYSIGN BACKUP & DISASTER RECOVERY SYSTEM")
            print("="*60)
            print(f"Initialization completed at: {report['timestamp']}")
            print(f"System status: {report['system_status'].upper()}")
            print(f"Backup directory: {report['backup_system']['backup_directory']}")
            print(f"Auto-recovery enabled: {report['disaster_recovery']['auto_recovery_enabled']}")
            print(f"Blue-green deployment: {report['deployment']['blue_green_enabled']}")
            print("="*60)
            
        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}")
            raise

    async def run_initialization(self):
        """Run the complete initialization process."""
        try:
            logger.info("Starting backup and disaster recovery system initialization...")
            
            # Step 1: Set up directories
            await self.setup_directories()
            
            # Step 2: Initialize services
            await self.initialize_services()
            
            # Step 3: Test backup system
            backup_test_passed = await self.test_backup_system()
            if not backup_test_passed:
                logger.error("Backup system tests failed")
                return False
            
            # Step 4: Test disaster recovery system
            dr_test_passed = await self.test_disaster_recovery_system()
            if not dr_test_passed:
                logger.error("Disaster recovery system tests failed")
                return False
            
            # Step 5: Test deployment system
            deployment_test_passed = await self.test_deployment_system()
            if not deployment_test_passed:
                logger.warning("Deployment system tests failed (non-critical)")
            
            # Step 6: Create initial backup
            await self.create_initial_backup()
            
            # Step 7: Set up monitoring and alerting
            await self.setup_monitoring_and_alerting()
            
            # Step 8: Generate system report
            await self.generate_system_report()
            
            logger.info("Backup and disaster recovery system initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
            return False
        finally:
            # Clean up resources
            if self.dr_service:
                await self.dr_service.stop_monitoring()
            if self.db_service:
                await self.db_service.close()


async def main():
    """Main entry point."""
    initializer = BackupRecoveryInitializer()
    
    try:
        success = await initializer.run_initialization()
        
        if success:
            print("\n✅ Backup and disaster recovery system initialized successfully!")
            sys.exit(0)
        else:
            print("\n❌ Backup and disaster recovery system initialization failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Initialization interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during initialization: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())