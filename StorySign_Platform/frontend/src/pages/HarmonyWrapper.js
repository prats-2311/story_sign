import React, { useCallback, useState } from "react";
import { useBackend } from "../contexts/BackendContext";
import HarmonyPage from "./HarmonyPage";

const HarmonyWrapper = () => {
  const { connectionStatus, testBackendConnection } = useBackend();

  const [streamingConnectionStatus, setStreamingConnectionStatus] =
    useState("disconnected");

  // Connection change handler
  const handleConnectionChange = useCallback(status => {
    setStreamingConnectionStatus(status);
  }, []);

  // Processed frame handler
  const handleProcessedFrame = useCallback(frameData => {
    console.log("Harmony processed frame:", frameData);
  }, []);

  // Error handler
  const handleError = useCallback(error => {
    console.error("Harmony error:", error);
  }, []);

  // Retry connection handler
  const handleRetryConnection = useCallback(() => {
    testBackendConnection();
  }, [testBackendConnection]);

  return (
    <HarmonyPage
      connectionStatus={connectionStatus}
      streamingConnectionStatus={streamingConnectionStatus}
      onConnectionChange={handleConnectionChange}
      onProcessedFrame={handleProcessedFrame}
      onError={handleError}
      onRetryConnection={handleRetryConnection}
    />
  );
};

export default HarmonyWrapper;
