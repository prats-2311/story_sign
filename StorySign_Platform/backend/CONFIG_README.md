# Configuration Management System

The StorySign ASL Platform backend uses a comprehensive configuration management system that supports multiple configuration sources with a clear precedence order.

## Configuration Sources (in order of precedence)

1. **Environment Variables** (highest priority)
2. **YAML Configuration File**
3. **Default Values** (lowest priority)

## Configuration Structure

The configuration is organized into three main sections:

### Video Configuration (`video`)

- `width`: Video frame width in pixels (320-1920, default: 640)
- `height`: Video frame height in pixels (240-1080, default: 480)
- `fps`: Target frames per second (10-60, default: 30)
- `format`: Video format codec (MJPG/YUYV/H264, default: "MJPG")
- `quality`: JPEG compression quality (50-100, default: 85)

### MediaPipe Configuration (`mediapipe`)

- `min_detection_confidence`: Minimum confidence for person detection (0.0-1.0, default: 0.5)
- `min_tracking_confidence`: Minimum confidence for landmark tracking (0.0-1.0, default: 0.5)
- `model_complexity`: Model complexity - 0=lite, 1=full, 2=heavy (default: 1)
- `enable_segmentation`: Enable pose segmentation mask (default: false)
- `refine_face_landmarks`: Enable refined face landmark detection (default: true)

### Server Configuration (`server`)

- `host`: Server host address (default: "0.0.0.0")
- `port`: Server port number (1024-65535, default: 8000)
- `reload`: Enable auto-reload in development (default: true)
- `log_level`: Logging level (debug/info/warning/error/critical, default: "info")
- `max_connections`: Maximum WebSocket connections (1-100, default: 10)

## Usage Examples

### 1. Using YAML Configuration File

Create a `config.yaml` file in the backend directory:

```yaml
video:
  width: 1280
  height: 720
  fps: 60
  format: "H264"
  quality: 95

mediapipe:
  min_detection_confidence: 0.7
  min_tracking_confidence: 0.6
  model_complexity: 2
  enable_segmentation: true

server:
  host: "127.0.0.1"
  port: 9000
  log_level: "debug"
  max_connections: 20
```

### 2. Using Environment Variables

Set environment variables with the `STORYSIGN_` prefix and double underscores for nesting:

```bash
# Video configuration
export STORYSIGN_VIDEO__WIDTH=1280
export STORYSIGN_VIDEO__HEIGHT=720
export STORYSIGN_VIDEO__FPS=60

# MediaPipe configuration
export STORYSIGN_MEDIAPIPE__MIN_DETECTION_CONFIDENCE=0.7
export STORYSIGN_MEDIAPIPE__MODEL_COMPLEXITY=2

# Server configuration
export STORYSIGN_SERVER__PORT=9000
export STORYSIGN_SERVER__LOG_LEVEL=debug
```

### 3. Programmatic Access

```python
from config import get_config

# Get configuration
config = get_config()

# Access configuration values
print(f"Video resolution: {config.video.width}x{config.video.height}")
print(f"MediaPipe complexity: {config.mediapipe.model_complexity}")
print(f"Server port: {config.server.port}")
```

## Configuration File Locations

The system automatically searches for configuration files in the following locations:

1. `config.yaml` (current directory)
2. `config.yml` (current directory)
3. `storysign_config.yaml` (current directory)
4. `storysign_config.yml` (current directory)
5. `~/.storysign/config.yaml` (user home directory)
6. `/etc/storysign/config.yaml` (system-wide)

## API Endpoints

### Health Check with Configuration Info

```
GET /
```

Returns system status including current configuration summary.

### Full Configuration Details

```
GET /config
```

Returns complete current configuration (excluding sensitive settings).

## Validation

All configuration values are validated:

- **Type checking**: Ensures correct data types
- **Range validation**: Numeric values must be within specified ranges
- **Enum validation**: String values must be from allowed sets
- **Custom validation**: Format-specific validation (e.g., video formats)

Invalid configuration will raise a `ValueError` with a descriptive error message.

## Testing

Run the configuration tests to verify the system:

```bash
python test_config.py
```

This will test:

- Default configuration loading
- YAML file configuration
- Environment variable overrides
- Configuration validation

## Development vs Production

### Development Settings

```yaml
server:
  host: "127.0.0.1"
  port: 8000
  reload: true
  log_level: "debug"
```

### Production Settings

```yaml
server:
  host: "0.0.0.0"
  port: 8000
  reload: false
  log_level: "info"
  max_connections: 50

video:
  quality: 90 # Higher quality for production

mediapipe:
  model_complexity: 1 # Balanced performance
```

## Troubleshooting

1. **Configuration not loading**: Check file permissions and YAML syntax
2. **Environment variables ignored**: Ensure correct naming with `STORYSIGN_` prefix
3. **Validation errors**: Check value ranges and types in error messages
4. **Performance issues**: Adjust `model_complexity` and `video.quality` settings
