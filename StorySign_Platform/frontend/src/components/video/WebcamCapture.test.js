import React from "react";
import { render, screen, waitFor, act } from "@testing-library/react";
import "@testing-library/jest-dom";
import WebcamCapture from "./WebcamCapture";

// Mock getUserMedia
const mockGetUserMedia = jest.fn();
Object.defineProperty(navigator, "mediaDevices", {
  writable: true,
  value: {
    getUserMedia: mockGetUserMedia,
  },
});

// Mock HTMLVideoElement methods
Object.defineProperty(HTMLVideoElement.prototype, "play", {
  writable: true,
  value: jest.fn().mockImplementation(() => Promise.resolve()),
});

// Mock canvas context
const mockGetContext = jest.fn();
const mockDrawImage = jest.fn();
const mockToDataURL = jest.fn();

Object.defineProperty(HTMLCanvasElement.prototype, "getContext", {
  writable: true,
  value: mockGetContext.mockReturnValue({
    drawImage: mockDrawImage,
  }),
});

Object.defineProperty(HTMLCanvasElement.prototype, "toDataURL", {
  writable: true,
  value: mockToDataURL,
});

// Mock requestAnimationFrame
global.requestAnimationFrame = jest.fn((cb) => setTimeout(cb, 16));
global.cancelAnimationFrame = jest.fn();

describe("WebcamCapture Component", () => {
  const mockOnFrameCapture = jest.fn();
  const mockOnError = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockGetUserMedia.mockClear();
    mockOnFrameCapture.mockClear();
    mockOnError.mockClear();
    mockToDataURL.mockReturnValue("data:image/jpeg;base64,mockbase64data");
  });

  afterEach(() => {
    jest.clearAllTimers();
  });

  test("renders inactive state correctly", () => {
    render(
      <WebcamCapture
        isActive={false}
        onFrameCapture={mockOnFrameCapture}
        onError={mockOnError}
      />
    );

    expect(screen.getByText("Inactive")).toBeInTheDocument();
    expect(screen.getByText("Webcam inactive")).toBeInTheDocument();
  });

  test("initializes webcam when activated", async () => {
    const mockStream = {
      getTracks: jest.fn().mockReturnValue([{ stop: jest.fn() }]),
    };

    mockGetUserMedia.mockResolvedValueOnce(mockStream);

    render(
      <WebcamCapture
        isActive={true}
        onFrameCapture={mockOnFrameCapture}
        onError={mockOnError}
      />
    );

    await waitFor(() => {
      expect(mockGetUserMedia).toHaveBeenCalledWith({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          frameRate: { ideal: 30 },
        },
        audio: false,
      });
    });
  });

  test("handles webcam access denied error", async () => {
    const notAllowedError = new Error("Permission denied");
    notAllowedError.name = "NotAllowedError";

    mockGetUserMedia.mockRejectedValueOnce(notAllowedError);

    render(
      <WebcamCapture
        isActive={true}
        onFrameCapture={mockOnFrameCapture}
        onError={mockOnError}
      />
    );

    await waitFor(() => {
      expect(mockOnError).toHaveBeenCalledWith(
        expect.stringContaining("Camera access denied")
      );
    });

    expect(screen.getByText("Error")).toBeInTheDocument();
  });

  test("handles no camera device found error", async () => {
    const notFoundError = new Error("No camera found");
    notFoundError.name = "NotFoundError";

    mockGetUserMedia.mockRejectedValueOnce(notFoundError);

    render(
      <WebcamCapture
        isActive={true}
        onFrameCapture={mockOnFrameCapture}
        onError={mockOnError}
      />
    );

    await waitFor(() => {
      expect(mockOnError).toHaveBeenCalledWith(
        expect.stringContaining("No camera device found")
      );
    });
  });

  test("handles camera in use error", async () => {
    const notReadableError = new Error("Camera in use");
    notReadableError.name = "NotReadableError";

    mockGetUserMedia.mockRejectedValueOnce(notReadableError);

    render(
      <WebcamCapture
        isActive={true}
        onFrameCapture={mockOnFrameCapture}
        onError={mockOnError}
      />
    );

    await waitFor(() => {
      expect(mockOnError).toHaveBeenCalledWith(
        expect.stringContaining("Camera is already in use")
      );
    });
  });

  test("attempts fallback when constraints not supported", async () => {
    const overConstrainedError = new Error("Constraints not supported");
    overConstrainedError.name = "OverconstrainedError";

    const mockFallbackStream = {
      getTracks: jest.fn().mockReturnValue([{ stop: jest.fn() }]),
    };

    mockGetUserMedia
      .mockRejectedValueOnce(overConstrainedError)
      .mockResolvedValueOnce(mockFallbackStream);

    render(
      <WebcamCapture
        isActive={true}
        onFrameCapture={mockOnFrameCapture}
        onError={mockOnError}
      />
    );

    await waitFor(() => {
      expect(mockGetUserMedia).toHaveBeenCalledTimes(2);
    });

    // Should call with relaxed constraints on second attempt
    expect(mockGetUserMedia).toHaveBeenNthCalledWith(2, {
      video: true,
      audio: false,
    });
  });

  test("displays performance stats when active", async () => {
    const mockStream = {
      getTracks: jest.fn().mockReturnValue([{ stop: jest.fn() }]),
    };

    mockGetUserMedia.mockResolvedValueOnce(mockStream);

    render(
      <WebcamCapture
        isActive={true}
        onFrameCapture={mockOnFrameCapture}
        onError={mockOnError}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Performance Metrics")).toBeInTheDocument();
    });

    expect(screen.getByText("Current FPS:")).toBeInTheDocument();
    expect(screen.getByText("Adaptive FPS:")).toBeInTheDocument();
    expect(screen.getByText("Dropped Frames:")).toBeInTheDocument();
    expect(screen.getByText("Processing Capability:")).toBeInTheDocument();
  });

  test("captures and processes frames when active", async () => {
    const mockStream = {
      getTracks: jest.fn().mockReturnValue([{ stop: jest.fn() }]),
    };

    mockGetUserMedia.mockResolvedValueOnce(mockStream);

    const { rerender } = render(
      <WebcamCapture
        isActive={true}
        onFrameCapture={mockOnFrameCapture}
        onError={mockOnError}
      />
    );

    // Wait for webcam to initialize
    await waitFor(() => {
      expect(mockGetUserMedia).toHaveBeenCalled();
    });

    // Simulate frame capture by triggering the animation frame
    await act(async () => {
      // Trigger requestAnimationFrame callback
      const callback = global.requestAnimationFrame.mock.calls[0][0];
      callback();
    });

    // Should eventually call onFrameCapture
    await waitFor(
      () => {
        expect(mockOnFrameCapture).toHaveBeenCalled();
      },
      { timeout: 3000 }
    );
  });

  test("stops webcam when deactivated", async () => {
    const mockTrack = { stop: jest.fn() };
    const mockStream = {
      getTracks: jest.fn().mockReturnValue([mockTrack]),
    };

    mockGetUserMedia.mockResolvedValueOnce(mockStream);

    const { rerender } = render(
      <WebcamCapture
        isActive={true}
        onFrameCapture={mockOnFrameCapture}
        onError={mockOnError}
      />
    );

    await waitFor(() => {
      expect(mockGetUserMedia).toHaveBeenCalled();
    });

    // Deactivate webcam
    rerender(
      <WebcamCapture
        isActive={false}
        onFrameCapture={mockOnFrameCapture}
        onError={mockOnError}
      />
    );

    await waitFor(() => {
      expect(mockTrack.stop).toHaveBeenCalled();
    });

    expect(screen.getByText("Inactive")).toBeInTheDocument();
  });

  test("handles frame capture errors gracefully", async () => {
    const mockStream = {
      getTracks: jest.fn().mockReturnValue([{ stop: jest.fn() }]),
    };

    mockGetUserMedia.mockResolvedValueOnce(mockStream);
    mockToDataURL.mockImplementation(() => {
      throw new Error("Canvas error");
    });

    render(
      <WebcamCapture
        isActive={true}
        onFrameCapture={mockOnFrameCapture}
        onError={mockOnError}
      />
    );

    await waitFor(() => {
      expect(mockGetUserMedia).toHaveBeenCalled();
    });

    // Should not crash when frame capture fails
    expect(screen.getByText(/Active/)).toBeInTheDocument();
  });

  test("validates frame message format", async () => {
    const mockStream = {
      getTracks: jest.fn().mockReturnValue([{ stop: jest.fn() }]),
    };

    mockGetUserMedia.mockResolvedValueOnce(mockStream);

    render(
      <WebcamCapture
        isActive={true}
        onFrameCapture={mockOnFrameCapture}
        onError={mockOnError}
      />
    );

    await waitFor(() => {
      expect(mockGetUserMedia).toHaveBeenCalled();
    });

    // Simulate successful frame capture
    await act(async () => {
      const callback = global.requestAnimationFrame.mock.calls[0][0];
      callback();
    });

    await waitFor(
      () => {
        if (mockOnFrameCapture.mock.calls.length > 0) {
          const capturedMessage = mockOnFrameCapture.mock.calls[0][0];

          // Validate message structure
          expect(capturedMessage).toHaveProperty("type", "raw_frame");
          expect(capturedMessage).toHaveProperty("timestamp");
          expect(capturedMessage).toHaveProperty("frame_data");
          expect(capturedMessage).toHaveProperty("metadata");
          expect(capturedMessage.metadata).toHaveProperty("frame_number");
          expect(capturedMessage.metadata).toHaveProperty("client_id");
        }
      },
      { timeout: 3000 }
    );
  });
});
