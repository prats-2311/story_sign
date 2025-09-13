import React, { useState, useRef, useCallback, useReducer } from "react";
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
  connectionStatus,
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

  // Render current view based on state
  const renderCurrentView = () => {
    switch (state.currentView) {
      case "setup":
        return (
          <ExerciseSelector
            onStartSession={handleStartSession}
            connectionStatus={connectionStatus}
            webcamStatus={webcamStatus}
            webcamError={webcamError}
            error={state.error}
            onClearError={handleClearError}
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
        <h1>Reconnect</h1>
        <p>Therapeutic Movement Analysis & Physical Rehabilitation</p>
        <div className="connection-status" aria-live="polite">
          <span
            className={`status-indicator ${connectionStatus}`}
            aria-hidden="true"
          >
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
      </header>

      <main className="page-content">{renderCurrentView()}</main>
    </div>
  );
};

export default ReconnectPage;
