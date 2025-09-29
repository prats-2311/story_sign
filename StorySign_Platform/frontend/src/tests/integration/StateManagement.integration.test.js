import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import "@testing-library/jest-dom";

// Import components to test
import ASLWorldPage from "../../pages/ASLWorldPage";
import HarmonyPage from "../../pages/HarmonyPage";
import ReconnectPage from "../../pages/ReconnectPage";

// Mock the hooks with more realistic implementations
jest.mock("../../hooks/useWebSocket", () => ({
  __esModule: true,
  default: jest.fn(),
}));

jest.mock("../../hooks/useWebcam", () => ({
  __esModule: true,
  default: jest.fn(),
}));

// Mock all the module components
jest.mock("../../modules/asl_world", () => ({
  StorySetup: ({
    webcamRef,
    isWebcamActive,
    captureFrame,
    connectionStatus,
    onStoryGenerate,
  }) => (
    <div data-testid="story-setup">
      <span data-testid="webcam-active">
        {isWebcamActive ? "true" : "false"}
      </span>
      <span data-testid="connection-status">{connectionStatus}</span>
      <button onClick={() => onStoryGenerate({ test: "data" })}>
        Generate Story
      </button>
    </div>
  ),
  StorySelection: ({ onStorySelect }) => (
    <div data-testid="story-selection">
      <button
        onClick={() =>
          onStorySelect({ title: "Test Story", sentences: ["Test"] })
        }
      >
        Select Story
      </button>
    </div>
  ),
  PracticeView: ({ processedFrame, sendControlMessage, children }) => (
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
  FeedbackPanel: () => <div data-testid="feedback-panel">Feedback Panel</div>,
}));

jest.mock("../../modules/harmony", () => ({
  ExpressionPractice: ({ isWebcamActive, webcamStream, onStartSession }) => (
    <div data-testid="expression-practice">
      <span data-testid="webcam-active">
        {isWebcamActive ? "true" : "false"}
      </span>
      <span data-testid="webcam-stream">
        {webcamStream ? "has-stream" : "no-stream"}
      </span>
      <button onClick={() => onStartSession("happy")}>Start Session</button>
    </div>
  ),
  EmotionMetrics: ({ isWebcamActive }) => (
    <div data-testid="emotion-metrics">
      <span data-testid="webcam-active">
        {isWebcamActive ? "true" : "false"}
      </span>
    </div>
  ),
  ProgressTracker: ({ isWebcamActive, onNewSession }) => (
    <div data-testid="progress-tracker">
      <span data-testid="webcam-active">
        {isWebcamActive ? "true" : "false"}
      </span>
      <button onClick={onNewSession}>New Session</button>
    </div>
  ),
}));

jest.mock("../../modules/reconnect", () => ({
  ExerciseSelector: ({ isWebcamActive, webcamStream, onStartSession }) => (
    <div data-testid="exercise-selector">
      <span data-testid="webcam-active">
        {isWebcamActive ? "true" : "false"}
      </span>
      <span data-testid="webcam-stream">
        {webcamStream ? "has-stream" : "no-stream"}
      </span>
      <button
        onClick={() => onStartSession({ id: "test", name: "Test Exercise" })}
      >
        Start Session
      </button>
    </div>
  ),
  MovementAnalysis: ({ isWebcamActive }) => (
    <div data-testid="movement-analysis">
      <span data-testid="webcam-active">
        {isWebcamActive ? "true" : "false"}
      </span>
    </div>
  ),
  TherapyDashboard: ({ isWebcamActive, onNewSession }) => (
    <div data-testid="therapy-dashboard">
      <span data-testid="webcam-active">
        {isWebcamActive ? "true" : "false"}
      </span>
      <button onClick={onNewSession}>New Session</button>
    </div>
  ),
}));

jest.mock("../../components/video/VideoStreamingClient", () => {
  const mockComponent = React.forwardRef((props, ref) => (
    <div data-testid="video-streaming-client">
      <span data-testid="streaming-active">
        {props.isActive ? "true" : "false"}
      </span>
    </div>
  ));
  return { __esModule: true, default: mockComponent };
});

describe("State Management Integration Tests", () => {
  let mockUseWebSocket, mockUseWebcam;
  let mockStartWebcam, mockStopWebcam, mockSendMessage;

  const defaultProps = {
    streamingConnectionStatus: "disconnected",
    onConnectionChange: jest.fn(),
    onProcessedFrame: jest.fn(),
    onError: jest.fn(),
    onRetryConnection: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();

    mockStartWebcam = jest.fn().mockResolvedValue(true);
    mockStopWebcam = jest.fn();
    mockSendMessage = jest.fn().mockReturnValue(true);

    mockUseWebSocket = require("../../hooks/useWebSocket").default;
    mockUseWebcam = require("../../hooks/useWebcam").default;

    // Default mock implementations
    mockUseWebSocket.mockReturnValue({
      connectionState: "connected",
      isConnected: true,
      lastMessage: null,
      sendMessage: mockSendMessage,
    });

    mockUseWebcam.mockReturnValue({
      stream: "mock-stream",
      isActive: true,
      status: "active",
      error: null,
      startWebcam: mockStartWebcam,
      stopWebcam: mockStopWebcam,
      captureFrame: jest.fn(),
    });
  });

  describe("ASLWorldPage State Management", () => {
    test("should maintain state during complete user workflow", async () => {
      render(<ASLWorldPage {...defaultProps} />);

      // Verify initial state
      expect(screen.getByTestId("story-setup")).toBeInTheDocument();
      expect(screen.getByTestId("webcam-active")).toHaveTextContent("true");
      expect(screen.getByTestId("connection-status")).toHaveTextContent(
        "connected"
      );

      // Generate story
      fireEvent.click(screen.getByText("Generate Story"));

      await waitFor(() => {
        expect(screen.getByTestId("story-selection")).toBeInTheDocument();
      });

      // Select story
      fireEvent.click(screen.getByText("Select Story"));

      await waitFor(() => {
        expect(screen.getByTestId("practice-view")).toBeInTheDocument();
        expect(screen.getByTestId("send-control")).toHaveTextContent(
          "has-control"
        );
        expect(
          screen.getByTestId("video-streaming-client")
        ).toBeInTheDocument();
      });

      // Verify webcam was initialized and not stopped during transitions
      expect(mockStartWebcam).toHaveBeenCalledTimes(1);
      expect(mockStopWebcam).not.toHaveBeenCalled();
    });

    test("should handle webcam state changes during workflow", async () => {
      const { rerender } = render(<ASLWorldPage {...defaultProps} />);

      // Start with inactive webcam
      mockUseWebcam.mockReturnValue({
        stream: null,
        isActive: false,
        status: "inactive",
        error: null,
        startWebcam: mockStartWebcam,
        stopWebcam: mockStopWebcam,
        captureFrame: jest.fn(),
      });

      rerender(<ASLWorldPage {...defaultProps} />);
      expect(screen.getByTestId("webcam-active")).toHaveTextContent("false");

      // Activate webcam
      mockUseWebcam.mockReturnValue({
        stream: "mock-stream",
        isActive: true,
        status: "active",
        error: null,
        startWebcam: mockStartWebcam,
        stopWebcam: mockStopWebcam,
        captureFrame: jest.fn(),
      });

      rerender(<ASLWorldPage {...defaultProps} />);
      expect(screen.getByTestId("webcam-active")).toHaveTextContent("true");
    });

    test("should handle WebSocket state changes during workflow", async () => {
      const { rerender } = render(<ASLWorldPage {...defaultProps} />);

      // Navigate to practice view
      fireEvent.click(screen.getByText("Generate Story"));
      await waitFor(() => screen.getByTestId("story-selection"));
      fireEvent.click(screen.getByText("Select Story"));
      await waitFor(() => screen.getByTestId("practice-view"));

      // Start with connected WebSocket
      expect(screen.getByTestId("send-control")).toHaveTextContent(
        "has-control"
      );

      // Disconnect WebSocket
      mockUseWebSocket.mockReturnValue({
        connectionState: "disconnected",
        isConnected: false,
        lastMessage: null,
        sendMessage: jest.fn().mockReturnValue(false),
      });

      rerender(<ASLWorldPage {...defaultProps} />);
      expect(screen.getByTestId("send-control")).toHaveTextContent(
        "no-control"
      );
    });
  });

  describe("HarmonyPage Camera Lifecycle", () => {
    test("should initialize camera on mount and cleanup on unmount", async () => {
      const { unmount } = render(<HarmonyPage {...defaultProps} />);

      // Verify camera initialization
      expect(mockStartWebcam).toHaveBeenCalledTimes(1);
      expect(screen.getByTestId("expression-practice")).toBeInTheDocument();
      expect(screen.getByTestId("webcam-active")).toHaveTextContent("true");

      // Unmount and verify cleanup
      unmount();
      expect(mockStopWebcam).toHaveBeenCalledTimes(1);
    });

    test("should show camera placeholder when webcam is inactive", () => {
      mockUseWebcam.mockReturnValue({
        stream: null,
        isActive: false,
        status: "inactive",
        error: null,
        startWebcam: mockStartWebcam,
        stopWebcam: mockStopWebcam,
        captureFrame: jest.fn(),
      });

      render(<HarmonyPage {...defaultProps} />);

      expect(screen.getByText("Camera Required")).toBeInTheDocument();
      expect(
        screen.queryByTestId("expression-practice")
      ).not.toBeInTheDocument();
    });

    test("should pass webcam state through complete session workflow", async () => {
      render(
        <HarmonyPage {...defaultProps} streamingConnectionStatus="connected" />
      );

      // Start session
      fireEvent.click(screen.getByText("Start Session"));

      await waitFor(() => {
        expect(screen.getByTestId("emotion-metrics")).toBeInTheDocument();
        expect(screen.getByTestId("webcam-active")).toHaveTextContent("true");
      });

      // Verify webcam state is maintained
      expect(mockStopWebcam).not.toHaveBeenCalled();
    });
  });

  describe("ReconnectPage Camera Lifecycle", () => {
    test("should initialize camera on mount and cleanup on unmount", async () => {
      const { unmount } = render(<ReconnectPage {...defaultProps} />);

      // Verify camera initialization
      expect(mockStartWebcam).toHaveBeenCalledTimes(1);
      expect(screen.getByTestId("exercise-selector")).toBeInTheDocument();
      expect(screen.getByTestId("webcam-active")).toHaveTextContent("true");

      // Unmount and verify cleanup
      unmount();
      expect(mockStopWebcam).toHaveBeenCalledTimes(1);
    });

    test("should show camera placeholder when webcam is inactive", () => {
      mockUseWebcam.mockReturnValue({
        stream: null,
        isActive: false,
        status: "inactive",
        error: null,
        startWebcam: mockStartWebcam,
        stopWebcam: mockStopWebcam,
        captureFrame: jest.fn(),
      });

      render(<ReconnectPage {...defaultProps} />);

      expect(screen.getByText("Camera Required")).toBeInTheDocument();
      expect(screen.queryByTestId("exercise-selector")).not.toBeInTheDocument();
    });

    test("should pass webcam state through complete therapy workflow", async () => {
      render(
        <ReconnectPage
          {...defaultProps}
          streamingConnectionStatus="connected"
        />
      );

      // Start session
      fireEvent.click(screen.getByText("Start Session"));

      await waitFor(() => {
        expect(screen.getByTestId("movement-analysis")).toBeInTheDocument();
        expect(screen.getByTestId("webcam-active")).toHaveTextContent("true");
      });

      // Verify webcam state is maintained
      expect(mockStopWebcam).not.toHaveBeenCalled();
    });
  });

  describe("Cross-Component State Consistency", () => {
    test("should maintain consistent webcam state across different pages", async () => {
      // Test ASLWorldPage
      const { unmount: unmountASL } = render(
        <ASLWorldPage {...defaultProps} />
      );
      expect(screen.getByTestId("webcam-active")).toHaveTextContent("true");
      unmountASL();

      // Test HarmonyPage
      const { unmount: unmountHarmony } = render(
        <HarmonyPage {...defaultProps} />
      );
      expect(screen.getByTestId("webcam-active")).toHaveTextContent("true");
      unmountHarmony();

      // Test ReconnectPage
      const { unmount: unmountReconnect } = render(
        <ReconnectPage {...defaultProps} />
      );
      expect(screen.getByTestId("webcam-active")).toHaveTextContent("true");
      unmountReconnect();

      // Each page should initialize and cleanup its own webcam
      expect(mockStartWebcam).toHaveBeenCalledTimes(3);
      expect(mockStopWebcam).toHaveBeenCalledTimes(3);
    });

    test("should handle error states consistently across pages", () => {
      const cameraError = { message: "Camera access denied" };
      mockUseWebcam.mockReturnValue({
        stream: null,
        isActive: false,
        status: "error",
        error: cameraError,
        startWebcam: mockStartWebcam,
        stopWebcam: mockStopWebcam,
        captureFrame: jest.fn(),
      });

      // Test error handling in ASLWorldPage
      const { unmount: unmountASL } = render(
        <ASLWorldPage {...defaultProps} />
      );
      expect(screen.getByTestId("webcam-active")).toHaveTextContent("false");
      unmountASL();

      // Test error handling in HarmonyPage
      const { unmount: unmountHarmony } = render(
        <HarmonyPage {...defaultProps} />
      );
      expect(screen.getByText("Camera Required")).toBeInTheDocument();
      expect(screen.getByText("Camera access denied")).toBeInTheDocument();
      unmountHarmony();

      // Test error handling in ReconnectPage
      render(<ReconnectPage {...defaultProps} />);
      expect(screen.getByText("Camera Required")).toBeInTheDocument();
      expect(screen.getByText("Camera access denied")).toBeInTheDocument();
    });
  });

  describe("Resource Management", () => {
    test("should properly cleanup resources when switching between pages", async () => {
      // Render ASLWorldPage
      const { unmount: unmountASL } = render(
        <ASLWorldPage {...defaultProps} />
      );
      expect(mockStartWebcam).toHaveBeenCalledTimes(1);

      unmountASL();
      expect(mockStopWebcam).toHaveBeenCalledTimes(1);

      // Render HarmonyPage
      const { unmount: unmountHarmony } = render(
        <HarmonyPage {...defaultProps} />
      );
      expect(mockStartWebcam).toHaveBeenCalledTimes(2);

      unmountHarmony();
      expect(mockStopWebcam).toHaveBeenCalledTimes(2);

      // Render ReconnectPage
      const { unmount: unmountReconnect } = render(
        <ReconnectPage {...defaultProps} />
      );
      expect(mockStartWebcam).toHaveBeenCalledTimes(3);

      unmountReconnect();
      expect(mockStopWebcam).toHaveBeenCalledTimes(3);
    });

    test("should handle multiple rapid mount/unmount cycles", async () => {
      for (let i = 0; i < 5; i++) {
        const { unmount } = render(<HarmonyPage {...defaultProps} />);
        unmount();
      }

      expect(mockStartWebcam).toHaveBeenCalledTimes(5);
      expect(mockStopWebcam).toHaveBeenCalledTimes(5);
    });
  });

  describe("Error Recovery", () => {
    test("should recover from webcam errors when retrying", async () => {
      // Start with error state
      const cameraError = { message: "Camera access denied" };
      mockUseWebcam.mockReturnValue({
        stream: null,
        isActive: false,
        status: "error",
        error: cameraError,
        startWebcam: mockStartWebcam,
        stopWebcam: mockStopWebcam,
        captureFrame: jest.fn(),
      });

      const { rerender } = render(<HarmonyPage {...defaultProps} />);
      expect(screen.getByText("Camera access denied")).toBeInTheDocument();

      // Simulate successful retry
      mockUseWebcam.mockReturnValue({
        stream: "mock-stream",
        isActive: true,
        status: "active",
        error: null,
        startWebcam: mockStartWebcam,
        stopWebcam: mockStopWebcam,
        captureFrame: jest.fn(),
      });

      rerender(<HarmonyPage {...defaultProps} />);
      expect(screen.getByTestId("expression-practice")).toBeInTheDocument();
      expect(screen.getByTestId("webcam-active")).toHaveTextContent("true");
    });

    test("should handle WebSocket reconnection scenarios", async () => {
      const { rerender } = render(<ASLWorldPage {...defaultProps} />);

      // Navigate to practice view
      fireEvent.click(screen.getByText("Generate Story"));
      await waitFor(() => screen.getByTestId("story-selection"));
      fireEvent.click(screen.getByText("Select Story"));
      await waitFor(() => screen.getByTestId("practice-view"));

      // Simulate WebSocket disconnection
      mockUseWebSocket.mockReturnValue({
        connectionState: "disconnected",
        isConnected: false,
        lastMessage: null,
        sendMessage: jest.fn().mockReturnValue(false),
      });

      rerender(<ASLWorldPage {...defaultProps} />);
      expect(screen.getByTestId("send-control")).toHaveTextContent(
        "no-control"
      );

      // Simulate WebSocket reconnection
      mockUseWebSocket.mockReturnValue({
        connectionState: "connected",
        isConnected: true,
        lastMessage: null,
        sendMessage: mockSendMessage,
      });

      rerender(<ASLWorldPage {...defaultProps} />);
      expect(screen.getByTestId("send-control")).toHaveTextContent(
        "has-control"
      );
    });
  });
});
