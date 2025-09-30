import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe, toHaveNoViolations } from "jest-axe";
import VideoDisplayPanel from "./VideoDisplayPanel";

expect.extend(toHaveNoViolations);

// Mock MediaDevices API
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
  value: jest.fn().mockResolvedValue(undefined),
});

Object.defineProperty(HTMLVideoElement.prototype, "pause", {
  writable: true,
  value: jest.fn(),
});

describe("VideoDisplayPanel Accessibility Tests", () => {
  const mockStream = {
    getTracks: () => [{ stop: jest.fn() }],
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders with proper ARIA attributes", () => {
    render(
      <VideoDisplayPanel
        stream={mockStream}
        ariaLabel="ASL practice video feed"
      />
    );

    const video = screen.getByLabelText("ASL practice video feed");
    expect(video).toBeInTheDocument();
    expect(video).toHaveAttribute("aria-label", "ASL practice video feed");
  });

  test("announces status changes to screen readers", async () => {
    const { rerender } = render(<VideoDisplayPanel stream={null} />);

    // Should announce when stream connects
    rerender(<VideoDisplayPanel stream={mockStream} />);

    await waitFor(() => {
      expect(screen.getByText("Video stream connecting")).toBeInTheDocument();
    });

    // Should announce when stream disconnects
    rerender(<VideoDisplayPanel stream={null} />);

    await waitFor(() => {
      expect(screen.getByText("Video stream disconnected")).toBeInTheDocument();
    });
  });

  test("provides appropriate status messages", () => {
    const { rerender } = render(<VideoDisplayPanel stream={null} />);

    // No stream state
    expect(screen.getByText("No video stream available")).toBeInTheDocument();

    // Loading state
    rerender(<VideoDisplayPanel stream={mockStream} />);
    expect(
      screen.getByText("Connecting to video stream...")
    ).toBeInTheDocument();
  });

  test("handles video events and announces changes", async () => {
    render(<VideoDisplayPanel stream={mockStream} />);

    const video = screen.getByRole("generic", { hidden: true }); // video element

    // Simulate video ready
    fireEvent.loadedData(video);

    await waitFor(() => {
      expect(screen.getByText("Video stream ready")).toBeInTheDocument();
    });

    // Simulate video play
    fireEvent.play(video);

    await waitFor(() => {
      expect(screen.getByText("Video stream playing")).toBeInTheDocument();
    });

    // Simulate video pause
    fireEvent.pause(video);

    await waitFor(() => {
      expect(screen.getByText("Video stream paused")).toBeInTheDocument();
    });
  });

  test("handles video errors gracefully", async () => {
    const onError = jest.fn();
    render(<VideoDisplayPanel stream={mockStream} onError={onError} />);

    const video = screen.getByRole("generic", { hidden: true });

    fireEvent.error(video, { target: { error: new Error("Video error") } });

    await waitFor(() => {
      expect(screen.getByText("Video stream error")).toBeInTheDocument();
      expect(
        screen.getByText("Video stream error occurred")
      ).toBeInTheDocument();
    });

    expect(onError).toHaveBeenCalled();
  });

  test("capture button is accessible", async () => {
    const user = userEvent.setup();
    const onFrameCapture = jest.fn();

    render(
      <VideoDisplayPanel
        stream={mockStream}
        showControls={true}
        onFrameCapture={onFrameCapture}
      />
    );

    // Simulate video playing state
    const video = screen.getByRole("generic", { hidden: true });
    fireEvent.loadedData(video);
    fireEvent.play(video);

    await waitFor(() => {
      const captureButton = screen.getByLabelText("Capture current frame");
      expect(captureButton).toBeInTheDocument();
      expect(captureButton).not.toBeDisabled();
    });

    const captureButton = screen.getByLabelText("Capture current frame");

    // Test keyboard activation
    captureButton.focus();
    await user.keyboard("{Enter}");

    expect(onFrameCapture).toHaveBeenCalled();
  });

  test("capture button is disabled when video not playing", () => {
    render(
      <VideoDisplayPanel
        stream={null}
        showControls={true}
        onFrameCapture={jest.fn()}
      />
    );

    const captureButton = screen.getByLabelText("Capture current frame");
    expect(captureButton).toBeDisabled();
  });

  test("hides overlay canvas from screen readers", () => {
    render(
      <VideoDisplayPanel stream={mockStream} overlayData={{ landmarks: [] }} />
    );

    const overlayCanvas = document.querySelector(".overlay-canvas");
    expect(overlayCanvas).toHaveAttribute("aria-hidden", "true");
  });

  test("hides capture canvas from screen readers", () => {
    render(<VideoDisplayPanel stream={mockStream} />);

    const captureCanvas = document.querySelector(".capture-canvas");
    expect(captureCanvas).toHaveAttribute("aria-hidden", "true");
  });

  test("passes axe accessibility tests", async () => {
    const { container } = render(
      <VideoDisplayPanel
        stream={mockStream}
        showControls={true}
        ariaLabel="Test video display"
      />
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  test("supports custom dimensions", () => {
    render(<VideoDisplayPanel stream={mockStream} width={800} height={600} />);

    const video = screen.getByRole("generic", { hidden: true });
    expect(video).toHaveAttribute("width", "800");
    expect(video).toHaveAttribute("height", "600");
  });

  test("calls onVideoReady callback", async () => {
    const onVideoReady = jest.fn();

    render(
      <VideoDisplayPanel stream={mockStream} onVideoReady={onVideoReady} />
    );

    const video = screen.getByRole("generic", { hidden: true });
    fireEvent.loadedData(video);

    await waitFor(() => {
      expect(onVideoReady).toHaveBeenCalled();
    });
  });

  test("renders children content", () => {
    render(
      <VideoDisplayPanel stream={mockStream}>
        <div data-testid="child-content">Child content</div>
      </VideoDisplayPanel>
    );

    expect(screen.getByTestId("child-content")).toBeInTheDocument();
  });

  test("applies custom className", () => {
    render(
      <VideoDisplayPanel stream={mockStream} className="custom-video-panel" />
    );

    const container = document.querySelector(".video-display-panel");
    expect(container).toHaveClass("custom-video-panel");
  });

  test("handles MediaPipe overlay data", () => {
    const overlayData = {
      landmarks: [
        { x: 0.5, y: 0.5 },
        { x: 0.3, y: 0.7 },
      ],
      connections: [{ start: 0, end: 1 }],
    };

    render(<VideoDisplayPanel stream={mockStream} overlayData={overlayData} />);

    const overlayCanvas = document.querySelector(".overlay-canvas");
    expect(overlayCanvas).toBeInTheDocument();
  });

  test("live region announcements are properly structured", async () => {
    render(<VideoDisplayPanel stream={mockStream} />);

    const liveRegion = document.querySelector('[aria-live="polite"]');
    expect(liveRegion).toBeInTheDocument();
    expect(liveRegion).toHaveAttribute("aria-atomic", "true");

    // Should contain announcement
    await waitFor(() => {
      expect(liveRegion).toHaveTextContent("Video stream connecting");
    });
  });
});
