import React, { useRef, useEffect, useState, useCallback } from "react";

const ProcessedVideoDisplay = ({
  processedFrameData,
  connectionStatus,
  streamingStats,
  onRetryConnection,
  isActive = false,
}) => {
  const canvasRef = useRef(null);
  const [displayStats, setDisplayStats] = useState({
    frameRate: 0,
    latency: 0,
    quality: "Unknown",
    resolution: "0x0",
    lastFrameTime: null,
    totalFrames: 0,
    droppedFrames: 0,
  });

  const [performanceMetrics, setPerformanceMetrics] = useState({
    avgLatency: 0,
    maxLatency: 0,
    minLatency: Infinity,
    frameRateHistory: [],
    qualityHistory: [],
    connectionUptime: 0,
    lastConnectionTime: null,
  });

  const frameHistoryRef = useRef([]);
  const performanceHistoryRef = useRef({
    latencies: [],
    frameRates: [],
    connectionStartTime: null,
  });

  // Update display statistics when new frame data arrives
  useEffect(() => {
    if (!processedFrameData || !processedFrameData.metadata) return;

    const now = Date.now();
    const frameTimestamp = new Date(processedFrameData.timestamp).getTime();
    const latency = now - frameTimestamp;

    // Update frame history for FPS calculation
    frameHistoryRef.current.push({
      timestamp: now,
      latency: latency,
      processingTime: processedFrameData.metadata.processing_time_ms || 0,
    });

    // Keep only last 30 frames for FPS calculation
    if (frameHistoryRef.current.length > 30) {
      frameHistoryRef.current = frameHistoryRef.current.slice(-30);
    }

    // Calculate frame rate from recent frames
    const recentFrames = frameHistoryRef.current.filter(
      (frame) => now - frame.timestamp < 5000 // Last 5 seconds
    );
    const frameRate =
      recentFrames.length > 1
        ? (recentFrames.length - 1) / ((now - recentFrames[0].timestamp) / 1000)
        : 0;

    // Update performance history
    const perfHistory = performanceHistoryRef.current;
    perfHistory.latencies.push(latency);
    perfHistory.frameRates.push(frameRate);

    // Keep only recent performance data (last 100 samples)
    if (perfHistory.latencies.length > 100) {
      perfHistory.latencies = perfHistory.latencies.slice(-100);
      perfHistory.frameRates = perfHistory.frameRates.slice(-100);
    }

    // Calculate performance metrics
    const avgLatency =
      perfHistory.latencies.reduce((a, b) => a + b, 0) /
      perfHistory.latencies.length;
    const maxLatency = Math.max(...perfHistory.latencies);
    const minLatency = Math.min(...perfHistory.latencies);

    // Determine quality based on frame data
    let quality = "Unknown";
    if (processedFrameData.metadata.landmarks_detected) {
      const landmarks = processedFrameData.metadata.landmarks_detected;
      const detectedCount = Object.values(landmarks).filter(Boolean).length;
      if (detectedCount === 3) quality = "Excellent";
      else if (detectedCount === 2) quality = "Good";
      else if (detectedCount === 1) quality = "Fair";
      else quality = "Poor";
    }

    // Get resolution from frame data
    const resolution = processedFrameData.frame_data
      ? `${processedFrameData.metadata.width || "Unknown"}x${
          processedFrameData.metadata.height || "Unknown"
        }`
      : "0x0";

    setDisplayStats({
      frameRate: Math.round(frameRate * 10) / 10,
      latency: Math.round(latency),
      quality: quality,
      resolution: resolution,
      lastFrameTime: new Date(processedFrameData.timestamp),
      totalFrames: processedFrameData.metadata.frame_number || 0,
      droppedFrames: streamingStats?.droppedFrames || 0,
    });

    setPerformanceMetrics({
      avgLatency: Math.round(avgLatency),
      maxLatency: Math.round(maxLatency),
      minLatency: Math.round(minLatency === Infinity ? 0 : minLatency),
      frameRateHistory: perfHistory.frameRates.slice(-10), // Last 10 readings
      qualityHistory: [], // Could be expanded for quality tracking
      connectionUptime: perfHistory.connectionStartTime
        ? Math.round((now - perfHistory.connectionStartTime) / 1000)
        : 0,
      lastConnectionTime: perfHistory.connectionStartTime,
    });
  }, [processedFrameData, streamingStats]);

  // Track connection uptime
  useEffect(() => {
    const perfHistory = performanceHistoryRef.current;

    if (connectionStatus === "connected" && !perfHistory.connectionStartTime) {
      perfHistory.connectionStartTime = Date.now();
    } else if (connectionStatus !== "connected") {
      perfHistory.connectionStartTime = null;
    }
  }, [connectionStatus]);

  // Get connection quality color based on latency and frame rate
  const getConnectionQualityColor = useCallback(() => {
    if (connectionStatus !== "connected") return "#f44336"; // Red for disconnected

    const latency = displayStats.latency;
    const frameRate = displayStats.frameRate;

    if (latency < 100 && frameRate > 20) return "#4CAF50"; // Green for excellent
    if (latency < 200 && frameRate > 15) return "#ff9800"; // Orange for good
    return "#f44336"; // Red for poor
  }, [connectionStatus, displayStats.latency, displayStats.frameRate]);

  // Draw overlay information on the canvas
  const drawOverlayInfo = useCallback(
    (ctx, width, height) => {
      if (!processedFrameData?.metadata) return;

      // Set up overlay style
      ctx.fillStyle = "rgba(0, 0, 0, 0.7)";
      ctx.font = "12px Arial";
      ctx.textAlign = "left";

      // Draw frame info overlay
      const overlayHeight = 80;
      ctx.fillRect(0, height - overlayHeight, width, overlayHeight);

      // Draw text information
      ctx.fillStyle = "white";
      const metadata = processedFrameData.metadata;

      ctx.fillText(
        `Frame: #${metadata.frame_number || "N/A"}`,
        10,
        height - 60
      );
      ctx.fillText(
        `Processing: ${metadata.processing_time_ms || 0}ms`,
        10,
        height - 45
      );
      ctx.fillText(`Latency: ${displayStats.latency}ms`, 10, height - 30);
      ctx.fillText(`FPS: ${displayStats.frameRate}`, 10, height - 15);

      // Draw landmarks status
      if (metadata.landmarks_detected) {
        const landmarks = metadata.landmarks_detected;
        let x = width - 150;
        ctx.fillText("Landmarks:", x, height - 60);

        ctx.fillStyle = landmarks.hands ? "#4CAF50" : "#f44336";
        ctx.fillText(`Hands: ${landmarks.hands ? "✓" : "✗"}`, x, height - 45);

        ctx.fillStyle = landmarks.face ? "#4CAF50" : "#f44336";
        ctx.fillText(`Face: ${landmarks.face ? "✓" : "✗"}`, x, height - 30);

        ctx.fillStyle = landmarks.pose ? "#4CAF50" : "#f44336";
        ctx.fillText(`Pose: ${landmarks.pose ? "✓" : "✗"}`, x, height - 15);
      }

      // Draw connection quality indicator
      ctx.fillStyle = getConnectionQualityColor();
      ctx.fillRect(width - 20, 10, 10, 10);
    },
    [processedFrameData, displayStats, getConnectionQualityColor]
  );

  // Render processed frame to canvas with enhanced display
  const renderFrameToCanvas = useCallback(() => {
    if (!processedFrameData?.frame_data || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const img = new Image();

    img.onload = () => {
      // Set canvas size to match image
      canvas.width = img.width;
      canvas.height = img.height;

      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw the processed frame
      ctx.drawImage(img, 0, 0);

      // Add overlay information if enabled
      if (isActive) {
        drawOverlayInfo(ctx, canvas.width, canvas.height);
      }
    };

    img.onerror = (error) => {
      console.error("Error loading processed frame:", error);
    };

    img.src = processedFrameData.frame_data;
  }, [processedFrameData, isActive, drawOverlayInfo]);

  // Render frame when data changes
  useEffect(() => {
    renderFrameToCanvas();
  }, [renderFrameToCanvas]);

  // Get status display information
  const getStatusInfo = () => {
    switch (connectionStatus) {
      case "connected":
        return {
          color: "#4CAF50",
          text: "Connected",
          description: "Receiving processed video stream",
        };
      case "connecting":
        return {
          color: "#ff9800",
          text: "Connecting",
          description: "Establishing connection to video processor",
        };
      case "error":
        return {
          color: "#f44336",
          text: "Connection Error",
          description: "Unable to connect to video processing server",
        };
      default:
        return {
          color: "#9e9e9e",
          text: "Disconnected",
          description: "Not connected to video processing server",
        };
    }
  };

  const statusInfo = getStatusInfo();

  return (
    <div className="processed-video-display">
      {/* Connection Status Header */}
      <div className="video-display-header">
        <div className="connection-status">
          <span
            className="status-dot"
            style={{ backgroundColor: statusInfo.color }}
          ></span>
          <div className="status-info">
            <span className="status-text">{statusInfo.text}</span>
            <span className="status-description">{statusInfo.description}</span>
          </div>
        </div>

        {connectionStatus === "error" && onRetryConnection && (
          <button className="retry-connection-btn" onClick={onRetryConnection}>
            Retry Connection
          </button>
        )}
      </div>

      {/* Video Display Area */}
      <div className="video-display-container">
        {processedFrameData?.frame_data ? (
          <div className="video-canvas-container">
            <canvas
              ref={canvasRef}
              className="processed-video-canvas"
              style={{
                maxWidth: "100%",
                height: "auto",
                border: `2px solid ${statusInfo.color}`,
                borderRadius: "8px",
              }}
            />
            <div className="video-overlay-controls">
              <button
                className="toggle-overlay-btn"
                onClick={() => renderFrameToCanvas()}
                title="Refresh display"
              >
                🔄
              </button>
            </div>
          </div>
        ) : connectionStatus === "connected" ? (
          <div className="video-placeholder waiting">
            <div className="loading-spinner"></div>
            <p>Waiting for processed frames...</p>
            <small>MediaPipe processing in progress</small>
          </div>
        ) : connectionStatus === "connecting" ? (
          <div className="video-placeholder connecting">
            <div className="loading-spinner"></div>
            <p>Connecting to video processor...</p>
            <small>Establishing WebSocket connection</small>
          </div>
        ) : (
          <div className="video-placeholder disconnected">
            <div className="placeholder-icon">📹</div>
            <p>Processed video will appear here</p>
            <small>Start streaming to see MediaPipe overlays</small>
          </div>
        )}
      </div>

      {/* Performance Metrics Dashboard */}
      <div className="performance-dashboard">
        <h4>Video Quality & Performance</h4>

        <div className="metrics-grid">
          {/* Real-time Stats */}
          <div className="metric-group">
            <h5>Real-time Stats</h5>
            <div className="metric-item">
              <span className="metric-label">Frame Rate:</span>
              <span
                className={`metric-value ${
                  displayStats.frameRate > 20
                    ? "good"
                    : displayStats.frameRate > 10
                    ? "warning"
                    : "poor"
                }`}
              >
                {displayStats.frameRate} FPS
              </span>
            </div>
            <div className="metric-item">
              <span className="metric-label">Latency:</span>
              <span
                className={`metric-value ${
                  displayStats.latency < 100
                    ? "good"
                    : displayStats.latency < 200
                    ? "warning"
                    : "poor"
                }`}
              >
                {displayStats.latency}ms
              </span>
            </div>
            <div className="metric-item">
              <span className="metric-label">Quality:</span>
              <span
                className={`metric-value ${
                  displayStats.quality === "Excellent"
                    ? "good"
                    : displayStats.quality === "Good"
                    ? "warning"
                    : "poor"
                }`}
              >
                {displayStats.quality}
              </span>
            </div>
            <div className="metric-item">
              <span className="metric-label">Resolution:</span>
              <span className="metric-value">{displayStats.resolution}</span>
            </div>
          </div>

          {/* Processing Stats */}
          <div className="metric-group">
            <h5>Processing Stats</h5>
            <div className="metric-item">
              <span className="metric-label">Total Frames:</span>
              <span className="metric-value">{displayStats.totalFrames}</span>
            </div>
            <div className="metric-item">
              <span className="metric-label">Dropped Frames:</span>
              <span
                className={`metric-value ${
                  displayStats.droppedFrames === 0 ? "good" : "warning"
                }`}
              >
                {displayStats.droppedFrames}
              </span>
            </div>
            <div className="metric-item">
              <span className="metric-label">Avg Latency:</span>
              <span
                className={`metric-value ${
                  performanceMetrics.avgLatency < 100 ? "good" : "warning"
                }`}
              >
                {performanceMetrics.avgLatency}ms
              </span>
            </div>
            <div className="metric-item">
              <span className="metric-label">Max Latency:</span>
              <span className="metric-value">
                {performanceMetrics.maxLatency}ms
              </span>
            </div>
          </div>

          {/* Connection Stats */}
          <div className="metric-group">
            <h5>Connection Health</h5>
            <div className="metric-item">
              <span className="metric-label">Status:</span>
              <span
                className={`metric-value ${
                  connectionStatus === "connected" ? "good" : "poor"
                }`}
              >
                {statusInfo.text}
              </span>
            </div>
            <div className="metric-item">
              <span className="metric-label">Uptime:</span>
              <span className="metric-value">
                {performanceMetrics.connectionUptime > 0
                  ? `${Math.floor(performanceMetrics.connectionUptime / 60)}:${(
                      performanceMetrics.connectionUptime % 60
                    )
                      .toString()
                      .padStart(2, "0")}`
                  : "0:00"}
              </span>
            </div>
            <div className="metric-item">
              <span className="metric-label">Last Frame:</span>
              <span className="metric-value">
                {displayStats.lastFrameTime
                  ? displayStats.lastFrameTime.toLocaleTimeString()
                  : "Never"}
              </span>
            </div>
            <div className="metric-item">
              <span className="metric-label">Stream Health:</span>
              <span
                className={`metric-value ${
                  getConnectionQualityColor() === "#4CAF50"
                    ? "good"
                    : getConnectionQualityColor() === "#ff9800"
                    ? "warning"
                    : "poor"
                }`}
              >
                {getConnectionQualityColor() === "#4CAF50"
                  ? "Excellent"
                  : getConnectionQualityColor() === "#ff9800"
                  ? "Good"
                  : "Poor"}
              </span>
            </div>
          </div>
        </div>

        {/* MediaPipe Landmarks Status */}
        {processedFrameData?.metadata?.landmarks_detected && (
          <div className="landmarks-status">
            <h5>MediaPipe Detection Status</h5>
            <div className="landmarks-grid">
              {Object.entries(
                processedFrameData.metadata.landmarks_detected
              ).map(([landmark, detected]) => (
                <div
                  key={landmark}
                  className={`landmark-status ${
                    detected ? "detected" : "not-detected"
                  }`}
                >
                  <span className="landmark-icon">
                    {landmark === "hands"
                      ? "👐"
                      : landmark === "face"
                      ? "😊"
                      : "🧍"}
                  </span>
                  <span className="landmark-name">
                    {landmark.charAt(0).toUpperCase() + landmark.slice(1)}
                  </span>
                  <span
                    className={`landmark-indicator ${
                      detected ? "active" : "inactive"
                    }`}
                  >
                    {detected ? "✓" : "✗"}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* System Health Indicators */}
      <div className="system-health">
        <h5>System Health</h5>
        <div className="health-indicators">
          <div
            className={`health-indicator ${
              connectionStatus === "connected" ? "healthy" : "unhealthy"
            }`}
          >
            <span className="health-icon">🔗</span>
            <span className="health-label">WebSocket</span>
            <span className="health-status">
              {connectionStatus === "connected" ? "Connected" : "Disconnected"}
            </span>
          </div>

          <div
            className={`health-indicator ${
              displayStats.frameRate > 15 ? "healthy" : "unhealthy"
            }`}
          >
            <span className="health-icon">🎬</span>
            <span className="health-label">Video Stream</span>
            <span className="health-status">
              {displayStats.frameRate > 15 ? "Smooth" : "Choppy"}
            </span>
          </div>

          <div
            className={`health-indicator ${
              displayStats.latency < 150 ? "healthy" : "unhealthy"
            }`}
          >
            <span className="health-icon">⚡</span>
            <span className="health-label">Latency</span>
            <span className="health-status">
              {displayStats.latency < 150 ? "Low" : "High"}
            </span>
          </div>

          <div
            className={`health-indicator ${
              displayStats.quality === "Excellent" ||
              displayStats.quality === "Good"
                ? "healthy"
                : "unhealthy"
            }`}
          >
            <span className="health-icon">🎯</span>
            <span className="health-label">Detection</span>
            <span className="health-status">{displayStats.quality}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProcessedVideoDisplay;
