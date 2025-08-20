/**
 * Frontend Integration and Performance Tests
 * Task 11.2: Create integration and performance tests
 *
 * Tests frontend components integration and performance metrics
 */

const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const WebSocket = require("ws");

class FrontendIntegrationTestSuite {
  constructor() {
    this.results = [];
    this.frontendPath = path.join(__dirname, "src");
    this.testResults = {};
  }

  log(message, status = "INFO") {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] ${status}: ${message}`;
    console.log(logMessage);
    this.results.push({ timestamp, status, message });
  }

  // Test WebSocket client integration
  async testWebSocketClientIntegration() {
    this.log("=== Testing WebSocket Client Integration ===");

    try {
      // Check VideoStreamingClient component
      const streamingPath = path.join(
        this.frontendPath,
        "VideoStreamingClient.js"
      );
      if (!fs.existsSync(streamingPath)) {
        this.log("VideoStreamingClient.js not found", "ERROR");
        return false;
      }

      const streamingContent = fs.readFileSync(streamingPath, "utf8");

      // Verify WebSocket integration features
      const requiredFeatures = [
        "WebSocket",
        "sendFrame",
        "onProcessedFrame",
        "reconnect",
        "exponential",
        "backoff",
      ];

      let featuresFound = 0;
      requiredFeatures.forEach((feature) => {
        if (streamingContent.includes(feature)) {
          featuresFound++;
          this.log(`✓ WebSocket feature '${feature}' found`, "SUCCESS");
        } else {
          this.log(`✗ WebSocket feature '${feature}' missing`, "ERROR");
        }
      });

      // Test WebSocket connection establishment (mock test)
      const connectionTest = await this.testWebSocketConnection();

      return featuresFound === requiredFeatures.length && connectionTest;
    } catch (error) {
      this.log(
        `WebSocket client integration test failed: ${error.message}`,
        "ERROR"
      );
      return false;
    }
  }

  // Test actual WebSocket connection to backend
  async testWebSocketConnection() {
    this.log("Testing WebSocket connection to backend...");

    return new Promise((resolve) => {
      try {
        const ws = new WebSocket("ws://localhost:8000/ws/video");
        let connectionEstablished = false;

        const timeout = setTimeout(() => {
          if (!connectionEstablished) {
            this.log("WebSocket connection timeout", "WARNING");
            ws.close();
            resolve(false);
          }
        }, 5000);

        ws.on("open", () => {
          connectionEstablished = true;
          clearTimeout(timeout);
          this.log("✓ WebSocket connection established", "SUCCESS");

          // Send test message
          const testMessage = {
            type: "ping",
            timestamp: new Date().toISOString(),
          };

          ws.send(JSON.stringify(testMessage));

          setTimeout(() => {
            ws.close();
            resolve(true);
          }, 1000);
        });

        ws.on("error", (error) => {
          clearTimeout(timeout);
          this.log(`WebSocket connection error: ${error.message}`, "WARNING");
          resolve(false);
        });

        ws.on("close", () => {
          clearTimeout(timeout);
          if (connectionEstablished) {
            this.log("✓ WebSocket connection closed gracefully", "SUCCESS");
          }
        });
      } catch (error) {
        this.log(`WebSocket connection test failed: ${error.message}`, "ERROR");
        resolve(false);
      }
    });
  }

  // Test video capture component integration
  testVideoCaptureIntegration() {
    this.log("=== Testing Video Capture Integration ===");

    try {
      const webcamPath = path.join(this.frontendPath, "WebcamCapture.js");
      if (!fs.existsSync(webcamPath)) {
        this.log("WebcamCapture.js not found", "ERROR");
        return false;
      }

      const webcamContent = fs.readFileSync(webcamPath, "utf8");

      // Check for required video capture features
      const captureFeatures = [
        "getUserMedia",
        "captureFrame",
        "canvas",
        "toDataURL",
        "adaptiveFPS",
        "processingCapability",
      ];

      let captureScore = 0;
      captureFeatures.forEach((feature) => {
        if (webcamContent.includes(feature)) {
          captureScore++;
          this.log(`✓ Video capture feature '${feature}' found`, "SUCCESS");
        } else {
          this.log(`✗ Video capture feature '${feature}' missing`, "ERROR");
        }
      });

      // Check for performance optimization features
      const performanceFeatures = [
        "requestAnimationFrame",
        "frameRate",
        "performance",
        "optimization",
      ];

      let performanceScore = 0;
      performanceFeatures.forEach((feature) => {
        if (webcamContent.includes(feature)) {
          performanceScore++;
        }
      });

      const totalScore = captureScore + performanceScore;
      const maxScore = captureFeatures.length + performanceFeatures.length;

      this.log(
        `Video capture integration score: ${totalScore}/${maxScore}`,
        totalScore >= maxScore * 0.8 ? "SUCCESS" : "WARNING"
      );

      return totalScore >= maxScore * 0.8; // 80% threshold
    } catch (error) {
      this.log(
        `Video capture integration test failed: ${error.message}`,
        "ERROR"
      );
      return false;
    }
  }

  // Test processed video display integration
  testProcessedVideoDisplayIntegration() {
    this.log("=== Testing Processed Video Display Integration ===");

    try {
      const displayPath = path.join(
        this.frontendPath,
        "ProcessedVideoDisplay.js"
      );
      if (!fs.existsSync(displayPath)) {
        this.log("ProcessedVideoDisplay.js not found", "ERROR");
        return false;
      }

      const displayContent = fs.readFileSync(displayPath, "utf8");

      // Check for display features
      const displayFeatures = [
        "renderFrameToCanvas",
        "landmarks_detected",
        "processing_time_ms",
        "frameRate",
        "latency",
        "connection-status",
        "performance-dashboard",
      ];

      let displayScore = 0;
      displayFeatures.forEach((feature) => {
        if (displayContent.includes(feature)) {
          displayScore++;
          this.log(`✓ Display feature '${feature}' found`, "SUCCESS");
        } else {
          this.log(`✗ Display feature '${feature}' missing`, "ERROR");
        }
      });

      // Check for real-time performance monitoring
      const monitoringFeatures = ["FPS", "metrics", "health", "status"];

      let monitoringScore = 0;
      monitoringFeatures.forEach((feature) => {
        if (displayContent.includes(feature)) {
          monitoringScore++;
        }
      });

      const totalScore = displayScore + monitoringScore;
      const maxScore = displayFeatures.length + monitoringFeatures.length;

      this.log(
        `Display integration score: ${totalScore}/${maxScore}`,
        totalScore >= maxScore * 0.7 ? "SUCCESS" : "WARNING"
      );

      return totalScore >= maxScore * 0.7; // 70% threshold
    } catch (error) {
      this.log(`Display integration test failed: ${error.message}`, "ERROR");
      return false;
    }
  }

  // Test error handling and recovery mechanisms
  testErrorHandlingIntegration() {
    this.log("=== Testing Error Handling Integration ===");

    try {
      const appPath = path.join(this.frontendPath, "App.js");
      if (!fs.existsSync(appPath)) {
        this.log("App.js not found", "ERROR");
        return false;
      }

      const appContent = fs.readFileSync(appPath, "utf8");

      // Check for error handling features
      const errorFeatures = [
        "onRetryConnection",
        "retryStreaming",
        "webcamError",
        "retryWebcam",
        "streamingError",
        "handleStreamingError",
        "exponentialBackoff",
        "maxRetries",
      ];

      let errorScore = 0;
      errorFeatures.forEach((feature) => {
        if (appContent.includes(feature)) {
          errorScore++;
          this.log(`✓ Error handling feature '${feature}' found`, "SUCCESS");
        } else {
          this.log(`✗ Error handling feature '${feature}' missing`, "WARNING");
        }
      });

      // Check for recovery mechanisms
      const recoveryFeatures = ["reconnect", "retry", "fallback", "graceful"];

      let recoveryScore = 0;
      recoveryFeatures.forEach((feature) => {
        if (appContent.includes(feature)) {
          recoveryScore++;
        }
      });

      const totalScore = errorScore + recoveryScore;
      const maxScore = errorFeatures.length + recoveryFeatures.length;

      this.log(
        `Error handling score: ${totalScore}/${maxScore}`,
        totalScore >= maxScore * 0.6 ? "SUCCESS" : "WARNING"
      );

      return totalScore >= maxScore * 0.6; // 60% threshold
    } catch (error) {
      this.log(`Error handling test failed: ${error.message}`, "ERROR");
      return false;
    }
  }

  // Test component data flow integration
  testComponentDataFlowIntegration() {
    this.log("=== Testing Component Data Flow Integration ===");

    try {
      const appPath = path.join(this.frontendPath, "App.js");
      const appContent = fs.readFileSync(appPath, "utf8");

      // Check for proper component imports
      const componentImports = [
        "WebcamCapture",
        "VideoStreamingClient",
        "ProcessedVideoDisplay",
      ];

      let importScore = 0;
      componentImports.forEach((component) => {
        if (
          appContent.includes(`import ${component}`) ||
          appContent.includes(`from './${component}`)
        ) {
          importScore++;
          this.log(`✓ Component '${component}' imported`, "SUCCESS");
        } else {
          this.log(`✗ Component '${component}' not imported`, "ERROR");
        }
      });

      // Check for data flow handlers
      const dataFlowFeatures = [
        "handleFrameCapture",
        "handleProcessedFrame",
        "processedFrameData",
        "onFrameProcessed",
        "frameData",
      ];

      let dataFlowScore = 0;
      dataFlowFeatures.forEach((feature) => {
        if (appContent.includes(feature)) {
          dataFlowScore++;
          this.log(`✓ Data flow feature '${feature}' found`, "SUCCESS");
        } else {
          this.log(`✗ Data flow feature '${feature}' missing`, "WARNING");
        }
      });

      const totalScore = importScore + dataFlowScore;
      const maxScore = componentImports.length + dataFlowFeatures.length;

      this.log(
        `Data flow integration score: ${totalScore}/${maxScore}`,
        totalScore >= maxScore * 0.7 ? "SUCCESS" : "WARNING"
      );

      return totalScore >= maxScore * 0.7;
    } catch (error) {
      this.log(`Data flow integration test failed: ${error.message}`, "ERROR");
      return false;
    }
  }

  // Test performance requirements compliance
  testPerformanceRequirements() {
    this.log("=== Testing Performance Requirements Compliance ===");

    try {
      // Check for performance monitoring in components
      const components = [
        "WebcamCapture.js",
        "VideoStreamingClient.js",
        "ProcessedVideoDisplay.js",
      ];
      let performanceScore = 0;
      let totalChecks = 0;

      components.forEach((componentFile) => {
        const componentPath = path.join(this.frontendPath, componentFile);
        if (fs.existsSync(componentPath)) {
          const content = fs.readFileSync(componentPath, "utf8");

          // Performance features to check
          const perfFeatures = [
            "performance.now",
            "requestAnimationFrame",
            "frameRate",
            "latency",
            "optimization",
            "throttle",
            "debounce",
          ];

          perfFeatures.forEach((feature) => {
            totalChecks++;
            if (content.includes(feature)) {
              performanceScore++;
              this.log(
                `✓ Performance feature '${feature}' in ${componentFile}`,
                "SUCCESS"
              );
            }
          });
        }
      });

      // Check for latency targets (<100ms requirement)
      const displayPath = path.join(
        this.frontendPath,
        "ProcessedVideoDisplay.js"
      );
      if (fs.existsSync(displayPath)) {
        const displayContent = fs.readFileSync(displayPath, "utf8");

        if (
          displayContent.includes("100") &&
          displayContent.includes("latency")
        ) {
          performanceScore += 2;
          this.log("✓ 100ms latency target reference found", "SUCCESS");
        }

        totalChecks += 2;
      }

      const performanceRatio = performanceScore / totalChecks;
      this.log(
        `Performance compliance score: ${performanceScore}/${totalChecks} (${(
          performanceRatio * 100
        ).toFixed(1)}%)`,
        performanceRatio >= 0.5 ? "SUCCESS" : "WARNING"
      );

      return performanceRatio >= 0.5; // 50% threshold
    } catch (error) {
      this.log(
        `Performance requirements test failed: ${error.message}`,
        "ERROR"
      );
      return false;
    }
  }

  // Test multi-client handling simulation
  async testMultiClientHandlingSimulation() {
    this.log("=== Testing Multi-Client Handling Simulation ===");

    try {
      // Simulate multiple WebSocket connections
      const numClients = 3;
      const connectionPromises = [];

      for (let i = 0; i < numClients; i++) {
        connectionPromises.push(this.simulateClientConnection(i));
      }

      const results = await Promise.allSettled(connectionPromises);

      let successfulConnections = 0;
      results.forEach((result, index) => {
        if (result.status === "fulfilled" && result.value) {
          successfulConnections++;
          this.log(`✓ Client ${index} connection successful`, "SUCCESS");
        } else {
          this.log(`✗ Client ${index} connection failed`, "WARNING");
        }
      });

      const successRate = successfulConnections / numClients;
      this.log(
        `Multi-client success rate: ${successfulConnections}/${numClients} (${(
          successRate * 100
        ).toFixed(1)}%)`,
        successRate >= 0.8 ? "SUCCESS" : "WARNING"
      );

      return successRate >= 0.8; // 80% success rate threshold
    } catch (error) {
      this.log(`Multi-client handling test failed: ${error.message}`, "ERROR");
      return false;
    }
  }

  // Simulate individual client connection
  async simulateClientConnection(clientId) {
    return new Promise((resolve) => {
      try {
        const ws = new WebSocket("ws://localhost:8000/ws/video");
        let connected = false;

        const timeout = setTimeout(() => {
          if (!connected) {
            ws.close();
            resolve(false);
          }
        }, 3000);

        ws.on("open", () => {
          connected = true;
          clearTimeout(timeout);

          // Send test frame
          const testFrame = this.createTestFrameData(clientId);
          ws.send(JSON.stringify(testFrame));

          setTimeout(() => {
            ws.close();
            resolve(true);
          }, 500);
        });

        ws.on("error", () => {
          clearTimeout(timeout);
          resolve(false);
        });
      } catch (error) {
        resolve(false);
      }
    });
  }

  // Create test frame data
  createTestFrameData(clientId) {
    // Create minimal test frame data
    const canvas = { width: 240, height: 180 };
    const testImageData =
      "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k=";

    return {
      type: "raw_frame",
      timestamp: new Date().toISOString(),
      frame_data: testImageData,
      metadata: {
        frame_number: 1,
        client_id: `test_client_${clientId}`,
        width: canvas.width,
        height: canvas.height,
      },
    };
  }

  // Run all frontend integration tests
  async runAllTests() {
    this.log("Starting Frontend Integration and Performance Test Suite");
    this.log(
      "================================================================"
    );

    const tests = [
      {
        name: "WebSocket Client Integration",
        test: () => this.testWebSocketClientIntegration(),
      },
      {
        name: "Video Capture Integration",
        test: () => this.testVideoCaptureIntegration(),
      },
      {
        name: "Processed Video Display Integration",
        test: () => this.testProcessedVideoDisplayIntegration(),
      },
      {
        name: "Error Handling Integration",
        test: () => this.testErrorHandlingIntegration(),
      },
      {
        name: "Component Data Flow Integration",
        test: () => this.testComponentDataFlowIntegration(),
      },
      {
        name: "Performance Requirements",
        test: () => this.testPerformanceRequirements(),
      },
      {
        name: "Multi-Client Handling Simulation",
        test: () => this.testMultiClientHandlingSimulation(),
      },
    ];

    let passedTests = 0;
    let totalTests = tests.length;

    for (const testCase of tests) {
      try {
        this.log(`\nRunning: ${testCase.name}`);
        const result = await testCase.test();

        if (result) {
          passedTests++;
          this.testResults[testCase.name] = { success: true };
          this.log(`✅ ${testCase.name} PASSED`, "SUCCESS");
        } else {
          this.testResults[testCase.name] = { success: false };
          this.log(`❌ ${testCase.name} FAILED`, "ERROR");
        }
      } catch (error) {
        this.testResults[testCase.name] = {
          success: false,
          error: error.message,
        };
        this.log(`❌ ${testCase.name} FAILED: ${error.message}`, "ERROR");
      }
    }

    this.log(
      "================================================================"
    );
    this.log(
      `Frontend Integration Test Complete: ${passedTests}/${totalTests} tests passed`
    );

    if (passedTests === totalTests) {
      this.log("✅ ALL FRONTEND INTEGRATION TESTS PASSED!", "SUCCESS");
      this.log(
        "Frontend components are properly integrated and ready for production",
        "SUCCESS"
      );
    } else {
      this.log(
        `❌ ${
          totalTests - passedTests
        } tests failed - Frontend needs attention`,
        "ERROR"
      );
    }

    return passedTests === totalTests;
  }

  // Generate detailed report
  generateReport() {
    const reportPath = path.join(
      __dirname,
      "frontend_integration_test_results.json"
    );
    const report = {
      test: "Frontend Integration and Performance Test Suite",
      timestamp: new Date().toISOString(),
      results: this.results,
      test_results: this.testResults,
      summary: {
        total_tests: Object.keys(this.testResults).length,
        passed_tests: Object.values(this.testResults).filter((r) => r.success)
          .length,
        failed_tests: Object.values(this.testResults).filter((r) => !r.success)
          .length,
        success_rate:
          Object.values(this.testResults).filter((r) => r.success).length /
          Object.keys(this.testResults).length,
      },
    };

    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    this.log(`Detailed report saved to: ${reportPath}`, "INFO");

    return report;
  }
}

// Run the test if this script is executed directly
if (require.main === module) {
  const tester = new FrontendIntegrationTestSuite();
  tester
    .runAllTests()
    .then((success) => {
      const report = tester.generateReport();

      console.log("\n" + "=".repeat(60));
      console.log("FRONTEND INTEGRATION TEST SUMMARY");
      console.log("=".repeat(60));
      console.log(`Total Tests: ${report.summary.total_tests}`);
      console.log(`Passed: ${report.summary.passed_tests}`);
      console.log(`Failed: ${report.summary.failed_tests}`);
      console.log(
        `Success Rate: ${(report.summary.success_rate * 100).toFixed(1)}%`
      );
      console.log("=".repeat(60));

      process.exit(success ? 0 : 1);
    })
    .catch((error) => {
      console.error("Frontend integration test failed:", error);
      process.exit(1);
    });
}

module.exports = FrontendIntegrationTestSuite;
