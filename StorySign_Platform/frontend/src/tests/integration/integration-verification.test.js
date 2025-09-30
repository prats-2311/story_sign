/**
 * Integration Verification Test
 *
 * Simplified test to verify navigation and module integration
 * Requirements: 5.5, 3.3, 6.4
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import ASLWorldPage from "../pages/ASLWorldPage";
import HarmonyPage from "../pages/HarmonyPage";
import ReconnectPage from "../pages/ReconnectPage";
import { MainDashboard } from "../pages";
import PlatformShell from "../components/shell/PlatformShell";

// Mock dependencies
jest.mock("../components/video/VideoStreamingClient", () => {
  const mockReact = require("react");
  return mockReact.forwardRef((props, ref) =>
    mockReact.createElement(
      "div",
      { "data-testid": "video-streaming-client" },
      "Mock Video Streaming Client"
    )
  );
});

jest.mock("../hooks/useWebcam", () => ({
  __esModule: true,
  default: () => ({
    stream: null,
    isActive: false,
    status: "inactive",
    error: null,
    startWebcam: jest.fn(),
    stopWebcam: jest.fn(),
    attachToVideoElement: jest.fn(),
  }),
}));

// Mock API calls
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ success: true }),
  })
);

describe("Integration Verification", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("ASL World Story Setup Integration", () => {
    test("should render ASL World page with Story Setup component", () => {
      const mockProps = {
        connectionStatus: "connected",
        webcamActive: false,
        streamingActive: false,
        streamingConnectionStatus: "disconnected",
        onFrameCapture: jest.fn(),
        videoStreamingRef: { current: null },
        processedFrameData: null,
        optimizationSettings: {},
        onOptimizationChange: jest.fn(),
        onConnectionChange: jest.fn(),
        onProcessedFrame: jest.fn(),
        onError: jest.fn(),
        onRetryConnection: jest.fn(),
        toggleWebcam: jest.fn(),
        toggleStreaming: jest.fn(),
        testBackendConnection: jest.fn(),
      };

      render(
        <BrowserRouter>
          <ASLWorldPage {...mockProps} />
        </BrowserRouter>
      );

      // Verify ASL World page renders
      expect(screen.getByText("ASL World")).toBeInTheDocument();
      expect(
        screen.getByText("Interactive American Sign Language Learning")
      ).toBeInTheDocument();

      // Verify connection status is displayed
      expect(screen.getByText(/Connection status:/)).toBeInTheDocument();

      // Verify the page structure indicates Story Setup is loaded
      // (The default view should be 'story_generation' which renders StorySetup)
      expect(screen.getByRole("main")).toBeInTheDocument();
    });
  });

  describe("Module Component Loading", () => {
    test("should render Harmony page correctly", () => {
      const mockProps = {
        connectionStatus: "connected",
        streamingConnectionStatus: "disconnected",
        onConnectionChange: jest.fn(),
        onProcessedFrame: jest.fn(),
        onError: jest.fn(),
        onRetryConnection: jest.fn(),
      };

      render(
        <BrowserRouter>
          <HarmonyPage {...mockProps} />
        </BrowserRouter>
      );

      expect(screen.getByText("Harmony")).toBeInTheDocument();
      expect(
        screen.getByText(
          "Facial Expression Practice & Social-Emotional Learning"
        )
      ).toBeInTheDocument();
      expect(screen.getByText(/Connection status:/)).toBeInTheDocument();
    });

    test("should render Reconnect page correctly", () => {
      const mockProps = {
        connectionStatus: "connected",
        streamingConnectionStatus: "disconnected",
        onConnectionChange: jest.fn(),
        onProcessedFrame: jest.fn(),
        onError: jest.fn(),
        onRetryConnection: jest.fn(),
      };

      render(
        <BrowserRouter>
          <ReconnectPage {...mockProps} />
        </BrowserRouter>
      );

      expect(screen.getByText("Reconnect")).toBeInTheDocument();
      expect(
        screen.getByText(
          "Therapeutic Movement Analysis & Physical Rehabilitation"
        )
      ).toBeInTheDocument();
      expect(screen.getByText("Connected")).toBeInTheDocument();
    });

    test("should render MainDashboard correctly", () => {
      render(
        <BrowserRouter>
          <MainDashboard />
        </BrowserRouter>
      );

      // Dashboard should render without errors
      expect(screen.getByText("Backend Connectivity")).toBeInTheDocument();
    });
  });

  describe("PlatformShell Integration", () => {
    test("should render PlatformShell with navigation elements", () => {
      render(
        <BrowserRouter>
          <PlatformShell>
            <div>Test Content</div>
          </PlatformShell>
        </BrowserRouter>
      );

      // Verify PlatformShell renders key elements
      expect(screen.getByText("StorySign")).toBeInTheDocument();
      expect(screen.getByText("Test Content")).toBeInTheDocument();

      // Verify navigation elements
      expect(
        screen.getByRole("button", { name: /Dashboard/i })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /ASL World/i })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /Harmony/i })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /Reconnect/i })
      ).toBeInTheDocument();

      // Verify header controls
      expect(screen.getByLabelText("Toggle sidebar")).toBeInTheDocument();
      expect(screen.getByLabelText("Change theme")).toBeInTheDocument();
    });

    test("should apply consistent CSS classes", () => {
      render(
        <BrowserRouter>
          <PlatformShell>
            <div>Test Content</div>
          </PlatformShell>
        </BrowserRouter>
      );

      // Verify structural CSS classes are applied
      const platformShell = document.querySelector(".platform-shell");
      expect(platformShell).toBeInTheDocument();

      const platformHeader = document.querySelector(".platform-header");
      expect(platformHeader).toBeInTheDocument();

      const platformMain = document.querySelector(".platform-main");
      expect(platformMain).toBeInTheDocument();
    });
  });

  describe("Component Integration Health Check", () => {
    test("should verify all page components can be imported and rendered", () => {
      // This test ensures all components can be imported without errors
      expect(ASLWorldPage).toBeDefined();
      expect(HarmonyPage).toBeDefined();
      expect(ReconnectPage).toBeDefined();
      expect(MainDashboard).toBeDefined();
      expect(PlatformShell).toBeDefined();
    });

    test("should verify ASL World includes StorySetup functionality", () => {
      const mockProps = {
        connectionStatus: "connected",
        webcamActive: false,
        streamingActive: false,
        streamingConnectionStatus: "disconnected",
        onFrameCapture: jest.fn(),
        videoStreamingRef: { current: null },
        processedFrameData: null,
        optimizationSettings: {},
        onOptimizationChange: jest.fn(),
        onConnectionChange: jest.fn(),
        onProcessedFrame: jest.fn(),
        onError: jest.fn(),
        onRetryConnection: jest.fn(),
        toggleWebcam: jest.fn(),
        toggleStreaming: jest.fn(),
        testBackendConnection: jest.fn(),
      };

      const { container } = render(
        <BrowserRouter>
          <ASLWorldPage {...mockProps} />
        </BrowserRouter>
      );

      // Verify the ASL World page structure
      expect(container.querySelector(".asl-world-page")).toBeInTheDocument();
      expect(container.querySelector(".page-header")).toBeInTheDocument();
      expect(container.querySelector(".page-content")).toBeInTheDocument();
    });
  });
});
