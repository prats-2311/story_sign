#!/usr/bin/env python3
"""
TiDB cluster setup and configuration script
Automates TiDB cluster deployment and optimization
"""

import os
import sys
import yaml
import subprocess
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config import get_config, DatabaseConfig

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TiDBClusterManager:
    """
    TiDB cluster management and setup
    """
    
    def __init__(self):
        self.config = get_config()
        self.cluster_config_path = Path(__file__).parent.parent / "config" / "tidb_cluster.yaml"
        self.tiup_available = False
        
    def check_prerequisites(self) -> bool:
        """Check if required tools are available"""
        logger.info("Checking prerequisites...")
        
        # Check if TiUP is installed
        try:
            result = subprocess.run(["tiup", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.tiup_available = True
                logger.info(f"TiUP is available: {result.stdout.strip()}")
            else:
                logger.warning("TiUP is not installed")
        except FileNotFoundError:
            logger.warning("TiUP is not installed")
        
        # Check Docker availability (for local development)
        docker_available = False
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                docker_available = True
                logger.info(f"Docker is available: {result.stdout.strip()}")
        except FileNotFoundError:
            logger.warning("Docker is not available")
        
        return self.tiup_available or docker_available
    
    def install_tiup(self) -> bool:
        """Install TiUP cluster management tool"""
        logger.info("Installing TiUP...")
        
        try:
            # Download and install TiUP
            install_cmd = "curl --proto '=https' --tlsv1.2 -sSf https://tiup-mirrors.pingcap.com/install.sh | sh"
            result = subprocess.run(install_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("TiUP installed successfully")
                
                # Source the environment
                os.environ["PATH"] = f"{os.path.expanduser('~/.tiup/bin')}:{os.environ.get('PATH', '')}"
                
                # Install cluster component
                subprocess.run(["tiup", "install", "cluster"], check=True)
                logger.info("TiUP cluster component installed")
                
                self.tiup_available = True
                return True
            else:
                logger.error(f"Failed to install TiUP: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error installing TiUP: {e}")
            return False
    
    def generate_cluster_config(self, deployment_type: str = "local") -> Dict[str, Any]:
        """Generate TiDB cluster configuration"""
        logger.info(f"Generating cluster configuration for {deployment_type} deployment...")
        
        if deployment_type == "local":
            # Local development configuration
            config = {
                "global": {
                    "user": "tidb",
                    "deploy_dir": "./tidb-deploy",
                    "data_dir": "./tidb-data",
                    "log_dir": "./tidb-logs"
                },
                "tidb_servers": [
                    {
                        "host": "127.0.0.1",
                        "port": 4000,
                        "status_port": 10080,
                        "config": {
                            "log.slow-threshold": 300,
                            "prepared-plan-cache.enabled": True
                        }
                    }
                ],
                "tikv_servers": [
                    {
                        "host": "127.0.0.1",
                        "port": 20160,
                        "status_port": 20180,
                        "config": {
                            "rocksdb.max-background-jobs": 4
                        }
                    }
                ],
                "pd_servers": [
                    {
                        "host": "127.0.0.1",
                        "client_port": 2379,
                        "peer_port": 2380
                    }
                ]
            }
        else:
            # Load production configuration from file
            if self.cluster_config_path.exists():
                with open(self.cluster_config_path, 'r') as f:
                    config = yaml.safe_load(f)
            else:
                logger.error(f"Cluster configuration file not found: {self.cluster_config_path}")
                return {}
        
        return config
    
    def deploy_cluster(self, deployment_type: str = "local") -> bool:
        """Deploy TiDB cluster"""
        if not self.tiup_available:
            logger.error("TiUP is not available. Cannot deploy cluster.")
            return False
        
        logger.info(f"Deploying TiDB cluster ({deployment_type})...")
        
        try:
            # Generate configuration
            config = self.generate_cluster_config(deployment_type)
            if not config:
                return False
            
            # Write temporary config file
            temp_config_path = Path("/tmp/tidb_cluster_config.yaml")
            with open(temp_config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            cluster_name = f"storysign-{deployment_type}"
            
            # Deploy cluster
            deploy_cmd = [
                "tiup", "cluster", "deploy",
                cluster_name,
                "v7.5.0",  # TiDB version
                str(temp_config_path),
                "--yes"
            ]
            
            if deployment_type == "local":
                deploy_cmd.append("--ignore-config-check")
            
            result = subprocess.run(deploy_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Cluster {cluster_name} deployed successfully")
                
                # Start cluster
                start_result = subprocess.run(
                    ["tiup", "cluster", "start", cluster_name],
                    capture_output=True, text=True
                )
                
                if start_result.returncode == 0:
                    logger.info(f"Cluster {cluster_name} started successfully")
                    return True
                else:
                    logger.error(f"Failed to start cluster: {start_result.stderr}")
                    return False
            else:
                logger.error(f"Failed to deploy cluster: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error deploying cluster: {e}")
            return False
        finally:
            # Clean up temporary config file
            if temp_config_path.exists():
                temp_config_path.unlink()
    
    def setup_docker_tidb(self) -> bool:
        """Set up TiDB using Docker for local development"""
        logger.info("Setting up TiDB using Docker...")
        
        try:
            # Create docker-compose.yml for TiDB
            docker_compose_content = """
version: '3.8'

services:
  pd:
    image: pingcap/pd:v7.5.0
    ports:
      - "2379:2379"
      - "2380:2380"
    volumes:
      - ./data/pd:/data
    command:
      - --name=pd
      - --client-urls=http://0.0.0.0:2379
      - --peer-urls=http://0.0.0.0:2380
      - --advertise-client-urls=http://pd:2379
      - --advertise-peer-urls=http://pd:2380
      - --initial-cluster=pd=http://pd:2380
      - --data-dir=/data
      - --log-file=/logs/pd.log
    restart: unless-stopped

  tikv:
    image: pingcap/tikv:v7.5.0
    ports:
      - "20160:20160"
    volumes:
      - ./data/tikv:/data
    command:
      - --addr=0.0.0.0:20160
      - --advertise-addr=tikv:20160
      - --data-dir=/data
      - --pd=pd:2379
      - --log-file=/logs/tikv.log
    depends_on:
      - pd
    restart: unless-stopped

  tidb:
    image: pingcap/tidb:v7.5.0
    ports:
      - "4000:4000"
      - "10080:10080"
    volumes:
      - ./logs/tidb:/logs
    command:
      - --store=tikv
      - --path=pd:2379
      - --log-file=/logs/tidb.log
      - --advertise-address=tidb
    depends_on:
      - tikv
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - ./data/redis:/data
    command: redis-server --appendonly yes
    restart: unless-stopped

volumes:
  pd_data:
  tikv_data:
  redis_data:
"""
            
            # Write docker-compose file
            compose_path = Path("docker-compose.tidb.yml")
            with open(compose_path, 'w') as f:
                f.write(docker_compose_content)
            
            # Create data directories
            for dir_name in ["data/pd", "data/tikv", "data/redis", "logs/tidb"]:
                Path(dir_name).mkdir(parents=True, exist_ok=True)
            
            # Start services
            result = subprocess.run([
                "docker-compose", "-f", "docker-compose.tidb.yml", "up", "-d"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("TiDB Docker services started successfully")
                
                # Wait for services to be ready
                logger.info("Waiting for services to be ready...")
                import time
                time.sleep(30)
                
                return True
            else:
                logger.error(f"Failed to start Docker services: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error setting up Docker TiDB: {e}")
            return False
    
    async def configure_database(self) -> bool:
        """Configure database settings and create initial schema"""
        logger.info("Configuring database...")
        
        try:
            from core.database_service import DatabaseService
            
            # Initialize database service
            db_service = DatabaseService()
            await db_service.initialize()
            
            if not db_service.is_connected():
                logger.error("Failed to connect to database")
                return False
            
            # Create database if it doesn't exist
            await db_service.execute_query(
                f"CREATE DATABASE IF NOT EXISTS {self.config.database.database}"
            )
            
            # Use the database
            await db_service.execute_query(f"USE {self.config.database.database}")
            
            # Set TiDB-specific configurations
            optimizations = [
                "SET GLOBAL tidb_enable_prepared_plan_cache = ON",
                "SET GLOBAL tidb_prepared_plan_cache_size = 1000",
                "SET GLOBAL tidb_enable_fast_analyze = ON",
                "SET GLOBAL tidb_enable_index_merge = ON",
                "SET GLOBAL tidb_enable_parallel_apply = ON",
                "SET GLOBAL tidb_max_chunk_size = 32768"
            ]
            
            for optimization in optimizations:
                try:
                    await db_service.execute_query(optimization)
                    logger.debug(f"Applied optimization: {optimization}")
                except Exception as e:
                    logger.warning(f"Failed to apply optimization '{optimization}': {e}")
            
            await db_service.cleanup()
            logger.info("Database configuration completed")
            return True
            
        except Exception as e:
            logger.error(f"Error configuring database: {e}")
            return False
    
    def create_monitoring_setup(self) -> bool:
        """Set up monitoring for TiDB cluster"""
        logger.info("Setting up monitoring...")
        
        try:
            # Create Prometheus configuration
            prometheus_config = """
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "tidb.rules.yml"

scrape_configs:
  - job_name: 'tidb'
    static_configs:
      - targets: ['localhost:10080']
  
  - job_name: 'tikv'
    static_configs:
      - targets: ['localhost:20180']
  
  - job_name: 'pd'
    static_configs:
      - targets: ['localhost:2379']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - localhost:9093
"""
            
            # Create monitoring directory
            monitoring_dir = Path("monitoring")
            monitoring_dir.mkdir(exist_ok=True)
            
            # Write Prometheus config
            with open(monitoring_dir / "prometheus.yml", 'w') as f:
                f.write(prometheus_config)
            
            # Create TiDB alerting rules
            alerting_rules = """
groups:
  - name: tidb
    rules:
      - alert: TiDBDown
        expr: up{job="tidb"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "TiDB instance is down"
          
      - alert: TiDBSlowQuery
        expr: tidb_server_slow_query_total > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High number of slow queries"
          
      - alert: TiDBHighConnections
        expr: tidb_server_connections > 80
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High number of connections"
"""
            
            with open(monitoring_dir / "tidb.rules.yml", 'w') as f:
                f.write(alerting_rules)
            
            logger.info("Monitoring configuration created")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up monitoring: {e}")
            return False
    
    async def run_setup(self, deployment_type: str = "local") -> bool:
        """Run complete TiDB setup process"""
        logger.info(f"Starting TiDB setup process ({deployment_type})...")
        
        # Check prerequisites
        if not self.check_prerequisites():
            logger.info("Installing TiUP...")
            if not self.install_tiup():
                logger.info("TiUP installation failed, trying Docker setup...")
                if not self.setup_docker_tidb():
                    logger.error("Both TiUP and Docker setup failed")
                    return False
        
        # Deploy cluster
        success = False
        if self.tiup_available and deployment_type != "docker":
            success = self.deploy_cluster(deployment_type)
        else:
            success = self.setup_docker_tidb()
        
        if not success:
            logger.error("Cluster deployment failed")
            return False
        
        # Configure database
        if not await self.configure_database():
            logger.error("Database configuration failed")
            return False
        
        # Set up monitoring
        if not self.create_monitoring_setup():
            logger.warning("Monitoring setup failed, but continuing...")
        
        logger.info("TiDB setup completed successfully!")
        logger.info("Connection details:")
        logger.info(f"  Host: {self.config.database.host}")
        logger.info(f"  Port: {self.config.database.port}")
        logger.info(f"  Database: {self.config.database.database}")
        
        return True


async def main():
    """Main setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="TiDB cluster setup script")
    parser.add_argument(
        "--type",
        choices=["local", "docker", "production"],
        default="local",
        help="Deployment type (default: local)"
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Skip TiUP installation"
    )
    
    args = parser.parse_args()
    
    manager = TiDBClusterManager()
    
    try:
        success = await manager.run_setup(args.type)
        if success:
            print("\n✅ TiDB cluster setup completed successfully!")
            print("\nNext steps:")
            print("1. Run database migrations: python run_migrations.py")
            print("2. Start the application: python main_api.py")
            print("3. Test optimization: python test_database_optimization.py")
        else:
            print("\n❌ TiDB cluster setup failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Setup failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())