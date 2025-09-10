import React, {
  useEffect,
  useCallback,
  forwardRef,
  useImperativeHandle,
} from "react";
import useWebSocket from "../../hooks/useWebSocket";

const VideoStreamingClient = forwardRef(
  (
    { isActive = false, onConnectionChange, onProcessedFrame, onError },
    ref
  ) => {
    // WebSocket configuration - optimized for low latency
    const WS_URL = "ws://localhost:8000/ws/video";

    // Use centralized WebSocket hook
    const {
      connectionState,
      isConnected,
      error: wsError,
      stats,
      sendMessage,
      addMessageListener,
      removeMessageListener,
      connect,
      disconnect,
    } = useWebSocket(WS_URL, {
      maxReconnectAttempts: 5,
      initialReconnectDelay: 500,
      frameThrottleMs: 50,
      autoConnect: false, // We'll control connection manually based on isActive
    });

    // Send frame data to server with enhanced message format
    const sendFrame = useCallback(
      (message) => {
        if (!isConnected) {
          console.warn("WebSocket not connected, cannot send frame");
          return false;
        }

        // Optimized throttling for low latency
        const processingCapability =
          message.metadata?.processing_capability || 1.0;

        // Use adaptive throttling - better performance gets higher frame rates
        const shouldThrottle = processingCapability < 0.8;

        try {
          console.log(
            `Sending frame ${message.metadata?.frame_number}, size: ${
              JSON.stringify(message).length
            } bytes, FPS: ${message.metadata?.adaptive_fps}, capability: ${(
              processingCapability * 100
            ).toFixed(0)}%`
          );

          return sendMessage(message, { throttle: shouldThrottle });
        } catch (error) {
          console.error("Error sending frame:", error);
          onError?.(`Failed to send frame: ${error.message}`);
          return false;
        }
      },
      [isConnected, sendMessage, onError]
    );

    // Send practice control messages for ASL World
    const sendPracticeControl = useCallback(
      (action, data = {}) => {
        if (!isConnected) {
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

          console.log(`Sending practice control: ${action}`, data);
          return sendMessage(controlMessage, { throttle: false });
        } catch (error) {
          console.error("Error sending practice control:", error);
          onError?.(`Failed to send practice control: ${error.message}`);
          return false;
        }
      },
      [isConnected, sendMessage, onError]
    );

    // Backward-compatible generic control sender exposed to parent via ref
    const sendControlMessage = useCallback(
      (message) => {
        if (!isConnected) {
          console.warn("WebSocket not connected, cannot send control message");
          return false;
        }

        try {
          return sendMessage(message, { throttle: false });
        } catch (error) {
          console.error("Error sending control message:", error);
          onError?.(`Failed to send control message: ${error.message}`);
          return false;
        }
      },
      [isConnected, sendMessage, onError]
    );

    // Handle incoming messages from server using message listeners
    const handleIncomingMessage = useCallback(
      (message) => {
        switch (message.type) {
          case "processed_frame":
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
              onError?.("Received invalid feedback data from server");
            }
            break;

          case "control_response":
          case "practice_session_response":
          case "session_complete":
            // Handle practice control responses
            console.log(`Received ${message.type}:`, message);
            onProcessedFrame?.(message);
            break;

          case "pong":
          case "keepalive":
            // System messages handled by hook
            console.debug(`Received ${message.type} from server`);
            break;

          default:
            console.warn("Unknown message type:", message.type, message);
            // Still pass unknown messages to parent for potential handling
            onProcessedFrame?.(message);
        }
      },
      [onProcessedFrame, onError]
    );

    // Setup message listener for all incoming messages
    useEffect(() => {
      const cleanup = addMessageListener("*", handleIncomingMessage);
      return cleanup;
    }, [addMessageListener, handleIncomingMessage]);

    // Handle connection state changes
    useEffect(() => {
      onConnectionChange?.(connectionState);
    }, [connectionState, onConnectionChange]);

    // Handle WebSocket errors
    useEffect(() => {
      if (wsError) {
        onError?.(wsError.message);
      }
    }, [wsError, onError]);

    // Expose methods and stats to parent component
    useImperativeHandle(
      ref,
      () => ({
        connect,
        disconnect,
        sendFrame,
        sendPracticeControl,
        sendControlMessage,
        framesSent: stats.messagesSent,
        framesReceived: stats.messagesReceived,
        connectionStatus: connectionState,
        lastError: wsError?.message || "",
      }),
      [
        connect,
        disconnect,
        sendFrame,
        sendPracticeControl,
        sendControlMessage,
        stats.messagesSent,
        stats.messagesReceived,
        connectionState,
        wsError,
      ]
    );

    // Effect to handle connection lifecycle
    useEffect(() => {
      if (isActive) {
        connect();
      } else {
        disconnect();
      }
    }, [isActive, connect, disconnect]);

    const getStatusColor = () => {
      switch (connectionState) {
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
      switch (connectionState) {
        case "connected":
          return `Connected (↑${stats.messagesSent} ↓${stats.messagesReceived})`;
        case "error":
          return "Connection Error";
        case "connecting":
          return stats.reconnectAttempts > 0
            ? `Reconnecting (${stats.reconnectAttempts}/5)...`
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

        {wsError && (
          <div className="error-message">
            <p>{wsError.message}</p>
            {connectionState === "error" && (
              <div className="error-actions">
                <button
                  className="retry-btn"
                  onClick={() => {
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
            <span className="stat-label">Messages Sent:</span>
            <span className="stat-value">{stats.messagesSent}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Messages Received:</span>
            <span className="stat-value">{stats.messagesReceived}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Connection:</span>
            <span className="stat-value">{connectionState}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Uptime:</span>
            <span className="stat-value">
              {Math.round(stats.connectionUptime / 1000)}s
            </span>
          </div>
        </div>
      </div>
    );
  }
);

export default VideoStreamingClient;
