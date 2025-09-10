import React, { useMemo } from "react";
import "./MovementAnalysis.css";

/**
 * MovementAnalysis component for real-time movement tracking and feedback
 * Shows current movement analysis results and joint angle measurements
 */
const MovementAnalysis = ({
  currentExercise,
  currentAnalysis,
  sessionData,
  isSessionActive,
}) => {
  // Calculate movement statistics
  const movementStats = useMemo(() => {
    if (!sessionData || !sessionData.movementData.length) {
      return {
        totalMovements: 0,
        averageRange: 0,
        jointMetrics: {},
        qualityScore: 0,
        recommendations: [],
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

        jointMetrics[joint] = {
          range: max - min,
          average: avg,
          min,
          max,
          measurements: angles.length,
        };
      }
    });

    // Calculate overall quality score
    const qualityScore =
      metrics.length > 0
        ? metrics.reduce((sum, metric) => sum + (metric.quality || 0), 0) /
          metrics.length
        : 0;

    // Calculate average range of motion
    const ranges = Object.values(jointMetrics).map((joint) => joint.range);
    const averageRange =
      ranges.length > 0
        ? ranges.reduce((sum, range) => sum + range, 0) / ranges.length
        : 0;

    return {
      totalMovements: movements.length,
      averageRange: Math.round(averageRange * 10) / 10,
      jointMetrics,
      qualityScore: Math.round(qualityScore * 100) / 100,
      recommendations: generateRecommendations(jointMetrics, qualityScore),
    };
  }, [sessionData]);

  // Generate movement recommendations
  const generateRecommendations = (jointMetrics, qualityScore) => {
    const recommendations = [];

    if (qualityScore < 0.6) {
      recommendations.push("Focus on slower, more controlled movements");
    }

    Object.entries(jointMetrics).forEach(([joint, metrics]) => {
      if (metrics.range < 30) {
        recommendations.push(`Try to increase range of motion for ${joint}`);
      }
    });

    if (Object.keys(jointMetrics).length < 3) {
      recommendations.push("Ensure your full body is visible to the camera");
    }

    return recommendations;
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

  // Get range of motion assessment
  const getRangeAssessment = (range, jointType) => {
    // Different joints have different normal ranges
    const normalRanges = {
      shoulder: { excellent: 150, good: 120, fair: 90 },
      elbow: { excellent: 140, good: 120, fair: 90 },
      hip: { excellent: 120, good: 90, fair: 60 },
      knee: { excellent: 130, good: 110, fair: 90 },
      spine: { excellent: 60, good: 45, fair: 30 },
      neck: { excellent: 80, good: 60, fair: 40 },
    };

    const jointCategory = jointType.includes("shoulder")
      ? "shoulder"
      : jointType.includes("elbow")
      ? "elbow"
      : jointType.includes("hip")
      ? "hip"
      : jointType.includes("knee")
      ? "knee"
      : jointType.includes("spine")
      ? "spine"
      : jointType.includes("neck")
      ? "neck"
      : "shoulder";

    const ranges = normalRanges[jointCategory];

    if (range >= ranges.excellent) {
      return {
        level: "Excellent",
        color: "#27ae60",
        description: "Great mobility",
      };
    } else if (range >= ranges.good) {
      return { level: "Good", color: "#f39c12", description: "Good mobility" };
    } else if (range >= ranges.fair) {
      return {
        level: "Fair",
        color: "#e67e22",
        description: "Limited mobility",
      };
    } else {
      return {
        level: "Needs Work",
        color: "#e74c3c",
        description: "Restricted mobility",
      };
    }
  };

  return (
    <div className="movement-analysis">
      <div className="analysis-header">
        <h3>Movement Analysis</h3>
        {isSessionActive && (
          <div className="session-indicator">
            <span className="recording-dot"></span>
            <span>Analyzing Movement</span>
          </div>
        )}
      </div>

      {/* Current Exercise Display */}
      {currentExercise && (
        <div className="current-exercise-section">
          <h4>Current Exercise</h4>
          <div className="exercise-display">
            <div
              className="exercise-icon"
              style={{ backgroundColor: currentExercise.color }}
            >
              {currentExercise.icon}
            </div>
            <div className="exercise-info">
              <span className="exercise-name">{currentExercise.name}</span>
              <span className="exercise-target">
                Target: {currentExercise.targetAreas?.join(", ")}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Current Analysis Display */}
      <div className="current-analysis-section">
        <h4>Real-time Feedback</h4>
        {currentAnalysis ? (
          <div className="analysis-display">
            <div className="quality-meter">
              <div className="meter-label">Movement Quality</div>
              <div className="meter-bar">
                <div
                  className="meter-fill"
                  style={{
                    width: `${(currentAnalysis.metrics?.quality || 0) * 100}%`,
                    backgroundColor:
                      (currentAnalysis.metrics?.quality || 0) >= 0.8
                        ? "#27ae60"
                        : (currentAnalysis.metrics?.quality || 0) >= 0.6
                        ? "#f39c12"
                        : "#e74c3c",
                  }}
                ></div>
              </div>
              <div className="meter-value">
                {Math.round((currentAnalysis.metrics?.quality || 0) * 100)}%
              </div>
            </div>

            {/* Current Joint Angles */}
            {currentAnalysis.jointAngles && (
              <div className="current-joints">
                <h5>Joint Angles</h5>
                <div className="joints-grid">
                  {Object.entries(currentAnalysis.jointAngles).map(
                    ([joint, angle]) => {
                      const jointInfo = getJointInfo(joint);
                      return (
                        <div key={joint} className="joint-item">
                          <div
                            className="joint-icon"
                            style={{ backgroundColor: jointInfo.color }}
                          >
                            {jointInfo.icon}
                          </div>
                          <div className="joint-data">
                            <span className="joint-name">{jointInfo.name}</span>
                            <span className="joint-angle">
                              {Math.round(angle)}°
                            </span>
                          </div>
                        </div>
                      );
                    }
                  )}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="no-analysis">
            <div className="no-analysis-icon">🤖</div>
            <span>No movement detected</span>
            <p>Position yourself in front of the camera and start moving</p>
          </div>
        )}
      </div>

      {/* Session Statistics */}
      {movementStats.totalMovements > 0 && (
        <div className="session-stats">
          <h4>Session Progress</h4>

          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-value">{movementStats.totalMovements}</span>
              <span className="stat-label">Movements</span>
            </div>

            <div className="stat-item">
              <span className="stat-value">{movementStats.averageRange}°</span>
              <span className="stat-label">Avg Range</span>
            </div>

            <div className="stat-item">
              <span className="stat-value">{movementStats.qualityScore}</span>
              <span className="stat-label">Quality Score</span>
            </div>

            <div className="stat-item">
              <span className="stat-value">
                {Object.keys(movementStats.jointMetrics).length}
              </span>
              <span className="stat-label">Joints Tracked</span>
            </div>
          </div>

          {/* Joint Metrics */}
          {Object.keys(movementStats.jointMetrics).length > 0 && (
            <div className="joint-metrics">
              <h5>Joint Range of Motion</h5>
              <div className="metrics-list">
                {Object.entries(movementStats.jointMetrics).map(
                  ([joint, metrics]) => {
                    const jointInfo = getJointInfo(joint);
                    const assessment = getRangeAssessment(metrics.range, joint);

                    return (
                      <div key={joint} className="metric-item">
                        <div className="metric-header">
                          <div
                            className="joint-icon small"
                            style={{ backgroundColor: jointInfo.color }}
                          >
                            {jointInfo.icon}
                          </div>
                          <span className="joint-name">{jointInfo.name}</span>
                          <span
                            className="assessment-badge"
                            style={{ backgroundColor: assessment.color }}
                          >
                            {assessment.level}
                          </span>
                        </div>

                        <div className="metric-details">
                          <div className="range-bar">
                            <div
                              className="range-fill"
                              style={{
                                width: `${Math.min(
                                  (metrics.range / 150) * 100,
                                  100
                                )}%`,
                                backgroundColor: assessment.color,
                              }}
                            ></div>
                          </div>
                          <div className="range-values">
                            <span>Range: {Math.round(metrics.range)}°</span>
                            <span>Avg: {Math.round(metrics.average)}°</span>
                            <span>{metrics.measurements} measurements</span>
                          </div>
                        </div>
                      </div>
                    );
                  }
                )}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {movementStats.recommendations.length > 0 && (
            <div className="recommendations">
              <h5>💡 Real-time Tips</h5>
              <ul>
                {movementStats.recommendations.map((recommendation, index) => (
                  <li key={index}>{recommendation}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Exercise Tips */}
      <div className="exercise-tips">
        <h4>💪 Exercise Tips</h4>
        <ul>
          <li>Keep movements slow and controlled</li>
          <li>Focus on full range of motion</li>
          <li>Maintain good posture throughout</li>
          <li>Stop if you feel any pain</li>
          <li>Use the feedback to improve form</li>
        </ul>
      </div>
    </div>
  );
};

export default MovementAnalysis;
