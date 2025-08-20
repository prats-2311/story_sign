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

    // WebSocket configuration
    const WS_URL = "ws://localhost:8000/ws/video";
    const MAX_RECONNECT_ATTEMPTS = 5;
    const INITIAL_RECONNECT_DELAY = 1000; // 1 second
    const FRAME_THROTTLE_MS = 100; // Send max 10 frames per second

    // Send frame data to server with enhanced message format
    const sendFrame = useCallback((message) => {
      if (wsRef.current?.readyState !== WebSocket.OPEN) {
        console.warn("WebSocket not connected, cannot send frame");
        return false;
      }

      // Adaptive throttling based on processing capability
      const processingCapability =
        message.metadata?.processing_capability || 1.0;
      const adaptiveThrottleMs = Math.max(
        50,
        FRAME_THROTTLE_MS * (2 - processingCapability)
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

    // Handle incoming messages from server
    const handleIncomingMessage = useCallback(
      (message) => {
        switch (message.type) {
          case "processed_frame":
            setFramesReceived((prev) => prev + 1);
            onProcessedFrame?.(message);
            break;

          case "error":
            console.error("Server error:", message.message);
            setLastError(`Server error: ${message.message}`);
            onError?.(message.message);
            break;

          default:
            console.warn("Unknown message type:", message.type);
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

          // Attempt reconnection if we're still active and it wasn't a manual disconnect
          // Only skip reconnection for manual disconnects (when isActive becomes false)
          if (isActive) {
            console.log(
              "Connection lost while streaming active, attempting reconnection..."
            );
            // Call scheduleReconnect directly to avoid dependency issues
            if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
              const errorMsg = `Max reconnection attempts (${MAX_RECONNECT_ATTEMPTS}) reached`;
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
          const errorMsg = "WebSocket connection error";
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

    // Expose sendFrame method to parent component
    useImperativeHandle(
      ref,
      () => ({
        sendFrame,
      }),
      [sendFrame]
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
