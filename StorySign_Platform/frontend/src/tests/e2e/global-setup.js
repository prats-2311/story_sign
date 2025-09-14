/**
 * Global Setup for E2E Tests
 *
 * Initializes test environment and prepares for E2E testing
 */

const fs = require("fs");
const path = require("path");

module.exports = async () => {
  console.log("🔧 Setting up E2E test environment...");

  // Create test results directory
  const testResultsDir = path.join(__dirname, "../../../test-results/e2e");
  if (!fs.existsSync(testResultsDir)) {
    fs.mkdirSync(testResultsDir, { recursive: true });
  }

  // Set up environment variables for testing
  process.env.NODE_ENV = "test";
  process.env.REACT_APP_API_URL = "http://localhost:8000";
  process.env.REACT_APP_WS_URL = "ws://localhost:8000/ws";
  process.env.REACT_APP_ENVIRONMENT = "test";

  // Initialize performance monitoring
  global.testStartTime = Date.now();
  global.performanceMetrics = {
    videoProcessing: [],
    websocketLatency: [],
    apiResponseTimes: [],
    memoryUsage: [],
  };

  // Set up test database (if needed)
  // This would typically involve setting up a test database
  // and running migrations for integration tests

  // Mock external services
  setupMockServices();

  console.log("✅ E2E test environment setup complete");
};

function setupMockServices() {
  // Mock external API endpoints that might be called during tests
  const mockEndpoints = {
    "/health": {
      method: "GET",
      response: { message: "Backend connected successfully!" },
    },
    "/api/v1/auth/login": {
      method: "POST",
      response: {
        user: { id: 1, email: "test@example.com", username: "testuser" },
        token: "mock-jwt-token",
      },
    },
    "/api/v1/auth/register": {
      method: "POST",
      response: { success: true, message: "Registration successful" },
    },
    "/api/asl-world/story/recognize_and_generate": {
      method: "POST",
      response: {
        success: true,
        stories: [
          {
            id: 1,
            title: "Test Story",
            sentences: ["Test sentence 1", "Test sentence 2"],
            object_detected: "test_object",
          },
        ],
      },
    },
    "/api/v1/harmony/sessions": {
      method: "POST",
      response: { success: true, session_id: "harmony_test_123" },
    },
    "/api/v1/reconnect/sessions": {
      method: "POST",
      response: { success: true, session_id: "reconnect_test_123" },
    },
  };

  // Store mock endpoints for use in tests
  global.mockEndpoints = mockEndpoints;
}
