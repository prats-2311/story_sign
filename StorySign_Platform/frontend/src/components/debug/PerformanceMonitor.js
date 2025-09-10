import React, { useState, useEffect } from "react";
import { usePerformanceMonitoring } from "../../utils/performance";
import {
  performanceTestRunner,
  runQuickPerformanceCheck,
} from "../../tests/performance/performance-test";
import "./PerformanceMonitor.css";

/**
 * Performance monitoring component for development and testing
 * Shows real-time performance metrics and allows running performance tests
 */
const PerformanceMonitor = ({ isVisible = false, onToggle }) => {
  const { metrics, memoryUsage, generateReport } = usePerformanceMonitoring();
  const [testResults, setTestResults] = useState(null);
  const [isRunningTests, setIsRunningTests] = useState(false);
  const [activeTab, setActiveTab] = useState("metrics");

  // Run quick performance check on mount
  useEffect(() => {
    if (isVisible) {
      runQuickPerformanceCheck().then(setTestResults);
    }
  }, [isVisible]);

  const handleRunFullTests = async () => {
    setIsRunningTests(true);
    try {
      const results = await performanceTestRunner.runAllTests();
      setTestResults(results);
    } catch (error) {
      console.error("Performance tests failed:", error);
    } finally {
      setIsRunningTests(false);
    }
  };

  const handleRunQuickCheck = async () => {
    setIsRunningTests(true);
    try {
      const results = await runQuickPerformanceCheck();
      setTestResults(results);
    } catch (error) {
      console.error("Quick performance check failed:", error);
    } finally {
      setIsRunningTests(false);
    }
  };

  const formatMemoryUsage = usage => {
    if (!usage) return "N/A";
    return `${usage.used}MB / ${usage.total}MB (${Math.round(
      (usage.used / usage.total) * 100
    )}%)`;
  };

  const formatDuration = duration => {
    if (typeof duration !== "number") return "N/A";
    return `${Math.round(duration)}ms`;
  };

  const getPerformanceStatus = () => {
    if (!testResults) return "unknown";

    if (testResults.tests?.routeTransitions?.summary?.successRate > 90) {
      return "excellent";
    } else if (testResults.tests?.routeTransitions?.summary?.successRate > 70) {
      return "good";
    } else if (testResults.tests?.routeTransitions?.summary?.successRate > 50) {
      return "fair";
    } else {
      return "poor";
    }
  };

  if (!isVisible) {
    return (
      <button
        className="performance-monitor-toggle"
        onClick={onToggle}
        title="Show Performance Monitor"
      >
        📊
      </button>
    );
  }

  return (
    <div className="performance-monitor">
      <div className="performance-monitor-header">
        <h3>Performance Monitor</h3>
        <button
          className="close-button"
          onClick={onToggle}
          aria-label="Close Performance Monitor"
        >
          ×
        </button>
      </div>

      <div className="performance-monitor-tabs">
        <button
          className={`tab ${activeTab === "metrics" ? "active" : ""}`}
          onClick={() => setActiveTab("metrics")}
        >
          Metrics
        </button>
        <button
          className={`tab ${activeTab === "memory" ? "active" : ""}`}
          onClick={() => setActiveTab("memory")}
        >
          Memory
        </button>
        <button
          className={`tab ${activeTab === "tests" ? "active" : ""}`}
          onClick={() => setActiveTab("tests")}
        >
          Tests
        </button>
      </div>

      <div className="performance-monitor-content">
        {activeTab === "metrics" && (
          <div className="metrics-tab">
            <div className="performance-status">
              <div className={`status-indicator ${getPerformanceStatus()}`}>
                {getPerformanceStatus().toUpperCase()}
              </div>
            </div>

            <div className="metrics-grid">
              <div className="metric-card">
                <h4>Route Transitions</h4>
                <div className="metric-value">
                  {testResults?.tests?.routeTransitions?.summary
                    ?.averageDuration
                    ? formatDuration(
                        testResults.tests.routeTransitions.summary
                          .averageDuration
                      )
                    : "N/A"}
                </div>
                <div className="metric-label">Average Duration</div>
              </div>

              <div className="metric-card">
                <h4>Success Rate</h4>
                <div className="metric-value">
                  {testResults?.tests?.routeTransitions?.summary?.successRate
                    ? `${Math.round(
                        testResults.tests.routeTransitions.summary.successRate
                      )}%`
                    : "N/A"}
                </div>
                <div className="metric-label">Route Transitions</div>
              </div>

              <div className="metric-card">
                <h4>Memory Usage</h4>
                <div className="metric-value">
                  {memoryUsage ? `${memoryUsage.used}MB` : "N/A"}
                </div>
                <div className="metric-label">Current Usage</div>
              </div>

              <div className="metric-card">
                <h4>Active Metrics</h4>
                <div className="metric-value">
                  {Object.keys(metrics).length}
                </div>
                <div className="metric-label">Tracked Operations</div>
              </div>
            </div>

            <div className="recent-metrics">
              <h4>Recent Performance Metrics</h4>
              <div className="metrics-list">
                {Object.entries(metrics)
                  .slice(-5)
                  .map(([name, metric]) => (
                    <div key={name} className="metric-item">
                      <span className="metric-name">{name}</span>
                      <span className="metric-duration">
                        {formatDuration(metric.duration)}
                      </span>
                    </div>
                  ))}
                {Object.keys(metrics).length === 0 && (
                  <div className="no-metrics">No metrics available</div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === "memory" && (
          <div className="memory-tab">
            <div className="memory-overview">
              <h4>Memory Overview</h4>
              {memoryUsage ? (
                <div className="memory-stats">
                  <div className="memory-stat">
                    <label>Used:</label>
                    <span>{memoryUsage.used}MB</span>
                  </div>
                  <div className="memory-stat">
                    <label>Total:</label>
                    <span>{memoryUsage.total}MB</span>
                  </div>
                  <div className="memory-stat">
                    <label>Limit:</label>
                    <span>{memoryUsage.limit}MB</span>
                  </div>
                  <div className="memory-usage-bar">
                    <div
                      className="memory-usage-fill"
                      style={{
                        width: `${
                          (memoryUsage.used / memoryUsage.total) * 100
                        }%`,
                      }}
                    />
                  </div>
                </div>
              ) : (
                <div className="no-memory-data">
                  Memory monitoring not available in this browser
                </div>
              )}
            </div>

            {testResults?.tests?.memoryUsage && (
              <div className="memory-test-results">
                <h4>Memory Leak Test Results</h4>
                <div className="memory-test-stats">
                  <div className="memory-test-stat">
                    <label>Initial:</label>
                    <span>{testResults.tests.memoryUsage.initial}MB</span>
                  </div>
                  <div className="memory-test-stat">
                    <label>Final:</label>
                    <span>{testResults.tests.memoryUsage.final}MB</span>
                  </div>
                  <div className="memory-test-stat">
                    <label>Increase:</label>
                    <span
                      className={
                        testResults.tests.memoryUsage.hasLeak
                          ? "warning"
                          : "good"
                      }
                    >
                      +{testResults.tests.memoryUsage.memoryIncrease}MB
                    </span>
                  </div>
                  <div className="memory-test-stat">
                    <label>Status:</label>
                    <span
                      className={
                        testResults.tests.memoryUsage.hasLeak
                          ? "warning"
                          : "good"
                      }
                    >
                      {testResults.tests.memoryUsage.hasLeak
                        ? "Potential Leak"
                        : "Normal"}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === "tests" && (
          <div className="tests-tab">
            <div className="test-controls">
              <button
                className="test-button primary"
                onClick={handleRunQuickCheck}
                disabled={isRunningTests}
              >
                {isRunningTests ? "Running..." : "Quick Check"}
              </button>
              <button
                className="test-button secondary"
                onClick={handleRunFullTests}
                disabled={isRunningTests}
              >
                {isRunningTests ? "Running..." : "Full Test Suite"}
              </button>
            </div>

            {testResults && (
              <div className="test-results">
                <h4>Test Results</h4>

                {testResults.tests?.routeTransitions && (
                  <div className="test-section">
                    <h5>Route Transitions</h5>
                    <div className="test-summary">
                      <span>
                        Success Rate:{" "}
                        {Math.round(
                          testResults.tests.routeTransitions.summary.successRate
                        )}
                        %
                      </span>
                      <span>
                        Average:{" "}
                        {formatDuration(
                          testResults.tests.routeTransitions.summary
                            .averageDuration
                        )}
                      </span>
                      <span>
                        Max:{" "}
                        {formatDuration(
                          testResults.tests.routeTransitions.summary.maxDuration
                        )}
                      </span>
                    </div>
                  </div>
                )}

                {testResults.tests?.memoryUsage && (
                  <div className="test-section">
                    <h5>Memory Usage</h5>
                    <div className="test-summary">
                      <span>
                        Trend: {testResults.tests.memoryUsage.analysis?.trend}
                      </span>
                      <span>
                        Severity:{" "}
                        {testResults.tests.memoryUsage.analysis?.severity}
                      </span>
                      <span>
                        Leak:{" "}
                        {testResults.tests.memoryUsage.hasLeak ? "Yes" : "No"}
                      </span>
                    </div>
                  </div>
                )}

                {testResults.tests?.componentRendering && (
                  <div className="test-section">
                    <h5>Component Rendering</h5>
                    <div className="component-stats">
                      {testResults.tests.componentRendering
                        .slice(0, 5)
                        .map(stat => (
                          <div
                            key={stat.componentName}
                            className="component-stat"
                          >
                            <span className="component-name">
                              {stat.componentName}
                            </span>
                            <span className="component-time">
                              {formatDuration(stat.averageTime)}
                            </span>
                          </div>
                        ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default PerformanceMonitor;
