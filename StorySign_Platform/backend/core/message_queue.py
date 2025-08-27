#!/usr/bin/env python3
"""
High-Performance Message Queue System
Optimized for real-time video processing and high-throughput scenarios
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from collections import deque
from datetime import datetime, timedelta
from enum import Enum
import heapq
import uuid


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class QueuedMessage:
    """Message in the queue with metadata"""
    id: str
    content: Dict[str, Any]
    priority: MessagePriority
    created_at: datetime
    expires_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __lt__(self, other):
        """For priority queue ordering"""
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value  # Higher priority first
        return self.created_at < other.created_at  # FIFO for same priority


@dataclass
class QueueStats:
    """Queue statistics"""
    messages_queued: int = 0
    messages_processed: int = 0
    messages_failed: int = 0
    messages_expired: int = 0
    avg_processing_time_ms: float = 0.0
    queue_depth: int = 0
    throughput_per_second: float = 0.0


class MessageQueue:
    """
    High-performance message queue with priority handling, batching, and flow control
    """
    
    def __init__(
        self,
        name: str,
        max_size: int = 10000,
        batch_size: int = 10,
        batch_timeout: float = 0.01,  # 10ms
        enable_persistence: bool = False
    ):
        self.name = name
        self.max_size = max_size
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.enable_persistence = enable_persistence
        
        self.logger = logging.getLogger(f"{__name__}.MessageQueue.{name}")
        
        # Queue storage
        self._priority_queue: List[QueuedMessage] = []
        self._message_lookup: Dict[str, QueuedMessage] = {}
        self._queue_lock = asyncio.Lock()
        
        # Processing
        self._processors: List[asyncio.Task] = []
        self._processor_count = 1
        self._processing = False
        self._message_handlers: List[Callable] = []
        
        # Batching
        self._pending_batch: List[QueuedMessage] = []
        self._batch_timer: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = QueueStats()
        self._processing_times = deque(maxlen=1000)
        self._throughput_samples = deque(maxlen=60)  # 1 minute of samples
        
        # Flow control
        self._flow_control_enabled = True
        self._max_processing_rate = 1000  # messages per second
        self._rate_limiter = asyncio.Semaphore(100)  # concurrent processing limit
        
        self.logger.info(f"Message queue '{name}' initialized (max_size: {max_size})")
    
    async def start(self, processor_count: int = 1):
        """Start the message queue processors"""
        self._processor_count = processor_count
        self._processing = True
        
        # Start processor tasks
        for i in range(processor_count):
            processor = asyncio.create_task(self._processor_loop(f"processor-{i}"))
            self._processors.append(processor)
        
        # Start throughput monitoring
        asyncio.create_task(self._throughput_monitor())
        
        self.logger.info(f"Message queue '{self.name}' started with {processor_count} processors")
    
    async def stop(self):
        """Stop the message queue and cleanup"""
        self._processing = False
        
        # Cancel batch timer
        if self._batch_timer:
            self._batch_timer.cancel()
        
        # Cancel all processors
        for processor in self._processors:
            processor.cancel()
        
        # Wait for processors to finish
        if self._processors:
            await asyncio.gather(*self._processors, return_exceptions=True)
        
        self._processors.clear()
        self.logger.info(f"Message queue '{self.name}' stopped")
    
    async def enqueue(
        self,
        message: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        ttl_seconds: Optional[float] = None,
        message_id: Optional[str] = None
    ) -> str:
        """
        Enqueue a message
        
        Args:
            message: Message content
            priority: Message priority
            ttl_seconds: Time to live in seconds
            message_id: Optional message ID
            
        Returns:
            Message ID
        """
        if not message_id:
            message_id = str(uuid.uuid4())
        
        # Check queue capacity
        async with self._queue_lock:
            if len(self._priority_queue) >= self.max_size:
                # Try to remove expired messages first
                await self._cleanup_expired_messages()
                
                if len(self._priority_queue) >= self.max_size:
                    raise RuntimeError(f"Queue '{self.name}' is full (max_size: {self.max_size})")
        
        # Create queued message
        expires_at = None
        if ttl_seconds:
            expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        
        queued_msg = QueuedMessage(
            id=message_id,
            content=message,
            priority=priority,
            created_at=datetime.now(),
            expires_at=expires_at
        )
        
        # Add to queue
        async with self._queue_lock:
            heapq.heappush(self._priority_queue, queued_msg)
            self._message_lookup[message_id] = queued_msg
            self.stats.messages_queued += 1
            self.stats.queue_depth = len(self._priority_queue)
        
        self.logger.debug(f"Message {message_id} enqueued with priority {priority.name}")
        return message_id
    
    async def dequeue(self, timeout: Optional[float] = None) -> Optional[QueuedMessage]:
        """
        Dequeue a message
        
        Args:
            timeout: Optional timeout in seconds
            
        Returns:
            QueuedMessage or None if timeout/empty
        """
        start_time = time.time()
        
        while True:
            async with self._queue_lock:
                # Clean up expired messages
                await self._cleanup_expired_messages()
                
                if self._priority_queue:
                    message = heapq.heappop(self._priority_queue)
                    del self._message_lookup[message.id]
                    self.stats.queue_depth = len(self._priority_queue)
                    return message
            
            # Check timeout
            if timeout and (time.time() - start_time) >= timeout:
                return None
            
            # Wait a bit before checking again
            await asyncio.sleep(0.001)  # 1ms
    
    async def _cleanup_expired_messages(self):
        """Remove expired messages from queue"""
        if not self._priority_queue:
            return
        
        current_time = datetime.now()
        expired_messages = []
        
        # Find expired messages
        for msg in self._priority_queue:
            if msg.expires_at and current_time > msg.expires_at:
                expired_messages.append(msg)
        
        # Remove expired messages
        for msg in expired_messages:
            try:
                self._priority_queue.remove(msg)
                del self._message_lookup[msg.id]
                self.stats.messages_expired += 1
                self.logger.debug(f"Message {msg.id} expired")
            except (ValueError, KeyError):
                pass  # Already removed
        
        # Rebuild heap if we removed messages
        if expired_messages:
            heapq.heapify(self._priority_queue)
            self.stats.queue_depth = len(self._priority_queue)
    
    def add_handler(self, handler: Callable[[QueuedMessage], Any]):
        """Add a message handler"""
        self._message_handlers.append(handler)
        self.logger.debug(f"Handler added to queue '{self.name}'")
    
    def remove_handler(self, handler: Callable):
        """Remove a message handler"""
        if handler in self._message_handlers:
            self._message_handlers.remove(handler)
            self.logger.debug(f"Handler removed from queue '{self.name}'")
    
    async def _processor_loop(self, processor_name: str):
        """Main processor loop"""
        self.logger.debug(f"Processor {processor_name} started for queue '{self.name}'")
        
        try:
            while self._processing:
                try:
                    # Apply rate limiting
                    async with self._rate_limiter:
                        # Dequeue message
                        message = await self.dequeue(timeout=1.0)
                        
                        if message:
                            await self._process_message(message, processor_name)
                
                except Exception as e:
                    self.logger.error(f"Processor {processor_name} error: {e}")
                    await asyncio.sleep(0.1)  # Brief pause on error
        
        except asyncio.CancelledError:
            self.logger.debug(f"Processor {processor_name} cancelled")
        
        except Exception as e:
            self.logger.error(f"Processor {processor_name} critical error: {e}")
    
    async def _process_message(self, message: QueuedMessage, processor_name: str):
        """Process a single message"""
        start_time = time.time()
        
        try:
            # Check if message should be batched
            if self.batch_size > 1 and message.priority != MessagePriority.CRITICAL:
                await self._add_to_batch(message)
            else:
                # Process immediately
                await self._handle_message(message)
            
            # Update statistics
            processing_time = (time.time() - start_time) * 1000  # ms
            self._processing_times.append(processing_time)
            self.stats.messages_processed += 1
            
            # Update average processing time
            if self._processing_times:
                self.stats.avg_processing_time_ms = sum(self._processing_times) / len(self._processing_times)
        
        except Exception as e:
            self.logger.error(f"Message processing error: {e}")
            
            # Retry logic
            if message.retry_count < message.max_retries:
                message.retry_count += 1
                await self.enqueue(
                    message.content,
                    message.priority,
                    message_id=message.id
                )
                self.logger.debug(f"Message {message.id} requeued (retry {message.retry_count})")
            else:
                self.stats.messages_failed += 1
                self.logger.error(f"Message {message.id} failed after {message.max_retries} retries")
    
    async def _add_to_batch(self, message: QueuedMessage):
        """Add message to batch for processing"""
        self._pending_batch.append(message)
        
        # Check if batch is ready
        if len(self._pending_batch) >= self.batch_size:
            await self._process_batch()
        elif len(self._pending_batch) == 1:
            # Start batch timer
            self._batch_timer = asyncio.create_task(self._batch_timeout_handler())
    
    async def _batch_timeout_handler(self):
        """Handle batch timeout"""
        try:
            await asyncio.sleep(self.batch_timeout)
            if self._pending_batch:
                await self._process_batch()
        except asyncio.CancelledError:
            pass
    
    async def _process_batch(self):
        """Process batched messages"""
        if not self._pending_batch:
            return
        
        # Cancel batch timer
        if self._batch_timer:
            self._batch_timer.cancel()
            self._batch_timer = None
        
        # Process batch
        batch = self._pending_batch.copy()
        self._pending_batch.clear()
        
        try:
            if len(batch) == 1:
                # Single message
                await self._handle_message(batch[0])
            else:
                # Batch processing
                await self._handle_message_batch(batch)
        
        except Exception as e:
            self.logger.error(f"Batch processing error: {e}")
            
            # Requeue failed messages
            for msg in batch:
                if msg.retry_count < msg.max_retries:
                    msg.retry_count += 1
                    await self.enqueue(msg.content, msg.priority, message_id=msg.id)
    
    async def _handle_message(self, message: QueuedMessage):
        """Handle a single message"""
        for handler in self._message_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                self.logger.error(f"Handler error for message {message.id}: {e}")
                raise
    
    async def _handle_message_batch(self, messages: List[QueuedMessage]):
        """Handle a batch of messages"""
        # Create batch message
        batch_content = {
            "type": "batch",
            "messages": [msg.content for msg in messages],
            "count": len(messages),
            "batch_id": str(uuid.uuid4())
        }
        
        batch_message = QueuedMessage(
            id=f"batch_{int(time.time())}",
            content=batch_content,
            priority=max(msg.priority for msg in messages),
            created_at=datetime.now()
        )
        
        await self._handle_message(batch_message)
    
    async def _throughput_monitor(self):
        """Monitor throughput and update statistics"""
        last_processed = 0
        
        while self._processing:
            try:
                await asyncio.sleep(1.0)  # Check every second
                
                current_processed = self.stats.messages_processed
                throughput = current_processed - last_processed
                
                self._throughput_samples.append(throughput)
                
                # Calculate average throughput
                if self._throughput_samples:
                    self.stats.throughput_per_second = sum(self._throughput_samples) / len(self._throughput_samples)
                
                last_processed = current_processed
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Throughput monitor error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        return {
            "name": self.name,
            "queue_depth": self.stats.queue_depth,
            "messages_queued": self.stats.messages_queued,
            "messages_processed": self.stats.messages_processed,
            "messages_failed": self.stats.messages_failed,
            "messages_expired": self.stats.messages_expired,
            "avg_processing_time_ms": round(self.stats.avg_processing_time_ms, 2),
            "throughput_per_second": round(self.stats.throughput_per_second, 2),
            "processor_count": len(self._processors),
            "batch_size": self.batch_size,
            "pending_batch_size": len(self._pending_batch),
            "is_processing": self._processing
        }


class MessageQueueManager:
    """
    Manager for multiple message queues with load balancing and routing
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.MessageQueueManager")
        self.queues: Dict[str, MessageQueue] = {}
        self.routing_rules: Dict[str, str] = {}  # message_type -> queue_name
        self.load_balancer_queues: Dict[str, List[str]] = {}  # group -> queue_names
        self.round_robin_counters: Dict[str, int] = {}
    
    async def create_queue(
        self,
        name: str,
        max_size: int = 10000,
        batch_size: int = 10,
        batch_timeout: float = 0.01,
        processor_count: int = 1
    ) -> MessageQueue:
        """Create and start a new message queue"""
        if name in self.queues:
            raise ValueError(f"Queue '{name}' already exists")
        
        queue = MessageQueue(
            name=name,
            max_size=max_size,
            batch_size=batch_size,
            batch_timeout=batch_timeout
        )
        
        await queue.start(processor_count)
        self.queues[name] = queue
        
        self.logger.info(f"Queue '{name}' created and started")
        return queue
    
    async def remove_queue(self, name: str):
        """Remove and stop a message queue"""
        if name not in self.queues:
            return
        
        queue = self.queues[name]
        await queue.stop()
        del self.queues[name]
        
        # Clean up routing rules
        self.routing_rules = {k: v for k, v in self.routing_rules.items() if v != name}
        
        # Clean up load balancer groups
        for group, queue_names in self.load_balancer_queues.items():
            if name in queue_names:
                queue_names.remove(name)
        
        self.logger.info(f"Queue '{name}' removed")
    
    def add_routing_rule(self, message_type: str, queue_name: str):
        """Add a message routing rule"""
        self.routing_rules[message_type] = queue_name
        self.logger.debug(f"Routing rule added: {message_type} -> {queue_name}")
    
    def add_load_balancer_group(self, group_name: str, queue_names: List[str]):
        """Add a load balancer group"""
        self.load_balancer_queues[group_name] = queue_names
        self.round_robin_counters[group_name] = 0
        self.logger.debug(f"Load balancer group '{group_name}' added with queues: {queue_names}")
    
    async def route_message(
        self,
        message: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        ttl_seconds: Optional[float] = None,
        target_queue: Optional[str] = None,
        load_balancer_group: Optional[str] = None
    ) -> str:
        """
        Route message to appropriate queue
        
        Args:
            message: Message content
            priority: Message priority
            ttl_seconds: Time to live
            target_queue: Specific target queue
            load_balancer_group: Load balancer group name
            
        Returns:
            Message ID
        """
        # Determine target queue
        queue_name = None
        
        if target_queue:
            queue_name = target_queue
        elif load_balancer_group:
            queue_name = self._get_load_balanced_queue(load_balancer_group)
        else:
            # Use routing rules
            message_type = message.get("type", "default")
            queue_name = self.routing_rules.get(message_type, "default")
        
        # Get queue
        if queue_name not in self.queues:
            raise ValueError(f"Queue '{queue_name}' not found")
        
        queue = self.queues[queue_name]
        
        # Enqueue message
        return await queue.enqueue(message, priority, ttl_seconds)
    
    def _get_load_balanced_queue(self, group_name: str) -> str:
        """Get next queue from load balancer group using round-robin"""
        if group_name not in self.load_balancer_queues:
            raise ValueError(f"Load balancer group '{group_name}' not found")
        
        queue_names = self.load_balancer_queues[group_name]
        if not queue_names:
            raise ValueError(f"Load balancer group '{group_name}' has no queues")
        
        # Round-robin selection
        counter = self.round_robin_counters[group_name]
        queue_name = queue_names[counter % len(queue_names)]
        self.round_robin_counters[group_name] = counter + 1
        
        return queue_name
    
    def get_queue(self, name: str) -> Optional[MessageQueue]:
        """Get a queue by name"""
        return self.queues.get(name)
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all queues"""
        return {
            "queues": {name: queue.get_stats() for name, queue in self.queues.items()},
            "routing_rules": self.routing_rules,
            "load_balancer_groups": self.load_balancer_queues,
            "total_queues": len(self.queues)
        }
    
    async def shutdown(self):
        """Shutdown all queues"""
        for queue in self.queues.values():
            await queue.stop()
        
        self.queues.clear()
        self.logger.info("All queues shut down")


# Global message queue manager
_queue_manager: Optional[MessageQueueManager] = None


def get_queue_manager() -> MessageQueueManager:
    """Get or create global queue manager"""
    global _queue_manager
    
    if _queue_manager is None:
        _queue_manager = MessageQueueManager()
    
    return _queue_manager


async def cleanup_queue_manager():
    """Cleanup global queue manager"""
    global _queue_manager
    
    if _queue_manager:
        await _queue_manager.shutdown()
        _queue_manager = None