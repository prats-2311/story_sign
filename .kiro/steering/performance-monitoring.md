---
inclusion: fileMatch
fileMatchPattern: "**/video_processor.py"
---

# Performance Monitoring Guidelines

## Critical Performance Metrics

- **Video Processing Latency**: Must be < 100ms
- **WebSocket Message Handling**: Must be < 50ms
- **Memory Usage**: Monitor for memory leaks during long sessions
- **Frame Rate**: Target 30 FPS for smooth experience

## Monitoring Implementation

```python
# Add performance logging to video_processor.py
import time
import logging

def process_frame_with_timing(self, frame):
    start_time = time.time()
    result = self.process_frame(frame)
    processing_time = (time.time() - start_time) * 1000

    if processing_time > 100:
        logging.warning(f"Slow frame processing: {processing_time:.2f}ms")

    return result, processing_time
```

## Performance Testing Commands

```bash
# Run latency tests
cd StorySign_Platform/backend
python test_latency_improvements.py

# Monitor system resources
python -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"

# Test gesture detection performance
python test_gesture_detection.py
```

## Optimization Strategies

1. **Frame Throttling**: Limit to 30 FPS max
2. **MediaPipe Model Complexity**: Use complexity=0 for fastest processing
3. **Thread Pool**: Use ThreadPoolExecutor for CPU-intensive operations
4. **Memory Management**: Clear buffers regularly during long sessions

#[[file:StorySign_Platform/backend/video_processor.py]]
