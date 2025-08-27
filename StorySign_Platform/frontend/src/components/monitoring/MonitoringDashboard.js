import React, { useState, useEffect, useCallback } from "react";
import "./MonitoringDashboard.css";

const MonitoringDashboard = () => {
  const [systemHealth, setSystemHealth] = useState(null);
  const [metrics, setMetrics] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [performance, setPerformance] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshInterval, setRefreshInterval] = useState(30000); // 30 seconds
  const [selectedTimeRange, setSelectedTimeRange] = useState(24); // 24 hours

  // Fetch system health data
  const fetchSystemHealth = useCallback(async () => {
    try {
      const response = await fetch("/api/v1/monitoring/health");
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setSystemHealth(data);
    } catch (err) {
      console.error("Failed to fetch system health:", err);
      setError(err.message);
    }
  }, []);

  // Fetch current metrics
  const fetchMetrics = useCallback(async () => {
    try {
      const response = await fetch("/api/v1/monitoring/metrics");
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setMetrics(data.metrics || {});
    } catch (err) {
      console.error("Failed to fetch metrics:", err);
    }
  }, []);

  // Fetch active alerts
  const fetchAlerts = useCallback(async () => {
    try {
      const response = await fetch("/api/v1/monitoring/alerts");
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setAlerts(data.alerts || []);
    } catch (err) {
      console.error("Failed to fetch alerts:", err);
    }
  }, []);

  // Fetch performance summary
  const fetchPerformance = useCallback(async () => {
    try {
      const response = await fetch(
        `/api/v1/monitoring/performance?hours=${selectedTimeRange}`
      );
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setPerformance(data);
    } catch (err) {
      console.error("Failed to fetch performance data:", err);
    }
  }, [selectedTimeRange]);

  // Fetch all data
  const fetchAllData = useCallback(async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchSystemHealth(),
        fetchMetrics(),
        fetchAlerts(),
        fetchPerformance(),
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [fetchSystemHealth, fetchMetrics, fetchAlerts, fetchPerformance]);

  // Initial load and refresh interval
  useEffect(() => {
    fetchAllData();

    const interval = setInterval(fetchAllData, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchAllData, refreshInterval]);

  // Acknowledge alert
  const acknowledgeAlert = async (alertId) => {
    try {
      const response = await fetch(
        `/api/v1/monitoring/alerts/${alertId}/acknowledge`,
        {
          method: "POST",
        }
      );
      if (response.ok) {
        // Refresh alerts
        fetchAlerts();
      }
    } catch (err) {
      console.error("Failed to acknowledge alert:", err);
    }
  };

  // Get status color
  const getStatusColor = (status) => {
    switch (status) {
      case "healthy":
        return "#4CAF50";
      case "warning":
        return "#FF9800";
      case "unhealthy":
        return "#F44336";
      case "critical":
        return "#D32F2F";
      default:
        return "#9E9E9E";
    }
  };

  // Get alert severity color
  const getAlertColor = (severity) => {
    switch (severity) {
      case "info":
        return "#2196F3";
      case "warning":
        return "#FF9800";
      case "error":
        return "#F44336";
      case "critical":
        return "#D32F2F";
      default:
        return "#9E9E9E";
    }
  };

  // Format metric value
  const formatMetricValue = (value, unit) => {
    if (typeof value !== "number") return "N/A";

    switch (unit) {
      case "percent":
        return `${value.toFixed(1)}%`;
      case "seconds":
        return `${(value * 1000).toFixed(0)}ms`;
      case "bytes":
        if (value > 1024 * 1024 * 1024) {
          return `${(value / (1024 * 1024 * 1024)).toFixed(2)} GB`;
        } else if (value > 1024 * 1024) {
          return `${(value / (1024 * 1024)).toFixed(2)} MB`;
        } else if (value > 1024) {
          return `${(value / 1024).toFixed(2)} KB`;
        }
        return `${value.toFixed(0)} B`;
      case "count":
        return value.toFixed(0);
      default:
        return value.toFixed(2);
    }
  };

  if (loading && !systemHealth) {
    return (
      <div className="monitoring-dashboard">
        <div className="loading">Loading monitoring data...</div>
      </div>
    );
  }

  if (error && !systemHealth) {
    return (
      <div className="monitoring-dashboard">
        <div className="error">Error loading monitoring data: {error}</div>
      </div>
    );
  }

  return (
    <div className="monitoring-dashboard">
      <div className="dashboard-header">
        <h1>System Monitoring Dashboard</h1>
        <div className="dashboard-controls">
          <select
            value={selectedTimeRange}
            onChange={(e) => setSelectedTimeRange(parseInt(e.target.value))}
          >
            <option value={1}>Last Hour</option>
            <option value={6}>Last 6 Hours</option>
            <option value={24}>Last 24 Hours</option>
            <option value={168}>Last Week</option>
          </select>
          <select
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(parseInt(e.target.value))}
          >
            <option value={10000}>10 seconds</option>
            <option value={30000}>30 seconds</option>
            <option value={60000}>1 minute</option>
            <option value={300000}>5 minutes</option>
          </select>
          <button onClick={fetchAllData} disabled={loading}>
            {loading ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </div>

      {/* System Health Overview */}
      <div className="health-overview">
        <div className="health-card">
          <h2>System Health</h2>
          {systemHealth && (
            <div className="health-status">
              <div
                className="status-indicator"
                style={{
                  backgroundColor: getStatusColor(systemHealth.overall_status),
                }}
              >
                {systemHealth.overall_status.toUpperCase()}
              </div>
              <div className="health-summary">
                <div>Components: {systemHealth.components?.length || 0}</div>
                <div>
                  Active Alerts:{" "}
                  {systemHealth.metrics_summary?.active_alerts || 0}
                </div>
                <div>
                  Critical: {systemHealth.metrics_summary?.critical_alerts || 0}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Active Alerts */}
        <div className="alerts-card">
          <h2>Active Alerts ({alerts.length})</h2>
          <div className="alerts-list">
            {alerts.length === 0 ? (
              <div className="no-alerts">No active alerts</div>
            ) : (
              alerts.slice(0, 5).map((alert) => (
                <div key={alert.id} className="alert-item">
                  <div
                    className="alert-severity"
                    style={{ backgroundColor: getAlertColor(alert.severity) }}
                  >
                    {alert.severity}
                  </div>
                  <div className="alert-content">
                    <div className="alert-title">{alert.title}</div>
                    <div className="alert-message">{alert.message}</div>
                    <div className="alert-time">
                      {new Date(alert.timestamp).toLocaleString()}
                    </div>
                  </div>
                  <button
                    className="alert-ack"
                    onClick={() => acknowledgeAlert(alert.id)}
                  >
                    ACK
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Component Health */}
      <div className="components-section">
        <h2>Component Health</h2>
        <div className="components-grid">
          {systemHealth?.components?.map((component) => (
            <div key={component.component} className="component-card">
              <div className="component-header">
                <h3>{component.component}</h3>
                <div
                  className="component-status"
                  style={{ backgroundColor: getStatusColor(component.status) }}
                >
                  {component.status}
                </div>
              </div>
              <div className="component-details">
                <div className="component-message">{component.message}</div>
                <div className="component-response-time">
                  Response: {component.response_time_ms?.toFixed(0)}ms
                </div>
                {component.details &&
                  Object.keys(component.details).length > 0 && (
                    <div className="component-metrics">
                      {Object.entries(component.details).map(([key, value]) => (
                        <div key={key} className="metric-item">
                          <span className="metric-key">{key}:</span>
                          <span className="metric-value">
                            {typeof value === "object"
                              ? JSON.stringify(value)
                              : String(value)}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="metrics-section">
        <h2>Key Metrics</h2>
        <div className="metrics-grid">
          {Object.entries(metrics).map(([metricName, metricData]) => (
            <div key={metricName} className="metric-card">
              <h3>
                {metricName
                  .replace(/_/g, " ")
                  .replace(/\b\w/g, (l) => l.toUpperCase())}
              </h3>
              <div className="metric-value">
                {formatMetricValue(metricData.value, metricData.unit)}
              </div>
              <div className="metric-timestamp">
                Updated: {new Date(metricData.timestamp).toLocaleTimeString()}
              </div>
              {metricData.tags && (
                <div className="metric-tags">
                  {Object.entries(metricData.tags).map(([key, value]) => (
                    <span key={key} className="metric-tag">
                      {key}: {value}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Performance Summary */}
      {performance.performance_metrics && (
        <div className="performance-section">
          <h2>Performance Summary ({selectedTimeRange}h)</h2>
          <div className="performance-grid">
            {Object.entries(performance.performance_metrics).map(
              ([metricName, metricData]) => (
                <div key={metricName} className="performance-card">
                  <h3>
                    {metricName
                      .replace(/_/g, " ")
                      .replace(/\b\w/g, (l) => l.toUpperCase())}
                  </h3>
                  <div className="performance-stats">
                    <div className="stat">
                      <span className="stat-label">Current:</span>
                      <span className="stat-value">
                        {metricData.current?.toFixed(2)}
                      </span>
                    </div>
                    <div className="stat">
                      <span className="stat-label">Average:</span>
                      <span className="stat-value">
                        {metricData.average?.toFixed(2)}
                      </span>
                    </div>
                    <div className="stat">
                      <span className="stat-label">Min:</span>
                      <span className="stat-value">
                        {metricData.min?.toFixed(2)}
                      </span>
                    </div>
                    <div className="stat">
                      <span className="stat-label">Max:</span>
                      <span className="stat-value">
                        {metricData.max?.toFixed(2)}
                      </span>
                    </div>
                  </div>
                  <div className="performance-trend">
                    Trend: {metricData.trend || "stable"}
                  </div>
                </div>
              )
            )}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="dashboard-footer">
        <div className="last-updated">
          Last updated: {new Date().toLocaleString()}
        </div>
        <div className="refresh-info">
          Auto-refresh: {refreshInterval / 1000}s
        </div>
      </div>
    </div>
  );
};

export default MonitoringDashboard;
