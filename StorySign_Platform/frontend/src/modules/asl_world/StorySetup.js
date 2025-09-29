import React, { useState, useRef, useCallback } from "react";
import { Button, LoadingSpinner } from "../../components/common";
import "./StorySetup.css";

/**
 * StorySetup component for topic selection interface
 * Handles story generation through object scanning, word selection, or custom prompts
 */
const StorySetup = ({
  onStoryGenerate,
  isGeneratingStory = false,
  generationError = "",
  onDismissError,
  // New props from parent for webcam management
  webcamRef = null,
  webcamStream = null,
  isWebcamActive = false,
  captureFrame = null,
  webcamError = null,
  // Connection status for display
  connectionStatus = "disconnected",
}) => {
  const [generationMode, setGenerationMode] = useState("scan");
  const [customPrompt, setCustomPrompt] = useState("");
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  // Effect to attach webcam stream to video element
  React.useEffect(() => {
    const videoElement = webcamRef?.current || videoRef.current;
    if (webcamStream && videoElement && isWebcamActive) {
      videoElement.srcObject = webcamStream;
      const playPromise = videoElement.play();
      if (playPromise && typeof playPromise.catch === "function") {
        playPromise.catch(error => {
          console.warn("Video autoplay failed:", error);
        });
      }
    }
  }, [webcamStream, isWebcamActive, webcamRef]);

  const simpleWords = [
    "Cat",
    "Dog",
    "House",
    "Ball",
    "Book",
    "Tree",
    "Car",
    "Sun",
  ];

  // Webcam is now managed by parent - no local initialization needed

  // Handle object scanning using parent's captureFrame function
  const handleScanObject = useCallback(async () => {
    try {
      const videoElement = webcamRef?.current || videoRef.current;
      if (captureFrame && videoElement) {
        // Use parent's captureFrame function with video element
        const frameData = await captureFrame(videoElement);
        if (frameData && onStoryGenerate) {
          await onStoryGenerate({ frame_data: frameData.frameData });
        }
      } else {
        console.error("captureFrame function or video element not available");
      }
    } catch (error) {
      console.error("Error capturing frame for story generation:", error);
    }
  }, [captureFrame, onStoryGenerate, webcamRef]);

  // Handle simple word generation
  const handleSimpleWordGenerate = word => {
    if (onStoryGenerate) {
      onStoryGenerate({ simple_word: word });
    }
  };

  // Handle custom prompt generation
  const handleCustomPromptGenerate = e => {
    e.preventDefault();
    if (customPrompt.trim() && onStoryGenerate) {
      onStoryGenerate({ custom_prompt: customPrompt });
    }
  };

  const canGenerate = !isGeneratingStory; // Backend connects automatically

  return (
    <div className="story-setup">
      <header className="story-setup-header">
        <h2>Create Your ASL Story</h2>
        <p>
          Choose how you'd like to generate your personalized ASL practice
          story.
        </p>

        <div className="connection-info" role="status">
          <span aria-hidden="true">🟢</span>
          <span>Backend ready - Stories will generate automatically</span>
        </div>
      </header>

      {generationError && (
        <div className="generation-error" role="alert">
          <div className="error-content">
            <span className="error-icon" aria-hidden="true">
              ❌
            </span>
            <div className="error-text">
              <strong>Story Generation Error:</strong>
              <p>{generationError}</p>
            </div>
            <Button
              variant="secondary"
              size="small"
              onClick={onDismissError}
              ariaLabel="Dismiss error message"
            >
              ×
            </Button>
          </div>
        </div>
      )}

      <nav
        className="generation-tabs"
        role="tablist"
        aria-label="Story generation methods"
      >
        <Button
          variant={generationMode === "scan" ? "primary" : "secondary"}
          onClick={() => setGenerationMode("scan")}
          role="tab"
          aria-selected={generationMode === "scan"}
          aria-controls="scan-panel"
        >
          Scan Object
        </Button>
        <Button
          variant={generationMode === "word" ? "primary" : "secondary"}
          onClick={() => setGenerationMode("word")}
          role="tab"
          aria-selected={generationMode === "word"}
          aria-controls="word-panel"
        >
          Choose a Word
        </Button>
        <Button
          variant={generationMode === "custom" ? "primary" : "secondary"}
          onClick={() => setGenerationMode("custom")}
          role="tab"
          aria-selected={generationMode === "custom"}
          aria-controls="custom-panel"
        >
          Custom Topic
        </Button>
      </nav>

      <div className="generation-content">
        {generationMode === "scan" && (
          <section
            id="scan-panel"
            role="tabpanel"
            aria-labelledby="scan-tab"
            className="generation-panel"
          >
            <h3>Scan an Object</h3>
            <p>
              Show an object to the camera to create a personalized story for
              ASL practice.
            </p>

            <div className="video-preview">
              {isWebcamActive ? (
                <video
                  ref={webcamRef || videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="preview-video"
                  aria-label="Camera preview for object scanning"
                />
              ) : (
                <div className="webcam-inactive" role="status">
                  <div className="inactive-message">
                    <span className="camera-icon">📷</span>
                    <p>Camera is inactive</p>
                    {webcamError && (
                      <p className="error-message">{webcamError}</p>
                    )}
                    <small>Camera access is required for object scanning</small>
                  </div>
                </div>
              )}
              <canvas
                ref={canvasRef}
                style={{ display: "none" }}
                aria-hidden="true"
              />
            </div>

            <div className="scan-controls">
              <Button
                size="large"
                onClick={handleScanObject}
                disabled={!canGenerate}
                loading={isGeneratingStory}
                ariaLabel={
                  isGeneratingStory
                    ? "Generating stories from scanned object"
                    : "Scan object to generate stories"
                }
              >
                {isGeneratingStory
                  ? "Generating Stories..."
                  : "Scan Object to Start"}
              </Button>
            </div>
          </section>
        )}

        {generationMode === "word" && (
          <section
            id="word-panel"
            role="tabpanel"
            aria-labelledby="word-tab"
            className="generation-panel"
          >
            <h3>Choose a Word to Start Your Story</h3>
            <p>
              Select a simple word to generate stories at different difficulty
              levels.
            </p>

            <div
              className="word-grid"
              role="group"
              aria-label="Simple words for story generation"
            >
              {simpleWords.map(word => (
                <Button
                  key={word}
                  variant="secondary"
                  className="word-chip"
                  onClick={() => handleSimpleWordGenerate(word)}
                  disabled={!canGenerate}
                  ariaLabel={`Generate stories about ${word}`}
                >
                  {word}
                </Button>
              ))}
            </div>

            {isGeneratingStory && (
              <div className="generation-status">
                <LoadingSpinner message="Generating stories..." />
              </div>
            )}
          </section>
        )}

        {generationMode === "custom" && (
          <section
            id="custom-panel"
            role="tabpanel"
            aria-labelledby="custom-tab"
            className="generation-panel"
          >
            <h3>Enter a Topic for Your Story</h3>
            <p>Describe what you'd like your story to be about.</p>

            <form
              onSubmit={handleCustomPromptGenerate}
              className="custom-prompt-form"
            >
              <div className="input-group">
                <label htmlFor="custom-prompt-input" className="input-label">
                  Story Topic
                </label>
                <input
                  id="custom-prompt-input"
                  type="text"
                  className="prompt-input"
                  value={customPrompt}
                  onChange={e => setCustomPrompt(e.target.value)}
                  placeholder="e.g., 'A friendly robot' or 'A magical key'"
                  disabled={!canGenerate}
                  aria-describedby="prompt-help"
                />
                <div id="prompt-help" className="input-help">
                  Enter any topic or theme for your ASL practice story
                </div>
              </div>

              <Button
                type="submit"
                size="large"
                disabled={!canGenerate || !customPrompt.trim()}
                loading={isGeneratingStory}
                ariaLabel={
                  isGeneratingStory
                    ? "Generating stories from custom topic"
                    : "Generate stories from custom topic"
                }
              >
                {isGeneratingStory
                  ? "Generating Stories..."
                  : "Generate Stories"}
              </Button>
            </form>
          </section>
        )}
      </div>
    </div>
  );
};

export default StorySetup;
