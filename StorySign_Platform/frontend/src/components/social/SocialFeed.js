import React, { useState, useEffect } from "react";
import "./SocialFeed.css";

const SocialFeed = ({ userId, feedType = "friends" }) => {
  const [feed, setFeed] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  useEffect(() => {
    loadFeed();
  }, [feedType]);

  const loadFeed = async (pageNum = 0) => {
    try {
      setLoading(true);
      const response = await fetch(
        `/api/social/progress/feed?feed_type=${feedType}&limit=20&offset=${
          pageNum * 20
        }`
      );

      if (!response.ok) {
        throw new Error("Failed to load feed");
      }

      const data = await response.json();

      if (pageNum === 0) {
        setFeed(data.shares);
      } else {
        setFeed((prev) => [...prev, ...data.shares]);
      }

      setHasMore(data.shares.length === 20);
      setPage(pageNum);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadMore = () => {
    if (!loading && hasMore) {
      loadFeed(page + 1);
    }
  };

  const handleInteraction = async (
    shareId,
    interactionType,
    content = null
  ) => {
    try {
      const response = await fetch(`/api/social/progress/${shareId}/interact`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          interaction_type: interactionType,
          content: content,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to interact with share");
      }

      // Refresh the feed to show updated counts
      loadFeed(0);
    } catch (err) {
      console.error("Interaction failed:", err);
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

  if (loading && feed.length === 0) {
    return (
      <div className="social-feed">
        <div className="loading-spinner">Loading feed...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="social-feed">
        <div className="error-message">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="social-feed">
      <div className="feed-header">
        <h2>
          {feedType === "friends" && "Friends Activity"}
          {feedType === "own" && "My Progress"}
          {feedType === "public" && "Community Feed"}
        </h2>

        <div className="feed-filters">
          <button
            className={feedType === "friends" ? "active" : ""}
            onClick={() => (window.location.search = "?feed=friends")}
          >
            Friends
          </button>
          <button
            className={feedType === "own" ? "active" : ""}
            onClick={() => (window.location.search = "?feed=own")}
          >
            My Progress
          </button>
          <button
            className={feedType === "public" ? "active" : ""}
            onClick={() => (window.location.search = "?feed=public")}
          >
            Community
          </button>
        </div>
      </div>

      <div className="feed-content">
        {feed.length === 0 ? (
          <div className="empty-feed">
            <p>No progress shares to show.</p>
            {feedType === "friends" && (
              <p>Connect with friends to see their learning progress!</p>
            )}
          </div>
        ) : (
          feed.map((item) => (
            <ProgressShareCard
              key={item.share.share_id}
              share={item.share}
              user={item.user}
              onInteraction={handleInteraction}
            />
          ))
        )}

        {hasMore && (
          <button
            className="load-more-btn"
            onClick={loadMore}
            disabled={loading}
          >
            {loading ? "Loading..." : "Load More"}
          </button>
        )}
      </div>
    </div>
  );
};

const ProgressShareCard = ({ share, user, onInteraction }) => {
  const [showComments, setShowComments] = useState(false);
  const [newComment, setNewComment] = useState("");
  const [liked, setLiked] = useState(false);

  const handleLike = () => {
    if (!liked) {
      onInteraction(share.share_id, "like");
      setLiked(true);
    }
  };

  const handleComment = () => {
    if (newComment.trim()) {
      onInteraction(share.share_id, "comment", newComment);
      setNewComment("");
    }
  };

  const getAchievementIcon = (achievementType) => {
    switch (achievementType) {
      case "milestone":
        return "🏆";
      case "streak":
        return "🔥";
      case "score":
        return "⭐";
      case "completion":
        return "✅";
      default:
        return "🎯";
    }
  };

  return (
    <div className="progress-share-card">
      <div className="card-header">
        <div className="user-info">
          <div className="user-avatar">
            {user.first_name ? user.first_name[0] : user.username[0]}
          </div>
          <div className="user-details">
            <span className="username">{user.username}</span>
            <span className="timestamp">{formatTimeAgo(share.created_at)}</span>
          </div>
        </div>

        {share.achievement_type && (
          <div className="achievement-badge">
            {getAchievementIcon(share.achievement_type)}
          </div>
        )}
      </div>

      <div className="card-content">
        <h3 className="share-title">{share.title}</h3>
        {share.description && (
          <p className="share-description">{share.description}</p>
        )}

        {share.progress_data && (
          <div className="progress-details">
            {share.progress_data.score && (
              <div className="progress-metric">
                <span className="metric-label">Score:</span>
                <span className="metric-value">
                  {share.progress_data.score}%
                </span>
              </div>
            )}
            {share.progress_data.sentences_completed && (
              <div className="progress-metric">
                <span className="metric-label">Sentences:</span>
                <span className="metric-value">
                  {share.progress_data.sentences_completed}/
                  {share.progress_data.total_sentences}
                </span>
              </div>
            )}
            {share.progress_data.practice_time && (
              <div className="progress-metric">
                <span className="metric-label">Time:</span>
                <span className="metric-value">
                  {share.progress_data.practice_time} min
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="card-actions">
        <button
          className={`action-btn like-btn ${liked ? "liked" : ""}`}
          onClick={handleLike}
          disabled={liked}
        >
          👍 {share.interaction_stats.like_count}
        </button>

        {share.settings.allow_comments && (
          <button
            className="action-btn comment-btn"
            onClick={() => setShowComments(!showComments)}
          >
            💬 {share.interaction_stats.comment_count}
          </button>
        )}

        <button className="action-btn view-btn">
          👁️ {share.interaction_stats.view_count}
        </button>
      </div>

      {showComments && share.settings.allow_comments && (
        <div className="comments-section">
          <div className="add-comment">
            <input
              type="text"
              placeholder="Add a comment..."
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && handleComment()}
            />
            <button onClick={handleComment} disabled={!newComment.trim()}>
              Post
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

const formatTimeAgo = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now - date) / 1000);

  if (diffInSeconds < 60) return "just now";
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
  return `${Math.floor(diffInSeconds / 86400)}d ago`;
};

export default SocialFeed;
