import React from "react";
import { Button, VideoDisplayPanel } from "../../components/common";
import "./PracticeView.css";

/**
 * PracticeView component for video and sentence practice
 * Handles the main practice interface with video display and sentence progression
 */
const PracticeView = ({
  selectedStory,
  currentSentenceIndex = 0,
  practiceStarted = false,
  gestureState = "listening",
  isProcessingFeedback = false,
  onStartPractice,
  onPracticeControl,
  children, // Video streaming component
}) => {
  if (!selectedStory) {
    return (
      <div className="practice-view-error" role="alert">
        <h3>No Story Selected</h3>
        <p>Please select a story to begin practice.</p>
      </div>
    );
  }

  const currentSentence = selectedStory.sentences?.[currentSentenceIndex];
  const totalSentences = selectedStory.sentences?.length || 0;
  const progressPercentage =
    totalSentences > 0
      ? ((currentSentenceIndex + 1) / totalSentences) * 100
      : 0;

  const getGestureStatusMessage = () => {
    switch (gestureState) {
      case "listening":
        return "Ready to detect your signing";
      case "detecting":
        return "Gesture detected - continue signing";
      case "analyzing":
        return "Analyzing your gesture...";
      case "completed":
        return "Story completed!";
      default:
        return "Waiting for gesture";
    }
  };

  const getGestureStatusIcon = () => {
    switch (gestureState) {
      case "listening":
        return "👋";
      case "detecting":
        return "✋";
      case "analyzing":
        return "🔍";
      case "completed":
        return "🎉";
      default:
        return "👋";
    }
  };

  return (
    <div className="practice-view">
      <header className="practice-header">
        <div className="story-info">
          <h2>Practice Story: {selectedStory.title}</h2>
          <div className="progress-section">
            <div
              className="progress-bar"
              role="progressbar"
              aria-valuenow={currentSentenceIndex + 1}
              aria-valuemin={1}
              aria-valuemax={totalSentences}
            >
              <div
                className="progress-fill"
                style={{ width: `${progressPercentage}%` }}
                aria-hidden="true"
              />
            </div>
            <span className="progress-text" aria-live="polite">
              Sentence {currentSentenceIndex + 1} of {totalSentences}
            </span>
          </div>
        </div>
      </header>

      <main className="practice-content">
        <section className="story-display" aria-label="Story sentences">
          <h3 className="sr-only">Story Sentences</h3>
          <div className="story-sentences">
            {selectedStory.sentences.map((sentence, index) => (
              <div
                key={index}
                className={`story-sentence ${
                  index === currentSentenceIndex ? "current" : ""
                } ${index < currentSentenceIndex ? "completed" : ""}`}
                aria-current={
                  index === currentSentenceIndex ? "step" : undefined
                }
              >
                <span className="sentence-number" aria-hidden="true">
                  {index + 1}.
                </span>
                <span className="sentence-text">{sentence}</span>
                {index < currentSentenceIndex && (
                  <span className="completion-indicator" aria-label="Completed">
                    ✓
                  </span>
                )}
              </div>
            ))}
          </div>
        </section>

        <section
          className="current-practice"
          aria-label="Current practice sentence"
        >
          <div className="current-sentence-card">
            <h3>Practice This Sentence:</h3>
            <div
              className="highlighted-sentence"
              role="text"
              aria-live="polite"
            >
              {currentSentence || "No sentence available"}
            </div>
          </div>

          {!practiceStarted ? (
            <div className="start-practice-section">
              <div className="start-practice-info">
                <h4>Ready to Practice?</h4>
                <p>
                  Your story is ready. Click the button below to start your
                  webcam and begin signing.
                </p>
                <ul className="practice-instructions">
                  <li>Position yourself clearly in front of the camera</li>
                  <li>Sign each sentence clearly and completely</li>
                  <li>
                    Wait for AI feedback before moving to the next sentence
                  </li>
                </ul>
              </div>
              <Button
                size="large"
                onClick={onStartPractice}
                ariaLabel="Start practice session with webcam"
              >
                Start Practice Session
              </Button>
            </div>
          ) : (
            <div className="active-practice-section">
              <div className="video-section">
                <h4 className="sr-only">Video Practice Area</h4>
                <details className="video-controls" open>
                  <summary>Video Feed Controls</summary>
                  <div className="video-container">{children}</div>
                </details>
              </div>

              <div className="practice-status">
                <div
                  className="gesture-status"
                  aria-live="polite"
                  aria-atomic="true"
                >
                  <div className={`status-indicator ${gestureState}`}>
                    <span className="status-icon" aria-hidden="true">
                      {getGestureStatusIcon()}
                    </span>
                    <span className="status-message">
                      {getGestureStatusMessage()}
                    </span>
                  </div>
                </div>

                {isProcessingFeedback && (
                  <div className="processing-indicator" aria-live="polite">
                    <div
                      className="processing-spinner"
                      aria-hidden="true"
                    ></div>
                    <span>Analyzing your signing...</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </section>
      </main>

      <footer className="practice-footer">
        <div className="practice-controls">
          <Button
            variant="secondary"
            onClick={() => onPracticeControl("new_story")}
            ariaLabel="Generate a new story"
          >
            New Story
          </Button>

          {practiceStarted && (
            <Button
              variant="secondary"
              onClick={() => onPracticeControl("restart_story")}
              ariaLabel="Restart current story from beginning"
            >
              Restart Story
            </Button>
          )}
        </div>
      </footer>
    </div>
  );
};

export default PracticeView;
