import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import ProcessedVideoDisplay from "./ProcessedVideoDisplay";

// Simple mock for canvas
Object.defineProperty(HTMLCanvasElement.prototype, "getContext", {
  writable: true,
  value: jest.fn().mockReturnValue({
    drawImage: jest.fn(),
    clearRect: jest.fn(),
    fillRect: jest.fn(),
    fillText: jest.fn(),
    fillStyle: "",
    font: "",
    textAlign: "",
  }),
});

// Mock Image
global.Image = class {
  constructor() {
    setTimeout(() => {
      if (this.onload) this.onload();
    }, 10);
  }

  set src(value) {
    this._src = value;
  }

  get src() {
    return this._src;
  }

  get width() {
    return 640;
  }
  get height() {
    return 480;
  }
};

describe("ProcessedVideoDisplay Component - Core Tests", () => {
  const mockOnRetryConnection = jest.fn();
  const defaultProps = {
    processedFrameData: null,
    connectionStatus: "disconnected",
    streamingStats: {
      framesSent: 0,
      framesReceived: 0,
      droppedFrames: 0,
    },
    onRetryConnection: mockOnRetryConnection,
    isActive: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders disconnected state correctly", () => {
    render(<ProcessedVideoDisplay {...defaultProps} />);

    expect(screen.getByText("Disconnected")).toBeInTheDocument();
    expect(
      screen.getByText("Not connected to video processing server")
    ).toBeInTheDocument();
  });

  test("renders connecting state correctly", () => {
    render(
      <ProcessedVideoDisplay {...defaultProps} connectionStatus="connecting" />
    );

    expect(screen.getByText("Connecting")).toBeInTheDocument();
    expect(
      screen.getByText("Establishing connection to video processor")
    ).toBeInTheDocument();
  });

  test("renders connected state correctly", () => {
    render(
      <ProcessedVideoDisplay {...defaultProps} connectionStatus="connected" />
    );

    expect(screen.getByText("Connected")).toBeInTheDocument();
    expect(
      screen.getByText("Receiving processed video stream")
    ).toBeInTheDocument();
  });

  test("renders error state with retry button", () => {
    render(
      <ProcessedVideoDisplay {...defaultProps} connectionStatus="error" />
    );

    expect(screen.getByText("Connection Error")).toBeInTheDocument();
    expect(screen.getByText("Retry Connection")).toBeInTheDocument();
  });

  test("calls retry function when retry button clicked", () => {
    render(
      <ProcessedVideoDisplay {...defaultProps} connectionStatus="error" />
    );

    const retryButton = screen.getByText("Retry Connection");
    fireEvent.click(retryButton);

    expect(mockOnRetryConnection).toHaveBeenCalledTimes(1);
  });

  test("displays performance metrics sections", () => {
    render(
      <ProcessedVideoDisplay {...defaultProps} connectionStatus="connected" />
    );

    expect(screen.getByText("Video Quality & Performance")).toBeInTheDocument();
    expect(screen.getByText("Real-time Stats")).toBeInTheDocument();
    expect(screen.getByText("Processing Stats")).toBeInTheDocument();
    expect(screen.getByText("Connection Health")).toBeInTheDocument();
  });

  test("displays system health indicators", () => {
    render(
      <ProcessedVideoDisplay {...defaultProps} connectionStatus="connected" />
    );

    expect(screen.getByText("System Health")).toBeInTheDocument();
    expect(screen.getByText("WebSocket")).toBeInTheDocument();
    expect(screen.getByText("Video Stream")).toBeInTheDocument();
    expect(screen.getByText("Latency")).toBeInTheDocument();
    expect(screen.getByText("Detection")).toBeInTheDocument();
  });

  test("displays MediaPipe landmarks when frame data available", () => {
    const processedFrameData = {
      type: "processed_frame",
      timestamp: "2024-08-20T10:30:00.000Z",
      frame_data: "data:image/jpeg;base64,testdata",
      metadata: {
        frame_number: 1,
        processing_time_ms: 16.7,
        landmarks_detected: {
          hands: true,
          face: false,
          pose: true,
        },
      },
    };

    render(
      <ProcessedVideoDisplay
        {...defaultProps}
        connectionStatus="connected"
        processedFrameData={processedFrameData}
      />
    );

    expect(screen.getByText("MediaPipe Detection Status")).toBeInTheDocument();
    expect(screen.getByText("Hands")).toBeInTheDocument();
    expect(screen.getByText("Face")).toBeInTheDocument();
    expect(screen.getByText("Pose")).toBeInTheDocument();
  });

  test("handles missing frame data gracefully", () => {
    const incompleteFrame = {
      type: "processed_frame",
      timestamp: "2024-08-20T10:30:00.000Z",
      // Missing frame_data
      metadata: {
        frame_number: 1,
        processing_time_ms: 16.7,
      },
    };

    render(
      <ProcessedVideoDisplay
        {...defaultProps}
        connectionStatus="connected"
        processedFrameData={incompleteFrame}
      />
    );

    // Should still render without crashing
    expect(screen.getByText("Video Quality & Performance")).toBeInTheDocument();
  });
});
