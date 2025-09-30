import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import ASLWorldPage from "./ASLWorldPage";

// Mock fetch for API calls
global.fetch = jest.fn();

// Mock MediaDevices API
const mockGetUserMedia = jest.fn();
Object.defineProperty(navigator, "mediaDevices", {
  writable: true,
  value: {
    getUserMedia: mockGetUserMedia,
  },
});

describe("ASLWorldPage Simple Tests", () => {
  const defaultProps = {
    connectionStatus: "connected",
    webcamActive: false,
    streamingActive: false,
    onFrameCapture: jest.fn(),
    videoStreamingRef: { current: null },
    processedFrameData: null,
    streamingConnectionStatus: "disconnected",
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

  beforeEach(() => {
    jest.clearAllMocks();
    fetch.mockClear();
    mockGetUserMedia.mockResolvedValue({
      getTracks: () => [{ stop: jest.fn() }],
    });
  });

  test("renders initial story generation view", () => {
    render(<ASLWorldPage {...defaultProps} />);

    expect(screen.getByText("Create Your ASL Story")).toBeInTheDocument();
    expect(screen.getByText("Scan Object")).toBeInTheDocument();
    expect(screen.getByText("Choose a Word")).toBeInTheDocument();
    expect(screen.getByText("Custom Topic")).toBeInTheDocument();
  });

  test("shows connection status", () => {
    render(<ASLWorldPage {...defaultProps} />);

    expect(screen.getByText("Connected")).toBeInTheDocument();
  });

  test("can switch between generation modes", async () => {
    const user = userEvent.setup();
    render(<ASLWorldPage {...defaultProps} />);

    // Initially shows scan mode
    expect(screen.getByText("Scan an Object")).toBeInTheDocument();

    // Switch to word mode
    const wordTabButton = screen.getByText("Choose a Word");
    await user.click(wordTabButton);

    await waitFor(() => {
      expect(
        screen.getByText("Choose a Word to Start Your Story")
      ).toBeInTheDocument();
      expect(screen.getByText("Cat")).toBeInTheDocument();
    });

    // Switch to custom mode
    const customTabButton = screen.getByText("Custom Topic");
    await user.click(customTabButton);

    await waitFor(() => {
      expect(
        screen.getByText("Enter a Topic for Your Story")
      ).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/friendly robot/)).toBeInTheDocument();
    });
  });

  test("handles story generation error", async () => {
    const user = userEvent.setup();

    // Mock failed story generation
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
      json: async () => ({
        success: false,
        message: "AI service temporarily unavailable",
      }),
    });

    render(<ASLWorldPage {...defaultProps} />);

    // Switch to word mode and click Cat
    const wordTabButton = screen.getByText("Choose a Word");
    await user.click(wordTabButton);

    await waitFor(() => {
      expect(screen.getByText("Cat")).toBeInTheDocument();
    });

    const catWordButton = screen.getByText("Cat");
    await user.click(catWordButton);

    // Should show error message
    await waitFor(() => {
      expect(screen.getByText(/Story Generation Error/)).toBeInTheDocument();
      expect(
        screen.getByText(/AI service temporarily unavailable/)
      ).toBeInTheDocument();
    });
  });

  test("shows disconnected status when backend is down", () => {
    render(<ASLWorldPage {...defaultProps} connectionStatus="disconnected" />);

    expect(screen.getByText("Disconnected")).toBeInTheDocument();
    expect(screen.getByText(/Backend connection required/)).toBeInTheDocument();
  });

  test("custom prompt input works correctly", async () => {
    const user = userEvent.setup();
    render(<ASLWorldPage {...defaultProps} />);

    // Switch to custom mode
    const customTabButton = screen.getByText("Custom Topic");
    await user.click(customTabButton);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/friendly robot/)).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText(/friendly robot/);
    await user.type(input, "A magical cat");

    expect(input).toHaveValue("A magical cat");

    // Generate button should be enabled now
    const generateButton = screen.getByText("Generate Stories");
    expect(generateButton).not.toBeDisabled();
  });
});
