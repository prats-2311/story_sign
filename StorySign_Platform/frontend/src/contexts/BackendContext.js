import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from "react";

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
const CONNECTION_RETRY_DELAY = 2000; // 2 seconds
const MAX_RETRY_ATTEMPTS = 5;

export const BackendProvider = ({ children }) => {
  const [connectionStatus, setConnectionStatus] = useState("disconnected");
  const [backendMessage, setBackendMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [retryAttempts, setRetryAttempts] = useState(0);
  const [lastConnectionTime, setLastConnectionTime] = useState(null);

  const testBackendConnection = useCallback(async () => {
    if (isLoading) return;

    setIsLoading(true);
    setConnectionStatus("testing");
    setBackendMessage("Testing backend connection...");

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

      const response = await fetch(`${BACKEND_URL}/health`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        setConnectionStatus("connected");
        setBackendMessage(
          `Backend connected successfully! ${data.message || "System ready"}`
        );
        setRetryAttempts(0);
        setLastConnectionTime(new Date().toISOString());
        console.log("Backend connection successful:", data);
        return { success: true, data };
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      console.error("Backend connection failed:", error);
      setConnectionStatus("error");

      if (error.name === "AbortError") {
        setBackendMessage(
          "Connection timeout. Please check if the backend server is running."
        );
      } else if (error.message.includes("Failed to fetch")) {
        setBackendMessage(
          "Cannot reach backend server. Please ensure it is running on http://127.0.0.1:8000"
        );
      } else {
        setBackendMessage(`Connection failed: ${error.message}`);
      }

      return { success: false, error: error.message };
    } finally {
      setIsLoading(false);
    }
  }, [isLoading]);

  // Auto-retry connection with exponential backoff
  const retryConnection = useCallback(async () => {
    if (retryAttempts >= MAX_RETRY_ATTEMPTS) {
      console.log("Max retry attempts reached. Stopping auto-retry.");
      return;
    }

    const delay = CONNECTION_RETRY_DELAY * Math.pow(2, retryAttempts);
    console.log(
      `Retrying connection in ${delay}ms (attempt ${
        retryAttempts + 1
      }/${MAX_RETRY_ATTEMPTS})`
    );

    setTimeout(async () => {
      setRetryAttempts(prev => prev + 1);
      const result = await testBackendConnection();

      if (!result.success && retryAttempts + 1 < MAX_RETRY_ATTEMPTS) {
        retryConnection();
      }
    }, delay);
  }, [retryAttempts, testBackendConnection]);

  // Auto-connect on component mount
  useEffect(() => {
    console.log("BackendProvider: Attempting automatic connection...");
    testBackendConnection().then(result => {
      if (!result.success) {
        console.log("Initial connection failed, starting retry sequence...");
        retryConnection();
      }
    });
  }, []); // Only run on mount

  // Periodic health check for connected state
  useEffect(() => {
    if (connectionStatus === "connected") {
      const healthCheckInterval = setInterval(async () => {
        try {
          const response = await fetch(`${BACKEND_URL}/health`, {
            method: "GET",
            headers: { "Content-Type": "application/json" },
            signal: AbortSignal.timeout(5000), // 5 second timeout
          });

          if (!response.ok) {
            throw new Error("Health check failed");
          }
        } catch (error) {
          console.warn("Health check failed, connection may be lost:", error);
          setConnectionStatus("error");
          setBackendMessage("Connection lost. Attempting to reconnect...");
          retryConnection();
        }
      }, 30000); // Check every 30 seconds

      return () => clearInterval(healthCheckInterval);
    }
  }, [connectionStatus, retryConnection]);

  // Manual retry function
  const manualRetry = useCallback(() => {
    setRetryAttempts(0);
    testBackendConnection();
  }, [testBackendConnection]);

  // Reset connection state
  const resetConnection = useCallback(() => {
    setConnectionStatus("disconnected");
    setBackendMessage("");
    setRetryAttempts(0);
    setLastConnectionTime(null);
  }, []);

  const contextValue = {
    // Connection state
    connectionStatus,
    backendMessage,
    isLoading,
    retryAttempts,
    lastConnectionTime,

    // Connection methods
    testBackendConnection,
    manualRetry,
    resetConnection,

    // Configuration
    backendUrl: BACKEND_URL,
    maxRetryAttempts: MAX_RETRY_ATTEMPTS,
  };

  return (
    <BackendContext.Provider value={contextValue}>
      {children}
    </BackendContext.Provider>
  );
};

export default BackendProvider;
