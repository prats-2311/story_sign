/**
 * Analytics Dashboard Component
 * Main dashboard for educators and researchers to view analytics data
 */

import React, { useState, useEffect } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from "chart.js";
import {
  UserActivityChart,
  ModuleUsageChart,
  LearningProgressChart,
  DifficultyDistributionChart,
  ResponseTimeChart,
  SystemLoadChart,
  GestureAccuracyChart,
  SessionDurationChart,
  LearningOutcomesChart,
  EngagementHeatmapChart,
  RetentionRateChart,
} from "./AnalyticsCharts";
import DataExportPanel from "./DataExportPanel";
import AdvancedReporting from "./AdvancedReporting";
import "./AnalyticsDashboard.css";

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const AnalyticsDashboard = ({ userRole = "educator" }) => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dateRange, setDateRange] = useState({
    startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
      .toISOString()
      .split("T")[0],
    endDate: new Date().toISOString().split("T")[0],
  });
  const [selectedModule, setSelectedModule] = useState("all");
  const [viewType, setViewType] = useState("overview");

  useEffect(() => {
    loadAnalyticsData();
  }, [dateRange, selectedModule]);

  const loadAnalyticsData = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        "/api/v1/analytics/platform?" +
          new URLSearchParams({
            start_date: dateRange.startDate,
            end_date: dateRange.endDate,
            module_name: selectedModule === "all" ? "" : selectedModule,
            include_anonymous: "true",
          }),
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("auth_token")}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setAnalyticsData(data);
      } else {
        throw new Error("Failed to load analytics data");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading)
    return <div className="analytics-loading">Loading analytics...</div>;
  if (error) return <div className="analytics-error">Error: {error}</div>;

  return (
    <div className="analytics-dashboard">
      <div className="dashboard-header">
        <h1>Analytics Dashboard</h1>
        <div className="dashboard-controls">
          <div className="date-range-selector">
            <label>Start Date:</label>
            <input
              type="date"
              value={dateRange.startDate}
              onChange={(e) =>
                setDateRange({ ...dateRange, startDate: e.target.value })
              }
            />
            <label>End Date:</label>
            <input
              type="date"
              value={dateRange.endDate}
              onChange={(e) =>
                setDateRange({ ...dateRange, endDate: e.target.value })
              }
            />
          </div>
        </div>
      </div>

      <div className="dashboard-content">
        <div className="view-selector">
          <button
            className={viewType === "overview" ? "active" : ""}
            onClick={() => setViewType("overview")}
          >
            Overview
          </button>
          <button
            className={viewType === "learning" ? "active" : ""}
            onClick={() => setViewType("learning")}
          >
            Learning Analytics
          </button>
          <button
            className={viewType === "performance" ? "active" : ""}
            onClick={() => setViewType("performance")}
          >
            Performance
          </button>
          <button
            className={viewType === "research" ? "active" : ""}
            onClick={() => setViewType("research")}
          >
            Research
          </button>
          <button
            className={viewType === "reports" ? "active" : ""}
            onClick={() => setViewType("reports")}
          >
            Advanced Reports
          </button>
          <button
            className={viewType === "export" ? "active" : ""}
            onClick={() => setViewType("export")}
          >
            Export Data
          </button>
        </div>

        {viewType === "overview" && (
          <OverviewDashboard analyticsData={analyticsData} />
        )}
        {viewType === "learning" && (
          <LearningAnalyticsDashboard analyticsData={analyticsData} />
        )}
        {viewType === "performance" && (
          <PerformanceDashboard analyticsData={analyticsData} />
        )}
        {viewType === "research" && (
          <ResearchDashboard analyticsData={analyticsData} />
        )}
        {viewType === "reports" && (
          <AdvancedReporting
            analyticsData={analyticsData}
            userRole={userRole}
          />
        )}
        {viewType === "export" && (
          <DataExportPanel
            analyticsData={analyticsData}
            dateRange={dateRange}
          />
        )}
      </div>
    </div>
  );
};

// Overview Dashboard Component
const OverviewDashboard = ({ analyticsData }) => {
  const metrics = analyticsData?.platform_metrics || {};

  return (
    <div className="overview-dashboard">
      <div className="metrics-grid">
        <div className="metric-card">
          <h3>Total Users</h3>
          <div className="metric-value">{metrics.total_users || 0}</div>
        </div>
        <div className="metric-card">
          <h3>Active Sessions</h3>
          <div className="metric-value">{metrics.active_sessions || 0}</div>
        </div>
        <div className="metric-card">
          <h3>Practice Sessions</h3>
          <div className="metric-value">{metrics.practice_sessions || 0}</div>
        </div>
        <div className="metric-card">
          <h3>Stories Completed</h3>
          <div className="metric-value">{metrics.stories_completed || 0}</div>
        </div>
      </div>

      <div className="charts-grid">
        <div className="chart-container">
          <h3>Daily Active Users</h3>
          <UserActivityChart data={metrics.daily_activity || []} />
        </div>
        <div className="chart-container">
          <h3>Module Usage</h3>
          <ModuleUsageChart data={metrics.module_usage || {}} />
        </div>
      </div>
    </div>
  );
};

// Learning Analytics Dashboard Component
const LearningAnalyticsDashboard = ({ analyticsData }) => {
  const learningMetrics =
    analyticsData?.platform_metrics?.learning_metrics || {};

  return (
    <div className="learning-dashboard">
      <div className="learning-metrics">
        <div className="metric-card">
          <h3>Average Score</h3>
          <div className="metric-value">
            {(learningMetrics.average_score || 0).toFixed(1)}%
          </div>
          <div className="metric-trend">
            {learningMetrics.score_trend > 0 ? "↗" : "↘"}
            {Math.abs(learningMetrics.score_trend || 0).toFixed(1)}%
          </div>
        </div>
        <div className="metric-card">
          <h3>Completion Rate</h3>
          <div className="metric-value">
            {(learningMetrics.completion_rate || 0).toFixed(1)}%
          </div>
          <div className="metric-trend">
            {learningMetrics.completion_trend > 0 ? "↗" : "↘"}
            {Math.abs(learningMetrics.completion_trend || 0).toFixed(1)}%
          </div>
        </div>
        <div className="metric-card">
          <h3>Average Session Time</h3>
          <div className="metric-value">
            {Math.round(learningMetrics.avg_session_time || 0)}min
          </div>
          <div className="metric-trend">
            {learningMetrics.session_time_trend > 0 ? "↗" : "↘"}
            {Math.abs(learningMetrics.session_time_trend || 0).toFixed(1)}min
          </div>
        </div>
        <div className="metric-card">
          <h3>Gesture Accuracy</h3>
          <div className="metric-value">
            {(learningMetrics.gesture_accuracy || 0).toFixed(1)}%
          </div>
          <div className="metric-trend">
            {learningMetrics.accuracy_trend > 0 ? "↗" : "↘"}
            {Math.abs(learningMetrics.accuracy_trend || 0).toFixed(1)}%
          </div>
        </div>
      </div>

      <div className="learning-charts">
        <div className="chart-container">
          <h3>Learning Progress Over Time</h3>
          <LearningProgressChart
            data={learningMetrics.progress_over_time || []}
          />
        </div>
        <div className="chart-container">
          <h3>Difficulty Distribution</h3>
          <DifficultyDistributionChart
            data={learningMetrics.difficulty_distribution || {}}
          />
        </div>
        <div className="chart-container">
          <h3>Gesture Accuracy by Type</h3>
          <GestureAccuracyChart
            data={learningMetrics.gesture_accuracy_by_type || []}
          />
        </div>
        <div className="chart-container">
          <h3>Session Duration Trends</h3>
          <SessionDurationChart
            data={learningMetrics.session_duration_trends || []}
          />
        </div>
      </div>

      <div className="insights-panel">
        <h3>Learning Insights</h3>
        <div className="insights-grid">
          <div className="insight-card">
            <h4>Top Performing Areas</h4>
            <ul>
              {(learningMetrics.top_performing_areas || []).map(
                (area, index) => (
                  <li key={index}>
                    <span className="area-name">{area.name}</span>
                    <span className="area-score">{area.score.toFixed(1)}%</span>
                  </li>
                )
              )}
            </ul>
          </div>
          <div className="insight-card">
            <h4>Areas for Improvement</h4>
            <ul>
              {(learningMetrics.improvement_areas || []).map((area, index) => (
                <li key={index}>
                  <span className="area-name">{area.name}</span>
                  <span className="area-score">{area.score.toFixed(1)}%</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="insight-card">
            <h4>Learning Recommendations</h4>
            <ul>
              {(learningMetrics.recommendations || []).map((rec, index) => (
                <li key={index}>
                  <span className="recommendation-text">{rec.text}</span>
                  <span className={`priority ${rec.priority}`}>
                    {rec.priority}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

// Performance Dashboard Component
const PerformanceDashboard = ({ analyticsData }) => {
  const performanceMetrics =
    analyticsData?.platform_metrics?.performance_metrics || {};

  return (
    <div className="performance-dashboard">
      <div className="performance-metrics">
        <div className="metric-card">
          <h3>Avg Response Time</h3>
          <div className="metric-value">
            {Math.round(performanceMetrics.avg_response_time || 0)}ms
          </div>
        </div>
        <div className="metric-card">
          <h3>Video Processing</h3>
          <div className="metric-value">
            {Math.round(performanceMetrics.avg_video_processing || 0)}ms
          </div>
        </div>
        <div className="metric-card">
          <h3>Error Rate</h3>
          <div className="metric-value">
            {(performanceMetrics.error_rate || 0).toFixed(2)}%
          </div>
        </div>
      </div>

      <div className="performance-charts">
        <div className="chart-container">
          <h3>Response Time Trends</h3>
          <ResponseTimeChart
            data={performanceMetrics.response_time_trends || []}
          />
        </div>
        <div className="chart-container">
          <h3>System Load</h3>
          <SystemLoadChart data={performanceMetrics.system_load || []} />
        </div>
      </div>
    </div>
  );
};

// Research Dashboard Component
const ResearchDashboard = ({ analyticsData }) => {
  const researchMetrics =
    analyticsData?.platform_metrics?.research_metrics || {};

  return (
    <div className="research-dashboard">
      <div className="research-overview">
        <div className="metric-card">
          <h3>Total Participants</h3>
          <div className="metric-value">
            {researchMetrics.total_participants || 0}
          </div>
        </div>
        <div className="metric-card">
          <h3>Consented Users</h3>
          <div className="metric-value">
            {researchMetrics.consented_users || 0}
          </div>
        </div>
        <div className="metric-card">
          <h3>Data Points Collected</h3>
          <div className="metric-value">{researchMetrics.data_points || 0}</div>
        </div>
        <div className="metric-card">
          <h3>Research Sessions</h3>
          <div className="metric-value">
            {researchMetrics.research_sessions || 0}
          </div>
        </div>
      </div>

      <div className="research-charts">
        <div className="chart-container">
          <h3>Learning Outcomes Achievement</h3>
          <LearningOutcomesChart
            data={researchMetrics.learning_outcomes || []}
          />
        </div>
        <div className="chart-container">
          <h3>User Engagement Patterns</h3>
          <EngagementHeatmapChart
            data={researchMetrics.engagement_heatmap || {}}
          />
        </div>
        <div className="chart-container">
          <h3>User Retention Over Time</h3>
          <RetentionRateChart data={researchMetrics.retention_data || []} />
        </div>
        <div className="chart-container">
          <h3>Gesture Learning Progression</h3>
          <LearningProgressChart
            data={researchMetrics.gesture_progression || []}
          />
        </div>
      </div>

      <div className="research-insights">
        <h3>Research Insights</h3>
        <div className="insights-grid">
          <div className="insight-card">
            <h4>Key Findings</h4>
            <ul>
              {(researchMetrics.key_findings || []).map((finding, index) => (
                <li key={index}>
                  <span className="finding-text">{finding.text}</span>
                  <span className="confidence-level">
                    Confidence: {finding.confidence}%
                  </span>
                </li>
              ))}
            </ul>
          </div>
          <div className="insight-card">
            <h4>Statistical Significance</h4>
            <div className="stats-grid">
              {(researchMetrics.statistical_tests || []).map((test, index) => (
                <div key={index} className="stat-item">
                  <span className="stat-name">{test.name}</span>
                  <span className="stat-value">p = {test.p_value}</span>
                  <span
                    className={`significance ${
                      test.significant ? "significant" : "not-significant"
                    }`}
                  >
                    {test.significant ? "Significant" : "Not Significant"}
                  </span>
                </div>
              ))}
            </div>
          </div>
          <div className="insight-card">
            <h4>Recommendations for Educators</h4>
            <ul>
              {(researchMetrics.educator_recommendations || []).map(
                (rec, index) => (
                  <li key={index}>
                    <span className="recommendation-text">{rec.text}</span>
                    <span className="evidence-level">
                      Evidence: {rec.evidence_level}
                    </span>
                  </li>
                )
              )}
            </ul>
          </div>
        </div>
      </div>

      <div className="privacy-notice">
        <h4>Privacy & Ethics Notice</h4>
        <p>
          All research data is anonymized and aggregated to protect participant
          privacy. Only users who have explicitly consented to research
          participation are included in these analytics. Data collection follows
          institutional review board (IRB) guidelines and applicable privacy
          regulations.
        </p>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
