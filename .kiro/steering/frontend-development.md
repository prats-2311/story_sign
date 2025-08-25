---
inclusion: fileMatch
fileMatchPattern: "StorySign_Platform/frontend/**/*.js"
---

# Frontend Development Guidelines

## Component Architecture

- Use functional components with hooks
- Implement proper error boundaries
- Add loading states for all async operations
- Use WebSocket reconnection logic

## State Management Patterns

```javascript
// Practice session state
const [practiceState, setPracticeState] = useState({
  currentSentence: 0,
  isListening: false,
  feedback: null,
  story: null,
});
```

## WebSocket Integration

- Always implement reconnection with exponential backoff
- Handle connection state in UI
- Parse message types properly: 'processed_frame', 'asl_feedback', 'control'
- Add error handling for malformed messages

## Performance Requirements

- Frame throttling: FRAME_THROTTLE_MS = 100
- Implement frame dropping if processing falls behind
- Use requestAnimationFrame for smooth video display
- Monitor WebSocket message queue size

## Testing Requirements

- Jest for unit tests
- React Testing Library for component tests
- Mock WebSocket connections for testing
- Test error scenarios and edge cases

#[[file:StorySign_Platform/frontend/src/**/*.js]]
