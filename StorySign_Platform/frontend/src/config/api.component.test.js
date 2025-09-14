/**
 * Component integration tests for API configuration
 * Tests that components can use API immediately without manual connection
 * Requirements: 3.3, 6.1, 6.4
 */

import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import API_BASE_URL from "./api";

// Mock fetch globally
global.fetch = jest.fn();

// Mock WebSocket
global.WebSocket = jest.fn().mockImplementation(() => ({
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  send: jest.fn(),
  close: jest.fn(),
  readyState: 1, // OPEN
}));

// Create a test component that uses the API configuration
const TestAPIComponent = () => {
  const [apiStatus, setApiStatus] = React.useState("loading");
  const [storyData, setStoryData] = React.useState(null);
  const [error, setError] = React.useState(null);

  React.useEffect(() => {
    // Simulate immediate API usage (like ASL World)
    const testAPIConnection = async () => {
      try {
        // Test health check
        const healthResponse = await fetch(`${API_BASE_URL}/api/v1/health`);
        if (!healthResponse.ok) {
          throw new Error("Health check failed");
        }

        // Test story generation (like "Scan Object to Start")
        const storyResponse = await fetch(
          `${API_BASE_URL}/api/v1/stories/generate`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: "test story" }),
          }
        );

        if (!storyResponse.ok) {
          throw new Error("Story generation failed");
        }

        const story = await storyResponse.json();
        setStoryData(story);
        setApiStatus("connected");
      } catch (err) {
        setError(err.message);
        setApiStatus("error");
      }
    };

    testAPIConnection();
  }, []);

  if (apiStatus === "loading") {
    return <div data-testid="loading">Loading...</div>;
  }

  if (apiStatus === "error") {
    return <div data-testid="error">Error: {error}</div>;
  }

  return (
    <div data-testid="success">
      <div data-testid="api-status">API Connected</div>
      {storyData && (
        <div data-testid="story-data">
          Story: {storyData.story || storyData.title || "Generated"}
        </div>
      )}
    </div>
  );
};

// Create a test component that simulates ASL World behavior
const TestASLWorldComponent = () => {
  const [streamStatus, setStreamStatus] = React.useState("initializing");
  const [wsConnection, setWsConnection] = React.useState(null);

  React.useEffect(() => {
    // Simulate ASL World immediate functionality
    const initializeASLWorld = async () => {
      try {
        // Start video stream immediately (no "Test Backend" required)
        const streamResponse = await fetch(
          `${API_BASE_URL}/api/v1/video/stream/start`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: "test-session" }),
          }
        );

        if (!streamResponse.ok) {
          throw new Error("Stream initialization failed");
        }

        const streamData = await streamResponse.json();

        // Initialize WebSocket connection
        const wsUrl =
          streamData.websocket_url || "ws://127.0.0.1:8000/ws/video";
        const ws = new WebSocket(wsUrl);
        setWsConnection(ws);
        setStreamStatus("ready");
      } catch (err) {
        setStreamStatus("error");
      }
    };

    initializeASLWorld();
  }, []);

  return (
    <div data-testid="asl-world">
      <div data-testid="stream-status">{streamStatus}</div>
      {streamStatus === "ready" && (
        <div data-testid="scan-ready">Scan Object to Start</div>
      )}
    </div>
  );
};

describe("API Configuration Component Integration", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    fetch.mockClear();
  });

  describe("Immediate API Usage", () => {
    test("should allow components to use API immediately without manual connection", async () => {
      // Mock successful API responses
      fetch
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ status: "healthy" }),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ story: "Test story generated" }),
        });

      render(
        <BrowserRouter>
          <TestAPIComponent />
        </BrowserRouter>
      );

      // Initially should show loading
      expect(screen.getByTestId("loading")).toBeInTheDocument();

      // Wait for API calls to complete
      await waitFor(() => {
        expect(screen.getByTestId("success")).toBeInTheDocument();
      });

      // Verify API was called immediately
      expect(fetch).toHaveBeenCalledWith("http://127.0.0.1:8000/api/v1/health");
      expect(fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/v1/stories/generate",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt: "test story" }),
        }
      );

      // Verify component shows success state
      expect(screen.getByTestId("api-status")).toHaveTextContent(
        "API Connected"
      );
      expect(screen.getByTestId("story-data")).toHaveTextContent(
        "Story: Test story generated"
      );
    });

    test("should handle API errors gracefully in components", async () => {
      // Mock API error
      fetch.mockRejectedValue(new Error("Network error"));

      render(
        <BrowserRouter>
          <TestAPIComponent />
        </BrowserRouter>
      );

      // Wait for error state
      await waitFor(() => {
        expect(screen.getByTestId("error")).toBeInTheDocument();
      });

      // Verify error is displayed
      expect(screen.getByTestId("error")).toHaveTextContent(
        "Error: Network error"
      );

      // Verify API was still attempted
      expect(fetch).toHaveBeenCalledWith("http://127.0.0.1:8000/api/v1/health");
    });
  });

  describe("ASL World Immediate Functionality", () => {
    test("should allow ASL World to work immediately without Test Backend button", async () => {
      // Mock successful stream initialization
      fetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          stream_id: "stream-123",
          websocket_url: "ws://127.0.0.1:8000/ws/video",
          status: "ready",
        }),
      });

      render(
        <BrowserRouter>
          <TestASLWorldComponent />
        </BrowserRouter>
      );

      // Initially should show initializing
      expect(screen.getByTestId("stream-status")).toHaveTextContent(
        "initializing"
      );

      // Wait for stream to be ready
      await waitFor(() => {
        expect(screen.getByTestId("stream-status")).toHaveTextContent("ready");
      });

      // Verify "Scan Object to Start" is available immediately
      expect(screen.getByTestId("scan-ready")).toHaveTextContent(
        "Scan Object to Start"
      );

      // Verify video stream API was called
      expect(fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/v1/video/stream/start",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: "test-session" }),
        }
      );

      // Verify WebSocket was initialized
      expect(WebSocket).toHaveBeenCalledWith("ws://127.0.0.1:8000/ws/video");
    });

    test("should handle stream initialization errors", async () => {
      // Mock stream initialization error
      fetch.mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({ error: "Stream initialization failed" }),
      });

      render(
        <BrowserRouter>
          <TestASLWorldComponent />
        </BrowserRouter>
      );

      // Wait for error state
      await waitFor(() => {
        expect(screen.getByTestId("stream-status")).toHaveTextContent("error");
      });

      // Verify API was attempted
      expect(fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/v1/video/stream/start",
        expect.any(Object)
      );

      // Verify WebSocket was not initialized on error
      expect(WebSocket).not.toHaveBeenCalled();
    });
  });

  describe("Multiple Component API Usage", () => {
    test("should support multiple components using API simultaneously", async () => {
      // Mock responses for multiple components
      fetch
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ status: "healthy" }),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({ story: "Component 1 story" }),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => ({
            stream_id: "stream-456",
            websocket_url: "ws://127.0.0.1:8000/ws/video",
          }),
        });

      render(
        <BrowserRouter>
          <div>
            <TestAPIComponent />
            <TestASLWorldComponent />
          </div>
        </BrowserRouter>
      );

      // Wait for both components to be ready
      await waitFor(() => {
        expect(screen.getByTestId("success")).toBeInTheDocument();
        expect(screen.getByTestId("stream-status")).toHaveTextContent("ready");
      });

      // Verify both components work
      expect(screen.getByTestId("api-status")).toHaveTextContent(
        "API Connected"
      );
      expect(screen.getByTestId("scan-ready")).toHaveTextContent(
        "Scan Object to Start"
      );

      // Verify all API calls were made
      expect(fetch).toHaveBeenCalledTimes(3);
      expect(fetch).toHaveBeenCalledWith("http://127.0.0.1:8000/api/v1/health");
      expect(fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/v1/stories/generate",
        expect.any(Object)
      );
      expect(fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/v1/video/stream/start",
        expect.any(Object)
      );
    });
  });

  describe("API Configuration Consistency", () => {
    test("should use consistent API base URL across all component API calls", async () => {
      // Mock all responses
      fetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ success: true }),
      });

      render(
        <BrowserRouter>
          <div>
            <TestAPIComponent />
            <TestASLWorldComponent />
          </div>
        </BrowserRouter>
      );

      // Wait for components to make API calls
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledTimes(3);
      });

      // Verify all calls use the same base URL
      const calls = fetch.mock.calls;
      calls.forEach(call => {
        const url = call[0];
        expect(url).toContain("http://127.0.0.1:8000");
        expect(url).toMatch(/^http:\/\/127\.0\.0\.1:8000\/api\/v1\//);
      });
    });

    test("should work with different API endpoints consistently", async () => {
      // Mock responses for different endpoints
      fetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ success: true }),
      });

      // Create component that uses multiple endpoints
      const MultiEndpointComponent = () => {
        React.useEffect(() => {
          // Test multiple endpoints
          const endpoints = [
            "/api/v1/health",
            "/api/v1/auth/me",
            "/api/v1/stories/list",
            "/api/v1/user/preferences",
            "/api/v1/video/stream/start",
          ];

          endpoints.forEach(endpoint => {
            fetch(`${API_BASE_URL}${endpoint}`);
          });
        }, []);

        return <div data-testid="multi-endpoint">Multi-endpoint test</div>;
      };

      render(
        <BrowserRouter>
          <MultiEndpointComponent />
        </BrowserRouter>
      );

      // Wait for all API calls
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledTimes(5);
      });

      // Verify all endpoints use correct base URL
      const expectedCalls = [
        "http://127.0.0.1:8000/api/v1/health",
        "http://127.0.0.1:8000/api/v1/auth/me",
        "http://127.0.0.1:8000/api/v1/stories/list",
        "http://127.0.0.1:8000/api/v1/user/preferences",
        "http://127.0.0.1:8000/api/v1/video/stream/start",
      ];

      expectedCalls.forEach(expectedUrl => {
        expect(fetch).toHaveBeenCalledWith(expectedUrl);
      });
    });
  });
});
