/**
 * Error Recovery Test Suite
 * Tests for comprehensive error boundaries and fallbacks
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import "@testing-library/jest-dom";

import { EnhancedErrorFallback } from "../components/error/ErrorBoundaries";
import { ErrorRecoveryService } from "../services/ErrorRecoveryService";
import { categorizeError, ERROR_TYPES } from "../utils/networkErrorHandler";
import {
  categorizeAuthError,
  AUTH_ERROR_TYPES,
} from "../utils/authErrorHandler";

// Test wrapper component
const TestWrapper = ({ children }) => <BrowserRouter>{children}</BrowserRouter>;

// Mock console methods to avoid test noise
const originalConsoleError = console.error;
const originalConsoleWarn = console.warn;

describe("Error Recovery System", () => {
  beforeEach(() => {
    // Mock console methods
    console.error = jest.fn();
    console.warn = jest.fn();

    // Mock window.location
    delete window.location;
    window.location = { href: "", pathname: "/", reload: jest.fn() };

    // Mock navigator.onLine
    Object.defineProperty(navigator, "onLine", {
      writable: true,
      value: true,
    });
  });

  afterEach(() => {
    console.error = originalConsoleError;
    console.warn = originalConsoleWarn;
    jest.clearAllMocks();
  });

  describe("EnhancedErrorFallback Component", () => {
    it("should render error information correctly", () => {
      const error = new Error("Test error message");
      const mockReset = jest.fn();

      render(
        <EnhancedErrorFallback
          error={error}
          resetErrorBoundary={mockReset}
          errorType="network"
          componentName="Test Component"
        />
      );

      expect(screen.getByText("Connection Error")).toBeInTheDocument();
      expect(
        screen.getByText(/Unable to connect to the server/)
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /try again/i })
      ).toBeInTheDocument();
    });

    it("should handle retry functionality", () => {
      const error = new Error("Test error");
      const mockReset = jest.fn();

      render(
        <EnhancedErrorFallback
          error={error}
          resetErrorBoundary={mockReset}
          errorType="general"
        />
      );

      const retryButton = screen.getByRole("button", { name: /try again/i });
      fireEvent.click(retryButton);

      expect(mockReset).toHaveBeenCalledTimes(1);
    });

    it("should show error details when requested", () => {
      const error = new Error("Detailed error message");
      const mockReset = jest.fn();

      render(
        <EnhancedErrorFallback error={error} resetErrorBoundary={mockReset} />
      );

      const detailsButton = screen.getByRole("button", {
        name: /show details/i,
      });
      fireEvent.click(detailsButton);

      expect(screen.getByText("Technical Details")).toBeInTheDocument();
      expect(screen.getByText("Detailed error message")).toBeInTheDocument();
    });

    it("should render different error types correctly", () => {
      const error = new Error("Auth error");
      const mockReset = jest.fn();

      const { rerender } = render(
        <EnhancedErrorFallback
          error={error}
          resetErrorBoundary={mockReset}
          errorType="authentication"
        />
      );

      expect(screen.getByText("Authentication Error")).toBeInTheDocument();

      rerender(
        <EnhancedErrorFallback
          error={error}
          resetErrorBoundary={mockReset}
          errorType="chunk"
        />
      );

      expect(screen.getByText("Loading Error")).toBeInTheDocument();
    });

    it("should handle custom actions", () => {
      const error = new Error("Test error");
      const mockReset = jest.fn();
      const mockCustomAction = jest.fn();

      render(
        <EnhancedErrorFallback
          error={error}
          resetErrorBoundary={mockReset}
          customActions={[
            { label: "Custom Action", onClick: mockCustomAction },
          ]}
        />
      );

      const customButton = screen.getByRole("button", {
        name: /custom action/i,
      });
      fireEvent.click(customButton);

      expect(mockCustomAction).toHaveBeenCalledTimes(1);
    });
  });

  describe("Error Categorization", () => {
    it("should categorize network errors correctly", () => {
      const networkError = new Error("Failed to fetch");
      networkError.name = "TypeError";

      const errorInfo = categorizeError(networkError);

      expect(errorInfo.type).toBe(ERROR_TYPES.NETWORK);
      expect(errorInfo.retryable).toBe(true);
      expect(errorInfo.userMessage).toContain("Connection failed");
      expect(errorInfo.suggestedActions).toContain(
        "Check your internet connection"
      );
    });

    it("should categorize authentication errors correctly", () => {
      const authError = new Error("Invalid credentials");
      authError.status = 401;

      const errorInfo = categorizeAuthError(authError);

      expect(errorInfo.authType).toBe(AUTH_ERROR_TYPES.INVALID_CREDENTIALS);
      expect(errorInfo.retryable).toBe(false);
      expect(errorInfo.userMessage).toContain("Invalid email or password");
    });

    it("should categorize chunk loading errors correctly", () => {
      const chunkError = new Error("Loading chunk 1 failed");
      chunkError.name = "ChunkLoadError";

      const errorInfo = categorizeError(chunkError);

      expect(errorInfo.type).toBe(ERROR_TYPES.CHUNK_LOAD);
      expect(errorInfo.retryable).toBe(true);
      expect(errorInfo.userMessage).toContain(
        "Failed to load application resources"
      );
    });

    it("should categorize timeout errors correctly", () => {
      const timeoutError = new Error("Request timed out");
      timeoutError.name = "TimeoutError";

      const errorInfo = categorizeError(timeoutError);

      expect(errorInfo.type).toBe(ERROR_TYPES.TIMEOUT);
      expect(errorInfo.retryable).toBe(true);
      expect(errorInfo.userMessage).toContain("Request timed out");
    });

    it("should categorize server errors correctly", () => {
      const serverError = new Error("Internal Server Error");
      serverError.status = 500;

      const errorInfo = categorizeError(serverError);

      expect(errorInfo.type).toBe(ERROR_TYPES.SERVER);
      expect(errorInfo.retryable).toBe(true);
      expect(errorInfo.userMessage).toContain("Server error");
    });

    it("should handle unknown errors", () => {
      const unknownError = new Error("Unknown error");

      const errorInfo = categorizeError(unknownError);

      expect(errorInfo.type).toBe(ERROR_TYPES.UNKNOWN);
      expect(errorInfo.retryable).toBe(true);
      expect(errorInfo.userMessage).toContain("An unexpected error occurred");
    });
  });

  describe("Error Recovery Service", () => {
    let recoveryService;

    beforeEach(() => {
      recoveryService = new ErrorRecoveryService({
        maxRetries: 3,
        retryDelay: 10, // Very short delay for tests
      });
    });

    afterEach(() => {
      recoveryService.cleanup();
    });

    it("should determine correct recovery strategy for network errors", () => {
      const networkError = new Error("Failed to fetch");
      networkError.name = "TypeError";

      const strategy = recoveryService.determineRecoveryStrategy(networkError);

      expect(strategy.strategy).toBe("retry");
      expect(strategy.maxAttempts).toBe(3);
      expect(strategy.description).toContain(
        "Retry when network connection is restored"
      );
    });

    it("should determine correct recovery strategy for chunk errors", () => {
      const chunkError = new Error("Loading chunk failed");
      chunkError.name = "ChunkLoadError";

      const strategy = recoveryService.determineRecoveryStrategy(chunkError);

      expect(strategy.strategy).toBe("reload");
      expect(strategy.maxAttempts).toBe(1);
      expect(strategy.description).toContain(
        "Reload page to fetch updated resources"
      );
    });

    it("should determine correct recovery strategy for auth errors", () => {
      const authError = new Error("Unauthorized");
      authError.status = 401;

      const strategy = recoveryService.determineRecoveryStrategy(authError);

      expect(strategy.strategy).toBe("logout");
      expect(strategy.maxAttempts).toBe(1);
      expect(strategy.description).toContain(
        "Clear authentication and redirect to login"
      );
    });

    it("should successfully retry failed operations", async () => {
      let attemptCount = 0;
      const operation = jest.fn().mockImplementation(() => {
        attemptCount++;
        if (attemptCount < 3) {
          const error = new Error("Temporary failure");
          error.name = "TypeError";
          throw error;
        }
        return "success";
      });

      // Mock the condition to always return true (online)
      recoveryService.isOnline = true;

      const result = await recoveryService.executeRecovery(
        new Error("Failed to fetch"),
        operation,
        { operationId: "test-op" }
      );

      expect(result).toBe("success");
      expect(operation).toHaveBeenCalledTimes(3);
    });

    it("should fail after max retry attempts", async () => {
      const operation = jest.fn().mockImplementation(() => {
        const error = new Error("Persistent failure");
        error.name = "TypeError";
        throw error;
      });

      // Mock the condition to always return true (online)
      recoveryService.isOnline = true;

      await expect(
        recoveryService.executeRecovery(
          new Error("Failed to fetch"),
          operation,
          { operationId: "test-op-2" } // Use different operation ID
        )
      ).rejects.toThrow();

      // Should try maxRetries times
      expect(operation).toHaveBeenCalledTimes(3);
    });

    it("should queue operations when network is offline", async () => {
      // Simulate offline state
      recoveryService.isOnline = false;

      const operation = jest.fn().mockResolvedValue("success");

      await expect(
        recoveryService.executeRecovery(
          new Error("Failed to fetch"),
          operation,
          { operationId: "test-op" }
        )
      ).rejects.toThrow("Recovery condition not met");

      expect(recoveryService.pendingOperations).toHaveLength(1);
    });

    it("should process queued operations when network comes back online", async () => {
      const operation = jest.fn().mockResolvedValue("success");

      // Add operation to queue
      recoveryService.queueOperation(operation, "test-op", {
        strategy: "retry",
        maxAttempts: 3,
      });

      expect(recoveryService.pendingOperations).toHaveLength(1);

      // Simulate network coming back online
      recoveryService.handleNetworkStatusChange(true);

      // Wait for async processing
      await new Promise(resolve => setTimeout(resolve, 50));

      expect(recoveryService.pendingOperations).toHaveLength(0);
    });

    it("should provide recovery statistics", () => {
      recoveryService.recoveryAttempts.set("test-op-1", 2);
      recoveryService.recoveryAttempts.set("test-op-2", 1);
      recoveryService.pendingOperations.push({ operationId: "pending-op" });

      const stats = recoveryService.getRecoveryStats();

      expect(stats.totalAttempts).toBe(2);
      expect(stats.pendingOperations).toBe(1);
      expect(stats.isOnline).toBe(true);
      expect(stats.attempts).toEqual({
        "test-op-1": 2,
        "test-op-2": 1,
      });
    });

    it("should handle network status changes", () => {
      const mockProcessQueue = jest.spyOn(
        recoveryService,
        "processQueuedOperations"
      );

      // Simulate going offline
      recoveryService.handleNetworkStatusChange(false);
      expect(recoveryService.isOnline).toBe(false);

      // Simulate coming back online
      recoveryService.handleNetworkStatusChange(true);
      expect(recoveryService.isOnline).toBe(true);
      expect(mockProcessQueue).toHaveBeenCalled();
    });
  });

  describe("Authentication Error Handling", () => {
    it("should categorize session expired errors", () => {
      const sessionError = new Error("session expired");

      const errorInfo = categorizeAuthError(sessionError);

      expect(errorInfo.authType).toBe(AUTH_ERROR_TYPES.SESSION_EXPIRED);
      expect(errorInfo.retryable).toBe(false);
      expect(errorInfo.userMessage).toContain("Your session has expired");
    });

    it("should categorize account locked errors", () => {
      const lockedError = new Error("account locked");

      const errorInfo = categorizeAuthError(lockedError);

      expect(errorInfo.authType).toBe(AUTH_ERROR_TYPES.ACCOUNT_LOCKED);
      expect(errorInfo.retryable).toBe(false);
      expect(errorInfo.userMessage).toContain("Account temporarily locked");
    });

    it("should categorize rate limit errors", () => {
      const rateLimitError = new Error("too many requests");
      rateLimitError.status = 429;

      const errorInfo = categorizeAuthError(rateLimitError);

      expect(errorInfo.authType).toBe(AUTH_ERROR_TYPES.RATE_LIMITED);
      expect(errorInfo.retryable).toBe(true);
      expect(errorInfo.userMessage).toContain("Too many login attempts");
    });
  });

  describe("Integration Tests", () => {
    it("should handle error fallback with retry functionality", () => {
      const error = new Error("Network error");
      const mockReset = jest.fn();

      render(
        <TestWrapper>
          <EnhancedErrorFallback
            error={error}
            resetErrorBoundary={mockReset}
            errorType="network"
            componentName="Test Component"
          />
        </TestWrapper>
      );

      // Should show network error UI
      expect(screen.getByText("Connection Error")).toBeInTheDocument();
      expect(
        screen.getByText(/Unable to connect to the server/)
      ).toBeInTheDocument();

      // Should have retry button
      const retryButton = screen.getByRole("button", { name: /try again/i });
      expect(retryButton).toBeInTheDocument();

      // Should call reset when retry is clicked
      fireEvent.click(retryButton);
      expect(mockReset).toHaveBeenCalledTimes(1);
    });

    it("should show appropriate suggestions for different error types", () => {
      const error = new Error("Chunk loading failed");
      const mockReset = jest.fn();

      render(
        <EnhancedErrorFallback
          error={error}
          resetErrorBoundary={mockReset}
          errorType="chunk"
        />
      );

      expect(screen.getByText("Loading Error")).toBeInTheDocument();
      expect(
        screen.getByText(/Refresh the page to reload resources/)
      ).toBeInTheDocument();
      expect(screen.getByText(/Clear your browser cache/)).toBeInTheDocument();
    });

    it("should handle authentication errors with appropriate actions", () => {
      const error = new Error("Authentication failed");
      const mockReset = jest.fn();

      render(
        <EnhancedErrorFallback
          error={error}
          resetErrorBoundary={mockReset}
          errorType="authentication"
          customActions={[
            {
              label: "Sign In Again",
              type: "primary",
              onClick: () => (window.location.href = "/login"),
            },
          ]}
        />
      );

      expect(screen.getByText("Authentication Error")).toBeInTheDocument();

      const signInButton = screen.getByRole("button", {
        name: /sign in again/i,
      });
      fireEvent.click(signInButton);

      expect(window.location.href).toBe("/login");
    });
  });
});
