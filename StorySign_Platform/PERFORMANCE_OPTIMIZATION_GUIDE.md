# StorySign Performance Optimization Guide

## Overview

This guide provides detailed instructions for optimizing the StorySign ASL Platform for maximum performance and minimal latency.

## Performance Targets

- **Latency**: < 100ms end-to-end
- **Frame Rate**: 20-30 FPS
- **CPU Usage**: < 80%
- **Memory Usage**: < 8GB
- **Frame Drop Rate**: < 5%

## Optimization Strategies

### 1. Adaptive Quality Management

The system automatically adjusts quality based on performance:

```python
# Quality profiles available
profiles = {
    "ultra_performance": {
        "jpeg_quality": 40,
        "resolution_scale": 0.6,
        "frame_skip": 3,
        "target_latency_ms": 30
    },
    "high_performance": {
        "jpeg_quality": 50,
        "resolution_scale": 0.75,
        "frame_skip": 2,
        "target_latency_ms": 50
    },
    "balanced": {
        "jpeg_quality": 65,
        "resolution_scale": 0.85,
        "frame_skip": 1,
        "target_latency_ms": 75
    },
    "high_quality": {
        "jpeg_quality": 80,
        "resolution_scale": 1.0,
        "frame_skip": 0,
        "target_latency_ms": 100
    }
}
```

### 2. Frame Rate Optimization

Dynamic frame rate adjustment based on processing capability:

- **Adaptive FPS**: Automatically adjusts between 10-60 FPS
- **Frame Skipping**: Processes every Nth frame when under load
- **Smart Throttling**: Client-side frame rate management

### 3. Compression Optimization

Multiple compression strategies for different scenarios:

- **Ultra Fast**: JPEG quality 35, no optimization
- **Fast**: JPEG quality 50, basic optimization
- **Balanced**: JPEG quality 65, full optimization
- **Quality**: JPEG quality 80, progressive encoding

### 4. Threading Strategy

Optimized multi-threading for video processing:

- **Thread Pool**: Dynamic worker count based on CPU cores
- **Async Processing**: Non-blocking frame processing
- **Resource Isolation**: Per-client processing threads

## Configuration Options

### Environment Variables

```bash
# Performance mode
export STORYSIGN_PERFORMANCE_MODE=ultra_performance

# Video settings
export STORYSIGN_VIDEO__QUALITY=50
export STORYSIGN_VIDEO__WIDTH=640
export STORYSIGN_VIDEO__HEIGHT=480
export STORYSIGN_VIDEO__FPS=30

# MediaPipe optimization
export STORYSIGN_MEDIAPIPE__MODEL_COMPLEXITY=0
export STORYSIGN_MEDIAPIPE__MIN_DETECTION_CONFIDENCE=0.3
export STORYSIGN_MEDIAPIPE__MIN_TRACKING_CONFIDENCE=0.3

# Server optimization
export STORYSIGN_SERVER__MAX_CONNECTIONS=20
```

### Configuration File

```yaml
# config.yaml
performance:
  adaptive_quality: true
  target_latency_ms: 75
  max_cpu_usage: 80
  max_memory_usage: 8192

video:
  quality: 50
  width: 640
  height: 480
  fps: 30

mediapipe:
  model_complexity: 0
  min_detection_confidence: 0.3
  min_tracking_confidence: 0.3
  enable_segmentation: false
```

## Hardware Optimization

### GPU Acceleration

Enable GPU processing for MediaPipe:

```bash
# Install CUDA support
pip install mediapipe-gpu

# Enable GPU in configuration
export STORYSIGN_MEDIAPIPE_GPU=true
```

### CPU Optimization

Optimize CPU usage:

```bash
# Set CPU affinity
taskset -c 0-3 python backend/main.py

# Adjust process priority
nice -n -10 python backend/main.py
```

### Memory Optimization

Configure memory settings:

```bash
# Increase shared memory
echo 'kernel.shmmax = 268435456' >> /etc/sysctl.conf

# Configure swap
swapon --show
```

## Network Optimization

### WebSocket Configuration

Optimize WebSocket performance:

```python
# WebSocket settings
websocket_config = {
    "ping_interval": 20,
    "ping_timeout": 10,
    "close_timeout": 10,
    "max_size": 2 * 1024 * 1024,  # 2MB
    "max_queue": 3,
    "compression": None  # Disable for speed
}
```

### Network Tuning

System-level network optimization:

```bash
# TCP buffer sizes
echo 'net.core.rmem_max = 16777216' >> /etc/sysctl.conf
echo 'net.core.wmem_max = 16777216' >> /etc/sysctl.conf

# TCP congestion control
echo 'net.ipv4.tcp_congestion_control = bbr' >> /etc/sysctl.conf
```

## Monitoring and Alerting

### Performance Metrics

Monitor these key metrics:

- **Latency**: End-to-end processing time
- **Throughput**: Frames processed per second
- **Resource Usage**: CPU, memory, GPU utilization
- **Error Rate**: Processing failures and timeouts
- **Queue Depth**: Frame processing backlog

### Alerting Thresholds

```yaml
alerts:
  latency:
    warning: 100ms
    critical: 200ms

  cpu_usage:
    warning: 80%
    critical: 90%

  memory_usage:
    warning: 6GB
    critical: 7GB

  frame_drop_rate:
    warning: 5%
    critical: 10%
```

## Troubleshooting Performance Issues

### High Latency

1. **Check system resources**

   ```bash
   htop
   nvidia-smi  # For GPU systems
   ```

2. **Reduce quality settings**

   ```python
   quality_manager.set_profile("ultra_performance")
   ```

3. **Enable frame skipping**
   ```python
   frame_processor.set_skip_ratio(2)  # Process every 2nd frame
   ```

### High CPU Usage

1. **Reduce MediaPipe complexity**

   ```yaml
   mediapipe:
     model_complexity: 0
   ```

2. **Limit concurrent connections**

   ```yaml
   server:
     max_connections: 10
   ```

3. **Enable GPU acceleration**
   ```bash
   export STORYSIGN_USE_GPU=true
   ```

### Memory Leaks

1. **Monitor memory usage**

   ```python
   import psutil
   process = psutil.Process()
   print(f"Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
   ```

2. **Force garbage collection**

   ```python
   import gc
   gc.collect()
   ```

3. **Restart service periodically**
   ```bash
   # Cron job for daily restart
   0 2 * * * systemctl restart storysign
   ```

## Best Practices

### Development

- Profile code regularly
- Use async/await for I/O operations
- Implement proper error handling
- Monitor resource usage during development

### Production

- Use production-grade WSGI server
- Implement health checks
- Set up monitoring and alerting
- Regular performance testing

### Maintenance

- Update dependencies regularly
- Monitor system logs
- Perform regular backups
- Test disaster recovery procedures

## Performance Testing

### Load Testing

```bash
# Install testing tools
pip install locust websocket-client

# Run load test
locust -f tests/load_test.py --host=ws://localhost:8000
```

### Benchmark Results

Target performance on recommended hardware:

- **Latency**: 45-75ms average
- **Throughput**: 25-30 FPS
- **CPU Usage**: 60-75%
- **Memory Usage**: 4-6GB
- **Concurrent Users**: 20-50

---

**Last Updated**: August 21, 2025
**Performance Target**: < 100ms latency, 20+ FPS
