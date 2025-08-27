"""
Database optimization service for TiDB
Provides query optimization, indexing, and performance monitoring
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from sqlalchemy import text, Index
from sqlalchemy.ext.asyncio import AsyncSession

from .base_service import BaseService
from .database_service import DatabaseService


@dataclass
class QueryPerformanceMetric:
    """Query performance metric data"""
    query_hash: str
    query_text: str
    execution_count: int
    avg_execution_time: float
    max_execution_time: float
    total_execution_time: float
    last_executed: datetime


@dataclass
class IndexRecommendation:
    """Index recommendation data"""
    table_name: str
    columns: List[str]
    index_type: str
    estimated_benefit: float
    reason: str


class DatabaseOptimizer(BaseService):
    """
    Database optimization service for TiDB performance tuning
    Provides query analysis, index recommendations, and performance monitoring
    """
    
    def __init__(self, service_name: str = "DatabaseOptimizer", config: Optional[Dict[str, Any]] = None):
        super().__init__(service_name, config)
        self.db_service: Optional[DatabaseService] = None
        self._monitoring_task: Optional[asyncio.Task] = None
        self._query_metrics: Dict[str, QueryPerformanceMetric] = {}
        
        # Configuration
        self.monitoring_interval = 300  # 5 minutes
        self.slow_query_threshold = 1.0  # 1 second
        self.max_metrics_history = 1000
        
        if self.config:
            opt_config = self.config.get("optimizer", {})
            self.monitoring_interval = opt_config.get("monitoring_interval", 300)
            self.slow_query_threshold = opt_config.get("slow_query_threshold", 1.0)
            self.max_metrics_history = opt_config.get("max_metrics_history", 1000)
    
    async def initialize(self) -> None:
        """Initialize database optimizer"""
        try:
            # Get database service
            from .service_container import get_service
            self.db_service = get_service("DatabaseService")
            
            if not self.db_service:
                raise RuntimeError("DatabaseService not available")
            
            # Start monitoring task
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            self.logger.info("Database optimizer initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database optimizer: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up optimizer resources"""
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Database optimizer cleaned up")
    
    async def _monitoring_loop(self) -> None:
        """Background monitoring loop for query performance"""
        while True:
            try:
                await asyncio.sleep(self.monitoring_interval)
                await self._collect_performance_metrics()
                await self._analyze_slow_queries()
                
            except asyncio.CancelledError:
                self.logger.debug("Monitoring loop cancelled")
                break
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
    
    async def _collect_performance_metrics(self) -> None:
        """Collect query performance metrics from TiDB"""
        if not self.db_service or not self.db_service.is_connected():
            return
        
        try:
            # Query TiDB's performance schema for slow queries
            query = """
            SELECT 
                DIGEST_TEXT as query_text,
                DIGEST as query_hash,
                COUNT_STAR as execution_count,
                AVG_TIMER_WAIT / 1000000000 as avg_execution_time,
                MAX_TIMER_WAIT / 1000000000 as max_execution_time,
                SUM_TIMER_WAIT / 1000000000 as total_execution_time,
                LAST_SEEN as last_executed
            FROM performance_schema.events_statements_summary_by_digest
            WHERE DIGEST_TEXT IS NOT NULL
            AND AVG_TIMER_WAIT / 1000000000 > %s
            ORDER BY AVG_TIMER_WAIT DESC
            LIMIT 100
            """
            
            async with self.db_service.get_session() as session:
                result = await session.execute(
                    text(query),
                    {"slow_threshold": self.slow_query_threshold}
                )
                
                rows = result.fetchall()
                
                for row in rows:
                    metric = QueryPerformanceMetric(
                        query_hash=row.query_hash,
                        query_text=row.query_text[:500],  # Truncate long queries
                        execution_count=row.execution_count,
                        avg_execution_time=row.avg_execution_time,
                        max_execution_time=row.max_execution_time,
                        total_execution_time=row.total_execution_time,
                        last_executed=row.last_executed
                    )
                    
                    self._query_metrics[row.query_hash] = metric
                
                # Limit metrics history
                if len(self._query_metrics) > self.max_metrics_history:
                    # Remove oldest metrics
                    sorted_metrics = sorted(
                        self._query_metrics.items(),
                        key=lambda x: x[1].last_executed
                    )
                    
                    for query_hash, _ in sorted_metrics[:-self.max_metrics_history]:
                        del self._query_metrics[query_hash]
                
                self.logger.debug(f"Collected {len(rows)} query performance metrics")
                
        except Exception as e:
            self.logger.error(f"Failed to collect performance metrics: {e}")
    
    async def _analyze_slow_queries(self) -> None:
        """Analyze slow queries and generate recommendations"""
        try:
            slow_queries = [
                metric for metric in self._query_metrics.values()
                if metric.avg_execution_time > self.slow_query_threshold
            ]
            
            if slow_queries:
                self.logger.info(f"Found {len(slow_queries)} slow queries")
                
                # Log top 5 slowest queries
                sorted_slow = sorted(slow_queries, key=lambda x: x.avg_execution_time, reverse=True)
                for i, query in enumerate(sorted_slow[:5]):
                    self.logger.warning(
                        f"Slow query #{i+1}: {query.avg_execution_time:.3f}s avg, "
                        f"{query.execution_count} executions - {query.query_text[:100]}..."
                    )
            
        except Exception as e:
            self.logger.error(f"Failed to analyze slow queries: {e}")
    
    async def get_query_performance_report(self) -> Dict[str, Any]:
        """
        Get comprehensive query performance report
        
        Returns:
            Performance report with metrics and recommendations
        """
        try:
            # Calculate summary statistics
            total_queries = len(self._query_metrics)
            slow_queries = [
                m for m in self._query_metrics.values()
                if m.avg_execution_time > self.slow_query_threshold
            ]
            
            avg_execution_time = (
                sum(m.avg_execution_time for m in self._query_metrics.values()) / total_queries
                if total_queries > 0 else 0
            )
            
            # Get top slow queries
            top_slow_queries = sorted(
                self._query_metrics.values(),
                key=lambda x: x.avg_execution_time,
                reverse=True
            )[:10]
            
            # Get most frequent queries
            top_frequent_queries = sorted(
                self._query_metrics.values(),
                key=lambda x: x.execution_count,
                reverse=True
            )[:10]
            
            return {
                "summary": {
                    "total_queries_monitored": total_queries,
                    "slow_queries_count": len(slow_queries),
                    "avg_execution_time": avg_execution_time,
                    "slow_query_threshold": self.slow_query_threshold
                },
                "top_slow_queries": [
                    {
                        "query_hash": q.query_hash,
                        "query_text": q.query_text,
                        "avg_execution_time": q.avg_execution_time,
                        "execution_count": q.execution_count,
                        "last_executed": q.last_executed.isoformat()
                    }
                    for q in top_slow_queries
                ],
                "top_frequent_queries": [
                    {
                        "query_hash": q.query_hash,
                        "query_text": q.query_text,
                        "execution_count": q.execution_count,
                        "avg_execution_time": q.avg_execution_time,
                        "last_executed": q.last_executed.isoformat()
                    }
                    for q in top_frequent_queries
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate performance report: {e}")
            return {"error": str(e)}
    
    async def analyze_table_usage(self) -> Dict[str, Any]:
        """
        Analyze table usage patterns for optimization recommendations
        
        Returns:
            Table usage analysis with recommendations
        """
        if not self.db_service or not self.db_service.is_connected():
            return {"error": "Database service not available"}
        
        try:
            # Get table statistics from information_schema
            query = """
            SELECT 
                TABLE_SCHEMA,
                TABLE_NAME,
                TABLE_ROWS,
                DATA_LENGTH,
                INDEX_LENGTH,
                AUTO_INCREMENT,
                CREATE_TIME,
                UPDATE_TIME
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_TYPE = 'BASE TABLE'
            ORDER BY DATA_LENGTH DESC
            """
            
            async with self.db_service.get_session() as session:
                result = await session.execute(text(query))
                tables = result.fetchall()
                
                table_stats = []
                for table in tables:
                    stats = {
                        "schema": table.TABLE_SCHEMA,
                        "name": table.TABLE_NAME,
                        "rows": table.TABLE_ROWS or 0,
                        "data_size_bytes": table.DATA_LENGTH or 0,
                        "index_size_bytes": table.INDEX_LENGTH or 0,
                        "auto_increment": table.AUTO_INCREMENT,
                        "created": table.CREATE_TIME.isoformat() if table.CREATE_TIME else None,
                        "updated": table.UPDATE_TIME.isoformat() if table.UPDATE_TIME else None
                    }
                    
                    # Calculate size ratios
                    total_size = stats["data_size_bytes"] + stats["index_size_bytes"]
                    if total_size > 0:
                        stats["index_ratio"] = stats["index_size_bytes"] / total_size
                    else:
                        stats["index_ratio"] = 0
                    
                    table_stats.append(stats)
                
                return {
                    "tables": table_stats,
                    "total_tables": len(table_stats),
                    "total_data_size": sum(t["data_size_bytes"] for t in table_stats),
                    "total_index_size": sum(t["index_size_bytes"] for t in table_stats)
                }
                
        except Exception as e:
            self.logger.error(f"Failed to analyze table usage: {e}")
            return {"error": str(e)}
    
    async def get_index_recommendations(self) -> List[IndexRecommendation]:
        """
        Generate index recommendations based on query patterns
        
        Returns:
            List of index recommendations
        """
        recommendations = []
        
        try:
            # Analyze query patterns for missing indexes
            for metric in self._query_metrics.values():
                if metric.avg_execution_time > self.slow_query_threshold:
                    # Simple heuristic: look for WHERE clauses without indexes
                    query_text = metric.query_text.upper()
                    
                    # Look for common patterns that might benefit from indexes
                    if "WHERE" in query_text and "INDEX" not in query_text:
                        # This is a simplified analysis - in production, you'd want
                        # more sophisticated query parsing
                        if "USER_ID" in query_text:
                            recommendations.append(IndexRecommendation(
                                table_name="inferred_from_query",
                                columns=["user_id"],
                                index_type="BTREE",
                                estimated_benefit=metric.avg_execution_time * 0.5,
                                reason=f"Frequent WHERE clause on user_id (avg: {metric.avg_execution_time:.3f}s)"
                            ))
                        
                        if "CREATED_AT" in query_text or "TIMESTAMP" in query_text:
                            recommendations.append(IndexRecommendation(
                                table_name="inferred_from_query",
                                columns=["created_at"],
                                index_type="BTREE",
                                estimated_benefit=metric.avg_execution_time * 0.3,
                                reason=f"Frequent date/time filtering (avg: {metric.avg_execution_time:.3f}s)"
                            ))
            
            # Remove duplicates
            unique_recommendations = {}
            for rec in recommendations:
                key = f"{rec.table_name}:{':'.join(rec.columns)}"
                if key not in unique_recommendations or rec.estimated_benefit > unique_recommendations[key].estimated_benefit:
                    unique_recommendations[key] = rec
            
            return list(unique_recommendations.values())
            
        except Exception as e:
            self.logger.error(f"Failed to generate index recommendations: {e}")
            return []
    
    async def optimize_table_indexes(self, table_name: str) -> Dict[str, Any]:
        """
        Optimize indexes for a specific table
        
        Args:
            table_name: Name of table to optimize
            
        Returns:
            Optimization results
        """
        if not self.db_service or not self.db_service.is_connected():
            return {"error": "Database service not available"}
        
        try:
            # Get current indexes
            query = """
            SELECT 
                INDEX_NAME,
                COLUMN_NAME,
                SEQ_IN_INDEX,
                NON_UNIQUE,
                INDEX_TYPE
            FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = %s
            ORDER BY INDEX_NAME, SEQ_IN_INDEX
            """
            
            async with self.db_service.get_session() as session:
                result = await session.execute(text(query), {"table_name": table_name})
                indexes = result.fetchall()
                
                index_info = {}
                for idx in indexes:
                    if idx.INDEX_NAME not in index_info:
                        index_info[idx.INDEX_NAME] = {
                            "columns": [],
                            "unique": not idx.NON_UNIQUE,
                            "type": idx.INDEX_TYPE
                        }
                    index_info[idx.INDEX_NAME]["columns"].append(idx.COLUMN_NAME)
                
                return {
                    "table_name": table_name,
                    "current_indexes": index_info,
                    "recommendations": await self.get_index_recommendations()
                }
                
        except Exception as e:
            self.logger.error(f"Failed to optimize table indexes for {table_name}: {e}")
            return {"error": str(e)}
    
    async def get_tidb_cluster_status(self) -> Dict[str, Any]:
        """
        Get TiDB cluster status and health information
        
        Returns:
            Cluster status information
        """
        if not self.db_service or not self.db_service.is_connected():
            return {"error": "Database service not available"}
        
        try:
            # Get TiDB cluster information
            queries = {
                "tidb_servers": "SELECT * FROM information_schema.CLUSTER_INFO WHERE TYPE = 'tidb'",
                "tikv_stores": "SELECT * FROM information_schema.CLUSTER_INFO WHERE TYPE = 'tikv'",
                "pd_servers": "SELECT * FROM information_schema.CLUSTER_INFO WHERE TYPE = 'pd'",
                "cluster_config": "SELECT * FROM information_schema.CLUSTER_CONFIG LIMIT 10"
            }
            
            results = {}
            
            async with self.db_service.get_session() as session:
                for name, query in queries.items():
                    try:
                        result = await session.execute(text(query))
                        rows = result.fetchall()
                        results[name] = [dict(row._mapping) for row in rows]
                    except Exception as e:
                        results[name] = {"error": str(e)}
                
                # Get basic cluster metrics
                try:
                    metrics_query = """
                    SELECT 
                        COUNT(*) as total_connections
                    FROM information_schema.PROCESSLIST
                    """
                    result = await session.execute(text(metrics_query))
                    row = result.fetchone()
                    results["metrics"] = {"total_connections": row.total_connections if row else 0}
                except Exception as e:
                    results["metrics"] = {"error": str(e)}
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to get TiDB cluster status: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform database optimizer health check
        
        Returns:
            Health check results
        """
        try:
            status = {
                "status": "healthy",
                "monitoring_active": self._monitoring_task is not None and not self._monitoring_task.done(),
                "metrics_collected": len(self._query_metrics),
                "slow_queries": len([
                    m for m in self._query_metrics.values()
                    if m.avg_execution_time > self.slow_query_threshold
                ]),
                "database_connected": self.db_service.is_connected() if self.db_service else False
            }
            
            if not status["database_connected"]:
                status["status"] = "degraded"
                status["warning"] = "Database service not connected"
            
            return status
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Global optimizer instance
_optimizer: Optional[DatabaseOptimizer] = None


async def get_database_optimizer(config: Optional[Dict[str, Any]] = None) -> DatabaseOptimizer:
    """
    Get or create global database optimizer instance
    
    Args:
        config: Optional optimizer configuration
        
    Returns:
        DatabaseOptimizer instance
    """
    global _optimizer
    
    if _optimizer is None:
        _optimizer = DatabaseOptimizer(config=config)
        await _optimizer.initialize()
    
    return _optimizer


async def cleanup_database_optimizer() -> None:
    """Clean up global database optimizer"""
    global _optimizer
    
    if _optimizer:
        await _optimizer.cleanup()
        _optimizer = None