import { renderHook, act, waitFor } from "@testing-library/react";
import useWebcam from "./useWebcam";

// Mock navigator.mediaDevices
const mockGetUserMedia = jest.fn();
Object.defineProperty(navigator, "mediaDevices", {
  writable: true,
  value: {
    getUserMedia: mockGetUserMedia,
  },
});

describe("useWebcam Hook", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockGetUserMedia.mockClear();
  });

  describe("Initial State", () => {
    test("should return initial state", () => {
      const { result } = renderHook(() => useWebcam());

      expect(result.current.stream).toBeNull();
      expect(result.current.isActive).toBe(false);
      expect(result.current.status).toBe("inactive");
      expect(result.current.error).toBeNull();
      expect(typeof result.current.startWebcam).toBe("function");
      expect(typeof result.current.stopWebcam).toBe("function");
      expect(typeof result.current.captureFrame).toBe("function");
    });
  });

  describe("Starting Webcam", () => {
    test("should successfully start webcam", async () => {
      const mockTrack = {
        stop: jest.fn(),
        getSettings: jest.fn(() => ({ width: 640, height: 480 })),
      };
      const mockStream = {
        getTracks: () => [mockTrack],
        getVideoTracks: () => [mockTrack],
      };
      mockGetUserMedia.mockResolvedValue(mockStream);

      const { result } = renderHook(() => useWebcam());

      await act(async () => {
        const success = await result.current.startWebcam();
        expect(success).toBe(true);
      });

      expect(result.current.stream).toBe(mockStream);
      expect(result.current.isActive).toBe(true);
      expect(result.current.status).toBe("active");
      expect(result.current.error).toBeNull();
    });

    test("should handle webcam permission denied", async () => {
      const permissionError = new Error("Permission denied");
      permissionError.name = "NotAllowedError";
      mockGetUserMedia.mockRejectedValue(permissionError);

      const { result } = renderHook(() => useWebcam());

      await act(async () => {
        const success = await result.current.startWebcam();
        expect(success).toBe(false);
      });

      expect(result.current.stream).toBeNull();
      expect(result.current.isActive).toBe(false);
      expect(result.current.status).toBe("error");
      expect(result.current.error).toEqual({
        type: "PERMISSION_DENIED",
        message:
          "Camera access denied. Please allow camera permissions in your browser settings and refresh the page.",
        userAction: "Check browser permissions and reload the page",
      });
    });

    test("should handle webcam not found", async () => {
      const notFoundError = new Error("Device not found");
      notFoundError.name = "NotFoundError";
      mockGetUserMedia.mockRejectedValue(notFoundError);

      const { result } = renderHook(() => useWebcam());

      await act(async () => {
        const success = await result.current.startWebcam();
        expect(success).toBe(false);
      });

      expect(result.current.error).toEqual({
        type: "NO_DEVICE_FOUND",
        message:
          "No camera device found. Please connect a camera and try again.",
        userAction: "Connect a camera device and try again",
      });
    });

    test("should handle webcam in use by another application", async () => {
      const inUseError = new Error("Device in use");
      inUseError.name = "NotReadableError";
      mockGetUserMedia.mockRejectedValue(inUseError);

      const { result } = renderHook(() => useWebcam());

      await act(async () => {
        const success = await result.current.startWebcam();
        expect(success).toBe(false);
      });

      expect(result.current.error).toEqual({
        type: "DEVICE_IN_USE",
        message:
          "Camera is already in use by another application. Please close other apps using the camera.",
        userAction: "Close other applications using the camera",
      });
    });

    test("should set status to initializing during startup", async () => {
      let resolvePromise;
      const promise = new Promise(resolve => {
        resolvePromise = resolve;
      });
      mockGetUserMedia.mockReturnValue(promise);

      const { result } = renderHook(() => useWebcam());

      act(() => {
        result.current.startWebcam();
      });

      expect(result.current.status).toBe("initializing");

      await act(async () => {
        resolvePromise({
          getTracks: () => [{ stop: jest.fn() }],
          getVideoTracks: () => [{ stop: jest.fn() }],
        });
        await promise;
      });

      expect(result.current.status).toBe("active");
    });
  });

  describe("Stopping Webcam", () => {
    test("should successfully stop webcam", async () => {
      const mockTrack = { stop: jest.fn() };
      const mockStream = {
        getTracks: () => [mockTrack],
        getVideoTracks: () => [mockTrack],
      };
      mockGetUserMedia.mockResolvedValue(mockStream);

      const { result } = renderHook(() => useWebcam());

      // Start webcam first
      await act(async () => {
        await result.current.startWebcam();
      });

      // Stop webcam
      act(() => {
        result.current.stopWebcam();
      });

      expect(mockTrack.stop).toHaveBeenCalled();
      expect(result.current.stream).toBeNull();
      expect(result.current.isActive).toBe(false);
      expect(result.current.status).toBe("inactive");
    });

    test("should handle stopping when no stream exists", () => {
      const { result } = renderHook(() => useWebcam());

      expect(() => {
        act(() => {
          result.current.stopWebcam();
        });
      }).not.toThrow();

      expect(result.current.stream).toBeNull();
      expect(result.current.isActive).toBe(false);
    });
  });

  describe("Frame Capture", () => {
    test("should capture frame when webcam is active", async () => {
      const mockStream = {
        getTracks: () => [{ stop: jest.fn() }],
        getVideoTracks: () => [{ stop: jest.fn() }],
      };
      mockGetUserMedia.mockResolvedValue(mockStream);

      // Mock canvas and video elements
      const mockCanvas = {
        getContext: jest.fn(() => ({
          drawImage: jest.fn(),
        })),
        toDataURL: jest.fn(() => "data:image/jpeg;base64,mockdata"),
        width: 640,
        height: 480,
      };

      const mockVideo = {
        videoWidth: 640,
        videoHeight: 480,
        srcObject: null,
      };

      // Mock document.createElement
      const originalCreateElement = document.createElement;
      document.createElement = jest.fn(tagName => {
        if (tagName === "canvas") return mockCanvas;
        if (tagName === "video") return mockVideo;
        return originalCreateElement.call(document, tagName);
      });

      const { result } = renderHook(() => useWebcam());

      // Start webcam first
      await act(async () => {
        await result.current.startWebcam();
      });

      // Capture frame
      let frameData;
      await act(async () => {
        frameData = await result.current.captureFrame();
      });

      expect(frameData).toBe("data:image/jpeg;base64,mockdata");
      expect(mockCanvas.getContext).toHaveBeenCalledWith("2d");

      // Restore original createElement
      document.createElement = originalCreateElement;
    });

    test("should return null when capturing frame without active webcam", async () => {
      const { result } = renderHook(() => useWebcam());

      let frameData;
      await act(async () => {
        frameData = await result.current.captureFrame();
      });

      expect(frameData).toBeNull();
    });
  });

  describe("Error Recovery", () => {
    test("should clear error when successfully starting webcam after failure", async () => {
      const permissionError = new Error("Permission denied");
      permissionError.name = "NotAllowedError";

      const { result } = renderHook(() => useWebcam());

      // First attempt fails
      mockGetUserMedia.mockRejectedValueOnce(permissionError);
      await act(async () => {
        await result.current.startWebcam();
      });

      expect(result.current.error).toBeTruthy();

      // Second attempt succeeds
      const mockStream = {
        getTracks: () => [{ stop: jest.fn() }],
        getVideoTracks: () => [{ stop: jest.fn() }],
      };
      mockGetUserMedia.mockResolvedValue(mockStream);

      await act(async () => {
        await result.current.startWebcam();
      });

      expect(result.current.error).toBeNull();
      expect(result.current.isActive).toBe(true);
    });
  });

  describe("Cleanup on Unmount", () => {
    test("should stop webcam when component unmounts", async () => {
      const mockTrack = { stop: jest.fn() };
      const mockStream = {
        getTracks: () => [mockTrack],
        getVideoTracks: () => [mockTrack],
      };
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

  describe("Multiple Start/Stop Cycles", () => {
    test("should handle multiple start/stop cycles correctly", async () => {
      const mockTrack = { stop: jest.fn() };
      const mockStream = {
        getTracks: () => [mockTrack],
        getVideoTracks: () => [mockTrack],
      };
      mockGetUserMedia.mockResolvedValue(mockStream);

      const { result } = renderHook(() => useWebcam());

      // First cycle
      await act(async () => {
        await result.current.startWebcam();
      });
      expect(result.current.isActive).toBe(true);

      act(() => {
        result.current.stopWebcam();
      });
      expect(result.current.isActive).toBe(false);

      // Second cycle
      await act(async () => {
        await result.current.startWebcam();
      });
      expect(result.current.isActive).toBe(true);

      act(() => {
        result.current.stopWebcam();
      });
      expect(result.current.isActive).toBe(false);

      expect(mockGetUserMedia).toHaveBeenCalledTimes(2);
    });
  });
});
