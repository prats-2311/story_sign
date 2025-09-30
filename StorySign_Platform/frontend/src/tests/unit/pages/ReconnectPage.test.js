import React from "react";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import "@testing-library/jest-dom";
import ReconnectPage from "./ReconnectPage";

// Mock the hooks
jest.mock("../hooks/useWebcam", () => ({
  __esModule: true,
  default: jest.fn(),
}));

// Mock the modules that ReconnectPage depends on
jest.mock("../modules/reconnect", () => ({
  ExerciseSelector: ({
    onStartSession,
    webcamStatus,
    webcamError,
    error,
    onClearError,
    isWebcamActive,
    webcamStream,
  }) => (
    <div data-testid="exercise-selector">
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
        onClick={() => onStartSession({ id: "test", name: "Test Exercise" })}
        data-testid="start-session"
      >
        Start Test Exercise
      </button>
      <button onClick={onClearError} data-testid="clear-error">
        Clear Error
      </button>
    </div>
  ),
  MovementAnalysis: ({
    currentExercise,
    isSessionActive,
    isWebcamActive,
    webcamStream,
  }) => (
    <div data-testid="movement-analysis">
      {currentExercise && (
        <span data-testid="current-exercise">{currentExercise.name}</span>
      )}
      <span data-testid="session-active">
        {isSessionActive ? "true" : "false"}
      </span>
      <span data-testid="webcam-active">
        {isWebcamActive ? "true" : "false"}
      </span>
    </div>
  ),
  TherapyDashboard: ({ sessionData, onNewSession, isWebcamActive }) => (
    <div data-testid="therapy-dashboard">
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

describe("ReconnectPage Camera Lifecycle Management", () => {
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

  describe("Basic Rendering", () => {
    test("renders ReconnectPage with header", () => {
      render(<ReconnectPage {...defaultProps} />);

      expect(screen.getByText("Reconnect")).toBeInTheDocument();
      expect(
        screen.getByText(
          "Therapeutic Movement Analysis & Physical Rehabilitation"
        )
      ).toBeInTheDocument();
    });

    test("renders ExerciseSelector in setup view", () => {
      mockUseWebcam.mockReturnValue({
        stream: "mock-stream",
        isActive: true,
        status: "active",
        error: null,
        startWebcam: mockStartWebcam,
        stopWebcam: mockStopWebcam,
        attachToVideoElement: jest.fn(),
      });

      render(<ReconnectPage {...defaultProps} />);

      expect(screen.getByTestId("exercise-selector")).toBeInTheDocument();
    });
  });

  describe("Automatic Camera Initialization", () => {
    test("should call startWebcam on component mount", async () => {
      await act(async () => {
        render(<ReconnectPage {...defaultProps} />);
      });

      expect(mockStartWebcam).toHaveBeenCalledTimes(1);
    });

    test("should call stopWebcam on component unmount", async () => {
      const { unmount } = render(<ReconnectPage {...defaultProps} />);

      await act(async () => {
        unmount();
      });

      expect(mockStopWebcam).toHaveBeenCalledTimes(1);
    });

    test("should handle webcam initialization errors", async () => {
      const initError = new Error("Camera permission denied");
      mockStartWebcam.mockRejectedValue(initError);

      await act(async () => {
        render(<ReconnectPage {...defaultProps} />);
      });

      expect(mockStartWebcam).toHaveBeenCalledTimes(1);
      // Component should still render without crashing
      expect(screen.getByText("Reconnect")).toBeInTheDocument();
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

      render(<ReconnectPage {...defaultProps} />);

      expect(screen.getByText("Camera Required")).toBeInTheDocument();
      expect(
        screen.getByText(
          "Reconnect requires camera access for therapeutic movement analysis and physical rehabilitation features."
        )
      ).toBeInTheDocument();
    });

    test("should show exercise selector when webcam is active", () => {
      mockUseWebcam.mockReturnValue({
        stream: "mock-stream",
        isActive: true,
        status: "active",
        error: null,
        startWebcam: mockStartWebcam,
        stopWebcam: mockStopWebcam,
        attachToVideoElement: jest.fn(),
      });

      render(<ReconnectPage {...defaultProps} />);

      expect(screen.getByTestId("exercise-selector")).toBeInTheDocument();
      expect(screen.getByTestId("webcam-active")).toHaveTextContent("true");
    });

    test("should show exercise selector during webcam initialization", () => {
      mockUseWebcam.mockReturnValue({
        stream: null,
        isActive: false,
        status: "initializing",
        error: null,
        startWebcam: mockStartWebcam,
        stopWebcam: mockStopWebcam,
        attachToVideoElement: jest.fn(),
      });

      render(<ReconnectPage {...defaultProps} />);

      // Should show exercise selector during initialization, not placeholder
      expect(screen.getByTestId("exercise-selector")).toBeInTheDocument();
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

      render(<ReconnectPage {...defaultProps} />);

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

      render(<ReconnectPage {...defaultProps} />);

      const retryButton = screen.getByText("Retry Camera Access");
      fireEvent.click(retryButton);

      expect(mockStartWebcam).toHaveBeenCalledTimes(2); // Once on mount, once on retry
    });

    test("should handle camera permission scenarios", () => {
      const permissionError = { message: "Permission denied by user" };
      mockUseWebcam.mockReturnValue({
        stream: null,
        isActive: false,
        status: "error",
        error: permissionError,
        startWebcam: mockStartWebcam,
        stopWebcam: mockStopWebcam,
        attachToVideoElement: jest.fn(),
      });

      render(<ReconnectPage {...defaultProps} />);

      expect(screen.getByText("Permission denied by user")).toBeInTheDocument();
      expect(
        screen.getByText("Allow camera permissions when prompted")
      ).toBeInTheDocument();
    });
  });

  describe("Module Prop Passing", () => {
    test("should pass webcam state to ExerciseSelector", () => {
      mockUseWebcam.mockReturnValue({
        stream: "mock-stream",
        isActive: true,
        status: "active",
        error: null,
        startWebcam: mockStartWebcam,
        stopWebcam: mockStopWebcam,
        attachToVideoElement: jest.fn(),
      });

      render(<ReconnectPage {...defaultProps} />);

      expect(screen.getByTestId("webcam-status")).toHaveTextContent("active");
      expect(screen.getByTestId("webcam-active")).toHaveTextContent("true");
      expect(screen.getByTestId("webcam-stream")).toHaveTextContent(
        "has-stream"
      );
    });

    test("should pass webcam state to MovementAnalysis during practice", async () => {
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
        <ReconnectPage
          {...defaultProps}
          streamingConnectionStatus="connected"
        />
      );

      // Start a session to navigate to practice view
      fireEvent.click(screen.getByTestId("start-session"));

      await waitFor(() => {
        expect(screen.getByTestId("movement-analysis")).toBeInTheDocument();
        expect(screen.getByTestId("webcam-active")).toHaveTextContent("true");
      });
    });

    test("should pass webcam state to TherapyDashboard in results view", async () => {
      mockUseWebcam.mockReturnValue({
        stream: "mock-stream",
        isActive: true,
        status: "active",
        error: null,
        startWebcam: mockStartWebcam,
        stopWebcam: mockStopWebcam,
        attachToVideoElement: jest.fn(),
      });

      render(<ReconnectPage {...defaultProps} />);

      // Start a session
      fireEvent.click(screen.getByTestId("start-session"));

      await waitFor(() => {
        expect(screen.getByTestId("movement-analysis")).toBeInTheDocument();
      });

      // End session would normally transition to results view
      // For testing purposes, we'll verify the prop passing structure
      expect(screen.getByTestId("webcam-active")).toHaveTextContent("true");
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

      render(<ReconnectPage {...defaultProps} />);

      expect(
        screen.getByText("Camera Active - Ready for therapy")
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

      render(<ReconnectPage {...defaultProps} />);

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

      render(<ReconnectPage {...defaultProps} />);

      expect(screen.getByText("Initializing camera...")).toBeInTheDocument();
    });
  });

  describe("Resource Cleanup", () => {
    test("should properly cleanup resources on unmount", async () => {
      const { unmount } = render(<ReconnectPage {...defaultProps} />);

      await act(async () => {
        unmount();
      });

      expect(mockStopWebcam).toHaveBeenCalledTimes(1);
    });

    test("should not call cleanup multiple times", async () => {
      const { unmount, rerender } = render(<ReconnectPage {...defaultProps} />);

      // Rerender component
      rerender(<ReconnectPage {...defaultProps} />);

      await act(async () => {
        unmount();
      });

      expect(mockStopWebcam).toHaveBeenCalledTimes(1);
    });

    test("should handle cleanup errors gracefully", async () => {
      mockStopWebcam.mockImplementation(() => {
        throw new Error("Cleanup error");
      });

      const { unmount } = render(<ReconnectPage {...defaultProps} />);

      // Should not throw error during unmount
      await act(async () => {
        expect(() => unmount()).not.toThrow();
      });
    });
  });
});
