---
inclusion: always
---

# StorySign ASL Platform Architecture Guidelines

## Project Overview

StorySign is a real-time ASL learning platform with React/Electron frontend and FastAPI backend using MediaPipe for computer vision.

## Key Architecture Patterns

### Backend Structure

- **FastAPI**: Main web framework with WebSocket support for real-time video streaming
- **MediaPipe**: Computer vision processing for hand/face/pose detection
- **Hybrid AI**: Local vision models (Ollama) + cloud LLM for story generation
- **Async Processing**: Thread pool executors for CPU-intensive MediaPipe operations

### Frontend Structure

- **React + Electron**: Desktop application with modular page-based routing
- **WebSocket Client**: Real-time video streaming with automatic reconnection
- **State Management**: React hooks for practice sessions and story generation

### Critical Performance Considerations

- Video processing must maintain <100ms latency
- MediaPipe operations run in separate threads to avoid blocking event loop
- Frame throttling prevents frontend from overwhelming backend
- Gesture detection uses velocity-based segmentation

### Testing Strategy

- Unit tests for individual components
- Integration tests for WebSocket communication
- End-to-end tests for complete user workflows
- Performance benchmarks for latency requirements

## Development Guidelines

### When modifying video processing:

- Always test with MediaPipe environment active
- Verify latency benchmarks after changes
- Update gesture detection parameters carefully
- Test WebSocket message handling

### When adding new AI features:

- Use async/await for all AI service calls
- Implement proper error handling and fallbacks
- Add loading states for user feedback
- Test with mock services for reliability

### When updating APIs:

- Maintain backward compatibility
- Update Pydantic models first
- Add comprehensive error responses
- Test WebSocket message types
