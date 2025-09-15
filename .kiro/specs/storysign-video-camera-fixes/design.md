# Design Document

## Overview

This design addresses critical video and camera functionality issues in the StorySign platform by implementing proper state management patterns and consistent webcam initialization across all modules. The solution focuses on "lifting state up" to resolve video stream persistence issues in ASL World and implementing proper camera lifecycle management in Harmony and Reconnect modules.

## Architecture

### Current State Management Issues

1. **ASL World Module**: WebSocket and webcam state are managed within `ASLWorldModule.js`, causing state loss during view transitions from `StorySetup` to `PracticeView`
2. **Harmony/Reconnect Pages**: Already implement `useWebcam` hook but lack proper initialization lifecycle management
3. **State Persistence**: Video streams disconnect when components re-render due to local state management

### Proposed Architecture Changes

```
┌─────────────────────────────────────────────────────────────────┐
│                        Page Level (Persistent)                  │
├─────────────────────────────────────────────────────────────────┤
│  ASLWorldPage.js                                               │
│  ├── Add useWebSocket and useWebcam hooks                      │
│  ├── Currently receives webcam/streaming props from parent     │
│  ├── Directly renders StorySetup, StorySelection, PracticeView │
│  └── Pass webcam/WebSocket state to individual components      │
│                                                                 │
│  HarmonyPage.js                                                │
│  ├── useWebcam() with useEffect lifecycle                      │
│  └── Conditional rendering based on camera status              │
│                                                                 │
│  ReconnectPage.js                                              │
│  ├── useWebcam() with useEffect lifecycle                      │
│  └── Conditional rendering based on camera status              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Component Level (Props-based)                │
├─────────────────────────────────────────────────────────────────┤
│  StorySetup.js                                                │
│  ├── Receives webcam props for object scanning                 │
│  └── Uses captureFrame for story generation                    │
│                                                                 │
│  PracticeView.js                                               │
│  ├── Receives processedFrame for video display                 │
│  ├── Contains VideoStreamingClient as children                 │
│  └── Shows ProcessedVideoDisplay component                     │
│                                                                 │
│  StorySelection.js                                             │
│  └── No video functionality needed                             │
│                                                                 │
│  FeedbackPanel.js                                              │
│  └── No video functionality needed                             │
└─────────────────────────────────────────────────────────────────┘

Note: ASLWorldModule.js exists but is not currently used by ASLWorldPage
```

## Components and Interfaces

### 1. ASLWorldPage Component Refactor

**Current Issues:**

- Currently receives webcam/streaming state as props from parent component
- Video state is not persistent at the page level, causing issues during view transitions
- Individual components (StorySetup, PracticeView) need direct access to webcam/WebSocket state

**Design Solution:**

```javascript
// ASLWorldPage.js - Enhanced structure
const ASLWorldPage = () => {
  // Add persistent state at page level (in addition to existing props)
  const {
    connectionStatus,
    processedFrame,
    sendControlMessage,
    startPracticeSession,
  } = useWebSocket("ws://127.0.0.1:8000/ws/video");

  const { webcamRef, isWebcamActive, startWebcam, stopWebcam, captureFrame } =
    useWebcam();

  // Existing reducer state management continues
  const [state, dispatch] = useReducer(aslWorldReducer, initialState);

  // Pass webcam/WebSocket state directly to individual components
  const renderCurrentView = () => {
    switch (state.currentView) {
      case "story_generation":
        return (
          <StorySetup
            onStoryGenerate={handleStoryGenerate}
            // Add webcam props
            webcamRef={webcamRef}
            isWebcamActive={isWebcamActive}
            captureFrame={captureFrame}
            connectionStatus={connectionStatus}
          />
        );
      case "practice":
        return (
          <PracticeView
            selectedStory={state.selectedStory}
            // Add video props
            processedFrame={processedFrame}
            sendControlMessage={sendControlMessage}
          >
            <VideoStreamingClient />
          </PracticeView>
        );
    }
  };
};
```

### 2. StorySetup Component Enhancement

**Current Issues:**

- Local state management for webcam and WebSocket
- State resets during view transitions

**Design Solution:**

```javascript
// ASLWorldModule.js - Refactored to be stateless for video/connection
export const ASLWorldModule = ({
  // Received props from parent
  connectionStatus,
  processedFrame,
  sendControlMessage,
  startPracticeSession,
  webcamRef,
  isWebcamActive,
  startWebcam,
  stopWebcam,
  captureFrame,
}) => {
  // Only local state for view management
  const [currentView, setCurrentView] = useState("story_generation");
  const [story, setStory] = useState(null);

  // Remove useWebSocket and useWebcam hooks
  // Use lifecycle effects for webcam management
  useEffect(() => {
    startWebcam();
    return () => stopWebcam();
  }, [startWebcam, stopWebcam]);

  // Pass props down to child components
  return (
    <div className="asl-world-module">
      {currentView === "story_generation" ? (
        <StorySetup
          webcamRef={webcamRef}
          isWebcamActive={isWebcamActive}
          captureFrame={captureFrame}
          connectionStatus={connectionStatus}
          onStoryGenerated={handleStoryGenerated}
        />
      ) : (
        <PracticeView
          story={story}
          processedFrame={processedFrame}
          sendControlMessage={sendControlMessage}
        />
      )}
    </div>
  );
};
```

### 3. HarmonyPage Component Enhancement

**Current Issues:**

- Already uses `useWebcam` but lacks proper initialization lifecycle
- Camera may not activate automatically on page load

**Design Solution:**

```javascript
// HarmonyPage.js - Enhanced with proper lifecycle
const HarmonyPage = () => {
  const { webcamRef, isWebcamActive, startWebcam, stopWebcam } = useWebcam();

  // Automatic camera initialization on mount
  useEffect(() => {
    startWebcam();
    return () => stopWebcam();
  }, [startWebcam, stopWebcam]);

  return (
    <div className="harmony-page">
      <main className="page-content">
        {isWebcamActive ? (
          <HarmonyModule webcamRef={webcamRef} />
        ) : (
          <div className="camera-inactive-placeholder">
            <p>Camera is inactive. Please grant permission to begin.</p>
          </div>
        )}
      </main>
    </div>
  );
};
```

### 4. ReconnectPage Component Enhancement

**Current Issues:**

- Same as HarmonyPage - lacks proper initialization lifecycle

**Design Solution:**

```javascript
// ReconnectPage.js - Enhanced with proper lifecycle
const ReconnectPage = () => {
  const { webcamRef, isWebcamActive, startWebcam, stopWebcam } = useWebcam();

  // Automatic camera initialization on mount
  useEffect(() => {
    startWebcam();
    return () => stopWebcam();
  }, [startWebcam, stopWebcam]);

  return (
    <div className="reconnect-page">
      <main className="page-content">
        {isWebcamActive ? (
          <ReconnectModule webcamRef={webcamRef} />
        ) : (
          <div className="camera-inactive-placeholder">
            <p>Camera is inactive. Please grant permission to begin.</p>
          </div>
        )}
      </main>
    </div>
  );
};
```

## Data Models

### WebSocket Connection State

```typescript
interface WebSocketState {
  connectionStatus: "connected" | "connecting" | "disconnected" | "error";
  processedFrame: ProcessedFrameData | null;
  sendControlMessage: (message: any) => boolean;
  startPracticeSession: (sentences: string[]) => void;
}
```

### Webcam State

```typescript
interface WebcamState {
  webcamRef: RefObject<HTMLVideoElement>;
  isWebcamActive: boolean;
  startWebcam: () => Promise<boolean>;
  stopWebcam: () => void;
  captureFrame: () => FrameData | null;
}
```

### Props Interface for ASLWorldModule

```typescript
interface ASLWorldModuleProps {
  // WebSocket Props
  connectionStatus: string;
  processedFrame: ProcessedFrameData | null;
  sendControlMessage: (message: any) => boolean;
  startPracticeSession: (sentences: string[]) => void;

  // Webcam Props
  webcamRef: RefObject<HTMLVideoElement>;
  isWebcamActive: boolean;
  startWebcam: () => Promise<boolean>;
  stopWebcam: () => void;
  captureFrame: () => FrameData | null;
}
```

## Error Handling

### Camera Permission Errors

```javascript
// Enhanced error handling for camera access
const handleCameraError = (error) => {
  switch (error.type) {
    case "PERMISSION_DENIED":
      return {
        message: "Camera access denied. Please allow camera permissions.",
        action: "Check browser settings and reload the page",
      };
    case "NO_DEVICE_FOUND":
      return {
        message: "No camera device found.",
        action: "Connect a camera and try again",
      };
    case "DEVICE_IN_USE":
      return {
        message: "Camera is in use by another application.",
        action: "Close other apps using the camera",
      };
    default:
      return {
        message: "Camera initialization failed.",
        action: "Please try again",
      };
  }
};
```

### WebSocket Connection Errors

```javascript
// Enhanced error handling for WebSocket connections
const handleWebSocketError = (error) => {
  switch (error.code) {
    case 1006: // Abnormal closure
      return {
        message: "Connection lost unexpectedly.",
        action: "Attempting automatic reconnection...",
      };
    case 1011: // Server error
      return {
        message: "Server encountered an error.",
        action: "Please try again in a moment",
      };
    default:
      return {
        message: "WebSocket connection failed.",
        action: "Check if backend is running",
      };
  }
};
```

## Testing Strategy

### Unit Tests

1. **State Management Tests**

   - Verify props are passed correctly from page to module
   - Test state persistence during view transitions
   - Validate webcam lifecycle management

2. **Hook Integration Tests**
   - Test `useWebSocket` and `useWebcam` integration
   - Verify proper cleanup on component unmount
   - Test error handling scenarios

### Integration Tests

1. **Video Stream Persistence**

   - Test video stream continuity during ASL World view transitions
   - Verify MediaPipe processing continues without interruption
   - Test WebSocket message handling during state changes

2. **Camera Initialization**
   - Test automatic camera activation on page load
   - Verify proper error handling for permission denied scenarios
   - Test camera resource cleanup on page navigation

### End-to-End Tests

1. **Complete User Workflows**
   - Generate story → practice session with continuous video
   - Navigate to Harmony → automatic camera activation
   - Navigate to Reconnect → automatic camera activation
   - Test cross-module navigation with proper resource management

### Performance Tests

1. **Latency Validation**
   - Ensure video processing maintains <100ms latency requirement
   - Test frame throttling during high-load scenarios
   - Validate MediaPipe performance with persistent connections

## Compatibility Considerations

### Backend Integration

- All fixes maintain compatibility with `main_api_production.py`
- WebSocket endpoint remains `ws://127.0.0.1:8000/ws/video` for local development
- Production deployment uses same backend file for consistency

### Browser Compatibility

- Camera access works across modern browsers (Chrome, Firefox, Safari, Edge)
- WebSocket connections support automatic reconnection
- Graceful degradation for browsers with limited MediaDevices API support

### Device Compatibility

- Responsive design maintains functionality on different screen sizes
- Camera resolution adapts based on device capabilities
- Touch-friendly controls for tablet/mobile usage

## Security Considerations

### Camera Access

- Proper permission handling with user-friendly error messages
- Secure camera stream handling without data leakage
- Automatic cleanup of camera resources on page navigation

### WebSocket Security

- Secure WebSocket connections in production environment
- Message validation to prevent malicious data injection
- Rate limiting for video frame transmission

## Performance Optimizations

### Memory Management

- Proper cleanup of video streams and WebSocket connections
- Efficient frame processing with adaptive quality settings
- Garbage collection optimization for long-running sessions

### Network Optimization

- Frame throttling to prevent network congestion
- Adaptive quality based on connection speed
- Efficient WebSocket message serialization

This design ensures robust video and camera functionality while maintaining the existing MediaPipe integration and performance characteristics required by the StorySign platform.
