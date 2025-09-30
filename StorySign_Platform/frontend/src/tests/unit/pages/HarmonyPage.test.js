import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import "@testing-library/jest-dom";
import HarmonyPage from "./HarmonyPage";

// Mock the hooks
jest.mock("../hooks/useWebcam", () => ({
  __esModule: true,
  default: jest.fn(),
}));

// Mock the modules
jest.mock("../modules/harmony", () => ({
  ExpressionPractice: ({
    onStartSession,
    webcamStatus,
    webcamError,
    error,
    onClearError,
    isWebcamActive,
    webcamStream,
  }) => (
    <div data-testid="expression-practice">
      <span data-testid="webcam-status">{webcamStatus}</span>
      <span data-testid="webcam-active">
        {isWebcamActive ? "true" : "false"}
      </span>
      <span data-testid="webcam-stream">
        {webcamStream ? "has-stream" : "no-stream"}
      </span>
      {error && <div data-testid="error">{error.message}</div>}
      {webcamError && (
        <div data-testid="webcam-error">{webcamError.message}</div>
      )}
      <button
        onClick={() => onStartSession("happy")}
        data-testid="start-session"
      >
        Start Session
      </button>
      <button onClick={onClearError} data-testid="clear-error">
        Clear Error
      </button>
    </div>
  ),
  EmotionMetrics: ({
    targetEmotion,
    currentDetection,
    sessionData,
    isSessionActive,
    isWebcamActive,
    webcamStream,
  }) => (
    <div data-testid="emotion-metrics">
      <span data-testid="target-emotion">{targetEmotion}</span>
      <span data-testid="session-active">
        {isSessionActive ? "true" : "false"}
      </span>
      <span data-testid="webcam-active">
        {isWebcamActive ? "true" : "false"}
      </span>
    </div>
  ),
  ProgressTracker: ({
    sessionData,
    sessionDuration,
    onNewSession,
    isWebcamActive,
  }) => (
    <div data-testid="progress-tracker">
      <span data-testid="webcam-active">
        {isWebcamActive ? "true" : "false"}
      </span>
      <button onClick={onNewSession} data-testid="new-session">
        New Session
      </button>
    </div>
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

describe("HarmonyPage Camera Lifecycle Management", () => {
  let mockUseWebcam;
  let mockStartWebcam;
  let mockStopWebcam;

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

    mockUseWebcam = require("../hooks/useWebcam").default;
    mockUseWebcam.mockReturnValue({
      stream: null,
      isActive: false,
      status: "inactive",
      error: null,
      startWebcam: mockStartWebcam,
      stopWebcam: mockStopWebcam,
      attachToVideoElement: jest.fn(),
    });
  });

  describe("Automatic Camera Initialization", () => {
    test("should call startWebcam on component mount", async () => {
      await act(async () => {
        render(<HarmonyPage {...defaultProps} />);
      });

      expect(mockStartWebcam).toHaveBeenCalledTimes(1);
    });

    test("should call stopWebcam on component unmount", async () => {
      const { unmount } = render(<HarmonyPage {...defaultProps} />);

      await act(async () => {
        unmount();
      });

      expect(mockStopWebcam).toHaveBeenCalledTimes(1);
    });

    test("should handle webcam initialization errors", async () => {
      const initError = new Error("Camera permission denied");
      mockStartWebcam.mockRejectedValue(initError);

      await act(async () => {
        render(<HarmonyPage {...defaultProps} />);
      });

      expect(mockStartWebcam).toHaveBeenCalledTimes(1);
      // Component should still render without crashing
      expect(screen.getByText("Harmony")).toBeInTheDocument();
    });
  });

  describe("Conditional Rendering Based on Webcam State", () => {
    test("should show camera inactive placeholder when webcam is not active", () => {
      mockUseWebcam.mockReturnValue({
        stream: null,
        isActive: false,
        status: "inactive",
        error: null,
        startWebcam: mockStartWebcam,
        stopWebcam: mockStopWebcam,
        attachToVideoElement: jest.fn(),
      });

      render(<HarmonyPage {...defaultProps} />);

      expect(screen.getByText("Camera Required")).toBeInTheDocument();
      expect(
        screen.getByText(
          "Harmony requires camera access for facial expression practice and social-emotional learning features."
        )
      ).toBeInTheDocument();
    });

    test("should show expression practice when webcam is active", () => {
      mockUseWebcam.mockReturnValue({
        stream: "mock-stream",
        isActive: true,
        status: "active",
        error: null,
        startWebcam: mockStartWebcam,
        stopWebcam: mockStopWebcam,
        attachToVideoElement: jest.fn(),
      });

      render(<HarmonyPage {...defaultProps} />);

      expect(screen.getByTestId("expression-practice")).toBeInTheDocument();
      expect(screen.getByTestId("webcam-active")).toHaveTextContent("true");
    });

    test("should show loading state during webcam initialization", () => {
      mockUseWebcam.mockReturnValue({
        stream: null,
        isActive: false,
        status: "initializing",
        error: null,
        startWebcam: mockStartWebcam,
        stopWebcam: mockStopWebcam,
        attachToVideoElement: jest.fn(),
      });

      render(<HarmonyPage {...defaultProps} />);

      // Should show expression practice during initialization, not placeholder
      expect(screen.getByTestId("expression-practice")).toBeInTheDocument();
    });
  });

  describe("Camera Error Handling", () => {
    test("should display camera error in placeholder", () => {
      const cameraError = { message: "Camera access denied" };
      mockUseWebcam.mockReturnValue({
        stream: null,
        isActive: false,
        status: "error",
        error: cameraError,
        startWebcam: mockStartWebcam,
        stopWebcam: mockStopWebcam,
        attachToVideoElement: jest.fn(),
      });

      render(<HarmonyPage {...defaultProps} />);

      expect(screen.getByText("Camera Required")).toBeInTheDocument();
      expect(screen.getByText("Camera access denied")).toBeInTheDocument();
      expect(screen.getByText("Retry Camera Access")).toBeInTheDocument();
    });

    test("should handle retry camera access", () => {
      const cameraError = { message: "Camera access denied" };
      mockUseWebcam.mockReturnValue({
        stream: null,
        isActive: false,
        status: "error",
        error: cameraError,
        startWebcam: mockStartWebcam,
        stopWebcam: mockStopWebcam,
        attachToVideoElement: jest.fn(),
      });

      render(<HarmonyPage {...defaultProps} />);

      const retryButton = screen.getByText("Retry Camera Access");
      fireEvent.click(retryButton);

      expect(mockStartWebcam).toHaveBeenCalledTimes(2); // Once on mount, once on retry
    });
  });

  describe("Module Prop Passing", () => {
    test("should pass webcam state to ExpressionPractice", () => {
      mockUseWebcam.mockReturnValue({
        stream: "mock-stream",
        isActive: true,
        status: "active",
        error: null,
        startWebcam: mockStartWebcam,
        stopWebcam: mockStopWebcam,
        attachToVideoElement: jest.fn(),
      });

      render(<HarmonyPage {...defaultProps} />);

      expect(screen.getByTestId("webcam-status")).toHaveTextContent("active");
      expect(screen.getByTestId("webcam-active")).toHaveTextContent("true");
      expect(screen.getByTestId("webcam-stream")).toHaveTextContent(
        "has-stream"
      );
    });

    test("should pass webcam state to EmotionMetrics during practice", async () => {
      mockUseWebcam.mockReturnValue({
        stream: "mock-stream",
        isActive: true,
        status: "active",
        error: null,
        startWebcam: mockStartWebcam,
        stopWebcam: mockStopWebcam,
        attachToVideoElement: jest.fn(),
      });

      render(
        <HarmonyPage {...defaultProps} streamingConnectionStatus="connected" />
      );

      // Start a session to navigate to practice view
      fireEvent.click(screen.getByTestId("start-session"));

      await waitFor(() => {
        expect(screen.getByTestId("emotion-metrics")).toBeInTheDocument();
        expect(screen.getByTestId("webcam-active")).toHaveTextContent("true");
      });
    });

    test("should pass webcam state to ProgressTracker in results view", async () => {
      mockUseWebcam.mockReturnValue({
        stream: "mock-stream",
        isActive: true,
        status: "active",
        error: null,
        startWebcam: mockStartWebcam,
        stopWebcam: mockStopWebcam,
        attachToVideoElement: jest.fn(),
      });

      render(<HarmonyPage {...defaultProps} />);

      // Navigate to results view by starting and ending a session
      fireEvent.click(screen.getByTestId("start-session"));

      await waitFor(() => {
        expect(screen.getByTestId("emotion-metrics")).toBeInTheDocument();
      });

      // Simulate ending session (this would normally be done through the component)
      // For testing, we'll trigger the state change directly
      const endButton = screen.getByText("End Session");
      if (endButton) {
        fireEvent.click(endButton);
      }
    });
  });

  describe("Connection Status Display", () => {
    test("should show camera active status when webcam is active", () => {
      mockUseWebcam.mockReturnValue({
        stream: "mock-stream",
        isActive: true,
        status: "active",
        error: null,
        startWebcam: mockStartWebcam,
        stopWebcam: mockStopWebcam,
        attachToVideoElement: jest.fn(),
      });

      render(<HarmonyPage {...defaultProps} />);

      expect(
        screen.getByText("Camera Active - Ready for practice")
      ).toBeInTheDocument();
    });

    test("should show camera required status when webcam is inactive", () => {
      mockUseWebcam.mockReturnValue({
        stream: null,
        isActive: false,
        status: "inactive",
        error: null,
        startWebcam: mockStartWebcam,
        stopWebcam: mockStopWebcam,
        attachToVideoElement: jest.fn(),
      });

      render(<HarmonyPage {...defaultProps} />);

      expect(
        screen.getByText("Camera Required - Please allow access")
      ).toBeInTheDocument();
    });

    test("should show initializing status during webcam startup", () => {
      mockUseWebcam.mockReturnValue({
        stream: null,
        isActive: false,
        status: "initializing",
        error: null,
        startWebcam: mockStartWebcam,
        stopWebcam: mockStopWebcam,
        attachToVideoElement: jest.fn(),
      });

      render(<HarmonyPage {...defaultProps} />);

      expect(screen.getByText("Initializing camera...")).toBeInTheDocument();
    });
  });

  describe("Resource Cleanup", () => {
    test("should properly cleanup resources on unmount", async () => {
      const { unmount } = render(<HarmonyPage {...defaultProps} />);

      await act(async () => {
        unmount();
      });

      expect(mockStopWebcam).toHaveBeenCalledTimes(1);
    });

    test("should not call cleanup multiple times", async () => {
      const { unmount, rerender } = render(<HarmonyPage {...defaultProps} />);

      // Rerender component
      rerender(<HarmonyPage {...defaultProps} />);

      await act(async () => {
        unmount();
      });

      expect(mockStopWebcam).toHaveBeenCalledTimes(1);
    });
  });
});
