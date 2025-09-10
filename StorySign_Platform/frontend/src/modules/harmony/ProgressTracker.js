import React, { useMemo } from "react";
import Button from "../../components/common/Button";
import "./ProgressTracker.css";

/**
 * ProgressTracker component for session progress visualization
 * Shows session results, statistics, and progress over time
 */
const ProgressTracker = ({ sessionData, sessionDuration, onNewSession }) => {
  // Calculate comprehensive session results
  const sessionResults = useMemo(() => {
    if (!sessionData || !sessionData.detectedEmotions.length) {
      return {
        totalDetections: 0,
        targetMatches: 0,
        accuracy: 0,
        averageConfidence: 0,
        sessionScore: 0,
        emotionBreakdown: [],
        confidenceDistribution: [],
        timeSpent: sessionDuration || 0,
        performance: "No Data",
        recommendations: [],
      };
    }

    const detections = sessionData.detectedEmotions;
    const confidences = sessionData.confidenceScores;
    const targetEmotion = sessionData.targetEmotion;

    // Basic statistics
    const totalDetections = detections.length;
    const targetMatches = detections.filter(
      (emotion) => emotion === targetEmotion
    ).length;
    const accuracy =
      totalDetections > 0 ? (targetMatches / totalDetections) * 100 : 0;
    const averageConfidence =
      confidences.length > 0
        ? confidences.reduce((sum, conf) => sum + conf, 0) / confidences.length
        : 0;

    // Calculate session score (weighted combination of accuracy and confidence)
    const sessionScore = Math.round(
      accuracy * 0.7 + averageConfidence * 100 * 0.3
    );

    // Emotion breakdown
    const emotionCounts = {};
    detections.forEach((emotion) => {
      emotionCounts[emotion] = (emotionCounts[emotion] || 0) + 1;
    });

    const emotionBreakdown = Object.entries(emotionCounts)
      .map(([emotion, count]) => ({
        emotion,
        count,
        percentage: (count / totalDetections) * 100,
      }))
      .sort((a, b) => b.count - a.count);

    // Confidence distribution
    const confidenceRanges = {
      high: confidences.filter((c) => c >= 0.8).length,
      good: confidences.filter((c) => c >= 0.6 && c < 0.8).length,
      fair: confidences.filter((c) => c >= 0.4 && c < 0.6).length,
      low: confidences.filter((c) => c < 0.4).length,
    };

    const confidenceDistribution = Object.entries(confidenceRanges).map(
      ([level, count]) => ({
        level,
        count,
        percentage: totalDetections > 0 ? (count / totalDetections) * 100 : 0,
      })
    );

    // Performance assessment
    let performance = "Needs Improvement";
    if (sessionScore >= 85) performance = "Excellent";
    else if (sessionScore >= 70) performance = "Good";
    else if (sessionScore >= 55) performance = "Fair";

    // Generate recommendations
    const recommendations = [];
    if (accuracy < 60) {
      recommendations.push(
        "Focus on practicing the target emotion more consistently"
      );
    }
    if (averageConfidence < 0.6) {
      recommendations.push(
        "Work on making your expressions more distinct and clear"
      );
    }
    if (sessionDuration < 30000) {
      // Less than 30 seconds
      recommendations.push("Try longer practice sessions for better results");
    }
    if (accuracy >= 80 && averageConfidence >= 0.7) {
      recommendations.push(
        "Great job! Try practicing a different emotion to expand your skills"
      );
    }

    return {
      totalDetections,
      targetMatches,
      accuracy: Math.round(accuracy * 10) / 10,
      averageConfidence: Math.round(averageConfidence * 100) / 100,
      sessionScore,
      emotionBreakdown,
      confidenceDistribution,
      timeSpent: sessionDuration || 0,
      performance,
      recommendations,
    };
  }, [sessionData, sessionDuration]);

  // Get emotion display info
  const getEmotionInfo = (emotionId) => {
    const emotionMap = {
      happy: { name: "Happy", icon: "😊", color: "#ffd93d" },
      sad: { name: "Sad", icon: "😢", color: "#74b9ff" },
      surprised: { name: "Surprised", icon: "😮", color: "#fd79a8" },
      angry: { name: "Angry", icon: "😠", color: "#e17055" },
      fearful: { name: "Fearful", icon: "😨", color: "#a29bfe" },
      disgusted: { name: "Disgusted", icon: "🤢", color: "#00b894" },
      neutral: { name: "Neutral", icon: "😐", color: "#636e72" },
    };
    return (
      emotionMap[emotionId] || { name: emotionId, icon: "❓", color: "#ddd" }
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
        return "#00b894";
      case "Good":
        return "#fdcb6e";
      case "Fair":
        return "#fd79a8";
      default:
        return "#e17055";
    }
  };

  const targetEmotionInfo = getEmotionInfo(sessionData?.targetEmotion);

  return (
    <div className="progress-tracker">
      <div className="results-header">
        <h2>Session Complete! 🎉</h2>
        <p>Here's how you did in your facial expression practice session</p>
      </div>

      {/* Overall Score */}
      <div className="overall-score">
        <div className="score-circle">
          <div className="score-value">{sessionResults.sessionScore}</div>
          <div className="score-label">Score</div>
        </div>
        <div className="score-details">
          <h3
            style={{ color: getPerformanceColor(sessionResults.performance) }}
          >
            {sessionResults.performance}
          </h3>
          <p>
            Target Emotion: {targetEmotionInfo.name} {targetEmotionInfo.icon}
          </p>
          <p>Session Duration: {formatDuration(sessionResults.timeSpent)}</p>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="key-metrics">
        <h3>Session Statistics</h3>
        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-value">{sessionResults.totalDetections}</div>
            <div className="metric-label">Total Detections</div>
          </div>

          <div className="metric-card">
            <div className="metric-value">{sessionResults.targetMatches}</div>
            <div className="metric-label">Target Matches</div>
          </div>

          <div className="metric-card">
            <div className="metric-value">{sessionResults.accuracy}%</div>
            <div className="metric-label">Accuracy</div>
          </div>

          <div className="metric-card">
            <div className="metric-value">
              {sessionResults.averageConfidence}
            </div>
            <div className="metric-label">Avg Confidence</div>
          </div>
        </div>
      </div>

      {/* Emotion Breakdown */}
      {sessionResults.emotionBreakdown.length > 0 && (
        <div className="emotion-breakdown">
          <h3>Emotion Breakdown</h3>
          <div className="breakdown-chart">
            {sessionResults.emotionBreakdown.map((item) => {
              const emotionInfo = getEmotionInfo(item.emotion);
              const isTarget = item.emotion === sessionData?.targetEmotion;

              return (
                <div
                  key={item.emotion}
                  className={`breakdown-item ${isTarget ? "target" : ""}`}
                >
                  <div className="emotion-header">
                    <div
                      className="emotion-icon"
                      style={{ backgroundColor: emotionInfo.color }}
                    >
                      {emotionInfo.icon}
                    </div>
                    <span className="emotion-name">{emotionInfo.name}</span>
                    {isTarget && <span className="target-badge">Target</span>}
                  </div>

                  <div className="breakdown-bar">
                    <div
                      className="breakdown-fill"
                      style={{
                        width: `${item.percentage}%`,
                        backgroundColor: emotionInfo.color,
                      }}
                    ></div>
                  </div>

                  <div className="breakdown-stats">
                    <span>{item.count} detections</span>
                    <span>{Math.round(item.percentage)}%</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Confidence Distribution */}
      {sessionResults.confidenceDistribution.length > 0 && (
        <div className="confidence-distribution">
          <h3>Confidence Distribution</h3>
          <div className="distribution-chart">
            {sessionResults.confidenceDistribution.map((item) => {
              const colors = {
                high: "#00b894",
                good: "#fdcb6e",
                fair: "#fd79a8",
                low: "#e17055",
              };

              const labels = {
                high: "High (80%+)",
                good: "Good (60-79%)",
                fair: "Fair (40-59%)",
                low: "Low (<40%)",
              };

              return (
                <div key={item.level} className="distribution-item">
                  <div className="distribution-header">
                    <span className="confidence-level">
                      {labels[item.level]}
                    </span>
                    <span className="confidence-count">{item.count}</span>
                  </div>
                  <div className="distribution-bar">
                    <div
                      className="distribution-fill"
                      style={{
                        width: `${item.percentage}%`,
                        backgroundColor: colors[item.level],
                      }}
                    ></div>
                  </div>
                  <span className="distribution-percentage">
                    {Math.round(item.percentage)}%
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {sessionResults.recommendations.length > 0 && (
        <div className="recommendations">
          <h3>💡 Recommendations</h3>
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
          ariaLabel="Start a new practice session"
          className="new-session-button"
        >
          🎯 Practice Another Emotion
        </Button>

        <Button
          variant="secondary"
          onClick={() => window.print()}
          ariaLabel="Print session results"
        >
          📄 Save Results
        </Button>
      </div>

      {/* Motivational Message */}
      <div className="motivational-message">
        <p>
          {sessionResults.performance === "Excellent" &&
            "Outstanding work! Your emotional expression skills are excellent. Keep practicing to maintain this level!"}
          {sessionResults.performance === "Good" &&
            "Great job! You're showing good progress in emotional expression. Keep practicing to reach excellence!"}
          {sessionResults.performance === "Fair" &&
            "Nice effort! You're making progress. Regular practice will help improve your emotional expression skills."}
          {sessionResults.performance === "Needs Improvement" &&
            "Every expert was once a beginner. Keep practicing and you'll see improvement in your emotional expression skills!"}
        </p>
      </div>
    </div>
  );
};

export default ProgressTracker;
