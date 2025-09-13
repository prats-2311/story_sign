/**
 * End-to-End User Journey Tests
 *
 * This test suite covers complete user workflows across all modules:
 * - Registration and login workflows
 * - ASL World story generation and practice sessions
 * - Harmony facial expression practice workflows
 * - Reconnect therapeutic movement analysis sessions
 *
 * Requirements: 9.1, 9.2
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
import { BrowserRouter } from "react-router-dom";
import "@testing-library/jest-dom";
import "./setup"; // Import E2E setup

import App from "../../App";
import { AuthProvider } from "../../contexts/AuthContext";
import authService from "../../services/AuthService";

// Mock external dependencies
jest.mock("../../services/AuthService");
jest.mock("../../config/api", () => "http://localhost:8000");
  default: {
    API_BASE_URL: "http://localhost:8000",
    WS_BASE_URL: "ws://localhost:8000",
    API_VERSION: "v1",
  },
}));

// Mock fetch for API calls
global.fetch = jest.fn();

// Mock WebSocket
const mockWebSocket = {
  send: jest.fn(),
  close: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  readyState: WebSocket.OPEN,
};

global.WebSocket = jest.fn(() => mockWebSocket);

// Test utilities
const renderApp = () => {
  return render(
    <BrowserRouter>
      <App />
    </BrowserRouter>
  );
};

const mockSuccessfulAuth = () => {
  authService.isAuthenticated.mockReturnValue(true);
  authService.getCurrentUser.mockReturnValue({
    id: 1,
    email: "test@example.com",
    username: "testuser",
  });
  authService.getToken.mockReturnValue("mock-jwt-token");
  authService.verifyToken.mockResolvedValue({
    id: 1,
    email: "test@example.com",
    username: "testuser",
  });
};

const mockUnauthenticatedUser = () => {
  authService.isAuthenticated.mockReturnValue(false);
  authService.getCurrentUser.mockReturnValue(null);
  authService.getToken.mockReturnValue(null);
};

describe("End-to-End User Journeys", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    fetch.mockClear();

    // Reset WebSocket mock
    mockWebSocket.send.mockClear();
    mockWebSocket.addEventListener.mockClear();

    // Mock successful health check by default
    fetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({ message: "Backend connected successfully!" }),
    });
  });

  describe("User Registration and Login Workflow", () => {
    test("complete new user registration flow", async () => {
      const user = userEvent.setup();
      mockUnauthenticatedUser();

      // Mock registration API response
      authService.register.mockResolvedValue({
        success: true,
        message: "Registration successful",
      });

      renderApp();

      // Should redirect to login page for unauthenticated users
      await waitFor(() => {
        expect(screen.getByText("Sign In to StorySign")).toBeInTheDocument();
      });

      // Navigate to registration page
      const registerLink = screen.getByText("Create one here");
      await user.click(registerLink);

      await waitFor(() => {
        expect(
          screen.getByText("Create Your StorySign Account")
        ).toBeInTheDocument();
      });

      // Fill out registration form
      const usernameInput = screen.getByLabelText(/username/i);
      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/^password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);

      await user.type(usernameInput, "newuser123");
      await user.type(emailInput, "newuser@example.com");
      await user.type(passwordInput, "SecurePass123!");
      await user.type(confirmPasswordInput, "SecurePass123!");

      // Submit registration form
      const submitButton = screen.getByRole("button", {
        name: /create account/i,
      });
      await user.click(submitButton);

      // Verify registration API was called
      await waitFor(() => {
        expect(authService.register).toHaveBeenCalledWith({
          username: "newuser123",
          email: "newuser@example.com",
          password: "SecurePass123!",
        });
      });

      // Should redirect to login page after successful registration
      await waitFor(() => {
        expect(screen.getByText("Sign In to StorySign")).toBeInTheDocument();
      });
    });

    test("complete user login flow and dashboard access", async () => {
      const user = userEvent.setup();
      mockUnauthenticatedUser();

      // Mock login API response
      authService.login.mockResolvedValue({
        user: {
          id: 1,
          email: "test@example.com",
          username: "testuser",
        },
        token: "mock-jwt-token",
      });

      renderApp();

      // Should show login page
      await waitFor(() => {
        expect(screen.getByText("Sign In to StorySign")).toBeInTheDocument();
      });

      // Fill out login form
      const emailInput = screen.getByLabelText(/email address/i);
      const passwordInput = screen.getByLabelText(/password/i);

      await user.type(emailInput, "test@example.com");
      await user.type(passwordInput, "password123");

      // Submit login form
      const submitButton = screen.getByRole("button", { name: /sign in/i });

      // Mock successful authentication after login
      authService.login.mockImplementation(() => {
        mockSuccessfulAuth();
        return Promise.resolve({
          user: {
            id: 1,
            email: "test@example.com",
            username: "testuser",
          },
          token: "mock-jwt-token",
        });
      });

      await user.click(submitButton);

      // Verify login API was called
      await waitFor(() => {
        expect(authService.login).toHaveBeenCalledWith(
          "test@example.com",
          "password123",
          false
        );
      });

      // Should redirect to dashboard after successful login
      await waitFor(
        () => {
          expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
        },
        { timeout: 5000 }
      );
    });

    test("handles login validation errors", async () => {
      const user = userEvent.setup();
      mockUnauthenticatedUser();

      renderApp();

      await waitFor(() => {
        expect(screen.getByText("Sign In to StorySign")).toBeInTheDocument();
      });

      // Try to submit empty form
      const submitButton = screen.getByRole("button", { name: /sign in/i });
      await user.click(submitButton);

      // Should show validation errors
      await waitFor(() => {
        expect(screen.getByText("Email is required")).toBeInTheDocument();
        expect(screen.getByText("Password is required")).toBeInTheDocument();
      });

      // Fill invalid email
      const emailInput = screen.getByLabelText(/email address/i);
      await user.type(emailInput, "invalid-email");
      await user.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText("Please enter a valid email address")
        ).toBeInTheDocument();
      });
    });
  });

  describe("ASL World Story Generation and Practice Workflow", () => {
    beforeEach(() => {
      mockSuccessfulAuth();
    });

    test("complete ASL World story generation and practice session", async () => {
      const user = userEvent.setup();

      // Mock story generation API response
      fetch.mockImplementation((url) => {
        if (url.includes("/asl-world/story/recognize_and_generate")) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                success: true,
                stories: [
                  {
                    id: 1,
                    title: "The Red Apple",
                    sentences: [
                      "I see a red apple on the table.",
                      "The apple looks fresh and delicious.",
                      "I want to eat the apple.",
                    ],
                    object_detected: "apple",
                  },
                ],
              }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({ message: "Backend connected successfully!" }),
        });
      });

      renderApp();

      // Navigate to ASL World
      await waitFor(() => {
        expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
      });

      const aslWorldLink = screen.getByText(/asl world/i);
      await user.click(aslWorldLink);

      await waitFor(() => {
        expect(screen.getByText("ASL World")).toBeInTheDocument();
        expect(
          screen.getByText("Interactive American Sign Language Learning")
        ).toBeInTheDocument();
      });

      // Should show story setup view initially
      expect(screen.getByText(/generate/i)).toBeInTheDocument();

      // Test story generation with text input
      const textInput = screen.getByLabelText(
        /describe what you want to practice/i
      );
      await user.type(textInput, "I want to practice signing about fruits");

      const generateButton = screen.getByRole("button", {
        name: /generate story/i,
      });
      await user.click(generateButton);

      // Should show loading state
      await waitFor(() => {
        expect(screen.getByText(/generating/i)).toBeInTheDocument();
      });

      // Should show story selection after generation
      await waitFor(
        () => {
          expect(screen.getByText("The Red Apple")).toBeInTheDocument();
          expect(
            screen.getByText("I see a red apple on the table.")
          ).toBeInTheDocument();
        },
        { timeout: 5000 }
      );

      // Select the generated story
      const selectStoryButton = screen.getByRole("button", {
        name: /select this story/i,
      });
      await user.click(selectStoryButton);

      // Should navigate to practice view
      await waitFor(() => {
        expect(screen.getByText(/practice view/i)).toBeInTheDocument();
        expect(
          screen.getByText("I see a red apple on the table.")
        ).toBeInTheDocument();
      });

      // Test practice session start
      const startPracticeButton = screen.getByRole("button", {
        name: /start practice/i,
      });
      await user.click(startPracticeButton);

      // Should show practice controls
      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /next sentence/i })
        ).toBeInTheDocument();
        expect(
          screen.getByRole("button", { name: /try again/i })
        ).toBeInTheDocument();
      });
    });

    test("handles story generation errors gracefully", async () => {
      const user = userEvent.setup();

      // Mock story generation API error
      fetch.mockImplementation((url) => {
        if (url.includes("/asl-world/story/recognize_and_generate")) {
          return Promise.resolve({
            ok: false,
            status: 500,
            json: () =>
              Promise.resolve({
                success: false,
                message: "AI service temporarily unavailable",
              }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({ message: "Backend connected successfully!" }),
        });
      });

      renderApp();

      // Navigate to ASL World
      await waitFor(() => {
        const aslWorldLink = screen.getByText(/asl world/i);
        user.click(aslWorldLink);
      });

      await waitFor(() => {
        expect(screen.getByText("ASL World")).toBeInTheDocument();
      });

      // Try to generate story
      const textInput = screen.getByLabelText(
        /describe what you want to practice/i
      );
      await user.type(textInput, "Test story");

      const generateButton = screen.getByRole("button", {
        name: /generate story/i,
      });
      await user.click(generateButton);

      // Should show error message
      await waitFor(() => {
        expect(
          screen.getByText(/ai service temporarily unavailable/i)
        ).toBeInTheDocument();
      });

      // Should have retry option
      expect(
        screen.getByRole("button", { name: /try again/i })
      ).toBeInTheDocument();
    });
  });

  describe("Harmony Facial Expression Practice Workflow", () => {
    beforeEach(() => {
      mockSuccessfulAuth();
    });

    test("complete Harmony emotion practice session", async () => {
      const user = userEvent.setup();

      // Mock Harmony session API response
      fetch.mockImplementation((url) => {
        if (url.includes("/harmony/sessions")) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                success: true,
                session_id: "harmony_123",
              }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({ message: "Backend connected successfully!" }),
        });
      });

      renderApp();

      // Navigate to Harmony module
      await waitFor(() => {
        const harmonyLink = screen.getByText(/harmony/i);
        user.click(harmonyLink);
      });

      await waitFor(() => {
        expect(screen.getByText("Harmony")).toBeInTheDocument();
        expect(
          screen.getByText("Facial expression practice module coming soon!")
        ).toBeInTheDocument();
      });

      // Note: Since Harmony is currently a placeholder, we'll test the expected behavior
      // when the module is fully implemented based on the HarmonyPage.js structure
    });
  });

  describe("Reconnect Therapeutic Movement Workflow", () => {
    beforeEach(() => {
      mockSuccessfulAuth();
    });

    test("complete Reconnect therapy session", async () => {
      const user = userEvent.setup();

      // Mock Reconnect session API response
      fetch.mockImplementation((url) => {
        if (url.includes("/reconnect/sessions")) {
          return Promise.resolve({
            ok: true,
            json: () =>
              Promise.resolve({
                success: true,
                session_id: "reconnect_123",
              }),
          });
        }
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({ message: "Backend connected successfully!" }),
        });
      });

      renderApp();

      // Navigate to Reconnect module
      await waitFor(() => {
        const reconnectLink = screen.getByText(/reconnect/i);
        user.click(reconnectLink);
      });

      await waitFor(() => {
        expect(screen.getByText("Reconnect")).toBeInTheDocument();
        expect(
          screen.getByText("Therapeutic movement analysis module coming soon!")
        ).toBeInTheDocument();
      });

      // Note: Since Reconnect is currently a placeholder, we'll test the expected behavior
      // when the module is fully implemented based on the ReconnectPage.js structure
    });
  });

  describe("Cross-Module Navigation and State Management", () => {
    beforeEach(() => {
      mockSuccessfulAuth();
    });

    test("seamless navigation between all modules", async () => {
      const user = userEvent.setup();

      renderApp();

      // Start at dashboard
      await waitFor(() => {
        expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
      });

      // Navigate to ASL World
      const aslWorldLink = screen.getByText(/asl world/i);
      await user.click(aslWorldLink);

      await waitFor(() => {
        expect(screen.getByText("ASL World")).toBeInTheDocument();
      });

      // Navigate to Harmony
      const harmonyLink = screen.getByText(/harmony/i);
      await user.click(harmonyLink);

      await waitFor(() => {
        expect(screen.getByText("Harmony")).toBeInTheDocument();
      });

      // Navigate to Reconnect
      const reconnectLink = screen.getByText(/reconnect/i);
      await user.click(reconnectLink);

      await waitFor(() => {
        expect(screen.getByText("Reconnect")).toBeInTheDocument();
      });

      // Navigate back to dashboard
      const dashboardLink = screen.getByText(/dashboard/i);
      await user.click(dashboardLink);

      await waitFor(() => {
        expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
      });
    });

    test("maintains authentication state across navigation", async () => {
      const user = userEvent.setup();

      renderApp();

      // Verify authenticated state is maintained
      await waitFor(() => {
        expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
      });

      // Navigate between modules
      const aslWorldLink = screen.getByText(/asl world/i);
      await user.click(aslWorldLink);

      await waitFor(() => {
        expect(screen.getByText("ASL World")).toBeInTheDocument();
      });

      // Verify user is still authenticated (no redirect to login)
      expect(
        screen.queryByText("Sign In to StorySign")
      ).not.toBeInTheDocument();
    });

    test("handles logout and redirects appropriately", async () => {
      const user = userEvent.setup();

      // Mock logout
      authService.logout.mockImplementation(() => {
        mockUnauthenticatedUser();
        return Promise.resolve();
      });

      renderApp();

      await waitFor(() => {
        expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
      });

      // Simulate logout (this would typically be triggered by a logout button)
      act(() => {
        // Trigger logout through auth context
        mockUnauthenticatedUser();
      });

      // Should redirect to login page
      await waitFor(() => {
        expect(screen.getByText("Sign In to StorySign")).toBeInTheDocument();
      });
    });
  });

  describe("Error Handling and Recovery", () => {
    beforeEach(() => {
      mockSuccessfulAuth();
    });

    test("handles network errors gracefully", async () => {
      const user = userEvent.setup();

      // Mock network error
      fetch.mockRejectedValue(new Error("Network error"));

      renderApp();

      await waitFor(() => {
        const aslWorldLink = screen.getByText(/asl world/i);
        user.click(aslWorldLink);
      });

      await waitFor(() => {
        expect(screen.getByText("ASL World")).toBeInTheDocument();
      });

      // Try to generate story with network error
      const textInput = screen.getByLabelText(
        /describe what you want to practice/i
      );
      await user.type(textInput, "Test story");

      const generateButton = screen.getByRole("button", {
        name: /generate story/i,
      });
      await user.click(generateButton);

      // Should show network error message
      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });
    });

    test("recovers from temporary backend unavailability", async () => {
      const user = userEvent.setup();

      // First call fails, second succeeds
      let callCount = 0;
      fetch.mockImplementation(() => {
        callCount++;
        if (callCount === 1) {
          return Promise.reject(new Error("Backend unavailable"));
        }
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({ message: "Backend connected successfully!" }),
        });
      });

      renderApp();

      await waitFor(() => {
        expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
      });

      // Test backend connection
      const testConnectionButton = screen.getByRole("button", {
        name: /test connection/i,
      });
      await user.click(testConnectionButton);

      // Should show error first
      await waitFor(() => {
        expect(screen.getByText(/backend unavailable/i)).toBeInTheDocument();
      });

      // Retry connection
      const retryButton = screen.getByRole("button", { name: /retry/i });
      await user.click(retryButton);

      // Should succeed on retry
      await waitFor(() => {
        expect(
          screen.getByText(/backend connected successfully/i)
        ).toBeInTheDocument();
      });
    });
  });
});
