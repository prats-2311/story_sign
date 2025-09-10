import React, { useState, useRef, useCallback, useReducer } from "react";
import {
  StorySetup,
  StorySelection,
  PracticeView,
  FeedbackPanel,
} from "../modules/asl_world";
import VideoStreamingClient from "../components/video/VideoStreamingClient";
import { buildApiUrl } from "../config/api";
import "./ASLWorldPage.css";

// State management reducer for ASL World
const aslWorldReducer = (state, action) => {
  switch (action.type) {
    case "SET_VIEW":
      return { ...state, currentView: action.payload };

    case "STORY_GENERATION_START":
      return {
        ...state,
        isGeneratingStory: true,
        storyGenerationError: "",
      };

    case "STORY_GENERATION_SUCCESS":
      return {
        ...state,
        isGeneratingStory: false,
        storyData: action.payload,
        currentView: "story_selection",
        selectedStory: null,
        currentSentenceIndex: 0,
        latestFeedback: null,
        practiceStarted: false,
      };

    case "STORY_GENERATION_ERROR":
      return {
        ...state,
        isGeneratingStory: false,
        storyGenerationError: action.payload,
      };

    case "DISMISS_ERROR":
      return {
        ...state,
        storyGenerationError: "",
      };

    case "SELECT_STORY":
      return {
        ...state,
        selectedStory: action.payload,
        currentView: "practice",
        currentSentenceIndex: 0,
        latestFeedback: null,
        practiceStarted: false,
      };

    case "START_PRACTICE":
      return {
        ...state,
        practiceStarted: true,
      };

    case "SET_GESTURE_STATE":
      return {
        ...state,
        gestureState: action.payload,
        isProcessingFeedback: action.payload === "analyzing",
      };

    case "SET_FEEDBACK":
      return {
        ...state,
        latestFeedback: action.payload,
        isProcessingFeedback: false,
        gestureState: action.payload?.completed ? "completed" : "listening",
      };

    case "NEXT_SENTENCE":
      return {
        ...state,
        currentSentenceIndex: state.currentSentenceIndex + 1,
        latestFeedback: null,
        isProcessingFeedback: false,
        gestureState: "listening",
      };

    case "TRY_AGAIN":
      return {
        ...state,
        latestFeedback: null,
        isProcessingFeedback: false,
        gestureState: "listening",
      };

    case "RESTART_STORY":
      return {
        ...state,
        currentSentenceIndex: 0,
        latestFeedback: null,
        isProcessingFeedback: false,
        gestureState: "listening",
      };

    case "NEW_STORY":
      return {
        ...state,
        currentView: "story_generation",
        storyData: null,
        selectedStory: null,
        currentSentenceIndex: 0,
        latestFeedback: null,
        isProcessingFeedback: false,
        gestureState: "listening",
        practiceStarted: false,
      };

    default:
      return state;
  }
};

const initialState = {
  currentView: "story_generation", // 'story_generation', 'story_selection', 'practice'
  storyData: null,
  selectedStory: null,
  currentSentenceIndex: 0,
  latestFeedback: null,
  isGeneratingStory: false,
  isProcessingFeedback: false,
  storyGenerationError: "",
  gestureState: "listening",
  practiceStarted: false,
};

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
  toggleWebcam,
  toggleStreaming,
  testBackendConnection,
}) => {
  const [state, dispatch] = useReducer(aslWorldReducer, initialState);
  const hasStartedPracticeRef = useRef(false);

  // Effect 1: When stories are generated, reset practice session flag
  React.useEffect(() => {
    if (state.storyData) {
      hasStartedPracticeRef.current = false;
    }
  }, [state.storyData]);

  // Effect 2: When the streaming connection is established, start the session (only if user started practice)
  React.useEffect(() => {
    if (
      state.selectedStory &&
      state.practiceStarted &&
      streamingConnectionStatus === "connected" &&
      videoStreamingRef.current &&
      !hasStartedPracticeRef.current
    ) {
      hasStartedPracticeRef.current = true;
      startPracticeSession(state.selectedStory);
    }
  }, [state.selectedStory, state.practiceStarted, streamingConnectionStatus]);

  // Effect 3: Auto-reconnect WebSocket after story generation if needed
  React.useEffect(() => {
    if (
      state.storyData &&
      !state.isGeneratingStory &&
      streamingConnectionStatus === "disconnected" &&
      webcamActive &&
      connectionStatus === "connected"
    ) {
      console.log(
        "Story generation completed but WebSocket disconnected, attempting reconnection..."
      );

      const reconnectTimer = setTimeout(() => {
        if (toggleStreaming && !streamingActive) {
          console.log("Auto-reconnecting WebSocket after story generation");
          toggleStreaming();
        }
      }, 2000);

      return () => clearTimeout(reconnectTimer);
    }
  }, [
    state.storyData,
    state.isGeneratingStory,
    streamingConnectionStatus,
    webcamActive,
    connectionStatus,
    streamingActive,
    toggleStreaming,
  ]);

  // Handler for starting practice session
  const handleStartPractice = useCallback(async () => {
    console.log(
      "Starting practice session - checking backend connection, webcam and streaming status"
    );

    // Test backend connection if not already connected
    if (connectionStatus !== "connected" && testBackendConnection) {
      console.log("Testing backend connection for practice session");
      await testBackendConnection();
    }

    // Activate webcam if not already active
    if (!webcamActive && toggleWebcam) {
      console.log("Activating webcam for practice session");
      toggleWebcam();
    }

    // Set practice started flag
    dispatch({ type: "START_PRACTICE" });
  }, [connectionStatus, testBackendConnection, webcamActive, toggleWebcam]);

  // Effect to handle streaming activation after webcam is active and backend is connected
  React.useEffect(() => {
    if (
      state.practiceStarted &&
      webcamActive &&
      !streamingActive &&
      connectionStatus === "connected" &&
      toggleStreaming
    ) {
      console.log(
        "Backend connected and webcam is active, now activating streaming for practice session"
      );
      const timer = setTimeout(() => {
        toggleStreaming();
      }, 1000);

      return () => clearTimeout(timer);
    }
  }, [
    state.practiceStarted,
    webcamActive,
    streamingActive,
    connectionStatus,
    toggleStreaming,
  ]);

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

  // Story generation handler
  const handleStoryGenerate = useCallback(async (payload) => {
    dispatch({ type: "STORY_GENERATION_START" });

    try {
      console.log("Starting story generation with payload:", payload);

      const response = await fetch(
        buildApiUrl("/asl-world/story/recognize_and_generate"),
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        }
      );

      if (response.ok) {
        const data = await response.json();

        if (data.success && data.stories) {
          console.log("Stories generated successfully:", data.stories);
          dispatch({ type: "STORY_GENERATION_SUCCESS", payload: data.stories });
        } else {
          const errorMessage =
            data.user_message || data.message || "Story generation failed";
          console.error("Story generation failed:", errorMessage);
          dispatch({ type: "STORY_GENERATION_ERROR", payload: errorMessage });
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
        dispatch({ type: "STORY_GENERATION_ERROR", payload: errorMessage });
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
      dispatch({ type: "STORY_GENERATION_ERROR", payload: errorMessage });
    }
  }, []);

  // Story selection handler
  const handleStorySelect = useCallback((story) => {
    console.log("Story selected:", story.title);
    dispatch({ type: "SELECT_STORY", payload: story });
  }, []);

  // Handler to go back to story generation
  const handleBackToGeneration = useCallback(() => {
    dispatch({ type: "SET_VIEW", payload: "story_generation" });
  }, []);

  // Handler to dismiss error
  const handleDismissError = useCallback(() => {
    dispatch({ type: "DISMISS_ERROR" });
  }, []);

  const handlePracticeControl = useCallback(
    async (action, sentenceIndex = state.currentSentenceIndex) => {
      console.log(
        `Practice control action: ${action} at sentence ${sentenceIndex}`
      );

      try {
        // Prepare control data with enhanced information
        const controlData = {
          sentence_index: sentenceIndex,
          target_sentence:
            state.selectedStory?.sentences?.[sentenceIndex] || "",
          story_sentences: state.selectedStory?.sentences || [],
          story_title: state.selectedStory?.title || "Unknown Story",
          session_timestamp: new Date().toISOString(),
          previous_feedback: state.latestFeedback
            ? {
                confidence: state.latestFeedback.confidence_score,
                had_suggestions: state.latestFeedback.suggestions?.length > 0,
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

        // Update local state based on action
        switch (action) {
          case "next_sentence":
            if (
              sentenceIndex <
              (state.selectedStory?.sentences?.length || 0) - 1
            ) {
              dispatch({ type: "NEXT_SENTENCE" });
              console.log(
                `Advanced to sentence ${sentenceIndex + 2}/${
                  state.selectedStory?.sentences?.length
                }`
              );
            } else {
              // This is the last sentence, trigger completion
              console.log("Attempting to complete story from last sentence");
              handlePracticeControl("complete_story", sentenceIndex);
            }
            break;

          case "try_again":
            dispatch({ type: "TRY_AGAIN" });
            console.log(
              `Retrying sentence ${sentenceIndex + 1}: "${
                state.selectedStory?.sentences?.[sentenceIndex]
              }"`
            );
            break;

          case "complete_story":
            console.log("Story practice completed!");
            dispatch({ type: "SET_GESTURE_STATE", payload: "completed" });
            break;

          case "restart_story":
            dispatch({ type: "RESTART_STORY" });
            console.log("Restarting story from beginning");
            break;

          case "new_story":
            dispatch({ type: "NEW_STORY" });
            console.log("Preparing for new story generation");
            break;

          default:
            console.warn(`Unknown practice control action: ${action}`);
        }
      } catch (error) {
        console.error("Error handling practice control:", error);
        dispatch({ type: "SET_GESTURE_STATE", payload: "listening" });
      }
    },
    [
      state.currentSentenceIndex,
      state.selectedStory,
      state.latestFeedback,
      streamingActive,
    ]
  );

  const handleASLFeedback = useCallback(
    (feedbackData, isEnhanced = false) => {
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
            state.selectedStory?.sentences?.[state.currentSentenceIndex] ||
            "",
          // Add metadata
          received_at: new Date().toISOString(),
          sentence_index: state.currentSentenceIndex,
          story_title: state.selectedStory?.title || "Unknown Story",
          // Processing information
          processing_time: feedbackData.processing_time || 0,
          session_id: feedbackData.session_id || "unknown",
        };

        dispatch({ type: "SET_FEEDBACK", payload: enhancedFeedback });

        // Log feedback for debugging
        console.log("Enhanced feedback set:", {
          sentence: enhancedFeedback.target_sentence,
          confidence: enhancedFeedback.confidence_score,
          suggestionsCount: enhancedFeedback.suggestions.length,
          processingTime: enhancedFeedback.processing_time,
        });
      } else {
        console.error("Invalid feedback data received:", feedbackData);
        const errorFeedback = {
          feedback: "Error: Invalid feedback received from server",
          confidence_score: 0,
          suggestions: ["Please try signing again"],
          target_sentence:
            state.selectedStory?.sentences?.[state.currentSentenceIndex] || "",
          error: true,
          received_at: new Date().toISOString(),
        };
        dispatch({ type: "SET_FEEDBACK", payload: errorFeedback });
      }
    },
    [state.selectedStory, state.currentSentenceIndex]
  );

  const handlePracticeSessionUpdate = useCallback((practiceData) => {
    console.log("Practice session update:", practiceData);

    // Update processing feedback state based on gesture state
    if (practiceData.gesture_state) {
      dispatch({
        type: "SET_GESTURE_STATE",
        payload: practiceData.gesture_state,
      });
    }
  }, []);

  const handlePracticeControlResponse = useCallback((message) => {
    console.log("Practice control response:", message);

    if (message.result && message.result.success) {
      const action = message.action;
      const result = message.result;

      // Update local state based on successful backend response
      if (
        action === "next_sentence" &&
        result.current_sentence_index !== undefined
      ) {
        // Backend confirmed the sentence change
        console.log("Backend confirmed sentence advancement");
      } else if (action === "try_again") {
        dispatch({ type: "TRY_AGAIN" });
      } else if (action === "complete_story") {
        dispatch({ type: "SET_GESTURE_STATE", payload: "completed" });
      }
    } else {
      console.error("Practice control failed:", message.result?.error);
    }
  }, []);

  const handlePracticeSessionResponse = useCallback((message) => {
    console.log("Practice session response:", message);

    if (message.result && message.result.success) {
      const action = message.action;

      if (action === "session_started") {
        console.log("Practice session started successfully on backend");
        // Reset practice state for new session
        dispatch({ type: "RESTART_STORY" });
      }
    } else {
      console.error(
        "Practice session operation failed:",
        message.result?.error
      );
    }
  }, []);

  const handleSessionComplete = useCallback(
    (message) => {
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
            total_sentences: state.selectedStory?.sentences?.length || 0,
            completion_time: completionData.completion_time || 0,
            average_confidence: completionData.average_confidence || 0,
          },
          received_at: new Date().toISOString(),
        };

        dispatch({ type: "SET_FEEDBACK", payload: completionFeedback });
        console.log("Story completion feedback set:", completionFeedback);
      }
    },
    [state.selectedStory]
  );

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

  const renderCurrentView = () => {
    switch (state.currentView) {
      case "story_generation":
        return (
          <StorySetup
            onStoryGenerate={handleStoryGenerate}
            isGeneratingStory={state.isGeneratingStory}
            connectionStatus={connectionStatus}
            generationError={state.storyGenerationError}
            onDismissError={handleDismissError}
          />
        );

      case "story_selection":
        return (
          <StorySelection
            storyData={state.storyData}
            onStorySelect={handleStorySelect}
            onBackToGeneration={handleBackToGeneration}
          />
        );

      case "practice":
        return (
          <div className="practice-container">
            <PracticeView
              selectedStory={state.selectedStory}
              currentSentenceIndex={state.currentSentenceIndex}
              practiceStarted={state.practiceStarted}
              gestureState={state.gestureState}
              isProcessingFeedback={state.isProcessingFeedback}
              onStartPractice={handleStartPractice}
              onPracticeControl={handlePracticeControl}
            >
              <VideoStreamingClient
                ref={videoStreamingRef}
                isActive={streamingActive}
                onConnectionChange={onConnectionChange}
                onProcessedFrame={handleProcessedFrameWithASLLogic}
                onError={onError}
              />
            </PracticeView>

            {state.latestFeedback && (
              <FeedbackPanel
                feedback={state.latestFeedback}
                currentSentenceIndex={state.currentSentenceIndex}
                totalSentences={state.selectedStory?.sentences?.length || 0}
                onPracticeControl={handlePracticeControl}
                isProcessingFeedback={state.isProcessingFeedback}
              />
            )}
          </div>
        );

      default:
        return (
          <div className="error-view" role="alert">
            <h2>Unknown View State</h2>
            <p>
              The application is in an unknown state. Please refresh the page.
            </p>
          </div>
        );
    }
  };

  return (
    <div className="asl-world-page">
      <header className="page-header">
        <h1 id="main-content">ASL World</h1>
        <p>Interactive American Sign Language Learning</p>
        <div className="connection-status" aria-live="polite" role="status">
          <span
            className={`status-indicator ${connectionStatus}`}
            aria-hidden="true"
          >
            {connectionStatus === "connected" && "🟢"}
            {connectionStatus === "connecting" && "🟡"}
            {connectionStatus === "disconnected" && "🔴"}
          </span>
          <span className="status-text">
            Connection status: {connectionStatus === "connected" && "Connected"}
            {connectionStatus === "connecting" && "Connecting..."}
            {connectionStatus === "disconnected" && "Disconnected"}
          </span>
        </div>
      </header>

      <main className="page-content" role="main" aria-labelledby="main-content">
        {renderCurrentView()}
      </main>
    </div>
  );
};

export default ASLWorldPage;
