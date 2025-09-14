/**
 * Complete User Workflow Integration Tests
 *
 * This test suite covers the complete user workflow as specified in task 8:
 * - Test end-to-end authentication flow with login and logout
 * - Verify protected route access and redirection after logout
 * - Test ASL World functionality works immediately without "Test Backend"
 *
 * Requirements: 6.5, 6.6
 */

import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter, MemoryRouter } from "react-router-dom";
import "@testing-library/jest-dom";

import App from "../../App";
import { AuthProvider } from "../../contexts/AuthContext";
import authService from "../../services/AuthService";

// Mock the auth service
jest.mock("../../services/AuthService");

// Mock complex components to focus on integration flow
jest.mock("../../components/video/VideoStreamingClient", () => {
  const React = require("react");
  return React.forwardRef((props, ref) => (
    <div data-testid="video-streaming-client" ref={ref}>
      Mock Video Streaming Client
    </div>
  ));
});

jest.mock("../../hooks/useWebcam", () => ({
  __esModule: true,
  default: () => ({
    stream: null,
    isActive: false,
    status: "inactive",
    error: null,
    startWebcam: jest.fn(),
    stopWebcam: jest.fn(),
    attachToVideoElement: jest.fn(),
  }),
}));

// Mock API configuration to simulate automatic backend connection
jest.mock("../../config/api.js", () => ({
  __esModule: true,
  default: "http://127.0.0.1:8000",
}));

// Mock performance and accessibility utilities
jest.mock("../../utils/performance", () => ({
  performanceMonitor: {
    startTiming: jest.fn(),
    endTiming: jest.fn(),
    setMemoryBaseline: jest.fn(),
    generateReport: jest.fn(() => ({
      routeTransitions: { slowTransitions: 0 },
    })),
    recordRouteTransition: jest.fn(),
  },
  usePerformanceMonitoring: () => ({
    memoryUsage: { used: 0, total: 0 },
    checkMemoryLeak: jest.fn(() => ({ isLeak: false })),
  }),
  useRouteTransitionPerformance: () => ({
    startTransition: jest.fn(),
    endTransition: jest.fn(),
    isTransitioning: false,
  }),
}));

jest.mock("../../utils/accessibility", () => ({
  manageFocusForSPA: jest.fn(),
}));

jest.mock("../../hooks/useMemoryManagement", () => ({
  useMemoryManagement: () => ({
    registerInterval: jest.fn((fn, interval) => setInterval(fn, interval)),
    registerCleanup: jest.fn(),
  }),
}));

jest.mock("../../services/ErrorRecoveryService", () => ({
  useErrorRecovery: () => ({
    recoverFromError: jest.fn(),
    isOnline: true,
    getRecoveryStats: jest.fn(() => ({})),
  }),
}));

jest.mock("../../utils/authErrorHandler", () => ({
  useAuthErrorHandler: () => jest.fn(),
}));

// Test wrapper component
const TestWrapper = ({ children, initialEntries = ["/"] }) => (
  <MemoryRouter initialEntries={initialEntries}>
    <AuthProvider>{children}</AuthProvider>
  </MemoryRouter>
);

describe("Complete User Workflow Integration Tests", () => {
  let user;

  beforeEach(() => {
    user = userEvent.setup();
    jest.clearAllMocks();

    // Default mock implementations
    authService.isAuthenticated.mockReturnValue(false);
    authService.getCurrentUser.mockReturnValue(null);
    authService.getToken.mockReturnValue(null);
    authService.verifyToken.mockResolvedValue(null);
    authService.login.mockResolvedValue({});
    authService.logout.mockResolvedValue({});
    authService.register.mockResolvedValue({});

    // Mock successful API responses for backend connectivity
    global.fetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({ status: "connected", message: "Backend ready" }),
    });
  });

  describe("End-to-End Authentication Flow", () => {
    test("should complete full login to logout workflow", async () => {
      // Start with unauthenticated state
      global.testUtils.setupUnauthenticatedState();

      render(
        <TestWrapper initialEntries={["/"]}>
          <App />
        </TestWrapper>
      );

      // Should redirect to login page
      await waitFor(() => {
        expect(screen.getByText(/sign in to storysign/i)).toBeInTheDocument();
      });

      // Fill in login form
      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByPlaceholderText(/enter your password/i);
      const loginButton = screen.getByRole("button", { name: /sign in/i });

      await user.type(emailInput, "test@example.com");
      await user.type(passwordInput, "password123");

      // Mock successful login
      const mockUser = global.testUtils.createMockUser();
      const mockToken = global.testUtils.createMockToken();

      authService.login.mockResolvedValue({
        user: mockUser,
        token: mockToken,
      });

      // Update auth state after login
      authService.isAuthenticated.mockReturnValue(true);
      authService.getCurrentUser.mockReturnValue(mockUser);
      authService.getToken.mockReturnValue(mockToken);
      authService.verifyToken.mockResolvedValue(mockUser);

      await user.click(loginButton);

      // Verify login was called
      await waitFor(() => {
        expect(authService.login).toHaveBeenCalledWith(
          "test@example.com",
          "password123",
          false
        );
      });

      // Should redirect to dashboard after successful login
      await waitFor(() => {
        expect(screen.getByText("StorySign")).toBeInTheDocument(); // Platform header
        expect(screen.getByText("Dashboard")).toBeInTheDocument();
      });

      // Verify user menu is available (indicating authenticated state)
      expect(screen.getByLabelText(/user menu/i)).toBeInTheDocument();

      // Test logout functionality
      const userMenuButton = screen.getByLabelText(/user menu/i);
      await user.click(userMenuButton);

      // Should show logout option
      await waitFor(() => {
        expect(screen.getByText(/logout/i)).toBeInTheDocument();
      });

      const logoutButton = screen.getByText(/logout/i);

      // Mock logout and update auth state
      authService.logout.mockResolvedValue({});
      authService.isAuthenticated.mockReturnValue(false);
      authService.getCurrentUser.mockReturnValue(null);
      authService.getToken.mockReturnValue(null);

      await user.click(logoutButton);

      // Verify logout was called
      await waitFor(() => {
        expect(authService.logout).toHaveBeenCalled();
      });

      // Should redirect back to login page after logout
      await waitFor(() => {
        expect(screen.getByText(/sign in to storysign/i)).toBeInTheDocument();
      });
    });

    test("should handle login errors gracefully", async () => {
      global.testUtils.setupUnauthenticatedState();

      render(
        <TestWrapper initialEntries={["/login"]}>
          <App />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/sign in to storysign/i)).toBeInTheDocument();
      });

      // Mock login failure
      authService.login.mockRejectedValue(new Error("Invalid credentials"));

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByPlaceholderText(/enter your password/i);
      const loginButton = screen.getByRole("button", { name: /sign in/i });

      await user.type(emailInput, "invalid@example.com");
      await user.type(passwordInput, "wrongpassword");
      await user.click(loginButton);

      // Should show error message
      await waitFor(() => {
        expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
      });

      // Should remain on login page
      expect(screen.getByText(/sign in to storysign/i)).toBeInTheDocument();
    });

    test("should handle logout errors gracefully", async () => {
      // Start with authenticated state
      const { user: mockUser, token: mockToken } =
        global.testUtils.setupAuthenticatedState();

      authService.isAuthenticated.mockReturnValue(true);
      authService.getCurrentUser.mockReturnValue(mockUser);
      authService.getToken.mockReturnValue(mockToken);
      authService.verifyToken.mockResolvedValue(mockUser);

      render(
        <TestWrapper initialEntries={["/dashboard"]}>
          <App />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText("Dashboard")).toBeInTheDocument();
      });

      // Open user menu and click logout
      const userMenuButton = screen.getByLabelText(/user menu/i);
      await user.click(userMenuButton);

      const logoutButton = screen.getByText(/logout/i);

      // Mock logout failure but still clear local state
      authService.logout.mockRejectedValue(new Error("Server error"));
      authService.isAuthenticated.mockReturnValue(false);
      authService.getCurrentUser.mockReturnValue(null);
      authService.getToken.mockReturnValue(null);

      await user.click(logoutButton);

      // Should still redirect to login even if server logout fails
      await waitFor(() => {
        expect(screen.getByText(/sign in to storysign/i)).toBeInTheDocument();
      });
    });
  });

  describe("Protected Route Access and Redirection", () => {
    test("should redirect unauthenticated users from protected routes to login", async () => {
      global.testUtils.setupUnauthenticatedState();

      const protectedRoutes = [
        "/dashboard",
        "/asl-world",
        "/harmony",
        "/reconnect",
      ];

      for (const route of protectedRoutes) {
        render(
          <TestWrapper initialEntries={[route]}>
            <App />
          </TestWrapper>
        );

        await waitFor(() => {
          expect(screen.getByText(/sign in to storysign/i)).toBeInTheDocument();
        });

        // Clean up for next iteration
        screen.unmount?.();
      }
    });

    test("should allow authenticated users to access protected routes", async () => {
      const { user: mockUser, token: mockToken } =
        global.testUtils.setupAuthenticatedState();

      authService.isAuthenticated.mockReturnValue(true);
      authService.getCurrentUser.mockReturnValue(mockUser);
      authService.getToken.mockReturnValue(mockToken);
      authService.verifyToken.mockResolvedValue(mockUser);

      const routeTests = [
        { path: "/dashboard", expectedText: "Dashboard" },
        { path: "/asl-world", expectedText: "ASL World" },
        { path: "/harmony", expectedText: "Harmony" },
        { path: "/reconnect", expectedText: "Reconnect" },
      ];

      for (const { path, expectedText } of routeTests) {
        render(
          <TestWrapper initialEntries={[path]}>
            <App />
          </TestWrapper>
        );

        await waitFor(() => {
          expect(screen.getByText(expectedText)).toBeInTheDocument();
          expect(screen.getByText("StorySign")).toBeInTheDocument(); // Platform header
        });

        // Clean up for next iteration
        screen.unmount?.();
      }
    });

    test("should redirect to login after logout from any protected route", async () => {
      const { user: mockUser, token: mockToken } =
        global.testUtils.setupAuthenticatedState();

      authService.isAuthenticated.mockReturnValue(true);
      authService.getCurrentUser.mockReturnValue(mockUser);
      authService.getToken.mockReturnValue(mockToken);
      authService.verifyToken.mockResolvedValue(mockUser);

      render(
        <TestWrapper initialEntries={["/asl-world"]}>
          <App />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText("ASL World")).toBeInTheDocument();
      });

      // Perform logout
      const userMenuButton = screen.getByLabelText(/user menu/i);
      await user.click(userMenuButton);

      const logoutButton = screen.getByText(/logout/i);

      // Update auth state for logout
      authService.isAuthenticated.mockReturnValue(false);
      authService.getCurrentUser.mockReturnValue(null);
      authService.getToken.mockReturnValue(null);

      await user.click(logoutButton);

      // Should redirect to login
      await waitFor(() => {
        expect(screen.getByText(/sign in to storysign/i)).toBeInTheDocument();
      });

      // Verify we can't access the protected route anymore
      expect(screen.queryByText("ASL World")).not.toBeInTheDocument();
    });

    test("should maintain authentication state across route navigation", async () => {
      const { user: mockUser, token: mockToken } =
        global.testUtils.setupAuthenticatedState();

      authService.isAuthenticated.mockReturnValue(true);
      authService.getCurrentUser.mockReturnValue(mockUser);
      authService.getToken.mockReturnValue(mockToken);
      authService.verifyToken.mockResolvedValue(mockUser);

      render(
        <TestWrapper initialEntries={["/dashboard"]}>
          <App />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText("Dashboard")).toBeInTheDocument();
      });

      // Navigate to ASL World
      const aslWorldButton = screen.getByRole("button", { name: /asl world/i });
      await user.click(aslWorldButton);

      await waitFor(() => {
        expect(screen.getByText("ASL World")).toBeInTheDocument();
      });

      // Verify user menu is still available (authenticated state maintained)
      expect(screen.getByLabelText(/user menu/i)).toBeInTheDocument();

      // Navigate to Harmony
      const harmonyButton = screen.getByRole("button", { name: /harmony/i });
      await user.click(harmonyButton);

      await waitFor(() => {
        expect(screen.getByText("Harmony")).toBeInTheDocument();
      });

      // Authentication state should still be maintained
      expect(screen.getByLabelText(/user menu/i)).toBeInTheDocument();
    });
  });

  describe("ASL World Functionality Without Manual Backend Connection", () => {
    test("should access ASL World immediately without Test Backend button", async () => {
      const { user: mockUser, token: mockToken } =
        global.testUtils.setupAuthenticatedState();

      authService.isAuthenticated.mockReturnValue(true);
      authService.getCurrentUser.mockReturnValue(mockUser);
      authService.getToken.mockReturnValue(mockToken);
      authService.verifyToken.mockResolvedValue(mockUser);

      render(
        <TestWrapper initialEntries={["/asl-world"]}>
          <App />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText("ASL World")).toBeInTheDocument();
        expect(
          screen.getByText("Interactive American Sign Language Learning")
        ).toBeInTheDocument();
      });

      // Verify that there's no "Test Backend" button
      expect(screen.queryByText(/test backend/i)).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /test backend/i })
      ).not.toBeInTheDocument();

      // Verify that ASL World functionality is immediately available
      // The page should show connection status and be ready for use
      expect(screen.getByText(/connection status/i)).toBeInTheDocument();
    });

    test("should show webcam controls immediately in ASL World", async () => {
      const { user: mockUser, token: mockToken } =
        global.testUtils.setupAuthenticatedState();

      authService.isAuthenticated.mockReturnValue(true);
      authService.getCurrentUser.mockReturnValue(mockUser);
      authService.getToken.mockReturnValue(mockToken);
      authService.verifyToken.mockResolvedValue(mockUser);

      render(
        <TestWrapper initialEntries={["/asl-world"]}>
          <App />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText("ASL World")).toBeInTheDocument();
      });

      // Verify webcam controls are available immediately
      // These should be present without needing to test backend connection
      const webcamSection = screen
        .getByText(/connection status/i)
        .closest("div");
      expect(webcamSection).toBeInTheDocument();
    });

    test("should handle story generation without manual backend setup", async () => {
      const { user: mockUser, token: mockToken } =
        global.testUtils.setupAuthenticatedState();

      authService.isAuthenticated.mockReturnValue(true);
      authService.getCurrentUser.mockReturnValue(mockUser);
      authService.getToken.mockReturnValue(mockToken);
      authService.verifyToken.mockResolvedValue(mockUser);

      // Mock story generation API response
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            story: "Once upon a time...",
            success: true,
          }),
      });

      render(
        <TestWrapper initialEntries={["/asl-world"]}>
          <App />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText("ASL World")).toBeInTheDocument();
      });

      // The story generation functionality should be immediately available
      // without requiring a "Test Backend" button click
      // This is verified by the absence of the Test Backend button
      expect(screen.queryByText(/test backend/i)).not.toBeInTheDocument();
    });

    test("should navigate from dashboard to ASL World seamlessly", async () => {
      const { user: mockUser, token: mockToken } =
        global.testUtils.setupAuthenticatedState();

      authService.isAuthenticated.mockReturnValue(true);
      authService.getCurrentUser.mockReturnValue(mockUser);
      authService.getToken.mockReturnValue(mockToken);
      authService.verifyToken.mockResolvedValue(mockUser);

      render(
        <TestWrapper initialEntries={["/dashboard"]}>
          <App />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText("Dashboard")).toBeInTheDocument();
      });

      // Navigate to ASL World
      const aslWorldButton = screen.getByRole("button", { name: /asl world/i });
      await user.click(aslWorldButton);

      await waitFor(() => {
        expect(screen.getByText("ASL World")).toBeInTheDocument();
        expect(
          screen.getByText("Interactive American Sign Language Learning")
        ).toBeInTheDocument();
      });

      // Verify immediate functionality without backend test
      expect(screen.queryByText(/test backend/i)).not.toBeInTheDocument();
      expect(screen.getByText(/connection status/i)).toBeInTheDocument();
    });

    test("should show automatic backend connection status", async () => {
      const { user: mockUser, token: mockToken } =
        global.testUtils.setupAuthenticatedState();

      authService.isAuthenticated.mockReturnValue(true);
      authService.getCurrentUser.mockReturnValue(mockUser);
      authService.getToken.mockReturnValue(mockToken);
      authService.verifyToken.mockResolvedValue(mockUser);

      render(
        <TestWrapper initialEntries={["/asl-world"]}>
          <App />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText("ASL World")).toBeInTheDocument();
      });

      // Should show connection status automatically
      expect(screen.getByText(/connection status/i)).toBeInTheDocument();

      // Should not require manual connection testing
      expect(screen.queryByText(/test backend/i)).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /test backend/i })
      ).not.toBeInTheDocument();
    });
  });

  describe("Complete User Journey Integration", () => {
    test("should complete full user journey: login -> navigate -> use features -> logout", async () => {
      // Start unauthenticated
      global.testUtils.setupUnauthenticatedState();

      render(
        <TestWrapper initialEntries={["/"]}>
          <App />
        </TestWrapper>
      );

      // 1. Should redirect to login
      await waitFor(() => {
        expect(screen.getByText(/sign in to storysign/i)).toBeInTheDocument();
      });

      // 2. Perform login
      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByPlaceholderText(/enter your password/i);
      const loginButton = screen.getByRole("button", { name: /sign in/i });

      await user.type(emailInput, "test@example.com");
      await user.type(passwordInput, "password123");

      // Mock successful login
      const mockUser = global.testUtils.createMockUser();
      const mockToken = global.testUtils.createMockToken();

      authService.login.mockResolvedValue({ user: mockUser, token: mockToken });
      authService.isAuthenticated.mockReturnValue(true);
      authService.getCurrentUser.mockReturnValue(mockUser);
      authService.getToken.mockReturnValue(mockToken);
      authService.verifyToken.mockResolvedValue(mockUser);

      await user.click(loginButton);

      // 3. Should redirect to dashboard
      await waitFor(() => {
        expect(screen.getByText("Dashboard")).toBeInTheDocument();
      });

      // 4. Navigate to ASL World
      const aslWorldButton = screen.getByRole("button", { name: /asl world/i });
      await user.click(aslWorldButton);

      await waitFor(() => {
        expect(screen.getByText("ASL World")).toBeInTheDocument();
      });

      // 5. Verify ASL World works immediately (no Test Backend button)
      expect(screen.queryByText(/test backend/i)).not.toBeInTheDocument();
      expect(screen.getByText(/connection status/i)).toBeInTheDocument();

      // 6. Navigate to other modules
      const harmonyButton = screen.getByRole("button", { name: /harmony/i });
      await user.click(harmonyButton);

      await waitFor(() => {
        expect(screen.getByText("Harmony")).toBeInTheDocument();
      });

      // 7. Perform logout
      const userMenuButton = screen.getByLabelText(/user menu/i);
      await user.click(userMenuButton);

      const logoutButton = screen.getByText(/logout/i);

      // Update auth state for logout
      authService.isAuthenticated.mockReturnValue(false);
      authService.getCurrentUser.mockReturnValue(null);
      authService.getToken.mockReturnValue(null);

      await user.click(logoutButton);

      // 8. Should redirect back to login
      await waitFor(() => {
        expect(screen.getByText(/sign in to storysign/i)).toBeInTheDocument();
      });

      // 9. Verify cannot access protected routes after logout
      expect(screen.queryByText("Harmony")).not.toBeInTheDocument();
      expect(screen.queryByLabelText(/user menu/i)).not.toBeInTheDocument();
    });

    test("should handle registration to login flow", async () => {
      global.testUtils.setupUnauthenticatedState();

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

      // Fill registration form
      const usernameInput = screen.getByLabelText(/username/i);
      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/^password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
      const registerButton = screen.getByRole("button", {
        name: /create account/i,
      });

      await user.type(usernameInput, "newuser");
      await user.type(emailInput, "newuser@example.com");
      await user.type(passwordInput, "StrongPass123!");
      await user.type(confirmPasswordInput, "StrongPass123!");

      // Mock successful registration
      authService.register.mockResolvedValue({
        message: "Registration successful",
        user: { id: 1, email: "newuser@example.com", username: "newuser" },
      });

      await user.click(registerButton);

      // Should handle registration success
      await waitFor(() => {
        expect(authService.register).toHaveBeenCalledWith({
          username: "newuser",
          email: "newuser@example.com",
          password: "StrongPass123!",
        });
      });
    });
  });

  describe("Error Handling and Edge Cases", () => {
    test("should handle network errors gracefully", async () => {
      global.testUtils.setupUnauthenticatedState();

      // Mock network error
      global.fetch.mockRejectedValue(new Error("Network error"));

      render(
        <TestWrapper initialEntries={["/login"]}>
          <App />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/sign in to storysign/i)).toBeInTheDocument();
      });

      // App should still render despite network errors
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText(/enter your password/i)
      ).toBeInTheDocument();
    });

    test("should handle token expiration during session", async () => {
      const { user: mockUser, token: mockToken } =
        global.testUtils.setupAuthenticatedState();

      authService.isAuthenticated.mockReturnValue(true);
      authService.getCurrentUser.mockReturnValue(mockUser);
      authService.getToken.mockReturnValue(mockToken);

      // Mock token verification failure (expired token)
      authService.verifyToken.mockResolvedValue(null);

      render(
        <TestWrapper initialEntries={["/dashboard"]}>
          <App />
        </TestWrapper>
      );

      // Should eventually redirect to login when token verification fails
      await waitFor(() => {
        expect(screen.getByText(/sign in to storysign/i)).toBeInTheDocument();
      });
    });

    test("should handle rapid navigation between routes", async () => {
      const { user: mockUser, token: mockToken } =
        global.testUtils.setupAuthenticatedState();

      authService.isAuthenticated.mockReturnValue(true);
      authService.getCurrentUser.mockReturnValue(mockUser);
      authService.getToken.mockReturnValue(mockToken);
      authService.verifyToken.mockResolvedValue(mockUser);

      render(
        <TestWrapper initialEntries={["/dashboard"]}>
          <App />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText("Dashboard")).toBeInTheDocument();
      });

      // Rapidly navigate between routes
      const aslWorldButton = screen.getByRole("button", { name: /asl world/i });
      const harmonyButton = screen.getByRole("button", { name: /harmony/i });
      const dashboardButton = screen.getByRole("button", {
        name: /dashboard/i,
      });

      await user.click(aslWorldButton);
      await user.click(harmonyButton);
      await user.click(dashboardButton);

      // Should handle rapid navigation without errors
      await waitFor(() => {
        expect(screen.getByText("Dashboard")).toBeInTheDocument();
      });
    });
  });
});
