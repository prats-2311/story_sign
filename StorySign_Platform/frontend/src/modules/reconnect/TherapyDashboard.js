import React, { useMemo } from "react";
import Button from "../../components/common/Button";
import "./TherapyDashboard.css";

/**
 * TherapyDashboard component for session progress visualization
 * Shows session results, movement metrics, and therapeutic progress
 */
const TherapyDashboard = ({
  sessionData,
  sessionDuration,
  exerciseType,
  onNewSession,
}) => {
  // Calculate comprehensive session results
  const sessionResults = useMemo(() => {
    if (!sessionData || !sessionData.movementData.length) {
      return {
        totalMovements: 0,
        averageQuality: 0,
        jointMetrics: {},
        overallScore: 0,
        timeSpent: sessionDuration || 0,
        performance: "No Data",
        improvements: [],
        recommendations: [],
        progressChart: [],
      };
    }

    const movements = sessionData.movementData;
    const jointAngles = sessionData.jointAngles;
    const metrics = sessionData.metrics;

    // Calculate joint-specific metrics
    const jointMetrics = {};
    Object.keys(jointAngles).forEach((joint) => {
      const angles = jointAngles[joint];
      if (angles && angles.length > 0) {
        const min = Math.min(...angles);
        const max = Math.max(...angles);
        const avg =
          angles.reduce((sum, angle) => sum + angle, 0) / angles.length;
        const range = max - min;

        jointMetrics[joint] = {
          range,
          average: avg,
          min,
          max,
          measurements: angles.length,
          improvement: calculateImprovement(angles),
        };
      }
    });

    // Calculate average quality
    const averageQuality =
      metrics.length > 0
        ? metrics.reduce((sum, metric) => sum + (metric.quality || 0), 0) /
          metrics.length
        : 0;

    // Calculate overall score (combination of quality, range, and consistency)
    const rangeScore =
      Object.values(jointMetrics).reduce(
        (sum, joint) => sum + Math.min(joint.range / 100, 1),
        0
      ) / Math.max(Object.keys(jointMetrics).length, 1);
    const overallScore = Math.round(
      (averageQuality * 0.4 +
        rangeScore * 0.4 +
        (movements.length > 10 ? 0.2 : movements.length / 50)) *
        100
    );

    // Performance assessment
    let performance = "Needs Improvement";
    if (overallScore >= 85) performance = "Excellent";
    else if (overallScore >= 70) performance = "Good";
    else if (overallScore >= 55) performance = "Fair";

    // Generate improvements and recommendations
    const improvements = generateImprovements(jointMetrics, averageQuality);
    const recommendations = generateRecommendations(
      jointMetrics,
      averageQuality,
      sessionDuration
    );

    // Create progress chart data
    const progressChart = createProgressChart(metrics);

    return {
      totalMovements: movements.length,
      averageQuality: Math.round(averageQuality * 100) / 100,
      jointMetrics,
      overallScore,
      timeSpent: sessionDuration || 0,
      performance,
      improvements,
      recommendations,
      progressChart,
    };
  }, [sessionData, sessionDuration]);

  // Calculate improvement trend for a joint
  const calculateImprovement = (angles) => {
    if (angles.length < 5) return 0;

    const firstHalf = angles.slice(0, Math.floor(angles.length / 2));
    const secondHalf = angles.slice(Math.floor(angles.length / 2));

    const firstAvg =
      firstHalf.reduce((sum, angle) => sum + angle, 0) / firstHalf.length;
    const secondAvg =
      secondHalf.reduce((sum, angle) => sum + angle, 0) / secondHalf.length;

    return secondAvg - firstAvg;
  };

  // Generate improvement highlights
  const generateImprovements = (jointMetrics, averageQuality) => {
    const improvements = [];

    if (averageQuality >= 0.7) {
      improvements.push("Maintained good movement quality throughout session");
    }

    Object.entries(jointMetrics).forEach(([joint, metrics]) => {
      if (metrics.improvement > 5) {
        improvements.push(
          `Improved range of motion in ${getJointInfo(joint).name}`
        );
      }
      if (metrics.range > 90) {
        improvements.push(`Excellent mobility in ${getJointInfo(joint).name}`);
      }
    });

    if (sessionResults.totalMovements >= 20) {
      improvements.push("Completed a comprehensive movement session");
    }

    return improvements;
  };

  // Generate recommendations
  const generateRecommendations = (jointMetrics, averageQuality, duration) => {
    const recommendations = [];

    if (averageQuality < 0.6) {
      recommendations.push("Focus on slower, more controlled movements");
      recommendations.push("Consider reducing range initially to improve form");
    }

    Object.entries(jointMetrics).forEach(([joint, metrics]) => {
      if (metrics.range < 60) {
        recommendations.push(
          `Work on increasing flexibility in ${getJointInfo(joint).name}`
        );
      }
      if (metrics.improvement < -5) {
        recommendations.push(
          `${
            getJointInfo(joint).name
          } showed fatigue - consider shorter sessions`
        );
      }
    });

    if (duration < 300000) {
      // Less than 5 minutes
      recommendations.push(
        "Try longer sessions for better therapeutic benefit"
      );
    }

    if (Object.keys(jointMetrics).length < 3) {
      recommendations.push(
        "Ensure full body visibility for comprehensive analysis"
      );
    }

    return recommendations;
  };

  // Create progress chart data
  const createProgressChart = (metrics) => {
    if (!metrics || metrics.length < 5) return [];

    const chunkSize = Math.max(1, Math.floor(metrics.length / 10));
    const chunks = [];

    for (let i = 0; i < metrics.length; i += chunkSize) {
      const chunk = metrics.slice(i, i + chunkSize);
      const avgQuality =
        chunk.reduce((sum, m) => sum + (m.quality || 0), 0) / chunk.length;
      chunks.push({
        time: i + chunkSize / 2,
        quality: avgQuality,
      });
    }

    return chunks;
  };

  // Get joint display information
  const getJointInfo = (jointName) => {
    const jointMap = {
      left_shoulder: { name: "Left Shoulder", icon: "🤲", color: "#3498db" },
      right_shoulder: { name: "Right Shoulder", icon: "🤲", color: "#3498db" },
      left_elbow: { name: "Left Elbow", icon: "💪", color: "#e74c3c" },
      right_elbow: { name: "Right Elbow", icon: "💪", color: "#e74c3c" },
      left_hip: { name: "Left Hip", icon: "🦵", color: "#27ae60" },
      right_hip: { name: "Right Hip", icon: "🦵", color: "#27ae60" },
      left_knee: { name: "Left Knee", icon: "🦴", color: "#f39c12" },
      right_knee: { name: "Right Knee", icon: "🦴", color: "#f39c12" },
      spine: { name: "Spine", icon: "🏃", color: "#9b59b6" },
      neck: { name: "Neck", icon: "🦢", color: "#e67e22" },
    };
    return (
      jointMap[jointName] || { name: jointName, icon: "⚪", color: "#95a5a6" }
    );
  };

  // Format duration
  const formatDuration = (milliseconds) => {
    const seconds = Math.floor(milliseconds / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;

    if (minutes > 0) {
      return `${minutes}m ${remainingSeconds}s`;
    }
    return `${remainingSeconds}s`;
  };

  // Get performance color
  const getPerformanceColor = (performance) => {
    switch (performance) {
      case "Excellent":
        return "#27ae60";
      case "Good":
        return "#f39c12";
      case "Fair":
        return "#e67e22";
      default:
        return "#e74c3c";
    }
  };

  return (
    <div className="therapy-dashboard">
      <div className="dashboard-header">
        <h2>Therapy Session Complete! 🎯</h2>
        <p>Here's your movement analysis and therapeutic progress</p>
      </div>

      {/* Overall Score */}
      <div className="overall-score">
        <div className="score-circle">
          <div className="score-value">{sessionResults.overallScore}</div>
          <div className="score-label">Therapy Score</div>
        </div>
        <div className="score-details">
          <h3
            style={{ color: getPerformanceColor(sessionResults.performance) }}
          >
            {sessionResults.performance}
          </h3>
          {exerciseType && (
            <p>
              Exercise: {exerciseType.name} {exerciseType.icon}
            </p>
          )}
          <p>Session Duration: {formatDuration(sessionResults.timeSpent)}</p>
          <p>
            Movement Quality: {Math.round(sessionResults.averageQuality * 100)}%
          </p>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="key-metrics">
        <h3>Session Metrics</h3>
        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-value">{sessionResults.totalMovements}</div>
            <div className="metric-label">Total Movements</div>
          </div>

          <div className="metric-card">
            <div className="metric-value">
              {Object.keys(sessionResults.jointMetrics).length}
            </div>
            <div className="metric-label">Joints Analyzed</div>
          </div>

          <div className="metric-card">
            <div className="metric-value">
              {Math.round(sessionResults.averageQuality * 100)}%
            </div>
            <div className="metric-label">Avg Quality</div>
          </div>

          <div className="metric-card">
            <div className="metric-value">
              {Object.values(sessionResults.jointMetrics).reduce(
                (sum, joint) => sum + joint.range,
                0
              ) /
                Math.max(Object.keys(sessionResults.jointMetrics).length, 1) ||
                0}
              °
            </div>
            <div className="metric-label">Avg Range</div>
          </div>
        </div>
      </div>

      {/* Progress Chart */}
      {sessionResults.progressChart.length > 0 && (
        <div className="progress-chart">
          <h3>Movement Quality Over Time</h3>
          <div className="chart-container">
            <div className="chart-area">
              {sessionResults.progressChart.map((point, index) => (
                <div
                  key={index}
                  className="chart-point"
                  style={{
                    left: `${
                      (point.time / sessionResults.totalMovements) * 100
                    }%`,
                    bottom: `${point.quality * 100}%`,
                    backgroundColor:
                      point.quality >= 0.7
                        ? "#27ae60"
                        : point.quality >= 0.5
                        ? "#f39c12"
                        : "#e74c3c",
                  }}
                  title={`Quality: ${Math.round(point.quality * 100)}%`}
                ></div>
              ))}
            </div>
            <div className="chart-labels">
              <span>Session Start</span>
              <span>Session End</span>
            </div>
          </div>
        </div>
      )}

      {/* Joint Analysis */}
      {Object.keys(sessionResults.jointMetrics).length > 0 && (
        <div className="joint-analysis">
          <h3>Joint Range of Motion Analysis</h3>
          <div className="joints-grid">
            {Object.entries(sessionResults.jointMetrics).map(
              ([joint, metrics]) => {
                const jointInfo = getJointInfo(joint);
                const improvementColor =
                  metrics.improvement > 0
                    ? "#27ae60"
                    : metrics.improvement < -5
                    ? "#e74c3c"
                    : "#95a5a6";

                return (
                  <div key={joint} className="joint-card">
                    <div className="joint-header">
                      <div
                        className="joint-icon"
                        style={{ backgroundColor: jointInfo.color }}
                      >
                        {jointInfo.icon}
                      </div>
                      <div className="joint-info">
                        <h4>{jointInfo.name}</h4>
                        <div className="joint-stats">
                          <span>Range: {Math.round(metrics.range)}°</span>
                          <span
                            className="improvement"
                            style={{ color: improvementColor }}
                          >
                            {metrics.improvement > 0 ? "+" : ""}
                            {Math.round(metrics.improvement)}°
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="range-visualization">
                      <div className="range-bar">
                        <div
                          className="range-fill"
                          style={{
                            width: `${Math.min(
                              (metrics.range / 150) * 100,
                              100
                            )}%`,
                            backgroundColor: jointInfo.color,
                          }}
                        ></div>
                      </div>
                      <div className="range-details">
                        <span>Min: {Math.round(metrics.min)}°</span>
                        <span>Avg: {Math.round(metrics.average)}°</span>
                        <span>Max: {Math.round(metrics.max)}°</span>
                      </div>
                    </div>

                    <div className="measurements-count">
                      {metrics.measurements} measurements recorded
                    </div>
                  </div>
                );
              }
            )}
          </div>
        </div>
      )}

      {/* Improvements */}
      {sessionResults.improvements.length > 0 && (
        <div className="improvements">
          <h3>🎉 Session Highlights</h3>
          <ul>
            {sessionResults.improvements.map((improvement, index) => (
              <li key={index}>{improvement}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommendations */}
      {sessionResults.recommendations.length > 0 && (
        <div className="recommendations">
          <h3>💡 Recommendations for Next Session</h3>
          <ul>
            {sessionResults.recommendations.map((recommendation, index) => (
              <li key={index}>{recommendation}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Actions */}
      <div className="session-actions">
        <Button
          variant="primary"
          onClick={onNewSession}
          ariaLabel="Start a new therapy session"
          className="new-session-button"
        >
          🎯 Start New Session
        </Button>

        <Button
          variant="secondary"
          onClick={() => window.print()}
          ariaLabel="Print therapy results"
        >
          📄 Save Progress Report
        </Button>
      </div>

      {/* Motivational Message */}
      <div className="motivational-message">
        <p>
          {sessionResults.performance === "Excellent" &&
            "Outstanding therapeutic session! Your movement quality and range of motion are excellent. Keep up the great work!"}
          {sessionResults.performance === "Good" &&
            "Great progress in your therapy session! You're showing good improvement in movement quality and joint mobility."}
          {sessionResults.performance === "Fair" &&
            "Good effort in your therapy session! Consistent practice will help improve your movement quality and range of motion."}
          {sessionResults.performance === "Needs Improvement" &&
            "Every step forward counts in your recovery journey. Keep practicing and you'll see improvement in your movement quality!"}
        </p>
      </div>
    </div>
  );
};

export default TherapyDashboard;
