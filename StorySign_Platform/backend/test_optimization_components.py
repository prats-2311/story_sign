#!/usr/bin/env python3
"""
Test database optimization components without requiring a running database
Tests the optimization services in mock mode
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from config import get_config
from core.cache_service import CacheService
from core.database_optimizer import DatabaseOptimizer
from core.monitoring_service import DatabaseMonitoringService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_cache_service():
    """Test cache service functionality"""
    logger.info("Testing Cache Service...")
    
    try:
        cache_service = CacheService()
        await cache_service.initialize()
        
        # Test health check
        health = await cache_service.health_check()
        logger.info(f"Cache service health: {health}")
        
        # Test basic operations (will work in mock mode if Redis not available)
        test_key = "test_optimization"
        test_value = {"test": True, "data": "optimization_test"}
        
        # Test set operation
        set_result = await cache_service.set(test_key, test_value, ttl=60)
        logger.info(f"Cache SET result: {set_result}")
        
        # Test get operation
        get_result = await cache_service.get(test_key)
        logger.info(f"Cache GET result: {get_result}")
        
        # Test exists operation
        exists_result = await cache_service.exists(test_key)
        logger.info(f"Cache EXISTS result: {exists_result}")
        
        # Test delete operation
        delete_result = await cache_service.delete(test_key)
        logger.info(f"Cache DELETE result: {delete_result}")
        
        await cache_service.cleanup()
        return True
        
    except Exception as e:
        logger.error(f"Cache service test failed: {e}")
        return False


async def test_monitoring_service():
    """Test monitoring service functionality"""
    logger.info("Testing Monitoring Service...")
    
    try:
        monitoring_service = DatabaseMonitoringService()
        
        # Test health check (should work without database)
        health = await monitoring_service.health_check()
        logger.info(f"Monitoring service health: {health}")
        
        # Test getting current metrics (will be empty but shouldn't fail)
        metrics = await monitoring_service.get_current_metrics()
        logger.info(f"Current metrics count: {len(metrics)}")
        
        # Test getting active alerts
        alerts = await monitoring_service.get_active_alerts()
        logger.info(f"Active alerts count: {len(alerts)}")
        
        # Test metric history
        history = await monitoring_service.get_metric_history("test_metric", hours=1)
        logger.info(f"Metric history points: {len(history)}")
        
        await monitoring_service.cleanup()
        return True
        
    except Exception as e:
        logger.error(f"Monitoring service test failed: {e}")
        return False


async def test_optimizer_service():
    """Test database optimizer functionality"""
    logger.info("Testing Database Optimizer...")
    
    try:
        optimizer = DatabaseOptimizer()
        
        # Test health check (should work without database)
        health = await optimizer.health_check()
        logger.info(f"Optimizer health: {health}")
        
        # Test getting index recommendations (will be empty but shouldn't fail)
        recommendations = await optimizer.get_index_recommendations()
        logger.info(f"Index recommendations count: {len(recommendations)}")
        
        await optimizer.cleanup()
        return True
        
    except Exception as e:
        logger.error(f"Optimizer test failed: {e}")
        return False


async def test_configuration():
    """Test configuration loading"""
    logger.info("Testing Configuration...")
    
    try:
        config = get_config()
        
        # Test database configuration
        db_config = config.database
        logger.info(f"Database config - Host: {db_config.host}, Port: {db_config.port}")
        logger.info(f"Database config - Pool size: {db_config.pool_size}")
        
        # Test cache configuration
        cache_config = config.cache
        logger.info(f"Cache config - Host: {cache_config.host}, Port: {cache_config.port}")
        logger.info(f"Cache config - Enabled: {cache_config.enabled}")
        
        # Test optimization configuration
        opt_config = config.optimization
        logger.info(f"Optimization config - Monitoring interval: {opt_config.monitoring_interval}")
        logger.info(f"Optimization config - Slow query threshold: {opt_config.slow_query_threshold}")
        
        return True
        
    except Exception as e:
        logger.error(f"Configuration test failed: {e}")
        return False


async def test_api_imports():
    """Test that optimization API can be imported"""
    logger.info("Testing API Imports...")
    
    try:
        # Test importing optimization API
        from api.optimization import router
        logger.info(f"Optimization API router imported successfully: {len(router.routes)} routes")
        
        # Test importing other optimization modules
        from core.cache_service import cache_result
        logger.info("Cache decorator imported successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"API import test failed: {e}")
        return False


async def run_all_tests():
    """Run all optimization component tests"""
    logger.info("Starting Database Optimization Component Tests...")
    
    test_results = {
        "configuration": await test_configuration(),
        "api_imports": await test_api_imports(),
        "cache_service": await test_cache_service(),
        "monitoring_service": await test_monitoring_service(),
        "optimizer_service": await test_optimizer_service()
    }
    
    # Print results
    print("\n" + "="*80)
    print("DATABASE OPTIMIZATION COMPONENT TEST RESULTS")
    print("="*80)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
        if result:
            passed_tests += 1
    
    print(f"\nSummary: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 All optimization components are working correctly!")
        print("\nNext steps:")
        print("1. Set up TiDB cluster: python scripts/setup_tidb_cluster.py --type docker")
        print("2. Run database migrations: python run_migrations.py")
        print("3. Start API server: python main_api.py")
        print("4. Test with database: python test_database_optimization.py")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} tests failed. Check the logs above.")
        return False


async def main():
    """Main test function"""
    try:
        success = await run_all_tests()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())