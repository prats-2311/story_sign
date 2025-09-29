import React, {
  useState,
  useRef,
  useCallback,
  useReducer,
  useEffect,
} from "react";
import {
  ExpressionPractice,
  EmotionMetrics,
  ProgressTracker,
} from "../modules/harmony";
import VideoStreamingClient from "../components/video/VideoStreamingClient";
import API_BASE_URL from "../config/api";
import useWebcam from "../hooks/useWebcam";
import "./HarmonyPage.css";

// State management reducer for Harmony module
const harmonyReducer = (state, action) => {
  switch (action.type) {
    case "SET_VIEW":
      return { ...state, currentView: action.payload };

    case "START_SESSION":
      return {
        ...state,
        currentView: "practice",
        isSessionActive: true,
        sessionStartTime: Date.now(),
        currentEmotion: action.payload.emotion,
        sessionData: {
          targetEmotion: action.payload.emotion,
          detectedEmotions: [],
          confidenceScores: [],
          landmarks: [],
        },
        error: null,
      };

    case "END_SESSION":
      return {
        ...state,
        isSessionActive: false,
        currentView: "results",
        sessionEndTime: Date.now(),
      };

    case "UPDATE_EMOTION_DATA":
      return {
        ...state,
        sessionData: {
          ...state.sessionData,
          detectedEmotions: [
            ...state.sessionData.detectedEmotions,
            action.payload.emotion,
          ],
          confidenceScores: [
            ...state.sessionData.confidenceScores,
            action.payload.confidence,
          ],
          landmarks: [...state.sessionData.landmarks, action.payload.landmarks],
        },
        currentDetection: action.payload,
      };

    case "SET_ERROR":
      return {
        ...state,
        error: action.payload,
        isSessionActive: false,
      };

    case "CLEAR_ERROR":
      return {
        ...state,
        error: null,
      };

    case "RESET_SESSION":
      return {
        ...state,
        currentView: "setup",
        isSessionActive: false,
        sessionData: {
          targetEmotion: null,
          detectedEmotions: [],
          confidenceScores: [],
          landmarks: [],
        },
        currentDetection: null,
        sessionStartTime: null,
        sessionEndTime: null,
        error: null,
      };

    default:
      return state;
  }
};

const initialState = {
  currentView: "setup", // 'setup', 'practice', 'results'
  isSessionActive: false,
  currentEmotion: null,
  sessionData: {
    targetEmotion: null,
    detectedEmotions: [],
    confidenceScores: [],
    landmarks: [],
  },
  currentDetection: null,
  sessionStartTime: null,
  sessionEndTime: null,
  error: null,
};

const HarmonyPage = ({
  streamingConnectionStatus,
  onConnectionChange,
  onProcessedFrame,
  onError,
  onRetryConnection,
}) => {
  const [state, dispatch] = useReducer(harmonyReducer, initialState);
  const videoStreamingRef = useRef(null);
  const sessionIdRef = useRef(null);

  // Use centralized webcam hook
  const {
    stream,
    isActive: webcamActive,
    status: webcamStatus,
    error: webcamError,
    startWebcam,
    stopWebcam,
    attachToVideoElement,
  } = useWebcam();

  // Automatic camera initialization on component mount
  useEffect(() => {
    const initializeWebcam = async () => {
      try {
        console.log("HarmonyPage: Initializing webcam on component mount");
        await startWebcam();
      } catch (error) {
        console.error("HarmonyPage: Failed to initialize webcam:", error);
        dispatch({
          type: "SET_ERROR",
          payload: {
            type: "WEBCAM_INIT_ERROR",
            message: "Failed to initialize camera on page load",
            userAction: "Please allow camera access and refresh the page",
          },
        });
      }
    };

    initializeWebcam();

    // Cleanup webcam on component unmount
    return () => {
      console.log("HarmonyPage: Cleaning up webcam on component unmount");
      stopWebcam();
    };
  }, [startWebcam, stopWebcam]);

  // Handle starting a new emotion practice session
  const handleStartSession = useCallback(
    async emotion => {
      try {
        // Generate session ID
        sessionIdRef.current = `harmony_${Date.now()}_${Math.random()
          .toString(36)
          .substr(2, 9)}`;

        // Start webcam if not already active
        if (!webcamActive) {
          const webcamStarted = await startWebcam();
          if (!webcamStarted) {
            dispatch({
              type: "SET_ERROR",
              payload: {
                type: "WEBCAM_ERROR",
                message:
                  "Failed to start webcam. Please check camera permissions.",
                userAction: "Allow camera access and try again",
              },
            });
            return;
          }
        }

        // Start the session
        dispatch({
          type: "START_SESSION",
          payload: { emotion },
        });

        // Send session start message to backend
        if (videoStreamingRef.current) {
          const sessionData = {
            session_id: sessionIdRef.current,
            target_emotion: emotion,
            session_type: "facial_expression_practice",
          };

          const success = videoStreamingRef.current.sendMessage({
            type: "harmony_session_start",
            data: sessionData,
          });

          if (!success) {
            console.error("Failed to send session start message to backend");
          }
        }

        console.log(`Started Harmony session for emotion: ${emotion}`);
      } catch (error) {
        console.error("Error starting Harmony session:", error);
        dispatch({
          type: "SET_ERROR",
          payload: {
            type: "SESSION_START_ERROR",
            message: "Failed to start practice session",
            userAction: "Please try again",
          },
        });
      }
    },
    [webcamActive, startWebcam]
  );

  // Handle ending the current session
  const handleEndSession = useCallback(async () => {
    try {
      // Send session end message to backend
      if (videoStreamingRef.current && sessionIdRef.current) {
        const sessionData = {
          session_id: sessionIdRef.current,
          session_duration: state.sessionStartTime
            ? Date.now() - state.sessionStartTime
            : 0,
          total_detections: state.sessionData.detectedEmotions.length,
        };

        videoStreamingRef.current.sendMessage({
          type: "harmony_session_end",
          data: sessionData,
        });
      }

      // Save session data to backend
      await saveSessionData();

      dispatch({ type: "END_SESSION" });
      console.log("Harmony session ended");
    } catch (error) {
      console.error("Error ending Harmony session:", error);
      dispatch({
        type: "SET_ERROR",
        payload: {
          type: "SESSION_END_ERROR",
          message: "Error saving session data",
          userAction: "Session data may not have been saved",
        },
      });
    }
  }, [state.sessionStartTime, state.sessionData]);

  // Save session data to backend
  const saveSessionData = useCallback(async () => {
    if (!sessionIdRef.current || !state.sessionData.targetEmotion) {
      return;
    }

    try {
      const sessionPayload = {
        session_id: sessionIdRef.current,
        target_emotion: state.sessionData.targetEmotion,
        detected_emotions: state.sessionData.detectedEmotions,
        confidence_scores: state.sessionData.confidenceScores,
        session_duration: state.sessionStartTime
          ? Date.now() - state.sessionStartTime
          : 0,
        landmarks_data: state.sessionData.landmarks,
        created_at: new Date().toISOString(),
      };

      const response = await fetch(`${API_BASE_URL}/api/v1/harmony/sessions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          // Add auth header if available
          ...(localStorage.getItem("token") && {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          }),
        },
        body: JSON.stringify(sessionPayload),
      });

      if (!response.ok) {
        throw new Error(`Failed to save session: ${response.status}`);
      }

      const result = await response.json();
      console.log("Session saved successfully:", result);
    } catch (error) {
      console.error("Error saving session data:", error);
      throw error;
    }
  }, [state.sessionData, state.sessionStartTime]);

  // Handle processed frame data from WebSocket
  const handleProcessedFrameWithHarmonyLogic = useCallback(
    message => {
      // Call parent's processed frame handler first
      if (onProcessedFrame) {
        onProcessedFrame(message);
      }

      // Handle Harmony-specific message types
      if (message.type === "harmony_emotion_detection") {
        const emotionData = message.data;

        if (emotionData && state.isSessionActive) {
          dispatch({
            type: "UPDATE_EMOTION_DATA",
            payload: {
              emotion: emotionData.detected_emotion,
              confidence: emotionData.confidence_score,
              landmarks: emotionData.facial_landmarks,
              timestamp: emotionData.timestamp,
            },
          });
        }
      } else if (message.type === "harmony_session_response") {
        console.log("Harmony session response:", message.data);
      } else if (message.type === "harmony_error") {
        dispatch({
          type: "SET_ERROR",
          payload: {
            type: "PROCESSING_ERROR",
            message:
              message.data.error || "Error processing facial expressions",
            userAction: "Please try again",
          },
        });
      }
    },
    [onProcessedFrame, state.isSessionActive]
  );

  // Handle resetting to start a new session
  const handleNewSession = useCallback(() => {
    dispatch({ type: "RESET_SESSION" });
    sessionIdRef.current = null;
  }, []);

  // Handle clearing errors
  const handleClearError = useCallback(() => {
    dispatch({ type: "CLEAR_ERROR" });
  }, []);

  // Camera inactive placeholder component
  const CameraInactivePlaceholder = () => (
    <div className="camera-inactive-placeholder" role="status">
      <div className="placeholder-content">
        <div className="camera-icon" aria-hidden="true">
          📷
        </div>
        <h3>Camera Required</h3>
        <p>
          Harmony requires camera access for facial expression practice and
          social-emotional learning features.
        </p>
        {webcamError ? (
          <div className="error-details">
            <p className="error-message">
              <strong>Error:</strong>{" "}
              {webcamError.message || "Camera access failed"}
            </p>
            <div className="error-actions">
              <button
                className="retry-button"
                onClick={startWebcam}
                aria-label="Retry camera access"
              >
                Retry Camera Access
              </button>
              <button
                className="clear-error-button"
                onClick={handleClearError}
                aria-label="Clear error message"
              >
                Clear Error
              </button>
            </div>
          </div>
        ) : (
          <div className="loading-camera">
            <div className="loading-spinner" aria-hidden="true"></div>
            <p>Initializing camera...</p>
          </div>
        )}
        <div className="help-text">
          <h4>Troubleshooting:</h4>
          <ul>
            <li>Allow camera permissions when prompted</li>
            <li>Check that no other applications are using your camera</li>
            <li>Refresh the page if camera access was denied</li>
            <li>Ensure your browser supports camera access</li>
          </ul>
        </div>
      </div>
    </div>
  );

  // Render current view based on state
  const renderCurrentView = () => {
    // Show camera inactive placeholder if webcam is not active
    if (!webcamActive && webcamStatus !== "initializing") {
      return <CameraInactivePlaceholder />;
    }

    switch (state.currentView) {
      case "setup":
        return (
          <ExpressionPractice
            onStartSession={handleStartSession}
            webcamStatus={webcamStatus}
            webcamError={webcamError}
            error={state.error}
            onClearError={handleClearError}
            // Pass webcam state to module
            isWebcamActive={webcamActive}
            webcamStream={stream}
          />
        );

      case "practice":
        return (
          <div className="harmony-practice-container">
            <div className="practice-video-section">
              <VideoStreamingClient
                ref={videoStreamingRef}
                isActive={streamingConnectionStatus === "connected"}
                onConnectionChange={onConnectionChange}
                onProcessedFrame={handleProcessedFrameWithHarmonyLogic}
                onError={onError}
                stream={stream}
                attachToVideoElement={attachToVideoElement}
              />

              <EmotionMetrics
                targetEmotion={state.currentEmotion}
                currentDetection={state.currentDetection}
                sessionData={state.sessionData}
                isSessionActive={state.isSessionActive}
                // Pass webcam state to module
                isWebcamActive={webcamActive}
                webcamStream={stream}
              />
            </div>

            <div className="practice-controls">
              <button
                className="end-session-button"
                onClick={handleEndSession}
                disabled={!state.isSessionActive}
              >
                End Session
              </button>
            </div>
          </div>
        );

      case "results":
        return (
          <ProgressTracker
            sessionData={state.sessionData}
            sessionDuration={
              state.sessionEndTime && state.sessionStartTime
                ? state.sessionEndTime - state.sessionStartTime
                : 0
            }
            onNewSession={handleNewSession}
            // Pass webcam state to module for consistency
            isWebcamActive={webcamActive}
          />
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
    <div className="harmony-page">
      <header className="page-header">
        <h1 id="main-content">Harmony</h1>
        <p>Facial Expression Practice & Social-Emotional Learning</p>
        <div className="connection-status" aria-live="polite" role="status">
          <span
            className={`status-indicator ${
              webcamActive ? "connected" : "disconnected"
            }`}
            aria-hidden="true"
          >
            {webcamActive ? "🟢" : "🔴"}
          </span>
          <span className="status-text">
            {webcamActive
              ? "Camera Active - Ready for practice"
              : webcamStatus === "initializing"
              ? "Initializing camera..."
              : "Camera Required - Please allow access"}
          </span>
        </div>
      </header>

      <main className="page-content" role="main" aria-labelledby="main-content">
        {renderCurrentView()}
      </main>
    </div>
  );
};

export default HarmonyPage;
