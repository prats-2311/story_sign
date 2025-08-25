---
inclusion: fileMatch
fileMatchPattern: "**/video_processor.py"
---

# MediaPipe Development Guidelines

## Environment Requirements

- MediaPipe must be installed in conda environment
- OpenCV compatibility is critical for frame processing
- Test environment with `test_mediapipe_env.py` before development

## Performance Optimization Patterns

```python
# Always use thread pool for MediaPipe processing
executor = ThreadPoolExecutor()
processed_frame = await loop.run_in_executor(
    executor, process_frame, data
)
```

## Gesture Detection Best Practices

- Use hand velocity thresholds: `GESTURE_START_THRESHOLD = 0.02`
- Implement pause detection for gesture end: `GESTURE_END_PAUSE_FRAMES = 10`
- Buffer landmark data during active gestures
- Clear buffers on session reset

## Testing Requirements

- Always run `test_gesture_detection.py` after changes
- Verify latency with `test_latency_improvements.py`
- Test WebSocket integration with mock data

#[[file:StorySign_Platform/backend/video_processor.py]]
