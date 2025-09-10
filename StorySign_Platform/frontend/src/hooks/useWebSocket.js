/**
 * useWebSocket Hook
 * Centralized WebSocket management hook for StorySign Platform
 * Provides auto-reconnection, connection state tracking, and message handling
 */

import { useState, useRef, useCallback, useEffect } from "react";

const useWebSocket = (url, options = {}) => {
  // Configuration with defaults
  const config = {
    maxReconnectAttempts: 5,
    initialReconnectDelay: 500,
    maxReconnectDelay: 30000,
    frameThrottleMs: 50,
    healthCheckInterval: 10000,
    autoConnect: true,
    ...options,
  };

  // State management
  const [connectionState, setConnectionState] = useState("disconnected"); // disconnected, connecting, connected, error
  const [lastMessage, setLastMessage] = useState(null);
  const [messageHistory, setMessageHistory] = useState([]);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    messagesSent: 0,
    messagesReceived: 0,
    reconnectAttempts: 0,
    connectionUptime: 0,
    lastConnectedAt: null,
  });

  // Refs for WebSocket management
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const lastMessageSentRef = useRef(0);
  const healthCheckIntervalRef = useRef(null);
  const connectionStartTimeRef = useRef(null);
  const messageListenersRef = useRef(new Map());

  /**
   * Handle incoming WebSocket messages
   */
  const handleMessage = useCallback((event) => {
    try {
      const message = JSON.parse(event.data);

      // Update stats
      setStats((prev) => ({
        ...prev,
        messagesReceived: prev.messagesReceived + 1,
      }));

      // Store message in history (keep last 100 messages)
      setMessageHistory((prev) => {
        const newHistory = [
          ...prev,
          { ...message, receivedAt: new Date().toISOString() },
        ];
        return newHistory.slice(-100);
      });

      // Set as last message
      setLastMessage(message);

      // Call registered message listeners
      messageListenersRef.current.forEach((listener, type) => {
        if (message.type === type || type === "*") {
          try {
            listener(message);
          } catch (err) {
            console.error(`Error in message listener for type ${type}:`, err);
          }
        }
      });

      // Handle system messages
      switch (message.type) {
        case "pong":
          console.debug("Received pong from server");
          break;
        case "keepalive":
          console.debug("Received keepalive from server");
          break;
        case "error":
          console.error("Server error:", message.message);
          setError({
            type: "SERVER_ERROR",
            message: message.message,
            timestamp: new Date().toISOString(),
          });
          break;
        case "critical_error":
          console.error("Critical server error:", message.message);
          setError({
            type: "CRITICAL_ERROR",
            message: message.message,
            timestamp: new Date().toISOString(),
          });
          // Critical errors may require reconnection
          if (message.metadata?.requires_reconnection) {
            disconnect();
            setTimeout(() => connect(), 2000);
          }
          break;
        default:
          // Regular message, already handled above
          break;
      }
    } catch (err) {
      console.error(
        "Error parsing WebSocket message:",
        err,
        "Raw data:",
        event.data
      );
      setError({
        type: "MESSAGE_PARSE_ERROR",
        message: "Invalid message format received",
        timestamp: new Date().toISOString(),
      });
    }
  }, []);

  /**
   * Handle WebSocket connection open
   */
  const handleOpen = useCallback(() => {
    console.log("WebSocket connected successfully");
    setConnectionState("connected");
    setError(null);
    reconnectAttemptsRef.current = 0;
    connectionStartTimeRef.current = Date.now();

    setStats((prev) => ({
      ...prev,
      reconnectAttempts: 0,
      lastConnectedAt: new Date().toISOString(),
    }));

    // Start health check
    if (config.healthCheckInterval > 0) {
      healthCheckIntervalRef.current = setInterval(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          sendMessage({
            type: "ping",
            timestamp: new Date().toISOString(),
          });
        }
      }, config.healthCheckInterval);
    }

    // Update connection uptime
    const uptimeInterval = setInterval(() => {
      if (connectionStartTimeRef.current) {
        setStats((prev) => ({
          ...prev,
          connectionUptime: Date.now() - connectionStartTimeRef.current,
        }));
      }
    }, 1000);

    // Store interval ref for cleanup
    wsRef.current.uptimeInterval = uptimeInterval;
  }, [config.healthCheckInterval]);

  /**
   * Handle WebSocket connection close
   */
  const handleClose = useCallback(
    (event) => {
      console.log("WebSocket closed:", event.code, event.reason);
      setConnectionState("disconnected");
      connectionStartTimeRef.current = null;

      // Clear health check interval
      if (healthCheckIntervalRef.current) {
        clearInterval(healthCheckIntervalRef.current);
        healthCheckIntervalRef.current = null;
      }

      // Clear uptime interval
      if (wsRef.current?.uptimeInterval) {
        clearInterval(wsRef.current.uptimeInterval);
      }

      // Determine close reason and handle reconnection
      let shouldReconnect = false;
      let errorMessage = "";

      switch (event.code) {
        case 1000: // Normal closure
        case 1001: // Going away
          // Don't reconnect for normal closures
          break;
        case 1006: // Abnormal closure
          errorMessage =
            "Connection lost unexpectedly. The server may be unavailable.";
          shouldReconnect = true;
          break;
        case 1011: // Server error
          errorMessage =
            "Server encountered an error while processing the connection.";
          shouldReconnect = true;
          break;
        case 1012: // Service restart
          errorMessage = "Server is restarting. Please wait and try again.";
          shouldReconnect = true;
          break;
        default:
          errorMessage = `Connection closed with code ${event.code}: ${
            event.reason || "Unknown reason"
          }`;
          shouldReconnect = event.code !== 1000;
      }

      if (errorMessage) {
        setError({
          type: "CONNECTION_CLOSED",
          message: errorMessage,
          code: event.code,
          timestamp: new Date().toISOString(),
        });
      }

      // Attempt reconnection if needed and auto-reconnect is enabled
      if (
        shouldReconnect &&
        config.autoConnect &&
        reconnectAttemptsRef.current < config.maxReconnectAttempts
      ) {
        scheduleReconnect();
      } else if (reconnectAttemptsRef.current >= config.maxReconnectAttempts) {
        setConnectionState("error");
        setError({
          type: "MAX_RECONNECT_ATTEMPTS",
          message: `Max reconnection attempts (${config.maxReconnectAttempts}) reached. ${errorMessage}`,
          timestamp: new Date().toISOString(),
        });
      }
    },
    [config.autoConnect, config.maxReconnectAttempts]
  );

  /**
   * Handle WebSocket errors
   */
  const handleError = useCallback((event) => {
    console.error("WebSocket error:", event);

    let errorMessage = "WebSocket connection error";

    // Provide more specific error messages when possible
    if (wsRef.current?.readyState === WebSocket.CONNECTING) {
      errorMessage =
        "Failed to connect to server. Please check if the backend is running.";
    } else if (wsRef.current?.readyState === WebSocket.OPEN) {
      errorMessage =
        "Connection error during communication. The connection may be unstable.";
    }

    setError({
      type: "CONNECTION_ERROR",
      message: errorMessage,
      timestamp: new Date().toISOString(),
    });
    setConnectionState("error");
  }, []);

  /**
   * Schedule reconnection attempt
   */
  const scheduleReconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    const delay = Math.min(
      config.initialReconnectDelay * Math.pow(2, reconnectAttemptsRef.current),
      config.maxReconnectDelay
    );

    reconnectAttemptsRef.current++;

    setStats((prev) => ({
      ...prev,
      reconnectAttempts: reconnectAttemptsRef.current,
    }));

    console.log(
      `Scheduling reconnection attempt ${reconnectAttemptsRef.current} in ${delay}ms`
    );

    reconnectTimeoutRef.current = setTimeout(() => {
      connect();
    }, delay);
  }, [config.initialReconnectDelay, config.maxReconnectDelay]);

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(() => {
    if (!url) {
      setError({
        type: "INVALID_URL",
        message: "WebSocket URL is required",
        timestamp: new Date().toISOString(),
      });
      return false;
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.warn("WebSocket already connected");
      return true;
    }

    // Clear any existing reconnection timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    setConnectionState("connecting");
    setError(null);

    try {
      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = handleOpen;
      wsRef.current.onmessage = handleMessage;
      wsRef.current.onclose = handleClose;
      wsRef.current.onerror = handleError;

      return true;
    } catch (err) {
      console.error("Error creating WebSocket:", err);
      setError({
        type: "CONNECTION_CREATION_ERROR",
        message: `Failed to create WebSocket connection: ${err.message}`,
        timestamp: new Date().toISOString(),
      });
      setConnectionState("error");
      return false;
    }
  }, [url, handleOpen, handleMessage, handleClose, handleError]);

  /**
   * Disconnect WebSocket
   */
  const disconnect = useCallback(() => {
    // Clear reconnection timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Clear health check interval
    if (healthCheckIntervalRef.current) {
      clearInterval(healthCheckIntervalRef.current);
      healthCheckIntervalRef.current = null;
    }

    // Close WebSocket connection
    if (wsRef.current) {
      // Clear uptime interval
      if (wsRef.current.uptimeInterval) {
        clearInterval(wsRef.current.uptimeInterval);
      }

      wsRef.current.close(1000, "Normal closure");
      wsRef.current = null;
    }

    setConnectionState("disconnected");
    reconnectAttemptsRef.current = 0;
    connectionStartTimeRef.current = null;

    setStats((prev) => ({
      ...prev,
      connectionUptime: 0,
    }));
  }, []);

  /**
   * Send message through WebSocket
   */
  const sendMessage = useCallback(
    (message, options = {}) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        console.warn("WebSocket not connected, cannot send message");
        return false;
      }

      // Apply throttling if specified
      if (options.throttle !== false && config.frameThrottleMs > 0) {
        const now = Date.now();
        if (now - lastMessageSentRef.current < config.frameThrottleMs) {
          return false; // Skip this message due to throttling
        }
        lastMessageSentRef.current = now;
      }

      try {
        const messageStr =
          typeof message === "string" ? message : JSON.stringify(message);
        wsRef.current.send(messageStr);

        setStats((prev) => ({
          ...prev,
          messagesSent: prev.messagesSent + 1,
        }));

        return true;
      } catch (err) {
        console.error("Error sending message:", err);
        setError({
          type: "MESSAGE_SEND_ERROR",
          message: `Failed to send message: ${err.message}`,
          timestamp: new Date().toISOString(),
        });
        return false;
      }
    },
    [config.frameThrottleMs]
  );

  /**
   * Add message listener for specific message types
   */
  const addMessageListener = useCallback((messageType, listener) => {
    messageListenersRef.current.set(messageType, listener);

    // Return cleanup function
    return () => {
      messageListenersRef.current.delete(messageType);
    };
  }, []);

  /**
   * Remove message listener
   */
  const removeMessageListener = useCallback((messageType) => {
    messageListenersRef.current.delete(messageType);
  }, []);

  /**
   * Clear message history
   */
  const clearMessageHistory = useCallback(() => {
    setMessageHistory([]);
  }, []);

  /**
   * Reset connection stats
   */
  const resetStats = useCallback(() => {
    setStats({
      messagesSent: 0,
      messagesReceived: 0,
      reconnectAttempts: 0,
      connectionUptime: 0,
      lastConnectedAt: null,
    });
  }, []);

  /**
   * Force reconnection
   */
  const reconnect = useCallback(() => {
    disconnect();
    setTimeout(() => {
      reconnectAttemptsRef.current = 0;
      connect();
    }, 100);
  }, [disconnect, connect]);

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (config.autoConnect && url) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [url, config.autoConnect, connect, disconnect]);

  // Return hook interface
  return {
    // Connection state
    connectionState,
    isConnected: connectionState === "connected",
    isConnecting: connectionState === "connecting",
    isDisconnected: connectionState === "disconnected",
    hasError: connectionState === "error",

    // Messages
    lastMessage,
    messageHistory,

    // Error handling
    error,

    // Statistics
    stats,

    // Actions
    connect,
    disconnect,
    reconnect,
    sendMessage,
    addMessageListener,
    removeMessageListener,
    clearMessageHistory,
    resetStats,

    // WebSocket reference (for advanced usage)
    wsRef: wsRef.current,
  };
};

export default useWebSocket;
