import React, { useState, useEffect } from "react";
import "./CommunityFeedback.css";

const CommunityFeedback = ({ userId, sessionId = null }) => {
  const [activeTab, setActiveTab] = useState("received");
  const [feedback, setFeedback] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showGiveFeedback, setShowGiveFeedback] = useState(false);
  const [feedbackFilter, setFeedbackFilter] = useState("all");

  useEffect(() => {
    loadFeedback();
  }, [activeTab, feedbackFilter]);

  const loadFeedback = async () => {
    try {
      setLoading(true);
      const filterParam =
        feedbackFilter !== "all" ? `&feedback_type=${feedbackFilter}` : "";
      const response = await fetch(
        `/api/social/feedback?direction=${activeTab}${filterParam}`
      );

      if (!response.ok) {
        throw new Error("Failed to load feedback");
      }

      const data = await response.json();
      setFeedback(data.feedback || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const rateFeedbackHelpfulness = async (feedbackId, isHelpful) => {
    try {
      const response = await fetch(`/api/social/feedback/${feedbackId}/rate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(isHelpful),
      });

      if (!response.ok) {
        throw new Error("Failed to rate feedback");
      }

      // Refresh feedback to show updated ratings
      await loadFeedback();
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  const feedbackTypes = [
    { value: "all", label: "All Types" },
    { value: "encouragement", label: "Encouragement" },
    { value: "suggestion", label: "Suggestions" },
    { value: "correction", label: "Corrections" },
    { value: "question", label: "Questions" },
    { value: "praise", label: "Praise" },
  ];

  return (
    <div className="community-feedback">
      <div className="feedback-header">
        <h2>Community Feedback</h2>

        <div className="header-actions">
          <button
            className="give-feedback-btn"
            onClick={() => setShowGiveFeedback(true)}
          >
            Give Feedback
          </button>
        </div>
      </div>

      <div className="feedback-controls">
        <div className="tab-navigation">
          <button
            className={activeTab === "received" ? "active" : ""}
            onClick={() => setActiveTab("received")}
          >
            Received
          </button>
          <button
            className={activeTab === "given" ? "active" : ""}
            onClick={() => setActiveTab("given")}
          >
            Given
          </button>
        </div>

        <div className="feedback-filters">
          <select
            value={feedbackFilter}
            onChange={(e) => setFeedbackFilter(e.target.value)}
            className="filter-select"
          >
            {feedbackTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && <div className="error-message">Error: {error}</div>}

      <div className="feedback-content">
        {loading ? (
          <div className="loading-spinner">Loading feedback...</div>
        ) : feedback.length === 0 ? (
          <div className="empty-state">
            <p>
              {activeTab === "received"
                ? "You haven't received any feedback yet."
                : "You haven't given any feedback yet."}
            </p>
            <p>
              {activeTab === "received"
                ? "Practice with friends to start receiving helpful feedback!"
                : "Help other learners by providing constructive feedback on their practice sessions."}
            </p>
          </div>
        ) : (
          <div className="feedback-list">
            {feedback.map((item) => (
              <FeedbackCard
                key={item.feedback_id}
                feedback={item}
                isReceived={activeTab === "received"}
                onRateHelpfulness={rateFeedbackHelpfulness}
              />
            ))}
          </div>
        )}
      </div>

      {showGiveFeedback && (
        <GiveFeedbackModal
          onClose={() => setShowGiveFeedback(false)}
          onSubmit={loadFeedback}
          sessionId={sessionId}
        />
      )}
    </div>
  );
};

const FeedbackCard = ({ feedback, isReceived, onRateHelpfulness }) => {
  const [showFullContent, setShowFullContent] = useState(false);

  const getFeedbackTypeIcon = (type) => {
    switch (type) {
      case "encouragement":
        return "💪";
      case "suggestion":
        return "💡";
      case "correction":
        return "✏️";
      case "question":
        return "❓";
      case "praise":
        return "👏";
      default:
        return "💬";
    }
  };

  const getFeedbackTypeColor = (type) => {
    switch (type) {
      case "encouragement":
        return "#28a745";
      case "suggestion":
        return "#007bff";
      case "correction":
        return "#ffc107";
      case "question":
        return "#6f42c1";
      case "praise":
        return "#fd7e14";
      default:
        return "#6c757d";
    }
  };

  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);

    if (diffInSeconds < 60) return "just now";
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400)
      return `${Math.floor(diffInSeconds / 3600)}h ago`;
    return `${Math.floor(diffInSeconds / 86400)}d ago`;
  };

  const contentPreview =
    feedback.content.length > 150
      ? feedback.content.substring(0, 150) + "..."
      : feedback.content;

  return (
    <div className="feedback-card">
      <div className="feedback-header">
        <div
          className="feedback-type-badge"
          style={{
            backgroundColor: getFeedbackTypeColor(feedback.feedback_type),
          }}
        >
          {getFeedbackTypeIcon(feedback.feedback_type)}
          <span>{feedback.feedback_type}</span>
        </div>

        <div className="feedback-meta">
          <span className="feedback-user">
            {isReceived
              ? `From: ${feedback.other_user.username}`
              : `To: ${feedback.other_user.username}`}
          </span>
          <span className="feedback-time">
            {formatTimeAgo(feedback.created_at)}
          </span>
        </div>
      </div>

      <div className="feedback-content">
        <p>
          {showFullContent ? feedback.content : contentPreview}
          {feedback.content.length > 150 && (
            <button
              className="show-more-btn"
              onClick={() => setShowFullContent(!showFullContent)}
            >
              {showFullContent ? "Show less" : "Show more"}
            </button>
          )}
        </p>

        {feedback.skill_areas && feedback.skill_areas.length > 0 && (
          <div className="skill-areas">
            <span className="skill-label">Skills:</span>
            {feedback.skill_areas.map((skill, index) => (
              <span key={index} className="skill-tag">
                {skill}
              </span>
            ))}
          </div>
        )}

        {feedback.tags && feedback.tags.length > 0 && (
          <div className="feedback-tags">
            {feedback.tags.map((tag, index) => (
              <span key={index} className="feedback-tag">
                #{tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {isReceived && feedback.quality_metrics && (
        <div className="feedback-actions">
          <div className="helpfulness-section">
            <span className="helpfulness-label">Was this helpful?</span>
            <div className="helpfulness-buttons">
              <button
                className="helpful-btn"
                onClick={() => onRateHelpfulness(feedback.feedback_id, true)}
              >
                👍 Yes
              </button>
              <button
                className="not-helpful-btn"
                onClick={() => onRateHelpfulness(feedback.feedback_id, false)}
              >
                👎 No
              </button>
            </div>
            {feedback.quality_metrics.helpfulness_votes > 0 && (
              <span className="helpfulness-score">
                {Math.round(feedback.quality_metrics.helpfulness_score * 20)}%
                helpful ({feedback.quality_metrics.helpfulness_votes} votes)
              </span>
            )}
          </div>
        </div>
      )}

      {feedback.session_id && (
        <div className="feedback-context">
          <span className="context-label">Related to practice session</span>
        </div>
      )}
    </div>
  );
};

const GiveFeedbackModal = ({ onClose, onSubmit, sessionId }) => {
  const [formData, setFormData] = useState({
    receiver_username: "",
    feedback_type: "encouragement",
    content: "",
    is_public: false,
    is_anonymous: false,
    tags: "",
    skill_areas: "",
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.receiver_username.trim() || !formData.content.trim()) {
      alert("Please fill in all required fields");
      return;
    }

    try {
      setSubmitting(true);

      const submitData = {
        ...formData,
        session_id: sessionId,
        tags: formData.tags
          ? formData.tags.split(",").map((tag) => tag.trim())
          : [],
        skill_areas: formData.skill_areas
          ? formData.skill_areas.split(",").map((skill) => skill.trim())
          : [],
      };

      const response = await fetch("/api/social/feedback", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(submitData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to submit feedback");
      }

      alert("Feedback submitted successfully!");
      onSubmit();
      onClose();
    } catch (err) {
      alert(`Error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="feedback-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Give Feedback</h3>
          <button className="close-btn" onClick={onClose}>
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="feedback-form">
          <div className="form-group">
            <label>To (Username) *</label>
            <input
              type="text"
              value={formData.receiver_username}
              onChange={(e) =>
                handleChange("receiver_username", e.target.value)
              }
              placeholder="Enter username"
              required
            />
          </div>

          <div className="form-group">
            <label>Feedback Type *</label>
            <select
              value={formData.feedback_type}
              onChange={(e) => handleChange("feedback_type", e.target.value)}
              required
            >
              <option value="encouragement">Encouragement</option>
              <option value="suggestion">Suggestion</option>
              <option value="correction">Correction</option>
              <option value="question">Question</option>
              <option value="praise">Praise</option>
            </select>
          </div>

          <div className="form-group">
            <label>Feedback Content *</label>
            <textarea
              value={formData.content}
              onChange={(e) => handleChange("content", e.target.value)}
              placeholder="Write your feedback here..."
              rows={4}
              required
            />
          </div>

          <div className="form-group">
            <label>Skill Areas (comma-separated)</label>
            <input
              type="text"
              value={formData.skill_areas}
              onChange={(e) => handleChange("skill_areas", e.target.value)}
              placeholder="e.g., fingerspelling, facial expressions"
            />
          </div>

          <div className="form-group">
            <label>Tags (comma-separated)</label>
            <input
              type="text"
              value={formData.tags}
              onChange={(e) => handleChange("tags", e.target.value)}
              placeholder="e.g., beginner, practice, improvement"
            />
          </div>

          <div className="form-options">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={formData.is_public}
                onChange={(e) => handleChange("is_public", e.target.checked)}
              />
              Make this feedback public
            </label>

            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={formData.is_anonymous}
                onChange={(e) => handleChange("is_anonymous", e.target.checked)}
              />
              Give feedback anonymously
            </label>
          </div>

          <div className="form-actions">
            <button type="button" onClick={onClose} className="cancel-btn">
              Cancel
            </button>
            <button type="submit" disabled={submitting} className="submit-btn">
              {submitting ? "Submitting..." : "Submit Feedback"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CommunityFeedback;
