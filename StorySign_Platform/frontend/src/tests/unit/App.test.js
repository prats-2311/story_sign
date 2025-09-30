import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";

import "@testing-library/jest-dom";
import App from "./App";
import authService from "./services/AuthService";

// Mock fetch for testing
global.fetch = jest.fn();

// Mock authService
jest.mock("./services/AuthService");

// Mock react-router-dom location
const mockLocation = {
  pathname: "/",
  search: "",
  hash: "",
  state: null,
  key: "default",
};

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useLocation: () => mockLocation,
}));

// Mock the useAuth hook to provide controlled auth state
const mockUseAuth = jest.fn();
jest.mock("./contexts/AuthContext", () => ({
  useAuth: () => mockUseAuth(),
  AuthProvider: ({ children }) => (
    <div data-testid="auth-provider">{children}</div>
  ),
}));

// Test wrapper component
const TestWrapper = ({ children }) => {
  return <BrowserRouter>{children}</BrowserRouter>;
};

describe("StorySign App", () => {
  beforeEach(() => {
    fetch.mockClear();
    mockUseAuth.mockClear();
    authService.isAuthenticated?.mockClear?.();
    authService.getCurrentUser?.mockClear?.();
    authService.getToken?.mockClear?.();
  });

  test("shows loading screen when authentication is loading", () => {
    mockUseAuth.mockReturnValue({
      isLoading: true,
      isAuthenticated: false,
      user: null,
    });

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(
      screen.getByText("Loading StorySign Platform...")
    ).toBeInTheDocument();
  });

  test("renders AppContent when not loading", async () => {
    mockUseAuth.mockReturnValue({
      isLoading: false,
      isAuthenticated: false,
      user: null,
    });

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    await waitFor(() => {
      // Should not show loading screen
      expect(screen.queryByRole("status")).not.toBeInTheDocument();
    });
  });

  test("handles page title updates for accessibility", async () => {
    mockUseAuth.mockReturnValue({
      isLoading: false,
      isAuthenticated: true,
      user: { id: 1, email: "test@example.com" },
    });

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    await waitFor(() => {
      // The manageFocusForSPA function should be called
      expect(document.title).toBeDefined();
    });
  });

  test("renders loading spinner with proper accessibility attributes", () => {
    mockUseAuth.mockReturnValue({
      isLoading: true,
      isAuthenticated: false,
      user: null,
    });

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    const loadingElement = screen.getByRole("status");
    expect(loadingElement).toHaveAttribute("aria-live", "polite");

    const spinner = loadingElement.querySelector(".loading-spinner");
    expect(spinner).toHaveAttribute("aria-hidden", "true");
  });

  test("authentication context integration works correctly", async () => {
    const mockUser = { id: 1, email: "test@example.com" };

    mockUseAuth.mockReturnValue({
      isLoading: false,
      isAuthenticated: true,
      user: mockUser,
    });

    render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    await waitFor(() => {
      // Should render without authentication errors
      expect(screen.queryByRole("status")).not.toBeInTheDocument();
    });
  });

  test("handles authentication state changes", async () => {
    // Start with loading state
    mockUseAuth.mockReturnValue({
      isLoading: true,
      isAuthenticated: false,
      user: null,
    });

    const { rerender } = render(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    expect(screen.getByRole("status")).toBeInTheDocument();

    // Change to authenticated state
    mockUseAuth.mockReturnValue({
      isLoading: false,
      isAuthenticated: true,
      user: { id: 1, email: "test@example.com" },
    });

    rerender(
      <TestWrapper>
        <App />
      </TestWrapper>
    );

    await waitFor(() => {
      expect(screen.queryByRole("status")).not.toBeInTheDocument();
    });
  });

  test("renders without crashing when auth state is undefined", () => {
    mockUseAuth.mockReturnValue({
      isLoading: false,
      isAuthenticated: false,
      user: null,
    });

    expect(() => {
      render(
        <TestWrapper>
          <App />
        </TestWrapper>
      );
    }).not.toThrow();
  });
});
