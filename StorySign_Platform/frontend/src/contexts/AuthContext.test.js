import React from "react";
import { render, screen, waitFor, act } from "@testing-library/react";
import "@testing-library/jest-dom";
import { AuthProvider, useAuth } from "./AuthContext";
import authService from "../services/AuthService";

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

  return (
    <div>
      <div data-testid="loading">{isLoading ? "loading" : "not-loading"}</div>
      <div data-testid="authenticated">
        {isAuthenticated ? "authenticated" : "not-authenticated"}
      </div>
      <div data-testid="user">{user ? user.email : "no-user"}</div>
      <div data-testid="error">{error || "no-error"}</div>
      <button onClick={() => login("test@example.com", "password")}>
        Login
      </button>
      <button
        onClick={() =>
          register({ email: "test@example.com", password: "password" })
        }
      >
        Register
      </button>
      <button onClick={logout}>Logout</button>
      <button onClick={clearError}>Clear Error</button>
    </div>
  );
};

describe("AuthContext", () => {
  beforeEach(() => {
    jest.clearAllMocks();
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
      "Invalid credentials"
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

  it("should handle logout", async () => {
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
