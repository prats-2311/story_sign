import React, { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { ASLWorldModule } from "../modules";
import { VideoStream } from "../components";

const ASLWorldPage = ({
  connectionStatus,
  webcamActive,
  streamingActive,
  onFrameCapture,
  videoStreamingRef,
  processedFrameData,
  streamingConnectionStatus,
  optimizationSettings,
  onOptimizationChange,
  onConnectionChange,
  onProcessedFrame,
  onError,
  onRetryConnection,
}) => {
  const navigate = useNavigate();

  // ASL World Module state management (moved from App.js)
  const [storyData, setStoryData] = useState(null); // Now holds StoryLevels
  const [selectedStory, setSelectedStory] = useState(null); // User's chosen story
  const [practiceStarted, setPracticeStarted] = useState(false); // NEW: user-controlled practice start
  const [currentSentenceIndex, setCurrentSentenceIndex] = useState(0);
  const [latestFeedback, setLatestFeedback] = useState(null);
  const [isGeneratingStory, setIsGeneratingStory] = useState(false);
  const [isProcessingFeedback, setIsProcessingFeedback] = useState(false);
  const [storyGenerationError, setStoryGenerationError] = useState("");
  const [gestureState, setGestureState] = useState("listening");

  const hasStartedPracticeRef = useRef(false);

  // Effect 1: When stories are generated, reset state for selection
  React.useEffect(() => {
    if (storyData) {
      // Reset practice session start flag for new stories
      hasStartedPracticeRef.current = false;
      setSelectedStory(null); // Reset selected story for new set
      setCurrentSentenceIndex(0);
      setPracticeStarted(false);
    }
  }, [storyData]); // Runs when new stories are loaded

  // Effect 2: When the streaming connection is established, start the session (only if user started practice)
  React.useEffect(() => {
    if (
      selectedStory &&
      practiceStarted &&
      streamingConnectionStatus === "connected" &&
      videoStreamingRef.current &&
      !hasStartedPracticeRef.current
    ) {
      hasStartedPracticeRef.current = true;
      // Start practice session safely after WS is connected
      startPracticeSession(selectedStory);
    }
  }, [selectedStory, practiceStarted, streamingConnectionStatus]);

  // Named handler for starting practice session
  const handleStartPractice = () => {
    if (!webcamActive) {
      // Note: webcam control is still managed by parent App component
      console.warn("Webcam should be activated by parent component");
    }
    if (!streamingActive) {
      // Note: streaming control is still managed by parent App component
      console.warn("Streaming should be activated by parent component");
    }
    setPracticeStarted(true);
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
  const handleStoryGenerate = async (payload) => {
    setIsGeneratingStory(true);
    setStoryGenerationError("");

    try {
      console.log("Starting story generation with payload:", payload);

      // Call story generation API
      const response = await fetch(
        "http://localhost:8000/api/story/recognize_and_generate",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
          timeout: 60000, // 60 second timeout for story generation
        }
      );

      if (response.ok) {
        const data = await response.json();

        if (data.success && data.stories) {
          console.log("Stories generated successfully:", data.stories);
          setStoryData(data.stories); // Store the collection of stories
          setSelectedStory(null); // Reset selected story for new set
          setCurrentSentenceIndex(0);
          setLatestFeedback(null);
          setStoryGenerationError("");
          // The UI will now show the selection screen
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

  // Story selection handler
  const handleStorySelect = (story) => {
    setSelectedStory(story); // Set the chosen story
    console.log("Story selected:", story.title);
  };

  const handlePracticeControl = async (action, sentenceIndex) => {
    console.log(
      `Practice control action: ${action} at sentence ${sentenceIndex}`
    );

    try {
      // Prepare control data with enhanced information
      const controlData = {
        sentence_index: sentenceIndex,
        target_sentence: selectedStory?.sentences?.[sentenceIndex] || "",
        story_sentences: selectedStory?.sentences || [],
        story_title: selectedStory?.title || "Unknown Story",
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
          if (sentenceIndex < (selectedStory?.sentences?.length || 0) - 1) {
            const nextIndex = sentenceIndex + 1;
            setCurrentSentenceIndex(nextIndex);
            setLatestFeedback(null);
            setIsProcessingFeedback(false);
            setGestureState("listening");

            console.log(
              `Advanced to sentence ${nextIndex + 1}/${
                selectedStory?.sentences?.length
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
              selectedStory?.sentences?.[sentenceIndex]
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
          setSelectedStory(null);
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
          selectedStory?.sentences?.[currentSentenceIndex] ||
          "",
        // Add metadata
        received_at: new Date().toISOString(),
        sentence_index: currentSentenceIndex,
        story_title: selectedStory?.title || "Unknown Story",
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
        target_sentence: selectedStory?.sentences?.[currentSentenceIndex] || "",
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
          total_sentences: selectedStory?.sentences?.length || 0,
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

  // Enhanced processed frame handler that includes ASL World specific logic
  const handleProcessedFrameWithASLLogic = (message) => {
    // Call the parent's processed frame handler first
    if (onProcessedFrame) {
      onProcessedFrame(message);
    }

    // Handle ASL World specific message types
    if (message.type === "asl_feedback") {
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
    } else if (message.type === "processed_frame") {
      // Check for practice session data in processed frames
      if (message.practice_session) {
        handlePracticeSessionUpdate(message.practice_session);
      }
    }
  };

  const handleBackToMain = () => {
    navigate("/");
  };

  return (
    <div className="asl-world-container">
      <div className="asl-world-header">
        <button className="back-to-main-btn" onClick={handleBackToMain}>
          ← Back to Main
        </button>
      </div>
      <ASLWorldModule
        storyData={storyData}
        selectedStory={selectedStory}
        onStorySelect={handleStorySelect}
        currentSentenceIndex={currentSentenceIndex}
        latestFeedback={latestFeedback}
        onStoryGenerate={handleStoryGenerate}
        onPracticeControl={handlePracticeControl}
        isGeneratingStory={isGeneratingStory}
        isProcessingFeedback={isProcessingFeedback}
        connectionStatus={connectionStatus}
        onFrameCapture={onFrameCapture}
        gestureState={gestureState}
        practiceStarted={practiceStarted}
        onStartPractice={handleStartPractice}
        streamingStats={{
          framesSent: videoStreamingRef.current?.framesSent || 0,
          framesReceived: videoStreamingRef.current?.framesReceived || 0,
        }}
        processedFrameData={processedFrameData}
        streamingConnectionStatus={streamingConnectionStatus}
        optimizationSettings={optimizationSettings}
        onOptimizationChange={onOptimizationChange}
      >
        <VideoStream
          webcamActive={webcamActive}
          streamingActive={streamingActive}
          onFrameCapture={onFrameCapture}
          videoStreamingRef={videoStreamingRef}
          onConnectionChange={onConnectionChange}
          onProcessedFrame={handleProcessedFrameWithASLLogic}
          onError={onError}
          processedFrameData={processedFrameData}
          streamingConnectionStatus={streamingConnectionStatus}
          onRetryConnection={onRetryConnection}
          hideWebcamPreview={practiceStarted}
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
  );
};

export default ASLWorldPage;
