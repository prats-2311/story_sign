/**
 * CollaborativeSession Component
 * Manages real-time collaborative practice sessions with multiple users
 */

import React, { useState, useEffect, useRef, useCallback } from "react";
import "./CollaborativeSession.css";

const CollaborativeSession = ({
  sessionId,
  userId,
  username,
  isHost = false,
  onSessionEnd,
  storyContent = null,
}) => {
  // WebSocket connection
  const [ws, setWs] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState("disconnected");

  // Session state
  const [sessionState, setSessionState] = useState({
    session_status: "waiting",
    participants: {},
    current_sentence: 0,
    story_content: null,
    practice_data: {},
    chat_messages: [],
    peer_feedback: {},
  });

  // UI state
  const [participants, setParticipants] = useState([]);
  const [chatMessages, setChatMessages] = useState([]);
  const [newChatMessage, setNewChatMessage] = useState("");
  const [showChat, setShowChat] = useState(true);
  const [showParticipants, setShowParticipants] = useState(true);
  const [peerFeedback, setPeerFeedback] = useState([]);

  // Practice state
  const [currentSentence, setCurrentSentence] = useState(0);
  const [userProgress, setUserProgress] = useState({});
  const [practiceActive, setPracticeActive] = useState(false);

  // Refs
  const wsRef = useRef(null);
  const chatContainerRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  // WebSocket connection management
  const connectWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${
      window.location.host
    }/api/ws/collaborative/${sessionId}?user_id=${userId}&username=${encodeURIComponent(
      username
    )}`;

    console.log("Connecting to collaborative WebSocket:", wsUrl);

    const websocket = new WebSocket(wsUrl);
    wsRef.current = websocket;

    websocket.onopen = () => {
      console.log("Connected to collaborative session");
      setConnectionStatus("connected");
      setWs(websocket);

      // Clear any reconnection timeout
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };

    websocket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
      }
    };

    websocket.onclose = (event) => {
      console.log("Collaborative WebSocket closed:", event.code, event.reason);
      setConnectionStatus("disconnected");
      setWs(null);

      // Attempt to reconnect after a delay
      if (!reconnectTimeoutRef.current) {
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log("Attempting to reconnect to collaborative session...");
          connectWebSocket();
        }, 3000);
      }
    };

    websocket.onerror = (error) => {
      console.error("Collaborative WebSocket error:", error);
      setConnectionStatus("error");
    };
  }, [sessionId, userId, username]);

  // Handle incoming WebSocket messages
  const handleWebSocketMessage = useCallback(
    (message) => {
      console.log("Received collaborative message:", message);

      switch (message.type) {
        case "session_state":
          setSessionState(message.state);
          setParticipants(
            Object.entries(message.state.participants).map(([id, data]) => ({
              user_id: id,
              ...data,
            }))
          );
          setChatMessages(message.state.chat_messages || []);
          setCurrentSentence(message.state.current_sentence || 0);
          break;

        case "participant_joined":
          setParticipants((prev) => {
            const existing = prev.find((p) => p.user_id === message.user_id);
            if (existing) return prev;

            return [
              ...prev,
              {
                user_id: message.user_id,
                username: message.username,
                connected_at: message.timestamp,
                status: "connected",
                current_sentence: 0,
                performance: {},
              },
            ];
          });

          // Add system message to chat
          setChatMessages((prev) => [
            ...prev,
            {
              type: "system",
              message: `${message.username} joined the session`,
              timestamp: message.timestamp,
            },
          ]);
          break;

        case "participant_left":
          setParticipants((prev) =>
            prev.filter((p) => p.user_id !== message.user_id)
          );

          // Add system message to chat
          setChatMessages((prev) => [
            ...prev,
            {
              type: "system",
              message: `${message.username} left the session`,
              timestamp: message.timestamp,
            },
          ]);
          break;

        case "practice_started":
          setSessionState((prev) => ({
            ...prev,
            session_status: "active",
            story_content: message.story_content,
            current_sentence: message.current_sentence,
          }));
          setCurrentSentence(message.current_sentence);
          setPracticeActive(true);
          break;

        case "participant_progress":
          setUserProgress((prev) => ({
            ...prev,
            [message.user_id]: {
              sentence_index: message.sentence_index,
              performance: message.performance,
              timestamp: message.timestamp,
            },
          }));

          // Update participant progress
          setParticipants((prev) =>
            prev.map((p) =>
              p.user_id === message.user_id
                ? {
                    ...p,
                    current_sentence: message.sentence_index,
                    performance: message.performance,
                  }
                : p
            )
          );
          break;

        case "peer_gesture_analysis":
          // Handle peer gesture analysis sharing
          console.log(
            "Peer gesture analysis from",
            message.from_user_id,
            ":",
            message.analysis
          );
          break;

        case "peer_feedback_received":
          setPeerFeedback((prev) => [
            ...prev,
            {
              id: Date.now(),
              from_user_id: message.from_user_id,
              feedback_type: message.feedback_type,
              message: message.message,
              sentence_index: message.sentence_index,
              timestamp: message.timestamp,
            },
          ]);
          break;

        case "peer_feedback_shared":
          // Show public peer feedback
          setChatMessages((prev) => [
            ...prev,
            {
              type: "peer_feedback",
              from_user_id: message.from_user_id,
              target_user_id: message.target_user_id,
              feedback_type: message.feedback_type,
              message: message.message,
              timestamp: message.timestamp,
            },
          ]);
          break;

        case "chat_message":
          setChatMessages((prev) => [
            ...prev,
            {
              type: "chat",
              from_user_id: message.from_user_id,
              message: message.message,
              timestamp: message.timestamp,
            },
          ]);
          break;

        case "session_paused":
          setSessionState((prev) => ({ ...prev, session_status: "paused" }));
          setPracticeActive(false);
          break;

        case "session_resumed":
          setSessionState((prev) => ({ ...prev, session_status: "active" }));
          setPracticeActive(true);
          break;

        case "sentence_changed":
          setCurrentSentence(message.new_sentence_index);
          setSessionState((prev) => ({
            ...prev,
            current_sentence: message.new_sentence_index,
          }));
          break;

        case "session_ended":
          setSessionState((prev) => ({ ...prev, session_status: "completed" }));
          setPracticeActive(false);
          if (onSessionEnd) {
            onSessionEnd(message.final_state);
          }
          break;

        case "error":
          console.error("Collaborative session error:", message.message);
          break;

        default:
          console.log("Unknown collaborative message type:", message.type);
      }
    },
    [onSessionEnd]
  );

  // Send WebSocket message
  const sendMessage = useCallback(
    (message) => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(message));
      } else {
        console.warn("WebSocket not connected, cannot send message:", message);
      }
    },
    [ws]
  );

  // Session control functions
  const startPractice = useCallback(() => {
    if (!isHost || !storyContent) return;

    sendMessage({
      type: "start_practice",
      story_content: storyContent,
    });
  }, [isHost, storyContent, sendMessage]);

  const pauseSession = useCallback(() => {
    if (!isHost) return;

    sendMessage({
      type: "session_control",
      action: "pause_session",
    });
  }, [isHost, sendMessage]);

  const resumeSession = useCallback(() => {
    if (!isHost) return;

    sendMessage({
      type: "session_control",
      action: "resume_session",
    });
  }, [isHost, sendMessage]);

  const nextSentence = useCallback(() => {
    if (!isHost) return;

    sendMessage({
      type: "session_control",
      action: "next_sentence",
    });
  }, [isHost, sendMessage]);

  const endSession = useCallback(() => {
    if (!isHost) return;

    sendMessage({
      type: "session_control",
      action: "end_session",
    });
  }, [isHost, sendMessage]);

  // Report sentence progress
  const reportSentenceProgress = useCallback(
    (sentenceIndex, performanceData) => {
      sendMessage({
        type: "sentence_progress",
        sentence_index: sentenceIndex,
        performance: performanceData,
      });
    },
    [sendMessage]
  );

  // Send peer feedback
  const sendPeerFeedback = useCallback(
    (targetUserId, feedbackType, message) => {
      sendMessage({
        type: "peer_feedback",
        target_user_id: targetUserId,
        feedback_type: feedbackType,
        message: message,
        sentence_index: currentSentence,
      });
    },
    [sendMessage, currentSentence]
  );

  // Send chat message
  const sendChatMessage = useCallback(() => {
    if (!newChatMessage.trim()) return;

    sendMessage({
      type: "chat_message",
      message: newChatMessage.trim(),
    });

    setNewChatMessage("");
  }, [newChatMessage, sendMessage]);

  // Handle chat input
  const handleChatKeyPress = useCallback(
    (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
      }
    },
    [sendChatMessage]
  );

  // Auto-scroll chat to bottom
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop =
        chatContainerRef.current.scrollHeight;
    }
  }, [chatMessages]);

  // Initialize WebSocket connection
  useEffect(() => {
    connectWebSocket();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connectWebSocket]);

  // Format timestamp for display
  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  // Get participant username
  const getParticipantUsername = (userId) => {
    const participant = participants.find((p) => p.user_id === userId);
    return participant?.username || "Unknown User";
  };

  return (
    <div className="collaborative-session">
      {/* Header */}
      <div className="session-header">
        <div className="session-info">
          <h2>Collaborative Session</h2>
          <div className="connection-status">
            <span className={`status-indicator ${connectionStatus}`}></span>
            {connectionStatus === "connected" ? "Connected" : "Disconnected"}
          </div>
        </div>

        {/* Session Controls (Host only) */}
        {isHost && (
          <div className="session-controls">
            {sessionState.session_status === "waiting" && storyContent && (
              <button onClick={startPractice} className="btn-primary">
                Start Practice
              </button>
            )}

            {sessionState.session_status === "active" && (
              <>
                <button onClick={pauseSession} className="btn-secondary">
                  Pause
                </button>
                <button onClick={nextSentence} className="btn-secondary">
                  Next Sentence
                </button>
                <button onClick={endSession} className="btn-danger">
                  End Session
                </button>
              </>
            )}

            {sessionState.session_status === "paused" && (
              <button onClick={resumeSession} className="btn-primary">
                Resume
              </button>
            )}
          </div>
        )}
      </div>

      <div className="session-content">
        {/* Main Practice Area */}
        <div className="practice-area">
          {sessionState.story_content ? (
            <div className="story-practice">
              <div className="current-sentence">
                <h3>
                  Current Sentence ({currentSentence + 1} of{" "}
                  {sessionState.story_content.sentences?.length || 0})
                </h3>
                <p className="sentence-text">
                  {sessionState.story_content.sentences?.[currentSentence] ||
                    "Loading..."}
                </p>
              </div>

              {/* Practice status */}
              <div className="practice-status">
                <span className={`status ${sessionState.session_status}`}>
                  {sessionState.session_status.toUpperCase()}
                </span>
                {practiceActive && (
                  <p>Practice this sentence with your peers!</p>
                )}
              </div>

              {/* User progress indicators */}
              <div className="progress-indicators">
                {participants.map((participant) => (
                  <div
                    key={participant.user_id}
                    className="participant-progress"
                  >
                    <span className="username">{participant.username}</span>
                    <div className="progress-bar">
                      <div
                        className="progress-fill"
                        style={{
                          width: `${
                            ((participant.current_sentence || 0) /
                              (sessionState.story_content.sentences?.length ||
                                1)) *
                            100
                          }%`,
                        }}
                      ></div>
                    </div>
                    <span className="sentence-count">
                      {participant.current_sentence || 0}/
                      {sessionState.story_content.sentences?.length || 0}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="waiting-area">
              <h3>Waiting for practice to begin...</h3>
              <p>The host will start the practice session when ready.</p>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="session-sidebar">
          {/* Participants Panel */}
          {showParticipants && (
            <div className="participants-panel">
              <div className="panel-header">
                <h4>Participants ({participants.length})</h4>
                <button
                  onClick={() => setShowParticipants(false)}
                  className="btn-close"
                >
                  ×
                </button>
              </div>
              <div className="participants-list">
                {participants.map((participant) => (
                  <div key={participant.user_id} className="participant-item">
                    <div className="participant-info">
                      <span className="username">{participant.username}</span>
                      {participant.user_id === userId && (
                        <span className="you-label">(You)</span>
                      )}
                      {isHost && participant.user_id !== userId && (
                        <div className="feedback-buttons">
                          <button
                            onClick={() =>
                              sendPeerFeedback(
                                participant.user_id,
                                "encouragement",
                                "👍 Great job!"
                              )
                            }
                            className="btn-feedback encourage"
                            title="Send encouragement"
                          >
                            👍
                          </button>
                          <button
                            onClick={() =>
                              sendPeerFeedback(
                                participant.user_id,
                                "celebration",
                                "🎉 Awesome!"
                              )
                            }
                            className="btn-feedback celebrate"
                            title="Celebrate success"
                          >
                            🎉
                          </button>
                        </div>
                      )}
                    </div>
                    <div className="participant-status">
                      <span className={`status ${participant.status}`}>
                        {participant.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Chat Panel */}
          {showChat && (
            <div className="chat-panel">
              <div className="panel-header">
                <h4>Chat</h4>
                <button
                  onClick={() => setShowChat(false)}
                  className="btn-close"
                >
                  ×
                </button>
              </div>

              <div className="chat-messages" ref={chatContainerRef}>
                {chatMessages.map((msg, index) => (
                  <div key={index} className={`chat-message ${msg.type}`}>
                    {msg.type === "system" ? (
                      <div className="system-message">
                        <span className="message-text">{msg.message}</span>
                        <span className="timestamp">
                          {formatTimestamp(msg.timestamp)}
                        </span>
                      </div>
                    ) : msg.type === "peer_feedback" ? (
                      <div className="feedback-message">
                        <span className="feedback-text">
                          {getParticipantUsername(msg.from_user_id)} sent
                          feedback to{" "}
                          {getParticipantUsername(msg.target_user_id)}:{" "}
                          {msg.message}
                        </span>
                        <span className="timestamp">
                          {formatTimestamp(msg.timestamp)}
                        </span>
                      </div>
                    ) : (
                      <div className="user-message">
                        <div className="message-header">
                          <span className="username">
                            {getParticipantUsername(msg.from_user_id)}
                          </span>
                          <span className="timestamp">
                            {formatTimestamp(msg.timestamp)}
                          </span>
                        </div>
                        <div className="message-text">{msg.message}</div>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <div className="chat-input">
                <input
                  type="text"
                  value={newChatMessage}
                  onChange={(e) => setNewChatMessage(e.target.value)}
                  onKeyPress={handleChatKeyPress}
                  placeholder="Type a message..."
                  disabled={connectionStatus !== "connected"}
                />
                <button
                  onClick={sendChatMessage}
                  disabled={
                    !newChatMessage.trim() || connectionStatus !== "connected"
                  }
                  className="btn-send"
                >
                  Send
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Peer Feedback Notifications */}
      {peerFeedback.length > 0 && (
        <div className="feedback-notifications">
          {peerFeedback.slice(-3).map((feedback) => (
            <div
              key={feedback.id}
              className={`feedback-notification ${feedback.feedback_type}`}
            >
              <div className="feedback-content">
                <strong>{getParticipantUsername(feedback.from_user_id)}</strong>
                : {feedback.message}
              </div>
              <button
                onClick={() =>
                  setPeerFeedback((prev) =>
                    prev.filter((f) => f.id !== feedback.id)
                  )
                }
                className="btn-close-notification"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Sidebar Toggle Buttons */}
      <div className="sidebar-toggles">
        {!showParticipants && (
          <button
            onClick={() => setShowParticipants(true)}
            className="btn-toggle"
            title="Show Participants"
          >
            👥 ({participants.length})
          </button>
        )}
        {!showChat && (
          <button
            onClick={() => setShowChat(true)}
            className="btn-toggle"
            title="Show Chat"
          >
            💬
          </button>
        )}
      </div>
    </div>
  );
};

export default CollaborativeSession;
