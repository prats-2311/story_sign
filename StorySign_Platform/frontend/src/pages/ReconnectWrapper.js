import React, { useCallback } from "react";
import { useBackend } from "../contexts/BackendContext";
import ReconnectPage from "./ReconnectPage";

const ReconnectWrapper = () => {
  const { connectionStatus, testBackendConnection } = useBackend();

  // Error handler
  const handleError = useCallback(error => {
    console.error("Reconnect error:", error);
  }, []);

  // Retry connection handler
  const handleRetryConnection = useCallback(() => {
    testBackendConnection();
  }, [testBackendConnection]);

  return (
    <ReconnectPage
      connectionStatus={connectionStatus}
      onError={handleError}
      onRetryConnection={handleRetryConnection}
    />
  );
};

export default ReconnectWrapper;
