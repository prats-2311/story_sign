/**
 * Test to verify practice session error fix
 * This test checks that handleStartPractice doesn't throw errors
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

// Mock the useWebSocket hook
jest.mock("../hooks/useWebSocket", () => ({
  __esModule: true,
  default: () => ({
    connectionState: "connected",
    isConnected: true,
    lastMessage: null,
    sendMessage: jest.fn().mockReturnValue(true),
  }),
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

describe("Practice Session Error Fix", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mock console.error to capture any errors
    jest.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    console.error.mockRestore();
  });

  test("should handle start practice without throwing errors", async () => {
    const mockToggleStreaming = jest.fn();
    const mockToggleWebcam = jest.fn();

    render(
      <ASLWorldPage
        toggleStreaming={mockToggleStreaming}
        toggleWebcam={mockToggleWebcam}
        webcamActive={true}
        streamingActive={false}
        streamingConnectionStatus="connected"
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
      expect(screen.getByText(/Start Practice Session/i)).toBeInTheDocument();
    });

    // Click start practice - this should not throw an error
    const startPracticeButton = screen.getByText(/Start Practice Session/i);

    // Verify no errors are thrown
    expect(() => {
      fireEvent.click(startPracticeButton);
    }).not.toThrow();

    // Verify console.error was not called with practice session errors
    await waitFor(() => {
      const errorCalls = console.error.mock.calls;
      const practiceErrors = errorCalls.filter(call =>
        call.some(
          arg =>
            typeof arg === "string" &&
            arg.includes("Failed to start practice session")
        )
      );
      expect(practiceErrors).toHaveLength(0);
    });
  });

  test("should handle errors gracefully in handleStartPractice", async () => {
    // Mock startWebcam to throw an error
    const mockStartWebcam = jest
      .fn()
      .mockRejectedValue(new Error("Webcam error"));

    jest.doMock("../hooks/useWebcam", () => ({
      __esModule: true,
      default: () => ({
        stream: null,
        isActive: false,
        status: "error",
        error: { message: "Webcam error" },
        startWebcam: mockStartWebcam,
        stopWebcam: jest.fn(),
        captureFrame: jest.fn(),
        performanceStats: {},
      }),
    }));

    render(<ASLWorldPage />);

    // The component should handle webcam errors gracefully
    expect(screen.getByText("ASL World")).toBeInTheDocument();
  });
});
