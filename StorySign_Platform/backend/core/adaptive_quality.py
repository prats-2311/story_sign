#!/usr/bin/env python3
"""
Adaptive Quality and Bandwidth Management System
Dynamically adjusts video quality and processing parameters based on network conditions and performance
"""

import asyncio
import logging
import time
import statistics
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import deque
from datetime import datetime, timedelta
from enum import Enum
import json


class QualityProfile(Enum):
    """Quality profile levels"""
    ULTRA_LOW = "ultra_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA_HIGH = "ultra_high"


class NetworkCondition(Enum):
    """Network condition assessment"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class QualitySettings:
    """Quality settings configuration"""
    profile: QualityProfile
    jpeg_quality: int
    resolution_scale: float
    frame_rate: int
    mediapipe_complexity: int
    batch_size: int
    compression_level: int
    skip_frames: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile": self.profile.value,
            "jpeg_quality": self.jpeg_quality,
            "resolution_scale": self.resolution_scale,
            "frame_rate": self.frame_rate,
            "mediapipe_complexity": self.mediapipe_complexity,
            "batch_size": self.batch_size,
            "compression_level": self.compression_level,
            "skip_frames": self.skip_frames
        }


@dataclass
class NetworkMetrics:
    """Network performance metrics"""
    bandwidth_mbps: float = 0.0
    latency_ms: float = 0.0
    packet_loss_percent: float = 0.0
    jitter_ms: float = 0.0
    throughput_mbps: float = 0.0
    connection_stability: float = 1.0  # 0.0 to 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "bandwidth_mbps": self.bandwidth_mbps,
            "latency_ms": self.latency_ms,
            "packet_loss_percent": self.packet_loss_percent,
            "jitter_ms": self.jitter_ms,
            "throughput_mbps": self.throughput_mbps,
            "connection_stability": self.connection_stability
        }


@dataclass
class PerformanceMetrics:
    """System performance metrics"""
    cpu_usage_percent: float = 0.0
    memory_usage_percent: float = 0.0
    processing_time_ms: float = 0.0
    queue_depth: int = 0
    frame_drop_rate: float = 0.0
    error_rate: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "cpu_usage_percent": self.cpu_usage_percent,
            "memory_usage_percent": self.memory_usage_percent,
            "processing_time_ms": self.processing_time_ms,
            "queue_depth": self.queue_depth,
            "frame_drop_rate": self.frame_drop_rate,
            "error_rate": self.error_rate
        }


class AdaptiveQualityManager:
    """
    Manages adaptive quality adjustments based on network conditions and system performance
    """
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.logger = logging.getLogger(f"{__name__}.AdaptiveQualityManager.{client_id}")
        
        # Quality profiles configuration
        self.quality_profiles = {
            QualityProfile.ULTRA_LOW: QualitySettings(
                profile=QualityProfile.ULTRA_LOW,
                jpeg_quality=25,
                resolution_scale=0.5,
                frame_rate=10,
                mediapipe_complexity=0,
                batch_size=5,
                compression_level=9,
                skip_frames=3
            ),
            QualityProfile.LOW: QualitySettings(
                profile=QualityProfile.LOW,
                jpeg_quality=40,
                resolution_scale=0.65,
                frame_rate=15,
                mediapipe_complexity=0,
                batch_size=3,
                compression_level=7,
                skip_frames=2
            ),
            QualityProfile.MEDIUM: QualitySettings(
                profile=QualityProfile.MEDIUM,
                jpeg_quality=60,
                resolution_scale=0.8,
                frame_rate=20,
                mediapipe_complexity=1,
                batch_size=2,
                compression_level=5,
                skip_frames=1
            ),
            QualityProfile.HIGH: QualitySettings(
                profile=QualityProfile.HIGH,
                jpeg_quality=75,
                resolution_scale=0.9,
                frame_rate=25,
                mediapipe_complexity=1,
                batch_size=1,
                compression_level=3,
                skip_frames=0
            ),
            QualityProfile.ULTRA_HIGH: QualitySettings(
                profile=QualityProfile.ULTRA_HIGH,
                jpeg_quality=90,
                resolution_scale=1.0,
                frame_rate=30,
                mediapipe_complexity=2,
                batch_size=1,
                compression_level=1,
                skip_frames=0
            )
        }
        
        # Current state
        self.current_profile = QualityProfile.MEDIUM
        self.current_settings = self.quality_profiles[self.current_profile]
        
        # Metrics history
        self.network_history = deque(maxlen=60)  # 1 minute of history
        self.performance_history = deque(maxlen=60)
        self.quality_history = deque(maxlen=100)
        
        # Adaptation parameters
        self.adaptation_interval = 2.0  # seconds
        self.last_adaptation = 0.0
        self.stability_threshold = 5  # seconds before allowing upgrades
        self.degradation_threshold = 1  # seconds before forcing downgrades
        
        # Thresholds for quality decisions
        self.network_thresholds = {
            NetworkCondition.EXCELLENT: {"latency": 30, "bandwidth": 10, "loss": 0.1},
            NetworkCondition.GOOD: {"latency": 50, "bandwidth": 5, "loss": 0.5},
            NetworkCondition.FAIR: {"latency": 100, "bandwidth": 2, "loss": 1.0},
            NetworkCondition.POOR: {"latency": 200, "bandwidth": 1, "loss": 2.0},
            NetworkCondition.CRITICAL: {"latency": 500, "bandwidth": 0.5, "loss": 5.0}
        }
        
        self.performance_thresholds = {
            "cpu_high": 80.0,
            "memory_high": 85.0,
            "processing_time_high": 100.0,  # ms
            "queue_depth_high": 10,
            "frame_drop_high": 5.0,  # percent
            "error_rate_high": 2.0   # percent
        }
        
        # Bandwidth estimation
        self.bandwidth_estimator = BandwidthEstimator(client_id)
        
        self.logger.info(f"Adaptive quality manager initialized for client {client_id}")
    
    def update_network_metrics(self, metrics: NetworkMetrics):
        """Update network performance metrics"""
        metrics.timestamp = datetime.now()
        self.network_history.append(metrics)
        
        # Update bandwidth estimator
        self.bandwidth_estimator.add_sample(
            metrics.throughput_mbps,
            metrics.latency_ms,
            metrics.packet_loss_percent
        )
        
        self.logger.debug(f"Network metrics updated: {metrics.to_dict()}")
    
    def update_performance_metrics(self, metrics: PerformanceMetrics):
        """Update system performance metrics"""
        metrics.timestamp = datetime.now()
        self.performance_history.append(metrics)
        
        self.logger.debug(f"Performance metrics updated: {metrics.to_dict()}")
    
    async def adapt_quality(self) -> Tuple[bool, QualitySettings]:
        """
        Adapt quality based on current conditions
        
        Returns:
            Tuple of (quality_changed, new_settings)
        """
        current_time = time.time()
        
        # Check if enough time has passed since last adaptation
        if current_time - self.last_adaptation < self.adaptation_interval:
            return False, self.current_settings
        
        # Assess current conditions
        network_condition = self._assess_network_condition()
        performance_condition = self._assess_performance_condition()
        
        # Determine optimal quality profile
        optimal_profile = self._calculate_optimal_profile(network_condition, performance_condition)
        
        # Check if change is needed
        if optimal_profile == self.current_profile:
            return False, self.current_settings
        
        # Apply stability/degradation rules
        if optimal_profile.value > self.current_profile.value:
            # Upgrading quality - check stability
            if current_time - self.last_adaptation < self.stability_threshold:
                self.logger.debug(f"Quality upgrade delayed for stability (current: {self.current_profile.value})")
                return False, self.current_settings
        
        # Change quality profile
        old_profile = self.current_profile
        self.current_profile = optimal_profile
        self.current_settings = self.quality_profiles[optimal_profile]
        self.last_adaptation = current_time
        
        # Record quality change
        self.quality_history.append({
            "timestamp": datetime.now(),
            "old_profile": old_profile.value,
            "new_profile": optimal_profile.value,
            "network_condition": network_condition.value,
            "performance_condition": performance_condition
        })
        
        self.logger.info(f"Quality adapted: {old_profile.value} → {optimal_profile.value} "
                        f"(network: {network_condition.value}, performance: {performance_condition})")
        
        return True, self.current_settings
    
    def _assess_network_condition(self) -> NetworkCondition:
        """Assess current network condition"""
        if not self.network_history:
            return NetworkCondition.FAIR
        
        # Get recent metrics (last 10 seconds)
        recent_metrics = [m for m in self.network_history 
                         if (datetime.now() - m.timestamp).total_seconds() <= 10]
        
        if not recent_metrics:
            return NetworkCondition.FAIR
        
        # Calculate averages
        avg_latency = statistics.mean(m.latency_ms for m in recent_metrics)
        avg_bandwidth = statistics.mean(m.bandwidth_mbps for m in recent_metrics)
        avg_loss = statistics.mean(m.packet_loss_percent for m in recent_metrics)
        
        # Determine condition based on thresholds
        for condition, thresholds in self.network_thresholds.items():
            if (avg_latency <= thresholds["latency"] and
                avg_bandwidth >= thresholds["bandwidth"] and
                avg_loss <= thresholds["loss"]):
                return condition
        
        return NetworkCondition.CRITICAL
    
    def _assess_performance_condition(self) -> str:
        """Assess current system performance condition"""
        if not self.performance_history:
            return "unknown"
        
        # Get recent metrics
        recent_metrics = [m for m in self.performance_history 
                         if (datetime.now() - m.timestamp).total_seconds() <= 10]
        
        if not recent_metrics:
            return "unknown"
        
        # Check for performance issues
        issues = []
        
        avg_cpu = statistics.mean(m.cpu_usage_percent for m in recent_metrics)
        if avg_cpu > self.performance_thresholds["cpu_high"]:
            issues.append("high_cpu")
        
        avg_memory = statistics.mean(m.memory_usage_percent for m in recent_metrics)
        if avg_memory > self.performance_thresholds["memory_high"]:
            issues.append("high_memory")
        
        avg_processing = statistics.mean(m.processing_time_ms for m in recent_metrics)
        if avg_processing > self.performance_thresholds["processing_time_high"]:
            issues.append("slow_processing")
        
        avg_queue = statistics.mean(m.queue_depth for m in recent_metrics)
        if avg_queue > self.performance_thresholds["queue_depth_high"]:
            issues.append("queue_backlog")
        
        avg_drops = statistics.mean(m.frame_drop_rate for m in recent_metrics)
        if avg_drops > self.performance_thresholds["frame_drop_high"]:
            issues.append("frame_drops")
        
        avg_errors = statistics.mean(m.error_rate for m in recent_metrics)
        if avg_errors > self.performance_thresholds["error_rate_high"]:
            issues.append("high_errors")
        
        if not issues:
            return "good"
        elif len(issues) <= 2:
            return "moderate"
        else:
            return "poor"
    
    def _calculate_optimal_profile(
        self, 
        network_condition: NetworkCondition, 
        performance_condition: str
    ) -> QualityProfile:
        """Calculate optimal quality profile based on conditions"""
        
        # Start with network-based profile
        network_profile_map = {
            NetworkCondition.EXCELLENT: QualityProfile.ULTRA_HIGH,
            NetworkCondition.GOOD: QualityProfile.HIGH,
            NetworkCondition.FAIR: QualityProfile.MEDIUM,
            NetworkCondition.POOR: QualityProfile.LOW,
            NetworkCondition.CRITICAL: QualityProfile.ULTRA_LOW
        }
        
        base_profile = network_profile_map[network_condition]
        
        # Adjust based on performance condition
        if performance_condition == "poor":
            # Downgrade by 2 levels
            profiles = list(QualityProfile)
            current_idx = profiles.index(base_profile)
            target_idx = max(0, current_idx - 2)
            return profiles[target_idx]
        
        elif performance_condition == "moderate":
            # Downgrade by 1 level
            profiles = list(QualityProfile)
            current_idx = profiles.index(base_profile)
            target_idx = max(0, current_idx - 1)
            return profiles[target_idx]
        
        elif performance_condition == "good":
            # Can potentially upgrade
            return base_profile
        
        else:  # unknown
            # Conservative approach
            return QualityProfile.MEDIUM
    
    def get_current_settings(self) -> QualitySettings:
        """Get current quality settings"""
        return self.current_settings
    
    def force_quality_profile(self, profile: QualityProfile):
        """Force a specific quality profile"""
        old_profile = self.current_profile
        self.current_profile = profile
        self.current_settings = self.quality_profiles[profile]
        self.last_adaptation = time.time()
        
        self.logger.info(f"Quality profile forced: {old_profile.value} → {profile.value}")
    
    def get_adaptation_stats(self) -> Dict[str, Any]:
        """Get adaptation statistics"""
        return {
            "client_id": self.client_id,
            "current_profile": self.current_profile.value,
            "current_settings": self.current_settings.to_dict(),
            "network_condition": self._assess_network_condition().value if self.network_history else "unknown",
            "performance_condition": self._assess_performance_condition(),
            "adaptations_count": len(self.quality_history),
            "last_adaptation": self.last_adaptation,
            "bandwidth_estimate": self.bandwidth_estimator.get_current_estimate(),
            "recent_quality_changes": [
                {
                    "timestamp": change["timestamp"].isoformat(),
                    "old_profile": change["old_profile"],
                    "new_profile": change["new_profile"],
                    "network_condition": change["network_condition"]
                }
                for change in list(self.quality_history)[-5:]  # Last 5 changes
            ]
        }


class BandwidthEstimator:
    """
    Estimates available bandwidth using various techniques
    """
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.logger = logging.getLogger(f"{__name__}.BandwidthEstimator.{client_id}")
        
        # Bandwidth samples
        self.throughput_samples = deque(maxlen=100)
        self.latency_samples = deque(maxlen=100)
        self.loss_samples = deque(maxlen=100)
        
        # Estimation parameters
        self.min_samples = 10
        self.estimation_window = 30  # seconds
        
        # Current estimates
        self.current_bandwidth = 0.0
        self.confidence = 0.0
    
    def add_sample(self, throughput_mbps: float, latency_ms: float, loss_percent: float):
        """Add a bandwidth measurement sample"""
        timestamp = time.time()
        
        self.throughput_samples.append((timestamp, throughput_mbps))
        self.latency_samples.append((timestamp, latency_ms))
        self.loss_samples.append((timestamp, loss_percent))
        
        # Update estimate
        self._update_estimate()
    
    def _update_estimate(self):
        """Update bandwidth estimate based on recent samples"""
        current_time = time.time()
        cutoff_time = current_time - self.estimation_window
        
        # Filter recent samples
        recent_throughput = [
            throughput for timestamp, throughput in self.throughput_samples
            if timestamp > cutoff_time
        ]
        
        recent_latency = [
            latency for timestamp, latency in self.latency_samples
            if timestamp > cutoff_time
        ]
        
        recent_loss = [
            loss for timestamp, loss in self.loss_samples
            if timestamp > cutoff_time
        ]
        
        if len(recent_throughput) < self.min_samples:
            self.confidence = 0.0
            return
        
        # Calculate bandwidth estimate using multiple methods
        estimates = []
        
        # Method 1: Average throughput
        avg_throughput = statistics.mean(recent_throughput)
        estimates.append(avg_throughput)
        
        # Method 2: Median throughput (more robust to outliers)
        median_throughput = statistics.median(recent_throughput)
        estimates.append(median_throughput)
        
        # Method 3: 90th percentile (conservative estimate)
        if len(recent_throughput) >= 10:
            percentile_90 = sorted(recent_throughput)[int(len(recent_throughput) * 0.9)]
            estimates.append(percentile_90)
        
        # Method 4: Latency-adjusted estimate
        if recent_latency:
            avg_latency = statistics.mean(recent_latency)
            latency_factor = max(0.1, 1.0 - (avg_latency - 50) / 200)  # Adjust based on latency
            latency_adjusted = avg_throughput * latency_factor
            estimates.append(latency_adjusted)
        
        # Method 5: Loss-adjusted estimate
        if recent_loss:
            avg_loss = statistics.mean(recent_loss)
            loss_factor = max(0.1, 1.0 - avg_loss / 10)  # Adjust based on packet loss
            loss_adjusted = avg_throughput * loss_factor
            estimates.append(loss_adjusted)
        
        # Combine estimates (weighted average)
        weights = [0.3, 0.2, 0.2, 0.15, 0.15][:len(estimates)]
        self.current_bandwidth = sum(est * weight for est, weight in zip(estimates, weights)) / sum(weights)
        
        # Calculate confidence based on sample count and variance
        if len(recent_throughput) >= self.min_samples:
            variance = statistics.variance(recent_throughput)
            sample_factor = min(1.0, len(recent_throughput) / 50)  # More samples = higher confidence
            variance_factor = max(0.1, 1.0 - variance / (avg_throughput + 1))  # Lower variance = higher confidence
            self.confidence = sample_factor * variance_factor
        else:
            self.confidence = 0.0
        
        self.logger.debug(f"Bandwidth estimate updated: {self.current_bandwidth:.2f} Mbps "
                         f"(confidence: {self.confidence:.2f})")
    
    def get_current_estimate(self) -> Dict[str, float]:
        """Get current bandwidth estimate"""
        return {
            "bandwidth_mbps": round(self.current_bandwidth, 2),
            "confidence": round(self.confidence, 2),
            "sample_count": len(self.throughput_samples)
        }


class AdaptiveQualityService:
    """
    Service managing adaptive quality for multiple clients
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.AdaptiveQualityService")
        self.client_managers: Dict[str, AdaptiveQualityManager] = {}
        self.monitoring_task: Optional[asyncio.Task] = None
        self.monitoring_active = False
    
    async def start(self):
        """Start the adaptive quality service"""
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        self.logger.info("Adaptive quality service started")
    
    async def stop(self):
        """Stop the adaptive quality service"""
        self.monitoring_active = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.client_managers.clear()
        self.logger.info("Adaptive quality service stopped")
    
    def add_client(self, client_id: str) -> AdaptiveQualityManager:
        """Add a client for quality management"""
        if client_id in self.client_managers:
            return self.client_managers[client_id]
        
        manager = AdaptiveQualityManager(client_id)
        self.client_managers[client_id] = manager
        
        self.logger.info(f"Client {client_id} added to adaptive quality service")
        return manager
    
    def remove_client(self, client_id: str):
        """Remove a client from quality management"""
        if client_id in self.client_managers:
            del self.client_managers[client_id]
            self.logger.info(f"Client {client_id} removed from adaptive quality service")
    
    def get_client_manager(self, client_id: str) -> Optional[AdaptiveQualityManager]:
        """Get quality manager for a client"""
        return self.client_managers.get(client_id)
    
    async def _monitoring_loop(self):
        """Monitor all clients and trigger adaptations"""
        while self.monitoring_active:
            try:
                # Trigger adaptation for all clients
                for client_id, manager in self.client_managers.items():
                    try:
                        changed, settings = await manager.adapt_quality()
                        if changed:
                            self.logger.info(f"Quality adapted for client {client_id}: {settings.profile.value}")
                    except Exception as e:
                        self.logger.error(f"Adaptation error for client {client_id}: {e}")
                
                await asyncio.sleep(1.0)  # Check every second
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(5.0)
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            "active_clients": len(self.client_managers),
            "monitoring_active": self.monitoring_active,
            "clients": {
                client_id: manager.get_adaptation_stats()
                for client_id, manager in self.client_managers.items()
            }
        }


# Global adaptive quality service
_adaptive_quality_service: Optional[AdaptiveQualityService] = None


async def get_adaptive_quality_service() -> AdaptiveQualityService:
    """Get or create global adaptive quality service"""
    global _adaptive_quality_service
    
    if _adaptive_quality_service is None:
        _adaptive_quality_service = AdaptiveQualityService()
        await _adaptive_quality_service.start()
    
    return _adaptive_quality_service


async def cleanup_adaptive_quality_service():
    """Cleanup global adaptive quality service"""
    global _adaptive_quality_service
    
    if _adaptive_quality_service:
        await _adaptive_quality_service.stop()
        _adaptive_quality_service = None