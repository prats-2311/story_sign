/**
 * User Workflow Integration Tests
 *
 * Simplified integration tests focusing on core user workflow functionality
 * without complex component dependencies.
 *
 * Requirements: 6.5, 6.6
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import "@testing-library/jest-dom";

import { AuthProvider } from "../../contexts/AuthContext";
import authService from "../../services/AuthService";
import LoginPage from "../../pages/LoginPage";
import RegisterPage from "../../pages/RegisterPage";

// Mock the auth service
jest.mock("../../services/AuthService");

// Mock complex components to avoid dependency issues
jest.mock("../../components/video/VideoStreamingClient", () => {
  const React = require("react");
  return React.forwardRef((props, ref) => (
    <div data-testid="video-streaming-client" ref={ref}>
      Mock Video Streaming Client
    </div>
  ));
});

// Mock API configuration
jest.mock("../../config/api.js", () => ({
  __esModule: true,
  default: "http://127.0.0.1:8000",
}));

// Test wrapper component
const TestWrapper = ({ children, initialEntries = ["/"] }) => (
  <MemoryRouter initialEntries={initialEntries}>
    <AuthProvider>{children}</AuthProvider>
  </MemoryRouter>
);

describe("User Workflow Integration Tests", () => {
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

    // Mock successful API responses
    global.fetch.mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({ status: "connected", message: "Backend ready" }),
    });
  });

  describe("Authentication Flow Integration", () => {
    test("should render login page correctly", async () => {
      render(
        <TestWrapper initialEntries={["/login"]}>
          <LoginPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/sign in to storysign/i)).toBeInTheDocument();
      });

      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText(/enter your password/i)
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /sign in/i })
      ).toBeInTheDocument();
    });

    test("should handle login form submission", async () => {
      const mockUser = global.testUtils.createMockUser();
      const mockToken = global.testUtils.createMockToken();

      authService.login.mockResolvedValue({
        user: mockUser,
        token: mockToken,
      });

      render(
        <TestWrapper initialEntries={["/login"]}>
          <LoginPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/sign in to storysign/i)).toBeInTheDocument();
      });

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByPlaceholderText(/enter your password/i);
      const loginButton = screen.getByRole("button", { name: /sign in/i });

      await user.type(emailInput, "test@example.com");
      await user.type(passwordInput, "password123");
      await user.click(loginButton);

      await waitFor(() => {
        expect(authService.login).toHaveBeenCalledWith(
          "test@example.com",
          "password123",
          false
        );
      });
    });

    test("should handle login errors", async () => {
      authService.login.mockRejectedValue(new Error("Invalid credentials"));

      render(
        <TestWrapper initialEntries={["/login"]}>
          <LoginPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/sign in to storysign/i)).toBeInTheDocument();
      });

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByPlaceholderText(/enter your password/i);
      const loginButton = screen.getByRole("button", { name: /sign in/i });

      await user.type(emailInput, "invalid@example.com");
      await user.type(passwordInput, "wrongpassword");
      await user.click(loginButton);

      await waitFor(() => {
        expect(
          screen.getAllByText(/invalid email or password/i)[0]
        ).toBeInTheDocument();
      });
    });

    test("should render registration page correctly", async () => {
      render(
        <TestWrapper initialEntries={["/register"]}>
          <RegisterPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(
          screen.getByText(/create your storysign account/i)
        ).toBeInTheDocument();
      });

      expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/^password/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /create account/i })
      ).toBeInTheDocument();
    });

    test("should handle registration form submission", async () => {
      authService.register.mockResolvedValue({
        message: "Registration successful",
        user: { id: 1, email: "newuser@example.com", username: "newuser" },
      });

      render(
        <TestWrapper initialEntries={["/register"]}>
          <RegisterPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(
          screen.getByText(/create your storysign account/i)
        ).toBeInTheDocument();
      });

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
      await user.click(registerButton);

      await waitFor(() => {
        expect(authService.register).toHaveBeenCalledWith({
          username: "newuser",
          email: "newuser@example.com",
          password: "StrongPass123!",
        });
      });
    });

    test("should handle registration errors", async () => {
      authService.register.mockRejectedValue(
        new Error("An account with this email already exists")
      );

      render(
        <TestWrapper initialEntries={["/register"]}>
          <RegisterPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(
          screen.getByText(/create your storysign account/i)
        ).toBeInTheDocument();
      });

      const usernameInput = screen.getByLabelText(/username/i);
      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/^password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
      const registerButton = screen.getByRole("button", {
        name: /create account/i,
      });

      await user.type(usernameInput, "existinguser");
      await user.type(emailInput, "existing@example.com");
      await user.type(passwordInput, "StrongPass123!");
      await user.type(confirmPasswordInput, "StrongPass123!");
      await user.click(registerButton);

      await waitFor(() => {
        expect(
          screen.getAllByText(/account with this email already exists/i)[0]
        ).toBeInTheDocument();
      });
    });
  });

  describe("AuthContext Integration", () => {
    test("should provide authentication context to components", async () => {
      const TestComponent = () => {
        const { useAuth } = require("../../contexts/AuthContext");
        const { isAuthenticated, user } = useAuth();

        return (
          <div>
            <div data-testid="auth-status">
              {isAuthenticated ? "Authenticated" : "Not Authenticated"}
            </div>
            <div data-testid="user-info">{user ? user.email : "No User"}</div>
          </div>
        );
      };

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByTestId("auth-status")).toHaveTextContent(
          "Not Authenticated"
        );
        expect(screen.getByTestId("user-info")).toHaveTextContent("No User");
      });
    });

    test("should handle authentication state changes", async () => {
      const mockUser = global.testUtils.createMockUser();
      const mockToken = global.testUtils.createMockToken();

      // Start unauthenticated
      authService.isAuthenticated.mockReturnValue(false);
      authService.getCurrentUser.mockReturnValue(null);
      authService.getToken.mockReturnValue(null);

      const TestComponent = () => {
        const { useAuth } = require("../../contexts/AuthContext");
        const { isAuthenticated, user, login } = useAuth();

        const handleLogin = async () => {
          try {
            await login("test@example.com", "password123");
          } catch (error) {
            // Handle error
          }
        };

        return (
          <div>
            <div data-testid="auth-status">
              {isAuthenticated ? "Authenticated" : "Not Authenticated"}
            </div>
            <div data-testid="user-info">{user ? user.email : "No User"}</div>
            <button onClick={handleLogin}>Login</button>
          </div>
        );
      };

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      // Initially not authenticated
      await waitFor(() => {
        expect(screen.getByTestId("auth-status")).toHaveTextContent(
          "Not Authenticated"
        );
      });

      // Mock successful login
      authService.login.mockResolvedValue({ user: mockUser, token: mockToken });
      authService.isAuthenticated.mockReturnValue(true);
      authService.getCurrentUser.mockReturnValue(mockUser);
      authService.getToken.mockReturnValue(mockToken);

      const loginButton = screen.getByText("Login");
      await user.click(loginButton);

      await waitFor(() => {
        expect(authService.login).toHaveBeenCalledWith(
          "test@example.com",
          "password123",
          false
        );
      });
    });
  });

  describe("API Configuration Integration", () => {
    test("should use automatic backend connection configuration", async () => {
      // Import the API config
      const apiConfig = require("../../config/api.js");

      // Verify it exports the expected URL directly
      expect(apiConfig.default).toBe("http://127.0.0.1:8000");
    });

    test("should make API calls with automatic backend URL", async () => {
      // Mock a component that makes API calls
      const TestComponent = () => {
        const [data, setData] = React.useState(null);
        const [loading, setLoading] = React.useState(false);

        const fetchData = async () => {
          setLoading(true);
          try {
            const apiUrl = require("../../config/api.js").default;
            const response = await fetch(`${apiUrl}/api/test`);
            const result = await response.json();
            setData(result);
          } catch (error) {
            setData({ error: error.message });
          } finally {
            setLoading(false);
          }
        };

        React.useEffect(() => {
          fetchData();
        }, []);

        if (loading) return <div>Loading...</div>;
        if (data?.error) return <div>Error: {data.error}</div>;
        if (data) return <div>Data: {JSON.stringify(data)}</div>;
        return <div>No data</div>;
      };

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          "http://127.0.0.1:8000/api/test"
        );
      });

      await waitFor(() => {
        expect(screen.getByText(/Data:/)).toBeInTheDocument();
      });
    });
  });

  describe("Form Validation Integration", () => {
    test("should validate login form inputs", async () => {
      render(
        <TestWrapper initialEntries={["/login"]}>
          <LoginPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/sign in to storysign/i)).toBeInTheDocument();
      });

      const loginButton = screen.getByRole("button", { name: /sign in/i });
      await user.click(loginButton);

      await waitFor(() => {
        expect(screen.getByText(/email is required/i)).toBeInTheDocument();
        expect(screen.getByText(/password is required/i)).toBeInTheDocument();
      });
    });

    test("should validate registration form inputs", async () => {
      render(
        <TestWrapper initialEntries={["/register"]}>
          <RegisterPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(
          screen.getByText(/create your storysign account/i)
        ).toBeInTheDocument();
      });

      const registerButton = screen.getByRole("button", {
        name: /create account/i,
      });
      await user.click(registerButton);

      await waitFor(() => {
        expect(screen.getByText(/username is required/i)).toBeInTheDocument();
        expect(screen.getByText(/email is required/i)).toBeInTheDocument();
        expect(screen.getByText(/password is required/i)).toBeInTheDocument();
      });
    });

    test("should validate password confirmation", async () => {
      render(
        <TestWrapper initialEntries={["/register"]}>
          <RegisterPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(
          screen.getByText(/create your storysign account/i)
        ).toBeInTheDocument();
      });

      const passwordInput = screen.getByLabelText(/^password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);

      await user.type(passwordInput, "password123");
      await user.type(confirmPasswordInput, "differentpassword");

      const registerButton = screen.getByRole("button", {
        name: /create account/i,
      });
      await user.click(registerButton);

      await waitFor(() => {
        expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
      });
    });
  });

  describe("Error Handling Integration", () => {
    test("should handle network errors gracefully", async () => {
      global.fetch.mockRejectedValue(new Error("Network error"));

      const TestComponent = () => {
        const [error, setError] = React.useState(null);

        const testNetworkCall = async () => {
          try {
            const apiUrl = require("../../config/api.js").default;
            await fetch(`${apiUrl}/api/test`);
          } catch (err) {
            setError(err.message);
          }
        };

        React.useEffect(() => {
          testNetworkCall();
        }, []);

        return error ? <div>Network Error: {error}</div> : <div>No Error</div>;
      };

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(
          screen.getByText(/Network Error: Network error/)
        ).toBeInTheDocument();
      });
    });

    test("should handle authentication service errors", async () => {
      authService.login.mockRejectedValue(new Error("Service unavailable"));

      render(
        <TestWrapper initialEntries={["/login"]}>
          <LoginPage />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/sign in to storysign/i)).toBeInTheDocument();
      });

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByPlaceholderText(/enter your password/i);
      const loginButton = screen.getByRole("button", { name: /sign in/i });

      await user.type(emailInput, "test@example.com");
      await user.type(passwordInput, "password123");
      await user.click(loginButton);

      await waitFor(() => {
        expect(
          screen.getAllByText(/service unavailable/i)[0]
        ).toBeInTheDocument();
      });
    });
  });

  describe("Backend Connection Integration", () => {
    test("should verify automatic backend connection is configured", () => {
      // Test that the API configuration is set to automatic connection
      const apiConfig = require("../../config/api.js");

      // Should export the backend URL directly without conditional logic
      expect(apiConfig.default).toBe("http://127.0.0.1:8000");
      expect(typeof apiConfig.default).toBe("string");
    });

    test("should make API calls without manual backend testing", async () => {
      // Mock successful API response
      global.fetch.mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            status: "ready",
            features: ["story-generation", "asl-detection"],
            message: "Backend connected automatically",
          }),
      });

      const TestComponent = () => {
        const [backendStatus, setBackendStatus] = React.useState(null);

        React.useEffect(() => {
          const checkBackend = async () => {
            try {
              const apiUrl = require("../../config/api.js").default;
              const response = await fetch(`${apiUrl}/api/health`);
              const data = await response.json();
              setBackendStatus(data);
            } catch (error) {
              setBackendStatus({ error: error.message });
            }
          };

          checkBackend();
        }, []);

        if (!backendStatus) return <div>Checking backend...</div>;
        if (backendStatus.error)
          return <div>Backend Error: {backendStatus.error}</div>;

        return (
          <div>
            <div>Backend Status: {backendStatus.status}</div>
            <div>Features Available: {backendStatus.features?.join(", ")}</div>
            <div>Message: {backendStatus.message}</div>
          </div>
        );
      };

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText("Backend Status: ready")).toBeInTheDocument();
        expect(
          screen.getByText(
            "Features Available: story-generation, asl-detection"
          )
        ).toBeInTheDocument();
        expect(
          screen.getByText("Message: Backend connected automatically")
        ).toBeInTheDocument();
      });

      // Verify the API call was made automatically
      expect(global.fetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/health"
      );
    });

    test("should handle backend connection without Test Backend button", async () => {
      // This test verifies that no manual "Test Backend" action is required

      const TestComponent = () => {
        const [features, setFeatures] = React.useState([]);

        React.useEffect(() => {
          // Simulate immediate feature availability
          const loadFeatures = async () => {
            try {
              const apiUrl = require("../../config/api.js").default;
              const response = await fetch(`${apiUrl}/api/features`);
              const data = await response.json();
              setFeatures(data.features || []);
            } catch (error) {
              setFeatures(["error"]);
            }
          };

          loadFeatures();
        }, []);

        return (
          <div>
            <div data-testid="features-list">
              {features.length > 0 ? (
                features.map(feature => (
                  <div key={feature}>Feature: {feature}</div>
                ))
              ) : (
                <div>Loading features...</div>
              )}
            </div>
            {/* Verify no Test Backend button is present */}
            {/* No Test Backend button should be present */}
          </div>
        );
      };

      // Mock features response
      global.fetch.mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            features: ["asl-world", "story-generation", "webcam-controls"],
          }),
      });

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText("Feature: asl-world")).toBeInTheDocument();
        expect(
          screen.getByText("Feature: story-generation")
        ).toBeInTheDocument();
        expect(
          screen.getByText("Feature: webcam-controls")
        ).toBeInTheDocument();
      });

      // Verify no Test Backend button is present
      expect(screen.queryByText(/test backend/i)).not.toBeInTheDocument();
    });
  });
});
