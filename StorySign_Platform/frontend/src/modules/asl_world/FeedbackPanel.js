import React from "react";
import { Button } from "../../components/common";
import "./FeedbackPanel.css";

/**
 * FeedbackPanel component for AI feedback display
 * Shows feedback, suggestions, and practice controls with full accessibility
 */
const FeedbackPanel = ({
  feedback,
  currentSentenceIndex = 0,
  totalSentences = 0,
  onPracticeControl,
  isProcessingFeedback = false,
}) => {
  if (!feedback) {
    return null;
  }

  const isStoryComplete = feedback.completed;
  const isLastSentence = currentSentenceIndex >= totalSentences - 1;
  const confidenceScore = Math.round((feedback.confidence_score || 0) * 100);

  const getConfidenceLevel = (score) => {
    if (score >= 80) return { level: "excellent", color: "#16a34a" };
    if (score >= 60) return { level: "good", color: "#2563eb" };
    if (score >= 40) return { level: "fair", color: "#d97706" };
    return { level: "needs-improvement", color: "#dc2626" };
  };

  const confidenceInfo = getConfidenceLevel(confidenceScore);

  return (
    <div className="feedback-panel" role="region" aria-label="AI Feedback">
      <header className="feedback-header">
        <h3>
          {isStoryComplete ? (
            <>
              <span className="completion-icon" aria-hidden="true">
                🎉
              </span>
              Story Complete!
            </>
          ) : (
            "AI Feedback"
          )}
        </h3>

        {!isStoryComplete && (
          <div className="sentence-context">
            <span className="sr-only">Feedback for sentence</span>
            <span
              aria-label={`Sentence ${
                currentSentenceIndex + 1
              } of ${totalSentences}`}
            >
              {currentSentenceIndex + 1}/{totalSentences}
            </span>
          </div>
        )}
      </header>

      <main className="feedback-content">
        <div className="feedback-message">
          <p className="feedback-text">{feedback.feedback}</p>

          {feedback.error && (
            <div className="feedback-error" role="alert">
              <span className="error-icon" aria-hidden="true">
                ⚠️
              </span>
              <span>
                There was an issue processing your signing. Please try again.
              </span>
            </div>
          )}
        </div>

        {/* Confidence Score */}
        {feedback.confidence_score !== undefined && (
          <div className="confidence-section">
            <div className="confidence-header">
              <span className="confidence-label">
                {isStoryComplete ? "Overall Score" : "Confidence"}:
              </span>
              <span
                className="confidence-score"
                style={{ color: confidenceInfo.color }}
                aria-label={`${confidenceScore} percent confidence, ${confidenceInfo.level}`}
              >
                {confidenceScore}%
              </span>
            </div>

            <div
              className="confidence-bar"
              role="progressbar"
              aria-valuenow={confidenceScore}
              aria-valuemin={0}
              aria-valuemax={100}
            >
              <div
                className="confidence-fill"
                style={{
                  width: `${confidenceScore}%`,
                  backgroundColor: confidenceInfo.color,
                }}
                aria-hidden="true"
              />
            </div>

            <div className="confidence-description">
              <span className={`confidence-level ${confidenceInfo.level}`}>
                {confidenceInfo.level.replace("-", " ")}
              </span>
            </div>
          </div>
        )}

        {/* Story Statistics for Completion */}
        {isStoryComplete && feedback.story_stats && (
          <div className="story-stats">
            <h4>Practice Summary</h4>
            <div className="stats-grid">
              <div className="stat-item">
                <span className="stat-label">Sentences Completed:</span>
                <span className="stat-value">
                  {feedback.story_stats.total_sentences}
                </span>
              </div>

              {feedback.story_stats.completion_time > 0 && (
                <div className="stat-item">
                  <span className="stat-label">Total Time:</span>
                  <span className="stat-value">
                    {Math.round(feedback.story_stats.completion_time / 1000)}s
                  </span>
                </div>
              )}

              {feedback.story_stats.average_confidence > 0 && (
                <div className="stat-item">
                  <span className="stat-label">Average Score:</span>
                  <span className="stat-value">
                    {Math.round(feedback.story_stats.average_confidence * 100)}%
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Processing Information */}
        {feedback.processing_time > 0 && !isStoryComplete && (
          <div className="processing-info">
            <small>Analysis completed in {feedback.processing_time}ms</small>
          </div>
        )}

        {/* Suggestions */}
        {feedback.suggestions && feedback.suggestions.length > 0 && (
          <div className="suggestions-section">
            <h4>{isStoryComplete ? "Next Steps:" : "Suggestions:"}</h4>
            <ul className="suggestions-list">
              {feedback.suggestions.map((suggestion, index) => (
                <li key={index} className="suggestion-item">
                  {suggestion}
                </li>
              ))}
            </ul>
          </div>
        )}
      </main>

      <footer className="feedback-actions">
        {!isStoryComplete ? (
          <div className="practice-controls">
            <Button
              variant="secondary"
              onClick={() => onPracticeControl("try_again")}
              disabled={isProcessingFeedback}
              ariaLabel="Try signing this sentence again"
            >
              Try Again
            </Button>

            {!isLastSentence ? (
              <Button
                variant="primary"
                onClick={() => onPracticeControl("next_sentence")}
                disabled={isProcessingFeedback}
                ariaLabel={`Move to next sentence (${
                  currentSentenceIndex + 2
                } of ${totalSentences})`}
              >
                Next Sentence ({currentSentenceIndex + 2}/{totalSentences})
              </Button>
            ) : (
              <Button
                variant="success"
                onClick={() => onPracticeControl("complete_story")}
                disabled={isProcessingFeedback}
                ariaLabel="Complete the story"
              >
                Complete Story
              </Button>
            )}
          </div>
        ) : (
          <div className="completion-controls">
            <Button
              variant="secondary"
              onClick={() => onPracticeControl("restart_story")}
              disabled={isProcessingFeedback}
              ariaLabel="Practice this story again from the beginning"
            >
              Practice Again
            </Button>

            <Button
              variant="primary"
              onClick={() => onPracticeControl("new_story")}
              disabled={isProcessingFeedback}
              ariaLabel="Generate a new story to practice"
            >
              New Story
            </Button>
          </div>
        )}
      </footer>
    </div>
  );
};

export default FeedbackPanel;
