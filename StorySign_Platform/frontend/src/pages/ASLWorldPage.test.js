import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";

// Mock react-router-dom
jest.mock("react-router-dom", () => ({
  useNavigate: () => jest.fn(),
}));

// Mock the hooks
jest.mock("../hooks/useWebSocket", () => ({
  __esModule: true,
  default: jest.fn(() => ({
    connectionState: "disconnected",
    isConnected: false,
    lastMessage: null,
    sendMessage: jest.fn(),
  })),
}));

jest.mock("../hooks/useWebcam", () => ({
  __esModule: true,
  default: jest.fn(() => ({
    stream: null,
    isActive: false,
    error: null,
    startWebcam: jest.fn(),
    stopWebcam: jest.fn(),
    captureFrame: jest.fn(),
  })),
}));

// Mock the modules
jest.mock("../modules/asl_world", () => ({
  StorySetup: ({
    webcamRef,
    isWebcamActive,
    captureFrame,
    connectionStatus,
    ...props
  }) => (
    <div data-testid="story-setup">
      <span data-testid="webcam-active">
        {isWebcamActive ? "true" : "false"}
      </span>
      <span data-testid="connection-status">{connectionStatus}</span>
      <button onClick={() => props.onStoryGenerate({ test: "data" })}>
        Generate Story
      </button>
    </div>
  ),
  StorySelection: props => (
    <div data-testid="story-selection">
      <button
        onClick={() =>
          props.onStorySelect({ title: "Test Story", sentences: ["Test"] })
        }
      >
        Select Story
      </button>
    </div>
  ),
  PracticeView: ({
    processedFrame,
    sendControlMessage,
    children,
    ...props
  }) => (
    <div data-testid="practice-view">
      <span data-testid="processed-frame">
        {processedFrame ? "has-frame" : "no-frame"}
      </span>
      <span data-testid="send-control">
        {sendControlMessage ? "has-control" : "no-control"}
      </span>
      {children}
    </div>
  ),
  FeedbackPanel: props => (
    <div data-testid="feedback-panel">Feedback Panel</div>
  ),
}));

jest.mock("../components/video/VideoStreamingClient", () => ({
  __esModule: true,
  default: props => (
    <div data-testid="video-streaming-client">
      Video Streaming Client
      <span data-testid="streaming-active">
        {props.isActive ? "true" : "false"}
      </span>
    </div>
  ),
}));

// Mock fetch API
global.fetch = jest.fn();

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

describe("ASLWorldPage State Management", () => {
  let mockUseWebSocket, mockUseWebcam;

  beforeEach(() => {
    jest.clearAllMocks();

    // Mock successful API response
    global.fetch.mockResolvedValue({
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
    });

    // Reset hook mocks
    mockUseWebSocket = require("../hooks/useWebSocket").default;
    mockUseWebcam = require("../hooks/useWebcam").default;

    mockUseWebSocket.mockReturnValue({
      connectionState: "disconnected",
      isConnected: false,
      lastMessage: null,
      sendMessage: jest.fn(),
    });

    mockUseWebcam.mockReturnValue({
      stream: null,
      isActive: false,
      error: null,
      startWebcam: jest.fn(),
      stopWebcam: jest.fn(),
      captureFrame: jest.fn(),
    });
  });

  describe("Prop Passing to Components", () => {
    test("should pass webcam props to StorySetup component", () => {
      mockUseWebcam.mockReturnValue({
        stream: "mock-stream",
        isActive: true,
        error: null,
        startWebcam: jest.fn(),
        stopWebcam: jest.fn(),
        captureFrame: jest.fn(),
      });

      render(<ASLWorldPage {...mockProps} />);

      expect(screen.getByTestId("story-setup")).toBeInTheDocument();
      expect(screen.getByTestId("webcam-active")).toHaveTextContent("true");
      expect(screen.getByTestId("connection-status")).toHaveTextContent(
        "disconnected"
      );
    });

    test("should pass WebSocket props to PracticeView component", async () => {
      mockUseWebSocket.mockReturnValue({
        connectionState: "connected",
        isConnected: true,
        lastMessage: { type: "test" },
        sendMessage: jest.fn(),
      });

      render(<ASLWorldPage {...mockProps} />);

      // Navigate to story selection and then practice
      fireEvent.click(screen.getByText("Generate Story"));

      await waitFor(() => {
        expect(screen.getByTestId("story-selection")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText("Select Story"));

      await waitFor(() => {
        expect(screen.getByTestId("practice-view")).toBeInTheDocument();
        expect(screen.getByTestId("processed-frame")).toHaveTextContent(
          "has-frame"
        );
        expect(screen.getByTestId("send-control")).toHaveTextContent(
          "has-control"
        );
      });
    });

    test("should pass VideoStreamingClient as children to PracticeView", async () => {
      render(<ASLWorldPage {...mockProps} />);

      // Navigate to practice view
      fireEvent.click(screen.getByText("Generate Story"));
      await waitFor(() => screen.getByTestId("story-selection"));
      fireEvent.click(screen.getByText("Select Story"));

      await waitFor(() => {
        expect(screen.getByTestId("practice-view")).toBeInTheDocument();
        expect(
          screen.getByTestId("video-streaming-client")
        ).toBeInTheDocument();
      });
    });
  });

  describe("Webcam and WebSocket State Persistence", () => {
    test("should maintain webcam state during view transitions", async () => {
      const mockStartWebcam = jest.fn();
      const mockStopWebcam = jest.fn();

      mockUseWebcam.mockReturnValue({
        stream: "mock-stream",
        isActive: true,
        error: null,
        startWebcam: mockStartWebcam,
        stopWebcam: mockStopWebcam,
      });

      render(<ASLWorldPage {...mockProps} />);

      // Verify webcam is initialized on mount
      expect(mockStartWebcam).toHaveBeenCalledTimes(1);

      // Navigate through views
      fireEvent.click(screen.getByText("Generate Story"));
      await waitFor(() => screen.getByTestId("story-selection"));

      fireEvent.click(screen.getByText("Select Story"));
      await waitFor(() => screen.getByTestId("practice-view"));

      // Webcam should remain active throughout transitions
      expect(mockStopWebcam).not.toHaveBeenCalled();
    });

    test("should maintain WebSocket connection during view transitions", async () => {
      const mockSendMessage = jest.fn();

      mockUseWebSocket.mockReturnValue({
        connectionState: "connected",
        isConnected: true,
        lastMessage: null,
        sendMessage: mockSendMessage,
      });

      render(<ASLWorldPage {...mockProps} />);

      // Navigate to practice view
      fireEvent.click(screen.getByText("Generate Story"));
      await waitFor(() => screen.getByTestId("story-selection"));

      fireEvent.click(screen.getByText("Select Story"));
      await waitFor(() => screen.getByTestId("practice-view"));

      // WebSocket should remain connected
      expect(screen.getByTestId("send-control")).toHaveTextContent(
        "has-control"
      );
    });

    test("should cleanup webcam on component unmount", () => {
      const mockStopWebcam = jest.fn();

      mockUseWebcam.mockReturnValue({
        stream: null,
        isActive: false,
        error: null,
        startWebcam: jest.fn(),
        stopWebcam: mockStopWebcam,
        captureFrame: jest.fn(),
      });

      const { unmount } = render(<ASLWorldPage {...mockProps} />);

      unmount();

      expect(mockStopWebcam).toHaveBeenCalledTimes(1);
    });
  });

  describe("Error Handling", () => {
    test("should handle webcam initialization errors", () => {
      mockUseWebcam.mockReturnValue({
        stream: null,
        isActive: false,
        error: { message: "Camera permission denied" },
        startWebcam: jest.fn(),
        stopWebcam: jest.fn(),
        captureFrame: jest.fn(),
      });

      render(<ASLWorldPage {...mockProps} />);

      // Should still render without crashing
      expect(screen.getByTestId("story-setup")).toBeInTheDocument();
    });

    test("should handle WebSocket connection errors", () => {
      mockUseWebSocket.mockReturnValue({
        connectionState: "error",
        isConnected: false,
        lastMessage: null,
        sendMessage: jest.fn(),
      });

      render(<ASLWorldPage {...mockProps} />);

      expect(screen.getByTestId("connection-status")).toHaveTextContent(
        "error"
      );
    });
  });

  describe("Legacy Props Support", () => {
    test("should use legacy props when provided", () => {
      const legacyProps = {
        ...mockProps,
        webcamActive: true,
        streamingActive: true,
        processedFrameData: { type: "legacy" },
      };

      render(<ASLWorldPage {...legacyProps} />);

      expect(screen.getByTestId("webcam-active")).toHaveTextContent("true");
    });

    test("should fallback to internal hooks when legacy props not provided", () => {
      mockUseWebcam.mockReturnValue({
        stream: "internal-stream",
        isActive: true,
        error: null,
        startWebcam: jest.fn(),
        stopWebcam: jest.fn(),
        captureFrame: jest.fn(),
      });

      render(<ASLWorldPage {...mockProps} />);

      expect(screen.getByTestId("webcam-active")).toHaveTextContent("true");
    });
  });
});
