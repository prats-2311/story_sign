/**
 * Unit tests for useWebcam hook
 */

import { renderHook, act } from "@testing-library/react";
import useWebcam from "./useWebcam";

// Mock navigator.mediaDevices
const mockGetUserMedia = jest.fn();
const mockEnumerateDevices = jest.fn();

Object.defineProperty(navigator, "mediaDevices", {
  writable: true,
  value: {
    getUserMedia: mockGetUserMedia,
    enumerateDevices: mockEnumerateDevices,
  },
});

// Mock performance.now
Object.defineProperty(window, "performance", {
  writable: true,
  value: {
    now: jest.fn(() => Date.now()),
  },
});

// Mock video track
const createMockVideoTrack = (settings = {}) => ({
  stop: jest.fn(),
  getSettings: jest.fn(() => ({
    deviceId: "mock-device-id",
    width: 640,
    height: 480,
    frameRate: 30,
    facingMode: "user",
    ...settings,
  })),
  label: "Mock Camera",
});

// Mock media stream
const createMockStream = (tracks = []) => ({
  getTracks: jest.fn(() => tracks),
  getVideoTracks: jest.fn(() => tracks.filter((t) => t.kind === "video")),
});

describe("useWebcam Hook", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetUserMedia.mockClear();
    mockEnumerateDevices.mockClear();
  });

  describe("Initial State", () => {
    test("should initialize with correct default state", () => {
      const { result } = renderHook(() => useWebcam());

      expect(result.current.stream).toBeNull();
      expect(result.current.isActive).toBe(false);
      expect(result.current.status).toBe("inactive");
      expect(result.current.error).toBeNull();
      expect(result.current.deviceInfo).toBeNull();
      expect(result.current.isInitializing).toBe(false);
      expect(result.current.hasError).toBe(false);
      expect(result.current.isReady).toBe(false);
    });

    test("should have correct performance stats initial state", () => {
      const { result } = renderHook(() => useWebcam());

      expect(result.current.performanceStats).toEqual({
        currentFPS: 0,
        adaptiveFPS: 30,
        droppedFrames: 0,
        processingCapability: 1.0,
        avgProcessingTime: 0,
      });
    });
  });

  describe("startWebcam", () => {
    test("should successfully start webcam with default constraints", async () => {
      const mockTrack = createMockVideoTrack();
      const mockStream = createMockStream([mockTrack]);
      mockGetUserMedia.mockResolvedValue(mockStream);

      const { result } = renderHook(() => useWebcam());

      await act(async () => {
        const success = await result.current.startWebcam();
        expect(success).toBe(true);
      });

      expect(result.current.isActive).toBe(true);
      expect(result.current.status).toBe("active");
      expect(result.current.stream).toBe(mockStream);
      expect(result.current.error).toBeNull();
      expect(result.current.deviceInfo).toEqual({
        deviceId: "mock-device-id",
        label: "Mock Camera",
        width: 640,
        height: 480,
        frameRate: 30,
        facingMode: "user",
      });
    });

    test("should handle permission denied error", async () => {
      const permissionError = new Error("Permission denied");
      permissionError.name = "NotAllowedError";
      mockGetUserMedia.mockRejectedValue(permissionError);

      const { result } = renderHook(() => useWebcam());

      await act(async () => {
        const success = await result.current.startWebcam();
        expect(success).toBe(false);
      });

      expect(result.current.status).toBe("error");
      expect(result.current.error).toEqual({
        type: "PERMISSION_DENIED",
        message:
          "Camera access denied. Please allow camera permissions in your browser settings and refresh the page.",
        userAction: "Check browser permissions and reload the page",
      });
    });

    test("should handle no device found error", async () => {
      const deviceError = new Error("No device found");
      deviceError.name = "NotFoundError";
      mockGetUserMedia.mockRejectedValue(deviceError);

      const { result } = renderHook(() => useWebcam());

      await act(async () => {
        const success = await result.current.startWebcam();
        expect(success).toBe(false);
      });

      expect(result.current.status).toBe("error");
      expect(result.current.error.type).toBe("NO_DEVICE_FOUND");
    });

    test("should handle device in use error", async () => {
      const deviceError = new Error("Device in use");
      deviceError.name = "NotReadableError";
      mockGetUserMedia.mockRejectedValue(deviceError);

      const { result } = renderHook(() => useWebcam());

      await act(async () => {
        const success = await result.current.startWebcam();
        expect(success).toBe(false);
      });

      expect(result.current.status).toBe("error");
      expect(result.current.error.type).toBe("DEVICE_IN_USE");
    });

    test("should fallback to basic constraints on OverconstrainedError", async () => {
      const constraintError = new Error("Constraints not supported");
      constraintError.name = "OverconstrainedError";

      const mockTrack = createMockVideoTrack();
      const mockStream = createMockStream([mockTrack]);

      mockGetUserMedia
        .mockRejectedValueOnce(constraintError)
        .mockResolvedValueOnce(mockStream);

      const { result } = renderHook(() => useWebcam());

      await act(async () => {
        const success = await result.current.startWebcam();
        expect(success).toBe(true);
      });

      expect(mockGetUserMedia).toHaveBeenCalledTimes(2);
      expect(result.current.status).toBe("active");
    });

    test("should handle browser not supported", async () => {
      // Temporarily remove getUserMedia support
      const originalGetUserMedia = navigator.mediaDevices.getUserMedia;
      delete navigator.mediaDevices.getUserMedia;

      const { result } = renderHook(() => useWebcam());

      await act(async () => {
        const success = await result.current.startWebcam();
        expect(success).toBe(false);
      });

      expect(result.current.status).toBe("error");
      expect(result.current.error.type).toBe("BROWSER_NOT_SUPPORTED");

      // Restore getUserMedia
      navigator.mediaDevices.getUserMedia = originalGetUserMedia;
    });
  });

  describe("stopWebcam", () => {
    test("should properly stop webcam and cleanup resources", async () => {
      const mockTrack = createMockVideoTrack();
      const mockStream = createMockStream([mockTrack]);
      mockGetUserMedia.mockResolvedValue(mockStream);

      const { result } = renderHook(() => useWebcam());

      // Start webcam first
      await act(async () => {
        await result.current.startWebcam();
      });

      expect(result.current.isActive).toBe(true);

      // Stop webcam
      act(() => {
        result.current.stopWebcam();
      });

      expect(mockTrack.stop).toHaveBeenCalled();
      expect(result.current.stream).toBeNull();
      expect(result.current.isActive).toBe(false);
      expect(result.current.status).toBe("inactive");
      expect(result.current.error).toBeNull();
      expect(result.current.deviceInfo).toBeNull();
    });
  });

  describe("attachToVideoElement", () => {
    test("should attach stream to video element", async () => {
      const mockTrack = createMockVideoTrack();
      const mockStream = createMockStream([mockTrack]);
      mockGetUserMedia.mockResolvedValue(mockStream);

      const { result } = renderHook(() => useWebcam());

      // Start webcam first
      await act(async () => {
        await result.current.startWebcam();
      });

      const mockVideoElement = {
        srcObject: null,
        onloadedmetadata: null,
        play: jest.fn().mockResolvedValue(),
      };

      act(() => {
        const success = result.current.attachToVideoElement(mockVideoElement);
        expect(success).toBe(true);
      });

      expect(mockVideoElement.srcObject).toBe(mockStream);
    });

    test("should return false when no stream available", () => {
      const { result } = renderHook(() => useWebcam());

      const mockVideoElement = {
        srcObject: null,
        onloadedmetadata: null,
        play: jest.fn(),
      };

      act(() => {
        const success = result.current.attachToVideoElement(mockVideoElement);
        expect(success).toBe(false);
      });

      expect(mockVideoElement.srcObject).toBeNull();
    });
  });

  describe("captureFrame", () => {
    test("should return null when webcam is not active", () => {
      const { result } = renderHook(() => useWebcam());

      const mockVideoElement = document.createElement("video");

      act(() => {
        const frame = result.current.captureFrame(mockVideoElement);
        expect(frame).toBeNull();
      });
    });

    test("should capture frame when webcam is active", async () => {
      const mockTrack = createMockVideoTrack();
      const mockStream = createMockStream([mockTrack]);
      mockGetUserMedia.mockResolvedValue(mockStream);

      // Mock canvas and context
      const mockCanvas = {
        width: 0,
        height: 0,
        getContext: jest.fn(() => ({
          drawImage: jest.fn(),
        })),
        toDataURL: jest.fn(() => "data:image/jpeg;base64,mock-data"),
      };

      const originalCreateElement = document.createElement;
      document.createElement = jest.fn((tagName) => {
        if (tagName === "canvas") {
          return mockCanvas;
        }
        return originalCreateElement.call(document, tagName);
      });

      const { result } = renderHook(() => useWebcam());

      // Start webcam first
      await act(async () => {
        await result.current.startWebcam();
      });

      const mockVideoElement = document.createElement("video");

      act(() => {
        const frame = result.current.captureFrame(mockVideoElement);
        expect(frame).toEqual({
          frameData: "data:image/jpeg;base64,mock-data",
          timestamp: expect.any(String),
          width: 320,
          height: 240,
          processingTime: expect.any(Number),
          quality: expect.any(Number),
          frameNumber: expect.any(Number),
        });
      });

      // Restore original createElement
      document.createElement = originalCreateElement;
    });
  });

  describe("getAvailableDevices", () => {
    test("should return available video input devices", async () => {
      const mockDevices = [
        { kind: "videoinput", deviceId: "camera1", label: "Camera 1" },
        { kind: "audioinput", deviceId: "mic1", label: "Microphone 1" },
        { kind: "videoinput", deviceId: "camera2", label: "Camera 2" },
      ];

      mockEnumerateDevices.mockResolvedValue(mockDevices);

      const { result } = renderHook(() => useWebcam());

      await act(async () => {
        const devices = await result.current.getAvailableDevices();
        expect(devices).toEqual([
          { kind: "videoinput", deviceId: "camera1", label: "Camera 1" },
          { kind: "videoinput", deviceId: "camera2", label: "Camera 2" },
        ]);
      });
    });

    test("should handle enumerate devices error", async () => {
      mockEnumerateDevices.mockRejectedValue(new Error("Enumeration failed"));

      const { result } = renderHook(() => useWebcam());

      await act(async () => {
        const devices = await result.current.getAvailableDevices();
        expect(devices).toEqual([]);
      });
    });
  });

  describe("switchCamera", () => {
    test("should switch to different camera device", async () => {
      const mockTrack1 = createMockVideoTrack({ deviceId: "camera1" });
      const mockStream1 = createMockStream([mockTrack1]);
      const mockTrack2 = createMockVideoTrack({ deviceId: "camera2" });
      const mockStream2 = createMockStream([mockTrack2]);

      mockGetUserMedia
        .mockResolvedValueOnce(mockStream1)
        .mockResolvedValueOnce(mockStream2);

      const { result } = renderHook(() => useWebcam());

      // Start with first camera
      await act(async () => {
        await result.current.startWebcam();
      });

      expect(result.current.deviceInfo.deviceId).toBe("camera1");

      // Switch to second camera
      await act(async () => {
        const success = await result.current.switchCamera("camera2");
        expect(success).toBe(true);
      });

      expect(mockTrack1.stop).toHaveBeenCalled();
      expect(result.current.deviceInfo.deviceId).toBe("camera2");
    });
  });

  describe("Cleanup", () => {
    test("should cleanup resources on unmount", async () => {
      const mockTrack = createMockVideoTrack();
      const mockStream = createMockStream([mockTrack]);
      mockGetUserMedia.mockResolvedValue(mockStream);

      const { result, unmount } = renderHook(() => useWebcam());

      // Start webcam
      await act(async () => {
        await result.current.startWebcam();
      });

      expect(result.current.isActive).toBe(true);

      // Unmount component
      unmount();

      expect(mockTrack.stop).toHaveBeenCalled();
    });
  });

  describe("Performance Metrics", () => {
    test("should track performance metrics during frame capture", async () => {
      const mockTrack = createMockVideoTrack();
      const mockStream = createMockStream([mockTrack]);
      mockGetUserMedia.mockResolvedValue(mockStream);

      const { result } = renderHook(() => useWebcam());

      await act(async () => {
        await result.current.startWebcam();
      });

      expect(result.current.performanceStats.adaptiveFPS).toBe(30);
      expect(result.current.performanceStats.processingCapability).toBe(1.0);
    });
  });
});
