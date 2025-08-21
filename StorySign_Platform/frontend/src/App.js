import React, { useState, useRef } from "react";
import "./App.css";
import "./PerformanceMonitor.css";
import WebcamCapture from "./WebcamCapture";
import VideoStreamingClient from "./VideoStreamingClient";
import ProcessedVideoDisplay from "./ProcessedVideoDisplay";
import PerformanceMonitorSimple from "./PerformanceMonitorSimple";
import ASLWorldModule from "./ASLWorldModule";

function App() {
  const [backendMessage, setBackendMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState("not_tested");
  const [webcamActive, setWebcamActive] = useState(false);
  const [webcamError, setWebcamError] = useState("");
  const [streamingActive, setStreamingActive] = useState(false);
  const [processedFrameData, setProcessedFrameData] = useState(null);
  const [streamingError, setStreamingError] = useState("");
  const [streamingConnectionStatus, setStreamingConnectionStatus] =
    useState("disconnected");
  const [showTroubleshooting, setShowTroubleshooting] = useState(false);
  const [showPerformanceMonitor, setShowPerformanceMonitor] = useState(true);
  const [optimizationSettings, setOptimizationSettings] = useState({
    adaptiveQuality: true,
    targetFPS: 30,
    maxLatency: 100,
    qualityProfile: "balanced",
  });

  // ASL World Module state management
  const [showASLWorld, setShowASLWorld] = useState(false);
  const [storyData, setStoryData] = useState(null);
  const [currentSentenceIndex, setCurrentSentenceIndex] = useState(0);
  const [latestFeedback, setLatestFeedback] = useState(null);
  const [isGeneratingStory, setIsGeneratingStory] = useState(false);
  const [isProcessingFeedback, setIsProcessingFeedback] = useState(false);
  const [storyGenerationError, setStoryGenerationError] = useState("");

  const videoStreamingRef = useRef(null);

  const testBackendConnection = async () => {
    setIsLoading(true);
    setConnectionStatus("testing");
    setShowTroubleshooting(false);

    try {
      const response = await fetch("http://localhost:8000/", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        timeout: 10000, // 10 second timeout
      });

      if (response.ok) {
        const data = await response.json();
        setBackendMessage(data.message || "Backend connected successfully!");
        setConnectionStatus("connected");
        setShowTroubleshooting(false);
      } else {
        let errorMessage = `Backend error: ${response.status} ${response.statusText}`;
        if (response.status === 404) {
          errorMessage =
            "Backend API endpoint not found. Please ensure the backend server is running correctly.";
        } else if (response.status >= 500) {
          errorMessage =
            "Backend server error. Please check the backend logs for more information.";
        }
        setBackendMessage(errorMessage);
        setConnectionStatus("error");
        setShowTroubleshooting(true);
      }
    } catch (error) {
      let errorMessage = "Connection failed: ";
      if (error.name === "TypeError" && error.message.includes("fetch")) {
        errorMessage +=
          "Cannot reach backend server. Please ensure the backend is running on http://localhost:8000";
      } else if (error.name === "AbortError") {
        errorMessage +=
          "Connection timeout. The backend server may be overloaded or not responding.";
      } else {
        errorMessage += error.message;
      }
      setBackendMessage(errorMessage);
      setConnectionStatus("error");
      setShowTroubleshooting(true);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = () => {
    switch (connectionStatus) {
      case "connected":
        return "#4CAF50";
      case "error":
        return "#f44336";
      case "testing":
        return "#ff9800";
      default:
        return "#9e9e9e";
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case "connected":
        return "Connected";
      case "error":
        return "Connection Failed";
      case "testing":
        return "Testing...";
      default:
        return "Not Tested";
    }
  };

  const handleFrameCapture = (message) => {
    // Send frame to WebSocket if streaming is active
    if (streamingActive && videoStreamingRef.current) {
      videoStreamingRef.current.sendFrame(message);
    }

    console.log("Frame captured:", {
      timestamp: message.timestamp,
      frameNumber: message.metadata?.frame_number,
      size: `${message.metadata?.width}x${message.metadata?.height}`,
      adaptiveFPS: message.metadata?.adaptive_fps,
      processingCapability: message.metadata?.processing_capability,
    });
  };

  const handleStreamingConnectionChange = (status) => {
    console.log("Streaming connection status:", status);
    setStreamingConnectionStatus(status);

    // Clear streaming error when connection is restored
    if (status === "connected") {
      setStreamingError("");
    }
  };

  const handleProcessedFrame = (message) => {
    // Handle different message types
    if (message.type === "processed_frame") {
      setProcessedFrameData(message);
      // Clear any previous streaming errors on successful frame processing
      setStreamingError("");
      console.log("Processed frame received:", {
        frameNumber: message.metadata?.frame_number,
        processingTime: message.metadata?.processing_time_ms,
        landmarks: message.metadata?.landmarks_detected,
      });
    } else if (message.type === "asl_feedback") {
      // Handle ASL feedback messages for practice sessions
      handleASLFeedback(message.data);
    } else {
      // Handle other message types as processed frames for backward compatibility
      setProcessedFrameData(message);
      setStreamingError("");
    }
  };

  const handleStreamingError = (error) => {
    console.error("Streaming error:", error);
    setStreamingError(error);

    // Don't override backend connection status if it's already connected
    if (connectionStatus !== "connected") {
      setBackendMessage(`Streaming error: ${error}`);
      setConnectionStatus("error");
    }
  };

  const handleOptimizationChange = (newSettings) => {
    setOptimizationSettings(newSettings);
    console.log("Optimization settings updated:", newSettings);

    // Send optimization settings to backend if needed
    // This could be implemented as a WebSocket message or REST API call
  };

  // Story generation workflow functions
  const handleStoryGenerate = async (frameData) => {
    setIsGeneratingStory(true);
    setStoryGenerationError("");

    try {
      console.log("Starting story generation with frame data");

      // Prepare request payload
      const requestPayload = {
        frame_data: frameData,
        custom_prompt: null, // Could be extended to allow custom prompts
      };

      // Call story generation API
      const response = await fetch(
        "http://localhost:8000/api/story/recognize_and_generate",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(requestPayload),
          timeout: 60000, // 60 second timeout for story generation
        }
      );

      if (response.ok) {
        const data = await response.json();

        if (data.success && data.story) {
          console.log("Story generated successfully:", data.story);
          setStoryData(data.story);
          setCurrentSentenceIndex(0);
          setLatestFeedback(null);
          setStoryGenerationError("");
        } else {
          const errorMessage =
            data.user_message || data.message || "Story generation failed";
          console.error("Story generation failed:", errorMessage);
          setStoryGenerationError(errorMessage);
        }
      } else {
        let errorMessage = `Story generation failed: ${response.status} ${response.statusText}`;

        try {
          const errorData = await response.json();
          errorMessage =
            errorData.user_message || errorData.message || errorMessage;
        } catch (parseError) {
          console.error("Failed to parse error response:", parseError);
        }

        console.error("Story generation API error:", errorMessage);
        setStoryGenerationError(errorMessage);
      }
    } catch (error) {
      let errorMessage = "Story generation failed: ";

      if (error.name === "TypeError" && error.message.includes("fetch")) {
        errorMessage +=
          "Cannot reach backend server. Please ensure the backend is running.";
      } else if (error.name === "AbortError") {
        errorMessage += "Request timeout. The AI services may be overloaded.";
      } else {
        errorMessage += error.message;
      }

      console.error("Story generation error:", error);
      setStoryGenerationError(errorMessage);
    } finally {
      setIsGeneratingStory(false);
    }
  };

  const handlePracticeControl = async (action, sentenceIndex) => {
    console.log(
      `Practice control action: ${action} at sentence ${sentenceIndex}`
    );

    try {
      switch (action) {
        case "next_sentence":
          if (sentenceIndex < (storyData?.sentences?.length || 0) - 1) {
            setCurrentSentenceIndex(sentenceIndex + 1);
            setLatestFeedback(null);
          }
          break;

        case "try_again":
          setLatestFeedback(null);
          break;

        case "complete_story":
          // Story completed - could show completion message or reset
          console.log("Story practice completed!");
          setLatestFeedback(null);
          break;

        default:
          console.warn(`Unknown practice control action: ${action}`);
      }
    } catch (error) {
      console.error("Error handling practice control:", error);
    }
  };

  const handleASLFeedback = (feedbackData) => {
    console.log("Received ASL feedback:", feedbackData);
    setLatestFeedback(feedbackData);
    setIsProcessingFeedback(false);
  };

  const handleWebcamError = (error) => {
    setWebcamError(error);
    // Auto-stop streaming if webcam fails
    if (streamingActive) {
      setStreamingActive(false);
    }
  };

  const toggleWebcam = () => {
    setWebcamActive(!webcamActive);
    if (webcamActive) {
      setWebcamError("");
      // Also stop streaming when stopping webcam
      setStreamingActive(false);
    }
  };

  const toggleStreaming = () => {
    if (!webcamActive) {
      setBackendMessage("Please start webcam first before enabling streaming");
      return;
    }

    if (connectionStatus !== "connected") {
      setBackendMessage(
        "Please test backend connection first before enabling streaming"
      );
      return;
    }

    // Clear previous streaming errors when starting
    if (!streamingActive) {
      setStreamingError("");
    }

    setStreamingActive(!streamingActive);
  };

  const retryWebcam = () => {
    setWebcamError("");
    setWebcamActive(false);
    // Small delay to ensure cleanup, then restart
    setTimeout(() => {
      setWebcamActive(true);
    }, 500);
  };

  const retryStreaming = () => {
    setStreamingError("");
    setStreamingActive(false);
    // Small delay to ensure cleanup, then restart
    setTimeout(() => {
      setStreamingActive(true);
    }, 500);
  };

  const toggleASLWorld = () => {
    setShowASLWorld(!showASLWorld);

    // Reset ASL World state when closing
    if (showASLWorld) {
      setStoryData(null);
      setCurrentSentenceIndex(0);
      setLatestFeedback(null);
      setIsGeneratingStory(false);
      setIsProcessingFeedback(false);
      setStoryGenerationError("");
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>StorySign</h1>
        <p>Real-time American Sign Language Recognition System</p>
      </header>
      <main className="App-main">
        {showASLWorld ? (
          <div className="asl-world-container">
            <div className="asl-world-header">
              <button className="back-to-main-btn" onClick={toggleASLWorld}>
                ← Back to Main
              </button>
            </div>
            <ASLWorldModule
              storyData={storyData}
              currentSentenceIndex={currentSentenceIndex}
              latestFeedback={latestFeedback}
              onStoryGenerate={handleStoryGenerate}
              onPracticeControl={handlePracticeControl}
              isGeneratingStory={isGeneratingStory}
              isProcessingFeedback={isProcessingFeedback}
              connectionStatus={connectionStatus}
              onFrameCapture={handleFrameCapture}
            />
            {storyGenerationError && (
              <div className="story-generation-error">
                <p className="error-text">
                  Story Generation Error: {storyGenerationError}
                </p>
                <button
                  className="retry-btn"
                  onClick={() => setStoryGenerationError("")}
                >
                  Dismiss
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="control-panel">
            <div className="connection-section">
              <h2>Backend Connectivity</h2>
              <div className="status-indicator">
                <span
                  className="status-dot"
                  style={{ backgroundColor: getStatusColor() }}
                ></span>
                <span className="status-text">{getStatusText()}</span>
              </div>
              <button
                className="test-backend-btn"
                onClick={testBackendConnection}
                disabled={isLoading}
              >
                {isLoading ? "Testing..." : "Test Backend"}
              </button>
            </div>

            <div className="message-area">
              <h3>System Messages</h3>
              <div className="message-display">
                {backendMessage ? (
                  <p className={`message ${connectionStatus}`}>
                    {backendMessage}
                  </p>
                ) : (
                  <p className="message placeholder">
                    Click "Test Backend" to verify connectivity
                  </p>
                )}
              </div>

              {showTroubleshooting && connectionStatus === "error" && (
                <div className="troubleshooting-panel">
                  <h4>Troubleshooting Steps:</h4>
                  <ul>
                    <li>
                      Ensure the backend server is running:{" "}
                      <code>python main.py</code>
                    </li>
                    <li>
                      Check that the backend is accessible at{" "}
                      <code>http://localhost:8000</code>
                    </li>
                    <li>Verify no firewall is blocking the connection</li>
                    <li>Check the backend console for error messages</li>
                    <li>Try restarting the backend server</li>
                  </ul>
                  <button
                    className="retry-btn"
                    onClick={testBackendConnection}
                    disabled={isLoading}
                  >
                    Retry Connection
                  </button>
                </div>
              )}
            </div>

            <div className="video-area">
              <h3>Video Feed</h3>
              <div className="video-controls">
                <button className="webcam-toggle-btn" onClick={toggleWebcam}>
                  {webcamActive ? "Stop Webcam" : "Start Webcam"}
                </button>
                <button
                  className="streaming-toggle-btn"
                  onClick={toggleStreaming}
                  disabled={!webcamActive}
                >
                  {streamingActive ? "Stop Streaming" : "Start Streaming"}
                </button>
              </div>
              {webcamError && (
                <div className="webcam-error">
                  <p className="error-text">{webcamError}</p>
                  <div className="error-actions">
                    <button className="retry-btn" onClick={retryWebcam}>
                      Retry Webcam
                    </button>
                    <div className="error-help">
                      <p>Common solutions:</p>
                      <ul>
                        <li>Check camera permissions in browser settings</li>
                        <li>Close other applications using the camera</li>
                        <li>Try refreshing the page</li>
                        <li>Ensure camera is properly connected</li>
                      </ul>
                    </div>
                  </div>
                </div>
              )}
              <WebcamCapture
                isActive={webcamActive}
                onFrameCapture={handleFrameCapture}
                onError={handleWebcamError}
              />
            </div>

            <div className="streaming-area">
              <h3>Processed Video Stream</h3>

              {streamingError && (
                <div className="streaming-error">
                  <p className="error-text">
                    Streaming Error: {streamingError}
                  </p>
                  <div className="error-actions">
                    <button className="retry-btn" onClick={retryStreaming}>
                      Retry Streaming
                    </button>
                    <div className="error-help">
                      <p>Troubleshooting steps:</p>
                      <ul>
                        <li>
                          Check that the backend server is running and
                          responsive
                        </li>
                        <li>
                          Verify WebSocket connection at
                          ws://localhost:8000/ws/video
                        </li>
                        <li>Ensure webcam is active and working properly</li>
                        <li>
                          Check browser console for additional error details
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              <VideoStreamingClient
                ref={videoStreamingRef}
                isActive={streamingActive}
                onConnectionChange={handleStreamingConnectionChange}
                onProcessedFrame={handleProcessedFrame}
                onError={handleStreamingError}
              />

              <ProcessedVideoDisplay
                processedFrameData={processedFrameData}
                connectionStatus={streamingConnectionStatus}
                streamingStats={{
                  framesSent: videoStreamingRef.current?.framesSent || 0,
                  framesReceived:
                    videoStreamingRef.current?.framesReceived || 0,
                  droppedFrames: 0, // This would come from WebcamCapture performance stats
                }}
                onRetryConnection={retryStreaming}
                isActive={streamingActive}
              />
            </div>

            {/* Performance Monitor */}
            {showPerformanceMonitor && (
              <div className="performance-section">
                <div className="section-header">
                  <h3>Performance Monitor</h3>
                  <button
                    className="toggle-monitor-btn"
                    onClick={() =>
                      setShowPerformanceMonitor(!showPerformanceMonitor)
                    }
                  >
                    {showPerformanceMonitor ? "Hide Monitor" : "Show Monitor"}
                  </button>
                </div>
                <PerformanceMonitorSimple
                  streamingStats={{
                    framesSent: videoStreamingRef.current?.framesSent || 0,
                    framesReceived:
                      videoStreamingRef.current?.framesReceived || 0,
                  }}
                  processedFrameData={processedFrameData}
                  connectionStatus={streamingConnectionStatus}
                  optimizationSettings={optimizationSettings}
                  onOptimizationChange={handleOptimizationChange}
                />
              </div>
            )}
          </div>
        )}

        {/* ASL World Toggle Button - Always visible */}
        <div className="asl-world-toggle">
          <button
            className="asl-world-toggle-btn"
            onClick={toggleASLWorld}
            disabled={connectionStatus !== "connected"}
          >
            {showASLWorld ? "Exit ASL World" : "Enter ASL World"}
          </button>
          {connectionStatus !== "connected" && (
            <p className="toggle-help">
              Connect to backend first to use ASL World
            </p>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
