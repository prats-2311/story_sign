import React, { useState, useEffect } from "react";
import "./GroupAnalyticsDashboard.css";

const GroupAnalyticsDashboard = ({ groupId, userRole }) => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [periodDays, setPeriodDays] = useState(30);
  const [selectedView, setSelectedView] = useState("overview");

  const canViewAnalytics = ["owner", "educator", "moderator"].includes(
    userRole
  );

  useEffect(() => {
    if (canViewAnalytics) {
      loadAnalytics();
    }
  }, [groupId, periodDays, canViewAnalytics]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `/api/v1/groups/${groupId}/progress-report?period_days=${periodDays}`
      );
      if (response.ok) {
        const data = await response.json();
        setAnalyticsData(data);
      }
    } catch (error) {
      console.error("Failed to load analytics:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatPercentage = (value) => {
    return `${value.toFixed(1)}%`;
  };

  const formatDuration = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const renderOverviewCards = () => {
    if (!analyticsData) return null;

    const { assignment_statistics, member_progress, engagement_metrics } =
      analyticsData;

    return (
      <div className="analytics-cards">
        <div className="analytics-card">
          <div className="card-header">
            <h4>Assignment Progress</h4>
            <div className="card-icon assignment-icon">📝</div>
          </div>
          <div className="card-content">
            <div className="metric-large">
              {formatPercentage(assignment_statistics.completion_rate)}
            </div>
            <div className="metric-label">Average Completion Rate</div>
            <div className="metric-details">
              <span>
                {assignment_statistics.completed_submissions} of{" "}
                {assignment_statistics.total_submissions} submissions completed
              </span>
            </div>
          </div>
        </div>

        <div className="analytics-card">
          <div className="card-header">
            <h4>Group Performance</h4>
            <div className="card-icon performance-icon">🎯</div>
          </div>
          <div className="card-content">
            <div className="metric-large">
              {assignment_statistics.average_score
                ? formatPercentage(assignment_statistics.average_score * 100)
                : "N/A"}
            </div>
            <div className="metric-label">Average Score</div>
            <div className="metric-details">
              <span>
                Across {assignment_statistics.published_assignments} published
                assignments
              </span>
            </div>
          </div>
        </div>

        <div className="analytics-card">
          <div className="card-header">
            <h4>Member Activity</h4>
            <div className="card-icon activity-icon">👥</div>
          </div>
          <div className="card-content">
            <div className="metric-large">{analyticsData.member_count}</div>
            <div className="metric-label">Total Members</div>
            <div className="metric-details">
              <span>
                {member_progress.filter((m) => m.recent_sessions > 0).length}{" "}
                active this period
              </span>
            </div>
          </div>
        </div>

        <div className="analytics-card">
          <div className="card-header">
            <h4>Engagement</h4>
            <div className="card-icon engagement-icon">💬</div>
          </div>
          <div className="card-content">
            <div className="metric-large">
              {engagement_metrics.total_messages}
            </div>
            <div className="metric-label">Messages Sent</div>
            <div className="metric-details">
              <span>{engagement_metrics.active_participants} participants</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderMemberProgress = () => {
    if (!analyticsData?.member_progress) return null;

    const sortedMembers = [...analyticsData.member_progress].sort(
      (a, b) => (b.average_score || 0) - (a.average_score || 0)
    );

    return (
      <div className="member-progress-section">
        <h4>Member Progress</h4>
        <div className="progress-table">
          <div className="table-header">
            <div className="col-member">Member</div>
            <div className="col-sessions">Recent Sessions</div>
            <div className="col-time">Practice Time</div>
            <div className="col-score">Avg Score</div>
            <div className="col-streak">Streak</div>
          </div>
          {sortedMembers.map((member, index) => (
            <div key={member.user_id} className="table-row">
              <div className="col-member">
                <div className="member-info">
                  <div className="member-avatar">{index + 1}</div>
                  <span>Member {member.user_id.slice(-6)}</span>
                </div>
              </div>
              <div className="col-sessions">{member.recent_sessions}</div>
              <div className="col-time">
                {formatDuration(member.total_practice_time)}
              </div>
              <div className="col-score">
                <div className="score-bar">
                  <div
                    className="score-fill"
                    style={{ width: `${(member.average_score || 0) * 100}%` }}
                  ></div>
                  <span className="score-text">
                    {member.average_score
                      ? formatPercentage(member.average_score * 100)
                      : "N/A"}
                  </span>
                </div>
              </div>
              <div className="col-streak">
                <span className="streak-badge">
                  🔥 {member.learning_streak}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderAssignmentBreakdown = () => {
    if (!analyticsData?.assignment_statistics) return null;

    const stats = analyticsData.assignment_statistics;

    return (
      <div className="assignment-breakdown">
        <h4>Assignment Breakdown</h4>
        <div className="breakdown-grid">
          <div className="breakdown-item">
            <div className="breakdown-number">{stats.total_assignments}</div>
            <div className="breakdown-label">Total Assignments</div>
          </div>
          <div className="breakdown-item">
            <div className="breakdown-number">
              {stats.published_assignments}
            </div>
            <div className="breakdown-label">Published</div>
          </div>
          <div className="breakdown-item">
            <div className="breakdown-number">{stats.total_submissions}</div>
            <div className="breakdown-label">Total Submissions</div>
          </div>
          <div className="breakdown-item">
            <div className="breakdown-number">
              {stats.completed_submissions}
            </div>
            <div className="breakdown-label">Completed</div>
          </div>
        </div>

        <div className="completion-chart">
          <div className="chart-header">
            <span>Completion Progress</span>
            <span>{formatPercentage(stats.completion_rate)}</span>
          </div>
          <div className="chart-bar">
            <div
              className="chart-fill"
              style={{ width: `${stats.completion_rate}%` }}
            ></div>
          </div>
        </div>
      </div>
    );
  };

  const renderEngagementMetrics = () => {
    if (!analyticsData?.engagement_metrics) return null;

    const metrics = analyticsData.engagement_metrics;

    return (
      <div className="engagement-section">
        <h4>Engagement Metrics</h4>
        <div className="engagement-grid">
          <div className="engagement-item">
            <div className="engagement-icon">💬</div>
            <div className="engagement-content">
              <div className="engagement-number">{metrics.total_messages}</div>
              <div className="engagement-label">Total Messages</div>
            </div>
          </div>
          <div className="engagement-item">
            <div className="engagement-icon">👤</div>
            <div className="engagement-content">
              <div className="engagement-number">
                {metrics.active_participants}
              </div>
              <div className="engagement-label">Active Participants</div>
            </div>
          </div>
          <div className="engagement-item">
            <div className="engagement-icon">📢</div>
            <div className="engagement-content">
              <div className="engagement-number">{metrics.announcements}</div>
              <div className="engagement-label">Announcements</div>
            </div>
          </div>
          <div className="engagement-item">
            <div className="engagement-icon">📊</div>
            <div className="engagement-content">
              <div className="engagement-number">
                {metrics.average_messages_per_day.toFixed(1)}
              </div>
              <div className="engagement-label">Messages/Day</div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  if (!canViewAnalytics) {
    return (
      <div className="analytics-dashboard">
        <div className="access-denied">
          <h3>Access Denied</h3>
          <p>You don't have permission to view group analytics.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="analytics-dashboard">
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Loading analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="analytics-dashboard">
      <div className="dashboard-header">
        <h3>Group Analytics</h3>
        <div className="dashboard-controls">
          <select
            value={periodDays}
            onChange={(e) => setPeriodDays(parseInt(e.target.value))}
            className="period-selector"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>

          <div className="view-tabs">
            <button
              className={`tab-button ${
                selectedView === "overview" ? "active" : ""
              }`}
              onClick={() => setSelectedView("overview")}
            >
              Overview
            </button>
            <button
              className={`tab-button ${
                selectedView === "members" ? "active" : ""
              }`}
              onClick={() => setSelectedView("members")}
            >
              Members
            </button>
            <button
              className={`tab-button ${
                selectedView === "assignments" ? "active" : ""
              }`}
              onClick={() => setSelectedView("assignments")}
            >
              Assignments
            </button>
          </div>
        </div>
      </div>

      <div className="dashboard-content">
        {selectedView === "overview" && (
          <>
            {renderOverviewCards()}
            {renderEngagementMetrics()}
          </>
        )}

        {selectedView === "members" && renderMemberProgress()}

        {selectedView === "assignments" && renderAssignmentBreakdown()}
      </div>

      {analyticsData && (
        <div className="dashboard-footer">
          <p className="generated-time">
            Report generated:{" "}
            {new Date(analyticsData.generated_at).toLocaleString()}
          </p>
        </div>
      )}
    </div>
  );
};

export default GroupAnalyticsDashboard;
