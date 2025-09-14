import React, { useCallback } from "react";
import ReconnectPage from "./ReconnectPage";

const ReconnectWrapper = () => {
  // Error handler
  const handleError = useCallback(error => {
    console.error("Reconnect error:", error);
  }, []);

  // Retry connection handler - backend connects automatically
  const handleRetryConnection = useCallback(() => {
    console.log("Backend connection is automatic - no manual retry needed");
  }, []);

  return (
    <ReconnectPage
      onError={handleError}
      onRetryConnection={handleRetryConnection}
    />
  );
};

export default ReconnectWrapper;
