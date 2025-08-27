import React, { useState, useEffect } from "react";
import "./NotificationCenter.css";

const NotificationCenter = ({ userId, onNotificationClick }) => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState("all"); // all, unread, assignments, groups

  useEffect(() => {
    loadNotifications();
    // Set up polling for new notifications
    const interval = setInterval(loadNotifications, 30000); // Poll every 30 seconds
    return () => clearInterval(interval);
  }, [userId, filter]);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const unreadOnly = filter === "unread";
      const response = await fetch(
        `/api/v1/my/notifications?unread_only=${unreadOnly}&limit=50`
      );

      if (response.ok) {
        const data = await response.json();
        setNotifications(data.notifications);
        setUnreadCount(data.unread_count);
      }
    } catch (error) {
      console.error("Failed to load notifications:", error);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      const response = await fetch(
        `/api/v1/notifications/${notificationId}/read`,
        {
          method: "POST",
        }
      );

      if (response.ok) {
        // Update local state
        setNotifications(
          notifications.map((n) =>
            n.notification_id === notificationId
              ? { ...n, is_read: true, read_at: new Date().toISOString() }
              : n
          )
        );
        setUnreadCount(Math.max(0, unreadCount - 1));
      }
    } catch (error) {
      console.error("Failed to mark notification as read:", error);
    }
  };

  const markAllAsRead = async () => {
    try {
      const response = await fetch("/api/v1/notifications/mark-all-read", {
        method: "POST",
      });

      if (response.ok) {
        setNotifications(
          notifications.map((n) => ({
            ...n,
            is_read: true,
            read_at: new Date().toISOString(),
          }))
        );
        setUnreadCount(0);
      }
    } catch (error) {
      console.error("Failed to mark all notifications as read:", error);
    }
  };

  const handleNotificationClick = (notification) => {
    if (!notification.is_read) {
      markAsRead(notification.notification_id);
    }

    if (notification.action_url && onNotificationClick) {
      onNotificationClick(notification.action_url);
    }

    setIsOpen(false);
  };

  const getNotificationIcon = (type) => {
    const iconMap = {
      assignment_created: "📝",
      assignment_due: "⏰",
      assignment_overdue: "🚨",
      assignment_graded: "✅",
      session_scheduled: "📅",
      session_starting: "🎯",
      group_invitation: "👥",
      group_update: "📢",
      peer_achievement: "🏆",
      system_announcement: "📣",
      feedback_received: "💬",
    };
    return iconMap[type] || "📋";
  };

  const getPriorityClass = (priority) => {
    return `priority-${priority}`;
  };

  const formatTimeAgo = (timestamp) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffInSeconds = Math.floor((now - time) / 1000);

    if (diffInSeconds < 60) return "Just now";
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400)
      return `${Math.floor(diffInSeconds / 3600)}h ago`;
    if (diffInSeconds < 604800)
      return `${Math.floor(diffInSeconds / 86400)}d ago`;
    return time.toLocaleDateString();
  };

  const filteredNotifications = notifications.filter((notification) => {
    if (filter === "all") return true;
    if (filter === "unread") return !notification.is_read;
    if (filter === "assignments")
      return notification.notification_type.includes("assignment");
    if (filter === "groups")
      return notification.notification_type.includes("group");
    return true;
  });

  return (
    <div className="notification-center">
      <button
        className="notification-trigger"
        onClick={() => setIsOpen(!isOpen)}
        aria-label={`Notifications (${unreadCount} unread)`}
      >
        <div className="notification-icon">
          🔔
          {unreadCount > 0 && (
            <span className="notification-badge">
              {unreadCount > 99 ? "99+" : unreadCount}
            </span>
          )}
        </div>
      </button>

      {isOpen && (
        <div className="notification-dropdown">
          <div className="notification-header">
            <h4>Notifications</h4>
            <div className="notification-actions">
              {unreadCount > 0 && (
                <button
                  className="mark-all-read-btn"
                  onClick={markAllAsRead}
                  title="Mark all as read"
                >
                  ✓
                </button>
              )}
              <button
                className="close-btn"
                onClick={() => setIsOpen(false)}
                title="Close"
              >
                ✕
              </button>
            </div>
          </div>

          <div className="notification-filters">
            <button
              className={`filter-btn ${filter === "all" ? "active" : ""}`}
              onClick={() => setFilter("all")}
            >
              All
            </button>
            <button
              className={`filter-btn ${filter === "unread" ? "active" : ""}`}
              onClick={() => setFilter("unread")}
            >
              Unread ({unreadCount})
            </button>
            <button
              className={`filter-btn ${
                filter === "assignments" ? "active" : ""
              }`}
              onClick={() => setFilter("assignments")}
            >
              Assignments
            </button>
            <button
              className={`filter-btn ${filter === "groups" ? "active" : ""}`}
              onClick={() => setFilter("groups")}
            >
              Groups
            </button>
          </div>

          <div className="notification-list">
            {loading ? (
              <div className="notification-loading">
                <div className="loading-spinner"></div>
                <span>Loading notifications...</span>
              </div>
            ) : filteredNotifications.length === 0 ? (
              <div className="no-notifications">
                <div className="no-notifications-icon">📭</div>
                <p>No notifications found</p>
                {filter !== "all" && (
                  <button
                    className="show-all-btn"
                    onClick={() => setFilter("all")}
                  >
                    Show all notifications
                  </button>
                )}
              </div>
            ) : (
              filteredNotifications.map((notification) => (
                <div
                  key={notification.notification_id}
                  className={`notification-item ${
                    !notification.is_read ? "unread" : ""
                  } ${getPriorityClass(notification.priority)}`}
                  onClick={() => handleNotificationClick(notification)}
                >
                  <div className="notification-icon-container">
                    <span className="notification-type-icon">
                      {getNotificationIcon(notification.notification_type)}
                    </span>
                    {!notification.is_read && (
                      <div className="unread-dot"></div>
                    )}
                  </div>

                  <div className="notification-content">
                    <div className="notification-title">
                      {notification.title}
                    </div>
                    <div className="notification-message">
                      {notification.message}
                    </div>
                    <div className="notification-meta">
                      <span className="notification-time">
                        {formatTimeAgo(notification.created_at)}
                      </span>
                      {notification.priority === "high" && (
                        <span className="priority-indicator high">
                          High Priority
                        </span>
                      )}
                      {notification.priority === "urgent" && (
                        <span className="priority-indicator urgent">
                          Urgent
                        </span>
                      )}
                    </div>
                  </div>

                  {notification.action_text && (
                    <div className="notification-action">
                      <span className="action-text">
                        {notification.action_text}
                      </span>
                      <span className="action-arrow">→</span>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          {filteredNotifications.length > 0 && (
            <div className="notification-footer">
              <button
                className="view-all-btn"
                onClick={() => {
                  setIsOpen(false);
                  if (onNotificationClick) {
                    onNotificationClick("/notifications");
                  }
                }}
              >
                View All Notifications
              </button>
            </div>
          )}
        </div>
      )}

      {isOpen && (
        <div
          className="notification-overlay"
          onClick={() => setIsOpen(false)}
        ></div>
      )}
    </div>
  );
};

export default NotificationCenter;
