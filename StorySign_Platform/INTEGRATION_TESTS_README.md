# Integration and Performance Tests

This directory contains comprehensive integration and performance tests for the StorySign ASL Platform, implementing **Task 11.2: Create integration and performance tests**.

## Test Suite Overview

The integration and performance test suite includes:

1. **End-to-end WebSocket communication tests**
2. **Video pipeline latency and quality metric validation**
3. **Error scenario simulation and recovery testing**
4. **Multi-client connection handling and isolation tests**
5. **Performance benchmarks for <100ms end-to-end processing target**

## Test Files

### Backend Tests

- `backend/test_integration_performance.py` - Comprehensive backend integration and performance tests
- `test_multi_client_stress.py` - Multi-client stress testing and isolation validation
- `test_integration_simple.py` - Simple integration tests (no OpenCV dependencies)

### Frontend Tests

- `frontend/test_integration_performance.js` - Frontend component integration tests

### Test Runners

- `run_integration_performance_tests.py` - Comprehensive test runner for all test suites
- `test_integration_quick.py` - Quick verification of test framework

## Requirements Covered

The test suite validates the following requirements from the specification:

### Requirement 1.5 (Real-time Performance)

- Tests maintain real-time performance with minimal latency
- Validates <100ms end-to-end processing target
- Measures frame rate and processing efficiency

### Requirement 4.6 (Real-time Data Transfer)

- Tests WebSocket message formatting and streaming
- Validates frame data transmission with minimal delay
- Measures end-to-end latency from capture to display

### Requirement 3.4 (Multi-client Support)

- Tests multiple WebSocket connections simultaneously
- Validates client session isolation
- Measures performance degradation under load

## Running the Tests

### Prerequisites

1. **Backend Server Running**

   ```bash
   cd backend
   python main.py
   ```

2. **Dependencies Installed**
   ```bash
   pip install -r requirements.txt
   ```

### Quick Test (Recommended First)

Run the simple integration test that doesn't require OpenCV:

```bash
python test_integration_simple.py
```

This will test:

- WebSocket connection establishment
- Basic frame processing
- Multiple message handling
- Error handling and recovery

### Comprehensive Test Suite

Run all integration and performance tests:

```bash
python run_integration_performance_tests.py
```

This will execute:

- Backend integration and performance tests
- Frontend integration tests
- Multi-client stress tests
- Existing test suites for comparison

### Individual Test Suites

#### Backend Integration Tests

```bash
cd backend
python test_integration_performance.py
```

#### Frontend Integration Tests

```bash
cd frontend
node test_integration_performance.js
```

#### Multi-Client Stress Tests

```bash
python test_multi_client_stress.py
```

## Test Results and Metrics

### Performance Targets

- **Latency Target**: <100ms end-to-end processing
- **Throughput Target**: 20+ FPS sustained processing
- **Success Rate Target**: >90% frame processing success
- **Multi-client Target**: 3+ concurrent clients without degradation

### Key Metrics Measured

1. **End-to-End Latency**

   - Frame capture to processed frame display
   - Target: <100ms for 90% of frames

2. **Processing Performance**

   - MediaPipe processing time
   - Frame encoding/decoding time
   - WebSocket transmission time

3. **System Resources**

   - CPU usage during processing
   - Memory consumption
   - Connection handling efficiency

4. **Error Handling**
   - Recovery from connection failures
   - Graceful degradation on processing errors
   - Client isolation during failures

### Test Reports

Test results are saved in JSON format:

- `integration_performance_test_results.json` - Backend test results
- `frontend_integration_test_results.json` - Frontend test results
- `multi_client_stress_test_results.json` - Stress test results
- `comprehensive_test_results_[timestamp].json` - Complete test suite results

## Test Architecture

### Backend Integration Tests (`test_integration_performance.py`)

```python
class IntegrationPerformanceTestSuite:
    - test_websocket_connection_establishment()
    - test_end_to_end_frame_processing()
    - test_video_pipeline_latency_validation()
    - test_multi_client_isolation()
    - test_error_scenario_simulation()
    - test_performance_benchmarks()
```

### Multi-Client Stress Tests (`test_multi_client_stress.py`)

```python
class MultiClientStressTest:
    - client_session() # Individual client simulation
    - monitor_system_resources() # Resource monitoring
    - run_stress_test() # Concurrent client execution
    - _analyze_stress_test_results() # Performance analysis
```

### Frontend Integration Tests (`test_integration_performance.js`)

```javascript
class FrontendIntegrationTestSuite {
    - testWebSocketClientIntegration()
    - testVideoCaptureIntegration()
    - testProcessedVideoDisplayIntegration()
    - testErrorHandlingIntegration()
    - testMultiClientHandlingSimulation()
}
```

## Troubleshooting

### Common Issues

1. **Backend Server Not Running**

   ```
   Error: Connection refused
   Solution: Start the backend server with `python backend/main.py`
   ```

2. **OpenCV/NumPy Compatibility Issues**

   ```
   Error: numpy.core.multiarray failed to import
   Solution: Use test_integration_simple.py or fix NumPy version compatibility
   ```

3. **WebSocket Connection Timeout**

   ```
   Error: WebSocket connection timeout
   Solution: Check firewall settings and ensure server is accessible on localhost:8000
   ```

4. **Performance Tests Failing**
   ```
   Error: Latency target not met
   Solution: Check system resources, reduce other processes, or adjust performance targets
   ```

### Environment Setup

For best test results:

- Close unnecessary applications
- Ensure stable network connection
- Run tests on a system with adequate resources (4GB+ RAM, modern CPU)
- Use Python 3.8+ with compatible NumPy/OpenCV versions

## Integration with CI/CD

The test suite is designed for integration with continuous integration systems:

```bash
# CI/CD Pipeline Example
python test_integration_simple.py  # Quick smoke test
if [ $? -eq 0 ]; then
    python run_integration_performance_tests.py  # Full test suite
fi
```

Exit codes:

- `0`: All tests passed
- `1`: Some tests failed
- `2`: Server not responsive

## Performance Benchmarking

The test suite includes performance benchmarking capabilities:

### Latency Benchmarks

- Single frame processing latency
- Sustained throughput latency
- Multi-client latency distribution

### Throughput Benchmarks

- Maximum sustainable FPS
- Frame processing efficiency
- Resource utilization curves

### Stress Testing

- Maximum concurrent clients
- Performance degradation curves
- Resource limit enforcement

## Future Enhancements

Planned improvements for the test suite:

1. **Automated Performance Regression Detection**
2. **Load Testing with Realistic Video Content**
3. **Network Latency Simulation**
4. **Cross-Platform Compatibility Testing**
5. **Memory Leak Detection**
6. **GPU Acceleration Testing**

## Contributing

When adding new tests:

1. Follow the existing test structure and naming conventions
2. Include comprehensive error handling and logging
3. Add performance metrics and validation
4. Update this documentation with new test descriptions
5. Ensure tests are deterministic and repeatable

## Support

For issues with the integration tests:

1. Check the troubleshooting section above
2. Review test logs and error messages
3. Verify system requirements and dependencies
4. Run the simple integration test first to isolate issues
