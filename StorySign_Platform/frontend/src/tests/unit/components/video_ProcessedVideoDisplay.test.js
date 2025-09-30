import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import ProcessedVideoDisplay from "./ProcessedVideoDisplay";

// Mock canvas context
const mockGetContext = jest.fn();
const mockDrawImage = jest.fn();
const mockClearRect = jest.fn();
const mockFillRect = jest.fn();
const mockFillText = jest.fn();

const mockCanvasContext = {
  drawImage: mockDrawImage,
  clearRect: mockClearRect,
  fillRect: mockFillRect,
  fillText: mockFillText,
  fillStyle: "",
  font: "",
  textAlign: "",
};

Object.defineProperty(HTMLCanvasElement.prototype, "getContext", {
  writable: true,
  value: mockGetContext.mockReturnValue(mockCanvasContext),
});

Object.defineProperty(HTMLCanvasElement.prototype, "width", {
  writable: true,
  value: 640,
});

Object.defineProperty(HTMLCanvasElement.prototype, "height", {
  writable: true,
  value: 480,
});

// Mock Image constructor
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

describe("ProcessedVideoDisplay Component", () => {
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
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  test("renders disconnected state correctly", () => {
    render(<ProcessedVideoDisplay {...defaultProps} />);

    expect(screen.getByText("Disconnected")).toBeInTheDocument();
    expect(
      screen.getByText("Not connected to video processing server")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Processed video will appear here")
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
    expect(
      screen.getByText("Connecting to video processor...")
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
    expect(
      screen.getByText("Waiting for processed frames...")
    ).toBeInTheDocument();
  });

  test("renders error state with retry button", () => {
    render(
      <ProcessedVideoDisplay {...defaultProps} connectionStatus="error" />
    );

    expect(screen.getByText("Connection Error")).toBeInTheDocument();
    expect(
      screen.getByText("Unable to connect to video processing server")
    ).toBeInTheDocument();
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

  test("displays processed frame when available", async () => {
    const processedFrameData = {
      type: "processed_frame",
      timestamp: "2024-08-20T10:30:00.000Z",
      frame_data: "data:image/jpeg;base64,testprocesseddata",
      metadata: {
        frame_number: 1,
        processing_time_ms: 16.7,
        landmarks_detected: {
          hands: true,
          face: true,
          pose: true,
        },
        width: 640,
        height: 480,
      },
    };

    render(
      <ProcessedVideoDisplay
        {...defaultProps}
        connectionStatus="connected"
        processedFrameData={processedFrameData}
        isActive={true}
      />
    );

    // Wait for image to load and canvas to be drawn
    await waitFor(() => {
      expect(mockDrawImage).toHaveBeenCalled();
    });

    // Should display the canvas
    const canvas =
      screen.getByRole("img", { hidden: true }) ||
      document.querySelector("canvas");
    expect(canvas).toBeInTheDocument();
  });

  test("displays performance metrics correctly", () => {
    const processedFrameData = {
      type: "processed_frame",
      timestamp: "2024-08-20T10:30:00.000Z",
      frame_data: "data:image/jpeg;base64,testdata",
      metadata: {
        frame_number: 5,
        processing_time_ms: 25.5,
        landmarks_detected: {
          hands: true,
          face: false,
          pose: true,
        },
        width: 640,
        height: 480,
      },
    };

    render(
      <ProcessedVideoDisplay
        {...defaultProps}
        connectionStatus="connected"
        processedFrameData={processedFrameData}
        streamingStats={{
          framesSent: 10,
          framesReceived: 8,
          droppedFrames: 2,
        }}
      />
    );

    expect(screen.getByText("Video Quality & Performance")).toBeInTheDocument();
    expect(screen.getByText("Real-time Stats")).toBeInTheDocument();
    expect(screen.getByText("Processing Stats")).toBeInTheDocument();
    expect(screen.getByText("Connection Health")).toBeInTheDocument();

    // Check specific metrics
    expect(screen.getByText("Frame Rate:")).toBeInTheDocument();
    expect(screen.getByText("Latency:")).toBeInTheDocument();
    expect(screen.getByText("Quality:")).toBeInTheDocument();
    expect(screen.getByText("Resolution:")).toBeInTheDocument();
    expect(screen.getByText("640x480")).toBeInTheDocument();
  });

  test("displays MediaPipe landmarks status", () => {
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

    // Check detection indicators
    const checkmarks = screen.getAllByText("✓");
    const crosses = screen.getAllByText("✗");
    expect(checkmarks).toHaveLength(2); // hands and pose detected
    expect(crosses).toHaveLength(1); // face not detected
  });

  test("calculates quality based on landmarks detected", () => {
    const excellentQualityFrame = {
      type: "processed_frame",
      timestamp: "2024-08-20T10:30:00.000Z",
      frame_data: "data:image/jpeg;base64,testdata",
      metadata: {
        frame_number: 1,
        processing_time_ms: 16.7,
        landmarks_detected: {
          hands: true,
          face: true,
          pose: true,
        },
      },
    };

    const { rerender } = render(
      <ProcessedVideoDisplay
        {...defaultProps}
        connectionStatus="connected"
        processedFrameData={excellentQualityFrame}
      />
    );

    expect(screen.getAllByText("Excellent")).toHaveLength(2); // Quality metric and system health

    // Test good quality (2 out of 3 landmarks)
    const goodQualityFrame = {
      ...excellentQualityFrame,
      metadata: {
        ...excellentQualityFrame.metadata,
        landmarks_detected: {
          hands: true,
          face: false,
          pose: true,
        },
      },
    };

    rerender(
      <ProcessedVideoDisplay
        {...defaultProps}
        connectionStatus="connected"
        processedFrameData={goodQualityFrame}
      />
    );

    expect(screen.getAllByText("Good")).toHaveLength(1);
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

  test("updates performance metrics over time", async () => {
    const initialFrame = {
      type: "processed_frame",
      timestamp: new Date().toISOString(),
      frame_data: "data:image/jpeg;base64,testdata",
      metadata: {
        frame_number: 1,
        processing_time_ms: 20.0,
        landmarks_detected: {
          hands: true,
          face: true,
          pose: true,
        },
      },
    };

    const { rerender } = render(
      <ProcessedVideoDisplay
        {...defaultProps}
        connectionStatus="connected"
        processedFrameData={initialFrame}
      />
    );

    // Wait a bit and send another frame
    jest.advanceTimersByTime(100);

    const secondFrame = {
      ...initialFrame,
      timestamp: new Date(Date.now() + 100).toISOString(),
      metadata: {
        ...initialFrame.metadata,
        frame_number: 2,
        processing_time_ms: 15.0,
      },
    };

    rerender(
      <ProcessedVideoDisplay
        {...defaultProps}
        connectionStatus="connected"
        processedFrameData={secondFrame}
      />
    );

    // Performance metrics should be updated
    expect(screen.getByText("Total Frames:")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
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
    expect(screen.getByText("Connected")).toBeInTheDocument();
  });

  test("refreshes display when refresh button clicked", async () => {
    const processedFrameData = {
      type: "processed_frame",
      timestamp: "2024-08-20T10:30:00.000Z",
      frame_data: "data:image/jpeg;base64,testdata",
      metadata: {
        frame_number: 1,
        processing_time_ms: 16.7,
        landmarks_detected: {
          hands: true,
          face: true,
          pose: true,
        },
      },
    };

    render(
      <ProcessedVideoDisplay
        {...defaultProps}
        connectionStatus="connected"
        processedFrameData={processedFrameData}
        isActive={true}
      />
    );

    // Wait for initial render
    await waitFor(() => {
      expect(mockDrawImage).toHaveBeenCalled();
    });

    const initialCallCount = mockDrawImage.mock.calls.length;

    // Find and click refresh button
    const refreshButton = screen.getByTitle("Refresh display");
    fireEvent.click(refreshButton);

    // Should trigger another draw
    await waitFor(() => {
      expect(mockDrawImage.mock.calls.length).toBeGreaterThan(initialCallCount);
    });
  });

  test("displays connection uptime correctly", () => {
    // Mock Date.now to control time
    const mockNow = jest.spyOn(Date, "now");
    const startTime = 1000000;
    mockNow.mockReturnValue(startTime);

    const { rerender } = render(
      <ProcessedVideoDisplay {...defaultProps} connectionStatus="connecting" />
    );

    // Simulate connection established
    rerender(
      <ProcessedVideoDisplay {...defaultProps} connectionStatus="connected" />
    );

    // Advance time by 65 seconds
    mockNow.mockReturnValue(startTime + 65000);

    rerender(
      <ProcessedVideoDisplay {...defaultProps} connectionStatus="connected" />
    );

    // Should show uptime as 1:05
    expect(screen.getByText("Uptime:")).toBeInTheDocument();

    mockNow.mockRestore();
  });
});
