import React, { useState, useRef, useCallback } from "react";
import PerformanceMonitorSimple from "./PerformanceMonitorSimple"; // NEW: import performance monitor
import "./ASLWorldModule.css";

const ASLWorldModule = ({
  storyData = null,
  currentSentenceIndex = 0,
  latestFeedback = null,
  onStoryGenerate,
  onPracticeControl,
  isGeneratingStory = false,
  isProcessingFeedback = false,
  connectionStatus = "disconnected",
  onFrameCapture,
  gestureState = "listening", // New prop for gesture state
  practiceStarted = false,
  onStartPractice,
  streamingStats,
  processedFrameData,
  streamingConnectionStatus,
  optimizationSettings,
  onOptimizationChange,
  children,
}) => {
  const [mode, setMode] = useState("story_generation"); // 'story_generation' or 'practice'
  const [showFeedback, setShowFeedback] = useState(false);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  // Handle object scanning and story generation
  const handleScanObject = useCallback(async () => {
    try {
      // Capture high-quality frame from webcam
      const canvas = canvasRef.current;
      const video = videoRef.current;

      if (!video || !canvas) {
        console.error("Video or canvas element not available");
        return;
      }

      // Set canvas dimensions to match video
      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;

      const ctx = canvas.getContext("2d");
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Convert to base64 JPEG with high quality for object recognition
      const frameData = canvas.toDataURL("image/jpeg", 0.9);

      // Call the story generation handler
      if (onStoryGenerate) {
        await onStoryGenerate(frameData);
      }
    } catch (error) {
      console.error("Error capturing frame for story generation:", error);
    }
  }, [onStoryGenerate]);

  // Handle practice control actions
  const handlePracticeControl = useCallback(
    (action) => {
      if (onPracticeControl) {
        onPracticeControl(action, currentSentenceIndex);
      }

      // Hide feedback when moving to next sentence or trying again
      if (action === "next_sentence" || action === "try_again") {
        setShowFeedback(false);
      }
    },
    [onPracticeControl, currentSentenceIndex]
  );

  // Switch to practice mode when story is available
  React.useEffect(() => {
    if (storyData && storyData.sentences && storyData.sentences.length > 0) {
      setMode("practice");
    }
  }, [storyData]);

  // Show feedback when it becomes available
  React.useEffect(() => {
    if (latestFeedback) {
      setShowFeedback(true);
    }
  }, [latestFeedback]);

  // Initialize webcam access for frame capture
  React.useEffect(() => {
    const initializeWebcam = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480 },
        });

        if (videoRef?.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (error) {
        console.error("Error accessing webcam:", error);
      }
    };

    const cleanupWebcam = () => {
      if (videoRef?.current && videoRef.current.srcObject) {
        const tracks = videoRef.current.srcObject.getTracks();
        tracks.forEach((track) => track.stop());
        videoRef.current.srcObject = null;
      }
    };

    // Only initialize when in story generation mode
    if (mode === "story_generation") {
      initializeWebcam();
    } else {
      // Explicitly cleanup when switching to practice mode
      cleanupWebcam();
    }

    // Cleanup function
    return () => {
      cleanupWebcam();
    };
  }, [mode]);

  const renderStoryGenerationMode = () => (
    <div className="story-generation-mode">
      <div className="scan-section">
        <h2>Generate Your Story</h2>
        <p>
          Show an object to the camera to create a personalized story for ASL
          practice.
        </p>

        <div className="video-preview">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="preview-video"
          />
          <canvas ref={canvasRef} style={{ display: "none" }} />
        </div>

        <div className="scan-controls">
          <button
            className="scan-object-btn"
            onClick={handleScanObject}
            disabled={isGeneratingStory || connectionStatus !== "connected"}
          >
            {isGeneratingStory ? (
              <>
                <div className="loading-spinner"></div>
                Generating Story...
              </>
            ) : (
              "Scan Object to Start"
            )}
          </button>
        </div>

        {connectionStatus !== "connected" && (
          <div className="connection-warning">
            <p>⚠️ Backend connection required for story generation</p>
          </div>
        )}
      </div>
    </div>
  );

  const renderPracticeMode = () => (
    <div className="practice-mode">
      {/* Hide the simple preview video when in practice mode */}
      <div className="video-preview" style={{ display: "none" }}>
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="preview-video"
          style={{ display: "none" }}
        />
        <canvas ref={canvasRef} style={{ display: "none" }} />
      </div>

      <div className="story-display">
        <h2>Practice Story: {storyData?.title || "Generated Story"}</h2>
        <div className="story-content">
          {storyData?.sentences?.map((sentence, index) => (
            <div
              key={index}
              className={`story-sentence ${
                index === currentSentenceIndex ? "current" : ""
              } ${index < currentSentenceIndex ? "completed" : ""}`}
            >
              <span className="sentence-number">{index + 1}.</span>
              <span className="sentence-text">{sentence}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="practice-controls">
        <div className="current-sentence">
          <div className="sentence-progress">
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{
                  width: `${
                    ((currentSentenceIndex + 1) /
                      (storyData?.sentences?.length || 1)) *
                    100
                  }%`,
                }}
              ></div>
            </div>
            <span className="progress-text">
              {currentSentenceIndex + 1} of {storyData?.sentences?.length || 0}
            </span>
          </div>
          <h3>Practice This Sentence:</h3>
          <div className="highlighted-sentence">
            {storyData?.sentences?.[currentSentenceIndex] ||
              "No sentence available"}
          </div>
        </div>

        {/* Video + Feedback area */}
        {!practiceStarted ? (
          <div className="start-practice-container">
            <h3>Ready to Practice?</h3>
            <p>
              Your story is generated. Click the button below to start your
              webcam and begin signing.
            </p>
            <button
              className="start-practice-btn"
              onClick={onStartPractice}
              disabled={isGeneratingStory || connectionStatus !== "connected"}
            >
              Start Practice Session
            </button>
          </div>
        ) : (
          <div className="video-and-feedback">
            <details className="video-stream-details" open>
              <summary>Show/Hide Live Video Feed</summary>
              <div className="video-container-asl">{children}</div>
            </details>

            <div className="practice-actions">
              {showFeedback && latestFeedback ? (
                <div className="feedback-section">
                  <div className="feedback-display">
                    <h4>
                      {latestFeedback?.completed
                        ? "🎉 Story Complete!"
                        : "AI Feedback"}
                    </h4>
                    <div className="feedback-content">
                      <p className="feedback-text">{latestFeedback.feedback}</p>

                      {/* Confidence Score Display */}
                      {latestFeedback.confidence_score !== undefined && (
                        <div className="confidence-score">
                          <span>
                            {latestFeedback?.completed
                              ? "Overall Score"
                              : "Confidence"}
                            :{" "}
                            {Math.round(latestFeedback.confidence_score * 100)}%
                          </span>
                        </div>
                      )}

                      {/* Story Statistics for Completion */}
                      {latestFeedback?.completed &&
                        latestFeedback?.story_stats && (
                          <div className="story-stats">
                            <h5>Practice Summary:</h5>
                            <div className="stats-grid">
                              <div className="stat-item">
                                <span className="stat-label">Sentences:</span>
                                <span className="stat-value">
                                  {latestFeedback.story_stats.total_sentences}
                                </span>
                              </div>
                              {latestFeedback.story_stats.completion_time >
                                0 && (
                                <div className="stat-item">
                                  <span className="stat-label">Time:</span>
                                  <span className="stat-value">
                                    {Math.round(
                                      latestFeedback.story_stats
                                        .completion_time / 1000
                                    )}
                                    s
                                  </span>
                                </div>
                              )}
                              {latestFeedback.story_stats.average_confidence >
                                0 && (
                                <div className="stat-item">
                                  <span className="stat-label">
                                    Avg. Score:
                                  </span>
                                  <span className="stat-value">
                                    {Math.round(
                                      latestFeedback.story_stats
                                        .average_confidence * 100
                                    )}
                                    %
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                      {/* Processing Information */}
                      {latestFeedback.processing_time > 0 &&
                        !latestFeedback?.completed && (
                          <div className="processing-info">
                            <small>
                              Analysis completed in{" "}
                              {latestFeedback.processing_time}
                              ms
                            </small>
                          </div>
                        )}

                      {/* Error Handling */}
                      {latestFeedback?.error && (
                        <div className="feedback-error">
                          <p>
                            ⚠️ There was an issue processing your signing.
                            Please try again.
                          </p>
                        </div>
                      )}

                      {/* Suggestions */}
                      {latestFeedback.suggestions &&
                        latestFeedback.suggestions.length > 0 && (
                          <div className="suggestions">
                            <h5>
                              {latestFeedback?.completed
                                ? "Next Steps:"
                                : "Suggestions:"}
                            </h5>
                            <ul>
                              {latestFeedback.suggestions.map(
                                (suggestion, index) => (
                                  <li key={index}>{suggestion}</li>
                                )
                              )}
                            </ul>
                          </div>
                        )}
                    </div>
                  </div>

                  <div className="control-buttons">
                    {!latestFeedback?.completed ? (
                      <>
                        <button
                          className="try-again-btn"
                          onClick={() => handlePracticeControl("try_again")}
                          disabled={isProcessingFeedback}
                        >
                          Try Again
                        </button>
                        {currentSentenceIndex <
                          (storyData?.sentences?.length || 0) - 1 && (
                          <button
                            className="next-sentence-btn"
                            onClick={() =>
                              handlePracticeControl("next_sentence")
                            }
                            disabled={isProcessingFeedback}
                          >
                            Next Sentence ({currentSentenceIndex + 2}/
                            {storyData?.sentences?.length})
                          </button>
                        )}
                        {currentSentenceIndex ===
                          (storyData?.sentences?.length || 0) - 1 && (
                          <button
                            className="complete-story-btn"
                            onClick={() =>
                              handlePracticeControl("complete_story")
                            }
                            disabled={isProcessingFeedback}
                          >
                            Complete Story
                          </button>
                        )}
                      </>
                    ) : (
                      // Story completion controls
                      <div className="completion-controls">
                        <button
                          className="restart-story-btn"
                          onClick={() => handlePracticeControl("restart_story")}
                          disabled={isProcessingFeedback}
                        >
                          Practice Again
                        </button>
                        <button
                          className="new-story-btn"
                          onClick={() => handlePracticeControl("new_story")}
                          disabled={isProcessingFeedback}
                        >
                          New Story
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="waiting-for-signing">
                  <div className="signing-indicator">
                    {isProcessingFeedback ? (
                      <>
                        <div className="loading-spinner"></div>
                        <p>Analyzing your signing...</p>
                        <small>
                          Please wait while AI analyzes your gesture
                        </small>
                      </>
                    ) : (
                      <>
                        <div className="gesture-icon">👋</div>
                        <p>Start signing the sentence above</p>
                        <small>
                          The system will automatically detect when you begin
                          and end your gesture
                        </small>
                        <div className="gesture-status">
                          <div className={`status-indicator ${gestureState}`}>
                            <span className="status-dot"></span>
                            <span>
                              {gestureState === "listening" &&
                                "Listening for gestures"}
                              {gestureState === "detecting" &&
                                "Gesture detected - keep signing"}
                              {gestureState === "analyzing" &&
                                "Analyzing your gesture"}
                              {gestureState === "completed" &&
                                "Story completed!"}
                            </span>
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="practice-footer">
        {/* Collapsible performance monitor */}
        <details className="performance-monitor-details">
          <summary>Show/Hide Performance Metrics</summary>
          <PerformanceMonitorSimple
            streamingStats={streamingStats}
            processedFrameData={processedFrameData}
            connectionStatus={streamingConnectionStatus}
            optimizationSettings={optimizationSettings}
            onOptimizationChange={onOptimizationChange}
          />
        </details>
        <button
          className="new-story-btn"
          onClick={() => {
            setMode("story_generation");
            setShowFeedback(false);
          }}
        >
          Generate New Story
        </button>
      </div>
    </div>
  );

  return (
    <div className="asl-world-module">
      <div className="module-header">
        <h1>ASL World</h1>
        <p>Interactive American Sign Language Learning</p>
        <div className="connection-status">
          <span className={`status-indicator ${connectionStatus}`}>
            {connectionStatus === "connected" && "🟢"}
            {connectionStatus === "connecting" && "🟡"}
            {connectionStatus === "disconnected" && "🔴"}
          </span>
          <span className="status-text">
            {connectionStatus === "connected" && "Connected"}
            {connectionStatus === "connecting" && "Connecting..."}
            {connectionStatus === "disconnected" && "Disconnected"}
          </span>
        </div>
      </div>

      <div className="module-content">
        {mode === "story_generation"
          ? renderStoryGenerationMode()
          : renderPracticeMode()}
      </div>
    </div>
  );
};
export default ASLWorldModule;
