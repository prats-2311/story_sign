import React, { useState, useRef, useCallback, useReducer } from "react";
import {
  ExpressionPractice,
  EmotionMetrics,
  ProgressTracker,
} from "../modules/harmony";
import VideoStreamingClient from "../components/video/VideoStreamingClient";
import { buildApiUrl } from "../config/api";
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
  connectionStatus,
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

  // Handle starting a new emotion practice session
  const handleStartSession = useCallback(
    async (emotion) => {
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

      const response = await fetch(buildApiUrl("/harmony/sessions"), {
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
    (message) => {
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

  // Render current view based on state
  const renderCurrentView = () => {
    switch (state.currentView) {
      case "setup":
        return (
          <ExpressionPractice
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

export default HarmonyPage;
