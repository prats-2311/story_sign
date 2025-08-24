import React, { useState, useEffect, useRef } from "react";

const PerformanceMonitor = ({
  streamingStats,
  processedFrameData,
  connectionStatus,
  onOptimizationChange,
}) => {
  const [performanceData, setPerformanceData] = useState({
    fps: 0,
    latency: 0,
    quality: "unknown",
    cpuUsage: 0,
    memoryUsage: 0,
    frameDropRate: 0,
    processingTime: 0,
  });

  const [optimizationSettings, setOptimizationSettings] = useState({
    adaptiveQuality: true,
    targetFPS: 30,
    maxLatency: 100,
    qualityProfile: "balanced",
  });

  const [alerts, setAlerts] = useState([]);
  const performanceHistory = useRef([]);
  const lastFrameTime = useRef(Date.now());

  // Performance thresholds
  const THRESHOLDS = {
    latency: { good: 50, warning: 100, poor: 200 },
    fps: { good: 25, warning: 15, poor: 10 },
    dropRate: { good: 2, warning: 5, poor: 10 },
    processingTime: { good: 30, warning: 50, poor: 100 },
  };

  useEffect(() => {
    if (processedFrameData && processedFrameData.metadata) {
      updatePerformanceMetrics(processedFrameData.metadata);
    }
  }, [processedFrameData]);

  useEffect(() => {
    // Cleanup old alerts
    const timer = setInterval(() => {
      setAlerts((prev) =>
        prev.filter((alert) => Date.now() - alert.timestamp < 10000)
      );
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const updatePerformanceMetrics = (metadata) => {
    const now = Date.now();
    const timeSinceLastFrame = now - lastFrameTime.current;
    lastFrameTime.current = now;

    // Calculate FPS
    const currentFPS = timeSinceLastFrame > 0 ? 1000 / timeSinceLastFrame : 0;

    // Extract metrics from metadata
    const processingTime = metadata.processing_time_ms || 0;
    const totalLatency = metadata.total_pipeline_time_ms || processingTime;

    // Update performance data
    const newData = {
      fps: currentFPS,
      latency: totalLatency,
      processingTime: processingTime,
      quality: metadata.quality_profile || "unknown",
      frameDropRate: calculateDropRate(),
      cpuUsage: metadata.cpu_usage || 0,
      memoryUsage: metadata.memory_usage || 0,
    };

    setPerformanceData(newData);

    // Store in history (keep last 60 seconds)
    performanceHistory.current.push({
      timestamp: now,
      ...newData,
    });

    if (performanceHistory.current.length > 60) {
      performanceHistory.current.shift();
    }

    // Check for performance issues
    checkPerformanceAlerts(newData);

    // Auto-adjust optimization settings if enabled
    if (optimizationSettings.adaptiveQuality) {
      autoAdjustOptimization(newData);
    }
  };

  const calculateDropRate = () => {
    if (!streamingStats.framesSent || streamingStats.framesSent === 0) {
      return 0;
    }

    const expectedFrames = streamingStats.framesSent;
    const receivedFrames = streamingStats.framesReceived;
    const droppedFrames = Math.max(0, expectedFrames - receivedFrames);

    return (droppedFrames / expectedFrames) * 100;
  };

  const checkPerformanceAlerts = (data) => {
    const newAlerts = [];

    // Latency alerts
    if (data.latency > THRESHOLDS.latency.poor) {
      newAlerts.push({
        id: `latency-${Date.now()}`,
        type: "error",
        message: `High latency detected: ${data.latency.toFixed(1)}ms`,
        suggestion: "Consider reducing video quality or resolution",
        timestamp: Date.now(),
      });
    } else if (data.latency > THRESHOLDS.latency.warning) {
      newAlerts.push({
        id: `latency-${Date.now()}`,
        type: "warning",
        message: `Elevated latency: ${data.latency.toFixed(1)}ms`,
        suggestion: "Monitor system performance",
        timestamp: Date.now(),
      });
    }

    // FPS alerts
    if (data.fps < THRESHOLDS.fps.poor) {
      newAlerts.push({
        id: `fps-${Date.now()}`,
        type: "error",
        message: `Low frame rate: ${data.fps.toFixed(1)} FPS`,
        suggestion: "Check system resources and network connection",
        timestamp: Date.now(),
      });
    }

    // Frame drop alerts
    if (data.frameDropRate > THRESHOLDS.dropRate.poor) {
      newAlerts.push({
        id: `drops-${Date.now()}`,
        type: "error",
        message: `High frame drop rate: ${data.frameDropRate.toFixed(1)}%`,
        suggestion: "Reduce frame rate or improve processing speed",
        timestamp: Date.now(),
      });
    }

    if (newAlerts.length > 0) {
      setAlerts((prev) => [...prev, ...newAlerts]);
    }
  };

  const autoAdjustOptimization = (data) => {
    let newSettings = { ...optimizationSettings };
    let changed = false;

    // Adjust quality profile based on performance
    if (data.latency > optimizationSettings.maxLatency * 1.5) {
      if (newSettings.qualityProfile !== "ultra_performance") {
        const profiles = [
          "high_quality",
          "balanced",
          "high_performance",
          "ultra_performance",
        ];
        const currentIndex = profiles.indexOf(newSettings.qualityProfile);
        if (currentIndex < profiles.length - 1) {
          newSettings.qualityProfile = profiles[currentIndex + 1];
          changed = true;
        }
      }
    } else if (data.latency < optimizationSettings.maxLatency * 0.6) {
      if (newSettings.qualityProfile !== "high_quality") {
        const profiles = [
          "ultra_performance",
          "high_performance",
          "balanced",
          "high_quality",
        ];
        const currentIndex = profiles.indexOf(newSettings.qualityProfile);
        if (currentIndex < profiles.length - 1) {
          newSettings.qualityProfile = profiles[currentIndex + 1];
          changed = true;
        }
      }
    }

    // Adjust target FPS based on performance
    if (data.fps < newSettings.targetFPS * 0.8) {
      newSettings.targetFPS = Math.max(15, newSettings.targetFPS - 5);
      changed = true;
    } else if (data.fps > newSettings.targetFPS * 1.2) {
      newSettings.targetFPS = Math.min(60, newSettings.targetFPS + 5);
      changed = true;
    }

    if (changed) {
      setOptimizationSettings(newSettings);
      onOptimizationChange?.(newSettings);
    }
  };

  const getMetricStatus = (value, thresholds) => {
    if (value <= thresholds.good) return "good";
    if (value <= thresholds.warning) return "warning";
    return "poor";
  };

  const getAverageMetrics = (timeWindow = 30) => {
    const cutoff = Date.now() - timeWindow * 1000;
    const recentData = performanceHistory.current.filter(
      (item) => item.timestamp > cutoff
    );

    if (recentData.length === 0) return null;

    return {
      avgFPS:
        recentData.reduce((sum, item) => sum + item.fps, 0) / recentData.length,
      avgLatency:
        recentData.reduce((sum, item) => sum + item.latency, 0) /
        recentData.length,
      avgProcessingTime:
        recentData.reduce((sum, item) => sum + item.processingTime, 0) /
        recentData.length,
    };
  };

  const handleOptimizationToggle = (setting, value) => {
    const newSettings = { ...optimizationSettings, [setting]: value };
    setOptimizationSettings(newSettings);
    onOptimizationChange?.(newSettings);
  };

  const dismissAlert = (alertId) => {
    setAlerts((prev) => prev.filter((alert) => alert.id !== alertId));
  };

  const averageMetrics = getAverageMetrics();

  return (
    <div className="performance-monitor">
      <div className="performance-header">
        <h4>🚀 Performance Monitor</h4>
        <div className="optimization-controls">
          <label className="toggle-control">
            <input
              type="checkbox"
              checked={optimizationSettings.adaptiveQuality}
              onChange={(e) =>
                handleOptimizationToggle("adaptiveQuality", e.target.checked)
              }
            />
            <span>Adaptive Quality</span>
          </label>
        </div>
      </div>

      {/* Performance Alerts */}
      {alerts.length > 0 && (
        <div className="performance-alerts">
          {alerts.map((alert) => (
            <div key={alert.id} className={`alert alert-${alert.type}`}>
              <div className="alert-content">
                <div className="alert-message">{alert.message}</div>
                <div className="alert-suggestion">{alert.suggestion}</div>
              </div>
              <button
                className="alert-dismiss"
                onClick={() => dismissAlert(alert.id)}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Real-time Metrics */}
      <div className="metrics-grid">
        <div className="metric-group">
          <h5>📊 Real-time Performance</h5>
          <div className="metric-item">
            <span className="metric-label">Frame Rate</span>
            <span
              className={`metric-value ${getMetricStatus(
                performanceData.fps,
                THRESHOLDS.fps
              )}`}
            >
              {performanceData.fps.toFixed(1)} FPS
            </span>
          </div>
          <div className="metric-item">
            <span className="metric-label">Latency</span>
            <span
              className={`metric-value ${getMetricStatus(
                performanceData.latency,
                THRESHOLDS.latency
              )}`}
            >
              {performanceData.latency.toFixed(1)}ms
            </span>
          </div>
          <div className="metric-item">
            <span className="metric-label">Processing Time</span>
            <span
              className={`metric-value ${getMetricStatus(
                performanceData.processingTime,
                THRESHOLDS.processingTime
              )}`}
            >
              {performanceData.processingTime.toFixed(1)}ms
            </span>
          </div>
          <div className="metric-item">
            <span className="metric-label">Frame Drops</span>
            <span
              className={`metric-value ${getMetricStatus(
                performanceData.frameDropRate,
                THRESHOLDS.dropRate
              )}`}
            >
              {performanceData.frameDropRate.toFixed(1)}%
            </span>
          </div>
        </div>

        {/* Average Metrics */}
        {averageMetrics && (
          <div className="metric-group">
            <h5>📈 30-Second Average</h5>
            <div className="metric-item">
              <span className="metric-label">Avg Frame Rate</span>
              <span className="metric-value">
                {averageMetrics.avgFPS.toFixed(1)} FPS
              </span>
            </div>
            <div className="metric-item">
              <span className="metric-label">Avg Latency</span>
              <span className="metric-value">
                {averageMetrics.avgLatency.toFixed(1)}ms
              </span>
            </div>
            <div className="metric-item">
              <span className="metric-label">Avg Processing</span>
              <span className="metric-value">
                {averageMetrics.avgProcessingTime.toFixed(1)}ms
              </span>
            </div>
          </div>
        )}

        {/* Optimization Settings */}
        <div className="metric-group">
          <h5>⚙️ Optimization Settings</h5>
          <div className="metric-item">
            <span className="metric-label">Quality Profile</span>
            <select
              className="metric-control"
              value={optimizationSettings.qualityProfile}
              onChange={(e) =>
                handleOptimizationToggle("qualityProfile", e.target.value)
              }
            >
              <option value="ultra_performance">Ultra Performance</option>
              <option value="high_performance">High Performance</option>
              <option value="balanced">Balanced</option>
              <option value="high_quality">High Quality</option>
            </select>
          </div>
          <div className="metric-item">
            <span className="metric-label">Target FPS</span>
            <input
              type="range"
              min="15"
              max="60"
              step="5"
              value={optimizationSettings.targetFPS}
              onChange={(e) =>
                handleOptimizationToggle("targetFPS", parseInt(e.target.value))
              }
              className="metric-slider"
            />
            <span className="metric-value">
              {optimizationSettings.targetFPS}
            </span>
          </div>
          <div className="metric-item">
            <span className="metric-label">Max Latency</span>
            <input
              type="range"
              min="50"
              max="200"
              step="10"
              value={optimizationSettings.maxLatency}
              onChange={(e) =>
                handleOptimizationToggle("maxLatency", parseInt(e.target.value))
              }
              className="metric-slider"
            />
            <span className="metric-value">
              {optimizationSettings.maxLatency}ms
            </span>
          </div>
        </div>

        {/* System Health */}
        <div className="metric-group">
          <h5>💻 System Health</h5>
          <div className="metric-item">
            <span className="metric-label">Connection</span>
            <span
              className={`metric-value ${
                connectionStatus === "connected" ? "good" : "poor"
              }`}
            >
              {connectionStatus}
            </span>
          </div>
          <div className="metric-item">
            <span className="metric-label">Frames Sent</span>
            <span className="metric-value">
              {streamingStats.framesSent || 0}
            </span>
          </div>
          <div className="metric-item">
            <span className="metric-label">Frames Received</span>
            <span className="metric-value">
              {streamingStats.framesReceived || 0}
            </span>
          </div>
          <div className="metric-item">
            <span className="metric-label">Quality Mode</span>
            <span className="metric-value">{performanceData.quality}</span>
          </div>
        </div>
      </div>

      {/* Performance Tips */}
      <div className="performance-tips">
        <h5>💡 Performance Tips</h5>
        <ul>
          <li>Close other applications to free up system resources</li>
          <li>Ensure good lighting for better MediaPipe detection</li>
          <li>Use a wired internet connection for stability</li>
          <li>Enable adaptive quality for automatic optimization</li>
          <li>Lower resolution if experiencing high latency</li>
        </ul>
      </div>
    </div>
  );
};

export default PerformanceMonitor;
