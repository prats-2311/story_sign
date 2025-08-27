import React, { useRef, useEffect, useState, useCallback } from "react";

const WebcamCapture = ({ onFrameCapture, onError, isActive = false }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const downscaleCanvasRef = useRef(null);
  const streamRef = useRef(null);
  const animationFrameRef = useRef(null);

  // Performance monitoring refs
  const performanceMetricsRef = useRef({
    frameCount: 0,
    droppedFrames: 0,
    lastFrameTime: 0,
    frameProcessingTimes: [],
    targetFPS: 30,
    currentFPS: 0,
    adaptiveFPS: 30,
    lastFPSUpdate: 0,
    processingCapability: 1.0, // 1.0 = full capability, lower values indicate performance issues
  });

  const [webcamStatus, setWebcamStatus] = useState("inactive"); // inactive, initializing, active, error
  const [errorMessage, setErrorMessage] = useState("");
  const [frameCount, setFrameCount] = useState(0);
  const [performanceStats, setPerformanceStats] = useState({
    currentFPS: 0,
    adaptiveFPS: 30,
    droppedFrames: 0,
    processingCapability: 1.0,
    avgProcessingTime: 0,
  });

  // Initialize webcam access
  const initializeWebcam = useCallback(async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      const error = "getUserMedia is not supported in this browser";
      setErrorMessage(error);
      setWebcamStatus("error");
      onError?.(error);
      return;
    }

    setWebcamStatus("initializing");
    setErrorMessage("");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          frameRate: { ideal: 30 },
        },
        audio: false,
      });

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current.play();
          setWebcamStatus("active");
        };
      }
    } catch (error) {
      let errorMsg = "Failed to access webcam";
      let errorCode = error.name;

      if (error.name === "NotAllowedError") {
        errorMsg =
          "Camera access denied. Please allow camera permissions in your browser settings and refresh the page.";
      } else if (error.name === "NotFoundError") {
        errorMsg =
          "No camera device found. Please connect a camera and try again.";
      } else if (error.name === "NotReadableError") {
        errorMsg =
          "Camera is already in use by another application. Please close other apps using the camera.";
      } else if (error.name === "OverconstrainedError") {
        errorMsg =
          "Camera does not support the requested video settings. Trying with default settings...";

        // Try again with more relaxed constraints
        try {
          const fallbackStream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: false,
          });

          streamRef.current = fallbackStream;
          if (videoRef.current) {
            videoRef.current.srcObject = fallbackStream;
            videoRef.current.onloadedmetadata = () => {
              videoRef.current.play();
              setWebcamStatus("active");
            };
          }
          return; // Success with fallback
        } catch (fallbackError) {
          errorMsg = `Camera constraints not supported: ${fallbackError.message}`;
        }
      } else if (error.name === "AbortError") {
        errorMsg = "Camera access was interrupted. Please try again.";
      } else if (error.name === "SecurityError") {
        errorMsg =
          "Camera access blocked by security policy. Please check browser settings.";
      } else {
        errorMsg = `Camera error (${errorCode}): ${error.message}`;
      }

      console.error("Webcam initialization error:", error);
      setErrorMessage(errorMsg);
      setWebcamStatus("error");
      onError?.(errorMsg);
    }
  }, [onError]);

  // Stop webcam stream
  const stopWebcam = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    setWebcamStatus("inactive");
    setFrameCount(0);
  }, []);

  // Calculate adaptive FPS based on processing capability
  const calculateAdaptiveFPS = useCallback(() => {
    const metrics = performanceMetricsRef.current;
    const now = performance.now();

    // Update FPS calculation every second
    if (now - metrics.lastFPSUpdate > 1000) {
      const timeDelta = (now - metrics.lastFPSUpdate) / 1000;
      metrics.currentFPS = metrics.frameCount / timeDelta;

      // Calculate average processing time
      const avgProcessingTime =
        metrics.frameProcessingTimes.length > 0
          ? metrics.frameProcessingTimes.reduce((a, b) => a + b, 0) /
            metrics.frameProcessingTimes.length
          : 0;

      // Determine processing capability based on frame processing times
      // If processing takes longer than frame interval, reduce capability
      const targetFrameInterval = 1000 / metrics.targetFPS;
      metrics.processingCapability = Math.min(
        1.0,
        targetFrameInterval / Math.max(avgProcessingTime, 1)
      );

      // Adapt FPS based on processing capability
      // Reduce FPS if processing capability is low to prevent frame dropping
      if (metrics.processingCapability < 0.8) {
        metrics.adaptiveFPS = Math.max(
          10,
          metrics.targetFPS * metrics.processingCapability
        );
      } else if (
        metrics.processingCapability > 0.95 &&
        metrics.adaptiveFPS < metrics.targetFPS
      ) {
        // Gradually increase FPS if processing capability is good
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

      // Keep only recent processing times (last 30 frames)
      if (metrics.frameProcessingTimes.length > 30) {
        metrics.frameProcessingTimes = metrics.frameProcessingTimes.slice(-30);
      }
    }
  }, []);

  // Check if frame should be dropped based on adaptive FPS
  const shouldDropFrame = useCallback(() => {
    const metrics = performanceMetricsRef.current;
    const now = performance.now();
    const targetInterval = 1000 / metrics.adaptiveFPS;

    // Drop frame if not enough time has passed since last frame
    if (now - metrics.lastFrameTime < targetInterval) {
      metrics.droppedFrames++;
      return true;
    }

    return false;
  }, []);

  // Capture frame from video and convert to base64 JPEG with performance monitoring
  const captureFrame = useCallback(() => {
    if (
      !videoRef.current ||
      !downscaleCanvasRef.current ||
      webcamStatus !== "active"
    ) {
      return null;
    }

    const frameStartTime = performance.now();

    // Check if frame should be dropped for performance
    if (shouldDropFrame()) {
      return null;
    }

    const video = videoRef.current;
    const downscaleCanvas = downscaleCanvasRef.current;
    const ctx = downscaleCanvas.getContext("2d");

    // Target backend resolution
    const backendWidth = 320;
    const backendHeight = 240;

    downscaleCanvas.width = backendWidth;
    downscaleCanvas.height = backendHeight;

    // Draw full-res video onto smaller canvas (browser handles downscaling)
    // Note: CSS transform on video element doesn't affect canvas drawImage
    ctx.drawImage(video, 0, 0, backendWidth, backendHeight);

    try {
      const metrics = performanceMetricsRef.current;
      const quality = Math.max(0.7, 0.85 * metrics.processingCapability);
      const base64Data = downscaleCanvas.toDataURL("image/jpeg", quality);

      // Update performance metrics
      const frameEndTime = performance.now();
      const processingTime = frameEndTime - frameStartTime;

      metrics.frameCount++;
      metrics.lastFrameTime = frameEndTime;
      metrics.frameProcessingTimes.push(processingTime);

      setFrameCount((prev) => prev + 1);

      return {
        frameData: base64Data,
        timestamp: new Date().toISOString(),
        frameNumber: frameCount + 1,
        width: backendWidth,
        height: backendHeight,
        processingTime: processingTime,
        quality: quality,
      };
    } catch (error) {
      console.error("Error capturing frame:", error);
      return null;
    }
  }, [webcamStatus, frameCount, shouldDropFrame]);

  // Enhanced frame capture loop with performance monitoring and adaptive FPS
  const startFrameCapture = useCallback(() => {
    if (!isActive || webcamStatus !== "active") {
      return;
    }

    // Initialize performance metrics
    const metrics = performanceMetricsRef.current;
    metrics.frameCount = 0;
    metrics.droppedFrames = 0;
    metrics.lastFrameTime = performance.now();
    metrics.lastFPSUpdate = performance.now();
    metrics.frameProcessingTimes = [];

    const captureLoop = () => {
      // Calculate adaptive FPS and update performance metrics
      calculateAdaptiveFPS();

      const frameData = captureFrame();
      if (frameData && onFrameCapture) {
        // Create WebSocket message format as specified in requirements
        const message = {
          type: "raw_frame",
          timestamp: frameData.timestamp,
          frame_data: frameData.frameData,
          metadata: {
            frame_number: frameData.frameNumber,
            client_id: `webcam_${Date.now()}`,
            width: frameData.width,
            height: frameData.height,
            processing_time_ms: frameData.processingTime,
            quality: frameData.quality,
            adaptive_fps: metrics.adaptiveFPS,
            processing_capability: metrics.processingCapability,
          },
        };

        onFrameCapture(message);
      }

      // Continue the loop if still active
      if (isActive && webcamStatus === "active") {
        animationFrameRef.current = requestAnimationFrame(captureLoop);
      }
    };

    // Start the capture loop
    animationFrameRef.current = requestAnimationFrame(captureLoop);
  }, [
    isActive,
    webcamStatus,
    captureFrame,
    onFrameCapture,
    calculateAdaptiveFPS,
  ]);

  // Stop frame capture loop
  const stopFrameCapture = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
  }, []);

  // Effect to handle webcam initialization/cleanup
  useEffect(() => {
    if (isActive && webcamStatus === "inactive") {
      initializeWebcam();
    } else if (!isActive && webcamStatus !== "inactive") {
      stopWebcam();
    }
  }, [isActive, webcamStatus, initializeWebcam, stopWebcam]);

  // Effect to handle frame capture loop
  useEffect(() => {
    if (isActive && webcamStatus === "active") {
      startFrameCapture();
    } else {
      stopFrameCapture();
    }

    return () => {
      stopFrameCapture();
    };
  }, [isActive, webcamStatus, startFrameCapture, stopFrameCapture]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopWebcam();
    };
  }, [stopWebcam]);

  const getStatusColor = () => {
    switch (webcamStatus) {
      case "active":
        return "#4CAF50";
      case "error":
        return "#f44336";
      case "initializing":
        return "#ff9800";
      default:
        return "#9e9e9e";
    }
  };

  const getStatusText = () => {
    switch (webcamStatus) {
      case "active":
        return `Active (${frameCount} frames, ${performanceStats.currentFPS} FPS)`;
      case "error":
        return "Error";
      case "initializing":
        return "Initializing...";
      default:
        return "Inactive";
    }
  };

  return (
    <div className="webcam-capture">
      <div className="webcam-status">
        <span
          className="status-dot"
          style={{ backgroundColor: getStatusColor() }}
        ></span>
        <span className="status-text">{getStatusText()}</span>
      </div>

      {errorMessage && (
        <div className="error-message">
          <p>{errorMessage}</p>
        </div>
      )}

      <div className="video-container">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          style={{
            width: "100%",
            maxWidth: "640px",
            height: "auto",
            display: webcamStatus === "active" ? "block" : "none",
            transform: "scaleX(-1)", // Flip horizontally to fix mirror effect
          }}
        />

        {webcamStatus === "inactive" && (
          <div className="video-placeholder">
            <p>Webcam inactive</p>
          </div>
        )}

        {webcamStatus === "initializing" && (
          <div className="video-placeholder">
            <p>Initializing webcam...</p>
          </div>
        )}

        {webcamStatus === "error" && (
          <div className="video-placeholder error">
            <p>Webcam unavailable</p>
          </div>
        )}
      </div>

      {/* Performance monitoring display */}
      {webcamStatus === "active" && (
        <div className="performance-stats">
          <h4>Performance Metrics</h4>
          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-label">Current FPS:</span>
              <span className="stat-value">{performanceStats.currentFPS}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Adaptive FPS:</span>
              <span className="stat-value">{performanceStats.adaptiveFPS}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Dropped Frames:</span>
              <span className="stat-value">
                {performanceStats.droppedFrames}
              </span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Processing Capability:</span>
              <span className="stat-value">
                {(performanceStats.processingCapability * 100).toFixed(0)}%
              </span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Avg Processing Time:</span>
              <span className="stat-value">
                {performanceStats.avgProcessingTime}ms
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Hidden canvases for frame capture */}
      <canvas ref={canvasRef} style={{ display: "none" }} />
      <canvas ref={downscaleCanvasRef} style={{ display: "none" }} />
    </div>
  );
};

export default WebcamCapture;
