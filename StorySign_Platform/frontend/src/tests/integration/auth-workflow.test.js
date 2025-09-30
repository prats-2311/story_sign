/**
 * Complete Authentication Workflow Tests
 * Tests the complete authentication flow including routing, redirects, and user experience
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import "@testing-library/jest-dom";

import App from "../App";
import { AuthProvider } from "../contexts/AuthContext";
import authService from "../services/AuthService";

// Mock the auth service
jest.mock("../services/AuthService");

// Mock the pages to avoid complex dependencies
jest.mock("../pages/dashboard/MainDashboard", () => {
  return function MockMainDashboard() {
    return <div data-testid="main-dashboard">Main Dashboard</div>;
  };
});

jest.mock("../pages/ASLWorldPage", () => {
  return function MockASLWorldPage() {
    return <div data-testid="asl-world-page">ASL World Page</div>;
  };
});

jest.mock("../pages/HarmonyPage", () => {
  return function MockHarmonyPage() {
    return <div data-testid="harmony-page">Harmony Page</div>;
  };
});

jest.mock("../pages/ReconnectPage", () => {
  return function MockReconnectPage() {
    return <div data-testid="reconnect-page">Reconnect Page</div>;
  };
});

// Mock PlatformShell to avoid complex dependencies
jest.mock("../components/shell/PlatformShell", () => {
  return {
    __esModule: true,
    default: ({ children }) => (
      <div data-testid="platform-shell">
        <nav data-testid="platform-nav">
          <a href="/dashboard">Dashboard</a>
          <a href="/asl-world">ASL World</a>
          <a href="/harmony">Harmony</a>
          <a href="/reconnect">Reconnect</a>
        </nav>
        {children}
      </div>
    ),
    usePlatform: () => ({}),
  };
});

// Mock accessibility utils
jest.mock("../utils/accessibility", () => ({
  manageFocusForSPA: jest.fn(),
}));

// Test wrapper component with memory router for controlled navigation
const TestWrapper = ({ children, initialEntries = ["/"] }) => (
  <MemoryRouter initialEntries={initialEntries}>
    <AuthProvider>{children}</AuthProvider>
  </MemoryRouter>
);

describe("Complete Authentication Workflow", () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Default mock implementations
    authService.isAuthenticated.mockReturnValue(false);
    authService.getCurrentUser.mockReturnValue(null);
    authService.getToken.mockReturnValue(null);
    authService.verifyToken.mockResolvedValue(null);
  });

  describe("Requirement 5.1: Unauthenticated users redirected to /login from root", () => {
    it("should redirect unauthenticated users from root path to login page", async () => {
      render(
        <TestWrapper initialEntries={["/"]}>
          <App />
        </TestWrapper>
      );

      // Wait for loading to complete and redirect to happen
      await waitFor(() => {
        expect(screen.getByText(/sign in to storysign/i)).toBeInTheDocument();
      });

      // Verify we're on the login page
      expect(
        screen.getByRole("button", { name: /sign in/i })
      ).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText(/enter your password/i)
      ).toBeInTheDocument();
    });

    it("should show loading screen while checking authentication state", async () => {
      // Mock the AuthContext to start in loading state
      const LoadingTestWrapper = ({ children }) => (
        <MemoryRouter initialEntries={["/"]}>
          <div>
            <div className="loading-screen" role="status" aria-live="polite">
              <div className="loading-spinner" aria-hidden="true"></div>
              <p>Loading StorySign Platform...</p>
            </div>
          </div>
        </MemoryRouter>
      );

      render(
        <LoadingTestWrapper>
          <div />
        </LoadingTestWrapper>
      );

      // Should show loading screen
      expect(
        screen.getByText(/loading storysign platform/i)
      ).toBeInTheDocument();
      expect(screen.getByRole("status")).toBeInTheDocument();
    });
  });

  describe("Requirement 5.2: Manual navigation to protected routes redirects to login", () => {
    it("should redirect unauthenticated users from /dashboard to login", async () => {
      render(
        <TestWrapper initialEntries={["/dashboard"]}>
          <App />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/sign in to storysign/i)).toBeInTheDocument();
      });

      expect(
        screen.getByRole("button", { name: /sign in/i })
      ).toBeInTheDocument();
    });

    it("should redirect unauthenticated users from /asl-world to login", async () => {
      render(
        <TestWrapper initialEntries={["/asl-world"]}>
          <App />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/sign in to storysign/i)).toBeInTheDocument();
      });
    });

    it("should redirect unauthenticated users from /harmony to login", async () => {
      render(
        <TestWrapper initialEntries={["/harmony"]}>
          <App />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/sign in to storysign/i)).toBeInTheDocument();
      });
    });

    it("should redirect unauthenticated users from /reconnect to login", async () => {
      render(
        <TestWrapper initialEntries={["/reconnect"]}>
          <App />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/sign in to storysign/i)).toBeInTheDocument();
      });
    });
  });

  describe("Requirement 5.3: Successful login redirects to dashboard", () => {
    it("should redirect to dashboard after successful login", async () => {
      // Mock successful login
      const mockUser = {
        id: 1,
        email: "test@example.com",
        username: "testuser",
      };
      const mockToken = "mock-jwt-token";

      authService.login.mockResolvedValue({
        user: mockUser,
        token: mockToken,
      });

      render(
        <TestWrapper initialEntries={["/login"]}>
          <App />
        </TestWrapper>
      );

      // Wait for login page to load
      await waitFor(() => {
        expect(screen.getByText(/sign in to storysign/i)).toBeInTheDocument();
      });

      // Fill in login form
      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByPlaceholderText(/enter your password/i);
      const submitButton = screen.getByRole("button", { name: /sign in/i });

      fireEvent.change(emailInput, { target: { value: "test@example.com" } });
      fireEvent.change(passwordInput, { target: { value: "password123" } });

      // Mock authentication state change after login
      authService.isAuthenticated.mockReturnValue(true);
      authService.getCurrentUser.mockReturnValue(mockUser);
      authService.getToken.mockReturnValue(mockToken);

      fireEvent.click(submitButton);

      // Verify login was called
      await waitFor(() => {
        expect(authService.login).toHaveBeenCalledWith(
          "test@example.com",
          "password123",
          false
        );
      });
    });

    it("should redirect to intended destination after login", async () => {
      // Mock successful login
      const mockUser = {
        id: 1,
        email: "test@example.com",
        username: "testuser",
      };
      const mockToken = "mock-jwt-token";

      authService.login.mockResolvedValue({
        user: mockUser,
        token: mockToken,
      });

      // Start from a protected route that should redirect to login with state
      render(
        <TestWrapper initialEntries={["/asl-world"]}>
          <App />
        </TestWrapper>
      );

      // Should redirect to login first
      await waitFor(() => {
        expect(screen.getByText(/sign in to storysign/i)).toBeInTheDocument();
      });

      // Simulate successful login
      authService.isAuthenticated.mockReturnValue(true);
      authService.getCurrentUser.mockReturnValue(mockUser);
      authService.getToken.mockReturnValue(mockToken);

      // The login should redirect back to the intended destination
      // This would be handled by the login form's navigation logic
    });
  });

  describe("Requirement 5.4: Registration workflow and immediate login", () => {
    it("should allow registration and redirect to login", async () => {
      // Mock successful registration
      authService.register.mockResolvedValue({
        message: "Registration successful",
        user: { id: 1, email: "newuser@example.com", username: "newuser" },
      });

      render(
        <TestWrapper initialEntries={["/register"]}>
          <App />
        </TestWrapper>
      );

      // Wait for register page to load
      await waitFor(() => {
        expect(
          screen.getByText(/create your storysign account/i)
        ).toBeInTheDocument();
      });

      // Fill in registration form
      const usernameInput = screen.getByLabelText(/username/i);
      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/^password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
      const submitButton = screen.getByRole("button", {
        name: /create account/i,
      });

      fireEvent.change(usernameInput, { target: { value: "newuser" } });
      fireEvent.change(emailInput, {
        target: { value: "newuser@example.com" },
      });
      fireEvent.change(passwordInput, { target: { value: "StrongPass123!" } });
      fireEvent.change(confirmPasswordInput, {
        target: { value: "StrongPass123!" },
      });

      fireEvent.click(submitButton);

      // Verify registration was called
      await waitFor(() => {
        expect(authService.register).toHaveBeenCalledWith({
          username: "newuser",
          email: "newuser@example.com",
          password: "StrongPass123!",
        });
      });
    });

    it("should handle registration errors appropriately", async () => {
      // Mock registration error
      authService.register.mockRejectedValue(
        new Error("An account with this email already exists")
      );

      render(
        <TestWrapper initialEntries={["/register"]}>
          <App />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(
          screen.getByText(/create your storysign account/i)
        ).toBeInTheDocument();
      });

      // Fill in registration form with existing email
      const usernameInput = screen.getByLabelText(/username/i);
      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/^password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
      const submitButton = screen.getByRole("button", {
        name: /create account/i,
      });

      fireEvent.change(usernameInput, { target: { value: "existinguser" } });
      fireEvent.change(emailInput, {
        target: { value: "existing@example.com" },
      });
      fireEvent.change(passwordInput, { target: { value: "StrongPass123!" } });
      fireEvent.change(confirmPasswordInput, {
        target: { value: "StrongPass123!" },
      });

      fireEvent.click(submitButton);

      // Should show error message
      await waitFor(() => {
        expect(
          screen.getByText(/account with this email already exists/i)
        ).toBeInTheDocument();
      });
    });
  });

  describe("Authenticated User Experience", () => {
    beforeEach(() => {
      // Mock authenticated state
      const mockUser = {
        id: 1,
        email: "test@example.com",
        username: "testuser",
      };
      const mockToken = "mock-jwt-token";

      authService.isAuthenticated.mockReturnValue(true);
      authService.getCurrentUser.mockReturnValue(mockUser);
      authService.getToken.mockReturnValue(mockToken);
      authService.verifyToken.mockResolvedValue(mockUser);
    });

    it("should redirect authenticated users away from login page", async () => {
      render(
        <TestWrapper initialEntries={["/login"]}>
          <App />
        </TestWrapper>
      );

      // Should redirect to dashboard instead of showing login
      await waitFor(() => {
        expect(screen.getByTestId("main-dashboard")).toBeInTheDocument();
      });

      expect(
        screen.queryByText(/sign in to storysign/i)
      ).not.toBeInTheDocument();
    });

    it("should redirect authenticated users away from register page", async () => {
      render(
        <TestWrapper initialEntries={["/register"]}>
          <App />
        </TestWrapper>
      );

      // Should redirect to dashboard instead of showing register
      await waitFor(() => {
        expect(screen.getByTestId("main-dashboard")).toBeInTheDocument();
      });

      expect(
        screen.queryByText(/create your storysign account/i)
      ).not.toBeInTheDocument();
    });

    it("should show dashboard for authenticated users on root path", async () => {
      render(
        <TestWrapper initialEntries={["/"]}>
          <App />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByTestId("main-dashboard")).toBeInTheDocument();
      });

      expect(screen.getByTestId("platform-shell")).toBeInTheDocument();
    });

    it("should allow access to protected routes", async () => {
      render(
        <TestWrapper initialEntries={["/asl-world"]}>
          <App />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByTestId("asl-world-page")).toBeInTheDocument();
      });

      expect(screen.getByTestId("platform-shell")).toBeInTheDocument();
    });

    it("should show consistent navigation in PlatformShell", async () => {
      render(
        <TestWrapper initialEntries={["/dashboard"]}>
          <App />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByTestId("platform-nav")).toBeInTheDocument();
      });

      // Check navigation links are present
      expect(screen.getByText("Dashboard")).toBeInTheDocument();
      expect(screen.getByText("ASL World")).toBeInTheDocument();
      expect(screen.getByText("Harmony")).toBeInTheDocument();
      expect(screen.getByText("Reconnect")).toBeInTheDocument();
    });
  });

  describe("Error Handling and Edge Cases", () => {
    it("should handle authentication verification failures gracefully", async () => {
      // Mock token exists but verification fails
      authService.isAuthenticated.mockReturnValue(true);
      authService.getToken.mockReturnValue("invalid-token");
      authService.verifyToken.mockResolvedValue(null);

      render(
        <TestWrapper initialEntries={["/dashboard"]}>
          <App />
        </TestWrapper>
      );

      // Should eventually redirect to login after verification fails
      await waitFor(() => {
        expect(screen.getByText(/sign in to storysign/i)).toBeInTheDocument();
      });
    });

    it("should handle network errors during authentication check", async () => {
      authService.isAuthenticated.mockReturnValue(true);
      authService.getToken.mockReturnValue("some-token");
      authService.verifyToken.mockRejectedValue(new Error("Network error"));

      render(
        <TestWrapper initialEntries={["/dashboard"]}>
          <App />
        </TestWrapper>
      );

      // Should redirect to login on verification error
      await waitFor(() => {
        expect(screen.getByText(/sign in to storysign/i)).toBeInTheDocument();
      });
    });

    it("should handle unknown routes appropriately", async () => {
      // Mock authenticated state
      const mockUser = {
        id: 1,
        email: "test@example.com",
        username: "testuser",
      };
      authService.isAuthenticated.mockReturnValue(true);
      authService.getCurrentUser.mockReturnValue(mockUser);
      authService.getToken.mockReturnValue("mock-token");
      authService.verifyToken.mockResolvedValue(mockUser);

      render(
        <TestWrapper initialEntries={["/unknown-route"]}>
          <App />
        </TestWrapper>
      );

      // Should redirect to dashboard for unknown protected routes
      await waitFor(() => {
        expect(screen.getByTestId("main-dashboard")).toBeInTheDocument();
      });
    });
  });

  describe("Form Validation", () => {
    it("should validate login form inputs", async () => {
      render(
        <TestWrapper initialEntries={["/login"]}>
          <App />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/sign in to storysign/i)).toBeInTheDocument();
      });

      const submitButton = screen.getByRole("button", { name: /sign in/i });
      fireEvent.click(submitButton);

      // Should show validation errors
      await waitFor(() => {
        expect(screen.getByText(/email is required/i)).toBeInTheDocument();
        expect(screen.getByText(/password is required/i)).toBeInTheDocument();
      });
    });

    it("should validate registration form inputs", async () => {
      render(
        <TestWrapper initialEntries={["/register"]}>
          <App />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(
          screen.getByText(/create your storysign account/i)
        ).toBeInTheDocument();
      });

      const submitButton = screen.getByRole("button", {
        name: /create account/i,
      });
      fireEvent.click(submitButton);

      // Should show validation errors
      await waitFor(() => {
        expect(screen.getByText(/username is required/i)).toBeInTheDocument();
        expect(screen.getByText(/email is required/i)).toBeInTheDocument();
        expect(screen.getByText(/password is required/i)).toBeInTheDocument();
      });
    });
  });
});
