#!/usr/bin/env python3
"""
Database optimization testing script
Tests database performance under load and validates optimization features
"""

import asyncio
import logging
import time
import random
import statistics
from typing import List, Dict, Any
from datetime import datetime, timedelta

from config import get_config
from core.database_service import DatabaseService
from core.cache_service import CacheService
from core.database_optimizer import DatabaseOptimizer
from core.monitoring_service import DatabaseMonitoringService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabasePerformanceTester:
    """
    Database performance testing suite
    Tests various aspects of database optimization
    """
    
    def __init__(self):
        self.config = get_config()
        self.db_service = None
        self.cache_service = None
        self.optimizer = None
        self.monitoring = None
        
        self.test_results = {}
    
    async def initialize(self):
        """Initialize all services"""
        logger.info("Initializing database performance tester...")
        
        # Initialize services
        self.db_service = DatabaseService()
        await self.db_service.initialize()
        
        self.cache_service = CacheService()
        await self.cache_service.initialize()
        
        self.optimizer = DatabaseOptimizer()
        await self.optimizer.initialize()
        
        self.monitoring = DatabaseMonitoringService()
        await self.monitoring.initialize()
        
        logger.info("All services initialized successfully")
    
    async def cleanup(self):
        """Clean up all services"""
        if self.monitoring:
            await self.monitoring.cleanup()
        if self.optimizer:
            await self.optimizer.cleanup()
        if self.cache_service:
            await self.cache_service.cleanup()
        if self.db_service:
            await self.db_service.cleanup()
    
    async def test_database_connection_performance(self) -> Dict[str, Any]:
        """Test database connection performance"""
        logger.info("Testing database connection performance...")
        
        connection_times = []
        query_times = []
        
        # Test multiple connections
        for i in range(10):
            start_time = time.time()
            
            try:
                async with self.db_service.get_session() as session:
                    connection_time = time.time() - start_time
                    connection_times.append(connection_time)
                    
                    # Test simple query
                    query_start = time.time()
                    await session.execute("SELECT 1 as test")
                    query_time = time.time() - query_start
                    query_times.append(query_time)
                    
            except Exception as e:
                logger.error(f"Connection test {i} failed: {e}")
        
        results = {
            "connection_count": len(connection_times),
            "avg_connection_time": statistics.mean(connection_times) if connection_times else 0,
            "max_connection_time": max(connection_times) if connection_times else 0,
            "min_connection_time": min(connection_times) if connection_times else 0,
            "avg_query_time": statistics.mean(query_times) if query_times else 0,
            "max_query_time": max(query_times) if query_times else 0,
            "min_query_time": min(query_times) if query_times else 0
        }
        
        logger.info(f"Connection performance: {results}")
        return results
    
    async def test_cache_performance(self) -> Dict[str, Any]:
        """Test Redis cache performance"""
        logger.info("Testing cache performance...")
        
        if not self.cache_service.is_connected():
            return {"error": "Cache service not connected"}
        
        # Test cache operations
        set_times = []
        get_times = []
        
        test_data = {
            f"test_key_{i}": f"test_value_{i}" * 100  # Larger values
            for i in range(100)
        }
        
        # Test SET operations
        for key, value in test_data.items():
            start_time = time.time()
            await self.cache_service.set(key, value, ttl=300)
            set_time = time.time() - start_time
            set_times.append(set_time)
        
        # Test GET operations
        for key in test_data.keys():
            start_time = time.time()
            await self.cache_service.get(key)
            get_time = time.time() - start_time
            get_times.append(get_time)
        
        # Test batch operations
        batch_start = time.time()
        await self.cache_service.set_many(test_data, ttl=300)
        batch_set_time = time.time() - batch_start
        
        batch_start = time.time()
        await self.cache_service.get_many(list(test_data.keys()))
        batch_get_time = time.time() - batch_start
        
        # Clean up test data
        for key in test_data.keys():
            await self.cache_service.delete(key)
        
        results = {
            "operations_tested": len(test_data),
            "avg_set_time": statistics.mean(set_times),
            "avg_get_time": statistics.mean(get_times),
            "batch_set_time": batch_set_time,
            "batch_get_time": batch_get_time,
            "cache_health": await self.cache_service.health_check()
        }
        
        logger.info(f"Cache performance: {results}")
        return results
    
    async def test_query_optimization(self) -> Dict[str, Any]:
        """Test query optimization features"""
        logger.info("Testing query optimization...")
        
        # Create test table if it doesn't exist
        await self._create_test_table()
        
        # Insert test data
        await self._insert_test_data(1000)
        
        # Test various query patterns
        query_results = {}
        
        # Test 1: Simple SELECT
        start_time = time.time()
        result = await self.db_service.execute_query(
            "SELECT COUNT(*) as count FROM test_performance",
            fetch_one=True
        )
        query_results["simple_count"] = {
            "time": time.time() - start_time,
            "result": dict(result._mapping) if result else None
        }
        
        # Test 2: WHERE clause without index
        start_time = time.time()
        result = await self.db_service.execute_query(
            "SELECT * FROM test_performance WHERE test_value > %s LIMIT 10",
            {"value": 500},
            fetch_all=True
        )
        query_results["unindexed_where"] = {
            "time": time.time() - start_time,
            "rows": len(result) if result else 0
        }
        
        # Test 3: ORDER BY without index
        start_time = time.time()
        result = await self.db_service.execute_query(
            "SELECT * FROM test_performance ORDER BY test_value DESC LIMIT 10",
            fetch_all=True
        )
        query_results["unindexed_order"] = {
            "time": time.time() - start_time,
            "rows": len(result) if result else 0
        }
        
        # Get optimizer recommendations
        recommendations = await self.optimizer.get_index_recommendations()
        
        results = {
            "query_performance": query_results,
            "index_recommendations": [
                {
                    "table": rec.table_name,
                    "columns": rec.columns,
                    "type": rec.index_type,
                    "benefit": rec.estimated_benefit,
                    "reason": rec.reason
                }
                for rec in recommendations
            ]
        }
        
        logger.info(f"Query optimization results: {results}")
        return results
    
    async def test_concurrent_load(self, concurrent_users: int = 10, operations_per_user: int = 50) -> Dict[str, Any]:
        """Test database performance under concurrent load"""
        logger.info(f"Testing concurrent load: {concurrent_users} users, {operations_per_user} ops each")
        
        async def user_simulation(user_id: int):
            """Simulate a user performing database operations"""
            user_results = {
                "user_id": user_id,
                "operations": 0,
                "errors": 0,
                "total_time": 0,
                "operation_times": []
            }
            
            for op in range(operations_per_user):
                try:
                    start_time = time.time()
                    
                    # Random operation
                    operation_type = random.choice(["read", "write", "cache"])
                    
                    if operation_type == "read":
                        await self.db_service.execute_query(
                            "SELECT * FROM test_performance WHERE id = %s",
                            {"id": random.randint(1, 1000)},
                            fetch_one=True
                        )
                    elif operation_type == "write":
                        await self.db_service.execute_query(
                            "UPDATE test_performance SET test_value = %s WHERE id = %s",
                            {"value": random.randint(1, 1000), "id": random.randint(1, 1000)}
                        )
                    elif operation_type == "cache":
                        if self.cache_service.is_connected():
                            cache_key = f"user_{user_id}_op_{op}"
                            await self.cache_service.set(cache_key, f"data_{random.randint(1, 1000)}")
                            await self.cache_service.get(cache_key)
                    
                    operation_time = time.time() - start_time
                    user_results["operation_times"].append(operation_time)
                    user_results["total_time"] += operation_time
                    user_results["operations"] += 1
                    
                except Exception as e:
                    logger.error(f"User {user_id} operation {op} failed: {e}")
                    user_results["errors"] += 1
            
            return user_results
        
        # Run concurrent user simulations
        start_time = time.time()
        tasks = [user_simulation(i) for i in range(concurrent_users)]
        user_results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Aggregate results
        total_operations = sum(r["operations"] for r in user_results if isinstance(r, dict))
        total_errors = sum(r["errors"] for r in user_results if isinstance(r, dict))
        all_operation_times = []
        for r in user_results:
            if isinstance(r, dict):
                all_operation_times.extend(r["operation_times"])
        
        results = {
            "concurrent_users": concurrent_users,
            "operations_per_user": operations_per_user,
            "total_operations": total_operations,
            "total_errors": total_errors,
            "total_time": total_time,
            "operations_per_second": total_operations / total_time if total_time > 0 else 0,
            "avg_operation_time": statistics.mean(all_operation_times) if all_operation_times else 0,
            "max_operation_time": max(all_operation_times) if all_operation_times else 0,
            "error_rate": (total_errors / (total_operations + total_errors)) * 100 if (total_operations + total_errors) > 0 else 0
        }
        
        logger.info(f"Concurrent load test results: {results}")
        return results
    
    async def test_monitoring_and_alerting(self) -> Dict[str, Any]:
        """Test monitoring and alerting functionality"""
        logger.info("Testing monitoring and alerting...")
        
        # Get current metrics
        current_metrics = await self.monitoring.get_current_metrics()
        
        # Get active alerts
        active_alerts = await self.monitoring.get_active_alerts()
        
        # Get monitoring health
        monitoring_health = await self.monitoring.health_check()
        
        # Test metric history
        if current_metrics:
            metric_name = list(current_metrics.keys())[0]
            metric_history = await self.monitoring.get_metric_history(metric_name, hours=1)
        else:
            metric_history = []
        
        results = {
            "current_metrics_count": len(current_metrics),
            "active_alerts_count": len(active_alerts),
            "monitoring_health": monitoring_health,
            "metric_history_points": len(metric_history),
            "sample_metrics": dict(list(current_metrics.items())[:5]) if current_metrics else {},
            "sample_alerts": active_alerts[:3] if active_alerts else []
        }
        
        logger.info(f"Monitoring test results: {results}")
        return results
    
    async def _create_test_table(self):
        """Create test table for performance testing"""
        try:
            await self.db_service.execute_query("""
                CREATE TABLE IF NOT EXISTS test_performance (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    test_value INT NOT NULL,
                    test_string VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.debug("Test table created successfully")
        except Exception as e:
            logger.error(f"Failed to create test table: {e}")
    
    async def _insert_test_data(self, count: int):
        """Insert test data for performance testing"""
        try:
            # Check if data already exists
            result = await self.db_service.execute_query(
                "SELECT COUNT(*) as count FROM test_performance",
                fetch_one=True
            )
            
            if result and result.count >= count:
                logger.debug(f"Test data already exists ({result.count} rows)")
                return
            
            # Insert test data in batches
            batch_size = 100
            for i in range(0, count, batch_size):
                values = []
                for j in range(min(batch_size, count - i)):
                    values.append(f"({i + j + 1}, 'test_string_{i + j + 1}')")
                
                query = f"""
                    INSERT IGNORE INTO test_performance (test_value, test_string)
                    VALUES {', '.join(values)}
                """
                
                await self.db_service.execute_query(query)
            
            logger.debug(f"Inserted {count} test records")
            
        except Exception as e:
            logger.error(f"Failed to insert test data: {e}")
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all performance tests"""
        logger.info("Starting comprehensive database optimization tests...")
        
        try:
            await self.initialize()
            
            # Run all tests
            self.test_results = {
                "test_timestamp": datetime.now().isoformat(),
                "configuration": {
                    "database_host": self.config.database.host,
                    "database_port": self.config.database.port,
                    "pool_size": self.config.database.pool_size,
                    "cache_enabled": self.config.cache.enabled,
                    "optimization_enabled": self.config.optimization.auto_optimize
                },
                "connection_performance": await self.test_database_connection_performance(),
                "cache_performance": await self.test_cache_performance(),
                "query_optimization": await self.test_query_optimization(),
                "concurrent_load": await self.test_concurrent_load(),
                "monitoring": await self.test_monitoring_and_alerting()
            }
            
            # Generate summary
            self.test_results["summary"] = self._generate_test_summary()
            
            logger.info("All tests completed successfully")
            return self.test_results
            
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return {"error": str(e)}
        
        finally:
            await self.cleanup()
    
    def _generate_test_summary(self) -> Dict[str, Any]:
        """Generate test summary and recommendations"""
        summary = {
            "overall_status": "healthy",
            "recommendations": [],
            "performance_score": 100
        }
        
        # Analyze connection performance
        conn_perf = self.test_results.get("connection_performance", {})
        if conn_perf.get("avg_connection_time", 0) > 0.1:
            summary["recommendations"].append("Consider increasing connection pool size")
            summary["performance_score"] -= 10
        
        # Analyze cache performance
        cache_perf = self.test_results.get("cache_performance", {})
        if "error" in cache_perf:
            summary["recommendations"].append("Enable Redis caching for better performance")
            summary["performance_score"] -= 20
        
        # Analyze concurrent load
        load_perf = self.test_results.get("concurrent_load", {})
        if load_perf.get("error_rate", 0) > 5:
            summary["recommendations"].append("High error rate under load - check database configuration")
            summary["performance_score"] -= 30
            summary["overall_status"] = "degraded"
        
        if load_perf.get("avg_operation_time", 0) > 1.0:
            summary["recommendations"].append("Slow query performance - consider adding indexes")
            summary["performance_score"] -= 15
        
        # Analyze monitoring
        monitoring = self.test_results.get("monitoring", {})
        if not monitoring.get("monitoring_health", {}).get("monitoring_active", False):
            summary["recommendations"].append("Enable database monitoring for better observability")
            summary["performance_score"] -= 10
        
        return summary


async def main():
    """Main test execution function"""
    tester = DatabasePerformanceTester()
    
    try:
        results = await tester.run_all_tests()
        
        # Print results
        print("\n" + "="*80)
        print("DATABASE OPTIMIZATION TEST RESULTS")
        print("="*80)
        
        if "error" in results:
            print(f"ERROR: {results['error']}")
            return
        
        # Print summary
        summary = results.get("summary", {})
        print(f"\nOverall Status: {summary.get('overall_status', 'unknown').upper()}")
        print(f"Performance Score: {summary.get('performance_score', 0)}/100")
        
        if summary.get("recommendations"):
            print("\nRecommendations:")
            for i, rec in enumerate(summary["recommendations"], 1):
                print(f"  {i}. {rec}")
        
        # Print detailed results
        print(f"\nConnection Performance:")
        conn = results.get("connection_performance", {})
        print(f"  Average connection time: {conn.get('avg_connection_time', 0):.4f}s")
        print(f"  Average query time: {conn.get('avg_query_time', 0):.4f}s")
        
        print(f"\nCache Performance:")
        cache = results.get("cache_performance", {})
        if "error" in cache:
            print(f"  Error: {cache['error']}")
        else:
            print(f"  Average SET time: {cache.get('avg_set_time', 0):.4f}s")
            print(f"  Average GET time: {cache.get('avg_get_time', 0):.4f}s")
        
        print(f"\nConcurrent Load Test:")
        load = results.get("concurrent_load", {})
        print(f"  Operations per second: {load.get('operations_per_second', 0):.2f}")
        print(f"  Error rate: {load.get('error_rate', 0):.2f}%")
        print(f"  Average operation time: {load.get('avg_operation_time', 0):.4f}s")
        
        print(f"\nMonitoring Status:")
        monitoring = results.get("monitoring", {})
        health = monitoring.get("monitoring_health", {})
        print(f"  Status: {health.get('status', 'unknown')}")
        print(f"  Active alerts: {monitoring.get('active_alerts_count', 0)}")
        print(f"  Metrics collected: {monitoring.get('current_metrics_count', 0)}")
        
        print("\n" + "="*80)
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        logger.exception("Test execution failed")


if __name__ == "__main__":
    asyncio.run(main())