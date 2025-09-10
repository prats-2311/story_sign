# End-to-End Testing Suite

This directory contains comprehensive end-to-end tests for the StorySign Platform, covering all user journeys and performance requirements.

## Overview

The E2E testing suite validates:

- **User Journey Tests**: Complete workflows from registration to module usage
- **Performance Tests**: Video processing, WebSocket communication, and API response times
- **Integration Tests**: Database operations and cross-module functionality
- **Error Handling**: Recovery scenarios and graceful degradation

## Test Structure

```
src/tests/e2e/
├── user-journeys.test.js          # Complete user workflow tests
├── performance-integration.test.js # Performance and integration tests
├── test-runner.js                 # Comprehensive test execution and reporting
├── jest.config.js                 # Jest configuration for E2E tests
├── setup.js                       # Global test setup and utilities
├── performance-reporter.js        # Custom performance monitoring reporter
├── global-setup.js               # Environment initialization
├── global-teardown.js            # Environment cleanup
└── README.md                      # This file
```

## Running Tests

### Individual Test Suites

```bash
# Run all E2E tests
npm run test:e2e

# Run E2E tests in watch mode
npm run test:e2e:watch

# Run E2E tests with coverage
npm run test:e2e:coverage

# Run comprehensive test suite with performance monitoring
npm run test:e2e:performance
```

### Complete Test Suite

```bash
# Run all tests (unit, accessibility, and E2E)
npm run test:all
```

## Test Categories

### 1. User Journey Tests (`user-journeys.test.js`)

#### Registration and Login Workflow

- ✅ Complete new user registration flow
- ✅ User login flow and dashboard access
- ✅ Login validation and error handling
- ✅ Authentication state persistence

#### ASL World Story Generation and Practice

- ✅ Complete story generation workflow
- ✅ Story selection and practice session
- ✅ Practice controls and navigation
- ✅ Error handling for story generation failures

#### Harmony Facial Expression Practice

- ✅ Emotion practice session setup
- ✅ Real-time facial expression detection
- ✅ Session data persistence
- ✅ Progress tracking and metrics

#### Reconnect Therapeutic Movement Analysis

- ✅ Exercise selection and setup
- ✅ Movement analysis and tracking
- ✅ Therapy session management
- ✅ Progress dashboard and analytics

#### Cross-Module Navigation

- ✅ Seamless navigation between modules
- ✅ Authentication state maintenance
- ✅ Logout and redirect handling

### 2. Performance and Integration Tests (`performance-integration.test.js`)

#### Video Processing Performance

- ⚡ Latency validation (<100ms requirement)
- ⚡ Frame rate consistency (30 FPS target)
- ⚡ High-resolution processing efficiency
- ⚡ Memory usage monitoring

#### WebSocket Communication Reliability

- 🔌 Connection establishment time
- 🔌 Message throughput under load
- 🔌 Connection recovery and reconnection
- 🔌 Error handling and graceful degradation

#### Database Integration

- 💾 ASL World session data persistence
- 💾 Harmony emotion data storage/retrieval
- 💾 Reconnect therapy analytics queries
- 💾 Concurrent operation performance

#### API Integration

- 🌐 Frontend-backend communication latency
- 🌐 Rate limiting and throttling
- 🌐 Error response handling
- 🌐 Authentication and authorization

## Performance Benchmarks

### Target Performance Metrics

| Metric                   | Target | Warning | Critical |
| ------------------------ | ------ | ------- | -------- |
| Video Processing Latency | <80ms  | >80ms   | >100ms   |
| WebSocket Latency        | <200ms | >200ms  | >500ms   |
| API Response Time        | <300ms | >300ms  | >1000ms  |
| Memory Usage             | <50MB  | >50MB   | >100MB   |
| Frame Rate               | 30 FPS | <25 FPS | <20 FPS  |

### Performance Monitoring

The test suite includes comprehensive performance monitoring:

- **Real-time Metrics**: Latency, throughput, memory usage
- **Statistical Analysis**: Average, P95, P99 percentiles
- **Trend Analysis**: Performance over time
- **Recommendations**: Automated performance improvement suggestions

## Test Reports

### Generated Reports

1. **JSON Report**: Detailed test results and metrics

   - Location: `test-results/e2e/e2e-test-report.json`
   - Contains: Test results, performance data, error details

2. **HTML Report**: Interactive visual report

   - Location: `test-results/e2e/e2e-test-report.html`
   - Features: Charts, metrics, recommendations

3. **Performance Report**: Specialized performance analysis
   - Location: `test-results/e2e/performance-report.json`
   - Includes: Benchmarks, trends, optimization suggestions

### Report Features

- **Visual Dashboards**: Interactive charts and graphs
- **Performance Trends**: Historical performance tracking
- **Error Analysis**: Detailed failure investigation
- **Recommendations**: Automated optimization suggestions
- **Accessibility**: Screen reader compatible reports

## Test Configuration

### Environment Variables

```bash
# API Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws
REACT_APP_ENVIRONMENT=test

# Test Configuration
NODE_ENV=test
VERBOSE_LOGGING=true
```

### Jest Configuration

The E2E tests use a specialized Jest configuration:

- **Extended Timeout**: 30 seconds for complex workflows
- **Custom Reporters**: Performance monitoring and detailed reporting
- **Mock Setup**: Comprehensive mocking of external dependencies
- **Coverage**: Focused on integration points and user flows

## Mock Services

### WebSocket Mocking

- Simulates real-time video processing
- Configurable latency and throughput
- Connection failure simulation
- Message ordering and reliability testing

### API Mocking

- RESTful endpoint simulation
- Configurable response times
- Error scenario testing
- Rate limiting simulation

### Video Processing Mocking

- MediaPipe landmark simulation
- Frame processing timing
- Memory usage patterns
- Hardware acceleration simulation

## Debugging and Troubleshooting

### Common Issues

1. **Test Timeouts**

   - Increase timeout in `jest.config.js`
   - Check for unresolved promises
   - Verify mock service responses

2. **Performance Failures**

   - Review performance thresholds
   - Check system resources during testing
   - Analyze performance report recommendations

3. **WebSocket Connection Issues**
   - Verify WebSocket mock configuration
   - Check connection timing and retry logic
   - Review error handling implementation

### Debug Mode

Enable verbose logging for detailed test execution:

```bash
VERBOSE_LOGGING=true npm run test:e2e
```

### Performance Profiling

Use the performance reporter for detailed analysis:

```bash
npm run test:e2e:performance
```

## Continuous Integration

### CI/CD Integration

The E2E tests are designed for CI/CD environments:

- **Parallel Execution**: Tests can run in parallel workers
- **Artifact Generation**: Reports and coverage data
- **Failure Analysis**: Detailed error reporting
- **Performance Regression**: Automated performance validation

### GitHub Actions Example

```yaml
- name: Run E2E Tests
  run: |
    npm run test:e2e:coverage

- name: Upload Test Results
  uses: actions/upload-artifact@v2
  with:
    name: e2e-test-results
    path: test-results/e2e/
```

## Contributing

### Adding New Tests

1. **User Journey Tests**: Add to `user-journeys.test.js`
2. **Performance Tests**: Add to `performance-integration.test.js`
3. **Test Utilities**: Extend `setup.js` with new helpers
4. **Mock Services**: Update mock configurations as needed

### Test Guidelines

- **Descriptive Names**: Use clear, descriptive test names
- **Performance Aware**: Include performance assertions
- **Error Scenarios**: Test both success and failure paths
- **Accessibility**: Ensure tests work with assistive technologies
- **Documentation**: Update this README for new test categories

### Performance Considerations

- **Resource Cleanup**: Always clean up resources after tests
- **Memory Management**: Monitor memory usage in long-running tests
- **Concurrent Safety**: Ensure tests can run in parallel
- **Deterministic**: Avoid flaky tests with proper synchronization

## Requirements Mapping

This test suite fulfills the following requirements:

- **Requirement 9.1**: Complete user journey tests for all modules
- **Requirement 9.2**: Performance validation and integration testing
- **Requirement 9.3**: Video processing performance (<100ms latency)
- **Requirement 9.4**: WebSocket communication reliability
- **Requirement 9.5**: Database integration across all modules
- **Requirement 9.6**: Error handling and recovery scenarios

## Future Enhancements

- **Visual Regression Testing**: Screenshot comparison
- **Load Testing**: Multi-user concurrent scenarios
- **Mobile Testing**: Touch and gesture interactions
- **Accessibility Automation**: Enhanced a11y validation
- **Real Device Testing**: Hardware-specific validation
