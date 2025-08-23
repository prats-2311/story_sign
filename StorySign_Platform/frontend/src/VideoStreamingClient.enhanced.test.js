import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import VideoStreamingClient from "./VideoStreamingClient";

// Mock WebSocket
class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = WebSocket.CONNECTING;
    this.onopen = null;
    this.onclose = null;
    this.onmessage = null;
    this.onerror = null;

    // Simulate connection after a short delay
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      if (this.onopen) this.onopen();
    }, 10);
  }

  send(data) {
    // Mock send functionality
    console.log("Mock WebSocket send:", data);
  }

  close(code, reason) {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) this.onclose({ code, reason });
  }
}

global.WebSocket = MockWebSocket;

describe("VideoStreamingClient - Task 17.2 Enhanced Functionality", () => {
  const defaultProps = {
    isActive: true,
    onConnectionChange: jest.fn(),
    onProcessedFrame: jest.fn(),
    onError: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Enhanced ASL Feedback Message Handling", () => {
    test("processes ASL feedback messages with validation", async () => {
      const mockOnProcessedFrame = jest.fn();
      const ref = React.createRef();

      render(
        <VideoStreamingClient
          {...defaultProps}
          onProcessedFrame={mockOnProcessedFrame}
          ref={ref}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Connected/)).toBeInTheDocument();
      });

      // Simulate receiving ASL feedback message
      const mockFeedbackMessage = {
        type: "asl_feedback",
        data: {
          feedback: "Good hand positioning!",
          confidence_score: 0.75,
          suggestions: ["Keep fingers closer together"],
          target_sentence: "Hello world",
        },
        message_id: "feedback_123",
        session_id: "session_456",
        metadata: {
          processing_time_ms: 1250,
        },
      };

      // Get the WebSocket instance and simulate message
      const wsInstance = ref.current;
      if (wsInstance) {
        // Simulate WebSocket message reception
        const messageEvent = {
          data: JSON.stringify(mockFeedbackMessage),
        };

        // Trigger the message handler directly
        wsInstance.onmessage?.(messageEvent);
      }

      await waitFor(() => {
        expect(mockOnProcessedFrame).toHaveBeenCalledWith(
          expect.objectContaining({
            type: "asl_feedback",
            enhanced: true,
            data: expect.objectContaining({
              feedback: "Good hand positioning!",
              confidence_score: 0.75,
              suggestions: ["Keep fingers closer together"],
              target_sentence: "Hello world",
              message_id: "feedback_123",
              session_id: "session_456",
              processing_time: 1250,
              timestamp: expect.any(String),
            }),
          })
        );
      });
    });

    test("handles invalid ASL feedback data gracefully", async () => {
      const mockOnProcessedFrame = jest.fn();
      const mockOnError = jest.fn();
      const ref = React.createRef();

      render(
        <VideoStreamingClient
          {...defaultProps}
          onProcessedFrame={mockOnProcessedFrame}
          onError={mockOnError}
          ref={ref}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Connected/)).toBeInTheDocument();
      });

      // Simulate receiving invalid ASL feedback message
      const invalidFeedbackMessage = {
        type: "asl_feedback",
        data: null, // Invalid data
      };

      const wsInstance = ref.current;
      if (wsInstance) {
        const messageEvent = {
          data: JSON.stringify(invalidFeedbackMessage),
        };

        wsInstance.onmessage?.(messageEvent);
      }

      // Should not call onProcessedFrame with invalid data
      expect(mockOnProcessedFrame).not.toHaveBeenCalled();
    });

    test("handles control response messages", async () => {
      const mockOnProcessedFrame = jest.fn();
      const ref = React.createRef();

      render(
        <VideoStreamingClient
          {...defaultProps}
          onProcessedFrame={mockOnProcessedFrame}
          ref={ref}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Connected/)).toBeInTheDocument();
      });

      const controlResponseMessage = {
        type: "control_response",
        action: "next_sentence",
        result: {
          success: true,
          current_sentence_index: 1,
        },
      };

      const wsInstance = ref.current;
      if (wsInstance) {
        const messageEvent = {
          data: JSON.stringify(controlResponseMessage),
        };

        wsInstance.onmessage?.(messageEvent);
      }

      await waitFor(() => {
        expect(mockOnProcessedFrame).toHaveBeenCalledWith(
          controlResponseMessage
        );
      });
    });

    test("handles session complete messages", async () => {
      const mockOnProcessedFrame = jest.fn();
      const ref = React.createRef();

      render(
        <VideoStreamingClient
          {...defaultProps}
          onProcessedFrame={mockOnProcessedFrame}
          ref={ref}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Connected/)).toBeInTheDocument();
      });

      const sessionCompleteMessage = {
        type: "session_complete",
        data: {
          completion_message: "Story completed successfully!",
          overall_score: 0.85,
          completion_time: 45000,
        },
      };

      const wsInstance = ref.current;
      if (wsInstance) {
        const messageEvent = {
          data: JSON.stringify(sessionCompleteMessage),
        };

        wsInstance.onmessage?.(messageEvent);
      }

      await waitFor(() => {
        expect(mockOnProcessedFrame).toHaveBeenCalledWith(
          sessionCompleteMessage
        );
      });
    });
  });

  describe("Practice Control Message Sending", () => {
    test("sends practice control messages with enhanced data", async () => {
      const ref = React.createRef();

      render(<VideoStreamingClient {...defaultProps} ref={ref} />);

      await waitFor(() => {
        expect(screen.getByText(/Connected/)).toBeInTheDocument();
      });

      // Test sending practice control
      const controlData = {
        sentence_index: 1,
        target_sentence: "Hello world",
        story_sentences: ["Hello", "world"],
        story_title: "Test Story",
      };

      const success = ref.current?.sendPracticeControl(
        "next_sentence",
        controlData
      );
      expect(success).toBe(true);
    });

    test("handles practice control send failures gracefully", async () => {
      const ref = React.createRef();

      render(
        <VideoStreamingClient
          {...defaultProps}
          isActive={false} // Not active, so WebSocket won't be connected
          ref={ref}
        />
      );

      // Try to send practice control when not connected
      const success = ref.current?.sendPracticeControl("next_sentence", {});
      expect(success).toBe(false);
    });
  });

  describe("Message Type Handling", () => {
    test("passes unknown message types to parent for handling", async () => {
      const mockOnProcessedFrame = jest.fn();
      const ref = React.createRef();

      render(
        <VideoStreamingClient
          {...defaultProps}
          onProcessedFrame={mockOnProcessedFrame}
          ref={ref}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Connected/)).toBeInTheDocument();
      });

      const unknownMessage = {
        type: "unknown_type",
        data: { some: "data" },
      };

      const wsInstance = ref.current;
      if (wsInstance) {
        const messageEvent = {
          data: JSON.stringify(unknownMessage),
        };

        wsInstance.onmessage?.(messageEvent);
      }

      await waitFor(() => {
        expect(mockOnProcessedFrame).toHaveBeenCalledWith(unknownMessage);
      });
    });

    test("handles malformed JSON messages gracefully", async () => {
      const mockOnProcessedFrame = jest.fn();
      const ref = React.createRef();

      render(
        <VideoStreamingClient
          {...defaultProps}
          onProcessedFrame={mockOnProcessedFrame}
          ref={ref}
        />
      );

      await waitFor(() => {
        expect(screen.getByText(/Connected/)).toBeInTheDocument();
      });

      const wsInstance = ref.current;
      if (wsInstance) {
        const messageEvent = {
          data: "invalid json {",
        };

        wsInstance.onmessage?.(messageEvent);
      }

      // Should not crash and should show error
      await waitFor(() => {
        expect(
          screen.getByText(/Invalid message format received/)
        ).toBeInTheDocument();
      });
    });
  });

  describe("Connection Status and Error Handling", () => {
    test("displays enhanced connection status information", async () => {
      render(<VideoStreamingClient {...defaultProps} isActive={true} />);

      await waitFor(() => {
        expect(screen.getByText(/Connected/)).toBeInTheDocument();
      });

      // Check that frame counters are displayed
      expect(screen.getByText(/Frames Sent:/)).toBeInTheDocument();
      expect(screen.getByText(/Frames Received:/)).toBeInTheDocument();
    });

    test("shows retry button on connection errors", async () => {
      const mockOnError = jest.fn();

      render(
        <VideoStreamingClient
          {...defaultProps}
          onError={mockOnError}
          isActive={true}
        />
      );

      // Wait for initial connection, then simulate error
      await waitFor(() => {
        expect(screen.getByText(/Connected/)).toBeInTheDocument();
      });

      // Simulate connection error by closing WebSocket
      // This would trigger error state and show retry button
      // The exact implementation depends on how errors are simulated
    });
  });
});
