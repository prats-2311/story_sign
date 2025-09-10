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
  connectionStatus = "disconnected",
  generationError = "",
  onDismissError,
}) => {
  const [generationMode, setGenerationMode] = useState("scan");
  const [customPrompt, setCustomPrompt] = useState("");
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

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

  // Initialize webcam for object scanning
  React.useEffect(() => {
    const initializeWebcam = async () => {
      if (generationMode !== "scan") return;

      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480 },
        });

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (error) {
        console.error("Error accessing webcam:", error);
      }
    };

    const cleanupWebcam = () => {
      if (videoRef.current?.srcObject) {
        const tracks = videoRef.current.srcObject.getTracks();
        tracks.forEach((track) => track.stop());
        videoRef.current.srcObject = null;
      }
    };

    if (generationMode === "scan") {
      initializeWebcam();
    } else {
      cleanupWebcam();
    }

    return cleanupWebcam;
  }, [generationMode]);

  // Handle object scanning
  const handleScanObject = useCallback(async () => {
    try {
      const canvas = canvasRef.current;
      const video = videoRef.current;

      if (!video || !canvas) {
        console.error("Video or canvas element not available");
        return;
      }

      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;

      const ctx = canvas.getContext("2d");
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      const frameData = canvas.toDataURL("image/jpeg", 0.9);

      if (onStoryGenerate) {
        await onStoryGenerate({ frame_data: frameData });
      }
    } catch (error) {
      console.error("Error capturing frame for story generation:", error);
    }
  }, [onStoryGenerate]);

  // Handle simple word generation
  const handleSimpleWordGenerate = (word) => {
    if (onStoryGenerate) {
      onStoryGenerate({ simple_word: word });
    }
  };

  // Handle custom prompt generation
  const handleCustomPromptGenerate = (e) => {
    e.preventDefault();
    if (customPrompt.trim() && onStoryGenerate) {
      onStoryGenerate({ custom_prompt: customPrompt });
    }
  };

  const isConnected = connectionStatus === "connected";
  const canGenerate = isConnected && !isGeneratingStory;

  return (
    <div className="story-setup">
      <header className="story-setup-header">
        <h2>Create Your ASL Story</h2>
        <p>
          Choose how you'd like to generate your personalized ASL practice
          story.
        </p>

        {!isConnected && (
          <div className="connection-warning" role="alert">
            <span aria-hidden="true">⚠️</span>
            <span>Backend connection required for story generation</span>
          </div>
        )}
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
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="preview-video"
                aria-label="Camera preview for object scanning"
              />
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
              {simpleWords.map((word) => (
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
                  onChange={(e) => setCustomPrompt(e.target.value)}
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
