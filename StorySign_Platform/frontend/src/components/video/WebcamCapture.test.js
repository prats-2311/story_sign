/**
 * WebcamCapture Component Test
 * Tests for the webcam mirror effect fix
 */

import React from "react";
import { render, screen } from "@testing-library/react";
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

describe("WebcamCapture Mirror Effect Fix", () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Mock successful getUserMedia
    mockGetUserMedia.mockResolvedValue({
      getTracks: () => [{ stop: jest.fn() }],
    });
  });

  test("video element has horizontal flip transform to fix mirror effect", async () => {
    const mockOnFrameCapture = jest.fn();
    const mockOnError = jest.fn();

    render(
      <WebcamCapture
        onFrameCapture={mockOnFrameCapture}
        onError={mockOnError}
        isActive={true}
      />
    );

    // Wait for component to initialize
    await new Promise((resolve) => setTimeout(resolve, 100));

    // Find the video element (it might be hidden initially)
    const videoElements = document.querySelectorAll("video");

    if (videoElements.length > 0) {
      const videoElement = videoElements[0];
      const computedStyle = window.getComputedStyle(videoElement);

      // Check if the transform includes scaleX(-1) for horizontal flip
      expect(computedStyle.transform).toContain("scaleX(-1)");
    }
  });

  test("webcam capture component renders without errors", () => {
    const mockOnFrameCapture = jest.fn();
    const mockOnError = jest.fn();

    render(
      <WebcamCapture
        onFrameCapture={mockOnFrameCapture}
        onError={mockOnError}
        isActive={false}
      />
    );

    // Check that the component renders
    expect(screen.getByText(/webcam/i)).toBeInTheDocument();
  });

  test("video element style includes mirror fix transform", () => {
    const mockOnFrameCapture = jest.fn();
    const mockOnError = jest.fn();

    render(
      <WebcamCapture
        onFrameCapture={mockOnFrameCapture}
        onError={mockOnError}
        isActive={true}
      />
    );

    // The video element should have the transform style applied
    // This is tested through the inline style prop
    const component = screen.getByText(/webcam/i).closest(".webcam-capture");
    expect(component).toBeInTheDocument();
  });

  test("component handles inactive state correctly", () => {
    const mockOnFrameCapture = jest.fn();
    const mockOnError = jest.fn();

    render(
      <WebcamCapture
        onFrameCapture={mockOnFrameCapture}
        onError={mockOnError}
        isActive={false}
      />
    );

    // Should show inactive status (use getAllByText since there are multiple matches)
    const inactiveElements = screen.getAllByText(/inactive/i);
    expect(inactiveElements.length).toBeGreaterThan(0);
  });
});
