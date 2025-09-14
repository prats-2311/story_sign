import React, { useCallback, useState } from "react";
import HarmonyPage from "./HarmonyPage";

const HarmonyWrapper = () => {
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

  // Retry connection handler - backend connects automatically
  const handleRetryConnection = useCallback(() => {
    console.log("Backend connection is automatic - no manual retry needed");
  }, []);

  return (
    <HarmonyPage
      streamingConnectionStatus={streamingConnectionStatus}
      onConnectionChange={handleConnectionChange}
      onProcessedFrame={handleProcessedFrame}
      onError={handleError}
      onRetryConnection={handleRetryConnection}
    />
  );
};

export default HarmonyWrapper;
