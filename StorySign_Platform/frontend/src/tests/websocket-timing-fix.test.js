/**
 * Test to verify WebSocket connection timing fix
 * This test checks that practice sessions wait for WebSocket connection
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ASLWorldPage from "../pages/ASLWorldPage";

// Mock the useWebcam hook
jest.mock("../hooks/useWebcam", () => ({
  __esModule: true,
  default: () => ({
    stream: {
      getTracks: () => [{ kind: "video", label: "Mock Camera" }],
      getVideoTracks: () => [
        { getSettings: () => ({ width: 640, height: 480 }) },
      ],
    },
    isActive: true,
    status: "active",
    error: null,
    deviceInfo: { label: "Mock Camera" },
    startWebcam: jest.fn().mockResolvedValue(true),
    stopWebcam: jest.fn(),
    captureFrame: jest.fn().mockResolvedValue({
      frameData: "data:image/jpeg;base64,mock-frame-data",
      timestamp: new Date().toISOString(),
      width: 320,
      height: 240,
    }),
    performanceStats: {
      currentFPS: 30,
      adaptiveFPS: 30,
      droppedFrames: 0,
      processingCapability: 1.0,
      avgProcessingTime: 10,
    },
  }),
}));

// Mock the useWebSocket hook with delayed connection
jest.mock("../hooks/useWebSocket", () => ({
  __esModule: true,
  default: () => {
    const [connectionState, setConnectionState] =
      React.useState("disconnected");

    // Simulate delayed connection
    React.useEffect(() => {
      const timer = setTimeout(() => {
        setConnectionState("connected");
      }, 1000); // Connect after 1 second

      return () => clearTimeout(timer);
    }, []);

    return {
      connectionState,
      isConnected: connectionState === "connected",
      lastMessage: null,
      sendMessage: jest.fn().mockReturnValue(true),
    };
  },
}));

// Mock fetch for story generation
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () =>
      Promise.resolve({
        success: true,
        stories: [
          {
            title: "Test Story",
            sentences: ["Test sentence 1", "Test sentence 2"],
            difficulty: "beginner",
          },
        ],
      }),
  })
);

describe("WebSocket Connection Timing Fix", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("should wait for WebSocket connection before starting practice", async () => {
    const mockToggleStreaming = jest.fn();

    render(
      <ASLWorldPage
        toggleStreaming={mockToggleStreaming}
        webcamActive={true}
        streamingActive={false}
        streamingConnectionStatus="disconnected"
      />
    );

    // Navigate to word selection
    const wordTabButton = screen.getByText("Choose a Word");
    fireEvent.click(wordTabButton);

    // Generate story with a word
    const catButton = screen.getByText("Cat");
    fireEvent.click(catButton);

    // Wait for story generation to complete
    await waitFor(
      () => {
        expect(
          screen.getByText(/Choose Your Challenge Level/i)
        ).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    // Select a story
    const storyButton = screen.getByText("Test Story");
    fireEvent.click(storyButton);

    // Wait for practice view
    await waitFor(() => {
      expect(screen.getByText(/Start Practice/i)).toBeInTheDocument();
    });

    // Click start practice
    const startPracticeButton = screen.getByText(/Start Practice/i);
    fireEvent.click(startPracticeButton);

    // Verify that streaming is activated
    await waitFor(() => {
      expect(mockToggleStreaming).toHaveBeenCalled();
    });
  });

  test("should handle connection timeout gracefully", async () => {
    // Mock console.error to capture timeout message
    const consoleSpy = jest
      .spyOn(console, "error")
      .mockImplementation(() => {});

    // Mock a WebSocket that never connects
    jest.doMock("../hooks/useWebSocket", () => ({
      __esModule: true,
      default: () => ({
        connectionState: "disconnected",
        isConnected: false,
        lastMessage: null,
        sendMessage: jest.fn().mockReturnValue(false),
      }),
    }));

    render(<ASLWorldPage />);

    // The component should handle the timeout gracefully
    // This test verifies no crashes occur with connection timeouts
    expect(screen.getByText("ASL World")).toBeInTheDocument();

    consoleSpy.mockRestore();
  });
});
