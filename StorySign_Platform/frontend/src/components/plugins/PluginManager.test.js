import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import PluginManager from "./PluginManager";
import PlatformShell from "../shell/PlatformShell";

// Mock fetch for API calls
global.fetch = jest.fn();

const MockPlatformProvider = ({ children }) => (
  <BrowserRouter>
    <PlatformShell>{children}</PlatformShell>
  </BrowserRouter>
);

describe("PluginManager", () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test("renders plugin manager with tabs", async () => {
    // Mock successful API response
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: "success",
        plugins: [],
      }),
    });

    render(
      <MockPlatformProvider>
        <PluginManager />
      </MockPlatformProvider>
    );

    expect(screen.getByText("Plugin Manager")).toBeInTheDocument();
    expect(screen.getByText(/Installed \(0\)/)).toBeInTheDocument();
    expect(screen.getByText(/Plugin Store \(0\)/)).toBeInTheDocument();
    expect(screen.getByText("Security Monitor")).toBeInTheDocument();
  });

  test("displays installed plugins correctly", async () => {
    const mockPlugins = [
      {
        id: "test-plugin",
        name: "Test Plugin",
        version: "1.0.0",
        description: "A test plugin",
        status: "active",
        author: "Test Author",
        installed_at: "2024-01-15T10:30:00Z",
        permissions: ["read:user_data"],
        error_message: null,
      },
    ];

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: "success",
        plugins: mockPlugins,
      }),
    });

    render(
      <MockPlatformProvider>
        <PluginManager />
      </MockPlatformProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("Test Plugin")).toBeInTheDocument();
      expect(screen.getByText("v1.0.0")).toBeInTheDocument();
      expect(screen.getByText("A test plugin")).toBeInTheDocument();
      expect(screen.getByText("active")).toBeInTheDocument();
    });
  });

  test("switches between tabs correctly", async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: "success",
        plugins: [],
      }),
    });

    render(
      <MockPlatformProvider>
        <PluginManager />
      </MockPlatformProvider>
    );

    // Click on Plugin Store tab
    fireEvent.click(screen.getByText(/Plugin Store/));

    await waitFor(() => {
      expect(screen.getByText(/Plugin Store/)).toHaveClass("active");
    });

    // Click on Security Monitor tab
    fireEvent.click(screen.getByText("Security Monitor"));

    await waitFor(() => {
      expect(screen.getByText("Security Monitor")).toHaveClass("active");
    });
  });

  test("opens install plugin modal", async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: "success",
        plugins: [],
      }),
    });

    render(
      <MockPlatformProvider>
        <PluginManager />
      </MockPlatformProvider>
    );

    fireEvent.click(screen.getByText("Install Plugin"));

    await waitFor(() => {
      expect(screen.getByText("Install Plugin")).toBeInTheDocument();
      expect(screen.getByText("Installation Method")).toBeInTheDocument();
    });
  });

  test("filters plugins by search query", async () => {
    const mockPlugins = [
      {
        id: "plugin1",
        name: "Gesture Enhancer",
        version: "1.0.0",
        description: "Enhances gesture recognition",
        status: "active",
        author: "Test Author",
        installed_at: "2024-01-15T10:30:00Z",
        permissions: ["read:user_data"],
        error_message: null,
      },
      {
        id: "plugin2",
        name: "Progress Tracker",
        version: "2.0.0",
        description: "Tracks learning progress",
        status: "active",
        author: "Test Author",
        installed_at: "2024-01-15T10:30:00Z",
        permissions: ["read:user_data"],
        error_message: null,
      },
    ];

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: "success",
        plugins: mockPlugins,
      }),
    });

    render(
      <MockPlatformProvider>
        <PluginManager />
      </MockPlatformProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("Gesture Enhancer")).toBeInTheDocument();
      expect(screen.getByText("Progress Tracker")).toBeInTheDocument();
    });

    // Search for "gesture"
    const searchInput = screen.getByPlaceholderText("Search plugins...");
    fireEvent.change(searchInput, { target: { value: "gesture" } });

    await waitFor(() => {
      expect(screen.getByText("Gesture Enhancer")).toBeInTheDocument();
      expect(screen.queryByText("Progress Tracker")).not.toBeInTheDocument();
    });
  });

  test("filters plugins by status", async () => {
    const mockPlugins = [
      {
        id: "plugin1",
        name: "Active Plugin",
        version: "1.0.0",
        description: "An active plugin",
        status: "active",
        author: "Test Author",
        installed_at: "2024-01-15T10:30:00Z",
        permissions: ["read:user_data"],
        error_message: null,
      },
      {
        id: "plugin2",
        name: "Disabled Plugin",
        version: "2.0.0",
        description: "A disabled plugin",
        status: "disabled",
        author: "Test Author",
        installed_at: "2024-01-15T10:30:00Z",
        permissions: ["read:user_data"],
        error_message: null,
      },
    ];

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: "success",
        plugins: mockPlugins,
      }),
    });

    render(
      <MockPlatformProvider>
        <PluginManager />
      </MockPlatformProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("Active Plugin")).toBeInTheDocument();
      expect(screen.getByText("Disabled Plugin")).toBeInTheDocument();
    });

    // Filter by active status
    const statusFilter = screen.getByDisplayValue("All Status");
    fireEvent.change(statusFilter, { target: { value: "active" } });

    await waitFor(() => {
      expect(screen.getByText("Active Plugin")).toBeInTheDocument();
      expect(screen.queryByText("Disabled Plugin")).not.toBeInTheDocument();
    });
  });

  test("handles plugin toggle action", async () => {
    const mockPlugin = {
      id: "test-plugin",
      name: "Test Plugin",
      version: "1.0.0",
      description: "A test plugin",
      status: "active",
      author: "Test Author",
      installed_at: "2024-01-15T10:30:00Z",
      permissions: ["read:user_data"],
      error_message: null,
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: "success",
        plugins: [mockPlugin],
      }),
    });

    render(
      <MockPlatformProvider>
        <PluginManager />
      </MockPlatformProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("Test Plugin")).toBeInTheDocument();
    });

    // Click disable button
    const disableButton = screen.getByText("Disable");
    fireEvent.click(disableButton);

    await waitFor(() => {
      expect(screen.getByText("Enable")).toBeInTheDocument();
    });
  });

  test("displays security information", async () => {
    const mockPlugin = {
      id: "test-plugin",
      name: "Test Plugin",
      version: "1.0.0",
      description: "A test plugin",
      status: "active",
      author: "Test Author",
      installed_at: "2024-01-15T10:30:00Z",
      permissions: ["read:user_data"],
      error_message: null,
    };

    const mockSecurityReport = {
      "test-plugin": {
        risk_level: "low",
        violations: [],
        resource_usage: { cpu: 15, memory: 45, network: 0 },
        last_scan: "2024-01-15T12:00:00Z",
      },
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: "success",
        plugins: [mockPlugin],
      }),
    });

    render(
      <MockPlatformProvider>
        <PluginManager />
      </MockPlatformProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("Test Plugin")).toBeInTheDocument();
      expect(screen.getByText("low")).toBeInTheDocument();
      expect(screen.getByText("15%")).toBeInTheDocument();
    });
  });

  test("handles plugin installation flow", async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: "success",
        plugins: [],
      }),
    });

    render(
      <MockPlatformProvider>
        <PluginManager />
      </MockPlatformProvider>
    );

    // Open install modal
    fireEvent.click(screen.getByText("Install Plugin"));

    await waitFor(() => {
      expect(screen.getByText("Installation Method")).toBeInTheDocument();
    });

    // Select manifest method
    const manifestRadio = screen.getByLabelText(/Paste Manifest/);
    fireEvent.click(manifestRadio);

    // Enter manifest data
    const manifestTextarea = screen.getByPlaceholderText(
      "Paste plugin manifest JSON here..."
    );
    const mockManifest = JSON.stringify({
      id: "test-plugin",
      name: "Test Plugin",
      version: "1.0.0",
      description: "A test plugin",
      author: "Test Author",
      permissions: ["read:user_data"],
    });

    fireEvent.change(manifestTextarea, { target: { value: mockManifest } });

    // Validate plugin
    const validateButton = screen.getByText("Validate Plugin");
    fireEvent.click(validateButton);

    // Mock validation response
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        validation: {
          valid: true,
          issues: [],
          security_score: 85,
          risk_level: "low",
        },
      }),
    });

    await waitFor(() => {
      expect(screen.getByText("✅ Validation Results")).toBeInTheDocument();
    });
  });

  test("displays error states correctly", async () => {
    const mockPlugin = {
      id: "broken-plugin",
      name: "Broken Plugin",
      version: "1.0.0",
      description: "A broken plugin",
      status: "error",
      author: "Test Author",
      installed_at: "2024-01-15T10:30:00Z",
      permissions: ["read:user_data"],
      error_message: "Failed to initialize: Missing dependency",
    };

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: "success",
        plugins: [mockPlugin],
      }),
    });

    render(
      <MockPlatformProvider>
        <PluginManager />
      </MockPlatformProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("Broken Plugin")).toBeInTheDocument();
      expect(screen.getByText("error")).toBeInTheDocument();
      expect(
        screen.getByText("Failed to initialize: Missing dependency")
      ).toBeInTheDocument();
    });

    // Enable button should be disabled for error status
    const enableButton = screen.getByText("Enable");
    expect(enableButton).toBeDisabled();
  });
});

describe("Plugin Store Integration", () => {
  test("displays available plugins in store", async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: "success",
        plugins: [],
      }),
    });

    render(
      <MockPlatformProvider>
        <PluginManager />
      </MockPlatformProvider>
    );

    // Switch to store tab
    fireEvent.click(screen.getByText(/Plugin Store/));

    await waitFor(() => {
      expect(screen.getByText("Accessibility Helper")).toBeInTheDocument();
      expect(screen.getByText("Custom Themes")).toBeInTheDocument();
      expect(screen.getByText("AI Tutor Assistant")).toBeInTheDocument();
    });
  });

  test("handles plugin installation from store", async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: "success",
        plugins: [],
      }),
    });

    // Mock installation API
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: "success",
      }),
    });

    render(
      <MockPlatformProvider>
        <PluginManager />
      </MockPlatformProvider>
    );

    // Switch to store tab
    fireEvent.click(screen.getByText(/Plugin Store/));

    await waitFor(() => {
      expect(screen.getByText("Accessibility Helper")).toBeInTheDocument();
    });

    // Find and click install button for accessibility helper
    const installButtons = screen.getAllByText("Install");
    fireEvent.click(installButtons[0]);

    // Should show installation progress
    await waitFor(() => {
      expect(screen.getByText(/Installing.../)).toBeInTheDocument();
    });
  });
});

describe("Security Monitor Integration", () => {
  test("displays security overview", async () => {
    const mockPlugins = [
      {
        id: "plugin1",
        name: "Plugin 1",
        version: "1.0.0",
        description: "Test plugin 1",
        status: "active",
        author: "Test Author",
        installed_at: "2024-01-15T10:30:00Z",
        permissions: ["read:user_data"],
        error_message: null,
      },
    ];

    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: "success",
        plugins: mockPlugins,
      }),
    });

    render(
      <MockPlatformProvider>
        <PluginManager />
      </MockPlatformProvider>
    );

    // Switch to security monitor tab
    fireEvent.click(screen.getByText("Security Monitor"));

    await waitFor(() => {
      expect(screen.getByText("Security Overview")).toBeInTheDocument();
      expect(screen.getByText("Total Plugins")).toBeInTheDocument();
      expect(screen.getByText("Active Plugins")).toBeInTheDocument();
      expect(screen.getByText("Security Issues")).toBeInTheDocument();
    });
  });
});
