---
inclusion: fileMatch
fileMatchPattern: "**/VideoStream.js"
---

# Video Streaming Troubleshooting Guide

## Common Issues and Solutions

### Video Stream Not Showing After Story Generation

**Problem**: MediaPipe video disappears after story generation and selection
**Root Cause**: Webcam and streaming not activated when practice starts
**Solution**: Ensure `toggleWebcam` and `toggleStreaming` are passed as props and called in `handleStartPractice`

```javascript
// In ASLWorldPage.js
const handleStartPractice = () => {
  if (!webcamActive && toggleWebcam) {
    toggleWebcam();
  }
  setPracticeStarted(true);
};

// Effect to handle streaming activation after webcam is active
React.useEffect(() => {
  if (practiceStarted && webcamActive && !streamingActive && toggleStreaming) {
    const timer = setTimeout(() => {
      toggleStreaming();
    }, 1000);
    return () => clearTimeout(timer);
  }
}, [practiceStarted, webcamActive, streamingActive, toggleStreaming]);
```

### WebSocket Connection Issues

**Problem**: Streaming connection status shows "disconnected"
**Solution**: Check backend is running and WebSocket endpoint is accessible

### Performance Issues

**Problem**: Video processing latency > 100ms
**Solution**:

- Verify MediaPipe environment is active
- Check frame throttling settings
- Monitor memory usage during processing

## Testing Checklist

- [ ] Webcam activates when "Start Practice" is clicked
- [ ] Streaming connection establishes within 2 seconds
- [ ] MediaPipe landmarks are visible on video
- [ ] No console errors related to WebSocket
- [ ] Video processing latency < 100ms

#[[file:StorySign_Platform/frontend/src/components/video/VideoStream.js]]
