/**
 * E2E Test Setup Verification
 *
 * Simple test to verify E2E test environment is working correctly
 */

import "@testing-library/jest-dom";
import "./setup"; // Import E2E setup

describe("E2E Test Setup", () => {
  test("test environment is properly configured", () => {
    expect(process.env.NODE_ENV).toBe("test");
    expect(global.testUtils).toBeDefined();
    expect(global.performanceMetrics).toBeDefined();
  });

  test("performance monitoring utilities work", () => {
    global.startPerformanceTimer("test");

    // Simulate some work
    const start = performance.now();
    while (performance.now() - start < 10) {
      // Wait 10ms
    }

    const duration = global.endPerformanceTimer("test");
    expect(duration).toBeGreaterThan(0);
  });

  test("mock WebSocket is available", () => {
    const ws = new WebSocket("ws://localhost:8000/test");
    expect(ws).toBeDefined();
    expect(ws.readyState).toBe(WebSocket.CONNECTING);

    ws.close();
  });

  test("mock MediaDevices is available", () => {
    expect(navigator.mediaDevices).toBeDefined();
    expect(navigator.mediaDevices.getUserMedia).toBeDefined();
  });

  test("test utilities are working", async () => {
    const testUser = global.testUtils.generateTestUser();
    expect(testUser).toHaveProperty("username");
    expect(testUser).toHaveProperty("email");
    expect(testUser).toHaveProperty("password");

    const testStory = global.testUtils.generateTestStory();
    expect(testStory).toHaveProperty("title");
    expect(testStory).toHaveProperty("sentences");
    expect(Array.isArray(testStory.sentences)).toBe(true);
  });
});
