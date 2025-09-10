import React, { useMemo } from "react";
import "./EmotionMetrics.css";

/**
 * EmotionMetrics component for real-time feedback display
 * Shows current emotion detection results and confidence scores
 */
const EmotionMetrics = ({
  targetEmotion,
  currentDetection,
  sessionData,
  isSessionActive,
}) => {
  // Calculate session statistics
  const sessionStats = useMemo(() => {
    if (!sessionData || !sessionData.detectedEmotions.length) {
      return {
        totalDetections: 0,
        averageConfidence: 0,
        targetMatches: 0,
        matchPercentage: 0,
        topEmotions: [],
      };
    }

    const detections = sessionData.detectedEmotions;
    const confidences = sessionData.confidenceScores;

    // Count emotion occurrences
    const emotionCounts = {};
    detections.forEach((emotion) => {
      emotionCounts[emotion] = (emotionCounts[emotion] || 0) + 1;
    });

    // Calculate target matches
    const targetMatches = detections.filter(
      (emotion) => emotion === targetEmotion
    ).length;
    const matchPercentage =
      detections.length > 0 ? (targetMatches / detections.length) * 100 : 0;

    // Calculate average confidence
    const averageConfidence =
      confidences.length > 0
        ? confidences.reduce((sum, conf) => sum + conf, 0) / confidences.length
        : 0;

    // Get top emotions
    const topEmotions = Object.entries(emotionCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 3)
      .map(([emotion, count]) => ({
        emotion,
        count,
        percentage: (count / detections.length) * 100,
      }));

    return {
      totalDetections: detections.length,
      averageConfidence: Math.round(averageConfidence * 100) / 100,
      targetMatches,
      matchPercentage: Math.round(matchPercentage * 10) / 10,
      topEmotions,
    };
  }, [sessionData, targetEmotion]);

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

  // Get confidence level description
  const getConfidenceLevel = (confidence) => {
    if (confidence >= 0.8)
      return {
        level: "High",
        color: "#00b894",
        description: "Excellent detection",
      };
    if (confidence >= 0.6)
      return { level: "Good", color: "#fdcb6e", description: "Good detection" };
    if (confidence >= 0.4)
      return { level: "Fair", color: "#fd79a8", description: "Fair detection" };
    return { level: "Low", color: "#e17055", description: "Needs improvement" };
  };

  const targetEmotionInfo = getEmotionInfo(targetEmotion);
  const currentEmotionInfo = currentDetection
    ? getEmotionInfo(currentDetection.emotion)
    : null;
  const confidenceInfo = currentDetection
    ? getConfidenceLevel(currentDetection.confidence)
    : null;

  return (
    <div className="emotion-metrics">
      <div className="metrics-header">
        <h3>Real-time Feedback</h3>
        {isSessionActive && (
          <div className="session-indicator">
            <span className="recording-dot"></span>
            <span>Session Active</span>
          </div>
        )}
      </div>

      {/* Target Emotion Display */}
      <div className="target-emotion-section">
        <h4>Target Emotion</h4>
        <div className="emotion-display target">
          <div
            className="emotion-icon large"
            style={{ backgroundColor: targetEmotionInfo.color }}
          >
            {targetEmotionInfo.icon}
          </div>
          <div className="emotion-info">
            <span className="emotion-name">{targetEmotionInfo.name}</span>
            <span className="emotion-label">Practice Goal</span>
          </div>
        </div>
      </div>

      {/* Current Detection Display */}
      <div className="current-detection-section">
        <h4>Current Detection</h4>
        {currentDetection ? (
          <div className="emotion-display current">
            <div
              className="emotion-icon large"
              style={{ backgroundColor: currentEmotionInfo.color }}
            >
              {currentEmotionInfo.icon}
            </div>
            <div className="emotion-info">
              <span className="emotion-name">{currentEmotionInfo.name}</span>
              <div className="confidence-display">
                <div className="confidence-bar">
                  <div
                    className="confidence-fill"
                    style={{
                      width: `${currentDetection.confidence * 100}%`,
                      backgroundColor: confidenceInfo.color,
                    }}
                  ></div>
                </div>
                <span className="confidence-text">
                  {Math.round(currentDetection.confidence * 100)}% -{" "}
                  {confidenceInfo.level}
                </span>
              </div>
            </div>

            {/* Match indicator */}
            <div
              className={`match-indicator ${
                currentDetection.emotion === targetEmotion
                  ? "match"
                  : "no-match"
              }`}
            >
              {currentDetection.emotion === targetEmotion ? "✅" : "❌"}
            </div>
          </div>
        ) : (
          <div className="no-detection">
            <div className="no-detection-icon">👤</div>
            <span>No face detected</span>
            <p>Position yourself in front of the camera</p>
          </div>
        )}
      </div>

      {/* Session Statistics */}
      {sessionStats.totalDetections > 0 && (
        <div className="session-stats">
          <h4>Session Progress</h4>

          <div className="stats-grid">
            <div className="stat-item">
              <span className="stat-value">{sessionStats.totalDetections}</span>
              <span className="stat-label">Total Detections</span>
            </div>

            <div className="stat-item">
              <span className="stat-value">{sessionStats.targetMatches}</span>
              <span className="stat-label">Target Matches</span>
            </div>

            <div className="stat-item">
              <span className="stat-value">
                {sessionStats.matchPercentage}%
              </span>
              <span className="stat-label">Accuracy</span>
            </div>

            <div className="stat-item">
              <span className="stat-value">
                {sessionStats.averageConfidence}
              </span>
              <span className="stat-label">Avg Confidence</span>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="progress-section">
            <div className="progress-label">
              <span>Target Emotion Accuracy</span>
              <span>{sessionStats.matchPercentage}%</span>
            </div>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{
                  width: `${sessionStats.matchPercentage}%`,
                  backgroundColor:
                    sessionStats.matchPercentage >= 70
                      ? "#00b894"
                      : sessionStats.matchPercentage >= 50
                      ? "#fdcb6e"
                      : "#e17055",
                }}
              ></div>
            </div>
          </div>

          {/* Top Emotions */}
          {sessionStats.topEmotions.length > 0 && (
            <div className="top-emotions">
              <h5>Most Detected Emotions</h5>
              <div className="emotions-list">
                {sessionStats.topEmotions.map((item, index) => {
                  const emotionInfo = getEmotionInfo(item.emotion);
                  return (
                    <div key={item.emotion} className="emotion-item">
                      <span className="rank">#{index + 1}</span>
                      <div
                        className="emotion-icon small"
                        style={{ backgroundColor: emotionInfo.color }}
                      >
                        {emotionInfo.icon}
                      </div>
                      <span className="emotion-name">{emotionInfo.name}</span>
                      <span className="emotion-percentage">
                        {Math.round(item.percentage)}%
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Practice Tips */}
      <div className="practice-tips">
        <h4>💡 Tips</h4>
        <ul>
          <li>Keep your face well-lit and centered</li>
          <li>Practice natural, authentic expressions</li>
          <li>Focus on how the emotion feels internally</li>
          <li>Use the confidence meter to gauge accuracy</li>
        </ul>
      </div>
    </div>
  );
};

export default EmotionMetrics;
