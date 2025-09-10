/**
 * useWebcam Hook
 * Centralized webcam management hook for StorySign Platform
 * Provides single source of truth for camera access and eliminates black screen bugs
 */

import { useState, useRef, useCallback, useEffect } from "react";

const useWebcam = () => {
  // State management
  const [stream, setStream] = useState(null);
  const [isActive, setIsActive] = useState(false);
  const [status, setStatus] = useState("inactive"); // inactive, initializing, active, error
  const [error, setError] = useState(null);
  const [deviceInfo, setDeviceInfo] = useState(null);

  // Refs for cleanup and performance tracking
  const streamRef = useRef(null);
  const videoElementRef = useRef(null);
  const performanceMetricsRef = useRef({
    frameCount: 0,
    droppedFrames: 0,
    lastFrameTime: 0,
    frameProcessingTimes: [],
    targetFPS: 30,
    currentFPS: 0,
    adaptiveFPS: 30,
    lastFPSUpdate: 0,
    processingCapability: 1.0,
  });

  // Performance stats state
  const [performanceStats, setPerformanceStats] = useState({
    currentFPS: 0,
    adaptiveFPS: 30,
    droppedFrames: 0,
    processingCapability: 1.0,
    avgProcessingTime: 0,
  });

  /**
   * Start webcam with comprehensive error handling
   */
  const startWebcam = useCallback(async (constraints = {}) => {
    // Check if getUserMedia is supported
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      const errorMsg = "getUserMedia is not supported in this browser";
      setError({
        type: "BROWSER_NOT_SUPPORTED",
        message: errorMsg,
        userAction: "Please use a modern browser that supports camera access",
      });
      setStatus("error");
      return false;
    }

    setStatus("initializing");
    setError(null);

    // Default constraints with performance optimizations
    const defaultConstraints = {
      video: {
        width: { ideal: 640 },
        height: { ideal: 480 },
        frameRate: { ideal: 30 },
        facingMode: "user",
      },
      audio: false,
      ...constraints,
    };

    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia(
        defaultConstraints
      );

      // Store stream reference for cleanup
      streamRef.current = mediaStream;
      setStream(mediaStream);

      // Get device information
      const videoTrack = mediaStream.getVideoTracks()[0];
      if (videoTrack) {
        const settings = videoTrack.getSettings();
        setDeviceInfo({
          deviceId: settings.deviceId,
          label: videoTrack.label,
          width: settings.width,
          height: settings.height,
          frameRate: settings.frameRate,
          facingMode: settings.facingMode,
        });
      }

      setStatus("active");
      setIsActive(true);

      // Reset performance metrics
      const metrics = performanceMetricsRef.current;
      metrics.frameCount = 0;
      metrics.droppedFrames = 0;
      metrics.lastFrameTime = performance.now();
      metrics.lastFPSUpdate = performance.now();
      metrics.frameProcessingTimes = [];

      return true;
    } catch (err) {
      console.error("Webcam initialization error:", err);

      let errorInfo = {
        type: "UNKNOWN_ERROR",
        message: "Failed to access webcam",
        userAction: "Please try again",
      };

      // Handle specific error types
      switch (err.name) {
        case "NotAllowedError":
          errorInfo = {
            type: "PERMISSION_DENIED",
            message:
              "Camera access denied. Please allow camera permissions in your browser settings and refresh the page.",
            userAction: "Check browser permissions and reload the page",
          };
          break;

        case "NotFoundError":
          errorInfo = {
            type: "NO_DEVICE_FOUND",
            message:
              "No camera device found. Please connect a camera and try again.",
            userAction: "Connect a camera device and try again",
          };
          break;

        case "NotReadableError":
          errorInfo = {
            type: "DEVICE_IN_USE",
            message:
              "Camera is already in use by another application. Please close other apps using the camera.",
            userAction: "Close other applications using the camera",
          };
          break;

        case "OverconstrainedError":
          // Try with fallback constraints
          try {
            const fallbackStream = await navigator.mediaDevices.getUserMedia({
              video: true,
              audio: false,
            });

            streamRef.current = fallbackStream;
            setStream(fallbackStream);
            setStatus("active");
            setIsActive(true);

            const videoTrack = fallbackStream.getVideoTracks()[0];
            if (videoTrack) {
              const settings = videoTrack.getSettings();
              setDeviceInfo({
                deviceId: settings.deviceId,
                label: videoTrack.label,
                width: settings.width,
                height: settings.height,
                frameRate: settings.frameRate,
                facingMode: settings.facingMode,
              });
            }

            return true;
          } catch (fallbackError) {
            errorInfo = {
              type: "CONSTRAINTS_NOT_SUPPORTED",
              message: `Camera constraints not supported: ${fallbackError.message}`,
              userAction:
                "Try with a different camera or check camera settings",
            };
          }
          break;

        case "AbortError":
          errorInfo = {
            type: "ACCESS_INTERRUPTED",
            message: "Camera access was interrupted. Please try again.",
            userAction: "Try accessing the camera again",
          };
          break;

        case "SecurityError":
          errorInfo = {
            type: "SECURITY_ERROR",
            message:
              "Camera access blocked by security policy. Please check browser settings.",
            userAction:
              "Check browser security settings and HTTPS requirements",
          };
          break;

        default:
          errorInfo = {
            type: "UNKNOWN_ERROR",
            message: `Camera error (${err.name}): ${err.message}`,
            userAction: "Please try again or check your camera settings",
          };
      }

      setError(errorInfo);
      setStatus("error");
      setIsActive(false);
      return false;
    }
  }, []);

  /**
   * Stop webcam with proper cleanup
   */
  const stopWebcam = useCallback(() => {
    if (streamRef.current) {
      // Stop all tracks to properly release camera resources
      streamRef.current.getTracks().forEach((track) => {
        track.stop();
      });
      streamRef.current = null;
    }

    // Clear video element source if attached
    if (videoElementRef.current) {
      videoElementRef.current.srcObject = null;
    }

    // Reset state
    setStream(null);
    setIsActive(false);
    setStatus("inactive");
    setError(null);
    setDeviceInfo(null);

    // Reset performance metrics
    setPerformanceStats({
      currentFPS: 0,
      adaptiveFPS: 30,
      droppedFrames: 0,
      processingCapability: 1.0,
      avgProcessingTime: 0,
    });
  }, []);

  /**
   * Attach stream to video element
   */
  const attachToVideoElement = useCallback(
    (videoElement) => {
      if (videoElement && stream) {
        videoElement.srcObject = stream;
        videoElementRef.current = videoElement;

        // Handle video element events
        videoElement.onloadedmetadata = () => {
          videoElement.play().catch((err) => {
            console.warn("Video autoplay failed:", err);
          });
        };

        return true;
      }
      return false;
    },
    [stream]
  );

  /**
   * Capture frame from video element
   */
  const captureFrame = useCallback(
    (videoElement, options = {}) => {
      if (!videoElement || !stream || status !== "active") {
        return null;
      }

      const frameStartTime = performance.now();

      // Check if frame should be dropped for performance
      const metrics = performanceMetricsRef.current;
      const now = performance.now();
      const targetInterval = 1000 / metrics.adaptiveFPS;

      if (now - metrics.lastFrameTime < targetInterval) {
        metrics.droppedFrames++;
        return null;
      }

      try {
        // Create canvas for frame capture
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");

        // Set canvas dimensions
        const width = options.width || 320;
        const height = options.height || 240;
        canvas.width = width;
        canvas.height = height;

        // Draw video frame to canvas
        ctx.drawImage(videoElement, 0, 0, width, height);

        // Convert to base64 with quality based on processing capability
        const quality = Math.max(0.7, 0.85 * metrics.processingCapability);
        const base64Data = canvas.toDataURL("image/jpeg", quality);

        // Update performance metrics
        const frameEndTime = performance.now();
        const processingTime = frameEndTime - frameStartTime;

        metrics.frameCount++;
        metrics.lastFrameTime = frameEndTime;
        metrics.frameProcessingTimes.push(processingTime);

        // Calculate adaptive FPS
        if (now - metrics.lastFPSUpdate > 1000) {
          const timeDelta = (now - metrics.lastFPSUpdate) / 1000;
          metrics.currentFPS = metrics.frameCount / timeDelta;

          // Calculate average processing time
          const avgProcessingTime =
            metrics.frameProcessingTimes.length > 0
              ? metrics.frameProcessingTimes.reduce((a, b) => a + b, 0) /
                metrics.frameProcessingTimes.length
              : 0;

          // Determine processing capability
          const targetFrameInterval = 1000 / metrics.targetFPS;
          metrics.processingCapability = Math.min(
            1.0,
            targetFrameInterval / Math.max(avgProcessingTime, 1)
          );

          // Adapt FPS based on processing capability
          if (metrics.processingCapability < 0.8) {
            metrics.adaptiveFPS = Math.max(
              10,
              metrics.targetFPS * metrics.processingCapability
            );
          } else if (
            metrics.processingCapability > 0.95 &&
            metrics.adaptiveFPS < metrics.targetFPS
          ) {
            metrics.adaptiveFPS = Math.min(
              metrics.targetFPS,
              metrics.adaptiveFPS + 2
            );
          }

          // Update UI stats
          setPerformanceStats({
            currentFPS: Math.round(metrics.currentFPS * 10) / 10,
            adaptiveFPS: Math.round(metrics.adaptiveFPS),
            droppedFrames: metrics.droppedFrames,
            processingCapability:
              Math.round(metrics.processingCapability * 100) / 100,
            avgProcessingTime: Math.round(avgProcessingTime * 10) / 10,
          });

          // Reset counters
          metrics.frameCount = 0;
          metrics.lastFPSUpdate = now;

          // Keep only recent processing times
          if (metrics.frameProcessingTimes.length > 30) {
            metrics.frameProcessingTimes =
              metrics.frameProcessingTimes.slice(-30);
          }
        }

        return {
          frameData: base64Data,
          timestamp: new Date().toISOString(),
          width,
          height,
          processingTime,
          quality,
          frameNumber: metrics.frameCount,
        };
      } catch (captureError) {
        console.error("Error capturing frame:", captureError);
        return null;
      }
    },
    [stream, status]
  );

  /**
   * Get available camera devices
   */
  const getAvailableDevices = useCallback(async () => {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      return devices.filter((device) => device.kind === "videoinput");
    } catch (err) {
      console.error("Error enumerating devices:", err);
      return [];
    }
  }, []);

  /**
   * Switch to different camera device
   */
  const switchCamera = useCallback(
    async (deviceId) => {
      if (isActive) {
        stopWebcam();
      }

      const constraints = {
        video: {
          deviceId: { exact: deviceId },
          width: { ideal: 640 },
          height: { ideal: 480 },
          frameRate: { ideal: 30 },
        },
        audio: false,
      };

      return await startWebcam(constraints);
    },
    [isActive, stopWebcam, startWebcam]
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopWebcam();
    };
  }, [stopWebcam]);

  // Return hook interface
  return {
    // State
    stream,
    isActive,
    status,
    error,
    deviceInfo,
    performanceStats,

    // Actions
    startWebcam,
    stopWebcam,
    attachToVideoElement,
    captureFrame,
    getAvailableDevices,
    switchCamera,

    // Computed values
    isInitializing: status === "initializing",
    hasError: status === "error",
    isReady: status === "active" && stream !== null,
  };
};

export default useWebcam;
