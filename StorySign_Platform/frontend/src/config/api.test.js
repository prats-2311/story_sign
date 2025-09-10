/**
 * Tests for API configuration
 */

import {
  getApiConfig,
  buildApiUrl,
  buildWsUrl,
  buildHealthCheckUrl,
  getEnvironmentInfo,
} from "./api";

// Mock environment variables
const originalEnv = process.env;

describe("API Configuration", () => {
  beforeEach(() => {
    jest.resetModules();
    process.env = { ...originalEnv };
  });

  afterAll(() => {
    process.env = originalEnv;
  });

  describe("getApiConfig", () => {
    test("should return default configuration in development", () => {
      process.env.NODE_ENV = "development";
      delete process.env.REACT_APP_API_URL;
      delete process.env.REACT_APP_WS_URL;

      const config = getApiConfig();

      expect(config.API_BASE_URL).toBe("http://localhost:8000");
      expect(config.WS_BASE_URL).toBe("ws://localhost:8000");
      expect(config.API_VERSION).toBe("v1");
    });

    test("should use environment variables when provided", () => {
      process.env.REACT_APP_API_URL = "https://api.example.com";
      process.env.REACT_APP_WS_URL = "wss://api.example.com";
      process.env.REACT_APP_API_VERSION = "v2";

      const config = getApiConfig();

      expect(config.API_BASE_URL).toBe("https://api.example.com");
      expect(config.WS_BASE_URL).toBe("wss://api.example.com");
      expect(config.API_VERSION).toBe("v2");
    });

    test("should remove trailing slashes from URLs", () => {
      process.env.REACT_APP_API_URL = "https://api.example.com/";
      process.env.REACT_APP_WS_URL = "wss://api.example.com/";

      const config = getApiConfig();

      expect(config.API_BASE_URL).toBe("https://api.example.com");
      expect(config.WS_BASE_URL).toBe("wss://api.example.com");
    });
  });

  describe("buildApiUrl", () => {
    test("should build correct API URL in development", () => {
      process.env.NODE_ENV = "development";
      process.env.REACT_APP_USE_PROXY = "false";

      const url = buildApiUrl("/auth/login");
      expect(url).toBe("http://localhost:8000/api/v1/auth/login");
    });

    test("should build correct API URL with custom version", () => {
      process.env.NODE_ENV = "development";
      process.env.REACT_APP_USE_PROXY = "false";

      const url = buildApiUrl("/auth/login", "v2");
      expect(url).toBe("http://localhost:8000/api/v2/auth/login");
    });

    test("should build relative URL for production with proxy", () => {
      process.env.NODE_ENV = "production";
      process.env.REACT_APP_USE_PROXY = "true";

      const url = buildApiUrl("/auth/login");
      expect(url).toBe("/api/v1/auth/login");
    });

    test("should handle leading slash in path", () => {
      process.env.NODE_ENV = "development";
      process.env.REACT_APP_USE_PROXY = "false";

      const url1 = buildApiUrl("/auth/login");
      const url2 = buildApiUrl("auth/login");

      expect(url1).toBe(url2);
      expect(url1).toBe("http://localhost:8000/api/v1/auth/login");
    });
  });

  describe("buildWsUrl", () => {
    test("should build correct WebSocket URL in development", () => {
      process.env.NODE_ENV = "development";
      process.env.REACT_APP_USE_PROXY = "false";

      const url = buildWsUrl("/ws/video");
      expect(url).toBe("ws://localhost:8000/ws/video");
    });

    test("should build relative WebSocket URL for production with proxy", () => {
      process.env.NODE_ENV = "production";
      process.env.REACT_APP_USE_PROXY = "true";

      // Mock window.location
      delete window.location;
      window.location = { protocol: "https:", host: "app.example.com" };

      const url = buildWsUrl("/ws/video");
      expect(url).toBe("wss://app.example.com/ws/video");
    });

    test("should use ws protocol for http in production with proxy", () => {
      process.env.NODE_ENV = "production";
      process.env.REACT_APP_USE_PROXY = "true";

      // Mock window.location
      delete window.location;
      window.location = { protocol: "http:", host: "localhost:3000" };

      const url = buildWsUrl("/ws/video");
      expect(url).toBe("ws://localhost:3000/ws/video");
    });

    test("should handle leading slash in path", () => {
      process.env.NODE_ENV = "development";
      process.env.REACT_APP_USE_PROXY = "false";

      const url1 = buildWsUrl("/ws/video");
      const url2 = buildWsUrl("ws/video");

      expect(url1).toBe(url2);
      expect(url1).toBe("ws://localhost:8000/ws/video");
    });
  });

  describe("buildHealthCheckUrl", () => {
    test("should build correct health check URL in development", () => {
      process.env.NODE_ENV = "development";
      process.env.REACT_APP_USE_PROXY = "false";

      const url = buildHealthCheckUrl();
      expect(url).toBe("http://localhost:8000/health");
    });

    test("should build relative health check URL for production with proxy", () => {
      process.env.NODE_ENV = "production";
      process.env.REACT_APP_USE_PROXY = "true";

      const url = buildHealthCheckUrl();
      expect(url).toBe("/health");
    });
  });

  describe("getEnvironmentInfo", () => {
    test("should return environment information", () => {
      process.env.NODE_ENV = "test";
      process.env.REACT_APP_API_URL = "https://test.example.com";
      process.env.REACT_APP_WS_URL = "wss://test.example.com";
      process.env.REACT_APP_USE_PROXY = "true";

      const info = getEnvironmentInfo();

      expect(info.NODE_ENV).toBe("test");
      expect(info.API_BASE_URL).toBe("https://test.example.com");
      expect(info.WS_BASE_URL).toBe("wss://test.example.com");
      expect(info.USE_PROXY).toBe("true");
      expect(info.REACT_APP_API_URL).toBe("https://test.example.com");
      expect(info.REACT_APP_WS_URL).toBe("wss://test.example.com");
    });
  });

  describe("Integration Tests", () => {
    test("should work with AuthService pattern", () => {
      process.env.NODE_ENV = "development";
      process.env.REACT_APP_USE_PROXY = "false";

      const loginUrl = buildApiUrl("/auth/login");
      const registerUrl = buildApiUrl("/auth/register");
      const logoutUrl = buildApiUrl("/auth/logout");

      expect(loginUrl).toBe("http://localhost:8000/api/v1/auth/login");
      expect(registerUrl).toBe("http://localhost:8000/api/v1/auth/register");
      expect(logoutUrl).toBe("http://localhost:8000/api/v1/auth/logout");
    });

    test("should work with WebSocket pattern", () => {
      process.env.NODE_ENV = "development";
      process.env.REACT_APP_USE_PROXY = "false";

      const videoWsUrl = buildWsUrl("ws/video");
      const syncWsUrl = buildWsUrl("api/v1/sync/ws/sync/session123");

      expect(videoWsUrl).toBe("ws://localhost:8000/ws/video");
      expect(syncWsUrl).toBe(
        "ws://localhost:8000/api/v1/sync/ws/sync/session123"
      );
    });

    test("should work in production environment", () => {
      process.env.NODE_ENV = "production";
      process.env.REACT_APP_USE_PROXY = "true";
      process.env.REACT_APP_API_URL = "https://api.storysign.com";

      // Mock window.location for production
      delete window.location;
      window.location = { protocol: "https:", host: "app.storysign.com" };

      const apiUrl = buildApiUrl("/auth/login");
      const wsUrl = buildWsUrl("ws/video");
      const healthUrl = buildHealthCheckUrl();

      expect(apiUrl).toBe("/api/v1/auth/login");
      expect(wsUrl).toBe("wss://app.storysign.com/ws/video");
      expect(healthUrl).toBe("/health");
    });
  });
});
