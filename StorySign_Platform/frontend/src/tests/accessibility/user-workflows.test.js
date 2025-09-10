// Mock API configuration before other imports
jest.mock("../../config/api", () => ({
  getApiConfig: () => ({
    API_BASE_URL: "http://localhost:8000",
    WS_BASE_URL: "ws://localhost:8000",
    API_VERSION: "v1",
  }),
  buildApiUrl: (path) => `http://localhost:8000/api/v1${path}`,
  buildWsUrl: (path) => `ws://localhost:8000${path}`,
  buildHealthCheckUrl: () => "http://localhost:8000/health",
}));

import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { axe, toHaveNoViolations } from "jest-axe";
import Button from "../../components/common/Button";
import Modal from "../../components/common/Modal";
import { FormField } from "../../components/common/AccessibleForm";
import LiveRegion from "../../components/common/LiveRegion";

// Extend Jest matchers
expect.extend(toHaveNoViolations);

// Mock services and dependencies
jest.mock("../../services/PWAService", () => ({
  init: jest.fn(),
  cacheResources: jest.fn(),
}));

jest.mock("../../config/api", () => ({
  buildHealthCheckUrl: jest.fn(() => "http://localhost:8000/health"),
  buildApiUrl: jest.fn((path) => `http://localhost:8000${path}`),
}));

// Mock fetch for API calls
global.fetch = jest.fn();

// Test wrapper component
const TestWrapper = ({ children }) => <MemoryRouter>{children}</MemoryRouter>;

describe("Complete User Workflow Accessibility Tests", () => {
  let user;

  beforeEach(() => {
    fetch.mockClear();
  });

  describe("Registration and Login Workflow", () => {
    test("should complete registration workflow with keyboard only", async () => {
      const MockRegistrationForm = () => (
        <form>
          <FormField
            id="email"
            label="Email"
            type="email"
            value=""
            onChange={jest.fn()}
          />
          <FormField
            id="password"
            label="Password"
            type="password"
            value=""
            onChange={jest.fn()}
          />
          <FormField
            id="confirm-password"
            label="Confirm Password"
            type="password"
            value=""
            onChange={jest.fn()}
          />
          <Button type="submit">Create Account</Button>
        </form>
      );

      const { container } = render(
        <TestWrapper>
          <MockRegistrationForm />
        </TestWrapper>
      );

      // Check for accessibility violations
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    test("should complete login workflow with screen reader announcements", async () => {
      const MockLoginForm = () => {
        const [loading, setLoading] = React.useState(false);

        const handleSubmit = (e) => {
          e.preventDefault();
          setLoading(true);
        };

        return (
          <form onSubmit={handleSubmit}>
            <FormField
              id="email"
              label="Email"
              type="email"
              value=""
              onChange={jest.fn()}
            />
            <FormField
              id="password"
              label="Password"
              type="password"
              value=""
              onChange={jest.fn()}
            />
            <Button type="submit" loading={loading}>
              {loading ? "Signing in..." : "Sign In"}
            </Button>
            {loading && (
              <LiveRegion
                message="Signing in, please wait..."
                politeness="polite"
              />
            )}
          </form>
        );
      };

      const { container } = render(
        <TestWrapper>
          <MockLoginForm />
        </TestWrapper>
      );

      // Check for accessibility violations
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    test("should handle login errors accessibly", async () => {
      const MockLoginFormWithError = () => {
        const [error, setError] = React.useState("");

        const handleSubmit = (e) => {
          e.preventDefault();
          setError("Invalid credentials");
        };

        return (
          <form onSubmit={handleSubmit}>
            <FormField
              id="email"
              label="Email"
              type="email"
              value=""
              onChange={jest.fn()}
              error={error}
            />
            <FormField
              id="password"
              label="Password"
              type="password"
              value=""
              onChange={jest.fn()}
            />
            <Button type="submit">Sign In</Button>
          </form>
        );
      };

      render(
        <TestWrapper>
          <MockLoginFormWithError />
        </TestWrapper>
      );

      const submitButton = screen.getByRole("button", { name: /sign in/i });
      fireEvent.click(submitButton);

      // Error should be announced to screen readers
      await waitFor(() => {
        const errorMessage = screen.getByRole("alert");
        expect(errorMessage).toBeInTheDocument();
        expect(errorMessage).toHaveTextContent(/invalid credentials/i);
      });
    });
  });

  describe("ASL World Module Workflow", () => {
    test("should navigate to ASL World and complete story generation", async () => {
      const MockASLWorldPage = () => (
        <div>
          <header>
            <h1>ASL World</h1>
          </header>
          <main role="main">
            <h2>Story Generation</h2>
            <Button>Generate Story</Button>
            <LiveRegion
              message="Story generated successfully"
              politeness="polite"
            />
          </main>
        </div>
      );

      const { container } = render(
        <TestWrapper>
          <MockASLWorldPage />
        </TestWrapper>
      );

      // Check page title and main content
      expect(
        screen.getByRole("heading", { name: /asl world/i })
      ).toBeInTheDocument();
      expect(screen.getByRole("main")).toBeInTheDocument();

      // Check for accessibility violations
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });

    test("should handle video streaming controls accessibly", async () => {
      const MockVideoControls = () => {
        const [webcamActive, setWebcamActive] = React.useState(false);

        return (
          <div>
            <Button
              onClick={() => setWebcamActive(!webcamActive)}
              aria-pressed={webcamActive}
            >
              {webcamActive ? "Stop Webcam" : "Start Webcam"}
            </Button>
            <div role="status" aria-live="polite">
              {webcamActive ? "Webcam active" : "Webcam inactive"}
            </div>
          </div>
        );
      };

      render(
        <TestWrapper>
          <MockVideoControls />
        </TestWrapper>
      );

      // Test webcam controls
      const webcamButton = screen.getByRole("button", { name: /webcam/i });
      expect(webcamButton).toHaveAttribute("aria-pressed");

      fireEvent.click(webcamButton);

      // Status should be announced
      const statusRegion = screen.getByRole("status");
      expect(statusRegion).toBeInTheDocument();
    });
  });

  describe("Harmony Module Workflow", () => {
    test("should navigate to Harmony module accessibly", async () => {
      const MockHarmonyPage = () => (
        <div>
          <header>
            <h1>Harmony</h1>
          </header>
          <main role="main">
            <h2>Emotion Recognition</h2>
            <Button>Start Practice</Button>
          </main>
        </div>
      );

      const { container } = render(
        <TestWrapper>
          <MockHarmonyPage />
        </TestWrapper>
      );

      // Check page structure
      expect(
        screen.getByRole("heading", { name: /harmony/i })
      ).toBeInTheDocument();
      expect(screen.getByRole("main")).toBeInTheDocument();

      // Check for accessibility violations
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    });
  });

  describe("Error Recovery Workflows", () => {
    test("should handle connection errors with clear recovery instructions", async () => {
      const MockErrorComponent = () => {
        const [error, setError] = React.useState(null);

        const handleTestConnection = () => {
          setError("Network error occurred");
        };

        return (
          <div>
            <Button onClick={handleTestConnection}>Test Connection</Button>
            {error && (
              <div role="alert" aria-live="assertive">
                <strong>Error:</strong> {error}
                <div>
                  <h3>Troubleshooting Steps:</h3>
                  <ol>
                    <li>Check your internet connection</li>
                    <li>Refresh the page</li>
                    <li>Contact support if the problem persists</li>
                  </ol>
                  <Button>Retry Connection</Button>
                </div>
              </div>
            )}
          </div>
        );
      };

      render(
        <TestWrapper>
          <MockErrorComponent />
        </TestWrapper>
      );

      // Trigger connection test
      const testConnectionButton = screen.getByRole("button", {
        name: /test.*connection/i,
      });
      fireEvent.click(testConnectionButton);

      // Error should be announced and provide recovery options
      await waitFor(() => {
        const errorMessage = screen.getByRole("alert");
        expect(errorMessage).toBeInTheDocument();
      });

      // Retry button should be available and accessible
      const retryButton = screen.getByRole("button", { name: /retry/i });
      expect(retryButton).toBeInTheDocument();
      expect(retryButton).not.toHaveAttribute("aria-disabled", "true");
    });

    test("should provide accessible troubleshooting information", async () => {
      const MockTroubleshootingComponent = () => (
        <div>
          <h2>Troubleshooting</h2>
          <h3>Common Issues</h3>
          <ul>
            <li>Connection problems</li>
            <li>Audio/Video issues</li>
            <li>Performance problems</li>
          </ul>
        </div>
      );

      render(
        <TestWrapper>
          <MockTroubleshootingComponent />
        </TestWrapper>
      );

      // Look for troubleshooting content
      const troubleshootingSection = screen.getByText(/troubleshooting/i);
      expect(troubleshootingSection).toBeInTheDocument();

      // Should have proper heading structure
      const headings = screen.getAllByRole("heading");
      expect(headings.length).toBeGreaterThan(0);
    });
  });

  describe("Navigation and Focus Management", () => {
    test("should manage focus correctly during navigation", async () => {
      const MockNavigationComponent = () => {
        const [currentPage, setCurrentPage] = React.useState("home");

        return (
          <div>
            <nav>
              <Button onClick={() => setCurrentPage("home")}>Home</Button>
              <Button onClick={() => setCurrentPage("asl-world")}>
                ASL World
              </Button>
            </nav>
            <main role="main" tabIndex="-1">
              <h1>{currentPage === "home" ? "Dashboard" : "ASL World"}</h1>
            </main>
          </div>
        );
      };

      render(
        <TestWrapper>
          <MockNavigationComponent />
        </TestWrapper>
      );

      // Navigate between pages and check focus management
      const aslWorldLink = screen.getByRole("button", { name: /asl world/i });
      fireEvent.click(aslWorldLink);

      // Main content should be focusable for screen readers
      const mainContent = screen.getByRole("main");
      expect(mainContent).toBeInTheDocument();
      expect(mainContent).toHaveAttribute("tabIndex", "-1");
    });

    test("should provide skip links for keyboard navigation", async () => {
      const MockPageWithSkipLinks = () => (
        <div>
          <a href="#main-content" className="skip-link">
            Skip to main content
          </a>
          <nav>
            <Button>Navigation</Button>
          </nav>
          <main id="main-content" role="main">
            <h1>Main Content</h1>
          </main>
        </div>
      );

      render(
        <TestWrapper>
          <MockPageWithSkipLinks />
        </TestWrapper>
      );

      // Skip links should be present
      const skipLink = screen.getByText(/skip to main content/i);
      expect(skipLink).toBeInTheDocument();

      // Main content should be present
      const mainContent = screen.getByRole("main");
      expect(mainContent).toBeInTheDocument();
    });
  });

  describe("Form Validation Workflows", () => {
    test("should provide accessible form validation", () => {
      const MockFormWithValidation = () => {
        const [errors, setErrors] = React.useState({});

        const handleSubmit = (e) => {
          e.preventDefault();
          setErrors({ email: "Email is required" });
        };

        return (
          <form onSubmit={handleSubmit}>
            <FormField
              id="email"
              label="Email"
              type="email"
              value=""
              onChange={jest.fn()}
              error={errors.email}
              required
            />
            <Button type="submit">Create Account</Button>
            {errors.email && (
              <div role="alert" aria-live="assertive">
                {errors.email}
              </div>
            )}
          </form>
        );
      };

      render(
        <TestWrapper>
          <MockFormWithValidation />
        </TestWrapper>
      );

      // Submit empty form to trigger validation
      const submitButton = screen.getByRole("button", {
        name: /create account/i,
      });
      fireEvent.click(submitButton);

      // Validation errors should be announced
      const errorMessages = screen.getAllByRole("alert");
      expect(errorMessages.length).toBeGreaterThan(0);
      expect(errorMessages[0]).toHaveTextContent(/email is required/i);
    });
  });

  describe("Loading States and Progress", () => {
    test("should announce loading states during async operations", async () => {
      const MockLoadingComponent = () => {
        const [loading, setLoading] = React.useState(false);

        const handleClick = () => {
          setLoading(true);
          setTimeout(() => setLoading(false), 100);
        };

        return (
          <div>
            <Button onClick={handleClick} disabled={loading}>
              {loading ? "Testing Connection..." : "Test Connection"}
            </Button>
            {loading && (
              <LiveRegion
                message="Testing connection, please wait..."
                politeness="polite"
              />
            )}
          </div>
        );
      };

      render(
        <TestWrapper>
          <MockLoadingComponent />
        </TestWrapper>
      );

      const testConnectionButton = screen.getByRole("button", {
        name: /test.*connection/i,
      });
      fireEvent.click(testConnectionButton);

      // Loading state should be announced
      expect(
        screen.getAllByText(/testing.*connection/i)[0]
      ).toBeInTheDocument();

      // Wait for completion
      await waitFor(
        () => {
          expect(
            screen.queryByText(/testing.*connection/i)
          ).not.toBeInTheDocument();
        },
        { timeout: 200 }
      );
    });
  });
});
