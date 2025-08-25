import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

// Mock react-router-dom
jest.mock("react-router-dom", () => ({
  useNavigate: () => jest.fn(),
}));

// Mock the modules
jest.mock("../modules", () => ({
  ASLWorldModule: ({ children, onStartPractice, ...props }) => (
    <div data-testid="asl-world-module">
      <button onClick={onStartPractice} data-testid="start-practice-btn">
        Start Practice
      </button>
      {children}
    </div>
  ),
}));

jest.mock("../components", () => ({
  VideoStream: (props) => (
    <div data-testid="video-stream">
      Video Stream Component
      {props.webcamActive && (
        <span data-testid="webcam-active">Webcam Active</span>
      )}
      {props.streamingActive && (
        <span data-testid="streaming-active">Streaming Active</span>
      )}
    </div>
  ),
}));

// Import after mocking
const ASLWorldPage = require("./ASLWorldPage").default;

const mockProps = {
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

describe("ASLWorldPage Video Streaming Fix", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("should activate webcam when start practice is clicked", async () => {
    const { rerender } = render(<ASLWorldPage {...mockProps} />);

    const startPracticeBtn = screen.getByTestId("start-practice-btn");
    fireEvent.click(startPracticeBtn);

    // Should call toggleWebcam
    expect(mockProps.toggleWebcam).toHaveBeenCalledTimes(1);
  });

  test("should activate streaming after webcam is active", async () => {
    const { rerender } = render(<ASLWorldPage {...mockProps} />);

    // Start practice
    const startPracticeBtn = screen.getByTestId("start-practice-btn");
    fireEvent.click(startPracticeBtn);

    // Simulate webcam becoming active
    rerender(<ASLWorldPage {...mockProps} webcamActive={true} />);

    // Wait for the effect to trigger streaming
    await waitFor(
      () => {
        expect(mockProps.toggleStreaming).toHaveBeenCalledTimes(1);
      },
      { timeout: 2000 }
    );
  });

  test("should not activate streaming if backend is not connected", async () => {
    const propsWithDisconnectedBackend = {
      ...mockProps,
      connectionStatus: "disconnected",
    };

    const { rerender } = render(
      <ASLWorldPage {...propsWithDisconnectedBackend} />
    );

    // Start practice
    const startPracticeBtn = screen.getByTestId("start-practice-btn");
    fireEvent.click(startPracticeBtn);

    // Simulate webcam becoming active
    rerender(
      <ASLWorldPage {...propsWithDisconnectedBackend} webcamActive={true} />
    );

    // Wait a bit and ensure streaming is not activated
    await new Promise((resolve) => setTimeout(resolve, 1500));
    expect(mockProps.toggleStreaming).not.toHaveBeenCalled();
  });

  test("should test backend connection if not connected when starting practice", async () => {
    const propsWithDisconnectedBackend = {
      ...mockProps,
      connectionStatus: "not_tested",
    };

    render(<ASLWorldPage {...propsWithDisconnectedBackend} />);

    const startPracticeBtn = screen.getByTestId("start-practice-btn");
    fireEvent.click(startPracticeBtn);

    // Should call testBackendConnection
    await waitFor(() => {
      expect(mockProps.testBackendConnection).toHaveBeenCalledTimes(1);
    });
  });

  test("should show video stream component with correct props", () => {
    render(
      <ASLWorldPage {...mockProps} webcamActive={true} streamingActive={true} />
    );

    expect(screen.getByTestId("video-stream")).toBeInTheDocument();
    expect(screen.getByTestId("webcam-active")).toBeInTheDocument();
    expect(screen.getByTestId("streaming-active")).toBeInTheDocument();
  });
});
