/**
 * SessionManager Component
 * Handles creating, joining, and managing collaborative sessions
 */

import React, { useState, useEffect } from "react";
import CollaborativeSession from "./CollaborativeSession";
import "./SessionManager.css";

const SessionManager = ({
  userId = "user_123",
  username = "TestUser",
  groupId = null,
  onBack = null,
}) => {
  // State management
  const [currentView, setCurrentView] = useState("list"); // 'list', 'create', 'session'
  const [sessions, setSessions] = useState([]);
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Current session state
  const [currentSession, setCurrentSession] = useState(null);
  const [isHost, setIsHost] = useState(false);

  // Form state for creating sessions
  const [createForm, setCreateForm] = useState({
    session_name: "",
    description: "",
    group_id: groupId || "",
    story_id: null,
    scheduled_start: "",
    scheduled_end: "",
    max_participants: 10,
    difficulty_level: "intermediate",
    allow_peer_feedback: true,
    enable_text_chat: true,
    enable_voice_chat: false,
    is_public: false,
  });

  // Mock data for development
  const mockSessions = [
    {
      session_id: "session_1",
      session_name: "Morning ASL Practice",
      description: "Daily morning practice session for beginners",
      host_id: "user_456",
      group_id: "group_1",
      status: "scheduled",
      participant_count: 3,
      max_participants: 8,
      scheduled_start: new Date(Date.now() + 3600000).toISOString(), // 1 hour from now
      difficulty_level: "beginner",
      collaboration_features: {
        allow_peer_feedback: true,
        enable_text_chat: true,
        enable_voice_chat: false,
      },
    },
    {
      session_id: "session_2",
      session_name: "Advanced Storytelling",
      description: "Practice complex narratives and expressions",
      host_id: userId,
      group_id: "group_2",
      status: "active",
      participant_count: 5,
      max_participants: 6,
      scheduled_start: new Date(Date.now() - 1800000).toISOString(), // 30 minutes ago
      difficulty_level: "advanced",
      collaboration_features: {
        allow_peer_feedback: true,
        enable_text_chat: true,
        enable_voice_chat: true,
      },
    },
  ];

  const mockGroups = [
    {
      id: "group_1",
      name: "Beginner ASL Learners",
      member_count: 12,
      user_role: "member",
    },
    {
      id: "group_2",
      name: "Advanced Practice Group",
      member_count: 8,
      user_role: "educator",
    },
  ];

  // Load sessions and groups
  useEffect(() => {
    loadSessions();
    loadGroups();
  }, []);

  const loadSessions = async () => {
    setLoading(true);
    try {
      // In a real app, this would be an API call
      // const response = await fetch('/api/sessions/my');
      // const data = await response.json();

      // For now, use mock data
      setSessions(mockSessions);
    } catch (err) {
      setError("Failed to load sessions");
      console.error("Error loading sessions:", err);
    } finally {
      setLoading(false);
    }
  };

  const loadGroups = async () => {
    try {
      // In a real app, this would be an API call
      // const response = await fetch('/api/groups/my');
      // const data = await response.json();

      // For now, use mock data
      setGroups(mockGroups);
    } catch (err) {
      console.error("Error loading groups:", err);
    }
  };

  const createSession = async () => {
    setLoading(true);
    try {
      // In a real app, this would be an API call
      // const response = await fetch(`/api/groups/${createForm.group_id}/sessions`, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(createForm)
      // });
      // const newSession = await response.json();

      // For now, create mock session
      const newSession = {
        session_id: `session_${Date.now()}`,
        ...createForm,
        host_id: userId,
        status: "scheduled",
        participant_count: 1,
        created_at: new Date().toISOString(),
        collaboration_features: {
          allow_peer_feedback: createForm.allow_peer_feedback,
          enable_text_chat: createForm.enable_text_chat,
          enable_voice_chat: createForm.enable_voice_chat,
        },
      };

      setSessions((prev) => [newSession, ...prev]);
      setCurrentView("list");

      // Reset form
      setCreateForm({
        session_name: "",
        description: "",
        group_id: groupId || "",
        story_id: null,
        scheduled_start: "",
        scheduled_end: "",
        max_participants: 10,
        difficulty_level: "intermediate",
        allow_peer_feedback: true,
        enable_text_chat: true,
        enable_voice_chat: false,
        is_public: false,
      });
    } catch (err) {
      setError("Failed to create session");
      console.error("Error creating session:", err);
    } finally {
      setLoading(false);
    }
  };

  const joinSession = async (sessionId) => {
    try {
      // In a real app, this would be an API call
      // await fetch(`/api/sessions/${sessionId}/join`, { method: 'POST' });

      const session = sessions.find((s) => s.session_id === sessionId);
      if (session) {
        setCurrentSession(session);
        setIsHost(session.host_id === userId);
        setCurrentView("session");
      }
    } catch (err) {
      setError("Failed to join session");
      console.error("Error joining session:", err);
    }
  };

  const startSession = async (sessionId) => {
    try {
      // In a real app, this would be an API call
      // await fetch(`/api/sessions/${sessionId}/start`, { method: 'POST' });

      const session = sessions.find((s) => s.session_id === sessionId);
      if (session && session.host_id === userId) {
        setCurrentSession({ ...session, status: "active" });
        setIsHost(true);
        setCurrentView("session");
      }
    } catch (err) {
      setError("Failed to start session");
      console.error("Error starting session:", err);
    }
  };

  const handleSessionEnd = (finalState) => {
    console.log("Session ended with final state:", finalState);
    setCurrentView("list");
    setCurrentSession(null);
    setIsHost(false);
    loadSessions(); // Refresh session list
  };

  const formatDateTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "scheduled":
        return "#2196F3";
      case "active":
        return "#4CAF50";
      case "paused":
        return "#ff9800";
      case "completed":
        return "#757575";
      default:
        return "#757575";
    }
  };

  const canJoinSession = (session) => {
    return session.status === "scheduled" || session.status === "active";
  };

  const canStartSession = (session) => {
    return session.host_id === userId && session.status === "scheduled";
  };

  // Render session view
  if (currentView === "session" && currentSession) {
    return (
      <CollaborativeSession
        sessionId={currentSession.session_id}
        userId={userId}
        username={username}
        isHost={isHost}
        onSessionEnd={handleSessionEnd}
        storyContent={{
          title: "Sample Story",
          sentences: [
            "Hello, my name is Sarah.",
            "I love learning American Sign Language.",
            "Today is a beautiful day for practice.",
            "Let's work together to improve our skills.",
          ],
        }}
      />
    );
  }

  return (
    <div className="session-manager">
      {/* Header */}
      <div className="manager-header">
        <div className="header-content">
          <h1>Collaborative Sessions</h1>
          {onBack && (
            <button onClick={onBack} className="btn-back">
              ← Back
            </button>
          )}
        </div>

        <div className="header-actions">
          {currentView === "list" && (
            <button
              onClick={() => setCurrentView("create")}
              className="btn-primary"
            >
              Create Session
            </button>
          )}
          {currentView === "create" && (
            <button
              onClick={() => setCurrentView("list")}
              className="btn-secondary"
            >
              Cancel
            </button>
          )}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-message">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="btn-close">
            ×
          </button>
        </div>
      )}

      {/* Main Content */}
      <div className="manager-content">
        {currentView === "list" && (
          <div className="sessions-list">
            <div className="list-header">
              <h2>Your Sessions</h2>
              <div className="list-filters">
                <select className="filter-select">
                  <option value="all">All Sessions</option>
                  <option value="scheduled">Scheduled</option>
                  <option value="active">Active</option>
                  <option value="completed">Completed</option>
                </select>
              </div>
            </div>

            {loading ? (
              <div className="loading-state">
                <div className="spinner"></div>
                <p>Loading sessions...</p>
              </div>
            ) : sessions.length === 0 ? (
              <div className="empty-state">
                <h3>No sessions found</h3>
                <p>Create your first collaborative session to get started!</p>
                <button
                  onClick={() => setCurrentView("create")}
                  className="btn-primary"
                >
                  Create Session
                </button>
              </div>
            ) : (
              <div className="sessions-grid">
                {sessions.map((session) => (
                  <div key={session.session_id} className="session-card">
                    <div className="session-header">
                      <h3>{session.session_name}</h3>
                      <span
                        className="session-status"
                        style={{
                          backgroundColor: getStatusColor(session.status),
                        }}
                      >
                        {session.status.toUpperCase()}
                      </span>
                    </div>

                    <div className="session-details">
                      <p className="session-description">
                        {session.description}
                      </p>

                      <div className="session-meta">
                        <div className="meta-item">
                          <span className="meta-label">Participants:</span>
                          <span className="meta-value">
                            {session.participant_count}/
                            {session.max_participants}
                          </span>
                        </div>

                        <div className="meta-item">
                          <span className="meta-label">Difficulty:</span>
                          <span className="meta-value">
                            {session.difficulty_level}
                          </span>
                        </div>

                        {session.scheduled_start && (
                          <div className="meta-item">
                            <span className="meta-label">Scheduled:</span>
                            <span className="meta-value">
                              {formatDateTime(session.scheduled_start)}
                            </span>
                          </div>
                        )}
                      </div>

                      <div className="session-features">
                        {session.collaboration_features
                          ?.allow_peer_feedback && (
                          <span className="feature-tag">Peer Feedback</span>
                        )}
                        {session.collaboration_features?.enable_text_chat && (
                          <span className="feature-tag">Text Chat</span>
                        )}
                        {session.collaboration_features?.enable_voice_chat && (
                          <span className="feature-tag">Voice Chat</span>
                        )}
                      </div>
                    </div>

                    <div className="session-actions">
                      {canStartSession(session) && (
                        <button
                          onClick={() => startSession(session.session_id)}
                          className="btn-primary"
                        >
                          Start Session
                        </button>
                      )}

                      {canJoinSession(session) && !canStartSession(session) && (
                        <button
                          onClick={() => joinSession(session.session_id)}
                          className="btn-secondary"
                        >
                          Join Session
                        </button>
                      )}

                      {session.status === "completed" && (
                        <button className="btn-outline">View Results</button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {currentView === "create" && (
          <div className="create-session">
            <h2>Create New Session</h2>

            <form
              className="create-form"
              onSubmit={(e) => {
                e.preventDefault();
                createSession();
              }}
            >
              <div className="form-section">
                <h3>Basic Information</h3>

                <div className="form-group">
                  <label htmlFor="session_name">Session Name *</label>
                  <input
                    type="text"
                    id="session_name"
                    value={createForm.session_name}
                    onChange={(e) =>
                      setCreateForm((prev) => ({
                        ...prev,
                        session_name: e.target.value,
                      }))
                    }
                    required
                    placeholder="Enter session name"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="description">Description</label>
                  <textarea
                    id="description"
                    value={createForm.description}
                    onChange={(e) =>
                      setCreateForm((prev) => ({
                        ...prev,
                        description: e.target.value,
                      }))
                    }
                    placeholder="Describe the session goals and activities"
                    rows={3}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="group_id">Learning Group *</label>
                  <select
                    id="group_id"
                    value={createForm.group_id}
                    onChange={(e) =>
                      setCreateForm((prev) => ({
                        ...prev,
                        group_id: e.target.value,
                      }))
                    }
                    required
                  >
                    <option value="">Select a group</option>
                    {groups.map((group) => (
                      <option key={group.id} value={group.id}>
                        {group.name} ({group.member_count} members)
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-section">
                <h3>Session Settings</h3>

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="difficulty_level">Difficulty Level</label>
                    <select
                      id="difficulty_level"
                      value={createForm.difficulty_level}
                      onChange={(e) =>
                        setCreateForm((prev) => ({
                          ...prev,
                          difficulty_level: e.target.value,
                        }))
                      }
                    >
                      <option value="beginner">Beginner</option>
                      <option value="intermediate">Intermediate</option>
                      <option value="advanced">Advanced</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label htmlFor="max_participants">Max Participants</label>
                    <input
                      type="number"
                      id="max_participants"
                      value={createForm.max_participants}
                      onChange={(e) =>
                        setCreateForm((prev) => ({
                          ...prev,
                          max_participants: parseInt(e.target.value),
                        }))
                      }
                      min={2}
                      max={50}
                    />
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="scheduled_start">
                      Start Time (Optional)
                    </label>
                    <input
                      type="datetime-local"
                      id="scheduled_start"
                      value={createForm.scheduled_start}
                      onChange={(e) =>
                        setCreateForm((prev) => ({
                          ...prev,
                          scheduled_start: e.target.value,
                        }))
                      }
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="scheduled_end">End Time (Optional)</label>
                    <input
                      type="datetime-local"
                      id="scheduled_end"
                      value={createForm.scheduled_end}
                      onChange={(e) =>
                        setCreateForm((prev) => ({
                          ...prev,
                          scheduled_end: e.target.value,
                        }))
                      }
                    />
                  </div>
                </div>
              </div>

              <div className="form-section">
                <h3>Collaboration Features</h3>

                <div className="checkbox-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={createForm.allow_peer_feedback}
                      onChange={(e) =>
                        setCreateForm((prev) => ({
                          ...prev,
                          allow_peer_feedback: e.target.checked,
                        }))
                      }
                    />
                    <span className="checkbox-text">Allow peer feedback</span>
                  </label>

                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={createForm.enable_text_chat}
                      onChange={(e) =>
                        setCreateForm((prev) => ({
                          ...prev,
                          enable_text_chat: e.target.checked,
                        }))
                      }
                    />
                    <span className="checkbox-text">Enable text chat</span>
                  </label>

                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={createForm.enable_voice_chat}
                      onChange={(e) =>
                        setCreateForm((prev) => ({
                          ...prev,
                          enable_voice_chat: e.target.checked,
                        }))
                      }
                    />
                    <span className="checkbox-text">Enable voice chat</span>
                  </label>

                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={createForm.is_public}
                      onChange={(e) =>
                        setCreateForm((prev) => ({
                          ...prev,
                          is_public: e.target.checked,
                        }))
                      }
                    />
                    <span className="checkbox-text">Make session public</span>
                  </label>
                </div>
              </div>

              <div className="form-actions">
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={loading}
                >
                  {loading ? "Creating..." : "Create Session"}
                </button>
                <button
                  type="button"
                  onClick={() => setCurrentView("list")}
                  className="btn-secondary"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};

export default SessionManager;
