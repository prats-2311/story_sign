import React from "react";
import { render, screen, waitFor, act } from "@testing-library/react";
import "@testing-library/jest-dom";
import { AuthProvider, useAuth } from "./AuthContext";
import authService from "../services/AuthService";

// Mock React Router
const mockNavigate = jest.fn();
jest.mock("react-router-dom", () => ({
  useNavigate: () => mockNavigate,
}));

// Mock the authService
jest.mock("../services/AuthService", () => ({
  isAuthenticated: jest.fn(),
  getCurrentUser: jest.fn(),
  getToken: jest.fn(),
  verifyToken: jest.fn(),
  login: jest.fn(),
  register: jest.fn(),
  logout: jest.fn(),
  clearAuthData: jest.fn(),
  refreshToken: jest.fn(),
  updateProfile: jest.fn(),
  changePassword: jest.fn(),
  requestPasswordReset: jest.fn(),
  resetPassword: jest.fn(),
}));

// Test component that uses the auth context
const TestComponent = () => {
  const {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    register,
    clearError,
  } = useAuth();

  const handleLogin = async () => {
    try {
      await login("test@example.com", "password");
    } catch (error) {
      // Error is handled by AuthContext
    }
  };

  const handleRegister = async () => {
    try {
      await register({ email: "test@example.com", password: "password" });
    } catch (error) {
      // Error is handled by AuthContext
    }
  };

  return (
    <div>
      <div data-testid="loading">{isLoading ? "loading" : "not-loading"}</div>
      <div data-testid="authenticated">
        {isAuthenticated ? "authenticated" : "not-authenticated"}
      </div>
      <div data-testid="user">{user ? user.email : "no-user"}</div>
      <div data-testid="error">{error || "no-error"}</div>
      <button onClick={handleLogin}>Login</button>
      <button onClick={handleRegister}>Register</button>
      <button onClick={logout}>Logout</button>
      <button onClick={clearError}>Clear Error</button>
    </div>
  );
};

describe("AuthContext", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockNavigate.mockClear();
    // Reset all mocks to default values
    authService.isAuthenticated.mockReturnValue(false);
    authService.getCurrentUser.mockReturnValue(null);
    authService.getToken.mockReturnValue(null);
    authService.verifyToken.mockResolvedValue(null);
  });

  it("should throw error when useAuth is used outside AuthProvider", () => {
    // Suppress console.error for this test
    const consoleSpy = jest
      .spyOn(console, "error")
      .mockImplementation(() => {});

    expect(() => {
      render(<TestComponent />);
    }).toThrow("useAuth must be used within an AuthProvider");

    consoleSpy.mockRestore();
  });

  it("should initialize with loading state and then set to not authenticated", async () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Initially should be loading
    expect(screen.getByTestId("loading")).toHaveTextContent("loading");

    // Wait for initialization to complete
    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("not-loading");
    });

    expect(screen.getByTestId("authenticated")).toHaveTextContent(
      "not-authenticated"
    );
    expect(screen.getByTestId("user")).toHaveTextContent("no-user");
    expect(screen.getByTestId("error")).toHaveTextContent("no-error");
  });

  it("should initialize with existing authentication", async () => {
    const mockUser = { id: 1, email: "test@example.com" };
    const mockToken = "mock-token";

    authService.isAuthenticated.mockReturnValue(true);
    authService.getCurrentUser.mockReturnValue(mockUser);
    authService.getToken.mockReturnValue(mockToken);
    authService.verifyToken.mockResolvedValue(mockUser);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("not-loading");
    });

    expect(screen.getByTestId("authenticated")).toHaveTextContent(
      "authenticated"
    );
    expect(screen.getByTestId("user")).toHaveTextContent("test@example.com");
    expect(authService.verifyToken).toHaveBeenCalled();
  });

  it("should handle failed token verification during initialization", async () => {
    authService.isAuthenticated.mockReturnValue(true);
    authService.getCurrentUser.mockReturnValue({
      id: 1,
      email: "test@example.com",
    });
    authService.getToken.mockReturnValue("invalid-token");
    authService.verifyToken.mockResolvedValue(null);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("not-loading");
    });

    expect(screen.getByTestId("authenticated")).toHaveTextContent(
      "not-authenticated"
    );
    expect(authService.clearAuthData).toHaveBeenCalled();
  });

  it("should handle successful login", async () => {
    const mockUser = { id: 1, email: "test@example.com" };
    const mockResponse = { user: mockUser, token: "new-token" };

    authService.login.mockResolvedValue(mockResponse);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("not-loading");
    });

    // Click login button
    act(() => {
      screen.getByText("Login").click();
    });

    // Should show loading during login
    expect(screen.getByTestId("loading")).toHaveTextContent("loading");

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("not-loading");
    });

    expect(screen.getByTestId("authenticated")).toHaveTextContent(
      "authenticated"
    );
    expect(screen.getByTestId("user")).toHaveTextContent("test@example.com");
    expect(authService.login).toHaveBeenCalledWith(
      "test@example.com",
      "password",
      false
    );
  });

  it("should handle login failure", async () => {
    const mockError = new Error("Invalid credentials");
    authService.login.mockRejectedValue(mockError);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("not-loading");
    });

    // Click login button
    act(() => {
      screen.getByText("Login").click();
    });

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("not-loading");
    });

    expect(screen.getByTestId("authenticated")).toHaveTextContent(
      "not-authenticated"
    );
    expect(screen.getByTestId("error")).toHaveTextContent(
      "Invalid email or password. Please check your credentials and try again."
    );
  });

  it("should handle successful registration", async () => {
    const mockResponse = { message: "Registration successful" };
    authService.register.mockResolvedValue(mockResponse);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("not-loading");
    });

    // Click register button
    act(() => {
      screen.getByText("Register").click();
    });

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("not-loading");
    });

    // Should not be authenticated after registration
    expect(screen.getByTestId("authenticated")).toHaveTextContent(
      "not-authenticated"
    );
    expect(authService.register).toHaveBeenCalledWith({
      email: "test@example.com",
      password: "password",
    });
  });

  it("should handle logout with navigation", async () => {
    const mockUser = { id: 1, email: "test@example.com" };

    // Start with authenticated state
    authService.isAuthenticated.mockReturnValue(true);
    authService.getCurrentUser.mockReturnValue(mockUser);
    authService.getToken.mockReturnValue("token");
    authService.verifyToken.mockResolvedValue(mockUser);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Wait for authentication
    await waitFor(() => {
      expect(screen.getByTestId("authenticated")).toHaveTextContent(
        "authenticated"
      );
    });

    // Click logout button
    act(() => {
      screen.getByText("Logout").click();
    });

    await waitFor(() => {
      expect(screen.getByTestId("authenticated")).toHaveTextContent(
        "not-authenticated"
      );
    });

    expect(screen.getByTestId("user")).toHaveTextContent("no-user");
    expect(authService.logout).toHaveBeenCalled();
    expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true });
  });

  it("should handle logout with server error and still navigate", async () => {
    const mockUser = { id: 1, email: "test@example.com" };

    // Start with authenticated state
    authService.isAuthenticated.mockReturnValue(true);
    authService.getCurrentUser.mockReturnValue(mockUser);
    authService.getToken.mockReturnValue("token");
    authService.verifyToken.mockResolvedValue(mockUser);

    // Mock logout to fail
    authService.logout.mockRejectedValue(new Error("Server error"));

    // Suppress console.error for this test
    const consoleSpy = jest
      .spyOn(console, "error")
      .mockImplementation(() => {});

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Wait for authentication
    await waitFor(() => {
      expect(screen.getByTestId("authenticated")).toHaveTextContent(
        "authenticated"
      );
    });

    // Click logout button
    await act(async () => {
      screen.getByText("Logout").click();
    });

    await waitFor(() => {
      expect(screen.getByTestId("authenticated")).toHaveTextContent(
        "not-authenticated"
      );
    });

    // Wait for navigation to be called
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true });
    });

    expect(screen.getByTestId("user")).toHaveTextContent("no-user");
    expect(authService.logout).toHaveBeenCalled();

    consoleSpy.mockRestore();
  });

  it("should handle logout with navigation error and use fallback", async () => {
    const mockUser = { id: 1, email: "test@example.com" };

    // Start with authenticated state
    authService.isAuthenticated.mockReturnValue(true);
    authService.getCurrentUser.mockReturnValue(mockUser);
    authService.getToken.mockReturnValue("token");
    authService.verifyToken.mockResolvedValue(mockUser);

    // Mock navigate to fail
    mockNavigate.mockImplementation(() => {
      throw new Error("Navigation error");
    });

    // Mock window.location
    const mockLocation = { href: "" };
    Object.defineProperty(window, "location", {
      value: mockLocation,
      writable: true,
    });

    // Suppress console.error for this test
    const consoleSpy = jest
      .spyOn(console, "error")
      .mockImplementation(() => {});

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Wait for authentication
    await waitFor(() => {
      expect(screen.getByTestId("authenticated")).toHaveTextContent(
        "authenticated"
      );
    });

    // Click logout button
    act(() => {
      screen.getByText("Logout").click();
    });

    await waitFor(() => {
      expect(screen.getByTestId("authenticated")).toHaveTextContent(
        "not-authenticated"
      );
    });

    expect(screen.getByTestId("user")).toHaveTextContent("no-user");
    expect(authService.logout).toHaveBeenCalled();
    expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true });
    expect(mockLocation.href).toBe("/login");

    consoleSpy.mockRestore();
  });

  // Enhanced logout functionality tests for task 6
  describe("Enhanced Logout Functionality", () => {
    it("should clear localStorage and sessionStorage on logout", async () => {
      const mockUser = { id: 1, email: "test@example.com" };

      // Start with authenticated state
      authService.isAuthenticated.mockReturnValue(true);
      authService.getCurrentUser.mockReturnValue(mockUser);
      authService.getToken.mockReturnValue("token");
      authService.verifyToken.mockResolvedValue(mockUser);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Wait for authentication
      await waitFor(() => {
        expect(screen.getByTestId("authenticated")).toHaveTextContent(
          "authenticated"
        );
      });

      // Click logout button
      act(() => {
        screen.getByText("Logout").click();
      });

      await waitFor(() => {
        expect(screen.getByTestId("authenticated")).toHaveTextContent(
          "not-authenticated"
        );
      });

      // Verify authService.logout was called (which handles localStorage cleanup internally)
      expect(authService.logout).toHaveBeenCalled();
    });

    it("should reset authentication state completely on logout", async () => {
      const mockUser = { id: 1, email: "test@example.com" };

      // Start with authenticated state
      authService.isAuthenticated.mockReturnValue(true);
      authService.getCurrentUser.mockReturnValue(mockUser);
      authService.getToken.mockReturnValue("token");
      authService.verifyToken.mockResolvedValue(mockUser);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Wait for authentication
      await waitFor(() => {
        expect(screen.getByTestId("authenticated")).toHaveTextContent(
          "authenticated"
        );
        expect(screen.getByTestId("user")).toHaveTextContent(
          "test@example.com"
        );
      });

      // Click logout button
      act(() => {
        screen.getByText("Logout").click();
      });

      await waitFor(() => {
        expect(screen.getByTestId("authenticated")).toHaveTextContent(
          "not-authenticated"
        );
      });

      // Verify complete state reset
      expect(screen.getByTestId("user")).toHaveTextContent("no-user");
      expect(screen.getByTestId("error")).toHaveTextContent("no-error");
      expect(screen.getByTestId("loading")).toHaveTextContent("not-loading");
    });

    it("should navigate to login page with replace: true on logout", async () => {
      const mockUser = { id: 1, email: "test@example.com" };

      // Start with authenticated state
      authService.isAuthenticated.mockReturnValue(true);
      authService.getCurrentUser.mockReturnValue(mockUser);
      authService.getToken.mockReturnValue("token");
      authService.verifyToken.mockResolvedValue(mockUser);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Wait for authentication
      await waitFor(() => {
        expect(screen.getByTestId("authenticated")).toHaveTextContent(
          "authenticated"
        );
      });

      // Click logout button
      act(() => {
        screen.getByText("Logout").click();
      });

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true });
      });

      // Verify state was reset
      expect(screen.getByTestId("authenticated")).toHaveTextContent(
        "not-authenticated"
      );
    });

    it("should handle logout when authService.logout throws an error", async () => {
      const mockUser = { id: 1, email: "test@example.com" };

      // Start with authenticated state
      authService.isAuthenticated.mockReturnValue(true);
      authService.getCurrentUser.mockReturnValue(mockUser);
      authService.getToken.mockReturnValue("token");
      authService.verifyToken.mockResolvedValue(mockUser);

      // Mock authService.logout to throw an error
      authService.logout.mockRejectedValue(new Error("Server logout failed"));

      // Suppress console.error for this test
      const consoleSpy = jest
        .spyOn(console, "error")
        .mockImplementation(() => {});

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Wait for authentication
      await waitFor(() => {
        expect(screen.getByTestId("authenticated")).toHaveTextContent(
          "authenticated"
        );
      });

      // Click logout button
      await act(async () => {
        screen.getByText("Logout").click();
      });

      await waitFor(() => {
        expect(screen.getByTestId("authenticated")).toHaveTextContent(
          "not-authenticated"
        );
      });

      // Verify logout was attempted
      expect(authService.logout).toHaveBeenCalled();

      // Wait for navigation to be called
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true });
      });

      // Verify state was reset despite server error
      expect(screen.getByTestId("user")).toHaveTextContent("no-user");

      consoleSpy.mockRestore();
    });

    it("should handle logout when both authService.logout and navigation fail", async () => {
      const mockUser = { id: 1, email: "test@example.com" };

      // Start with authenticated state
      authService.isAuthenticated.mockReturnValue(true);
      authService.getCurrentUser.mockReturnValue(mockUser);
      authService.getToken.mockReturnValue("token");
      authService.verifyToken.mockResolvedValue(mockUser);

      // Mock authService.logout to throw an error
      authService.logout.mockRejectedValue(new Error("Server logout failed"));

      // Mock navigate to fail
      mockNavigate.mockImplementation(() => {
        throw new Error("Navigation failed");
      });

      // Mock window.location
      const mockLocation = { href: "" };
      Object.defineProperty(window, "location", {
        value: mockLocation,
        writable: true,
      });

      // Suppress console.error for this test
      const consoleSpy = jest
        .spyOn(console, "error")
        .mockImplementation(() => {});

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Wait for authentication
      await waitFor(() => {
        expect(screen.getByTestId("authenticated")).toHaveTextContent(
          "authenticated"
        );
      });

      // Click logout button
      await act(async () => {
        screen.getByText("Logout").click();
      });

      await waitFor(() => {
        expect(screen.getByTestId("authenticated")).toHaveTextContent(
          "not-authenticated"
        );
      });

      // Verify logout was attempted
      expect(authService.logout).toHaveBeenCalled();

      // Wait for navigation to be attempted
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true });
      });

      // Verify fallback navigation was used
      expect(mockLocation.href).toBe("/login");

      // Verify state was reset despite all errors
      expect(screen.getByTestId("user")).toHaveTextContent("no-user");

      consoleSpy.mockRestore();
    });

    it("should maintain logout functionality when user is not authenticated", async () => {
      // Start with unauthenticated state
      authService.isAuthenticated.mockReturnValue(false);
      authService.getCurrentUser.mockReturnValue(null);
      authService.getToken.mockReturnValue(null);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Wait for initialization
      await waitFor(() => {
        expect(screen.getByTestId("loading")).toHaveTextContent("not-loading");
      });

      expect(screen.getByTestId("authenticated")).toHaveTextContent(
        "not-authenticated"
      );

      // Click logout button (should still work even when not authenticated)
      act(() => {
        screen.getByText("Logout").click();
      });

      // Should still call logout and navigate
      await waitFor(() => {
        expect(authService.logout).toHaveBeenCalled();
      });

      expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true });
    });

    it("should clear any existing errors on logout", async () => {
      const mockUser = { id: 1, email: "test@example.com" };
      const mockError = new Error("Some previous error");

      // Start with unauthenticated state
      authService.isAuthenticated.mockReturnValue(false);
      authService.getCurrentUser.mockReturnValue(null);
      authService.getToken.mockReturnValue(null);

      // Mock login to fail first to create an error state
      authService.login.mockRejectedValue(mockError);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Wait for initialization
      await waitFor(() => {
        expect(screen.getByTestId("loading")).toHaveTextContent("not-loading");
      });

      // Trigger an error by attempting login
      act(() => {
        screen.getByText("Login").click();
      });

      await waitFor(() => {
        expect(screen.getByTestId("error")).not.toHaveTextContent("no-error");
      });

      // Now mock successful authentication and login
      authService.login.mockResolvedValue({
        user: mockUser,
        token: "new-token",
      });

      // Login successfully
      act(() => {
        screen.getByText("Login").click();
      });

      await waitFor(() => {
        expect(screen.getByTestId("authenticated")).toHaveTextContent(
          "authenticated"
        );
      });

      // Now logout
      act(() => {
        screen.getByText("Logout").click();
      });

      await waitFor(() => {
        expect(screen.getByTestId("authenticated")).toHaveTextContent(
          "not-authenticated"
        );
      });

      // Verify error was cleared by logout action
      expect(screen.getByTestId("error")).toHaveTextContent("no-error");
      expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true });
    });

    it("should handle multiple rapid logout calls gracefully", async () => {
      const mockUser = { id: 1, email: "test@example.com" };

      // Start with authenticated state
      authService.isAuthenticated.mockReturnValue(true);
      authService.getCurrentUser.mockReturnValue(mockUser);
      authService.getToken.mockReturnValue("token");
      authService.verifyToken.mockResolvedValue(mockUser);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Wait for authentication
      await waitFor(() => {
        expect(screen.getByTestId("authenticated")).toHaveTextContent(
          "authenticated"
        );
      });

      // Click logout button multiple times rapidly
      await act(async () => {
        screen.getByText("Logout").click();
        screen.getByText("Logout").click();
        screen.getByText("Logout").click();
      });

      await waitFor(() => {
        expect(screen.getByTestId("authenticated")).toHaveTextContent(
          "not-authenticated"
        );
      });

      // Should still work correctly
      expect(authService.logout).toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true });
      expect(screen.getByTestId("user")).toHaveTextContent("no-user");
    });

    it("should preserve logout functionality after token refresh failure", async () => {
      const mockUser = { id: 1, email: "test@example.com" };

      // Start with authenticated state
      authService.isAuthenticated.mockReturnValue(true);
      authService.getCurrentUser.mockReturnValue(mockUser);
      authService.getToken.mockReturnValue("token");
      authService.verifyToken.mockResolvedValue(mockUser);

      // Mock token refresh to fail
      authService.refreshToken.mockResolvedValue(false);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Wait for authentication
      await waitFor(() => {
        expect(screen.getByTestId("authenticated")).toHaveTextContent(
          "authenticated"
        );
      });

      // Logout should still work even if token refresh failed
      await act(async () => {
        screen.getByText("Logout").click();
      });

      await waitFor(() => {
        expect(screen.getByTestId("authenticated")).toHaveTextContent(
          "not-authenticated"
        );
      });

      expect(authService.logout).toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true });
    });

    it("should handle logout with network connectivity issues", async () => {
      const mockUser = { id: 1, email: "test@example.com" };

      // Start with authenticated state
      authService.isAuthenticated.mockReturnValue(true);
      authService.getCurrentUser.mockReturnValue(mockUser);
      authService.getToken.mockReturnValue("token");
      authService.verifyToken.mockResolvedValue(mockUser);

      // Mock logout to fail with network error
      const networkError = new Error("Network error");
      networkError.name = "TypeError";
      authService.logout.mockRejectedValue(networkError);

      // Suppress console.error for this test
      const consoleSpy = jest
        .spyOn(console, "error")
        .mockImplementation(() => {});

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      // Wait for authentication
      await waitFor(() => {
        expect(screen.getByTestId("authenticated")).toHaveTextContent(
          "authenticated"
        );
      });

      // Logout should still work despite network issues
      await act(async () => {
        screen.getByText("Logout").click();
      });

      await waitFor(() => {
        expect(screen.getByTestId("authenticated")).toHaveTextContent(
          "not-authenticated"
        );
      });

      expect(authService.logout).toHaveBeenCalled();
      expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true });
      expect(screen.getByTestId("user")).toHaveTextContent("no-user");

      consoleSpy.mockRestore();
    });

    it("should verify authentication state is completely reset after logout", async () => {
      const mockUser = {
        id: 1,
        email: "test@example.com",
        roles: ["user"],
        permissions: ["read"],
      };

      // Start with authenticated state
      authService.isAuthenticated.mockReturnValue(true);
      authService.getCurrentUser.mockReturnValue(mockUser);
      authService.getToken.mockReturnValue("token");
      authService.verifyToken.mockResolvedValue(mockUser);

      const TestComponentWithRoles = () => {
        const { user, isAuthenticated, hasRole, hasPermission, logout } =
          useAuth();

        return (
          <div>
            <div data-testid="authenticated">
              {isAuthenticated ? "authenticated" : "not-authenticated"}
            </div>
            <div data-testid="user">{user ? user.email : "no-user"}</div>
            <div data-testid="has-role">
              {hasRole("user") ? "has-role" : "no-role"}
            </div>
            <div data-testid="has-permission">
              {hasPermission("read") ? "has-permission" : "no-permission"}
            </div>
            <button onClick={logout}>Logout</button>
          </div>
        );
      };

      render(
        <AuthProvider>
          <TestComponentWithRoles />
        </AuthProvider>
      );

      // Wait for authentication
      await waitFor(() => {
        expect(screen.getByTestId("authenticated")).toHaveTextContent(
          "authenticated"
        );
        expect(screen.getByTestId("has-role")).toHaveTextContent("has-role");
        expect(screen.getByTestId("has-permission")).toHaveTextContent(
          "has-permission"
        );
      });

      // Logout
      await act(async () => {
        screen.getByText("Logout").click();
      });

      await waitFor(() => {
        expect(screen.getByTestId("authenticated")).toHaveTextContent(
          "not-authenticated"
        );
      });

      // Verify all authentication-related state is reset
      expect(screen.getByTestId("user")).toHaveTextContent("no-user");
      expect(screen.getByTestId("has-role")).toHaveTextContent("no-role");
      expect(screen.getByTestId("has-permission")).toHaveTextContent(
        "no-permission"
      );
      expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true });
    });
  });

  it("should clear error when clearError is called", async () => {
    const mockError = new Error("Test error");
    authService.login.mockRejectedValue(mockError);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("not-loading");
    });

    // Trigger an error
    act(() => {
      screen.getByText("Login").click();
    });

    await waitFor(() => {
      expect(screen.getByTestId("error")).toHaveTextContent("Test error");
    });

    // Clear the error
    act(() => {
      screen.getByText("Clear Error").click();
    });

    expect(screen.getByTestId("error")).toHaveTextContent("no-error");
  });

  it("should handle initialization error gracefully", async () => {
    authService.isAuthenticated.mockReturnValue(true);
    authService.getCurrentUser.mockReturnValue({
      id: 1,
      email: "test@example.com",
    });
    authService.getToken.mockReturnValue("token");
    authService.verifyToken.mockRejectedValue(new Error("Network error"));

    // Suppress console.error for this test
    const consoleSpy = jest
      .spyOn(console, "error")
      .mockImplementation(() => {});

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("not-loading");
    });

    expect(screen.getByTestId("authenticated")).toHaveTextContent(
      "not-authenticated"
    );
    expect(authService.clearAuthData).toHaveBeenCalled();

    consoleSpy.mockRestore();
  });
});
