import React, { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useBackend } from "../../contexts/BackendContext";
import MainDashboard from "./MainDashboard";

const Dashboard = () => {
  const navigate = useNavigate();
  const {
    connectionStatus,
    backendMessage,
    isLoading,
    testBackendConnection,
    manualRetry,
  } = useBackend();

  // Webcam and streaming state (placeholder for future implementation)
  const [webcamActive, setWebcamActive] = useState(false);
  const [webcamError, setWebcamError] = useState(null);
  const [streamingActive, setStreamingActive] = useState(false);
  const [streamingError, setStreamingError] = useState(null);
  const [showTroubleshooting, setShowTroubleshooting] = useState(false);

  // Webcam controls (placeholder implementations)
  const toggleWebcam = useCallback(async () => {
    try {
      if (!webcamActive) {
        // Request webcam access
        const stream = await navigator.mediaDevices.getUserMedia({
          video: true,
        });
        setWebcamActive(true);
        setWebcamError(null);
        // Store stream reference for cleanup
        window.currentWebcamStream = stream;
      } else {
        // Stop webcam
        if (window.currentWebcamStream) {
          window.currentWebcamStream.getTracks().forEach(track => track.stop());
          window.currentWebcamStream = null;
        }
        setWebcamActive(false);
        setStreamingActive(false);
      }
    } catch (error) {
      console.error("Webcam error:", error);
      setWebcamError(`Failed to access webcam: ${error.message}`);
      setWebcamActive(false);
    }
  }, [webcamActive]);

  const toggleStreaming = useCallback(() => {
    if (webcamActive && connectionStatus === "connected") {
      setStreamingActive(!streamingActive);
      setStreamingError(null);
    } else {
      setStreamingError(
        "Webcam must be active and backend connected to start streaming"
      );
    }
  }, [webcamActive, connectionStatus, streamingActive]);

  const retryWebcam = useCallback(() => {
    setWebcamError(null);
    toggleWebcam();
  }, [toggleWebcam]);

  const retryStreaming = useCallback(() => {
    setStreamingError(null);
    toggleStreaming();
  }, [toggleStreaming]);

  // Navigation handler
  const handleNavigateToASLWorld = useCallback(() => {
    navigate("/asl-world");
  }, [navigate]);

  // Show troubleshooting when connection fails
  React.useEffect(() => {
    setShowTroubleshooting(connectionStatus === "error");
  }, [connectionStatus]);

  return (
    <MainDashboard
      backendMessage={backendMessage}
      isLoading={isLoading}
      connectionStatus={connectionStatus}
      webcamActive={webcamActive}
      webcamError={webcamError}
      streamingActive={streamingActive}
      streamingError={streamingError}
      showTroubleshooting={showTroubleshooting}
      testBackendConnection={manualRetry}
      toggleWebcam={toggleWebcam}
      toggleStreaming={toggleStreaming}
      retryWebcam={retryWebcam}
      retryStreaming={retryStreaming}
      onNavigateToASLWorld={handleNavigateToASLWorld}
    />
  );
};

export default Dashboard;
