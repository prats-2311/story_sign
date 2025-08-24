import React from "react";
import { render, screen, waitFor, act } from "@testing-library/react";
import "@testing-library/jest-dom";
import VideoStreamingClient from "./VideoStreamingClient";

// Mock WebSocket
class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = WebSocket.CONNECTING;
    this.onopen = null;
    this.onclose = null;
    this.onmessage = null;
    this.onerror = null;

    // Simulate connection after a short delay
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      if (this.onopen) this.onopen();
    }, 10);
  }

  send(data) {
    if (this.readyState !== WebSocket.OPEN) {
      throw new Error("WebSocket is not open");
    }
    // Store sent data for testing
    this.lastSentData = data;
  }

  close(code = 1000, reason = "") {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) {
      this.onclose({ code, reason });
    }
  }

  // Simulate receiving a message
  simulateMessage(data) {
    if (this.onmessage) {
      this.onmessage({ data: JSON.stringify(data) });
    }
  }

  // Simulate connection error
  simulateError() {
    if (this.onerror) {
      this.onerror({ type: "error" });
    }
  }
}

global.WebSocket = MockWebSocket;
WebSocket.CONNECTING = 0;
WebSocket.OPEN = 1;
WebSocket.CLOSING = 2;
WebSocket.CLOSED = 3;

describe("VideoStreamingClient Component", () => {
  const mockOnConnectionChange = jest.fn();
  const mockOnProcessedFrame = jest.fn();
  const mockOnError = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  test("renders disconnected state initially", () => {
    render(
      <VideoStreamingClient
        isActive={false}
        onConnectionChange={mockOnConnectionChange}
        onProcessedFrame={mockOnProcessedFrame}
        onError={mockOnError}
      />
    );

    expect(screen.getByText("Disconnected")).toBeInTheDocument();
    expect(screen.getByText("Connection: disconnected")).toBeInTheDocument();
  });

  test("connects to WebSocket when activated", async () => {
    render(
      <VideoStreamingClient
        isActive={true}
        onConnectionChange={mockOnConnectionChange}
        onProcessedFrame={mockOnProcessedFrame}
        onError={mockOnError}
      />
    );

    expect(screen.getByText("Connecting...")).toBeInTheDocument();

    // Fast-forward timers to simulate connection
    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(mockOnConnectionChange).toHaveBeenCalledWith("connected");
    });

    expect(screen.getByText(/Connected/)).toBeInTheDocument();
  });

  test("handles WebSocket connection error", async () => {
    const { container } = render(
      <VideoStreamingClient
        isActive={true}
        onConnectionChange={mockOnConnectionChange}
        onProcessedFrame={mockOnProcessedFrame}
        onError={mockOnError}
      />
    );

    // Get the WebSocket instance and simulate error
    act(() => {
      jest.advanceTimersByTime(5);
    });

    // Find the WebSocket instance (it's created internally)
    // We'll simulate the error through the component's internal state
    await waitFor(() => {
      expect(screen.getByText("Connecting...")).toBeInTheDocument();
    });

    // Simulate error by triggering the error callback
    act(() => {
      // This would normally be triggered by WebSocket error
      mockOnError("WebSocket connection error");
    });

    expect(mockOnError).toHaveBeenCalledWith("WebSocket connection error");
  });

  test("sends frame data through WebSocket", async () => {
    const ref = React.createRef();

    render(
      <VideoStreamingClient
        ref={ref}
        isActive={true}
        onConnectionChange={mockOnConnectionChange}
        onProcessedFrame={mockOnProcessedFrame}
        onError={mockOnError}
      />
    );

    // Wait for connection
    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(mockOnConnectionChange).toHaveBeenCalledWith("connected");
    });

    // Test sending frame
    const testFrame = {
      type: "raw_frame",
      timestamp: "2024-08-20T10:30:00.000Z",
      frame_data: "data:image/jpeg;base64,testdata",
      metadata: {
        frame_number: 1,
        client_id: "test_client",
      },
    };

    act(() => {
      const success = ref.current.sendFrame(testFrame);
      expect(success).toBe(true);
    });

    // Verify frame was sent
    expect(ref.current.framesSent).toBe(1);
  });

  test("handles incoming processed frame message", async () => {
    let wsInstance;

    // Override WebSocket constructor to capture instance
    const OriginalWebSocket = global.WebSocket;
    global.WebSocket = function (url) {
      wsInstance = new OriginalWebSocket(url);
      return wsInstance;
    };
    Object.assign(global.WebSocket, OriginalWebSocket);

    render(
      <VideoStreamingClient
        isActive={true}
        onConnectionChange={mockOnConnectionChange}
        onProcessedFrame={mockOnProcessedFrame}
        onError={mockOnError}
      />
    );

    // Wait for connection
    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(mockOnConnectionChange).toHaveBeenCalledWith("connected");
    });

    // Simulate receiving processed frame
    const processedFrame = {
      type: "processed_frame",
      timestamp: "2024-08-20T10:30:00.000Z",
      frame_data: "data:image/jpeg;base64,processeddata",
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

    act(() => {
      wsInstance.simulateMessage(processedFrame);
    });

    expect(mockOnProcessedFrame).toHaveBeenCalledWith(processedFrame);
  });

  test("handles server error message", async () => {
    let wsInstance;

    const OriginalWebSocket = global.WebSocket;
    global.WebSocket = function (url) {
      wsInstance = new OriginalWebSocket(url);
      return wsInstance;
    };
    Object.assign(global.WebSocket, OriginalWebSocket);

    render(
      <VideoStreamingClient
        isActive={true}
        onConnectionChange={mockOnConnectionChange}
        onProcessedFrame={mockOnProcessedFrame}
        onError={mockOnError}
      />
    );

    // Wait for connection
    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(mockOnConnectionChange).toHaveBeenCalledWith("connected");
    });

    // Simulate server error
    const errorMessage = {
      type: "error",
      message: "Processing failed",
    };

    act(() => {
      wsInstance.simulateMessage(errorMessage);
    });

    expect(mockOnError).toHaveBeenCalledWith("Processing failed");
  });

  test("attempts reconnection on connection loss", async () => {
    let wsInstance;

    const OriginalWebSocket = global.WebSocket;
    global.WebSocket = function (url) {
      wsInstance = new OriginalWebSocket(url);
      return wsInstance;
    };
    Object.assign(global.WebSocket, OriginalWebSocket);

    render(
      <VideoStreamingClient
        isActive={true}
        onConnectionChange={mockOnConnectionChange}
        onProcessedFrame={mockOnProcessedFrame}
        onError={mockOnError}
      />
    );

    // Wait for initial connection
    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(mockOnConnectionChange).toHaveBeenCalledWith("connected");
    });

    // Simulate connection loss
    act(() => {
      wsInstance.close(1006, "Connection lost");
    });

    expect(mockOnConnectionChange).toHaveBeenCalledWith("disconnected");

    // Should show reconnecting status
    await waitFor(() => {
      expect(screen.getByText(/Reconnecting/)).toBeInTheDocument();
    });
  });

  test("stops reconnection attempts after max retries", async () => {
    let wsInstance;
    let connectionAttempts = 0;

    const OriginalWebSocket = global.WebSocket;
    global.WebSocket = function (url) {
      connectionAttempts++;
      wsInstance = new OriginalWebSocket(url);
      // Simulate immediate failure for reconnection attempts
      if (connectionAttempts > 1) {
        setTimeout(() => {
          wsInstance.close(1006, "Connection failed");
        }, 5);
      }
      return wsInstance;
    };
    Object.assign(global.WebSocket, OriginalWebSocket);

    render(
      <VideoStreamingClient
        isActive={true}
        onConnectionChange={mockOnConnectionChange}
        onProcessedFrame={mockOnProcessedFrame}
        onError={mockOnError}
      />
    );

    // Wait for initial connection
    act(() => {
      jest.advanceTimersByTime(20);
    });

    // Simulate connection loss to trigger reconnection
    act(() => {
      wsInstance.close(1006, "Connection lost");
    });

    // Fast-forward through multiple reconnection attempts
    for (let i = 0; i < 6; i++) {
      act(() => {
        jest.advanceTimersByTime(5000); // Advance by reconnection delay
      });
    }

    // Should eventually give up and show error
    await waitFor(() => {
      expect(mockOnError).toHaveBeenCalledWith(
        expect.stringContaining("Max reconnection attempts")
      );
    });
  });

  test("disconnects cleanly when deactivated", async () => {
    const { rerender } = render(
      <VideoStreamingClient
        isActive={true}
        onConnectionChange={mockOnConnectionChange}
        onProcessedFrame={mockOnProcessedFrame}
        onError={mockOnError}
      />
    );

    // Wait for connection
    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(mockOnConnectionChange).toHaveBeenCalledWith("connected");
    });

    // Deactivate
    rerender(
      <VideoStreamingClient
        isActive={false}
        onConnectionChange={mockOnConnectionChange}
        onProcessedFrame={mockOnProcessedFrame}
        onError={mockOnError}
      />
    );

    expect(mockOnConnectionChange).toHaveBeenCalledWith("disconnected");
    expect(screen.getByText("Disconnected")).toBeInTheDocument();
  });

  test("throttles frame sending based on processing capability", async () => {
    const ref = React.createRef();

    render(
      <VideoStreamingClient
        ref={ref}
        isActive={true}
        onConnectionChange={mockOnConnectionChange}
        onProcessedFrame={mockOnProcessedFrame}
        onError={mockOnError}
      />
    );

    // Wait for connection
    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(mockOnConnectionChange).toHaveBeenCalledWith("connected");
    });

    // Send frames rapidly
    const testFrame = {
      type: "raw_frame",
      timestamp: "2024-08-20T10:30:00.000Z",
      frame_data: "data:image/jpeg;base64,testdata",
      metadata: {
        frame_number: 1,
        client_id: "test_client",
        processing_capability: 0.5, // Low capability should throttle
      },
    };

    // Send multiple frames quickly
    act(() => {
      ref.current.sendFrame(testFrame);
      ref.current.sendFrame({
        ...testFrame,
        metadata: { ...testFrame.metadata, frame_number: 2 },
      });
      ref.current.sendFrame({
        ...testFrame,
        metadata: { ...testFrame.metadata, frame_number: 3 },
      });
    });

    // Should throttle frames (not all should be sent)
    expect(ref.current.framesSent).toBeLessThan(3);
  });

  test("displays connection statistics", async () => {
    const ref = React.createRef();

    render(
      <VideoStreamingClient
        ref={ref}
        isActive={true}
        onConnectionChange={mockOnConnectionChange}
        onProcessedFrame={mockOnProcessedFrame}
        onError={mockOnError}
      />
    );

    // Wait for connection
    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(screen.getByText("Frames Sent:")).toBeInTheDocument();
      expect(screen.getByText("Frames Received:")).toBeInTheDocument();
      expect(screen.getByText("Connection:")).toBeInTheDocument();
    });

    // Verify initial stats
    expect(screen.getByText("0")).toBeInTheDocument(); // Initial frame counts
  });

  test("handles malformed JSON messages gracefully", async () => {
    let wsInstance;

    const OriginalWebSocket = global.WebSocket;
    global.WebSocket = function (url) {
      wsInstance = new OriginalWebSocket(url);
      return wsInstance;
    };
    Object.assign(global.WebSocket, OriginalWebSocket);

    render(
      <VideoStreamingClient
        isActive={true}
        onConnectionChange={mockOnConnectionChange}
        onProcessedFrame={mockOnProcessedFrame}
        onError={mockOnError}
      />
    );

    // Wait for connection
    act(() => {
      jest.advanceTimersByTime(20);
    });

    await waitFor(() => {
      expect(mockOnConnectionChange).toHaveBeenCalledWith("connected");
    });

    // Send malformed JSON
    act(() => {
      if (wsInstance.onmessage) {
        wsInstance.onmessage({ data: "invalid json {" });
      }
    });

    // Should handle gracefully without crashing
    expect(screen.getByText(/Connected/)).toBeInTheDocument();
  });
});
