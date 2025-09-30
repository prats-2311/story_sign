import authService from "./AuthService";

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

describe("AuthService Logout Functionality", () => {
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

  describe("logout method", () => {
    it("should call server logout endpoint and clear auth data", async () => {
      // Mock token exists
      localStorageMock.getItem.mockReturnValue("test-token");

      // Mock successful server logout
      fetch.mockResolvedValue({
        ok: true,
        status: 200,
      });

      await authService.logout();

      // Verify server logout was called
      expect(fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/v1/auth/logout",
        {
          method: "POST",
          headers: {
            Authorization: "Bearer test-token",
            "Content-Type": "application/json",
          },
        }
      );

      // Verify localStorage cleanup
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("auth_token");
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("auth_user");
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("refresh_token");

      // Verify sessionStorage cleanup
      expect(sessionStorageMock.removeItem).toHaveBeenCalledWith("auth_token");
      expect(sessionStorageMock.removeItem).toHaveBeenCalledWith("auth_user");
      expect(sessionStorageMock.removeItem).toHaveBeenCalledWith(
        "refresh_token"
      );
    });

    it("should clear auth data even when server logout fails", async () => {
      // Mock token exists
      localStorageMock.getItem.mockReturnValue("test-token");

      // Mock server logout failure
      fetch.mockRejectedValue(new Error("Server error"));

      // Suppress console.warn for this test
      const consoleSpy = jest
        .spyOn(console, "warn")
        .mockImplementation(() => {});

      await authService.logout();

      // Verify server logout was attempted
      expect(fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/v1/auth/logout",
        {
          method: "POST",
          headers: {
            Authorization: "Bearer test-token",
            "Content-Type": "application/json",
          },
        }
      );

      // Verify localStorage cleanup still happened
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("auth_token");
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("auth_user");
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("refresh_token");

      // Verify sessionStorage cleanup still happened
      expect(sessionStorageMock.removeItem).toHaveBeenCalledWith("auth_token");
      expect(sessionStorageMock.removeItem).toHaveBeenCalledWith("auth_user");
      expect(sessionStorageMock.removeItem).toHaveBeenCalledWith(
        "refresh_token"
      );

      consoleSpy.mockRestore();
    });

    it("should handle logout when no token exists", async () => {
      // Mock no token exists
      localStorageMock.getItem.mockReturnValue(null);
      sessionStorageMock.getItem.mockReturnValue(null);

      await authService.logout();

      // Verify no server call was made (no token to send)
      expect(fetch).not.toHaveBeenCalled();

      // Verify cleanup still happened
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("auth_token");
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("auth_user");
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("refresh_token");
      expect(sessionStorageMock.removeItem).toHaveBeenCalledWith("auth_token");
      expect(sessionStorageMock.removeItem).toHaveBeenCalledWith("auth_user");
      expect(sessionStorageMock.removeItem).toHaveBeenCalledWith(
        "refresh_token"
      );
    });

    it("should handle network errors during logout gracefully", async () => {
      // Mock token exists
      localStorageMock.getItem.mockReturnValue("test-token");

      // Mock network error
      const networkError = new Error("Network error");
      networkError.name = "TypeError";
      fetch.mockRejectedValue(networkError);

      // Suppress console.warn for this test
      const consoleSpy = jest
        .spyOn(console, "warn")
        .mockImplementation(() => {});

      await authService.logout();

      // Verify server logout was attempted
      expect(fetch).toHaveBeenCalled();

      // Verify cleanup still happened despite network error
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("auth_token");
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("auth_user");
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("refresh_token");

      consoleSpy.mockRestore();
    });
  });

  describe("clearAuthData method", () => {
    it("should remove all auth-related items from both localStorage and sessionStorage", () => {
      authService.clearAuthData();

      // Verify localStorage cleanup
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("auth_token");
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("auth_user");
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("refresh_token");

      // Verify sessionStorage cleanup
      expect(sessionStorageMock.removeItem).toHaveBeenCalledWith("auth_token");
      expect(sessionStorageMock.removeItem).toHaveBeenCalledWith("auth_user");
      expect(sessionStorageMock.removeItem).toHaveBeenCalledWith(
        "refresh_token"
      );
    });

    it("should attempt to clear all storage items", () => {
      authService.clearAuthData();

      // Verify all removal attempts were made
      expect(localStorageMock.removeItem).toHaveBeenCalledTimes(3);
      expect(sessionStorageMock.removeItem).toHaveBeenCalledTimes(3);

      // Verify specific keys were targeted
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("auth_token");
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("auth_user");
      expect(localStorageMock.removeItem).toHaveBeenCalledWith("refresh_token");
      expect(sessionStorageMock.removeItem).toHaveBeenCalledWith("auth_token");
      expect(sessionStorageMock.removeItem).toHaveBeenCalledWith("auth_user");
      expect(sessionStorageMock.removeItem).toHaveBeenCalledWith(
        "refresh_token"
      );
    });
  });

  describe("getToken method", () => {
    it("should return null after logout", () => {
      // Mock token initially exists
      localStorageMock.getItem.mockReturnValue("test-token");

      // Get token before logout
      const tokenBefore = authService.getToken();
      expect(tokenBefore).toBe("test-token");

      // Clear auth data (simulating logout)
      authService.clearAuthData();

      // Mock token no longer exists after cleanup
      localStorageMock.getItem.mockReturnValue(null);
      sessionStorageMock.getItem.mockReturnValue(null);

      // Get token after logout
      const tokenAfter = authService.getToken();
      expect(tokenAfter).toBeNull();
    });
  });

  describe("getCurrentUser method", () => {
    it("should return null after logout", () => {
      // Mock user initially exists
      const mockUser = { id: 1, email: "test@example.com" };
      localStorageMock.getItem.mockReturnValue(JSON.stringify(mockUser));

      // Get user before logout
      const userBefore = authService.getCurrentUser();
      expect(userBefore).toEqual(mockUser);

      // Clear auth data (simulating logout)
      authService.clearAuthData();

      // Mock user no longer exists after cleanup
      localStorageMock.getItem.mockReturnValue(null);
      sessionStorageMock.getItem.mockReturnValue(null);

      // Get user after logout
      const userAfter = authService.getCurrentUser();
      expect(userAfter).toBeNull();
    });
  });

  describe("isAuthenticated method", () => {
    it("should return false after logout", () => {
      // Mock valid token initially exists
      const validToken =
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjk5OTk5OTk5OTl9.Lp-38RNpyBo3_eFbXdYjKZZzSof1HCQWs6bK-3P6MhE";
      localStorageMock.getItem.mockReturnValue(validToken);

      // Should be authenticated before logout
      const authBefore = authService.isAuthenticated();
      expect(authBefore).toBe(true);

      // Clear auth data (simulating logout)
      authService.clearAuthData();

      // Mock token no longer exists after cleanup
      localStorageMock.getItem.mockReturnValue(null);
      sessionStorageMock.getItem.mockReturnValue(null);

      // Should not be authenticated after logout
      const authAfter = authService.isAuthenticated();
      expect(authAfter).toBe(false);
    });
  });
});
