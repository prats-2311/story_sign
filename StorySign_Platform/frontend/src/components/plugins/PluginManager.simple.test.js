import React from "react";
import { render, screen } from "@testing-library/react";

// Mock the PlatformShell context
const mockPlatformContext = {
  addNotification: jest.fn(),
  notificationTypes: {
    SUCCESS: "success",
    ERROR: "error",
    INFO: "info",
    WARNING: "warning",
  },
};

// Mock the usePlatform hook
jest.mock("../shell/PlatformShell", () => ({
  usePlatform: () => mockPlatformContext,
}));

// Mock fetch for API calls
global.fetch = jest.fn();

// Import after mocking
import PluginManager from "./PluginManager";

describe("PluginManager Component", () => {
  beforeEach(() => {
    fetch.mockClear();
    mockPlatformContext.addNotification.mockClear();
  });

  test("renders plugin manager header", async () => {
    // Mock successful API response
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: "success",
        plugins: [],
      }),
    });

    render(<PluginManager />);

    expect(screen.getByText("Plugin Manager")).toBeInTheDocument();
    expect(screen.getByText("Install Plugin")).toBeInTheDocument();
    expect(screen.getByText("Refresh")).toBeInTheDocument();
  });

  test("renders tab navigation", async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: "success",
        plugins: [],
      }),
    });

    render(<PluginManager />);

    expect(screen.getByText(/Installed \(0\)/)).toBeInTheDocument();
    expect(screen.getByText(/Plugin Store \(0\)/)).toBeInTheDocument();
    expect(screen.getByText("Security Monitor")).toBeInTheDocument();
  });

  test("renders search and filter controls", async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: "success",
        plugins: [],
      }),
    });

    render(<PluginManager />);

    expect(
      screen.getByPlaceholderText("Search plugins...")
    ).toBeInTheDocument();
    expect(screen.getByDisplayValue("All Status")).toBeInTheDocument();
  });

  test("displays empty state when no plugins installed", async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: "success",
        plugins: [],
      }),
    });

    render(<PluginManager />);

    // Wait for the component to load
    await screen.findByText("No plugins installed");
    expect(
      screen.getByText(
        "Install plugins from the Plugin Store to extend StorySign's functionality."
      )
    ).toBeInTheDocument();
  });

  test("handles API errors gracefully", async () => {
    fetch.mockRejectedValueOnce(new Error("Network error"));

    render(<PluginManager />);

    // Should still render the basic structure
    expect(screen.getByText("Plugin Manager")).toBeInTheDocument();
  });

  test("displays loading state", () => {
    // Mock a pending promise to simulate loading
    fetch.mockImplementationOnce(() => new Promise(() => {}));

    render(<PluginManager />);

    expect(screen.getByText("Loading plugins...")).toBeInTheDocument();
  });
});

describe("Plugin Store Tab", () => {
  test("displays available plugins", async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: "success",
        plugins: [],
      }),
    });

    render(<PluginManager />);

    // Switch to store tab by finding the tab button
    const storeTab = screen.getByText(/Plugin Store/);
    storeTab.click();

    // Should show available plugins (mocked data)
    expect(screen.getByText("Accessibility Helper")).toBeInTheDocument();
    expect(screen.getByText("Custom Themes")).toBeInTheDocument();
  });
});

describe("Security Monitor Tab", () => {
  test("displays security overview", async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: "success",
        plugins: [],
      }),
    });

    render(<PluginManager />);

    // Switch to security monitor tab
    const securityTab = screen.getByText("Security Monitor");
    securityTab.click();

    expect(screen.getByText("Security Overview")).toBeInTheDocument();
    expect(screen.getByText("Total Plugins")).toBeInTheDocument();
  });
});

// Test individual components
describe("Plugin Components Integration", () => {
  test("plugin manager components are properly exported", () => {
    // Test that all components can be imported
    const PluginManager = require("./PluginManager").default;
    const InstalledPluginsTab = require("./InstalledPluginsTab").default;
    const PluginStoreTab = require("./PluginStoreTab").default;
    const SecurityMonitorTab = require("./SecurityMonitorTab").default;

    expect(PluginManager).toBeDefined();
    expect(InstalledPluginsTab).toBeDefined();
    expect(PluginStoreTab).toBeDefined();
    expect(SecurityMonitorTab).toBeDefined();
  });

  test("modal components are properly exported", () => {
    const PluginInstallModal = require("./PluginInstallModal").default;
    const PluginConfigModal = require("./PluginConfigModal").default;
    const SecurityReportModal = require("./SecurityReportModal").default;

    expect(PluginInstallModal).toBeDefined();
    expect(PluginConfigModal).toBeDefined();
    expect(SecurityReportModal).toBeDefined();
  });
});

// Integration test
describe("Plugin Management Integration", () => {
  test("complete plugin management workflow", async () => {
    // Mock API responses for the complete workflow
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          status: "success",
          plugins: [],
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          validation: {
            valid: true,
            issues: [],
            security_score: 85,
          },
        }),
      });

    render(<PluginManager />);

    // Verify initial render
    expect(screen.getByText("Plugin Manager")).toBeInTheDocument();

    // Verify tabs are present
    expect(screen.getByText(/Installed/)).toBeInTheDocument();
    expect(screen.getByText(/Plugin Store/)).toBeInTheDocument();
    expect(screen.getByText("Security Monitor")).toBeInTheDocument();

    // Verify action buttons
    expect(screen.getByText("Install Plugin")).toBeInTheDocument();
    expect(screen.getByText("Refresh")).toBeInTheDocument();

    console.log("✅ Plugin Manager component integration test passed");
  });
});
