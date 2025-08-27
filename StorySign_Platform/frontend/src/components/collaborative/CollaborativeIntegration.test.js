/**
 * Integration tests for collaborative features
 * Tests integration with ASL World and other platform components
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import CollaborativeSession from "./CollaborativeSession";
import SessionManager from "./SessionManager";

// Mock WebSocket
class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = WebSocket.CONNECTING;
    this.onopen = null;
    this.onmessage = null;
    this.onclose = null;
    this.onerror = null;

    // Simulate connection after a short delay
    setTimeout(() => {
      this.readyState = WebSocket.OPEN;
      if (this.onopen) {
        this.onopen();
      }

      // Send initial session state
      this.simulateMessage({
        type: "session_state",
        session_id: "test_session",
        state: {
          session_status: "waiting",
          participants: {
            user_123: {
              username: "TestUser",
              connected_at: new Date().toISOString(),
              status: "connected",
              current_sentence: 0,
              performance: {},
            },
          },
          current_sentence: 0,
          story_content: null,
          practice_data: {},
          chat_messages: [],
          peer_feedback: {},
        },
        your_user_id: "user_123",
      });
    }, 100);
  }

  send(data) {
    const message = JSON.parse(data);
    console.log("Mock WebSocket send:", message);

    // Simulate responses based on message type
    setTimeout(() => {
      if (message.type === "start_practice") {
        this.simulateMessage({
          type: "practice_started",
          story_content: message.story_content,
          started_by: "user_123",
          current_sentence: 0,
          timestamp: new Date().toISOString(),
        });
      } else if (message.type === "sentence_progress") {
        this.simulateMessage({
          type: "participant_progress",
          user_id: "user_123",
          sentence_index: message.sentence_index,
          performance: message.performance,
          timestamp: new Date().toISOString(),
        });
      } else if (message.type === "chat_message") {
        this.simulateMessage({
          type: "chat_message",
          from_user_id: "user_123",
          message: message.message,
          timestamp: new Date().toISOString(),
        });
      }
    }, 50);
  }

  close() {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) {
      this.onclose();
    }
  }

  simulateMessage(data) {
    if (this.onmessage) {
      this.onmessage({ data: JSON.stringify(data) });
    }
  }

  // Simulate another user joining
  simulateUserJoin(userId, username) {
    this.simulateMessage({
      type: "participant_joined",
      user_id: userId,
      username: username,
      timestamp: new Date().toISOString(),
      participant_count: 2,
    });
  }

  // Simulate peer feedback
  simulatePeerFeedback(fromUserId, message) {
    this.simulateMessage({
      type: "peer_feedback_received",
      from_user_id: fromUserId,
      feedback_type: "encouragement",
      message: message,
      sentence_index: 0,
      timestamp: new Date().toISOString(),
    });
  }
}

// Mock global WebSocket
global.WebSocket = MockWebSocket;

describe("CollaborativeSession Integration", () => {
  const defaultProps = {
    sessionId: "test_session",
    userId: "user_123",
    username: "TestUser",
    isHost: true,
    onSessionEnd: jest.fn(),
    storyContent: {
      title: "Test Story",
      sentences: [
        "Hello, my name is Sarah.",
        "I love learning sign language.",
        "Today is a beautiful day.",
        "Let's practice together!",
      ],
    },
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders collaborative session interface", async () => {
    render(<CollaborativeSession {...defaultProps} />);

    expect(screen.getByText("Collaborative Session")).toBeInTheDocument();
    expect(
      screen.getByText("Waiting for practice to begin...")
    ).toBeInTheDocument();

    // Wait for WebSocket connection
    await waitFor(() => {
      expect(screen.getByText("Connected")).toBeInTheDocument();
    });
  });

  test("host can start practice session", async () => {
    render(<CollaborativeSession {...defaultProps} />);

    // Wait for connection
    await waitFor(() => {
      expect(screen.getByText("Connected")).toBeInTheDocument();
    });

    // Start practice button should be available for host
    const startButton = screen.getByText("Start Practice");
    expect(startButton).toBeInTheDocument();

    fireEvent.click(startButton);

    // Should show practice interface after starting
    await waitFor(() => {
      expect(screen.getByText("Current Sentence (1 of 4)")).toBeInTheDocument();
      expect(screen.getByText("Hello, my name is Sarah.")).toBeInTheDocument();
    });
  });

  test("displays participants list", async () => {
    render(<CollaborativeSession {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("Participants (1)")).toBeInTheDocument();
      expect(screen.getByText("TestUser")).toBeInTheDocument();
      expect(screen.getByText("(You)")).toBeInTheDocument();
    });
  });

  test("handles chat functionality", async () => {
    render(<CollaborativeSession {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("Connected")).toBeInTheDocument();
    });

    // Find chat input and send button
    const chatInput = screen.getByPlaceholderText("Type a message...");
    const sendButton = screen.getByText("Send");

    // Type and send a message
    fireEvent.change(chatInput, { target: { value: "Hello everyone!" } });
    fireEvent.click(sendButton);

    // Message should appear in chat
    await waitFor(() => {
      expect(screen.getByText("Hello everyone!")).toBeInTheDocument();
    });

    // Input should be cleared
    expect(chatInput.value).toBe("");
  });

  test("handles peer feedback notifications", async () => {
    const mockWebSocket = new MockWebSocket("ws://test");
    render(<CollaborativeSession {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("Connected")).toBeInTheDocument();
    });

    // Simulate receiving peer feedback
    mockWebSocket.simulatePeerFeedback("user_456", "Great job! 👍");

    await waitFor(() => {
      expect(screen.getByText("Great job! 👍")).toBeInTheDocument();
    });
  });

  test("shows progress indicators for participants", async () => {
    render(<CollaborativeSession {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("Connected")).toBeInTheDocument();
    });

    // Start practice first
    fireEvent.click(screen.getByText("Start Practice"));

    await waitFor(() => {
      expect(screen.getByText("0/4")).toBeInTheDocument(); // Progress indicator
    });
  });

  test("non-host cannot start session", async () => {
    render(<CollaborativeSession {...defaultProps} isHost={false} />);

    await waitFor(() => {
      expect(screen.getByText("Connected")).toBeInTheDocument();
    });

    // Start button should not be available for non-host
    expect(screen.queryByText("Start Practice")).not.toBeInTheDocument();
    expect(
      screen.getByText("The host will start the practice session when ready.")
    ).toBeInTheDocument();
  });

  test("handles session end callback", async () => {
    const onSessionEnd = jest.fn();
    render(
      <CollaborativeSession {...defaultProps} onSessionEnd={onSessionEnd} />
    );

    await waitFor(() => {
      expect(screen.getByText("Connected")).toBeInTheDocument();
    });

    // Start practice
    fireEvent.click(screen.getByText("Start Practice"));

    await waitFor(() => {
      expect(screen.getByText("End Session")).toBeInTheDocument();
    });

    // End session
    fireEvent.click(screen.getByText("End Session"));

    // Should call onSessionEnd callback
    await waitFor(() => {
      expect(onSessionEnd).toHaveBeenCalled();
    });
  });
});

describe("SessionManager Integration", () => {
  const defaultProps = {
    userId: "user_123",
    username: "TestUser",
    groupId: "group_1",
  };

  test("renders session manager interface", () => {
    render(<SessionManager {...defaultProps} />);

    expect(screen.getByText("Collaborative Sessions")).toBeInTheDocument();
    expect(screen.getByText("Create Session")).toBeInTheDocument();
  });

  test("can navigate to create session form", () => {
    render(<SessionManager {...defaultProps} />);

    fireEvent.click(screen.getByText("Create Session"));

    expect(screen.getByText("Create New Session")).toBeInTheDocument();
    expect(screen.getByLabelText("Session Name *")).toBeInTheDocument();
  });

  test("displays session list", () => {
    render(<SessionManager {...defaultProps} />);

    expect(screen.getByText("Your Sessions")).toBeInTheDocument();
    // Mock sessions should be displayed
    expect(screen.getByText("Morning ASL Practice")).toBeInTheDocument();
    expect(screen.getByText("Advanced Storytelling")).toBeInTheDocument();
  });

  test("can join existing session", () => {
    render(<SessionManager {...defaultProps} />);

    // Find and click join button for scheduled session
    const joinButtons = screen.getAllByText("Join Session");
    expect(joinButtons.length).toBeGreaterThan(0);

    fireEvent.click(joinButtons[0]);

    // Should navigate to collaborative session
    expect(screen.getByText("Collaborative Session")).toBeInTheDocument();
  });

  test("host can start their own session", () => {
    render(<SessionManager {...defaultProps} />);

    // Find start button for host's session
    const startButton = screen.getByText("Start Session");
    expect(startButton).toBeInTheDocument();

    fireEvent.click(startButton);

    // Should navigate to collaborative session as host
    expect(screen.getByText("Collaborative Session")).toBeInTheDocument();
  });

  test("create session form validation", () => {
    render(<SessionManager {...defaultProps} />);

    fireEvent.click(screen.getByText("Create Session"));

    // Try to submit empty form
    fireEvent.click(screen.getByText("Create Session"));

    // Should show validation (form won't submit without required fields)
    expect(screen.getByText("Create New Session")).toBeInTheDocument();
  });

  test("create session form submission", () => {
    render(<SessionManager {...defaultProps} />);

    fireEvent.click(screen.getByText("Create Session"));

    // Fill out form
    fireEvent.change(screen.getByLabelText("Session Name *"), {
      target: { value: "Test Session" },
    });

    fireEvent.change(screen.getByLabelText("Description"), {
      target: { value: "Test description" },
    });

    // Submit form
    fireEvent.click(screen.getByText("Create Session"));

    // Should return to session list
    expect(screen.getByText("Your Sessions")).toBeInTheDocument();
  });
});

describe("Collaborative Features Integration with ASL World", () => {
  test("collaborative session integrates with story content", async () => {
    const storyContent = {
      title: "ASL World Story",
      sentences: [
        "Welcome to ASL World!",
        "Let's practice signing together.",
        "This is a collaborative session.",
        "Great job everyone!",
      ],
    };

    render(
      <CollaborativeSession
        sessionId="asl_world_session"
        userId="user_123"
        username="ASLLearner"
        isHost={true}
        storyContent={storyContent}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Connected")).toBeInTheDocument();
    });

    // Start practice with ASL World content
    fireEvent.click(screen.getByText("Start Practice"));

    await waitFor(() => {
      expect(screen.getByText("Welcome to ASL World!")).toBeInTheDocument();
      expect(screen.getByText("Current Sentence (1 of 4)")).toBeInTheDocument();
    });
  });

  test("progress tracking works with collaborative features", async () => {
    render(
      <CollaborativeSession
        sessionId="progress_session"
        userId="user_123"
        username="ProgressTracker"
        isHost={true}
        storyContent={{
          sentences: ["Test sentence 1", "Test sentence 2"],
        }}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Connected")).toBeInTheDocument();
    });

    // Start practice
    fireEvent.click(screen.getByText("Start Practice"));

    await waitFor(() => {
      expect(screen.getByText("0/2")).toBeInTheDocument(); // Initial progress
    });

    // Progress should be trackable and shareable with peers
    expect(screen.getByText("ProgressTracker")).toBeInTheDocument();
  });
});

describe("Error Handling and Edge Cases", () => {
  test("handles WebSocket connection failure gracefully", () => {
    // Mock WebSocket that fails to connect
    global.WebSocket = class FailingWebSocket {
      constructor() {
        setTimeout(() => {
          if (this.onerror) {
            this.onerror(new Error("Connection failed"));
          }
        }, 100);
      }
      send() {}
      close() {}
    };

    render(
      <CollaborativeSession
        sessionId="failing_session"
        userId="user_123"
        username="TestUser"
        isHost={true}
      />
    );

    // Should show disconnected state
    expect(screen.getByText("Disconnected")).toBeInTheDocument();
  });

  test("handles empty participant list", async () => {
    render(
      <CollaborativeSession
        sessionId="empty_session"
        userId="user_123"
        username="LoneUser"
        isHost={true}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Participants (1)")).toBeInTheDocument();
    });
  });

  test("handles missing story content", async () => {
    render(
      <CollaborativeSession
        sessionId="no_story_session"
        userId="user_123"
        username="TestUser"
        isHost={true}
        storyContent={null}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Connected")).toBeInTheDocument();
    });

    // Should show waiting state when no story content
    expect(
      screen.getByText("Waiting for practice to begin...")
    ).toBeInTheDocument();
  });
});
