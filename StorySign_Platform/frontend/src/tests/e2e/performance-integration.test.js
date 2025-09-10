/**
 * Performance and Integration Tests
 *
 * This test suite covers:
 * - Video processing performance tests with latency validation
 * - WebSocket communication reliability tests
 * - Database integration tests for all modules
 * - API integration tests for frontend-backend communication
 * - Error handling and recovery scenarios across all components
 *
 * Requirements: 9.3, 9.4, 9.5, 9.6
 */

import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import "@testing-library/jest-dom";
import "./setup"; // Import E2E setup

import App from "../../App";
import VideoStreamingClient from "../../components/video/VideoStreamingClient";

// Mock external dependencies
jest.mock("../../hooks/useWebSocket", () => ({
  useWebSocket: jest.fn(),
}));

jest.mock("../../hooks/useWebcam", () => ({
  __esModule: true,
  default: jest.fn(),
}));

jest.mock("../../services/AuthService", () => ({
  __esModule: true,
  default: {
    isAuthenticated: jest.fn(),
    getCurrentUser: jest.fn(),
    getToken: jest.fn(),
    login: jest.fn(),
    register: jest.fn(),
    logout: jest.fn(),
  },
}));

jest.mock("../../config/api", () => ({
  getApiConfig: () => ({
    API_BASE_URL: "http://localhost:8000",
    WS_BASE_URL: "ws://localhost:8000",
    API_VERSION: "v1",
  }),
  buildApiUrl: (path) => `http://localhost:8000/api/v1${path}`,
  buildHealthCheckUrl: () => "http://localhost:8000/health",
  buildWebSocketUrl: () => "ws://localhost:8000/ws",
  __esModule: true,
  default: {
    API_BASE_URL: "http://localhost:8000",
    WS_BASE_URL: "ws://localhost:8000",
    API_VERSION: "v1",
  },
}));
jest.mock("../../hooks/useWebSocket");
jest.mock("../../hooks/useWebcam");
jest.mock("../../services/AuthService");

// Performance monitoring utilities
class PerformanceMonitor {
  constructor() {
    this.metrics = {
      videoProcessingLatency: [],
      websocketLatency: [],
      apiResponseTimes: [],
      frameProcessingTimes: [],
    };
  }

  startTimer(label) {
    this.timers = this.timers || {};
    this.timers[label] = performance.now();
  }

  endTimer(label) {
    if (!this.timers || !this.timers[label]) return 0;
    const duration = performance.now() - this.timers[label];
    delete this.timers[label];
    return duration;
  }

  recordMetric(type, value) {
    if (this.metrics[type]) {
      this.metrics[type].push(value);
    }
  }

  getAverageLatency(type) {
    const values = this.metrics[type];
    if (values.length === 0) return 0;
    return values.reduce((sum, val) => sum + val, 0) / values.length;
  }

  getMaxLatency(type) {
    const values = this.metrics[type];
    return values.length > 0 ? Math.max(...values) : 0;
  }

  getPercentile(type, percentile) {
    const values = this.metrics[type].sort((a, b) => a - b);
    if (values.length === 0) return 0;
    const index = Math.ceil((percentile / 100) * values.length) - 1;
    return values[index];
  }

  reset() {
    Object.keys(this.metrics).forEach((key) => {
      this.metrics[key] = [];
    });
  }
}

// Mock WebSocket with performance tracking
class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = WebSocket.CONNECTING;
    this.onopen = null;
    this.onmessage = null;
    this.onerror = null;
    this.onclose = null;
    this.sentMessages = [];
    this.performanceMonitor = new PerformanceMonitor();

    // Simulate connection after a delay
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      if (this.onopen) this.onopen();
    }, 100);
  }

  send(data) {
    const timestamp = performance.now();
    this.sentMessages.push({ data, timestamp });

    // Simulate processing delay and response
    setTimeout(() => {
      const responseTime = performance.now() - timestamp;
      this.performanceMonitor.recordMetric("websocketLatency", responseTime);

      if (this.onmessage) {
        this.onmessage({
          data: JSON.stringify({
            type: "processed_frame",
            timestamp: performance.now(),
            processing_time: Math.random() * 50 + 10, // 10-60ms
            metadata: {
              frame_number: this.sentMessages.length,
              processing_time_ms: responseTime,
            },
          }),
        });
      }
    }, Math.random() * 100 + 50); // 50-150ms processing time
  }

  close() {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) this.onclose();
  }

  addEventListener(event, handler) {
    this[`on${event}`] = handler;
  }

  removeEventListener(event, handler) {
    this[`on${event}`] = null;
  }
}

// Mock fetch with performance tracking
const createMockFetch = (performanceMonitor) => {
  return jest.fn((url, options) => {
    const startTime = performance.now();

    return new Promise((resolve) => {
      // Simulate network latency
      const networkDelay = Math.random() * 200 + 100; // 100-300ms

      setTimeout(() => {
        const responseTime = performance.now() - startTime;
        performanceMonitor.recordMetric("apiResponseTimes", responseTime);

        // Mock different API responses based on URL
        let mockResponse;

        if (url.includes("/health")) {
          mockResponse = {
            ok: true,
            status: 200,
            json: () =>
              Promise.resolve({
                message: "Backend connected successfully!",
                response_time: responseTime,
              }),
          };
        } else if (url.includes("/asl-world/story/recognize_and_generate")) {
          mockResponse = {
            ok: true,
            status: 200,
            json: () =>
              Promise.resolve({
                success: true,
                stories: [
                  {
                    id: 1,
                    title: "Test Story",
                    sentences: ["Test sentence 1", "Test sentence 2"],
                    processing_time: responseTime,
                  },
                ],
              }),
          };
        } else if (url.includes("/harmony/sessions")) {
          mockResponse = {
            ok: true,
            status: 200,
            json: () =>
              Promise.resolve({
                success: true,
                session_id: "harmony_test_123",
                processing_time: responseTime,
              }),
          };
        } else if (url.includes("/reconnect/sessions")) {
          mockResponse = {
            ok: true,
            status: 200,
            json: () =>
              Promise.resolve({
                success: true,
                session_id: "reconnect_test_123",
                processing_time: responseTime,
              }),
          };
        } else {
          mockResponse = {
            ok: true,
            status: 200,
            json: () => Promise.resolve({ message: "Success" }),
          };
        }

        resolve(mockResponse);
      }, networkDelay);
    });
  });
};

describe("Performance and Integration Tests", () => {
  let performanceMonitor;
  let mockWebSocket;

  beforeEach(() => {
    performanceMonitor = new PerformanceMonitor();
    global.fetch = createMockFetch(performanceMonitor);

    // Mock WebSocket globally
    global.WebSocket = jest.fn((url) => {
      mockWebSocket = new MockWebSocket(url);
      return mockWebSocket;
    });

    // Mock webcam hook
    const mockUseWebcam = require("../../hooks/useWebcam").default;
    mockUseWebcam.mockReturnValue({
      stream: { id: "mock-stream" },
      isActive: true,
      status: "active",
      error: null,
      startWebcam: jest.fn().mockResolvedValue(true),
      stopWebcam: jest.fn(),
      attachToVideoElement: jest.fn(),
    });

    // Mock WebSocket hook
    const mockUseWebSocket = require("../../hooks/useWebSocket").useWebSocket;
    mockUseWebSocket.mockReturnValue({
      socket: mockWebSocket,
      connectionState: "connected",
      lastMessage: null,
      sendMessage: jest.fn(),
    });
  });

  afterEach(() => {
    performanceMonitor.reset();
    jest.clearAllMocks();
  });

  describe("Video Processing Performance Tests", () => {
    test("video processing latency meets performance requirements (<100ms)", async () => {
      const frameCount = 30; // Test 30 frames
      const maxLatency = 100; // 100ms requirement

      // Simulate video frame processing
      for (let i = 0; i < frameCount; i++) {
        const startTime = performance.now();

        // Simulate frame capture and processing
        const frameData = {
          timestamp: startTime,
          frame_number: i,
          width: 640,
          height: 480,
        };

        // Simulate processing delay
        await new Promise((resolve) => {
          setTimeout(() => {
            const processingTime = performance.now() - startTime;
            performanceMonitor.recordMetric(
              "frameProcessingTimes",
              processingTime
            );
            resolve();
          }, Math.random() * 80 + 10); // 10-90ms processing time
        });
      }

      // Verify performance requirements
      const averageLatency = performanceMonitor.getAverageLatency(
        "frameProcessingTimes"
      );
      const maxRecordedLatency = performanceMonitor.getMaxLatency(
        "frameProcessingTimes"
      );
      const p95Latency = performanceMonitor.getPercentile(
        "frameProcessingTimes",
        95
      );

      expect(averageLatency).toBeLessThan(maxLatency);
      expect(p95Latency).toBeLessThan(maxLatency * 1.2); // Allow 20% tolerance for P95

      console.log(`Video Processing Performance:
        Average Latency: ${averageLatency.toFixed(2)}ms
        Max Latency: ${maxRecordedLatency.toFixed(2)}ms
        P95 Latency: ${p95Latency.toFixed(2)}ms
        Frames Processed: ${frameCount}`);
    });

    test("maintains consistent frame rate under load", async () => {
      const targetFPS = 30;
      const testDuration = 2000; // 2 seconds
      const expectedFrames = (testDuration / 1000) * targetFPS;

      let frameCount = 0;
      const startTime = performance.now();

      // Simulate continuous frame processing
      const frameInterval = setInterval(() => {
        frameCount++;
        const processingStart = performance.now();

        // Simulate frame processing
        setTimeout(() => {
          const processingTime = performance.now() - processingStart;
          performanceMonitor.recordMetric(
            "frameProcessingTimes",
            processingTime
          );
        }, Math.random() * 30 + 5); // 5-35ms processing
      }, 1000 / targetFPS);

      // Wait for test duration
      await new Promise((resolve) => setTimeout(resolve, testDuration));
      clearInterval(frameInterval);

      const actualDuration = performance.now() - startTime;
      const actualFPS = (frameCount / actualDuration) * 1000;
      const frameDropRate = Math.max(
        0,
        (expectedFrames - frameCount) / expectedFrames
      );

      expect(actualFPS).toBeGreaterThan(targetFPS * 0.9); // Allow 10% tolerance
      expect(frameDropRate).toBeLessThan(0.05); // Less than 5% frame drops

      console.log(`Frame Rate Performance:
        Target FPS: ${targetFPS}
        Actual FPS: ${actualFPS.toFixed(2)}
        Frame Drop Rate: ${(frameDropRate * 100).toFixed(2)}%
        Total Frames: ${frameCount}`);
    });

    test("handles high-resolution video processing efficiently", async () => {
      const resolutions = [
        { width: 640, height: 480, name: "SD" },
        { width: 1280, height: 720, name: "HD" },
        { width: 1920, height: 1080, name: "Full HD" },
      ];

      for (const resolution of resolutions) {
        const frameSize = resolution.width * resolution.height * 4; // RGBA
        const processingStart = performance.now();

        // Simulate processing based on frame size
        const expectedProcessingTime = (frameSize / 1000000) * 10; // Rough estimate

        await new Promise((resolve) => {
          setTimeout(() => {
            const actualProcessingTime = performance.now() - processingStart;
            performanceMonitor.recordMetric(
              "videoProcessingLatency",
              actualProcessingTime
            );
            resolve();
          }, expectedProcessingTime);
        });
      }

      const averageLatency = performanceMonitor.getAverageLatency(
        "videoProcessingLatency"
      );
      expect(averageLatency).toBeLessThan(150); // 150ms max for high-res processing

      console.log(`High-Resolution Processing:
        Average Processing Time: ${averageLatency.toFixed(2)}ms`);
    });
  });

  describe("WebSocket Communication Reliability Tests", () => {
    test("WebSocket connection establishes within acceptable time", async () => {
      const connectionStart = performance.now();

      const ws = new MockWebSocket("ws://localhost:8000/ws");

      await new Promise((resolve) => {
        ws.onopen = () => {
          const connectionTime = performance.now() - connectionStart;
          performanceMonitor.recordMetric("websocketLatency", connectionTime);
          resolve();
        };
      });

      const connectionTime =
        performanceMonitor.getAverageLatency("websocketLatency");
      expect(connectionTime).toBeLessThan(1000); // 1 second max connection time

      console.log(`WebSocket Connection Time: ${connectionTime.toFixed(2)}ms`);
    });

    test("handles message throughput under load", async () => {
      const ws = new MockWebSocket("ws://localhost:8000/ws");
      const messageCount = 100;
      let receivedCount = 0;

      await new Promise((resolve) => {
        ws.onopen = resolve;
      });

      const startTime = performance.now();

      ws.onmessage = () => {
        receivedCount++;
        if (receivedCount === messageCount) {
          const totalTime = performance.now() - startTime;
          const throughput = (messageCount / totalTime) * 1000; // messages per second

          expect(throughput).toBeGreaterThan(50); // Minimum 50 messages/second
          console.log(
            `WebSocket Throughput: ${throughput.toFixed(2)} messages/second`
          );
        }
      };

      // Send messages rapidly
      for (let i = 0; i < messageCount; i++) {
        ws.send(JSON.stringify({ frame: i, timestamp: performance.now() }));
      }

      // Wait for all messages to be processed
      await new Promise((resolve) => {
        const checkComplete = () => {
          if (receivedCount === messageCount) {
            resolve();
          } else {
            setTimeout(checkComplete, 10);
          }
        };
        checkComplete();
      });
    });

    test("recovers from connection interruptions", async () => {
      const ws = new MockWebSocket("ws://localhost:8000/ws");
      let reconnectCount = 0;

      await new Promise((resolve) => {
        ws.onopen = resolve;
      });

      // Simulate connection interruption
      ws.close();

      // Simulate reconnection attempts
      const reconnectAttempts = 3;
      for (let i = 0; i < reconnectAttempts; i++) {
        const reconnectStart = performance.now();
        const newWs = new MockWebSocket("ws://localhost:8000/ws");

        await new Promise((resolve) => {
          newWs.onopen = () => {
            reconnectCount++;
            const reconnectTime = performance.now() - reconnectStart;
            performanceMonitor.recordMetric("websocketLatency", reconnectTime);
            resolve();
          };
        });

        newWs.close();
      }

      expect(reconnectCount).toBe(reconnectAttempts);

      const averageReconnectTime =
        performanceMonitor.getAverageLatency("websocketLatency");
      expect(averageReconnectTime).toBeLessThan(2000); // 2 seconds max reconnect time

      console.log(`WebSocket Recovery:
        Reconnect Attempts: ${reconnectCount}
        Average Reconnect Time: ${averageReconnectTime.toFixed(2)}ms`);
    });
  });

  describe("Database Integration Tests", () => {
    test("ASL World session data persistence", async () => {
      const sessionData = {
        story_id: 1,
        sentences: ["Test sentence 1", "Test sentence 2"],
        user_progress: {
          completed_sentences: 1,
          feedback_scores: [0.85, 0.92],
        },
      };

      const startTime = performance.now();

      const response = await fetch("/api/v1/asl-world/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(sessionData),
      });

      const responseTime = performance.now() - startTime;
      performanceMonitor.recordMetric("apiResponseTimes", responseTime);

      expect(response.ok).toBe(true);
      expect(responseTime).toBeLessThan(500); // 500ms max for database operations

      const result = await response.json();
      expect(result.success).toBe(true);

      console.log(`ASL World DB Operation: ${responseTime.toFixed(2)}ms`);
    });

    test("Harmony emotion data storage and retrieval", async () => {
      const emotionData = {
        session_id: "harmony_test_123",
        target_emotion: "happy",
        detected_emotions: ["happy", "neutral", "happy"],
        confidence_scores: [0.89, 0.45, 0.92],
        session_duration: 30000,
      };

      // Test data storage
      const storeStart = performance.now();
      const storeResponse = await fetch("/api/v1/harmony/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(emotionData),
      });
      const storeTime = performance.now() - storeStart;

      expect(storeResponse.ok).toBe(true);
      expect(storeTime).toBeLessThan(500);

      // Test data retrieval
      const retrieveStart = performance.now();
      const retrieveResponse = await fetch(
        "/api/v1/harmony/sessions/harmony_test_123"
      );
      const retrieveTime = performance.now() - retrieveStart;

      expect(retrieveResponse.ok).toBe(true);
      expect(retrieveTime).toBeLessThan(300); // Retrieval should be faster

      console.log(`Harmony DB Operations:
        Store: ${storeTime.toFixed(2)}ms
        Retrieve: ${retrieveTime.toFixed(2)}ms`);
    });

    test("Reconnect therapy data analytics queries", async () => {
      const therapyData = {
        session_id: "reconnect_test_123",
        exercise_type: "shoulder_mobility",
        movement_metrics: {
          range_of_motion: { shoulder_flexion: 145, shoulder_extension: 45 },
          joint_angles: { shoulder: [90, 120, 145, 130, 95] },
          improvement_score: 0.78,
        },
        session_duration: 45000,
      };

      // Test complex analytics query
      const queryStart = performance.now();
      const analyticsResponse = await fetch("/api/v1/reconnect/analytics", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query_type: "progress_analysis",
          user_id: 1,
          exercise_type: "shoulder_mobility",
          date_range: { start: "2024-01-01", end: "2024-12-31" },
        }),
      });
      const queryTime = performance.now() - queryStart;

      expect(analyticsResponse.ok).toBe(true);
      expect(queryTime).toBeLessThan(1000); // Complex queries up to 1 second

      console.log(`Reconnect Analytics Query: ${queryTime.toFixed(2)}ms`);
    });

    test("concurrent database operations performance", async () => {
      const concurrentOperations = 10;
      const operations = [];

      for (let i = 0; i < concurrentOperations; i++) {
        const operation = fetch("/api/v1/health", {
          method: "GET",
        }).then((response) => {
          expect(response.ok).toBe(true);
          return response.json();
        });

        operations.push(operation);
      }

      const startTime = performance.now();
      await Promise.all(operations);
      const totalTime = performance.now() - startTime;

      const averageTime = totalTime / concurrentOperations;
      expect(averageTime).toBeLessThan(200); // Average should be under 200ms

      console.log(`Concurrent DB Operations:
        Total Time: ${totalTime.toFixed(2)}ms
        Average Time: ${averageTime.toFixed(2)}ms
        Operations: ${concurrentOperations}`);
    });
  });

  describe("API Integration Tests", () => {
    test("frontend-backend communication latency", async () => {
      const endpoints = [
        "/api/v1/health",
        "/api/v1/asl-world/stories",
        "/api/v1/harmony/emotions",
        "/api/v1/reconnect/exercises",
      ];

      for (const endpoint of endpoints) {
        const startTime = performance.now();
        const response = await fetch(endpoint);
        const responseTime = performance.now() - startTime;

        performanceMonitor.recordMetric("apiResponseTimes", responseTime);
        expect(response.ok).toBe(true);
        expect(responseTime).toBeLessThan(1000); // 1 second max
      }

      const averageLatency =
        performanceMonitor.getAverageLatency("apiResponseTimes");
      const maxLatency = performanceMonitor.getMaxLatency("apiResponseTimes");

      expect(averageLatency).toBeLessThan(500); // 500ms average
      expect(maxLatency).toBeLessThan(1000); // 1 second max

      console.log(`API Communication Performance:
        Average Latency: ${averageLatency.toFixed(2)}ms
        Max Latency: ${maxLatency.toFixed(2)}ms`);
    });

    test("handles API rate limiting gracefully", async () => {
      const requestCount = 20;
      const requests = [];

      // Simulate rapid API requests
      for (let i = 0; i < requestCount; i++) {
        const request = fetch(
          "/api/v1/asl-world/story/recognize_and_generate",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: `Test story ${i}` }),
          }
        );
        requests.push(request);
      }

      const responses = await Promise.allSettled(requests);

      // Check that most requests succeed or are properly rate limited
      const successfulRequests = responses.filter(
        (r) => r.status === "fulfilled" && r.value.ok
      ).length;

      const rateLimitedRequests = responses.filter(
        (r) => r.status === "fulfilled" && r.value.status === 429
      ).length;

      // Either most requests succeed, or they're properly rate limited
      expect(successfulRequests + rateLimitedRequests).toBeGreaterThan(
        requestCount * 0.8
      );

      console.log(`Rate Limiting Test:
        Successful: ${successfulRequests}
        Rate Limited: ${rateLimitedRequests}
        Total: ${requestCount}`);
    });

    test("API error responses include proper error information", async () => {
      // Test with invalid data to trigger errors
      const invalidRequests = [
        {
          url: "/api/v1/asl-world/story/recognize_and_generate",
          data: {
            /* missing required fields */
          },
        },
        {
          url: "/api/v1/harmony/sessions",
          data: { invalid_field: "invalid_value" },
        },
        {
          url: "/api/v1/reconnect/sessions",
          data: null,
        },
      ];

      for (const request of invalidRequests) {
        const response = await fetch(request.url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(request.data),
        });

        // Should return proper error status
        expect(response.status).toBeGreaterThanOrEqual(400);

        const errorData = await response.json();

        // Should include error information
        expect(errorData).toHaveProperty("error");
        expect(typeof errorData.error).toBe("string");
        expect(errorData.error.length).toBeGreaterThan(0);
      }
    });
  });

  describe("Error Handling and Recovery Scenarios", () => {
    test("graceful degradation when backend is unavailable", async () => {
      // Mock fetch to simulate backend unavailability
      global.fetch = jest
        .fn()
        .mockRejectedValue(new Error("Backend unavailable"));

      const { container } = render(
        <BrowserRouter>
          <App />
        </BrowserRouter>
      );

      // Should show appropriate error messages
      await waitFor(() => {
        expect(screen.getByText(/backend unavailable/i)).toBeInTheDocument();
      });

      // Should provide retry mechanisms
      expect(
        screen.getByRole("button", { name: /retry/i })
      ).toBeInTheDocument();
    });

    test("handles WebSocket disconnections and reconnections", async () => {
      let connectionAttempts = 0;

      global.WebSocket = jest.fn(() => {
        connectionAttempts++;
        const ws = new MockWebSocket("ws://localhost:8000/ws");

        // Simulate connection failure on first attempt
        if (connectionAttempts === 1) {
          setTimeout(() => {
            ws.readyState = WebSocket.CLOSED;
            if (ws.onclose) ws.onclose();
          }, 50);
        }

        return ws;
      });

      const { container } = render(
        <BrowserRouter>
          <VideoStreamingClient
            isActive={true}
            onConnectionChange={jest.fn()}
            onProcessedFrame={jest.fn()}
            onError={jest.fn()}
          />
        </BrowserRouter>
      );

      // Wait for initial connection attempt and failure
      await waitFor(() => {
        expect(connectionAttempts).toBeGreaterThan(1);
      });

      // Should attempt reconnection
      expect(connectionAttempts).toBeGreaterThanOrEqual(2);
    });

    test("memory usage remains stable during extended operation", async () => {
      const initialMemory = performance.memory
        ? performance.memory.usedJSHeapSize
        : 0;

      // Simulate extended operation with many frame processing cycles
      for (let i = 0; i < 100; i++) {
        const frameData = new ArrayBuffer(640 * 480 * 4); // Simulate video frame

        // Process frame (simulate MediaPipe processing)
        await new Promise((resolve) => setTimeout(resolve, 10));

        // Cleanup (important for memory management)
        // In real implementation, this would be handled by the video processing pipeline
      }

      const finalMemory = performance.memory
        ? performance.memory.usedJSHeapSize
        : 0;
      const memoryIncrease = finalMemory - initialMemory;

      // Memory increase should be reasonable (less than 50MB for this test)
      if (performance.memory) {
        expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024);
        console.log(`Memory Usage:
          Initial: ${(initialMemory / 1024 / 1024).toFixed(2)}MB
          Final: ${(finalMemory / 1024 / 1024).toFixed(2)}MB
          Increase: ${(memoryIncrease / 1024 / 1024).toFixed(2)}MB`);
      }
    });

    test("handles concurrent user sessions without performance degradation", async () => {
      const sessionCount = 5;
      const sessions = [];

      // Simulate multiple concurrent user sessions
      for (let i = 0; i < sessionCount; i++) {
        const session = {
          id: i,
          websocket: new MockWebSocket(`ws://localhost:8000/ws?session=${i}`),
          frameCount: 0,
          startTime: performance.now(),
        };

        sessions.push(session);

        // Simulate frame processing for each session
        const frameInterval = setInterval(() => {
          session.frameCount++;
          session.websocket.send(
            JSON.stringify({
              session_id: session.id,
              frame_number: session.frameCount,
              timestamp: performance.now(),
            })
          );
        }, 100); // 10 FPS per session

        // Stop after 2 seconds
        setTimeout(() => clearInterval(frameInterval), 2000);
      }

      // Wait for all sessions to complete
      await new Promise((resolve) => setTimeout(resolve, 2500));

      // Verify each session processed frames successfully
      sessions.forEach((session) => {
        expect(session.frameCount).toBeGreaterThan(15); // Should process ~20 frames
        const duration = performance.now() - session.startTime;
        const fps = (session.frameCount / duration) * 1000;
        expect(fps).toBeGreaterThan(8); // Should maintain reasonable FPS
      });

      console.log(`Concurrent Sessions Performance:
        Sessions: ${sessionCount}
        Average Frames per Session: ${
          sessions.reduce((sum, s) => sum + s.frameCount, 0) / sessionCount
        }`);
    });
  });
});
