import React, { useRef, useCallback, useReducer, useEffect } from "react";
import {
  StorySetup,
  StorySelection,
  PracticeView,
  FeedbackPanel,
} from "../modules/asl_world";
import VideoStreamingClient from "../components/video/VideoStreamingClient";
import useWebSocket from "../hooks/useWebSocket";
import useWebcam from "../hooks/useWebcam";
import API_BASE_URL from "../config/api";
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
  // Existing props for backward compatibility
  webcamActive,
  streamingActive,
  videoStreamingRef,
  processedFrameData,
  streamingConnectionStatus,
  onConnectionChange,
  onProcessedFrame,
  onError,
  toggleWebcam,
  toggleStreaming,
}) => {
  const [state, dispatch] = useReducer(aslWorldReducer, initialState);
  const hasStartedPracticeRef = useRef(false);

  // Add persistent webcam and WebSocket state at page level
  const { connectionState, isConnected, lastMessage, sendMessage } =
    useWebSocket("ws://127.0.0.1:8000/ws/video", {
      autoConnect: false, // We'll connect manually when needed
      maxReconnectAttempts: 5,
      frameThrottleMs: 50,
    });

  const {
    stream: webcamStream,
    isActive: isWebcamActive,
    error: webcamError,
    startWebcam,
    stopWebcam,
    captureFrame,
  } = useWebcam();

  // Internal refs for video streaming client
  const internalVideoStreamingRef = useRef(null);

  // Webcam lifecycle management
  useEffect(() => {
    // Initialize webcam when component mounts
    const initializeWebcam = async () => {
      try {
        await startWebcam();
      } catch (error) {
        console.error("Failed to initialize webcam:", error);
      }
    };

    initializeWebcam();

    // Cleanup webcam on unmount
    return () => {
      stopWebcam();
    };
  }, [startWebcam, stopWebcam]);

  // Helper functions to determine which state to use (props vs internal hooks)
  const getWebcamActive = () =>
    webcamActive !== undefined ? webcamActive : isWebcamActive;
  const getStreamingActive = () =>
    streamingActive !== undefined ? streamingActive : isConnected;
  const getConnectionStatus = () =>
    streamingConnectionStatus || connectionState;
  const getVideoStreamingRef = () =>
    videoStreamingRef || internalVideoStreamingRef;

  // Effect 1: When stories are generated, reset practice session flag
  React.useEffect(() => {
    if (state.storyData) {
      hasStartedPracticeRef.current = false;
    }
  }, [state.storyData]);

  // Effect 2: When the streaming connection is established, start the session (only if user started practice)
  React.useEffect(() => {
    const currentStreamingStatus = getConnectionStatus();
    const currentVideoRef = getVideoStreamingRef();

    if (
      state.selectedStory &&
      state.practiceStarted &&
      currentStreamingStatus === "connected" &&
      currentVideoRef.current &&
      !hasStartedPracticeRef.current
    ) {
      hasStartedPracticeRef.current = true;
      startPracticeSession(state.selectedStory);
    }
  }, [
    state.selectedStory,
    state.practiceStarted,
    connectionState,
    streamingConnectionStatus,
  ]);

  // Effect 3: Auto-reconnect WebSocket after story generation if needed
  React.useEffect(() => {
    const currentStreamingStatus = getConnectionStatus();
    const currentWebcamActive = getWebcamActive();
    const currentStreamingActive = getStreamingActive();

    if (
      state.storyData &&
      !state.isGeneratingStory &&
      currentStreamingStatus === "disconnected" &&
      currentWebcamActive
    ) {
      console.log(
        "Story generation completed but WebSocket disconnected, attempting reconnection..."
      );

      const reconnectTimer = setTimeout(() => {
        if (toggleStreaming && !currentStreamingActive) {
          console.log("Auto-reconnecting WebSocket after story generation");
          toggleStreaming();
        }
      }, 2000);

      return () => clearTimeout(reconnectTimer);
    }
  }, [
    state.storyData,
    state.isGeneratingStory,
    connectionState,
    streamingConnectionStatus,
    isWebcamActive,
    webcamActive,
    isConnected,
    streamingActive,
    toggleStreaming,
  ]);

  // Handler for starting practice session - automatic backend connection
  const handleStartPractice = useCallback(async () => {
    console.log("Starting practice session - activating webcam and streaming");

    const currentWebcamActive = getWebcamActive();

    // Activate webcam if not already active
    if (!currentWebcamActive) {
      if (toggleWebcam) {
        console.log("Activating webcam for practice session via props");
        toggleWebcam();
      } else if (!isWebcamActive) {
        console.log("Activating webcam for practice session via hook");
        await startWebcam();
      }
    }

    // Set practice started flag - backend connection is automatic
    dispatch({ type: "START_PRACTICE" });
  }, [
    webcamActive,
    isWebcamActive,
    toggleWebcam,
    startWebcam,
    getWebcamActive,
  ]);

  // Effect to handle streaming activation after webcam is active - automatic backend connection
  React.useEffect(() => {
    const currentWebcamActive = getWebcamActive();
    const currentStreamingActive = getStreamingActive();

    if (
      state.practiceStarted &&
      currentWebcamActive &&
      !currentStreamingActive
    ) {
      console.log(
        "Webcam is active, now activating streaming for practice session (backend connects automatically)"
      );
      const timer = setTimeout(() => {
        if (toggleStreaming) {
          toggleStreaming();
        }
      }, 1000);

      return () => clearTimeout(timer);
    }
  }, [
    state.practiceStarted,
    webcamActive,
    isWebcamActive,
    streamingActive,
    isConnected,
    toggleStreaming,
    getWebcamActive,
    getStreamingActive,
  ]);

  // Practice session management functions
  const startPracticeSession = async story => {
    console.log("Starting practice session with story:", story.title);

    try {
      const currentVideoRef = getVideoStreamingRef();
      const currentStreamingActive = getStreamingActive();

      // Send practice session start message to backend via WebSocket
      if (currentVideoRef.current && currentStreamingActive) {
        const sessionData = {
          story_sentences: story.sentences,
          session_id: `session_${Date.now()}`,
          story_title: story.title,
        };

        const success = currentVideoRef.current.sendPracticeControl(
          "start_session",
          sessionData
        );

        if (success) {
          console.log("Practice session started successfully");
        } else {
          console.error("Failed to start practice session");
        }
      } else if (isConnected && sendMessage) {
        // Use internal WebSocket hook if available
        const sessionData = {
          type: "start_session",
          story_sentences: story.sentences,
          session_id: `session_${Date.now()}`,
          story_title: story.title,
        };

        const success = sendMessage(sessionData);
        if (success) {
          console.log(
            "Practice session started successfully via internal WebSocket"
          );
        } else {
          console.error(
            "Failed to start practice session via internal WebSocket"
          );
        }
      } else {
        console.warn("WebSocket not available for practice session start");
      }
    } catch (error) {
      console.error("Error starting practice session:", error);
    }
  };

  // Story generation handler
  const handleStoryGenerate = useCallback(async payload => {
    dispatch({ type: "STORY_GENERATION_START" });

    try {
      console.log("Starting story generation with payload:", payload);

      const response = await fetch(
        `${API_BASE_URL}/api/asl-world/story/recognize_and_generate`,
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
  const handleStorySelect = useCallback(story => {
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
        const currentVideoRef = getVideoStreamingRef();
        const currentStreamingActive = getStreamingActive();

        if (currentVideoRef.current && currentStreamingActive) {
          const success = currentVideoRef.current.sendPracticeControl(
            action,
            controlData
          );

          if (!success) {
            console.error("Failed to send practice control to backend");
            return;
          }
        } else if (isConnected && sendMessage) {
          // Use internal WebSocket hook if available
          const controlMessage = {
            type: "practice_control",
            action,
            data: controlData,
          };

          const success = sendMessage(controlMessage);
          if (!success) {
            console.error(
              "Failed to send practice control via internal WebSocket"
            );
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
      isConnected,
      sendMessage,
      getVideoStreamingRef,
      getStreamingActive,
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

  const handlePracticeSessionUpdate = useCallback(practiceData => {
    console.log("Practice session update:", practiceData);

    // Update processing feedback state based on gesture state
    if (practiceData.gesture_state) {
      dispatch({
        type: "SET_GESTURE_STATE",
        payload: practiceData.gesture_state,
      });
    }
  }, []);

  const handlePracticeControlResponse = useCallback(message => {
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

  const handlePracticeSessionResponse = useCallback(message => {
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
    message => {
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
  const handleProcessedFrameWithASLLogic = message => {
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
    const currentWebcamActive = getWebcamActive();
    const currentStreamingActive = getStreamingActive();
    const currentConnectionStatus = getConnectionStatus();
    const currentVideoRef = getVideoStreamingRef();

    switch (state.currentView) {
      case "story_generation":
        return (
          <StorySetup
            onStoryGenerate={handleStoryGenerate}
            isGeneratingStory={state.isGeneratingStory}
            generationError={state.storyGenerationError}
            onDismissError={handleDismissError}
            // Pass webcam props for object scanning
            webcamRef={webcamStream} // Pass the actual webcam stream
            isWebcamActive={currentWebcamActive}
            captureFrame={captureFrame}
            webcamError={webcamError?.message}
            // Pass connection status for display
            connectionStatus={currentConnectionStatus}
          />
        );

      case "story_selection":
        return (
          <StorySelection
            storyData={state.storyData}
            onStorySelect={handleStorySelect}
            onBackToGeneration={handleBackToGeneration}
            // StorySelection doesn't need webcam/WebSocket props for consistency
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
              // Pass processedFrame and sendControlMessage props for video streaming
              processedFrame={processedFrameData || lastMessage}
              sendControlMessage={sendMessage}
            >
              {/* VideoStreamingClient continues to work as children of PracticeView */}
              <VideoStreamingClient
                ref={currentVideoRef}
                isActive={currentStreamingActive}
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
                // FeedbackPanel doesn't need webcam/WebSocket props for consistency
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
            className={`status-indicator ${
              getConnectionStatus() === "connected"
                ? "connected"
                : "disconnected"
            }`}
            aria-hidden="true"
          >
            {getConnectionStatus() === "connected" ? "🟢" : "🔴"}
          </span>
          <span className="status-text">
            {getConnectionStatus() === "connected"
              ? "Backend connected - Ready for practice"
              : "Backend ready - Start practicing to connect automatically"}
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
