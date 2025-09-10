import React, { useRef, useEffect, useState, useCallback } from "react";
import "./VideoDisplayPanel.css";

/**
 * Accessible VideoDisplayPanel component with accessibility announcements
 * Supports MediaPipe overlays and screen reader compatibility
 */
const VideoDisplayPanel = ({
  stream,
  overlayData = null,
  className = "",
  ariaLabel = "Video display",
  onFrameCapture,
  showControls = false,
  width = 640,
  height = 480,
  autoPlay = true,
  muted = true,
  playsInline = true,
  onVideoReady,
  onError,
  children,
}) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const overlayCanvasRef = useRef(null);
  const [videoStatus, setVideoStatus] = useState("loading");
  const [announcements, setAnnouncements] = useState([]);
  const announcementId = useRef(0);

  // Announce status changes to screen readers
  const announce = useCallback((message) => {
    const id = ++announcementId.current;
    setAnnouncements((prev) => [...prev, { id, message }]);

    // Remove announcement after it's been read
    setTimeout(() => {
      setAnnouncements((prev) => prev.filter((ann) => ann.id !== id));
    }, 1000);
  }, []);

  // Handle video stream changes
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    if (stream) {
      video.srcObject = stream;
      setVideoStatus("loading");
      announce("Video stream connecting");
    } else {
      video.srcObject = null;
      setVideoStatus("no-stream");
      announce("Video stream disconnected");
    }
  }, [stream, announce]);

  // Video event handlers
  const handleVideoReady = useCallback(() => {
    setVideoStatus("ready");
    announce("Video stream ready");
    if (onVideoReady) {
      onVideoReady();
    }
  }, [onVideoReady, announce]);

  const handleVideoError = useCallback(
    (error) => {
      setVideoStatus("error");
      announce("Video stream error occurred");
      console.error("Video error:", error);
      if (onError) {
        onError(error);
      }
    },
    [onError, announce]
  );

  const handleVideoPlay = useCallback(() => {
    setVideoStatus("playing");
    announce("Video stream playing");
  }, [announce]);

  const handleVideoPause = useCallback(() => {
    setVideoStatus("paused");
    announce("Video stream paused");
  }, [announce]);

  // Frame capture functionality
  const captureFrame = useCallback(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (!video || !canvas || videoStatus !== "playing") {
      return null;
    }

    const ctx = canvas.getContext("2d");
    canvas.width = video.videoWidth || width;
    canvas.height = video.videoHeight || height;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const frameData = canvas.toDataURL("image/jpeg", 0.8);

    if (onFrameCapture) {
      onFrameCapture(frameData);
    }

    return frameData;
  }, [videoStatus, width, height, onFrameCapture]);

  // Draw MediaPipe overlays
  useEffect(() => {
    const overlayCanvas = overlayCanvasRef.current;
    const video = videoRef.current;

    if (!overlayCanvas || !video || !overlayData) return;

    const ctx = overlayCanvas.getContext("2d");
    const videoWidth = video.videoWidth || width;
    const videoHeight = video.videoHeight || height;

    overlayCanvas.width = videoWidth;
    overlayCanvas.height = videoHeight;

    // Clear previous overlays
    ctx.clearRect(0, 0, videoWidth, videoHeight);

    // Draw landmarks if available
    if (overlayData.landmarks) {
      ctx.strokeStyle = "#00ff00";
      ctx.lineWidth = 2;
      ctx.fillStyle = "#ff0000";

      overlayData.landmarks.forEach((landmark) => {
        const x = landmark.x * videoWidth;
        const y = landmark.y * videoHeight;

        // Draw landmark point
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, 2 * Math.PI);
        ctx.fill();
      });
    }

    // Draw connections if available
    if (overlayData.connections) {
      ctx.strokeStyle = "#00ff00";
      ctx.lineWidth = 2;

      overlayData.connections.forEach((connection) => {
        const startLandmark = overlayData.landmarks[connection.start];
        const endLandmark = overlayData.landmarks[connection.end];

        if (startLandmark && endLandmark) {
          const startX = startLandmark.x * videoWidth;
          const startY = startLandmark.y * videoHeight;
          const endX = endLandmark.x * videoWidth;
          const endY = endLandmark.y * videoHeight;

          ctx.beginPath();
          ctx.moveTo(startX, startY);
          ctx.lineTo(endX, endY);
          ctx.stroke();
        }
      });
    }
  }, [overlayData, width, height]);

  const containerClasses = [
    "video-display-panel",
    `status-${videoStatus}`,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={containerClasses}>
      {/* Screen reader announcements */}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {announcements.map((ann) => (
          <div key={ann.id}>{ann.message}</div>
        ))}
      </div>

      <div className="video-container" style={{ width, height }}>
        <video
          ref={videoRef}
          className="video-element"
          width={width}
          height={height}
          autoPlay={autoPlay}
          muted={muted}
          playsInline={playsInline}
          onLoadedData={handleVideoReady}
          onError={handleVideoError}
          onPlay={handleVideoPlay}
          onPause={handleVideoPause}
          aria-label={ariaLabel}
        />

        {/* Hidden canvas for frame capture */}
        <canvas
          ref={canvasRef}
          className="capture-canvas"
          style={{ display: "none" }}
          aria-hidden="true"
        />

        {/* Overlay canvas for MediaPipe visualizations */}
        <canvas
          ref={overlayCanvasRef}
          className="overlay-canvas"
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            pointerEvents: "none",
          }}
          aria-hidden="true"
        />

        {/* Status overlay */}
        <div className="video-status-overlay">
          {videoStatus === "loading" && (
            <div className="status-message">
              <div className="loading-spinner" aria-hidden="true"></div>
              <span>Connecting to video stream...</span>
            </div>
          )}

          {videoStatus === "error" && (
            <div className="status-message error">
              <span>Video stream error</span>
            </div>
          )}

          {videoStatus === "no-stream" && (
            <div className="status-message">
              <span>No video stream available</span>
            </div>
          )}
        </div>

        {/* Controls */}
        {showControls && (
          <div className="video-controls">
            <button
              className="capture-button"
              onClick={captureFrame}
              disabled={videoStatus !== "playing"}
              aria-label="Capture current frame"
            >
              📷 Capture Frame
            </button>
          </div>
        )}

        {/* Additional content */}
        {children}
      </div>
    </div>
  );
};

export default VideoDisplayPanel;
