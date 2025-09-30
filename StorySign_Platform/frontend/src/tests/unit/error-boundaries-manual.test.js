/**
 * Manual Error Boundaries Test
 * Simple test to verify error boundaries work correctly
 */

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import "@testing-library/jest-dom";

import {
  EnhancedErrorFallback,
  NetworkErrorBoundary,
  AuthenticationErrorBoundary,
  ComponentLoadingErrorBoundary,
  RouteErrorBoundary,
} from "../components/error/ErrorBoundaries";

// Test wrapper component
const TestWrapper = ({ children }) => <BrowserRouter>{children}</BrowserRouter>;

// Component that throws an error
const ErrorThrowingComponent = ({ errorType = "general" }) => {
  const error = new Error("Test error");

  if (errorType === "network") {
    error.name = "TypeError";
    error.message = "Failed to fetch";
  } else if (errorType === "chunk") {
    error.name = "ChunkLoadError";
    error.message = "Loading chunk 1 failed";
  } else if (errorType === "auth") {
    error.status = 401;
    error.message = "Unauthorized";
  }

  throw error;
};

describe("Error Boundaries Manual Tests", () => {
  beforeEach(() => {
    // Mock console.error to avoid test noise
    jest.spyOn(console, "error").mockImplementation(() => {});

    // Mock window.location
    delete window.location;
    window.location = { href: "", reload: jest.fn() };
  });

  afterEach(() => {
    console.error.mockRestore();
    jest.clearAllMocks();
  });

  describe("EnhancedErrorFallback", () => {
    it("should display network error correctly", () => {
      const error = new Error("Network connection failed");
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
      expect(
        screen.getByRole("button", { name: /reload page/i })
      ).toBeInTheDocument();
    });

    it("should display authentication error correctly", () => {
      const error = new Error("Authentication failed");
      const mockReset = jest.fn();

      render(
        <EnhancedErrorFallback
          error={error}
          resetErrorBoundary={mockReset}
          errorType="authentication"
        />
      );

      expect(screen.getByText("Authentication Error")).toBeInTheDocument();
      expect(
        screen.getByText(/There was a problem with your authentication/)
      ).toBeInTheDocument();
    });

    it("should display chunk loading error correctly", () => {
      const error = new Error("Loading chunk failed");
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
        screen.getByText(/Failed to load application resources/)
      ).toBeInTheDocument();
    });

    it("should handle retry button click", () => {
      const error = new Error("Test error");
      const mockReset = jest.fn();

      render(
        <EnhancedErrorFallback error={error} resetErrorBoundary={mockReset} />
      );

      const retryButton = screen.getByRole("button", { name: /try again/i });
      fireEvent.click(retryButton);

      expect(mockReset).toHaveBeenCalledTimes(1);
    });

    it("should handle reload button click", () => {
      const error = new Error("Test error");
      const mockReset = jest.fn();

      render(
        <EnhancedErrorFallback error={error} resetErrorBoundary={mockReset} />
      );

      const reloadButton = screen.getByRole("button", { name: /reload page/i });
      fireEvent.click(reloadButton);

      expect(window.location.reload).toHaveBeenCalledTimes(1);
    });

    it("should show/hide error details", () => {
      const error = new Error("Detailed error message");
      const mockReset = jest.fn();

      render(
        <EnhancedErrorFallback error={error} resetErrorBoundary={mockReset} />
      );

      // Details should be hidden initially
      expect(screen.queryByText("Technical Details")).not.toBeInTheDocument();

      // Click show details
      const detailsButton = screen.getByRole("button", {
        name: /show details/i,
      });
      fireEvent.click(detailsButton);

      // Details should now be visible
      expect(screen.getByText("Technical Details")).toBeInTheDocument();
      expect(screen.getByText("Detailed error message")).toBeInTheDocument();

      // Click hide details
      const hideButton = screen.getByRole("button", { name: /hide details/i });
      fireEvent.click(hideButton);
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
            {
              label: "Custom Action",
              onClick: mockCustomAction,
              type: "primary",
            },
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

  describe("NetworkErrorBoundary", () => {
    it("should catch network errors and display fallback", () => {
      render(
        <TestWrapper>
          <NetworkErrorBoundary componentName="Test Network Component">
            <ErrorThrowingComponent errorType="network" />
          </NetworkErrorBoundary>
        </TestWrapper>
      );

      expect(screen.getByText("Connection Error")).toBeInTheDocument();
      expect(
        screen.getByText(/Unable to connect to the server/)
      ).toBeInTheDocument();
    });

    it("should render children when no error occurs", () => {
      render(
        <TestWrapper>
          <NetworkErrorBoundary componentName="Test Network Component">
            <div>No error occurred</div>
          </NetworkErrorBoundary>
        </TestWrapper>
      );

      expect(screen.getByText("No error occurred")).toBeInTheDocument();
    });
  });

  describe("AuthenticationErrorBoundary", () => {
    it("should catch authentication errors and display fallback", () => {
      render(
        <TestWrapper>
          <AuthenticationErrorBoundary>
            <ErrorThrowingComponent errorType="auth" />
          </AuthenticationErrorBoundary>
        </TestWrapper>
      );

      expect(screen.getByText("Authentication Error")).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /sign in again/i })
      ).toBeInTheDocument();
    });

    it("should redirect to login when sign in again is clicked", () => {
      render(
        <TestWrapper>
          <AuthenticationErrorBoundary>
            <ErrorThrowingComponent errorType="auth" />
          </AuthenticationErrorBoundary>
        </TestWrapper>
      );

      const signInButton = screen.getByRole("button", {
        name: /sign in again/i,
      });
      fireEvent.click(signInButton);

      expect(window.location.href).toBe("/login");
    });
  });

  describe("ComponentLoadingErrorBoundary", () => {
    it("should catch component loading errors and display fallback", () => {
      render(
        <TestWrapper>
          <ComponentLoadingErrorBoundary componentName="Test Component">
            <ErrorThrowingComponent errorType="chunk" />
          </ComponentLoadingErrorBoundary>
        </TestWrapper>
      );

      expect(screen.getByText("Loading Error")).toBeInTheDocument();
      expect(
        screen.getByText(/Failed to load application resources/)
      ).toBeInTheDocument();
    });

    it("should suggest page reload for chunk errors", () => {
      render(
        <TestWrapper>
          <ComponentLoadingErrorBoundary componentName="Test Component">
            <ErrorThrowingComponent errorType="chunk" />
          </ComponentLoadingErrorBoundary>
        </TestWrapper>
      );

      expect(
        screen.getByRole("button", { name: /reload page/i })
      ).toBeInTheDocument();
    });
  });

  describe("RouteErrorBoundary", () => {
    it("should catch route errors and display fallback", () => {
      render(
        <TestWrapper>
          <RouteErrorBoundary routeName="Dashboard" fallbackRoute="/dashboard">
            <ErrorThrowingComponent />
          </RouteErrorBoundary>
        </TestWrapper>
      );

      expect(
        screen.getByText(/Failed to Load Dashboard Page/)
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /go to dashboard/i })
      ).toBeInTheDocument();
    });

    it("should navigate to fallback route when button is clicked", () => {
      render(
        <TestWrapper>
          <RouteErrorBoundary routeName="ASL World" fallbackRoute="/dashboard">
            <ErrorThrowingComponent />
          </RouteErrorBoundary>
        </TestWrapper>
      );

      const fallbackButton = screen.getByRole("button", {
        name: /go to dashboard/i,
      });
      fireEvent.click(fallbackButton);

      expect(window.location.href).toBe("/dashboard");
    });
  });

  describe("Error Boundary Integration", () => {
    it("should handle nested error boundaries correctly", () => {
      render(
        <TestWrapper>
          <NetworkErrorBoundary componentName="Outer Network">
            <ComponentLoadingErrorBoundary componentName="Inner Component">
              <ErrorThrowingComponent errorType="chunk" />
            </ComponentLoadingErrorBoundary>
          </NetworkErrorBoundary>
        </TestWrapper>
      );

      // Should show the inner error boundary (ComponentLoadingErrorBoundary)
      expect(screen.getByText("Loading Error")).toBeInTheDocument();
    });

    it("should reset error state when retry is clicked", () => {
      let shouldThrow = true;

      const ConditionalErrorComponent = () => {
        if (shouldThrow) {
          throw new Error("Conditional error");
        }
        return <div>Component loaded successfully</div>;
      };

      const { rerender } = render(
        <TestWrapper>
          <ComponentLoadingErrorBoundary componentName="Conditional Component">
            <ConditionalErrorComponent />
          </ComponentLoadingErrorBoundary>
        </TestWrapper>
      );

      // Should show error initially
      expect(
        screen.getByText(/Failed to Load Conditional Component/)
      ).toBeInTheDocument();

      // Simulate fixing the error
      shouldThrow = false;

      const retryButton = screen.getByRole("button", { name: /try again/i });
      fireEvent.click(retryButton);

      // Re-render with fixed component
      rerender(
        <TestWrapper>
          <ComponentLoadingErrorBoundary componentName="Conditional Component">
            <ConditionalErrorComponent />
          </ComponentLoadingErrorBoundary>
        </TestWrapper>
      );

      // Should show successful component
      expect(
        screen.getByText("Component loaded successfully")
      ).toBeInTheDocument();
    });
  });
});
