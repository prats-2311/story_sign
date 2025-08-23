import React, { useState, useRef } from "react";
import "./App.css";
import "./PerformanceMonitor.css";
import VideoStream from "./VideoStream";
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
  const [gestureState, setGestureState] = useState("listening");

  const videoStreamingRef = useRef(null);
  const hasStartedPracticeRef = useRef(false);

  // Effect 1: When a story is generated, ensure webcam/streaming are active
  React.useEffect(() => {
    if (storyData) {
      // Reset practice session start flag for new story
      hasStartedPracticeRef.current = false;

      if (!webcamActive) {
        setWebcamActive(true);
      }
      if (!streamingActive) {
        setStreamingActive(true);
      }
      // Reset sentence index for the new story
      setCurrentSentenceIndex(0);
    }
  }, [storyData]); // Runs when a new story is loaded

  // Effect 2: When the streaming connection is established, start the session
  React.useEffect(() => {
    if (
      storyData &&
      streamingConnectionStatus === "connected" &&
      videoStreamingRef.current &&
      !hasStartedPracticeRef.current
    ) {
      hasStartedPracticeRef.current = true;
      // Start practice session safely after WS is connected
      startPracticeSession(storyData);
    }
  }, [storyData, streamingConnectionStatus]);

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

      // Check for practice session data in processed frames
      if (message.practice_session) {
        handlePracticeSessionUpdate(message.practice_session);
      }

      console.log("Processed frame received:", {
        frameNumber: message.metadata?.frame_number,
        processingTime: message.metadata?.processing_time_ms,
        landmarks: message.metadata?.landmarks_detected,
        gestureState: message.practice_session?.gesture_state,
      });
    } else if (message.type === "asl_feedback") {
      // Handle ASL feedback messages for practice sessions
      handleASLFeedback(message.data, message.enhanced);
    } else if (message.type === "control_response") {
      // Handle practice control responses
      handlePracticeControlResponse(message);
    } else if (message.type === "practice_session_response") {
      // Handle practice session responses
      handlePracticeSessionResponse(message);
    } else if (message.type === "session_complete") {
      // Handle story completion notifications
      handleSessionComplete(message);
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

  // Practice session management functions
  const startPracticeSession = async (story) => {
    console.log("Starting practice session with story:", story.title);

    try {
      // Send practice session start message to backend via WebSocket
      if (videoStreamingRef.current && streamingActive) {
        const sessionData = {
          story_sentences: story.sentences,
          session_id: `session_${Date.now()}`,
          story_title: story.title,
        };

        const success = videoStreamingRef.current.sendPracticeControl(
          "start_session",
          sessionData
        );

        if (success) {
          console.log("Practice session started successfully");
        } else {
          console.error("Failed to start practice session");
        }
      } else {
        console.warn("WebSocket not available for practice session start");
      }
    } catch (error) {
      console.error("Error starting practice session:", error);
    }
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

          // Start practice session with the generated story
          await startPracticeSession(data.story);
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
      // Prepare control data with enhanced information
      const controlData = {
        sentence_index: sentenceIndex,
        target_sentence: storyData?.sentences?.[sentenceIndex] || "",
        story_sentences: storyData?.sentences || [],
        story_title: storyData?.title || "Unknown Story",
        session_timestamp: new Date().toISOString(),
        previous_feedback: latestFeedback
          ? {
              confidence: latestFeedback.confidence_score,
              had_suggestions: latestFeedback.suggestions?.length > 0,
            }
          : null,
      };

      // Send control message to backend via WebSocket
      if (videoStreamingRef.current && streamingActive) {
        const success = videoStreamingRef.current.sendPracticeControl(
          action,
          controlData
        );

        if (!success) {
          console.error("Failed to send practice control to backend");
          return;
        }
      }

      // Update local state based on action with enhanced handling
      switch (action) {
        case "next_sentence":
          if (sentenceIndex < (storyData?.sentences?.length || 0) - 1) {
            const nextIndex = sentenceIndex + 1;
            setCurrentSentenceIndex(nextIndex);
            setLatestFeedback(null);
            setIsProcessingFeedback(false);
            setGestureState("listening");

            console.log(
              `Advanced to sentence ${nextIndex + 1}/${
                storyData?.sentences?.length
              }`
            );
          } else {
            // This is the last sentence, trigger completion
            console.log("Attempting to complete story from last sentence");
            handlePracticeControl("complete_story", sentenceIndex);
          }
          break;

        case "try_again":
          setLatestFeedback(null);
          setIsProcessingFeedback(false);
          setGestureState("listening");
          console.log(
            `Retrying sentence ${sentenceIndex + 1}: "${
              storyData?.sentences?.[sentenceIndex]
            }"`
          );
          break;

        case "complete_story":
          // Story completed - show completion state
          console.log("Story practice completed!");
          setGestureState("completed");
          // Keep current feedback to show completion message
          // The backend should send a session_complete message with final feedback
          break;

        case "restart_story":
          // Restart the current story from the beginning
          setCurrentSentenceIndex(0);
          setLatestFeedback(null);
          setIsProcessingFeedback(false);
          setGestureState("listening");
          console.log("Restarting story from beginning");
          break;

        case "new_story":
          // Reset all story-related state for new story generation
          setStoryData(null);
          setCurrentSentenceIndex(0);
          setLatestFeedback(null);
          setIsProcessingFeedback(false);
          setGestureState("listening");
          console.log("Preparing for new story generation");
          break;

        default:
          console.warn(`Unknown practice control action: ${action}`);
      }
    } catch (error) {
      console.error("Error handling practice control:", error);
      // Reset to safe state on error
      setIsProcessingFeedback(false);
      setGestureState("listening");
    }
  };

  const handleASLFeedback = (feedbackData, isEnhanced = false) => {
    console.log(
      "Received ASL feedback:",
      feedbackData,
      "Enhanced:",
      isEnhanced
    );

    // Validate and enhance feedback data
    if (feedbackData && typeof feedbackData === "object") {
      const enhancedFeedback = {
        ...feedbackData,
        // Ensure required fields exist
        feedback: feedbackData.feedback || "No feedback available",
        confidence_score: feedbackData.confidence_score || 0,
        suggestions: feedbackData.suggestions || [],
        target_sentence:
          feedbackData.target_sentence ||
          storyData?.sentences?.[currentSentenceIndex] ||
          "",
        // Add metadata
        received_at: new Date().toISOString(),
        sentence_index: currentSentenceIndex,
        story_title: storyData?.title || "Unknown Story",
        // Processing information
        processing_time: feedbackData.processing_time || 0,
        session_id: feedbackData.session_id || "unknown",
      };

      setLatestFeedback(enhancedFeedback);
      setIsProcessingFeedback(false);
      setGestureState("listening"); // Reset gesture state after feedback

      // Log feedback for debugging
      console.log("Enhanced feedback set:", {
        sentence: enhancedFeedback.target_sentence,
        confidence: enhancedFeedback.confidence_score,
        suggestionsCount: enhancedFeedback.suggestions.length,
        processingTime: enhancedFeedback.processing_time,
      });
    } else {
      console.error("Invalid feedback data received:", feedbackData);
      setLatestFeedback({
        feedback: "Error: Invalid feedback received from server",
        confidence_score: 0,
        suggestions: ["Please try signing again"],
        target_sentence: storyData?.sentences?.[currentSentenceIndex] || "",
        error: true,
        received_at: new Date().toISOString(),
      });
      setIsProcessingFeedback(false);
      setGestureState("listening");
    }
  };

  const handlePracticeSessionUpdate = (practiceData) => {
    console.log("Practice session update:", practiceData);

    // Update processing feedback state based on gesture state
    if (practiceData.gesture_state) {
      const currentGestureState = practiceData.gesture_state;
      setGestureState(currentGestureState);

      if (currentGestureState === "analyzing") {
        setIsProcessingFeedback(true);
      } else if (currentGestureState === "listening") {
        setIsProcessingFeedback(false);
      }
    }
  };

  const handlePracticeControlResponse = (message) => {
    console.log("Practice control response:", message);

    if (message.result && message.result.success) {
      const action = message.action;
      const result = message.result;

      // Update local state based on successful backend response
      if (
        action === "next_sentence" &&
        result.current_sentence_index !== undefined
      ) {
        setCurrentSentenceIndex(result.current_sentence_index);
        setLatestFeedback(null);
        setIsProcessingFeedback(false);
      } else if (action === "try_again") {
        setLatestFeedback(null);
        setIsProcessingFeedback(false);
      } else if (action === "complete_story") {
        setLatestFeedback(null);
        setIsProcessingFeedback(false);
      }
    } else {
      console.error("Practice control failed:", message.result?.error);
    }
  };

  const handlePracticeSessionResponse = (message) => {
    console.log("Practice session response:", message);

    if (message.result && message.result.success) {
      const action = message.action;

      if (action === "session_started") {
        console.log("Practice session started successfully on backend");
        // Reset practice state for new session
        setCurrentSentenceIndex(0);
        setLatestFeedback(null);
        setIsProcessingFeedback(false);
        setGestureState("listening");
      }
    } else {
      console.error(
        "Practice session operation failed:",
        message.result?.error
      );
    }
  };

  const handleSessionComplete = (message) => {
    console.log("Session complete:", message);

    // Handle story completion
    if (message.data) {
      const completionData = message.data;

      // Create completion feedback
      const completionFeedback = {
        feedback:
          completionData.completion_message ||
          "Congratulations! You've completed the story!",
        confidence_score: completionData.overall_score || 1.0,
        suggestions: completionData.final_suggestions || [
          "Great job completing the story!",
          "Try generating a new story to continue practicing",
        ],
        target_sentence: "Story Complete",
        completed: true,
        story_stats: {
          total_sentences: storyData?.sentences?.length || 0,
          completion_time: completionData.completion_time || 0,
          average_confidence: completionData.average_confidence || 0,
        },
        received_at: new Date().toISOString(),
      };

      setLatestFeedback(completionFeedback);
      setIsProcessingFeedback(false);
      setGestureState("completed");

      console.log("Story completion feedback set:", completionFeedback);
    }
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
      setGestureState("listening");
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
              gestureState={gestureState}
            >
              <VideoStream
                webcamActive={webcamActive}
                streamingActive={streamingActive}
                onFrameCapture={handleFrameCapture}
                videoStreamingRef={videoStreamingRef}
                onConnectionChange={handleStreamingConnectionChange}
                onProcessedFrame={handleProcessedFrame}
                onError={handleStreamingError}
                processedFrameData={processedFrameData}
                streamingConnectionStatus={streamingConnectionStatus}
                streamingStats={{
                  framesSent: videoStreamingRef.current?.framesSent || 0,
                  framesReceived: videoStreamingRef.current?.framesReceived || 0,
                }}
                onRetryConnection={retryStreaming}
              />
            </ASLWorldModule>
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
              {/* Video components moved into ASLWorldModule via <VideoStream /> */}
            </div>

            {/* Streaming area moved into ASLWorldModule via <VideoStream /> */}

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
