"""
Monitoring and observability API endpoints
Provides comprehensive system monitoring, alerting, and health check capabilities
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio
import logging

from core.monitoring_service import get_monitoring_service, DatabaseMonitoringService
from core.database_service import get_database_service
from middleware.auth_middleware import get_current_user
from models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def system_health_check():
    """
    Comprehensive system health check
    Returns overall system status and component health
    """
    try:
        monitoring_service = await get_monitoring_service()
        db_service = await get_database_service()
        
        # Get monitoring service health
        monitoring_health = await monitoring_service.health_check()
        
        # Get database health
        db_health = await db_service.health_check()
        
        # Get current metrics
        current_metrics = await monitoring_service.get_current_metrics()
        
        # Get active alerts
        active_alerts = await monitoring_service.get_active_alerts()
        
        # Determine overall status
        overall_status = "healthy"
        if db_health.get("status") != "healthy":
            overall_status = "unhealthy"
        elif len(active_alerts) > 0:
            critical_alerts = [a for a in active_alerts if a["severity"] == "critical"]
            if critical_alerts:
                overall_status = "critical"
            else:
                overall_status = "warning"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "components": {
                "database": db_health,
                "monitoring": monitoring_health
            },
            "metrics_summary": {
                "total_metrics": len(current_metrics),
                "active_alerts": len(active_alerts),
                "critical_alerts": len([a for a in active_alerts if a["severity"] == "critical"])
            },
            "current_metrics": current_metrics
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/metrics")
async def get_current_metrics(
    current_user: User = Depends(get_current_user)
):
    """
    Get current system metrics
    Requires admin privileges
    """
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        monitoring_service = await get_monitoring_service()
        metrics = await monitoring_service.get_current_metrics()
        
        return {
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/metrics/{metric_name}/history")
async def get_metric_history(
    metric_name: str,
    hours: int = Query(default=1, ge=1, le=168),  # 1 hour to 1 week
    current_user: User = Depends(get_current_user)
):
    """
    Get historical data for a specific metric
    """
    try:
        if current_user.role not in ["admin", "researcher"]:
            raise HTTPException(status_code=403, detail="Admin or researcher access required")
        
        monitoring_service = await get_monitoring_service()
        history = await monitoring_service.get_metric_history(metric_name, hours)
        
        return {
            "metric_name": metric_name,
            "hours": hours,
            "data_points": len(history),
            "history": history
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metric history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metric history: {str(e)}")


@router.get("/alerts")
async def get_active_alerts(
    current_user: User = Depends(get_current_user)
):
    """
    Get all active system alerts
    """
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        monitoring_service = await get_monitoring_service()
        alerts = await monitoring_service.get_active_alerts()
        
        return {
            "alerts": alerts,
            "total_count": len(alerts),
            "by_severity": {
                "critical": len([a for a in alerts if a["severity"] == "critical"]),
                "error": len([a for a in alerts if a["severity"] == "error"]),
                "warning": len([a for a in alerts if a["severity"] == "warning"]),
                "info": len([a for a in alerts if a["severity"] == "info"])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Acknowledge an alert (mark as seen by admin)
    """
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # This would typically update the alert status in the database
        # For now, we'll just log the acknowledgment
        logger.info(f"Alert {alert_id} acknowledged by user {current_user.id}")
        
        return {
            "message": f"Alert {alert_id} acknowledged",
            "acknowledged_by": current_user.id,
            "acknowledged_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge alert: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")


@router.get("/performance")
async def get_performance_summary(
    hours: int = Query(default=24, ge=1, le=168),
    current_user: User = Depends(get_current_user)
):
    """
    Get performance summary and trends
    """
    try:
        if current_user.role not in ["admin", "researcher"]:
            raise HTTPException(status_code=403, detail="Admin or researcher access required")
        
        monitoring_service = await get_monitoring_service()
        
        # Get key performance metrics
        key_metrics = [
            "query_response_time",
            "cpu_usage_percent",
            "memory_usage_percent",
            "connection_count",
            "error_rate_percent"
        ]
        
        performance_data = {}
        for metric in key_metrics:
            history = await monitoring_service.get_metric_history(metric, hours)
            if history:
                values = [point["value"] for point in history]
                performance_data[metric] = {
                    "current": values[-1] if values else 0,
                    "average": sum(values) / len(values) if values else 0,
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0,
                    "trend": "stable"  # Would calculate actual trend
                }
        
        return {
            "period_hours": hours,
            "performance_metrics": performance_data,
            "summary": {
                "overall_health": "good",  # Would calculate based on metrics
                "performance_score": 85,   # Would calculate composite score
                "recommendations": []      # Would generate based on analysis
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get performance summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance summary: {str(e)}")


@router.post("/maintenance/database-check")
async def run_database_integrity_check(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Run database integrity check
    """
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Add background task for database check
        background_tasks.add_task(perform_database_integrity_check)
        
        return {
            "message": "Database integrity check started",
            "started_by": current_user.id,
            "started_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start database check: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start database check: {str(e)}")


@router.get("/logs")
async def get_system_logs(
    level: str = Query(default="ERROR", regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"),
    hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """
    Get system logs with filtering
    """
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # This would typically read from log files or log aggregation system
        # For now, return a placeholder response
        return {
            "logs": [],
            "filters": {
                "level": level,
                "hours": hours,
                "limit": limit
            },
            "message": "Log retrieval not implemented - would integrate with logging system"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get logs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")


async def perform_database_integrity_check():
    """
    Background task to perform database integrity check
    """
    try:
        logger.info("Starting database integrity check")
        
        db_service = await get_database_service()
        
        # Perform various integrity checks
        async with db_service.get_session() as session:
            # Check for orphaned records
            orphaned_sessions = await session.execute("""
                SELECT COUNT(*) as count
                FROM practice_sessions ps
                LEFT JOIN users u ON ps.user_id = u.id
                WHERE u.id IS NULL
            """)
            
            orphaned_attempts = await session.execute("""
                SELECT COUNT(*) as count
                FROM sentence_attempts sa
                LEFT JOIN practice_sessions ps ON sa.session_id = ps.id
                WHERE ps.id IS NULL
            """)
            
            # Check for data consistency
            inconsistent_progress = await session.execute("""
                SELECT COUNT(*) as count
                FROM user_progress up
                WHERE up.current_level < 0 OR up.current_level > 100
            """)
            
            results = {
                "orphaned_sessions": orphaned_sessions.fetchone().count,
                "orphaned_attempts": orphaned_attempts.fetchone().count,
                "inconsistent_progress": inconsistent_progress.fetchone().count
            }
            
            logger.info(f"Database integrity check completed: {results}")
            
            # If issues found, create alerts
            monitoring_service = await get_monitoring_service()
            total_issues = sum(results.values())
            
            if total_issues > 0:
                # Would create alert for data integrity issues
                logger.warning(f"Database integrity issues found: {total_issues} total issues")
        
    except Exception as e:
        logger.error(f"Database integrity check failed: {e}")