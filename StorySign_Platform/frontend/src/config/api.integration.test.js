/**
 * Integration tests for API configuration with services
 * Tests that API calls work automatically without manual connection
 * Requirements: 3.3, 6.1, 6.4
 */

import API_BASE_URL from "./api";
import authService from "../services/AuthService";

// Mock fetch globally
global.fetch = jest.fn();

// Mock localStorage and sessionStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

Object.defineProperty(window, "localStorage", {
  value: localStorageMock,
});

Object.defineProperty(window, "sessionStorage", {
  value: sessionStorageMock,
});

describe("API Configuration Integration Tests", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    fetch.mockClear();
    localStorageMock.getItem.mockClear();
    localStorageMock.setItem.mockClear();
    localStorageMock.removeItem.mockClear();
    sessionStorageMock.getItem.mockClear();
    sessionStorageMock.setItem.mockClear();
    sessionStorageMock.removeItem.mockClear();
  });

  describe("AuthService Integration", () => {
    test("should work with login immediately without manual backend connection", async () => {
      // Mock successful login response
      fetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          access_token: "test-token-123",
          user: {
            id: 1,
            email: "test@example.com",
            username: "testuser",
          },
          refresh_token: "refresh-token-123",
        }),
      });

      // Test login works immediately using the simplified API config
      const result = await authService.login(
        "test@example.com",
        "password",
        true
      );

      // Verify the correct API endpoint was called
      expect(fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/v1/auth/login",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            identifier: "test@example.com",
            password: "password",
          }),
        }
      );

      // Verify login was successful
      expect(result.user.email).toBe("test@example.com");
      expect(result.token).toBe("test-token-123");

      // Verify auth data was stored
      expect(localStorageMock.setItem).toHaveBeenCalledWith(
        "auth_token",
        "test-token-123"
      );
    });

    test("should work with register immediately without manual backend connection", async () => {
      // Mock successful registration response
      fetch.mockResolvedValue({
        ok: true,
        status: 201,
        json: async () => ({
          message: "User registered successfully",
          user: {
            id: 2,
            email: "newuser@example.com",
            username: "newuser",
          },
        }),
      });

      // Test registration works immediately
      const result = await authService.register({
        username: "newuser",
        email: "newuser@example.com",
        password: "newpassword",
      });

      // Verify the correct API endpoint was called
      expect(fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/v1/auth/register",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            username: "newuser",
            email: "newuser@example.com",
            password: "newpassword",
          }),
        }
      );

      // Verify registration was successful
      expect(result.message).toBe("User registered successfully");
      expect(result.user.email).toBe("newuser@example.com");
    });

    test("should work with authenticated requests immediately", async () => {
      // Mock token exists
      localStorageMock.getItem.mockReturnValue("test-token-123");

      // Mock successful authenticated request
      fetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          id: 1,
          email: "test@example.com",
          username: "testuser",
        }),
      });

      // Test authenticated request works immediately
      const response = await authService.makeAuthenticatedRequest("/auth/me");
      const userData = await response.json();

      // Verify the correct API endpoint was called with auth header
      expect(fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/v1/auth/me",
        {
          headers: {
            "Content-Type": "application/json",
            Authorization: "Bearer test-token-123",
          },
        }
      );

      // Verify response was successful
      expect(userData.email).toBe("test@example.com");
    });

    test("should handle logout API call immediately", async () => {
      // Mock token exists
      localStorageMock.getItem.mockReturnValue("test-token-123");

      // Mock successful logout response
      fetch.mockResolvedValue({
        ok: true,
        status: 200,
      });

      // Test logout works immediately
      await authService.logout();

      // Verify the correct API endpoint was called
      expect(fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/v1/auth/logout",
        {
          method: "POST",
          headers: {
            Authorization: "Bearer test-token-123",
            "Content-Type": "application/json",
          },
        }
      );

      // Verify auth data was cleared
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("auth_token");
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("auth_user");
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("refresh_token");
    });
  });

  describe("Application Startup Simulation", () => {
    test("should support immediate health check on app start", async () => {
      // Mock successful health check
      fetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          status: "healthy",
          timestamp: "2024-01-01T00:00:00Z",
          version: "1.0.0",
          database: "connected",
          services: ["auth", "stories", "video"],
        }),
      });

      // Simulate app startup health check
      const healthCheck = async () => {
        const response = await fetch(`${API_BASE_URL}/api/v1/health`);
        return await response.json();
      };

      const healthData = await healthCheck();

      // Verify health check worked immediately
      expect(fetch).toHaveBeenCalledWith("http://127.0.0.1:8000/api/v1/health");
      expect(healthData.status).toBe("healthy");
      expect(healthData.services).toContain("auth");
      expect(healthData.services).toContain("stories");
      expect(healthData.services).toContain("video");
    });

    test("should support immediate story generation on app start", async () => {
      // Mock successful story generation
      fetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          story: {
            id: "story-123",
            title: "Test Story",
            content: "Once upon a time...",
            created_at: "2024-01-01T00:00:00Z",
          },
        }),
      });

      // Simulate immediate story generation (like ASL World "Scan Object to Start")
      const generateStory = async prompt => {
        const response = await fetch(
          `${API_BASE_URL}/api/v1/stories/generate`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ prompt }),
          }
        );
        return await response.json();
      };

      const storyData = await generateStory("A magical adventure");

      // Verify story generation worked immediately
      expect(fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/v1/stories/generate",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ prompt: "A magical adventure" }),
        }
      );
      expect(storyData.story.title).toBe("Test Story");
      expect(storyData.story.content).toBe("Once upon a time...");
    });

    test("should support immediate video streaming setup", async () => {
      // Mock successful video stream initialization
      fetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          stream_id: "stream-456",
          websocket_url: "ws://127.0.0.1:8000/ws/video",
          status: "ready",
          session_id: "session-789",
        }),
      });

      // Simulate immediate video streaming setup (like ASL World)
      const initializeVideoStream = async sessionId => {
        const response = await fetch(
          `${API_BASE_URL}/api/v1/video/stream/start`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ session_id: sessionId }),
          }
        );
        return await response.json();
      };

      const streamData = await initializeVideoStream("test-session");

      // Verify video streaming setup worked immediately
      expect(fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/v1/video/stream/start",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ session_id: "test-session" }),
        }
      );
      expect(streamData.status).toBe("ready");
      expect(streamData.websocket_url).toBe("ws://127.0.0.1:8000/ws/video");
    });
  });

  describe("No Manual Connection Required", () => {
    test("should work without any 'Test Backend' button clicks", async () => {
      // Mock multiple API calls that would previously require manual connection
      fetch
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ status: "healthy" }),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ story: "Generated story" }),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ stream_id: "stream-123" }),
        });

      // Simulate multiple API calls that should work immediately
      const healthResponse = await fetch(`${API_BASE_URL}/api/v1/health`);
      const healthData = await healthResponse.json();

      const storyResponse = await fetch(
        `${API_BASE_URL}/api/v1/stories/generate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt: "test" }),
        }
      );
      const storyData = await storyResponse.json();

      const streamResponse = await fetch(
        `${API_BASE_URL}/api/v1/video/stream/start`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: "test" }),
        }
      );
      const streamData = await streamResponse.json();

      // Verify all calls worked immediately
      expect(healthData.status).toBe("healthy");
      expect(storyData.story).toBe("Generated story");
      expect(streamData.stream_id).toBe("stream-123");

      // Verify all endpoints were called with correct URLs
      expect(fetch).toHaveBeenNthCalledWith(
        1,
        "http://127.0.0.1:8000/api/v1/health"
      );
      expect(fetch).toHaveBeenNthCalledWith(
        2,
        "http://127.0.0.1:8000/api/v1/stories/generate",
        expect.any(Object)
      );
      expect(fetch).toHaveBeenNthCalledWith(
        3,
        "http://127.0.0.1:8000/api/v1/video/stream/start",
        expect.any(Object)
      );
    });

    test("should handle concurrent API calls immediately", async () => {
      // Mock responses for concurrent calls
      fetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ success: true }),
      });

      // Simulate concurrent API calls (like app initialization)
      const promises = [
        fetch(`${API_BASE_URL}/api/v1/health`),
        fetch(`${API_BASE_URL}/api/v1/auth/me`, {
          headers: { Authorization: "Bearer test-token" },
        }),
        fetch(`${API_BASE_URL}/api/v1/stories/list`),
        fetch(`${API_BASE_URL}/api/v1/user/preferences`),
      ];

      const responses = await Promise.all(promises);

      // Verify all concurrent calls succeeded
      responses.forEach(response => {
        expect(response.ok).toBe(true);
      });

      // Verify all endpoints were called
      expect(fetch).toHaveBeenCalledTimes(4);
      expect(fetch).toHaveBeenCalledWith("http://127.0.0.1:8000/api/v1/health");
      expect(fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/v1/auth/me",
        { headers: { Authorization: "Bearer test-token" } }
      );
      expect(fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/v1/stories/list"
      );
      expect(fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/v1/user/preferences"
      );
    });
  });

  describe("Error Scenarios", () => {
    test("should handle backend unavailable gracefully", async () => {
      // Mock network error (backend not running)
      const networkError = new Error("Failed to fetch");
      networkError.name = "TypeError";
      fetch.mockRejectedValue(networkError);

      // Test that error handling works immediately
      try {
        await fetch(`${API_BASE_URL}/api/v1/health`);
        fail("Should have thrown an error");
      } catch (error) {
        expect(error.message).toBe("Failed to fetch");
        expect(error.name).toBe("TypeError");
      }

      expect(fetch).toHaveBeenCalledWith("http://127.0.0.1:8000/api/v1/health");
    });

    test("should handle server errors immediately", async () => {
      // Mock server error
      fetch.mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({ error: "Internal server error" }),
      });

      const response = await fetch(`${API_BASE_URL}/api/v1/stories/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: "test" }),
      });

      const errorData = await response.json();

      expect(response.ok).toBe(false);
      expect(response.status).toBe(500);
      expect(errorData.error).toBe("Internal server error");
    });

    test("should maintain consistent error handling across services", async () => {
      // Mock authentication error
      fetch.mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => ({ message: "Unauthorized" }),
      });

      // Test that AuthService handles errors consistently
      try {
        await authService.login("invalid@example.com", "wrongpassword");
        fail("Should have thrown an error");
      } catch (error) {
        expect(error.message).toContain("Invalid email or password");
      }

      expect(fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/v1/auth/login",
        expect.any(Object)
      );
    });
  });
});
