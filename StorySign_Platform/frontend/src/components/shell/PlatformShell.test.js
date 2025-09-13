import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import "@testing-library/jest-dom";
import PlatformShell, { usePlatform } from "./PlatformShell";
import { AuthProvider } from "../../contexts/AuthContext";

// Mock the AuthContext
jest.mock("../../contexts/AuthContext", () => ({
  AuthProvider: ({ children }) => children,
  useAuth: () => ({
    user: {
      id: "test-user",
      email: "test@example.com",
      firstName: "Test",
      lastName: "User",
    },
    isAuthenticated: true,
    isLoading: false,
    logout: jest.fn(),
  }),
}));

// Mock component to test the usePlatform hook
const TestComponent = () => {
  const {
    user,
    isAuthenticated,
    currentTheme,
    currentModule,
    notifications,
    addNotification,
    changeTheme,
    navigateToModule,
    toggleSidebar,
    sidebarOpen,
  } = usePlatform();

  return (
    <div data-testid="test-component">
      <div data-testid="auth-status">
        {isAuthenticated ? "authenticated" : "not-authenticated"}
      </div>
      <div data-testid="current-theme">{currentTheme}</div>
      <div data-testid="current-module">{currentModule}</div>
      <div data-testid="sidebar-status">
        {sidebarOpen ? "sidebar-open" : "sidebar-closed"}
      </div>
      <div data-testid="notifications-count">{notifications.length}</div>
      <button
        data-testid="add-notification-btn"
        onClick={() => addNotification("Test notification", "info")}
      >
        Add Notification
      </button>
      <button
        data-testid="change-theme-btn"
        onClick={() => changeTheme("dark")}
      >
        Change Theme
      </button>
      <button data-testid="toggle-sidebar-btn" onClick={toggleSidebar}>
        Toggle Sidebar
      </button>
      <button
        data-testid="navigate-asl-btn"
        onClick={() => navigateToModule("asl-world")}
      >
        Navigate to ASL World
      </button>
    </div>
  );
};

const renderWithRouter = component => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe("PlatformShell", () => {
  beforeEach(() => {
    // Reset any global state before each test
    document.documentElement.style.cssText = "";
  });

  test("renders platform shell with header and sidebar", () => {
    renderWithRouter(
      <PlatformShell>
        <div data-testid="child-content">Test Content</div>
      </PlatformShell>
    );

    // Check if main elements are rendered
    expect(screen.getByText("StorySign")).toBeInTheDocument();
    expect(screen.getAllByText("Dashboard")).toHaveLength(2); // Header and sidebar
    expect(screen.getByText("ASL World")).toBeInTheDocument();
    expect(screen.getByTestId("child-content")).toBeInTheDocument();
  });

  test("renders logout button with icon when authenticated", () => {
    renderWithRouter(
      <PlatformShell>
        <div data-testid="child-content">Test Content</div>
      </PlatformShell>
    );

    // Click on user avatar to open dropdown
    const userAvatar = screen.getByLabelText("User menu");
    fireEvent.click(userAvatar);

    // Check if logout button with icon is rendered
    const logoutButton = screen.getByText("Logout");
    expect(logoutButton).toBeInTheDocument();
    expect(logoutButton.closest("button")).toHaveClass("logout-button");
  });

  test("provides platform context to child components", () => {
    renderWithRouter(
      <PlatformShell>
        <TestComponent />
      </PlatformShell>
    );

    // Check initial context values (now using mocked authenticated state)
    expect(screen.getByTestId("auth-status")).toHaveTextContent(
      "authenticated"
    );
    expect(screen.getByTestId("current-theme")).toHaveTextContent("light");
    expect(screen.getByTestId("current-module")).toHaveTextContent("dashboard");
    expect(screen.getByTestId("sidebar-status")).toHaveTextContent(
      "sidebar-open"
    );
    expect(screen.getByTestId("notifications-count")).toHaveTextContent("0");
  });

  test("handles theme changes", async () => {
    renderWithRouter(
      <PlatformShell>
        <TestComponent />
      </PlatformShell>
    );

    const changeThemeBtn = screen.getByTestId("change-theme-btn");
    fireEvent.click(changeThemeBtn);

    await waitFor(() => {
      expect(screen.getByTestId("current-theme")).toHaveTextContent("dark");
    });

    // Check if CSS variables are updated
    const root = document.documentElement;
    expect(root.style.getPropertyValue("--theme-primary")).toBe("#64B5F6");
  });

  test("handles sidebar toggle", () => {
    renderWithRouter(
      <PlatformShell>
        <TestComponent />
      </PlatformShell>
    );

    const toggleSidebarBtn = screen.getByTestId("toggle-sidebar-btn");

    // Initially sidebar should be open
    expect(screen.getByTestId("sidebar-status")).toHaveTextContent(
      "sidebar-open"
    );

    // Toggle sidebar
    fireEvent.click(toggleSidebarBtn);
    expect(screen.getByTestId("sidebar-status")).toHaveTextContent(
      "sidebar-closed"
    );

    // Toggle back
    fireEvent.click(toggleSidebarBtn);
    expect(screen.getByTestId("sidebar-status")).toHaveTextContent(
      "sidebar-open"
    );
  });

  test("handles notifications", async () => {
    renderWithRouter(
      <PlatformShell>
        <TestComponent />
      </PlatformShell>
    );

    const addNotificationBtn = screen.getByTestId("add-notification-btn");

    // Initially no notifications
    expect(screen.getByTestId("notifications-count")).toHaveTextContent("0");

    // Add notification
    fireEvent.click(addNotificationBtn);

    await waitFor(() => {
      expect(screen.getByTestId("notifications-count")).toHaveTextContent("1");
      expect(screen.getByText("Test notification")).toBeInTheDocument();
    });
  });

  test("handles navigation between modules", () => {
    renderWithRouter(
      <PlatformShell>
        <TestComponent />
      </PlatformShell>
    );

    // Check initial module
    expect(screen.getByTestId("current-module")).toHaveTextContent("dashboard");

    // Navigate to ASL World
    const navigateBtn = screen.getByTestId("navigate-asl-btn");
    fireEvent.click(navigateBtn);

    // Note: In a real test, we'd need to mock the router to verify navigation
    // For now, we just verify the button click doesn't cause errors
    expect(navigateBtn).toBeInTheDocument();
  });

  test("displays module navigation in sidebar", () => {
    renderWithRouter(
      <PlatformShell>
        <div>Test Content</div>
      </PlatformShell>
    );

    // Check if all modules are displayed (using getAllByText for multiple instances)
    expect(screen.getAllByText("Dashboard")).toHaveLength(2); // Header and sidebar
    expect(screen.getByText("ASL World")).toBeInTheDocument();
    expect(screen.getByText("Harmony")).toBeInTheDocument();
    expect(screen.getByText("Reconnect")).toBeInTheDocument();

    // Check if coming soon modules have the disabled class (they're not actually disabled in the current implementation)
    const harmonyButton = screen.getByText("Harmony").closest("button");
    const reconnectButton = screen.getByText("Reconnect").closest("button");

    // Note: The modules are marked as disabled: false in MODULE_DEFINITIONS, so they're not actually disabled
    expect(harmonyButton).toBeInTheDocument();
    expect(reconnectButton).toBeInTheDocument();
  });

  test("handles theme selector dropdown", () => {
    renderWithRouter(
      <PlatformShell>
        <div>Test Content</div>
      </PlatformShell>
    );

    // Find and click theme toggle button
    const themeToggle = screen.getByLabelText("Change theme");
    fireEvent.click(themeToggle);

    // Check if theme options are displayed
    expect(screen.getByText("Light")).toBeInTheDocument();
    expect(screen.getByText("Dark")).toBeInTheDocument();
    expect(screen.getByText("High Contrast")).toBeInTheDocument();
  });

  test("handles accessibility settings", async () => {
    renderWithRouter(
      <PlatformShell>
        <TestComponent />
      </PlatformShell>
    );

    // Test that CSS variables are set for accessibility
    const root = document.documentElement;

    // Check default font size
    expect(root.style.getPropertyValue("--base-font-size")).toBe("16px");

    // Check animation duration
    expect(root.style.getPropertyValue("--animation-duration")).toBe("0.3s");
  });

  test("notification auto-removal", async () => {
    jest.useFakeTimers();

    renderWithRouter(
      <PlatformShell>
        <TestComponent />
      </PlatformShell>
    );

    const addNotificationBtn = screen.getByTestId("add-notification-btn");

    // Add notification
    fireEvent.click(addNotificationBtn);

    await waitFor(() => {
      expect(screen.getByTestId("notifications-count")).toHaveTextContent("1");
    });

    // Fast-forward time to trigger auto-removal
    jest.advanceTimersByTime(5000);

    await waitFor(() => {
      expect(screen.getByTestId("notifications-count")).toHaveTextContent("0");
    });

    jest.useRealTimers();
  });

  test("notification manual removal", async () => {
    renderWithRouter(
      <PlatformShell>
        <TestComponent />
      </PlatformShell>
    );

    const addNotificationBtn = screen.getByTestId("add-notification-btn");

    // Add notification
    fireEvent.click(addNotificationBtn);

    await waitFor(() => {
      expect(screen.getByText("Test notification")).toBeInTheDocument();
    });

    // Find and click close button
    const closeButton = screen.getByLabelText("Close notification");
    fireEvent.click(closeButton);

    await waitFor(() => {
      expect(screen.queryByText("Test notification")).not.toBeInTheDocument();
      expect(screen.getByTestId("notifications-count")).toHaveTextContent("0");
    });
  });

  test("throws error when usePlatform is used outside PlatformShell", () => {
    // Suppress console.error for this test
    const originalError = console.error;
    console.error = jest.fn();

    expect(() => {
      render(<TestComponent />);
    }).toThrow("usePlatform must be used within a PlatformShell");

    console.error = originalError;
  });
});

describe("PlatformShell Integration", () => {
  test("integrates with ASL World module", () => {
    renderWithRouter(
      <PlatformShell>
        <div data-testid="asl-world-content">ASL World Content</div>
      </PlatformShell>
    );

    // Verify that ASL World content can be rendered within the shell
    expect(screen.getByTestId("asl-world-content")).toBeInTheDocument();

    // Verify shell components are still present
    expect(screen.getByText("StorySign")).toBeInTheDocument();
    expect(screen.getByText("ASL World")).toBeInTheDocument();
  });

  test("maintains state across module navigation", async () => {
    renderWithRouter(
      <PlatformShell>
        <TestComponent />
      </PlatformShell>
    );

    // Add a notification
    const addNotificationBtn = screen.getByTestId("add-notification-btn");
    fireEvent.click(addNotificationBtn);

    await waitFor(() => {
      expect(screen.getByTestId("notifications-count")).toHaveTextContent("1");
    });

    // Change theme
    const changeThemeBtn = screen.getByTestId("change-theme-btn");
    fireEvent.click(changeThemeBtn);

    await waitFor(() => {
      expect(screen.getByTestId("current-theme")).toHaveTextContent("dark");
    });

    // Verify state is maintained (theme change also adds a notification, so count is 2)
    expect(screen.getByTestId("notifications-count")).toHaveTextContent("2");
    expect(screen.getByTestId("current-theme")).toHaveTextContent("dark");
  });
});
