"""
Database optimization API endpoints
Provides REST API for database performance monitoring and optimization
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any, List, Optional
import logging

from core.database_optimizer import get_database_optimizer, DatabaseOptimizer
from core.monitoring_service import get_monitoring_service, DatabaseMonitoringService
from core.cache_service import get_cache_service, CacheService

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_optimizer() -> DatabaseOptimizer:
    """Dependency to get database optimizer"""
    try:
        return await get_database_optimizer()
    except Exception as e:
        logger.error(f"Failed to get database optimizer: {e}")
        raise HTTPException(status_code=503, detail="Database optimizer service unavailable")


async def get_monitoring() -> DatabaseMonitoringService:
    """Dependency to get monitoring service"""
    try:
        return await get_monitoring_service()
    except Exception as e:
        logger.error(f"Failed to get monitoring service: {e}")
        raise HTTPException(status_code=503, detail="Monitoring service unavailable")


async def get_cache() -> CacheService:
    """Dependency to get cache service"""
    try:
        return await get_cache_service()
    except Exception as e:
        logger.error(f"Failed to get cache service: {e}")
        raise HTTPException(status_code=503, detail="Cache service unavailable")


@router.get("/health")
async def get_optimization_health(
    optimizer: DatabaseOptimizer = Depends(get_optimizer),
    monitoring: DatabaseMonitoringService = Depends(get_monitoring),
    cache: CacheService = Depends(get_cache)
) -> Dict[str, Any]:
    """
    Get health status of all optimization services
    """
    try:
        return {
            "optimizer": await optimizer.health_check(),
            "monitoring": await monitoring.health_check(),
            "cache": await cache.health_check()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/report")
async def get_performance_report(
    optimizer: DatabaseOptimizer = Depends(get_optimizer)
) -> Dict[str, Any]:
    """
    Get comprehensive query performance report
    """
    try:
        return await optimizer.get_query_performance_report()
    except Exception as e:
        logger.error(f"Failed to get performance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/tables")
async def get_table_analysis(
    optimizer: DatabaseOptimizer = Depends(get_optimizer)
) -> Dict[str, Any]:
    """
    Get table usage analysis and statistics
    """
    try:
        return await optimizer.analyze_table_usage()
    except Exception as e:
        logger.error(f"Failed to analyze table usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/indexes")
async def get_index_recommendations(
    optimizer: DatabaseOptimizer = Depends(get_optimizer)
) -> List[Dict[str, Any]]:
    """
    Get index recommendations for performance optimization
    """
    try:
        recommendations = await optimizer.get_index_recommendations()
        return [
            {
                "table_name": rec.table_name,
                "columns": rec.columns,
                "index_type": rec.index_type,
                "estimated_benefit": rec.estimated_benefit,
                "reason": rec.reason
            }
            for rec in recommendations
        ]
    except Exception as e:
        logger.error(f"Failed to get index recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/performance/optimize/{table_name}")
async def optimize_table(
    table_name: str,
    optimizer: DatabaseOptimizer = Depends(get_optimizer)
) -> Dict[str, Any]:
    """
    Optimize indexes for a specific table
    """
    try:
        return await optimizer.optimize_table_indexes(table_name)
    except Exception as e:
        logger.error(f"Failed to optimize table {table_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cluster/status")
async def get_cluster_status(
    optimizer: DatabaseOptimizer = Depends(get_optimizer)
) -> Dict[str, Any]:
    """
    Get TiDB cluster status and health information
    """
    try:
        return await optimizer.get_tidb_cluster_status()
    except Exception as e:
        logger.error(f"Failed to get cluster status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/metrics")
async def get_current_metrics(
    monitoring: DatabaseMonitoringService = Depends(get_monitoring)
) -> Dict[str, Any]:
    """
    Get current performance metrics
    """
    try:
        return await monitoring.get_current_metrics()
    except Exception as e:
        logger.error(f"Failed to get current metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/metrics/{metric_name}/history")
async def get_metric_history(
    metric_name: str,
    hours: int = 1,
    monitoring: DatabaseMonitoringService = Depends(get_monitoring)
) -> List[Dict[str, Any]]:
    """
    Get historical data for a specific metric
    """
    try:
        if hours < 1 or hours > 168:  # Max 1 week
            raise HTTPException(status_code=400, detail="Hours must be between 1 and 168")
        
        return await monitoring.get_metric_history(metric_name, hours)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metric history for {metric_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring/alerts")
async def get_active_alerts(
    monitoring: DatabaseMonitoringService = Depends(get_monitoring)
) -> List[Dict[str, Any]]:
    """
    Get all active alerts
    """
    try:
        return await monitoring.get_active_alerts()
    except Exception as e:
        logger.error(f"Failed to get active alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def get_cache_stats(
    cache: CacheService = Depends(get_cache)
) -> Dict[str, Any]:
    """
    Get cache statistics and health information
    """
    try:
        return await cache.health_check()
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_cache_pattern(
    pattern: str = "*",
    cache: CacheService = Depends(get_cache)
) -> Dict[str, Any]:
    """
    Clear cache keys matching pattern
    """
    try:
        if not pattern:
            raise HTTPException(status_code=400, detail="Pattern cannot be empty")
        
        deleted_count = await cache.clear_pattern(pattern)
        return {
            "pattern": pattern,
            "deleted_keys": deleted_count,
            "message": f"Cleared {deleted_count} cache keys matching pattern '{pattern}'"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear cache pattern {pattern}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/test")
async def test_cache_operations(
    cache: CacheService = Depends(get_cache)
) -> Dict[str, Any]:
    """
    Test cache operations for performance validation
    """
    try:
        import time
        
        # Test basic operations
        test_key = "optimization_test"
        test_value = {"test": True, "timestamp": time.time()}
        
        # Test SET
        set_start = time.time()
        set_result = await cache.set(test_key, test_value, ttl=60)
        set_time = time.time() - set_start
        
        # Test GET
        get_start = time.time()
        get_result = await cache.get(test_key)
        get_time = time.time() - get_start
        
        # Test EXISTS
        exists_start = time.time()
        exists_result = await cache.exists(test_key)
        exists_time = time.time() - exists_start
        
        # Test DELETE
        delete_start = time.time()
        delete_result = await cache.delete(test_key)
        delete_time = time.time() - delete_start
        
        return {
            "operations": {
                "set": {"success": set_result, "time_seconds": set_time},
                "get": {"success": get_result == test_value, "time_seconds": get_time},
                "exists": {"success": exists_result, "time_seconds": exists_time},
                "delete": {"success": delete_result, "time_seconds": delete_time}
            },
            "total_time": set_time + get_time + exists_time + delete_time,
            "cache_available": cache.is_connected()
        }
    except Exception as e:
        logger.error(f"Cache test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/performance/test")
async def run_performance_test(
    background_tasks: BackgroundTasks,
    concurrent_users: int = 10,
    operations_per_user: int = 50
) -> Dict[str, Any]:
    """
    Run comprehensive performance test in background
    """
    try:
        if concurrent_users < 1 or concurrent_users > 100:
            raise HTTPException(status_code=400, detail="Concurrent users must be between 1 and 100")
        
        if operations_per_user < 1 or operations_per_user > 1000:
            raise HTTPException(status_code=400, detail="Operations per user must be between 1 and 1000")
        
        # Start performance test in background
        async def run_test():
            try:
                from test_database_optimization import DatabasePerformanceTester
                tester = DatabasePerformanceTester()
                results = await tester.run_all_tests()
                logger.info(f"Performance test completed: {results.get('summary', {})}")
            except Exception as e:
                logger.error(f"Background performance test failed: {e}")
        
        background_tasks.add_task(run_test)
        
        return {
            "message": "Performance test started in background",
            "parameters": {
                "concurrent_users": concurrent_users,
                "operations_per_user": operations_per_user
            },
            "note": "Check logs for test results"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start performance test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_optimization_dashboard(
    optimizer: DatabaseOptimizer = Depends(get_optimizer),
    monitoring: DatabaseMonitoringService = Depends(get_monitoring),
    cache: CacheService = Depends(get_cache)
) -> Dict[str, Any]:
    """
    Get comprehensive optimization dashboard data
    """
    try:
        # Gather all dashboard data
        dashboard_data = {
            "timestamp": "2025-01-27T00:00:00Z",  # Current timestamp would be added
            "services": {
                "optimizer": await optimizer.health_check(),
                "monitoring": await monitoring.health_check(),
                "cache": await cache.health_check()
            },
            "performance": await optimizer.get_query_performance_report(),
            "metrics": await monitoring.get_current_metrics(),
            "alerts": await monitoring.get_active_alerts(),
            "recommendations": []
        }
        
        # Get index recommendations
        try:
            recommendations = await optimizer.get_index_recommendations()
            dashboard_data["recommendations"] = [
                {
                    "type": "index",
                    "table": rec.table_name,
                    "columns": rec.columns,
                    "benefit": rec.estimated_benefit,
                    "reason": rec.reason
                }
                for rec in recommendations[:5]  # Top 5 recommendations
            ]
        except Exception as e:
            logger.warning(f"Failed to get recommendations: {e}")
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))