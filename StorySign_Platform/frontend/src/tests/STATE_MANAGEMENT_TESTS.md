# State Management Tests

This document describes the comprehensive test suite for the video/camera state management fixes
implemented in the StorySign platform.

## Overview

The test suite covers the state management changes made to fix critical video and camera
functionality issues across the ASL World, Harmony, and Reconnect modules. These tests ensure that:

1. Webcam and WebSocket state is properly managed at the page level
2. Props are correctly passed down to individual components
3. Camera lifecycle management works correctly
4. Error handling for camera permission scenarios is robust
5. Resource cleanup happens properly on component unmount

## Test Categories

### Unit Tests

#### Page Component Tests

**ASLWorldPage.test.js**

- Tests prop passing to StorySetup, PracticeView, and other components
- Verifies webcam and WebSocket state persistence during view transitions
- Tests legacy props support and fallback to internal hooks
- Validates error handling scenarios

**HarmonyPage.test.js**

- Tests automatic camera initialization on component mount
- Verifies camera cleanup on component unmount
- Tests conditional rendering based on webcam state
- Validates camera error handling and retry functionality
- Tests module prop passing for webcam state

**ReconnectPage.test.js**

- Tests automatic camera initialization on component mount
- Verifies camera cleanup on component unmount
- Tests conditional rendering based on webcam state
- Validates camera error handling and retry functionality
- Tests module prop passing for webcam state

#### Hook Tests

**useWebcam.test.js**

- Tests webcam initialization and cleanup
- Validates error handling for various camera scenarios
- Tests frame capture functionality
- Verifies multiple start/stop cycles
- Tests cleanup on unmount

**useWebSocket.test.js**

- Tests WebSocket connection management
- Validates message sending and receiving
- Tests reconnection logic with exponential backoff
- Verifies frame throttling functionality
- Tests error scenarios and recovery

### Integration Tests

**StateManagement.integration.test.js**

- Tests complete user workflows across all pages
- Verifies state consistency during page transitions
- Tests cross-component state management
- Validates resource management across components
- Tests error recovery scenarios

## Running Tests

### Run All State Management Tests

```bash
npm run test:state-management
```

### Run Only Unit Tests

```bash
npm run test:state-management:unit
```

### Run Only Integration Tests

```bash
npm run test:state-management:integration
```

### Run Individual Test Files

```bash
# ASLWorldPage tests
npm test -- src/pages/ASLWorldPage.test.js

# HarmonyPage tests
npm test -- src/pages/HarmonyPage.test.js

# ReconnectPage tests
npm test -- src/pages/ReconnectPage.test.js

# useWebcam hook tests
npm test -- src/hooks/useWebcam.test.js

# useWebSocket hook tests
npm test -- src/hooks/useWebSocket.test.js

# Integration tests
npm test -- src/tests/integration/StateManagement.integration.test.js
```

## Test Coverage

The test suite aims for comprehensive coverage of:

- **Component Rendering**: All components render correctly with various prop combinations
- **State Management**: State is properly managed and persisted across transitions
- **Prop Passing**: Props are correctly passed from parent to child components
- **Lifecycle Management**: Components properly initialize and cleanup resources
- **Error Handling**: All error scenarios are handled gracefully
- **User Workflows**: Complete user journeys work end-to-end

### Coverage Targets

- **Lines**: 80%+
- **Functions**: 80%+
- **Branches**: 75%+
- **Statements**: 80%+

## Test Structure

### Mocking Strategy

The tests use comprehensive mocking to isolate components and test specific functionality:

- **Hooks**: `useWebcam` and `useWebSocket` are mocked with configurable return values
- **Components**: Module components are mocked to focus on prop passing and state management
- **WebSocket**: Mock WebSocket implementation for testing connection scenarios
- **MediaDevices**: Mock `navigator.mediaDevices` for webcam testing

### Test Patterns

1. **Arrange**: Set up mocks and initial state
2. **Act**: Trigger user interactions or state changes
3. **Assert**: Verify expected behavior and state changes

### Async Testing

Many tests involve async operations (webcam initialization, WebSocket connections). The test suite
uses:

- `act()` for React state updates
- `waitFor()` for async assertions
- `jest.advanceTimersByTime()` for timer-based operations

## Key Test Scenarios

### Camera Lifecycle Management

1. **Initialization**: Camera starts automatically on page mount
2. **Cleanup**: Camera stops properly on page unmount
3. **Error Handling**: Permission denied, device not found, device in use
4. **Recovery**: Successful retry after initial failure
5. **Multiple Cycles**: Repeated start/stop operations

### State Persistence

1. **View Transitions**: State maintained during navigation
2. **Component Remounting**: State preserved across remounts
3. **Error Recovery**: State restored after error resolution
4. **Cross-Component**: Consistent state across different components

### Prop Passing

1. **Webcam Props**: Stream, active state, error state passed correctly
2. **WebSocket Props**: Connection state, message handler passed correctly
3. **Legacy Support**: Backward compatibility with existing prop interfaces
4. **Conditional Props**: Props passed based on component state

### Error Scenarios

1. **Camera Permissions**: Denied, not found, in use by other app
2. **WebSocket Errors**: Connection failed, message send failed, reconnection
3. **Component Errors**: Graceful handling of component failures
4. **Resource Cleanup**: Proper cleanup even when errors occur

## Debugging Tests

### Common Issues

1. **Async Timing**: Use `act()` and `waitFor()` for async operations
2. **Mock Configuration**: Ensure mocks return expected values
3. **State Updates**: Verify React state updates are properly wrapped
4. **Cleanup**: Check that cleanup functions are called correctly

### Debug Commands

```bash
# Run tests with verbose output
npm test -- --verbose src/pages/ASLWorldPage.test.js

# Run tests with coverage
npm test -- --coverage src/hooks/useWebcam.test.js

# Run tests in watch mode
npm test -- --watch src/tests/integration/StateManagement.integration.test.js
```

## Continuous Integration

The state management tests are integrated into the CI pipeline:

1. **Pre-commit**: Basic unit tests run on commit
2. **Pull Request**: Full test suite runs on PR creation
3. **Deployment**: All tests must pass before deployment

## Maintenance

### Adding New Tests

When adding new state management functionality:

1. Add unit tests for individual components/hooks
2. Add integration tests for complete workflows
3. Update coverage thresholds if needed
4. Document new test scenarios in this file

### Updating Existing Tests

When modifying existing functionality:

1. Update affected unit tests
2. Verify integration tests still pass
3. Update mocks if interfaces change
4. Maintain backward compatibility where possible

## Performance Considerations

The test suite is optimized for:

- **Fast Execution**: Mocks minimize external dependencies
- **Parallel Execution**: Tests can run in parallel where possible
- **Resource Efficiency**: Proper cleanup prevents memory leaks
- **Deterministic Results**: Tests produce consistent results across runs

## Related Documentation

- [Video Camera Fixes Requirements](../../specs/storysign-video-camera-fixes/requirements.md)
- [Video Camera Fixes Design](../../specs/storysign-video-camera-fixes/design.md)
- [Video Camera Fixes Tasks](../../specs/storysign-video-camera-fixes/tasks.md)
- [Frontend Development Guidelines](../../docs/frontend-development.md)
- [Testing Best Practices](../../docs/testing-guidelines.md)
