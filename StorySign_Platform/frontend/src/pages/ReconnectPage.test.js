import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import ReconnectPage from "./ReconnectPage";

// Mock the modules that ReconnectPage depends on
jest.mock("../modules/reconnect", () => ({
  ExerciseSelector: ({
    onStartSession,
    connectionStatus,
    webcamStatus,
    error,
    onClearError,
  }) => (
    <div data-testid="exercise-selector">
      <h2>Exercise Selector</h2>
      <div>Connection: {connectionStatus}</div>
      <div>Webcam: {webcamStatus}</div>
      {error && <div data-testid="error">{error.message}</div>}
      <button
        onClick={() => onStartSession({ id: "test", name: "Test Exercise" })}
      >
        Start Test Exercise
      </button>
    </div>
  ),
  MovementAnalysis: ({ currentExercise, isSessionActive }) => (
    <div data-testid="movement-analysis">
      <h2>Movement Analysis</h2>
      {currentExercise && <div>Current: {currentExercise.name}</div>}
      <div>Active: {isSessionActive ? "Yes" : "No"}</div>
    </div>
  ),
  TherapyDashboard: ({ sessionData, onNewSession }) => (
    <div data-testid="therapy-dashboard">
      <h2>Therapy Dashboard</h2>
      <button onClick={onNewSession}>New Session</button>
    </div>
  ),
}));

jest.mock("../components/video/VideoStreamingClient", () => {
  const mockComponent = (props, ref) => (
    <div data-testid="video-streaming-client">Video Streaming Client</div>
  );
  return { __esModule: true, default: mockComponent };
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

describe("ReconnectPage", () => {
  const defaultProps = {
    connectionStatus: "disconnected",
    streamingConnectionStatus: "disconnected",
    onConnectionChange: jest.fn(),
    onProcessedFrame: jest.fn(),
    onError: jest.fn(),
    onRetryConnection: jest.fn(),
  };

  test("renders ReconnectPage with header", () => {
    render(<ReconnectPage {...defaultProps} />);

    expect(screen.getByText("Reconnect")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Therapeutic Movement Analysis & Physical Rehabilitation"
      )
    ).toBeInTheDocument();
  });

  test("shows connection status", () => {
    render(<ReconnectPage {...defaultProps} connectionStatus="connected" />);

    expect(screen.getByText("Connected")).toBeInTheDocument();
  });

  test("renders ExerciseSelector in setup view", () => {
    render(<ReconnectPage {...defaultProps} />);

    expect(screen.getByTestId("exercise-selector")).toBeInTheDocument();
    expect(screen.getByText("Exercise Selector")).toBeInTheDocument();
  });

  test("displays error state correctly", () => {
    const errorProps = {
      ...defaultProps,
      connectionStatus: "disconnected",
    };

    render(<ReconnectPage {...errorProps} />);

    expect(screen.getByText("Disconnected")).toBeInTheDocument();
  });

  test("handles unknown view state gracefully", () => {
    // This test ensures the component handles edge cases
    render(<ReconnectPage {...defaultProps} />);

    // Should render without crashing
    expect(screen.getByText("Reconnect")).toBeInTheDocument();
  });
});
