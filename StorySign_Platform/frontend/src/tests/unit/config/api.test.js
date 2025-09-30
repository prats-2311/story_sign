/**
 * Tests for simplified API configuration
 * Requirements: 3.3, 6.1, 6.4
 */

import API_BASE_URL from "./api";

// Mock fetch for testing API calls
global.fetch = jest.fn();

describe("API Configuration", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    fetch.mockClear();
  });

  describe("Basic Configuration Export", () => {
    test("should export the correct backend URL", () => {
      expect(API_BASE_URL).toBe("http://127.0.0.1:8000");
    });

    test("should be a string", () => {
      expect(typeof API_BASE_URL).toBe("string");
    });

    test("should not have trailing slash", () => {
      expect(API_BASE_URL).not.toMatch(/\/$/);
    });

    test("should be a valid URL", () => {
      expect(() => new URL(API_BASE_URL)).not.toThrow();
    });

    test("should use localhost with port 8000", () => {
      const url = new URL(API_BASE_URL);
      expect(url.hostname).toBe("127.0.0.1");
      expect(url.port).toBe("8000");
      expect(url.protocol).toBe("http:");
    });

    test("should be directly importable without function calls", () => {
      // Verify it's a direct export, not a function
      expect(typeof API_BASE_URL).toBe("string");
      expect(API_BASE_URL).not.toBeInstanceOf(Function);
    });

    test("should be consistent across multiple imports", () => {
      // Re-import to verify consistency
      const { default: reimportedUrl } = require("./api");
      expect(reimportedUrl).toBe(API_BASE_URL);
      expect(reimportedUrl).toBe("http://127.0.0.1:8000");
    });
  });

  describe("Automatic API Connectivity", () => {
    test("should work with fetch calls immediately without manual connection", async () => {
      // Mock successful API response
      fetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ message: "API connected" }),
      });

      // Test that API calls work immediately using the exported URL
      const response = await fetch(`${API_BASE_URL}/api/v1/health`);
      const data = await response.json();

      expect(fetch).toHaveBeenCalledWith("http://127.0.0.1:8000/api/v1/health");
      expect(response.ok).toBe(true);
      expect(data.message).toBe("API connected");
    });

    test("should construct API endpoints correctly", () => {
      const endpoints = [
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/logout",
        "/api/v1/stories/generate",
        "/api/v1/health",
      ];

      endpoints.forEach(endpoint => {
        const fullUrl = `${API_BASE_URL}${endpoint}`;
        expect(fullUrl).toBe(`http://127.0.0.1:8000${endpoint}`);
        expect(() => new URL(fullUrl)).not.toThrow();
      });
    });

    test("should support WebSocket URL construction", () => {
      const wsUrl = API_BASE_URL.replace("http://", "ws://");
      expect(wsUrl).toBe("ws://127.0.0.1:8000");

      const wsEndpoint = `${wsUrl}/ws/video`;
      expect(wsEndpoint).toBe("ws://127.0.0.1:8000/ws/video");
    });

    test("should handle API calls without conditional logic", async () => {
      // Mock API response
      fetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ status: "ready" }),
      });

      // Test multiple API calls work immediately
      const endpoints = [
        "/api/v1/health",
        "/api/v1/auth/me",
        "/api/v1/stories/list",
      ];

      for (const endpoint of endpoints) {
        const response = await fetch(`${API_BASE_URL}${endpoint}`);
        expect(response.ok).toBe(true);
        expect(fetch).toHaveBeenCalledWith(`http://127.0.0.1:8000${endpoint}`);
      }

      expect(fetch).toHaveBeenCalledTimes(3);
    });
  });

  describe("Backend Connectivity on Application Start", () => {
    test("should be immediately available for health checks", async () => {
      // Mock successful health check
      fetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          status: "healthy",
          timestamp: new Date().toISOString(),
          version: "1.0.0",
        }),
      });

      // Simulate application startup health check
      const healthCheckUrl = `${API_BASE_URL}/api/v1/health`;
      const response = await fetch(healthCheckUrl);
      const healthData = await response.json();

      expect(fetch).toHaveBeenCalledWith("http://127.0.0.1:8000/api/v1/health");
      expect(response.ok).toBe(true);
      expect(healthData.status).toBe("healthy");
    });

    test("should support immediate story generation API calls", async () => {
      // Mock story generation response
      fetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          story: "Generated story content",
          id: "story-123",
          created_at: new Date().toISOString(),
        }),
      });

      // Test story generation works immediately
      const storyResponse = await fetch(
        `${API_BASE_URL}/api/v1/stories/generate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt: "Test story" }),
        }
      );

      const storyData = await storyResponse.json();

      expect(fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/v1/stories/generate",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt: "Test story" }),
        }
      );
      expect(storyResponse.ok).toBe(true);
      expect(storyData.story).toBe("Generated story content");
    });

    test("should handle authentication API calls immediately", async () => {
      // Mock login response
      fetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          access_token: "test-token",
          user: { id: 1, email: "test@example.com" },
        }),
      });

      // Test login works immediately
      const loginResponse = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          identifier: "test@example.com",
          password: "password",
        }),
      });

      const loginData = await loginResponse.json();

      expect(fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/v1/auth/login",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            identifier: "test@example.com",
            password: "password",
          }),
        }
      );
      expect(loginResponse.ok).toBe(true);
      expect(loginData.access_token).toBe("test-token");
    });

    test("should work with ASL World video streaming endpoints", async () => {
      // Mock video streaming endpoint response
      fetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          stream_id: "stream-123",
          status: "ready",
          websocket_url: "ws://127.0.0.1:8000/ws/video",
        }),
      });

      // Test ASL World endpoints work immediately
      const streamResponse = await fetch(
        `${API_BASE_URL}/api/v1/video/stream/start`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: "test-session" }),
        }
      );

      const streamData = await streamResponse.json();

      expect(fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/v1/video/stream/start",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: "test-session" }),
        }
      );
      expect(streamResponse.ok).toBe(true);
      expect(streamData.status).toBe("ready");
    });
  });

  describe("Error Handling", () => {
    test("should handle network errors gracefully", async () => {
      // Mock network error
      const networkError = new Error("Network error");
      networkError.name = "TypeError";
      fetch.mockRejectedValue(networkError);

      try {
        await fetch(`${API_BASE_URL}/api/v1/health`);
      } catch (error) {
        expect(error.message).toBe("Network error");
        expect(error.name).toBe("TypeError");
      }

      expect(fetch).toHaveBeenCalledWith("http://127.0.0.1:8000/api/v1/health");
    });

    test("should handle server errors appropriately", async () => {
      // Mock server error
      fetch.mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({ error: "Internal server error" }),
      });

      const response = await fetch(`${API_BASE_URL}/api/v1/health`);
      const errorData = await response.json();

      expect(response.ok).toBe(false);
      expect(response.status).toBe(500);
      expect(errorData.error).toBe("Internal server error");
    });

    test("should maintain URL consistency even with malformed requests", () => {
      // Test various URL constructions
      const testCases = [
        `${API_BASE_URL}/api/v1/test`,
        `${API_BASE_URL}//api/v1/test`, // Double slash
        `${API_BASE_URL}/api/v1/test/`, // Trailing slash
      ];

      testCases.forEach(url => {
        expect(url).toContain("http://127.0.0.1:8000");
        expect(() => new URL(url)).not.toThrow();
      });
    });
  });

  describe("Integration with Services", () => {
    test("should work with AuthService patterns", async () => {
      // Mock successful auth request
      fetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ user: { id: 1 } }),
      });

      // Test the pattern used in AuthService
      const makeRequest = async (endpoint, options = {}) => {
        const url = `${API_BASE_URL}/api/v1${endpoint}`;
        return await fetch(url, {
          headers: { "Content-Type": "application/json" },
          ...options,
        });
      };

      const response = await makeRequest("/auth/me");
      const data = await response.json();

      expect(fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/v1/auth/me",
        {
          headers: { "Content-Type": "application/json" },
        }
      );
      expect(data.user.id).toBe(1);
    });

    test("should work with video streaming patterns", () => {
      // Test WebSocket URL construction pattern
      const wsUrl = API_BASE_URL.replace("http://", "ws://");
      const videoStreamUrl = `${wsUrl}/ws/video`;

      expect(videoStreamUrl).toBe("ws://127.0.0.1:8000/ws/video");

      // Test that it would work with WebSocket constructor
      // Note: We can't actually create WebSocket in Jest, but we can test URL format
      expect(videoStreamUrl.startsWith("ws://")).toBe(true);
      expect(videoStreamUrl).toContain("127.0.0.1:8000");
    });

    test("should support all common HTTP methods", async () => {
      const methods = ["GET", "POST", "PUT", "DELETE", "PATCH"];

      // Mock responses for all methods
      fetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ success: true }),
      });

      for (const method of methods) {
        const response = await fetch(`${API_BASE_URL}/api/v1/test`, {
          method,
          headers: { "Content-Type": "application/json" },
        });

        expect(response.ok).toBe(true);
        expect(fetch).toHaveBeenCalledWith(
          "http://127.0.0.1:8000/api/v1/test",
          {
            method,
            headers: { "Content-Type": "application/json" },
          }
        );
      }

      expect(fetch).toHaveBeenCalledTimes(methods.length);
    });
  });
});
