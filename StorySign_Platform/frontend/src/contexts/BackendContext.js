import React, { createContext, useContext } from "react";

const BackendContext = createContext();

export const useBackend = () => {
  const context = useContext(BackendContext);
  if (!context) {
    throw new Error("useBackend must be used within a BackendProvider");
  }
  return context;
};

const BACKEND_URL =
  process.env.REACT_APP_BACKEND_URL || "http://127.0.0.1:8000";

export const BackendProvider = ({ children }) => {
  // Simplified context - backend connection is automatic
  const contextValue = {
    // Configuration
    backendUrl: BACKEND_URL,
    // Backend is always considered ready since connection is automatic
    connectionStatus: "connected",
    backendMessage: "Backend ready - connections are automatic",
    isLoading: false,
  };

  return (
    <BackendContext.Provider value={contextValue}>
      {children}
    </BackendContext.Provider>
  );
};

export default BackendProvider;
