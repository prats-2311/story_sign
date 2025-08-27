#!/usr/bin/env python3
"""
WebSocket Connection Pool Manager
Optimizes WebSocket connections for high-throughput real-time performance
"""

import asyncio
import logging
import time
import weakref
from typing import Dict, List, Optional, Set, Callable, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
from datetime import datetime, timedelta
import json
import uuid

from fastapi import WebSocket, WebSocketDisconnect


@dataclass
class ConnectionMetrics:
    """Metrics for a WebSocket connection"""
    client_id: str
    connected_at: datetime
    last_activity: datetime
    messages_sent: int = 0
    messages_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    errors: int = 0
    latency_samples: deque = field(default_factory=lambda: deque(maxlen=100))
    
    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency in milliseconds"""
        if not self.latency_samples:
            return 0.0
        return sum(self.latency_samples) / len(self.latency_samples)
    
    @property
    def connection_duration(self) -> timedelta:
        """Get connection duration"""
        return datetime.now() - self.connected_at


@dataclass
class PoolStats:
    """Connection pool statistics"""
    total_connections: int = 0
    active_connections: int = 0
    peak_connections: int = 0
    total_messages_sent: int = 0
    total_messages_received: int = 0
    total_bytes_sent: int = 0
    total_bytes_received: int = 0
    avg_latency_ms: float = 0.0
    error_rate: float = 0.0
    uptime_seconds: float = 0.0


class WebSocketConnectionPool:
    """
    High-performance WebSocket connection pool with optimizations for real-time video streaming
    
    Features:
    - Connection pooling and reuse
    - Automatic load balancing
    - Health monitoring and auto-recovery
    - Message queuing and batching
    - Performance metrics and monitoring
    """
    
    def __init__(self, max_connections: int = 1000, max_queue_size: int = 10000):
        self.logger = logging.getLogger(f"{__name__}.WebSocketConnectionPool")
        
        # Pool configuration
        self.max_connections = max_connections
        self.max_queue_size = max_queue_size
        
        # Connection management
        self.connections: Dict[str, WebSocket] = {}
        self.connection_metrics: Dict[str, ConnectionMetrics] = {}
        self.connection_handlers: Dict[str, Callable] = {}
        
        # Message queuing
        self.message_queues: Dict[str, asyncio.Queue] = {}
        self.queue_processors: Dict[str, asyncio.Task] = {}
        
        # Load balancing
        self.connection_groups: Dict[str, Set[str]] = defaultdict(set)
        self.round_robin_counters: Dict[str, int] = defaultdict(int)
        
        # Performance monitoring
        self.pool_stats = PoolStats()
        self.start_time = datetime.now()
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Health checking
        self.health_check_interval = 30  # seconds
        self.health_check_task: Optional[asyncio.Task] = None
        self.unhealthy_connections: Set[str] = set()
        
        # Message batching
        self.batch_size = 10
        self.batch_timeout = 0.01  # 10ms
        self.pending_batches: Dict[str, List] = defaultdict(list)
        self.batch_timers: Dict[str, asyncio.Task] = {}
        
        self.logger.info(f"WebSocket connection pool initialized (max_connections: {max_connections})")
    
    async def start(self):
        """Start the connection pool"""
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        self.logger.info("WebSocket connection pool started")
    
    async def stop(self):
        """Stop the connection pool and cleanup resources"""
        # Cancel monitoring tasks
        if self.monitoring_task:
            self.monitoring_task.cancel()
        if self.health_check_task:
            self.health_check_task.cancel()
        
        # Stop all queue processors
        for task in self.queue_processors.values():
            task.cancel()
        
        # Cancel batch timers
        for timer in self.batch_timers.values():
            timer.cancel()
        
        # Close all connections
        for client_id in list(self.connections.keys()):
            await self.disconnect_client(client_id)
        
        self.logger.info("WebSocket connection pool stopped")
    
    async def connect_client(
        self, 
        websocket: WebSocket, 
        client_id: Optional[str] = None,
        group: str = "default",
        message_handler: Optional[Callable] = None
    ) -> str:
        """
        Connect a new client to the pool
        
        Args:
            websocket: WebSocket connection
            client_id: Optional client ID (generated if not provided)
            group: Connection group for load balancing
            message_handler: Optional message handler function
            
        Returns:
            Client ID
        """
        if len(self.connections) >= self.max_connections:
            raise RuntimeError(f"Connection pool full (max: {self.max_connections})")
        
        # Generate client ID if not provided
        if not client_id:
            client_id = str(uuid.uuid4())
        
        # Accept WebSocket connection
        await websocket.accept()
        
        # Store connection
        self.connections[client_id] = websocket
        self.connection_groups[group].add(client_id)
        
        # Initialize metrics
        self.connection_metrics[client_id] = ConnectionMetrics(
            client_id=client_id,
            connected_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        # Create message queue
        self.message_queues[client_id] = asyncio.Queue(maxsize=self.max_queue_size)
        
        # Start queue processor
        self.queue_processors[client_id] = asyncio.create_task(
            self._process_message_queue(client_id)
        )
        
        # Store message handler
        if message_handler:
            self.connection_handlers[client_id] = message_handler
        
        # Update stats
        self.pool_stats.total_connections += 1
        self.pool_stats.active_connections += 1
        self.pool_stats.peak_connections = max(
            self.pool_stats.peak_connections, 
            self.pool_stats.active_connections
        )
        
        self.logger.info(f"Client {client_id} connected to pool (group: {group})")
        return client_id
    
    async def disconnect_client(self, client_id: str):
        """Disconnect a client from the pool"""
        if client_id not in self.connections:
            return
        
        try:
            # Close WebSocket connection
            websocket = self.connections[client_id]
            await websocket.close()
        except Exception as e:
            self.logger.debug(f"Error closing WebSocket for {client_id}: {e}")
        
        # Cleanup resources
        await self._cleanup_client_resources(client_id)
        
        self.logger.info(f"Client {client_id} disconnected from pool")
    
    async def _cleanup_client_resources(self, client_id: str):
        """Clean up all resources for a client"""
        # Remove from connections
        self.connections.pop(client_id, None)
        
        # Remove from groups
        for group_clients in self.connection_groups.values():
            group_clients.discard(client_id)
        
        # Stop queue processor
        if client_id in self.queue_processors:
            self.queue_processors[client_id].cancel()
            del self.queue_processors[client_id]
        
        # Clear message queue
        if client_id in self.message_queues:
            queue = self.message_queues[client_id]
            while not queue.empty():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
            del self.message_queues[client_id]
        
        # Cancel batch timer
        if client_id in self.batch_timers:
            self.batch_timers[client_id].cancel()
            del self.batch_timers[client_id]
        
        # Clear pending batches
        self.pending_batches.pop(client_id, None)
        
        # Remove handlers and metrics
        self.connection_handlers.pop(client_id, None)
        self.connection_metrics.pop(client_id, None)
        self.unhealthy_connections.discard(client_id)
        
        # Update stats
        self.pool_stats.active_connections = len(self.connections)
    
    async def send_message(
        self, 
        client_id: str, 
        message: Dict[str, Any], 
        priority: bool = False,
        batch: bool = True
    ) -> bool:
        """
        Send message to a specific client
        
        Args:
            client_id: Target client ID
            message: Message to send
            priority: If True, skip queue and send immediately
            batch: If True, allow message batching
            
        Returns:
            True if message was queued/sent successfully
        """
        if client_id not in self.connections:
            return False
        
        if client_id in self.unhealthy_connections:
            return False
        
        try:
            if priority or not batch:
                # Send immediately
                return await self._send_message_direct(client_id, message)
            else:
                # Queue for batched sending
                return await self._queue_message(client_id, message)
        
        except Exception as e:
            self.logger.error(f"Error sending message to {client_id}: {e}")
            await self._mark_connection_unhealthy(client_id)
            return False
    
    async def _send_message_direct(self, client_id: str, message: Dict[str, Any]) -> bool:
        """Send message directly to WebSocket"""
        try:
            websocket = self.connections[client_id]
            message_str = json.dumps(message)
            
            start_time = time.time()
            await websocket.send_text(message_str)
            latency_ms = (time.time() - start_time) * 1000
            
            # Update metrics
            metrics = self.connection_metrics[client_id]
            metrics.messages_sent += 1
            metrics.bytes_sent += len(message_str)
            metrics.latency_samples.append(latency_ms)
            metrics.last_activity = datetime.now()
            
            return True
            
        except WebSocketDisconnect:
            await self.disconnect_client(client_id)
            return False
        except Exception as e:
            self.logger.error(f"Direct send error for {client_id}: {e}")
            await self._mark_connection_unhealthy(client_id)
            return False
    
    async def _queue_message(self, client_id: str, message: Dict[str, Any]) -> bool:
        """Queue message for batched sending"""
        try:
            queue = self.message_queues[client_id]
            
            # Check queue capacity
            if queue.full():
                self.logger.warning(f"Message queue full for {client_id}, dropping message")
                return False
            
            await queue.put(message)
            return True
            
        except Exception as e:
            self.logger.error(f"Queue message error for {client_id}: {e}")
            return False
    
    async def _process_message_queue(self, client_id: str):
        """Process message queue for a client with batching"""
        try:
            while client_id in self.connections:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(
                        self.message_queues[client_id].get(),
                        timeout=1.0
                    )
                    
                    # Add to batch
                    self.pending_batches[client_id].append(message)
                    
                    # Check if batch is ready
                    if len(self.pending_batches[client_id]) >= self.batch_size:
                        await self._send_batch(client_id)
                    elif len(self.pending_batches[client_id]) == 1:
                        # Start batch timer for first message
                        self.batch_timers[client_id] = asyncio.create_task(
                            self._batch_timeout(client_id)
                        )
                
                except asyncio.TimeoutError:
                    # Send any pending messages
                    if self.pending_batches[client_id]:
                        await self._send_batch(client_id)
                
                except Exception as e:
                    self.logger.error(f"Queue processor error for {client_id}: {e}")
                    break
        
        except asyncio.CancelledError:
            # Send any remaining messages before shutdown
            if client_id in self.pending_batches and self.pending_batches[client_id]:
                await self._send_batch(client_id)
        
        except Exception as e:
            self.logger.error(f"Queue processor critical error for {client_id}: {e}")
    
    async def _batch_timeout(self, client_id: str):
        """Handle batch timeout"""
        try:
            await asyncio.sleep(self.batch_timeout)
            if self.pending_batches[client_id]:
                await self._send_batch(client_id)
        except asyncio.CancelledError:
            pass
    
    async def _send_batch(self, client_id: str):
        """Send batched messages"""
        if not self.pending_batches[client_id]:
            return
        
        try:
            # Cancel batch timer
            if client_id in self.batch_timers:
                self.batch_timers[client_id].cancel()
                del self.batch_timers[client_id]
            
            # Create batch message
            batch = self.pending_batches[client_id].copy()
            self.pending_batches[client_id].clear()
            
            if len(batch) == 1:
                # Single message - send directly
                await self._send_message_direct(client_id, batch[0])
            else:
                # Multiple messages - send as batch
                batch_message = {
                    "type": "batch",
                    "messages": batch,
                    "count": len(batch),
                    "timestamp": datetime.now().isoformat()
                }
                await self._send_message_direct(client_id, batch_message)
        
        except Exception as e:
            self.logger.error(f"Batch send error for {client_id}: {e}")
    
    async def broadcast_message(
        self, 
        message: Dict[str, Any], 
        group: Optional[str] = None,
        exclude: Optional[Set[str]] = None
    ):
        """
        Broadcast message to multiple clients
        
        Args:
            message: Message to broadcast
            group: Optional group to broadcast to (all clients if None)
            exclude: Optional set of client IDs to exclude
        """
        exclude = exclude or set()
        
        if group:
            target_clients = self.connection_groups.get(group, set())
        else:
            target_clients = set(self.connections.keys())
        
        # Remove excluded clients
        target_clients -= exclude
        
        # Send to all targets
        tasks = []
        for client_id in target_clients:
            if client_id not in self.unhealthy_connections:
                task = asyncio.create_task(
                    self.send_message(client_id, message, batch=True)
                )
                tasks.append(task)
        
        # Wait for all sends to complete
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if r is True)
            self.logger.debug(f"Broadcast sent to {success_count}/{len(tasks)} clients")
    
    async def _mark_connection_unhealthy(self, client_id: str):
        """Mark a connection as unhealthy"""
        self.unhealthy_connections.add(client_id)
        
        # Update error metrics
        if client_id in self.connection_metrics:
            self.connection_metrics[client_id].errors += 1
        
        self.logger.warning(f"Connection {client_id} marked as unhealthy")
    
    async def _health_check_loop(self):
        """Periodic health check for connections"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._perform_health_checks()
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check error: {e}")
    
    async def _perform_health_checks(self):
        """Perform health checks on all connections"""
        current_time = datetime.now()
        stale_threshold = timedelta(minutes=5)
        
        unhealthy_clients = []
        
        for client_id, metrics in self.connection_metrics.items():
            # Check for stale connections
            if current_time - metrics.last_activity > stale_threshold:
                unhealthy_clients.append(client_id)
                continue
            
            # Send ping to check connection health
            try:
                ping_message = {
                    "type": "ping",
                    "timestamp": current_time.isoformat()
                }
                success = await self.send_message(client_id, ping_message, priority=True, batch=False)
                
                if success and client_id in self.unhealthy_connections:
                    # Connection recovered
                    self.unhealthy_connections.remove(client_id)
                    self.logger.info(f"Connection {client_id} recovered")
                
            except Exception as e:
                self.logger.debug(f"Health check failed for {client_id}: {e}")
                unhealthy_clients.append(client_id)
        
        # Disconnect unhealthy clients
        for client_id in unhealthy_clients:
            await self.disconnect_client(client_id)
    
    async def _monitoring_loop(self):
        """Periodic monitoring and stats collection"""
        while True:
            try:
                await asyncio.sleep(60)  # Update every minute
                await self._update_pool_stats()
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
    
    async def _update_pool_stats(self):
        """Update pool statistics"""
        try:
            # Calculate aggregate metrics
            total_messages_sent = sum(m.messages_sent for m in self.connection_metrics.values())
            total_messages_received = sum(m.messages_received for m in self.connection_metrics.values())
            total_bytes_sent = sum(m.bytes_sent for m in self.connection_metrics.values())
            total_bytes_received = sum(m.bytes_received for m in self.connection_metrics.values())
            
            # Calculate average latency
            all_latencies = []
            for metrics in self.connection_metrics.values():
                all_latencies.extend(metrics.latency_samples)
            
            avg_latency = sum(all_latencies) / len(all_latencies) if all_latencies else 0.0
            
            # Calculate error rate
            total_errors = sum(m.errors for m in self.connection_metrics.values())
            total_operations = total_messages_sent + total_messages_received
            error_rate = (total_errors / total_operations * 100) if total_operations > 0 else 0.0
            
            # Update stats
            self.pool_stats.total_messages_sent = total_messages_sent
            self.pool_stats.total_messages_received = total_messages_received
            self.pool_stats.total_bytes_sent = total_bytes_sent
            self.pool_stats.total_bytes_received = total_bytes_received
            self.pool_stats.avg_latency_ms = avg_latency
            self.pool_stats.error_rate = error_rate
            self.pool_stats.uptime_seconds = (datetime.now() - self.start_time).total_seconds()
            
            self.logger.debug(f"Pool stats updated: {self.pool_stats.active_connections} active connections, "
                            f"{avg_latency:.2f}ms avg latency, {error_rate:.2f}% error rate")
        
        except Exception as e:
            self.logger.error(f"Stats update error: {e}")
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get current pool statistics"""
        return {
            "total_connections": self.pool_stats.total_connections,
            "active_connections": self.pool_stats.active_connections,
            "peak_connections": self.pool_stats.peak_connections,
            "unhealthy_connections": len(self.unhealthy_connections),
            "total_messages_sent": self.pool_stats.total_messages_sent,
            "total_messages_received": self.pool_stats.total_messages_received,
            "total_bytes_sent": self.pool_stats.total_bytes_sent,
            "total_bytes_received": self.pool_stats.total_bytes_received,
            "avg_latency_ms": round(self.pool_stats.avg_latency_ms, 2),
            "error_rate_percent": round(self.pool_stats.error_rate, 2),
            "uptime_seconds": round(self.pool_stats.uptime_seconds, 2),
            "queue_depths": {
                client_id: queue.qsize() 
                for client_id, queue in self.message_queues.items()
            }
        }
    
    def get_client_metrics(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific client"""
        if client_id not in self.connection_metrics:
            return None
        
        metrics = self.connection_metrics[client_id]
        return {
            "client_id": client_id,
            "connected_at": metrics.connected_at.isoformat(),
            "connection_duration_seconds": metrics.connection_duration.total_seconds(),
            "last_activity": metrics.last_activity.isoformat(),
            "messages_sent": metrics.messages_sent,
            "messages_received": metrics.messages_received,
            "bytes_sent": metrics.bytes_sent,
            "bytes_received": metrics.bytes_received,
            "errors": metrics.errors,
            "avg_latency_ms": round(metrics.avg_latency_ms, 2),
            "is_healthy": client_id not in self.unhealthy_connections,
            "queue_depth": self.message_queues[client_id].qsize() if client_id in self.message_queues else 0
        }


# Global connection pool instance
_connection_pool: Optional[WebSocketConnectionPool] = None


async def get_connection_pool(max_connections: int = 1000) -> WebSocketConnectionPool:
    """Get or create global connection pool"""
    global _connection_pool
    
    if _connection_pool is None:
        _connection_pool = WebSocketConnectionPool(max_connections=max_connections)
        await _connection_pool.start()
    
    return _connection_pool


async def cleanup_connection_pool():
    """Cleanup global connection pool"""
    global _connection_pool
    
    if _connection_pool:
        await _connection_pool.stop()
        _connection_pool = None