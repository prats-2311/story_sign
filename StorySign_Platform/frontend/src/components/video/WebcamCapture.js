import React, { useRef, useEffect, useState, useCallback } from "react";
import useWebcam from "../../hooks/useWebcam";

const WebcamCapture = ({ onFrameCapture, onError, isActive = false }) => {
  const videoRef = useRef(null);
  const animationFrameRef = useRef(null);

  // Use centralized webcam hook
  const {
    stream,
    status: webcamStatus,
    error: webcamError,
    performanceStats,
    startWebcam,
    stopWebcam,
    attachToVideoElement,
    captureFrame,
    isReady,
  } = useWebcam();

  const [frameCount, setFrameCount] = useState(0);

  // Handle webcam errors from hook
  useEffect(() => {
    if (webcamError) {
      onError?.(webcamError.message);
    }
  }, [webcamError, onError]);

  // Enhanced frame capture using the centralized hook
  const captureFrameFromVideo = useCallback(() => {
    if (!videoRef.current || !isReady) {
      return null;
    }

    const frameData = captureFrame(videoRef.current, {
      width: 320,
      height: 240,
    });

    if (frameData) {
      setFrameCount((prev) => prev + 1);
    }

    return frameData;
  }, [isReady, captureFrame]);

  // Enhanced frame capture loop using centralized hook
  const startFrameCapture = useCallback(() => {
    if (!isActive || !isReady) {
      return;
    }

    const captureLoop = () => {
      const frameData = captureFrameFromVideo();
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
            adaptive_fps: performanceStats.adaptiveFPS,
            processing_capability: performanceStats.processingCapability,
          },
        };

        onFrameCapture(message);
      }

      // Continue the loop if still active
      if (isActive && isReady) {
        animationFrameRef.current = requestAnimationFrame(captureLoop);
      }
    };

    // Start the capture loop
    animationFrameRef.current = requestAnimationFrame(captureLoop);
  }, [
    isActive,
    isReady,
    captureFrameFromVideo,
    onFrameCapture,
    performanceStats.adaptiveFPS,
    performanceStats.processingCapability,
  ]);

  // Stop frame capture loop
  const stopFrameCapture = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
  }, []);

  // Effect to handle webcam initialization/cleanup using centralized hook
  useEffect(() => {
    if (isActive) {
      startWebcam();
    } else {
      stopWebcam();
    }
  }, [isActive, startWebcam, stopWebcam]);

  // Effect to attach stream to video element when available
  useEffect(() => {
    if (stream && videoRef.current) {
      attachToVideoElement(videoRef.current);
    }
  }, [stream, attachToVideoElement]);

  // Effect to handle frame capture loop
  useEffect(() => {
    if (isActive && isReady) {
      startFrameCapture();
    } else {
      stopFrameCapture();
    }

    return () => {
      stopFrameCapture();
    };
  }, [isActive, isReady, startFrameCapture, stopFrameCapture]);

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

  // Get error message from hook or fallback
  const errorMessage = webcamError?.message || "";

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

      {/* Note: Canvas creation is now handled by the useWebcam hook */}
    </div>
  );
};

export default WebcamCapture;
