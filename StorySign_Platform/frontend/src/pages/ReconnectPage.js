import React, {
  useState,
  useRef,
  useCallback,
  useReducer,
  useEffect,
} from "react";
import {
  ExerciseSelector,
  MovementAnalysis,
  TherapyDashboard,
} from "../modules/reconnect";
import VideoStreamingClient from "../components/video/VideoStreamingClient";
import API_BASE_URL from "../config/api";
import useWebcam from "../hooks/useWebcam";
import "./ReconnectPage.css";

// State management reducer for Reconnect module
const reconnectReducer = (state, action) => {
  switch (action.type) {
    case "SET_VIEW":
      return { ...state, currentView: action.payload };

    case "START_SESSION":
      return {
        ...state,
        currentView: "practice",
        isSessionActive: true,
        sessionStartTime: Date.now(),
        currentExercise: action.payload.exercise,
        sessionData: {
          exerciseType: action.payload.exercise.id,
          movementData: [],
          jointAngles: {},
          rangeOfMotion: {},
          metrics: [],
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

    case "UPDATE_MOVEMENT_DATA":
      return {
        ...state,
        sessionData: {
          ...state.sessionData,
          movementData: [
            ...state.sessionData.movementData,
            action.payload.landmarks,
          ],
          jointAngles: {
            ...state.sessionData.jointAngles,
            ...action.payload.jointAngles,
          },
          rangeOfMotion: {
            ...state.sessionData.rangeOfMotion,
            ...action.payload.rangeOfMotion,
          },
          metrics: [...state.sessionData.metrics, action.payload.metrics],
        },
        currentAnalysis: action.payload,
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
          exerciseType: null,
          movementData: [],
          jointAngles: {},
          rangeOfMotion: {},
          metrics: [],
        },
        currentAnalysis: null,
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
  currentExercise: null,
  sessionData: {
    exerciseType: null,
    movementData: [],
    jointAngles: {},
    rangeOfMotion: {},
    metrics: [],
  },
  currentAnalysis: null,
  sessionStartTime: null,
  sessionEndTime: null,
  error: null,
};

const ReconnectPage = ({
  streamingConnectionStatus,
  onConnectionChange,
  onProcessedFrame,
  onError,
  onRetryConnection,
}) => {
  const [state, dispatch] = useReducer(reconnectReducer, initialState);
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
        console.log("ReconnectPage: Initializing webcam on component mount");
        await startWebcam();
      } catch (error) {
        console.error("ReconnectPage: Failed to initialize webcam:", error);
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
      console.log("ReconnectPage: Cleaning up webcam on component unmount");
      stopWebcam();
    };
  }, [startWebcam, stopWebcam]);

  // Handle starting a new therapy session
  const handleStartSession = useCallback(
    async exercise => {
      try {
        // Generate session ID
        sessionIdRef.current = `reconnect_${Date.now()}_${Math.random()
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
          payload: { exercise },
        });

        // Send session start message to backend
        if (videoStreamingRef.current) {
          const sessionData = {
            session_id: sessionIdRef.current,
            exercise_type: exercise.id,
            session_type: "therapeutic_movement_analysis",
          };

          const success = videoStreamingRef.current.sendMessage({
            type: "reconnect_session_start",
            data: sessionData,
          });

          if (!success) {
            console.error("Failed to send session start message to backend");
          }
        }

        console.log(`Started Reconnect session for exercise: ${exercise.name}`);
      } catch (error) {
        console.error("Error starting Reconnect session:", error);
        dispatch({
          type: "SET_ERROR",
          payload: {
            type: "SESSION_START_ERROR",
            message: "Failed to start therapy session",
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
          total_movements: state.sessionData.movementData.length,
        };

        videoStreamingRef.current.sendMessage({
          type: "reconnect_session_end",
          data: sessionData,
        });
      }

      // Save session data to backend
      await saveSessionData();

      dispatch({ type: "END_SESSION" });
      console.log("Reconnect session ended");
    } catch (error) {
      console.error("Error ending Reconnect session:", error);
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
    if (!sessionIdRef.current || !state.sessionData.exerciseType) {
      return;
    }

    try {
      const sessionPayload = {
        session_id: sessionIdRef.current,
        exercise_type: state.sessionData.exerciseType,
        movement_data: state.sessionData.movementData,
        joint_angles: state.sessionData.jointAngles,
        range_of_motion: state.sessionData.rangeOfMotion,
        session_duration: state.sessionStartTime
          ? Date.now() - state.sessionStartTime
          : 0,
        metrics: state.sessionData.metrics,
        created_at: new Date().toISOString(),
      };

      const response = await fetch(
        `${API_BASE_URL}/api/v1/reconnect/sessions`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            // Add auth header if available
            ...(localStorage.getItem("token") && {
              Authorization: `Bearer ${localStorage.getItem("token")}`,
            }),
          },
          body: JSON.stringify(sessionPayload),
        }
      );

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
  const handleProcessedFrameWithReconnectLogic = useCallback(
    message => {
      // Call parent's processed frame handler first
      if (onProcessedFrame) {
        onProcessedFrame(message);
      }

      // Handle Reconnect-specific message types
      if (message.type === "reconnect_movement_analysis") {
        const movementData = message.data;

        if (movementData && state.isSessionActive) {
          dispatch({
            type: "UPDATE_MOVEMENT_DATA",
            payload: {
              landmarks: movementData.pose_landmarks,
              jointAngles: movementData.joint_angles,
              rangeOfMotion: movementData.range_of_motion,
              metrics: movementData.movement_metrics,
              timestamp: movementData.timestamp,
            },
          });
        }
      } else if (message.type === "reconnect_session_response") {
        console.log("Reconnect session response:", message.data);
      } else if (message.type === "reconnect_error") {
        dispatch({
          type: "SET_ERROR",
          payload: {
            type: "PROCESSING_ERROR",
            message: message.data.error || "Error processing movement analysis",
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
          Reconnect requires camera access for therapeutic movement analysis and
          physical rehabilitation features.
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
            <li>Make sure you have adequate lighting for movement tracking</li>
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
          <ExerciseSelector
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
          <div className="reconnect-practice-container">
            <div className="practice-video-section">
              <VideoStreamingClient
                ref={videoStreamingRef}
                isActive={streamingConnectionStatus === "connected"}
                onConnectionChange={onConnectionChange}
                onProcessedFrame={handleProcessedFrameWithReconnectLogic}
                onError={onError}
                stream={stream}
                attachToVideoElement={attachToVideoElement}
              />

              <MovementAnalysis
                currentExercise={state.currentExercise}
                currentAnalysis={state.currentAnalysis}
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
          <TherapyDashboard
            sessionData={state.sessionData}
            sessionDuration={
              state.sessionEndTime && state.sessionStartTime
                ? state.sessionEndTime - state.sessionStartTime
                : 0
            }
            exerciseType={state.currentExercise}
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
    <div className="reconnect-page">
      <header className="page-header">
        <h1 id="main-content">Reconnect</h1>
        <p>Therapeutic Movement Analysis & Physical Rehabilitation</p>
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
              ? "Camera Active - Ready for therapy"
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

export default ReconnectPage;
