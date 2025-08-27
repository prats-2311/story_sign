/**
 * Data Export Panel Component
 * Provides data export capabilities for research and analysis
 */

import React, { useState } from "react";
import "./DataExportPanel.css";

const DataExportPanel = ({ analyticsData, dateRange }) => {
  const [exportConfig, setExportConfig] = useState({
    format: "json",
    includeAnonymous: true,
    includePersonalData: false,
    eventTypes: [],
    modules: [],
    aggregationLevel: "raw",
  });
  const [exporting, setExporting] = useState(false);
  const [exportHistory, setExportHistory] = useState([]);

  const availableEventTypes = [
    "practice_session_start",
    "practice_session_end",
    "sentence_attempt",
    "gesture_detected",
    "ai_feedback_received",
    "user_login",
    "user_logout",
    "page_view",
    "feature_used",
    "story_generated",
    "story_completed",
    "collaborative_session",
    "error_occurred",
    "plugin_activated",
  ];

  const availableModules = [
    "asl_world",
    "harmony",
    "reconnect",
    "platform",
    "plugins",
  ];

  const handleExport = async () => {
    setExporting(true);
    try {
      const exportParams = {
        start_date: dateRange.startDate,
        end_date: dateRange.endDate,
        format: exportConfig.format,
        include_anonymous: exportConfig.includeAnonymous,
        include_personal_data: exportConfig.includePersonalData,
        event_types: exportConfig.eventTypes.join(","),
        modules: exportConfig.modules.join(","),
        aggregation_level: exportConfig.aggregationLevel,
      };

      const response = await fetch(
        "/api/v1/analytics/export?" + new URLSearchParams(exportParams),
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("auth_token")}`,
          },
        }
      );

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `analytics_export_${
          new Date().toISOString().split("T")[0]
        }.${exportConfig.format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        // Add to export history
        const exportRecord = {
          id: Date.now(),
          timestamp: new Date().toISOString(),
          format: exportConfig.format,
          dateRange: `${dateRange.startDate} to ${dateRange.endDate}`,
          recordCount: analyticsData?.platform_metrics?.total_events || 0,
          status: "completed",
        };
        setExportHistory((prev) => [exportRecord, ...prev]);
      } else {
        throw new Error("Export failed");
      }
    } catch (error) {
      console.error("Export error:", error);
      alert("Export failed: " + error.message);
    } finally {
      setExporting(false);
    }
  };

  const handleConfigChange = (field, value) => {
    setExportConfig((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleArrayConfigChange = (field, value, checked) => {
    setExportConfig((prev) => ({
      ...prev,
      [field]: checked
        ? [...prev[field], value]
        : prev[field].filter((item) => item !== value),
    }));
  };

  const applyTemplate = (templateType) => {
    const templates = {
      learning_progress: {
        format: "csv",
        includeAnonymous: false,
        includePersonalData: false,
        eventTypes: [
          "practice_session_start",
          "practice_session_end",
          "sentence_attempt",
          "story_completed",
        ],
        modules: ["asl_world"],
        aggregationLevel: "daily",
      },
      engagement_analysis: {
        format: "json",
        includeAnonymous: true,
        includePersonalData: false,
        eventTypes: [
          "page_view",
          "feature_used",
          "user_login",
          "collaborative_session",
        ],
        modules: ["asl_world", "harmony", "reconnect", "platform"],
        aggregationLevel: "hourly",
      },
      performance_metrics: {
        format: "csv",
        includeAnonymous: true,
        includePersonalData: false,
        eventTypes: [
          "gesture_detected",
          "ai_feedback_received",
          "error_occurred",
        ],
        modules: ["asl_world"],
        aggregationLevel: "raw",
      },
      research_dataset: {
        format: "xlsx",
        includeAnonymous: true,
        includePersonalData: false,
        eventTypes: [
          "practice_session_start",
          "practice_session_end",
          "sentence_attempt",
          "gesture_detected",
        ],
        modules: ["asl_world"],
        aggregationLevel: "raw",
      },
    };

    const template = templates[templateType];
    if (template) {
      setExportConfig(template);
    }
  };

  return (
    <div className="data-export-panel">
      <div className="export-configuration">
        <h3>Export Configuration</h3>

        <div className="config-section">
          <h4>Export Format</h4>
          <div className="radio-group">
            <label>
              <input
                type="radio"
                value="json"
                checked={exportConfig.format === "json"}
                onChange={(e) => handleConfigChange("format", e.target.value)}
              />
              JSON
            </label>
            <label>
              <input
                type="radio"
                value="csv"
                checked={exportConfig.format === "csv"}
                onChange={(e) => handleConfigChange("format", e.target.value)}
              />
              CSV
            </label>
            <label>
              <input
                type="radio"
                value="xlsx"
                checked={exportConfig.format === "xlsx"}
                onChange={(e) => handleConfigChange("format", e.target.value)}
              />
              Excel
            </label>
          </div>
        </div>

        <div className="config-section">
          <h4>Privacy Settings</h4>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={exportConfig.includeAnonymous}
              onChange={(e) =>
                handleConfigChange("includeAnonymous", e.target.checked)
              }
            />
            Include Anonymous Data
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={exportConfig.includePersonalData}
              onChange={(e) =>
                handleConfigChange("includePersonalData", e.target.checked)
              }
            />
            Include Personal Data (Requires Special Permission)
          </label>
          <div className="config-section">
            <h4>Event Types</h4>
            <div className="checkbox-grid">
              {availableEventTypes.map((eventType) => (
                <label key={eventType} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={exportConfig.eventTypes.includes(eventType)}
                    onChange={(e) =>
                      handleArrayConfigChange(
                        "eventTypes",
                        eventType,
                        e.target.checked
                      )
                    }
                  />
                  {eventType
                    .replace(/_/g, " ")
                    .replace(/\b\w/g, (l) => l.toUpperCase())}
                </label>
              ))}
            </div>
          </div>

          <div className="config-section">
            <h4>Modules</h4>
            <div className="checkbox-grid">
              {availableModules.map((module) => (
                <label key={module} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={exportConfig.modules.includes(module)}
                    onChange={(e) =>
                      handleArrayConfigChange(
                        "modules",
                        module,
                        e.target.checked
                      )
                    }
                  />
                  {module
                    .replace(/_/g, " ")
                    .replace(/\b\w/g, (l) => l.toUpperCase())}
                </label>
              ))}
            </div>
          </div>

          <div className="config-section">
            <h4>Aggregation Level</h4>
            <select
              value={exportConfig.aggregationLevel}
              onChange={(e) =>
                handleConfigChange("aggregationLevel", e.target.value)
              }
              className="aggregation-select"
            >
              <option value="raw">Raw Events</option>
              <option value="hourly">Hourly Aggregation</option>
              <option value="daily">Daily Aggregation</option>
              <option value="weekly">Weekly Aggregation</option>
              <option value="monthly">Monthly Aggregation</option>
            </select>
          </div>

          <div className="config-section">
            <h4>Report Templates</h4>
            <div className="template-buttons">
              <button
                type="button"
                className="template-button"
                onClick={() => applyTemplate("learning_progress")}
              >
                Learning Progress Report
              </button>
              <button
                type="button"
                className="template-button"
                onClick={() => applyTemplate("engagement_analysis")}
              >
                Engagement Analysis
              </button>
              <button
                type="button"
                className="template-button"
                onClick={() => applyTemplate("performance_metrics")}
              >
                Performance Metrics
              </button>
              <button
                type="button"
                className="template-button"
                onClick={() => applyTemplate("research_dataset")}
              >
                Research Dataset
              </button>
            </div>
          </div>

          <div className="export-actions">
            <button
              className="export-button primary"
              onClick={handleExport}
              disabled={exporting}
            >
              {exporting ? "Exporting..." : "Export Data"}
            </button>
            <button
              className="export-button secondary"
              onClick={() =>
                setExportConfig({
                  format: "json",
                  includeAnonymous: true,
                  includePersonalData: false,
                  eventTypes: [],
                  modules: [],
                  aggregationLevel: "raw",
                })
              }
            >
              Reset Configuration
            </button>
          </div>
        </div>

        <div className="export-history">
          <h3>Export History</h3>
          {exportHistory.length === 0 ? (
            <p className="no-exports">No exports yet</p>
          ) : (
            <div className="export-list">
              {exportHistory.map((export_) => (
                <div key={export_.id} className="export-item">
                  <div className="export-info">
                    <div className="export-timestamp">
                      {new Date(export_.timestamp).toLocaleString()}
                    </div>
                    <div className="export-details">
                      Format: {export_.format.toUpperCase()} | Date Range:{" "}
                      {export_.dateRange} | Records: {export_.recordCount}
                    </div>
                  </div>
                  <div className={`export-status ${export_.status}`}>
                    {export_.status}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="export-info-panel">
          <h3>Export Information</h3>
          <div className="info-grid">
            <div className="info-item">
              <label>Total Events Available:</label>
              <span>{analyticsData?.platform_metrics?.total_events || 0}</span>
            </div>
            <div className="info-item">
              <label>Date Range:</label>
              <span>
                {dateRange.startDate} to {dateRange.endDate}
              </span>
            </div>
            <div className="info-item">
              <label>Estimated File Size:</label>
              <span>
                {calculateEstimatedSize(
                  analyticsData?.platform_metrics?.total_events || 0,
                  exportConfig.format
                )}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Helper function to calculate estimated file size
const calculateEstimatedSize = (eventCount, format) => {
  const avgEventSize = {
    json: 500, // bytes per event
    csv: 200, // bytes per event
    xlsx: 150, // bytes per event
  };

  const totalBytes = eventCount * (avgEventSize[format] || 300);

  if (totalBytes < 1024) return `${totalBytes} B`;
  if (totalBytes < 1024 * 1024) return `${(totalBytes / 1024).toFixed(1)} KB`;
  if (totalBytes < 1024 * 1024 * 1024)
    return `${(totalBytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(totalBytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
};

export default DataExportPanel;
