/**
 * E2E Test Setup
 *
 * Global setup and utilities for end-to-end testing
 */

import "@testing-library/jest-dom";

// Performance monitoring setup
global.performanceMetrics = {
  videoProcessing: [],
  websocketLatency: [],
  apiResponseTimes: [],
  memoryUsage: [],
};

// Mock performance API if not available
if (!global.performance) {
  global.performance = {
    now: () => Date.now(),
    memory: {
      usedJSHeapSize: 0,
      totalJSHeapSize: 0,
      jsHeapSizeLimit: 0,
    },
  };
}

// Enhanced console logging for E2E tests
const originalConsoleLog = console.log;
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

console.log = (...args) => {
  if (process.env.NODE_ENV === "test" && process.env.VERBOSE_LOGGING) {
    originalConsoleLog("[E2E LOG]", ...args);
  }
};

console.error = (...args) => {
  if (process.env.NODE_ENV === "test") {
    originalConsoleError("[E2E ERROR]", ...args);
  }
};

console.warn = (...args) => {
  if (process.env.NODE_ENV === "test" && process.env.VERBOSE_LOGGING) {
    originalConsoleWarn("[E2E WARN]", ...args);
  }
};

// Global test utilities
global.testUtils = {
  // Wait for condition with timeout
  waitForCondition: async (condition, timeout = 5000, interval = 100) => {
    const startTime = Date.now();

    while (Date.now() - startTime < timeout) {
      if (await condition()) {
        return true;
      }
      await new Promise((resolve) => setTimeout(resolve, interval));
    }

    throw new Error(`Condition not met within ${timeout}ms`);
  },

  // Measure execution time
  measureTime: async (fn) => {
    const startTime = performance.now();
    const result = await fn();
    const endTime = performance.now();

    return {
      result,
      duration: endTime - startTime,
    };
  },

  // Generate test data
  generateTestUser: (overrides = {}) => ({
    username: "testuser123",
    email: "test@example.com",
    password: "SecurePass123!",
    ...overrides,
  }),

  generateTestStory: (overrides = {}) => ({
    id: 1,
    title: "Test Story",
    sentences: [
      "This is the first sentence.",
      "This is the second sentence.",
      "This is the third sentence.",
    ],
    object_detected: "test_object",
    ...overrides,
  }),

  generateTestSession: (type = "asl_world", overrides = {}) => {
    const baseSession = {
      session_id: `${type}_${Date.now()}`,
      user_id: 1,
      created_at: new Date().toISOString(),
      ...overrides,
    };

    switch (type) {
      case "harmony":
        return {
          ...baseSession,
          target_emotion: "happy",
          detected_emotions: ["happy", "neutral", "happy"],
          confidence_scores: [0.89, 0.45, 0.92],
          session_duration: 30000,
        };

      case "reconnect":
        return {
          ...baseSession,
          exercise_type: "shoulder_mobility",
          movement_data: [],
          joint_angles: { shoulder: [90, 120, 145] },
          range_of_motion: { shoulder_flexion: 145 },
          session_duration: 45000,
        };

      default: // asl_world
        return {
          ...baseSession,
          story_id: 1,
          sentences_completed: 2,
          feedback_scores: [0.85, 0.92],
          session_duration: 60000,
        };
    }
  },
};

// Mock WebRTC APIs for video testing
Object.defineProperty(navigator, "mediaDevices", {
  writable: true,
  value: {
    getUserMedia: jest.fn(() => {
      const mockStream = {
        id: "mock-stream-id",
        getTracks: () => [
          {
            kind: "video",
            stop: jest.fn(),
            getSettings: () => ({ width: 640, height: 480, frameRate: 30 }),
          },
        ],
        getVideoTracks: () => [
          {
            kind: "video",
            stop: jest.fn(),
            getSettings: () => ({ width: 640, height: 480, frameRate: 30 }),
          },
        ],
        getAudioTracks: () => [],
      };

      return Promise.resolve(mockStream);
    }),

    enumerateDevices: jest.fn(() =>
      Promise.resolve([
        {
          deviceId: "mock-camera-1",
          kind: "videoinput",
          label: "Mock Camera 1",
          groupId: "mock-group-1",
        },
      ])
    ),
  },
});

// Mock WebSocket for testing
class MockWebSocketForTesting {
  constructor(url) {
    this.url = url;
    this.readyState = WebSocket.CONNECTING;
    this.onopen = null;
    this.onmessage = null;
    this.onerror = null;
    this.onclose = null;
    this.sentMessages = [];

    // Simulate connection
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      if (this.onopen) {
        this.onopen({ type: "open" });
      }
    }, 100);
  }

  send(data) {
    if (this.readyState !== WebSocket.OPEN) {
      throw new Error("WebSocket is not open");
    }

    this.sentMessages.push({
      data,
      timestamp: performance.now(),
    });

    // Simulate response
    setTimeout(() => {
      if (this.onmessage) {
        this.onmessage({
          data: JSON.stringify({
            type: "processed_frame",
            timestamp: performance.now(),
            metadata: {
              frame_number: this.sentMessages.length,
            },
          }),
        });
      }
    }, Math.random() * 100 + 50);
  }

  close(code = 1000, reason = "") {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) {
      this.onclose({ code, reason });
    }
  }

  addEventListener(event, handler) {
    this[`on${event}`] = handler;
  }

  removeEventListener(event, handler) {
    if (this[`on${event}`] === handler) {
      this[`on${event}`] = null;
    }
  }
}

// Set up WebSocket mock
global.WebSocket = MockWebSocketForTesting;
global.WebSocket.CONNECTING = 0;
global.WebSocket.OPEN = 1;
global.WebSocket.CLOSING = 2;
global.WebSocket.CLOSED = 3;

// Mock Canvas API for video processing tests
const mockCanvas = {
  getContext: jest.fn(() => ({
    clearRect: jest.fn(),
    fillRect: jest.fn(),
    strokeRect: jest.fn(),
    beginPath: jest.fn(),
    moveTo: jest.fn(),
    lineTo: jest.fn(),
    stroke: jest.fn(),
    fill: jest.fn(),
    arc: jest.fn(),
    drawImage: jest.fn(),
    getImageData: jest.fn(() => ({
      data: new Uint8ClampedArray(640 * 480 * 4),
      width: 640,
      height: 480,
    })),
    putImageData: jest.fn(),
    createImageData: jest.fn(() => ({
      data: new Uint8ClampedArray(640 * 480 * 4),
      width: 640,
      height: 480,
    })),
    canvas: {
      width: 640,
      height: 480,
      toDataURL: jest.fn(() => "data:image/png;base64,mock-image-data"),
    },
  })),
  width: 640,
  height: 480,
  toDataURL: jest.fn(() => "data:image/png;base64,mock-image-data"),
};

Object.defineProperty(HTMLCanvasElement.prototype, "getContext", {
  value: mockCanvas.getContext,
});

// Performance monitoring helpers
global.startPerformanceTimer = (label) => {
  global.performanceTimers = global.performanceTimers || {};
  global.performanceTimers[label] = performance.now();
};

global.endPerformanceTimer = (label) => {
  if (!global.performanceTimers || !global.performanceTimers[label]) {
    return 0;
  }

  const duration = performance.now() - global.performanceTimers[label];
  delete global.performanceTimers[label];

  return duration;
};

global.recordPerformanceMetric = (type, value) => {
  if (global.performanceMetrics[type]) {
    global.performanceMetrics[type].push({
      value,
      timestamp: performance.now(),
    });
  }
};

// Clean up after each test
afterEach(() => {
  // Clear performance metrics
  Object.keys(global.performanceMetrics).forEach((key) => {
    global.performanceMetrics[key] = [];
  });

  // Clear performance timers
  global.performanceTimers = {};

  // Clean up any remaining timeouts/intervals
  jest.clearAllTimers();
});

// Global error handler for unhandled promise rejections
process.on("unhandledRejection", (reason, promise) => {
  console.error("Unhandled Rejection at:", promise, "reason:", reason);
});

// Increase timeout for E2E tests
jest.setTimeout(30000);
