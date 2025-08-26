import React, {
  useRef,
  useEffect,
  useState,
  useCallback,
  forwardRef,
  useImperativeHandle,
} from "react";

const VideoStreamingClient = forwardRef(
  (
    { isActive = false, onConnectionChange, onProcessedFrame, onError },
    ref
  ) => {
    const wsRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);
    const reconnectAttemptsRef = useRef(0);
    const lastFrameSentRef = useRef(0);

    const [connectionStatus, setConnectionStatus] = useState("disconnected"); // disconnected, connecting, connected, error
    const [framesSent, setFramesSent] = useState(0);
    const [framesReceived, setFramesReceived] = useState(0);
    const [lastError, setLastError] = useState("");

    // WebSocket configuration - optimized for low latency
    const WS_URL = "ws://localhost:8000/ws/video";
    const MAX_RECONNECT_ATTEMPTS = 5;
    const INITIAL_RECONNECT_DELAY = 500; // Reduced from 1000ms
    const FRAME_THROTTLE_MS = 50; // Increased to 20 FPS for lower latency

    // Send frame data to server with enhanced message format
    const sendFrame = useCallback((message) => {
      if (wsRef.current?.readyState !== WebSocket.OPEN) {
        console.warn("WebSocket not connected, cannot send frame");
        return false;
      }

      // Optimized throttling for low latency
      const processingCapability =
        message.metadata?.processing_capability || 1.0;
      const adaptiveThrottleMs = Math.max(
        33, // Minimum 30 FPS (33ms interval)
        FRAME_THROTTLE_MS * (1.5 - processingCapability * 0.5)
      );

      const now = Date.now();
      if (now - lastFrameSentRef.current < adaptiveThrottleMs) {
        return false; // Skip this frame
      }
      lastFrameSentRef.current = now;

      try {
        const messageStr = JSON.stringify(message);
        console.log(
          `Sending frame ${message.metadata?.frame_number}, size: ${
            messageStr.length
          } bytes, FPS: ${message.metadata?.adaptive_fps}, capability: ${(
            processingCapability * 100
          ).toFixed(0)}%`
        );
        wsRef.current.send(messageStr);
        setFramesSent((prev) => prev + 1);
        return true;
      } catch (error) {
        console.error("Error sending frame:", error);
        setLastError(`Failed to send frame: ${error.message}`);
        return false;
      }
    }, []);

    // Send practice control messages for ASL World
    const sendPracticeControl = useCallback((action, data = {}) => {
      if (wsRef.current?.readyState !== WebSocket.OPEN) {
        console.warn("WebSocket not connected, cannot send practice control");
        return false;
      }

      try {
        const controlMessage = {
          type: "control",
          action: action,
          data: data,
          timestamp: new Date().toISOString(),
        };

        const messageStr = JSON.stringify(controlMessage);
        console.log(`Sending practice control: ${action}`, data);
        wsRef.current.send(messageStr);
        return true;
      } catch (error) {
        console.error("Error sending practice control:", error);
        setLastError(`Failed to send practice control: ${error.message}`);
        return false;
      }
    }, []);

    // Backward-compatible generic control sender exposed to parent via ref
    // Accepts a full message object and sends as-is over WebSocket
    const sendControlMessage = useCallback((message) => {
      if (wsRef.current?.readyState !== WebSocket.OPEN) {
        console.warn("WebSocket not connected, cannot send control message");
        return false;
      }
      try {
        const msg =
          typeof message === "string" ? message : JSON.stringify(message);
        wsRef.current.send(msg);
        return true;
      } catch (error) {
        console.error("Error sending control message:", error);
        setLastError(`Failed to send control message: ${error.message}`);
        return false;
      }
    }, []);

    // Handle incoming messages from server
    const handleIncomingMessage = useCallback(
      (message) => {
        switch (message.type) {
          case "processed_frame":
            setFramesReceived((prev) => prev + 1);
            onProcessedFrame?.(message);
            break;

          case "asl_feedback":
            // Enhanced ASL feedback handling for practice sessions
            console.log("Received ASL feedback:", message.data);

            // Validate feedback data structure
            if (message.data && typeof message.data === "object") {
              // Add timestamp if not present
              if (!message.data.timestamp) {
                message.data.timestamp = new Date().toISOString();
              }

              // Ensure feedback has required fields
              const enhancedFeedback = {
                ...message.data,
                message_id: message.message_id || `feedback_${Date.now()}`,
                session_id: message.session_id || "unknown",
                processing_time: message.metadata?.processing_time_ms || 0,
              };

              // Create enhanced message for parent handling
              const enhancedMessage = {
                ...message,
                data: enhancedFeedback,
                enhanced: true,
              };

              onProcessedFrame?.(enhancedMessage);
            } else {
              console.error("Invalid ASL feedback data structure:", message);
              setLastError("Received invalid feedback data from server");
            }
            break;

          case "control_response":
            // Handle practice control responses (next_sentence, try_again, etc.)
            console.log("Received control response:", message);
            onProcessedFrame?.(message);
            break;

          case "practice_session_response":
            // Handle practice session management responses
            console.log("Received practice session response:", message);
            onProcessedFrame?.(message);
            break;

          case "session_complete":
            // Handle story completion notifications
            console.log("Received session complete:", message);
            onProcessedFrame?.(message);
            break;

          case "pong":
            // Handle pong response to ping
            console.debug("Received pong from server");
            break;

          case "keepalive":
            // Handle keepalive message from server
            console.debug("Received keepalive from server");
            break;

          case "error":
            console.error("Server error:", message.message);
            setLastError(`Server error: ${message.message}`);
            onError?.(message.message);
            break;

          case "critical_error":
            console.error("Critical server error:", message.message);
            setLastError(`Critical error: ${message.message}`);
            onError?.(message.message);
            // Critical errors may require reconnection
            if (message.metadata?.requires_reconnection) {
              disconnect();
              setTimeout(() => connect(), 2000);
            }
            break;

          default:
            console.warn("Unknown message type:", message.type, message);
            // Still pass unknown messages to parent for potential handling
            onProcessedFrame?.(message);
        }
      },
      [onProcessedFrame, onError]
    );

    // Connect to WebSocket
    const connect = useCallback(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        return; // Already connected
      }

      setConnectionStatus("connecting");
      setLastError("");

      try {
        wsRef.current = new WebSocket(WS_URL);

        wsRef.current.onopen = () => {
          console.log("WebSocket connected successfully");
          setConnectionStatus("connected");
          reconnectAttemptsRef.current = 0;
          setLastError("");
          onConnectionChange?.("connected");
        };

        wsRef.current.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            console.log(
              "Received WebSocket message:",
              message.type,
              message.metadata?.frame_number
            );
            handleIncomingMessage(message);
          } catch (error) {
            console.error(
              "Error parsing WebSocket message:",
              error,
              "Raw data:",
              event.data
            );
            setLastError("Invalid message format received");
          }
        };

        wsRef.current.onclose = (event) => {
          console.log("WebSocket closed:", event.code, event.reason);
          setConnectionStatus("disconnected");
          onConnectionChange?.("disconnected");

          // Provide more specific error messages based on close codes
          let closeReason = "";
          if (event.code === 1006) {
            closeReason =
              "Connection lost unexpectedly. The server may be unavailable.";
          } else if (event.code === 1011) {
            closeReason =
              "Server encountered an error while processing the connection.";
          } else if (event.code === 1012) {
            closeReason = "Server is restarting. Please wait and try again.";
          } else if (event.code !== 1000 && event.code !== 1001) {
            closeReason = `Connection closed with code ${event.code}: ${
              event.reason || "Unknown reason"
            }`;
          }

          if (closeReason) {
            setLastError(closeReason);
          }

          // Attempt reconnection if we're still active and it wasn't a manual disconnect
          // Only skip reconnection for manual disconnects (when isActive becomes false)
          if (isActive && event.code !== 1000) {
            // 1000 is normal closure
            console.log(
              "Connection lost while streaming active, attempting reconnection..."
            );
            // Call scheduleReconnect directly to avoid dependency issues
            if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
              const errorMsg = `Max reconnection attempts (${MAX_RECONNECT_ATTEMPTS}) reached. ${closeReason}`;
              setLastError(errorMsg);
              setConnectionStatus("error");
              onError?.(errorMsg);
              return;
            }

            const delay = Math.min(
              INITIAL_RECONNECT_DELAY *
                Math.pow(2, reconnectAttemptsRef.current),
              30000 // Max 30 seconds
            );
            reconnectAttemptsRef.current++;

            console.log(
              `Scheduling reconnection attempt ${reconnectAttemptsRef.current} in ${delay}ms`
            );

            reconnectTimeoutRef.current = setTimeout(() => {
              if (isActive) {
                connect();
              }
            }, delay);
          }
        };

        wsRef.current.onerror = (error) => {
          console.error("WebSocket error:", error);
          let errorMsg = "WebSocket connection error";

          // Provide more specific error messages when possible
          if (
            error.type === "error" &&
            wsRef.current?.readyState === WebSocket.CONNECTING
          ) {
            errorMsg =
              "Failed to connect to video processing server. Please check if the backend is running.";
          } else if (
            error.type === "error" &&
            wsRef.current?.readyState === WebSocket.OPEN
          ) {
            errorMsg =
              "Connection error during video streaming. The connection may be unstable.";
          }

          setLastError(errorMsg);
          setConnectionStatus("error");
          onConnectionChange?.("error");
          onError?.(errorMsg);
        };
      } catch (error) {
        console.error("Error creating WebSocket:", error);
        const errorMsg = `Failed to create WebSocket connection: ${error.message}`;
        setLastError(errorMsg);
        setConnectionStatus("error");
        onError?.(errorMsg);
      }
    }, [isActive, onConnectionChange, onError, handleIncomingMessage]);

    // Disconnect WebSocket
    const disconnect = useCallback(() => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }

      if (wsRef.current) {
        wsRef.current.close(1000, "Normal closure");
        wsRef.current = null;
      }

      setConnectionStatus("disconnected");
      reconnectAttemptsRef.current = 0;
      onConnectionChange?.("disconnected");
    }, [onConnectionChange]);

    // Expose methods and stats to parent component
    useImperativeHandle(
      ref,
      () => ({
        connect,
        disconnect,
        sendFrame,
        sendPracticeControl,
        sendControlMessage,
        framesSent,
        framesReceived,
        connectionStatus,
        lastError,
      }),
      [
        connect,
        disconnect,
        sendFrame,
        sendPracticeControl,
        sendControlMessage,
        framesSent,
        framesReceived,
        connectionStatus,
        lastError,
      ]
    );

    // Effect to handle connection lifecycle
    useEffect(() => {
      if (isActive) {
        connect();
      } else {
        disconnect();
      }

      return () => {
        disconnect();
      };
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isActive]); // Remove connect/disconnect from dependencies to prevent recreation

    // Add periodic connection health check
    useEffect(() => {
      if (!isActive || connectionStatus !== "connected") {
        return;
      }

      const healthCheckInterval = setInterval(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          // Send ping to keep connection alive
          try {
            const pingMessage = {
              type: "ping",
              timestamp: new Date().toISOString(),
            };
            wsRef.current.send(JSON.stringify(pingMessage));
          } catch (error) {
            console.warn("Failed to send ping:", error);
          }
        } else if (wsRef.current?.readyState === WebSocket.CLOSED) {
          console.log(
            "Connection lost during health check, attempting reconnection..."
          );
          connect();
        }
      }, 10000); // Check every 10 seconds

      return () => clearInterval(healthCheckInterval);
    }, [isActive, connectionStatus, connect]);

    // Reset counters when connection changes
    useEffect(() => {
      if (connectionStatus === "connecting") {
        setFramesSent(0);
        setFramesReceived(0);
      }
    }, [connectionStatus]);

    const getStatusColor = () => {
      switch (connectionStatus) {
        case "connected":
          return "#4CAF50";
        case "error":
          return "#f44336";
        case "connecting":
          return "#ff9800";
        default:
          return "#9e9e9e";
      }
    };

    const getStatusText = () => {
      switch (connectionStatus) {
        case "connected":
          return `Connected (↑${framesSent} ↓${framesReceived})`;
        case "error":
          return "Connection Error";
        case "connecting":
          return reconnectAttemptsRef.current > 0
            ? `Reconnecting (${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS})...`
            : "Connecting...";
        default:
          return "Disconnected";
      }
    };

    return (
      <div className="video-streaming-client">
        <div className="streaming-status">
          <span
            className="status-dot"
            style={{ backgroundColor: getStatusColor() }}
          ></span>
          <span className="status-text">{getStatusText()}</span>
        </div>

        {lastError && (
          <div className="error-message">
            <p>{lastError}</p>
            {connectionStatus === "error" && (
              <div className="error-actions">
                <button
                  className="retry-btn"
                  onClick={() => {
                    setLastError("");
                    reconnectAttemptsRef.current = 0;
                    connect();
                  }}
                >
                  Retry Connection
                </button>
              </div>
            )}
          </div>
        )}

        <div className="streaming-stats">
          <div className="stat">
            <span className="stat-label">Frames Sent:</span>
            <span className="stat-value">{framesSent}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Frames Received:</span>
            <span className="stat-value">{framesReceived}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Connection:</span>
            <span className="stat-value">{connectionStatus}</span>
          </div>
        </div>
      </div>
    );
  }
);

export default VideoStreamingClient;
