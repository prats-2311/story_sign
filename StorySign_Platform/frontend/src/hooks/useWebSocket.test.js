/**
 * Unit tests for useWebSocket hook
 */

import { renderHook, act } from "@testing-library/react";
import useWebSocket from "./useWebSocket";

// Mock WebSocket
class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = WebSocket.CONNECTING;
    this.onopen = null;
    this.onmessage = null;
    this.onclose = null;
    this.onerror = null;

    // Simulate async connection
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      if (this.onopen) {
        this.onopen();
      }
    }, 10);
  }

  send(data) {
    if (this.readyState !== WebSocket.OPEN) {
      throw new Error("WebSocket is not open");
    }
    // Store sent data for testing
    this.lastSentData = data;
  }

  close(code = 1000, reason = "") {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) {
      this.onclose({ code, reason });
    }
  }

  // Simulate receiving a message
  simulateMessage(data) {
    if (this.onmessage) {
      this.onmessage({ data: JSON.stringify(data) });
    }
  }

  // Simulate an error
  simulateError() {
    if (this.onerror) {
      this.onerror(new Event("error"));
    }
  }
}

// Mock WebSocket constants
Object.defineProperty(window, "WebSocket", {
  writable: true,
  value: MockWebSocket,
});

WebSocket.CONNECTING = 0;
WebSocket.OPEN = 1;
WebSocket.CLOSING = 2;
WebSocket.CLOSED = 3;

// Mock timers
jest.useFakeTimers();

describe("useWebSocket Hook", () => {
  const mockUrl = "ws://localhost:8000/test";

  beforeEach(() => {
    jest.clearAllMocks();
    jest.clearAllTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
  });

  describe("Initial State", () => {
    test("should initialize with correct default state", () => {
      const { result } = renderHook(() =>
        useWebSocket(mockUrl, { autoConnect: false })
      );

      expect(result.current.connectionState).toBe("disconnected");
      expect(result.current.isConnected).toBe(false);
      expect(result.current.isConnecting).toBe(false);
      expect(result.current.isDisconnected).toBe(true);
      expect(result.current.hasError).toBe(false);
      expect(result.current.lastMessage).toBeNull();
      expect(result.current.messageHistory).toEqual([]);
      expect(result.current.error).toBeNull();
      expect(result.current.stats).toEqual({
        messagesSent: 0,
        messagesReceived: 0,
        reconnectAttempts: 0,
        connectionUptime: 0,
        lastConnectedAt: null,
      });
    });
  });

  describe("Connection Management", () => {
    test("should connect successfully", async () => {
      const { result } = renderHook(() =>
        useWebSocket(mockUrl, { autoConnect: false })
      );

      act(() => {
        result.current.connect();
      });

      expect(result.current.connectionState).toBe("connecting");
      expect(result.current.isConnecting).toBe(true);

      // Wait for connection to complete
      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      expect(result.current.connectionState).toBe("connected");
      expect(result.current.isConnected).toBe(true);
      expect(result.current.stats.lastConnectedAt).toBeTruthy();
    });

    test("should auto-connect when autoConnect is true", async () => {
      const { result } = renderHook(() =>
        useWebSocket(mockUrl, { autoConnect: true })
      );

      expect(result.current.connectionState).toBe("connecting");

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      expect(result.current.connectionState).toBe("connected");
    });

    test("should disconnect properly", async () => {
      const { result } = renderHook(() =>
        useWebSocket(mockUrl, { autoConnect: false })
      );

      // Connect first
      act(() => {
        result.current.connect();
      });

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      expect(result.current.isConnected).toBe(true);

      // Disconnect
      act(() => {
        result.current.disconnect();
      });

      expect(result.current.connectionState).toBe("disconnected");
      expect(result.current.isDisconnected).toBe(true);
    });

    test("should handle connection errors", () => {
      const { result } = renderHook(() =>
        useWebSocket(mockUrl, { autoConnect: false })
      );

      act(() => {
        result.current.connect();
      });

      // Simulate error
      act(() => {
        result.current.wsRef.simulateError();
      });

      expect(result.current.connectionState).toBe("error");
      expect(result.current.hasError).toBe(true);
      expect(result.current.error).toEqual({
        type: "CONNECTION_ERROR",
        message: expect.any(String),
        timestamp: expect.any(String),
      });
    });

    test("should handle invalid URL", () => {
      const { result } = renderHook(() =>
        useWebSocket("", { autoConnect: false })
      );

      act(() => {
        const success = result.current.connect();
        expect(success).toBe(false);
      });

      expect(result.current.error).toEqual({
        type: "INVALID_URL",
        message: "WebSocket URL is required",
        timestamp: expect.any(String),
      });
    });
  });

  describe("Message Handling", () => {
    test("should send messages successfully", async () => {
      const { result } = renderHook(() =>
        useWebSocket(mockUrl, { autoConnect: false })
      );

      // Connect first
      act(() => {
        result.current.connect();
      });

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      const testMessage = { type: "test", data: "hello" };

      act(() => {
        const success = result.current.sendMessage(testMessage);
        expect(success).toBe(true);
      });

      expect(result.current.stats.messagesSent).toBe(1);
      expect(result.current.wsRef.lastSentData).toBe(
        JSON.stringify(testMessage)
      );
    });

    test("should fail to send messages when not connected", () => {
      const { result } = renderHook(() =>
        useWebSocket(mockUrl, { autoConnect: false })
      );

      const testMessage = { type: "test", data: "hello" };

      act(() => {
        const success = result.current.sendMessage(testMessage);
        expect(success).toBe(false);
      });

      expect(result.current.stats.messagesSent).toBe(0);
    });

    test("should receive and parse messages", async () => {
      const { result } = renderHook(() =>
        useWebSocket(mockUrl, { autoConnect: false })
      );

      // Connect first
      act(() => {
        result.current.connect();
      });

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      const testMessage = { type: "test_response", data: "world" };

      act(() => {
        result.current.wsRef.simulateMessage(testMessage);
      });

      expect(result.current.lastMessage).toEqual(testMessage);
      expect(result.current.messageHistory).toHaveLength(1);
      expect(result.current.messageHistory[0]).toEqual({
        ...testMessage,
        receivedAt: expect.any(String),
      });
      expect(result.current.stats.messagesReceived).toBe(1);
    });

    test("should handle message parsing errors", async () => {
      const { result } = renderHook(() =>
        useWebSocket(mockUrl, { autoConnect: false })
      );

      // Connect first
      act(() => {
        result.current.connect();
      });

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      // Simulate invalid JSON message
      act(() => {
        if (result.current.wsRef.onmessage) {
          result.current.wsRef.onmessage({ data: "invalid json" });
        }
      });

      expect(result.current.error).toEqual({
        type: "MESSAGE_PARSE_ERROR",
        message: "Invalid message format received",
        timestamp: expect.any(String),
      });
    });

    test("should handle server error messages", async () => {
      const { result } = renderHook(() =>
        useWebSocket(mockUrl, { autoConnect: false })
      );

      // Connect first
      act(() => {
        result.current.connect();
      });

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      const errorMessage = { type: "error", message: "Server error occurred" };

      act(() => {
        result.current.wsRef.simulateMessage(errorMessage);
      });

      expect(result.current.error).toEqual({
        type: "SERVER_ERROR",
        message: "Server error occurred",
        timestamp: expect.any(String),
      });
    });
  });

  describe("Message Listeners", () => {
    test("should add and call message listeners", async () => {
      const { result } = renderHook(() =>
        useWebSocket(mockUrl, { autoConnect: false })
      );
      const mockListener = jest.fn();

      // Add listener
      act(() => {
        result.current.addMessageListener("test_type", mockListener);
      });

      // Connect
      act(() => {
        result.current.connect();
      });

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      const testMessage = { type: "test_type", data: "test" };

      act(() => {
        result.current.wsRef.simulateMessage(testMessage);
      });

      expect(mockListener).toHaveBeenCalledWith(testMessage);
    });

    test("should remove message listeners", async () => {
      const { result } = renderHook(() =>
        useWebSocket(mockUrl, { autoConnect: false })
      );
      const mockListener = jest.fn();

      // Add and remove listener
      act(() => {
        result.current.addMessageListener("test_type", mockListener);
        result.current.removeMessageListener("test_type");
      });

      // Connect
      act(() => {
        result.current.connect();
      });

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      const testMessage = { type: "test_type", data: "test" };

      act(() => {
        result.current.wsRef.simulateMessage(testMessage);
      });

      expect(mockListener).not.toHaveBeenCalled();
    });

    test("should handle wildcard listeners", async () => {
      const { result } = renderHook(() =>
        useWebSocket(mockUrl, { autoConnect: false })
      );
      const mockListener = jest.fn();

      // Add wildcard listener
      act(() => {
        result.current.addMessageListener("*", mockListener);
      });

      // Connect
      act(() => {
        result.current.connect();
      });

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      const testMessage = { type: "any_type", data: "test" };

      act(() => {
        result.current.wsRef.simulateMessage(testMessage);
      });

      expect(mockListener).toHaveBeenCalledWith(testMessage);
    });
  });

  describe("Reconnection Logic", () => {
    test("should attempt reconnection on abnormal closure", async () => {
      const { result } = renderHook(() =>
        useWebSocket(mockUrl, {
          autoConnect: false,
          maxReconnectAttempts: 2,
          initialReconnectDelay: 100,
        })
      );

      // Connect first
      act(() => {
        result.current.connect();
      });

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      expect(result.current.isConnected).toBe(true);

      // Simulate abnormal closure
      act(() => {
        result.current.wsRef.close(1006, "Connection lost");
      });

      expect(result.current.connectionState).toBe("disconnected");
      expect(result.current.stats.reconnectAttempts).toBe(1);

      // Wait for reconnection attempt
      await act(async () => {
        jest.advanceTimersByTime(150);
      });

      expect(result.current.connectionState).toBe("connecting");
    });

    test("should not reconnect on normal closure", async () => {
      const { result } = renderHook(() =>
        useWebSocket(mockUrl, { autoConnect: false })
      );

      // Connect first
      act(() => {
        result.current.connect();
      });

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      // Simulate normal closure
      act(() => {
        result.current.wsRef.close(1000, "Normal closure");
      });

      expect(result.current.connectionState).toBe("disconnected");
      expect(result.current.stats.reconnectAttempts).toBe(0);

      // Wait to ensure no reconnection attempt
      await act(async () => {
        jest.advanceTimersByTime(1000);
      });

      expect(result.current.connectionState).toBe("disconnected");
    });

    test("should stop reconnecting after max attempts", async () => {
      const { result } = renderHook(() =>
        useWebSocket(mockUrl, {
          autoConnect: false,
          maxReconnectAttempts: 1,
          initialReconnectDelay: 100,
        })
      );

      // Connect first
      act(() => {
        result.current.connect();
      });

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      // Simulate abnormal closure twice
      act(() => {
        result.current.wsRef.close(1006, "Connection lost");
      });

      await act(async () => {
        jest.advanceTimersByTime(150);
      });

      // Second failure
      act(() => {
        result.current.wsRef.close(1006, "Connection lost again");
      });

      await act(async () => {
        jest.advanceTimersByTime(300);
      });

      expect(result.current.connectionState).toBe("error");
      expect(result.current.error.type).toBe("MAX_RECONNECT_ATTEMPTS");
    });

    test("should force reconnect", async () => {
      const { result } = renderHook(() =>
        useWebSocket(mockUrl, { autoConnect: false })
      );

      // Connect first
      act(() => {
        result.current.connect();
      });

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      expect(result.current.isConnected).toBe(true);

      // Force reconnect
      act(() => {
        result.current.reconnect();
      });

      expect(result.current.connectionState).toBe("disconnected");

      await act(async () => {
        jest.advanceTimersByTime(150);
      });

      expect(result.current.connectionState).toBe("connected");
    });
  });

  describe("Utility Functions", () => {
    test("should clear message history", async () => {
      const { result } = renderHook(() =>
        useWebSocket(mockUrl, { autoConnect: false })
      );

      // Connect and receive messages
      act(() => {
        result.current.connect();
      });

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      act(() => {
        result.current.wsRef.simulateMessage({ type: "test1", data: "data1" });
        result.current.wsRef.simulateMessage({ type: "test2", data: "data2" });
      });

      expect(result.current.messageHistory).toHaveLength(2);

      act(() => {
        result.current.clearMessageHistory();
      });

      expect(result.current.messageHistory).toHaveLength(0);
    });

    test("should reset stats", () => {
      const { result } = renderHook(() =>
        useWebSocket(mockUrl, { autoConnect: false })
      );

      // Modify stats
      act(() => {
        result.current.resetStats();
      });

      expect(result.current.stats).toEqual({
        messagesSent: 0,
        messagesReceived: 0,
        reconnectAttempts: 0,
        connectionUptime: 0,
        lastConnectedAt: null,
      });
    });
  });

  describe("Throttling", () => {
    test("should throttle messages when enabled", async () => {
      const { result } = renderHook(() =>
        useWebSocket(mockUrl, {
          autoConnect: false,
          frameThrottleMs: 100,
        })
      );

      // Connect first
      act(() => {
        result.current.connect();
      });

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      // Send multiple messages quickly
      act(() => {
        const success1 = result.current.sendMessage({ type: "test1" });
        const success2 = result.current.sendMessage({ type: "test2" });

        expect(success1).toBe(true);
        expect(success2).toBe(false); // Should be throttled
      });

      expect(result.current.stats.messagesSent).toBe(1);
    });

    test("should bypass throttling when disabled", async () => {
      const { result } = renderHook(() =>
        useWebSocket(mockUrl, {
          autoConnect: false,
          frameThrottleMs: 100,
        })
      );

      // Connect first
      act(() => {
        result.current.connect();
      });

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      // Send messages with throttle disabled
      act(() => {
        const success1 = result.current.sendMessage(
          { type: "test1" },
          { throttle: false }
        );
        const success2 = result.current.sendMessage(
          { type: "test2" },
          { throttle: false }
        );

        expect(success1).toBe(true);
        expect(success2).toBe(true);
      });

      expect(result.current.stats.messagesSent).toBe(2);
    });
  });

  describe("Cleanup", () => {
    test("should cleanup on unmount", async () => {
      const { result, unmount } = renderHook(() =>
        useWebSocket(mockUrl, { autoConnect: false })
      );

      // Connect first
      act(() => {
        result.current.connect();
      });

      await act(async () => {
        jest.advanceTimersByTime(20);
      });

      expect(result.current.isConnected).toBe(true);

      // Unmount
      unmount();

      // Connection should be closed
      expect(result.current.connectionState).toBe("disconnected");
    });
  });
});
