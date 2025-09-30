import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import "@testing-library/jest-dom";
import PlatformShell, { usePlatform } from "./PlatformShell";

// Simple test component that uses platform context
const PlatformTestComponent = () => {
  const {
    addNotification,
    changeTheme,
    currentTheme,
    toggleSidebar,
    sidebarOpen,
    notificationTypes,
  } = usePlatform();

  return (
    <div data-testid="platform-test">
      <div data-testid="theme-display">{currentTheme}</div>
      <div data-testid="sidebar-display">{sidebarOpen ? "open" : "closed"}</div>
      <button
        data-testid="test-notification"
        onClick={() =>
          addNotification("Test message", notificationTypes.SUCCESS)
        }
      >
        Add Success Notification
      </button>
      <button
        data-testid="test-theme-change"
        onClick={() => changeTheme("dark")}
      >
        Change to Dark Theme
      </button>
      <button data-testid="test-sidebar-toggle" onClick={toggleSidebar}>
        Toggle Sidebar
      </button>
    </div>
  );
};

const renderWithRouter = (component) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe("PlatformShell Integration Tests", () => {
  test("renders basic shell structure", () => {
    renderWithRouter(
      <PlatformShell>
        <div data-testid="test-content">Test Content</div>
      </PlatformShell>
    );

    // Check if main shell elements are present
    expect(screen.getByText("StorySign")).toBeInTheDocument();
    expect(screen.getByTestId("test-content")).toBeInTheDocument();

    // Check if navigation modules are present
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("ASL World")).toBeInTheDocument();
  });

  test("provides working platform context", () => {
    renderWithRouter(
      <PlatformShell>
        <PlatformTestComponent />
      </PlatformShell>
    );

    // Check initial state
    expect(screen.getByTestId("theme-display")).toHaveTextContent("light");
    expect(screen.getByTestId("sidebar-display")).toHaveTextContent("open");

    // Test theme change
    fireEvent.click(screen.getByTestId("test-theme-change"));
    expect(screen.getByTestId("theme-display")).toHaveTextContent("dark");

    // Test sidebar toggle
    fireEvent.click(screen.getByTestId("test-sidebar-toggle"));
    expect(screen.getByTestId("sidebar-display")).toHaveTextContent("closed");

    // Test notification
    fireEvent.click(screen.getByTestId("test-notification"));
    expect(screen.getByText("Test message")).toBeInTheDocument();
  });

  test("handles navigation modules correctly", () => {
    renderWithRouter(
      <PlatformShell>
        <div>Content</div>
      </PlatformShell>
    );

    // Check that ASL World module is enabled
    const aslWorldButton = screen.getByText("ASL World").closest("button");
    expect(aslWorldButton).not.toBeDisabled();

    // Check that future modules are disabled
    const harmonyButton = screen.getByText("Harmony").closest("button");
    const reconnectButton = screen.getByText("Reconnect").closest("button");

    expect(harmonyButton).toBeDisabled();
    expect(reconnectButton).toBeDisabled();

    // Check for "Soon" badges
    expect(screen.getAllByText("Soon")).toHaveLength(2);
  });

  test("theme selector works", () => {
    renderWithRouter(
      <PlatformShell>
        <PlatformTestComponent />
      </PlatformShell>
    );

    // Find and click theme toggle
    const themeToggle = screen.getByLabelText("Change theme");
    fireEvent.click(themeToggle);

    // Check if theme options appear
    expect(screen.getByText("Light")).toBeInTheDocument();
    expect(screen.getByText("Dark")).toBeInTheDocument();
    expect(screen.getByText("High Contrast")).toBeInTheDocument();

    // Click dark theme
    fireEvent.click(screen.getByText("Dark"));
    expect(screen.getByTestId("theme-display")).toHaveTextContent("dark");
  });

  test("notification system works", () => {
    renderWithRouter(
      <PlatformShell>
        <PlatformTestComponent />
      </PlatformShell>
    );

    // Add notification
    fireEvent.click(screen.getByTestId("test-notification"));

    // Check notification appears
    expect(screen.getByText("Test message")).toBeInTheDocument();

    // Check notification can be closed
    const closeButton = screen.getByLabelText("Close notification");
    fireEvent.click(closeButton);

    expect(screen.queryByText("Test message")).not.toBeInTheDocument();
  });

  test("sidebar toggle functionality", () => {
    renderWithRouter(
      <PlatformShell>
        <PlatformTestComponent />
      </PlatformShell>
    );

    // Check initial sidebar state
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByTestId("sidebar-display")).toHaveTextContent("open");

    // Toggle sidebar closed
    fireEvent.click(screen.getByTestId("test-sidebar-toggle"));
    expect(screen.getByTestId("sidebar-display")).toHaveTextContent("closed");

    // Toggle sidebar open again
    fireEvent.click(screen.getByTestId("test-sidebar-toggle"));
    expect(screen.getByTestId("sidebar-display")).toHaveTextContent("open");
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });

  test("integrates with ASL World content", () => {
    renderWithRouter(
      <PlatformShell>
        <div data-testid="asl-world-mock">
          <h2>ASL World Module</h2>
          <div>Story generation interface</div>
          <div>Video processing area</div>
        </div>
      </PlatformShell>
    );

    // Verify ASL World content is rendered within shell
    expect(screen.getByTestId("asl-world-mock")).toBeInTheDocument();
    expect(screen.getByText("ASL World Module")).toBeInTheDocument();
    expect(screen.getByText("Story generation interface")).toBeInTheDocument();
    expect(screen.getByText("Video processing area")).toBeInTheDocument();

    // Verify shell navigation is still present
    expect(screen.getByText("StorySign")).toBeInTheDocument();
    expect(screen.getByText("ASL World")).toBeInTheDocument();
  });
});

describe("PlatformShell Error Handling", () => {
  test("handles context usage outside provider gracefully", () => {
    // Mock console.error to prevent test output pollution
    const originalError = console.error;
    console.error = jest.fn();

    // Component that tries to use context outside provider
    const BadComponent = () => {
      try {
        usePlatform();
        return <div>Should not render</div>;
      } catch (error) {
        return <div data-testid="error-caught">{error.message}</div>;
      }
    };

    render(<BadComponent />);

    expect(screen.getByTestId("error-caught")).toHaveTextContent(
      "usePlatform must be used within a PlatformShell"
    );

    console.error = originalError;
  });
});
