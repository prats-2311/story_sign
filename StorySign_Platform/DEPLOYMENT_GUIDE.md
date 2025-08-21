# StorySign ASL Platform - Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the StorySign ASL Platform in production environments. The platform consists of a FastAPI backend with MediaPipe processing and a React/Electron frontend.

## System Requirements

### Minimum Requirements

- **CPU**: 4 cores, 2.5GHz
- **RAM**: 8GB
- **Storage**: 10GB free space
- **OS**: Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **Python**: 3.8+
- **Node.js**: 16+

### Recommended Requirements

- **CPU**: 8 cores, 3.0GHz (with GPU acceleration support)
- **RAM**: 16GB
- **Storage**: 20GB SSD
- **GPU**: NVIDIA GTX 1060+ or equivalent (for GPU acceleration)
- **Network**: Gigabit Ethernet

## Pre-deployment Setup

### 1. Environment Preparation

```bash
# Clone repository
git clone <repository-url>
cd StorySign_Platform

# Create Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
cd frontend
npm install
cd ..
```

### 2. Configuration

Create production configuration file:

```yaml
# config.yaml
video:
  width: 640
  height: 480
  fps: 30
  quality: 65
  format: "MJPG"

mediapipe:
  min_detection_confidence: 0.5
  min_tracking_confidence: 0.5
  model_complexity: 1
  enable_segmentation: false
  refine_face_landmarks: true

server:
  host: "0.0.0.0"
  port: 8000
  log_level: "info"
  max_connections: 50
```

## Production Deployment

### Option 1: Docker Deployment (Recommended)

Create Dockerfile for backend:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ ./backend/
COPY config.yaml .

EXPOSE 8000
CMD ["python", "backend/main.py"]
```

### Option 2: Direct Deployment

1. **Backend Deployment**

```bash
# Production server startup
python backend/main.py --host 0.0.0.0 --port 8000
```

2. **Frontend Build**

```bash
cd frontend
npm run build
npm run electron-pack
```

## Performance Optimization

### 1. Enable GPU Acceleration

```bash
# Install CUDA support (NVIDIA GPUs)
pip install cupy-cuda11x

# Install OpenCL support
pip install pyopencl
```

### 2. System Tuning

```bash
# Increase file descriptor limits
ulimit -n 65536

# Optimize network settings
echo 'net.core.rmem_max = 16777216' >> /etc/sysctl.conf
echo 'net.core.wmem_max = 16777216' >> /etc/sysctl.conf
```

## Monitoring and Maintenance

### Health Checks

- Backend: `GET http://localhost:8000/`
- WebSocket: `ws://localhost:8000/ws/video`

### Log Management

- Backend logs: `storysign_backend.log`
- Frontend logs: Browser console
- System logs: `/var/log/storysign/`

### Performance Monitoring

- CPU usage: < 80%
- Memory usage: < 16GB
- Latency: < 100ms
- Frame rate: > 20 FPS

## Troubleshooting

### Common Issues

1. **High Latency**

   - Reduce video quality
   - Enable GPU acceleration
   - Check network bandwidth

2. **Memory Leaks**

   - Monitor with `htop`
   - Restart service if memory > 90%

3. **Connection Issues**
   - Check firewall settings
   - Verify port availability
   - Test WebSocket connectivity

## Security Considerations

### Network Security

- Use HTTPS in production
- Configure firewall rules
- Implement rate limiting

### Application Security

- Validate all inputs
- Sanitize file uploads
- Monitor for suspicious activity

## Backup and Recovery

### Data Backup

- Configuration files
- Application logs
- User preferences

### Recovery Procedures

1. Stop services
2. Restore from backup
3. Verify configuration
4. Restart services
5. Test functionality

## Support and Maintenance

### Regular Maintenance

- Update dependencies monthly
- Monitor system resources
- Review security logs
- Performance optimization

### Support Contacts

- Technical Issues: [support-email]
- Security Issues: [security-email]
- Documentation: [docs-url]

---

**Last Updated**: August 21, 2025
**Version**: 1.0.0
