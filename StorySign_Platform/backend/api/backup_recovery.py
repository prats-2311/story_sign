"""
Backup and Disaster Recovery API endpoints for StorySign Platform.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field

from core.database_service import DatabaseService
from core.monitoring_service import DatabaseMonitoringService
from services.backup_service import BackupService, BackupType, BackupStatus
from services.disaster_recovery_service import DisasterRecoveryService, DisasterType, RecoveryStatus
from services.deployment_service import DeploymentService, DeploymentEnvironment
from middleware.auth_middleware import get_current_admin_user


# Pydantic models for API requests/responses

class BackupRequest(BaseModel):
    backup_type: str = Field(..., description="Type of backup: 'full' or 'incremental'")
    since_backup_id: Optional[str] = Field(None, description="Reference backup ID for incremental backups")


class BackupResponse(BaseModel):
    backup_id: str
    backup_type: str
    status: str
    timestamp: datetime
    size_bytes: int
    checksum: str
    tables_included: List[str]
    error_message: Optional[str] = None


class RestoreRequest(BaseModel):
    backup_id: str = Field(..., description="ID of the backup to restore from")
    target_database: Optional[str] = Field(None, description="Target database name (optional)")


class DisasterResponse(BaseModel):
    event_id: str
    disaster_type: str
    detected_at: datetime
    description: str
    severity: str
    affected_components: List[str]
    recovery_status: str
    recovery_actions: Optional[List[str]] = None
    error_messages: Optional[List[str]] = None


class DeploymentRequest(BaseModel):
    version: str = Field(..., description="Version to deploy")
    git_commit: str = Field(..., description="Git commit hash")
    auto_switch: bool = Field(False, description="Automatically switch traffic after deployment")


class DeploymentResponse(BaseModel):
    deployment_id: str
    status: str
    version: str
    source_environment: str
    target_environment: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    current_step: str
    steps_completed: List[str]
    error_message: Optional[str] = None


# Initialize router
router = APIRouter()
logger = logging.getLogger(__name__)


# Dependency injection
async def get_backup_service() -> BackupService:
    # This would be injected from the application container
    # For now, we'll assume it's available globally
    from main import app
    return app.state.backup_service


async def get_disaster_recovery_service() -> DisasterRecoveryService:
    from main import app
    return app.state.disaster_recovery_service


async def get_deployment_service() -> DeploymentService:
    from main import app
    return app.state.deployment_service


# Backup Management Endpoints

@router.post("/backups", response_model=BackupResponse)
async def create_backup(
    request: BackupRequest,
    background_tasks: BackgroundTasks,
    backup_service: BackupService = Depends(get_backup_service),
    current_user = Depends(get_current_admin_user)
):
    """Create a new backup."""
    try:
        if request.backup_type == "full":
            backup_id = await backup_service.create_full_backup()
        elif request.backup_type == "incremental":
            backup_id = await backup_service.create_incremental_backup(request.since_backup_id)
        else:
            raise HTTPException(status_code=400, detail="Invalid backup type. Must be 'full' or 'incremental'")
        
        # Get backup metadata
        metadata = backup_service.backup_metadata.get(backup_id)
        if not metadata:
            raise HTTPException(status_code=500, detail="Backup created but metadata not found")
        
        return BackupResponse(
            backup_id=metadata.backup_id,
            backup_type=metadata.backup_type.value,
            status=metadata.status.value,
            timestamp=metadata.timestamp,
            size_bytes=metadata.size_bytes,
            checksum=metadata.checksum,
            tables_included=metadata.tables_included,
            error_message=metadata.error_message
        )
        
    except Exception as e:
        logger.error(f"Backup creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Backup creation failed: {str(e)}")


@router.get("/backups", response_model=List[BackupResponse])
async def list_backups(
    limit: int = Query(50, ge=1, le=100),
    backup_service: BackupService = Depends(get_backup_service),
    current_user = Depends(get_current_admin_user)
):
    """List all backups."""
    try:
        backups = []
        for backup_id, metadata in backup_service.backup_metadata.items():
            backups.append(BackupResponse(
                backup_id=metadata.backup_id,
                backup_type=metadata.backup_type.value,
                status=metadata.status.value,
                timestamp=metadata.timestamp,
                size_bytes=metadata.size_bytes,
                checksum=metadata.checksum,
                tables_included=metadata.tables_included,
                error_message=metadata.error_message
            ))
        
        # Sort by timestamp, most recent first
        backups.sort(key=lambda b: b.timestamp, reverse=True)
        
        return backups[:limit]
        
    except Exception as e:
        logger.error(f"Failed to list backups: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list backups: {str(e)}")


@router.get("/backups/{backup_id}", response_model=BackupResponse)
async def get_backup(
    backup_id: str,
    backup_service: BackupService = Depends(get_backup_service),
    current_user = Depends(get_current_admin_user)
):
    """Get details of a specific backup."""
    try:
        metadata = backup_service.backup_metadata.get(backup_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Backup not found")
        
        return BackupResponse(
            backup_id=metadata.backup_id,
            backup_type=metadata.backup_type.value,
            status=metadata.status.value,
            timestamp=metadata.timestamp,
            size_bytes=metadata.size_bytes,
            checksum=metadata.checksum,
            tables_included=metadata.tables_included,
            error_message=metadata.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get backup {backup_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get backup: {str(e)}")


@router.post("/backups/{backup_id}/verify")
async def verify_backup(
    backup_id: str,
    backup_service: BackupService = Depends(get_backup_service),
    current_user = Depends(get_current_admin_user)
):
    """Verify the integrity of a backup."""
    try:
        is_valid = await backup_service.verify_backup_integrity(backup_id)
        
        return {
            "backup_id": backup_id,
            "is_valid": is_valid,
            "verified_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Backup verification failed for {backup_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Backup verification failed: {str(e)}")


@router.post("/backups/{backup_id}/restore")
async def restore_backup(
    backup_id: str,
    request: RestoreRequest,
    background_tasks: BackgroundTasks,
    backup_service: BackupService = Depends(get_backup_service),
    current_user = Depends(get_current_admin_user)
):
    """Restore from a backup."""
    try:
        # Verify backup exists
        if backup_id not in backup_service.backup_metadata:
            raise HTTPException(status_code=404, detail="Backup not found")
        
        # Start restore process in background
        background_tasks.add_task(
            backup_service.restore_from_backup,
            backup_id,
            request.target_database
        )
        
        return {
            "backup_id": backup_id,
            "restore_initiated": True,
            "message": "Restore process started in background",
            "initiated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Restore initiation failed for {backup_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Restore initiation failed: {str(e)}")


@router.delete("/backups/cleanup")
async def cleanup_old_backups(
    backup_service: BackupService = Depends(get_backup_service),
    current_user = Depends(get_current_admin_user)
):
    """Clean up old backups based on retention policy."""
    try:
        cleaned_count = await backup_service.cleanup_old_backups()
        
        return {
            "cleaned_backups": cleaned_count,
            "cleanup_completed_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Backup cleanup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Backup cleanup failed: {str(e)}")


# Disaster Recovery Endpoints

@router.get("/disasters", response_model=List[DisasterResponse])
async def list_disasters(
    dr_service: DisasterRecoveryService = Depends(get_disaster_recovery_service),
    current_user = Depends(get_current_admin_user)
):
    """List active disasters."""
    try:
        disasters = []
        for disaster_id, disaster in dr_service.active_disasters.items():
            disasters.append(DisasterResponse(
                event_id=disaster.event_id,
                disaster_type=disaster.disaster_type.value,
                detected_at=disaster.detected_at,
                description=disaster.description,
                severity=disaster.severity,
                affected_components=disaster.affected_components,
                recovery_status=disaster.recovery_status.value,
                recovery_actions=disaster.recovery_actions,
                error_messages=disaster.error_messages
            ))
        
        return disasters
        
    except Exception as e:
        logger.error(f"Failed to list disasters: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list disasters: {str(e)}")


@router.post("/disasters/detect")
async def detect_disasters(
    dr_service: DisasterRecoveryService = Depends(get_disaster_recovery_service),
    current_user = Depends(get_current_admin_user)
):
    """Manually trigger disaster detection."""
    try:
        detected_disasters = await dr_service.detect_disasters()
        
        return {
            "detection_timestamp": datetime.now().isoformat(),
            "disasters_detected": len(detected_disasters),
            "disasters": [
                {
                    "event_id": d.event_id,
                    "disaster_type": d.disaster_type.value,
                    "severity": d.severity,
                    "description": d.description
                }
                for d in detected_disasters
            ]
        }
        
    except Exception as e:
        logger.error(f"Disaster detection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Disaster detection failed: {str(e)}")


@router.post("/disasters/{disaster_id}/recover")
async def initiate_recovery(
    disaster_id: str,
    background_tasks: BackgroundTasks,
    dr_service: DisasterRecoveryService = Depends(get_disaster_recovery_service),
    current_user = Depends(get_current_admin_user)
):
    """Initiate recovery for a specific disaster."""
    try:
        if disaster_id not in dr_service.active_disasters:
            raise HTTPException(status_code=404, detail="Disaster not found")
        
        # Start recovery in background
        background_tasks.add_task(dr_service.initiate_recovery, disaster_id)
        
        return {
            "disaster_id": disaster_id,
            "recovery_initiated": True,
            "message": "Recovery process started",
            "initiated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recovery initiation failed for {disaster_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Recovery initiation failed: {str(e)}")


@router.post("/disasters/failover")
async def perform_failover(
    target_environment: str = "standby",
    background_tasks: BackgroundTasks = None,
    dr_service: DisasterRecoveryService = Depends(get_disaster_recovery_service),
    current_user = Depends(get_current_admin_user)
):
    """Perform failover to standby environment."""
    try:
        # Start failover in background
        if background_tasks:
            background_tasks.add_task(dr_service.perform_failover, target_environment)
            
            return {
                "failover_initiated": True,
                "target_environment": target_environment,
                "message": "Failover process started",
                "initiated_at": datetime.now().isoformat()
            }
        else:
            # Synchronous failover (use with caution)
            success = await dr_service.perform_failover(target_environment)
            
            return {
                "failover_completed": success,
                "target_environment": target_environment,
                "completed_at": datetime.now().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Failover failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failover failed: {str(e)}")


@router.post("/disasters/test")
async def test_disaster_recovery(
    dr_service: DisasterRecoveryService = Depends(get_disaster_recovery_service),
    current_user = Depends(get_current_admin_user)
):
    """Test disaster recovery procedures."""
    try:
        test_results = await dr_service.test_disaster_recovery()
        
        return test_results
        
    except Exception as e:
        logger.error(f"DR test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DR test failed: {str(e)}")


# Data Corruption Detection

@router.get("/data-integrity/check")
async def check_data_integrity(
    backup_service: BackupService = Depends(get_backup_service),
    current_user = Depends(get_current_admin_user)
):
    """Check for data corruption issues."""
    try:
        corruption_issues = await backup_service.detect_data_corruption()
        
        return {
            "check_timestamp": datetime.now().isoformat(),
            "issues_found": len(corruption_issues),
            "issues": corruption_issues
        }
        
    except Exception as e:
        logger.error(f"Data integrity check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Data integrity check failed: {str(e)}")


# Blue-Green Deployment Endpoints

@router.post("/deployments", response_model=DeploymentResponse)
async def create_deployment(
    request: DeploymentRequest,
    deployment_service: DeploymentService = Depends(get_deployment_service),
    current_user = Depends(get_current_admin_user)
):
    """Initiate a blue-green deployment."""
    try:
        deployment_id = await deployment_service.initiate_blue_green_deployment(
            version=request.version,
            git_commit=request.git_commit,
            auto_switch=request.auto_switch
        )
        
        # Get deployment status
        status = await deployment_service.get_deployment_status(deployment_id)
        if not status:
            raise HTTPException(status_code=500, detail="Deployment created but status not available")
        
        return DeploymentResponse(**status)
        
    except Exception as e:
        logger.error(f"Deployment creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Deployment creation failed: {str(e)}")


@router.get("/deployments", response_model=List[Dict[str, Any]])
async def list_deployments(
    limit: int = Query(50, ge=1, le=100),
    deployment_service: DeploymentService = Depends(get_deployment_service),
    current_user = Depends(get_current_admin_user)
):
    """List recent deployments."""
    try:
        deployments = await deployment_service.list_deployments(limit)
        return deployments
        
    except Exception as e:
        logger.error(f"Failed to list deployments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list deployments: {str(e)}")


@router.get("/deployments/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: str,
    deployment_service: DeploymentService = Depends(get_deployment_service),
    current_user = Depends(get_current_admin_user)
):
    """Get deployment status."""
    try:
        status = await deployment_service.get_deployment_status(deployment_id)
        if not status:
            raise HTTPException(status_code=404, detail="Deployment not found")
        
        return DeploymentResponse(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get deployment {deployment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get deployment: {str(e)}")


@router.post("/deployments/{deployment_id}/switch-traffic")
async def switch_traffic(
    deployment_id: str,
    deployment_service: DeploymentService = Depends(get_deployment_service),
    current_user = Depends(get_current_admin_user)
):
    """Switch traffic to the new deployment."""
    try:
        success = await deployment_service.switch_traffic(deployment_id)
        
        return {
            "deployment_id": deployment_id,
            "traffic_switched": success,
            "switched_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Traffic switch failed for {deployment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Traffic switch failed: {str(e)}")


@router.post("/deployments/{deployment_id}/rollback")
async def rollback_deployment(
    deployment_id: str,
    deployment_service: DeploymentService = Depends(get_deployment_service),
    current_user = Depends(get_current_admin_user)
):
    """Rollback a deployment."""
    try:
        success = await deployment_service.rollback_deployment(deployment_id)
        
        return {
            "deployment_id": deployment_id,
            "rollback_completed": success,
            "rolled_back_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Rollback failed for {deployment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Rollback failed: {str(e)}")


@router.get("/deployments/readiness/check")
async def check_deployment_readiness(
    deployment_service: DeploymentService = Depends(get_deployment_service),
    current_user = Depends(get_current_admin_user)
):
    """Check if the system is ready for deployment."""
    try:
        readiness = await deployment_service.test_deployment_readiness()
        return readiness
        
    except Exception as e:
        logger.error(f"Deployment readiness check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Deployment readiness check failed: {str(e)}")


# System Health and Status

@router.get("/system/health")
async def get_system_health(
    dr_service: DisasterRecoveryService = Depends(get_disaster_recovery_service),
    backup_service: BackupService = Depends(get_backup_service),
    current_user = Depends(get_current_admin_user)
):
    """Get overall system health status."""
    try:
        # Check for active disasters
        active_disasters = len(dr_service.active_disasters)
        
        # Get latest backup info
        latest_backup_id = backup_service._get_latest_backup_id()
        latest_backup = None
        if latest_backup_id:
            latest_backup = backup_service.backup_metadata.get(latest_backup_id)
        
        # Check data integrity
        corruption_issues = await backup_service.detect_data_corruption()
        
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_health": "healthy" if active_disasters == 0 and len(corruption_issues) == 0 else "degraded",
            "active_disasters": active_disasters,
            "data_corruption_issues": len(corruption_issues),
            "latest_backup": {
                "backup_id": latest_backup.backup_id if latest_backup else None,
                "timestamp": latest_backup.timestamp.isoformat() if latest_backup else None,
                "status": latest_backup.status.value if latest_backup else None
            } if latest_backup else None,
            "backup_system_operational": True,  # Could add more sophisticated check
            "disaster_recovery_monitoring": dr_service._monitoring_task is not None
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"System health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"System health check failed: {str(e)}")


# Monitoring and Alerting

@router.post("/monitoring/start")
async def start_monitoring(
    dr_service: DisasterRecoveryService = Depends(get_disaster_recovery_service),
    current_user = Depends(get_current_admin_user)
):
    """Start disaster recovery monitoring."""
    try:
        await dr_service.start_monitoring()
        
        return {
            "monitoring_started": True,
            "started_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")


@router.post("/monitoring/stop")
async def stop_monitoring(
    dr_service: DisasterRecoveryService = Depends(get_disaster_recovery_service),
    current_user = Depends(get_current_admin_user)
):
    """Stop disaster recovery monitoring."""
    try:
        await dr_service.stop_monitoring()
        
        return {
            "monitoring_stopped": True,
            "stopped_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to stop monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {str(e)}")