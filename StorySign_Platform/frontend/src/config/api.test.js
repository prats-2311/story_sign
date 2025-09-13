/**
 * Tests for simplified API configuration
 */

import API_BASE_URL from "./api";

describe("API Configuration", () => {
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
});
