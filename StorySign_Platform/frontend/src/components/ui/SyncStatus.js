/**
 * Sync Status Component
 * Displays cross-platform synchronization status and controls
 */

import React, { useState, useEffect } from "react";
import {
  useSync,
  useSyncOptimization,
  useConflictResolution,
} from "../../hooks/useSync";
import "./SyncStatus.css";

const SyncStatus = ({
  showDetails = false,
  showControls = true,
  onConflictResolve = null,
}) => {
  const {
    syncStatus,
    conflicts,
    syncMetrics,
    lastSyncTime,
    createSession,
    processOfflineChanges,
    refreshStatus,
    refreshMetrics,
    isOnline,
    hasActiveSession,
    syncInProgress,
    hasOfflineChanges,
    hasConflicts,
  } = useSync();

  const {
    bandwidthProfile,
    compressionEnabled,
    optimizeForBandwidth,
    getOptimizationRecommendations,
  } = useSyncOptimization();

  const { pendingConflicts, resolveConflictBatch, getConflictSummary } =
    useConflictResolution();

  const [showOptimizations, setShowOptimizations] = useState(false);
  const [showConflictDetails, setShowConflictDetails] = useState(false);
  const [recommendations, setRecommendations] = useState([]);

  useEffect(() => {
    const recs = getOptimizationRecommendations();
    setRecommendations(recs);
  }, [getOptimizationRecommendations, syncStatus]);

  const handleCreateSession = async () => {
    try {
      await createSession();
      refreshStatus();
    } catch (error) {
      console.error("Failed to create session:", error);
    }
  };

  const handleProcessOfflineChanges = async () => {
    try {
      await processOfflineChanges();
      refreshStatus();
    } catch (error) {
      console.error("Failed to process offline changes:", error);
    }
  };

  const handleResolveAllConflicts = async (strategy = "latest_wins") => {
    try {
      await resolveConflictBatch(pendingConflicts, strategy);
      if (onConflictResolve) {
        onConflictResolve();
      }
    } catch (error) {
      console.error("Failed to resolve conflicts:", error);
    }
  };

  const getStatusIcon = () => {
    if (!isOnline) return "🔴";
    if (syncInProgress) return "🔄";
    if (hasConflicts) return "⚠️";
    if (hasOfflineChanges) return "📤";
    if (hasActiveSession) return "🟢";
    return "⚪";
  };

  const getStatusText = () => {
    if (!isOnline) return "Offline";
    if (syncInProgress) return "Syncing...";
    if (hasConflicts) return "Conflicts detected";
    if (hasOfflineChanges) return "Offline changes pending";
    if (hasActiveSession) return "Connected";
    return "Not connected";
  };

  const formatLastSync = () => {
    if (!lastSyncTime) return "Never";

    const now = new Date();
    const diff = now - lastSyncTime;
    const minutes = Math.floor(diff / 60000);

    if (minutes < 1) return "Just now";
    if (minutes < 60) return `${minutes}m ago`;

    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;

    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  const conflictSummary = getConflictSummary();

  return (
    <div className="sync-status">
      <div className="sync-status-header">
        <div className="sync-status-indicator">
          <span className="sync-icon">{getStatusIcon()}</span>
          <span className="sync-text">{getStatusText()}</span>
        </div>

        {showControls && (
          <div className="sync-controls">
            {!hasActiveSession && isOnline && (
              <button
                className="sync-button primary"
                onClick={handleCreateSession}
              >
                Connect
              </button>
            )}

            {hasOfflineChanges && (
              <button
                className="sync-button secondary"
                onClick={handleProcessOfflineChanges}
                disabled={syncInProgress}
              >
                Sync Changes ({syncStatus.offlineChangesCount})
              </button>
            )}

            {hasConflicts && (
              <button
                className="sync-button warning"
                onClick={() => setShowConflictDetails(!showConflictDetails)}
              >
                Resolve Conflicts ({conflicts.length})
              </button>
            )}

            <button
              className="sync-button icon"
              onClick={refreshStatus}
              title="Refresh status"
            >
              🔄
            </button>
          </div>
        )}
      </div>

      {showDetails && (
        <div className="sync-details">
          <div className="sync-info-grid">
            <div className="sync-info-item">
              <label>Status:</label>
              <span className={`status ${isOnline ? "online" : "offline"}`}>
                {isOnline ? "Online" : "Offline"}
              </span>
            </div>

            <div className="sync-info-item">
              <label>Last Sync:</label>
              <span>{formatLastSync()}</span>
            </div>

            <div className="sync-info-item">
              <label>Device:</label>
              <span>{syncStatus.deviceInfo?.platform || "Unknown"}</span>
            </div>

            <div className="sync-info-item">
              <label>Bandwidth:</label>
              <span className={`bandwidth ${bandwidthProfile}`}>
                {bandwidthProfile}
                {compressionEnabled && " (compressed)"}
              </span>
            </div>

            <div className="sync-info-item">
              <label>Pending:</label>
              <span>
                {syncStatus.offlineChangesCount} changes,{" "}
                {syncStatus.queuedOperationsCount} operations
              </span>
            </div>

            <div className="sync-info-item">
              <label>Conflicts:</label>
              <span className={hasConflicts ? "warning" : ""}>
                {conflictSummary.total}
              </span>
            </div>
          </div>

          {syncMetrics && (
            <div className="sync-metrics">
              <h4>Sync Metrics</h4>
              <div className="metrics-grid">
                <div className="metric">
                  <label>Success Rate:</label>
                  <span>
                    {Math.round(
                      (syncMetrics.successful_syncs / syncMetrics.total_syncs) *
                        100
                    )}
                    %
                  </span>
                </div>
                <div className="metric">
                  <label>Avg Sync Time:</label>
                  <span>{syncMetrics.average_sync_time_ms}ms</span>
                </div>
                <div className="metric">
                  <label>Data Synced:</label>
                  <span>
                    {Math.round(syncMetrics.total_data_synced_bytes / 1024)}KB
                  </span>
                </div>
                <div className="metric">
                  <label>Conflicts Resolved:</label>
                  <span>{syncMetrics.conflicts_resolved}</span>
                </div>
              </div>
            </div>
          )}

          {recommendations.length > 0 && (
            <div className="sync-recommendations">
              <h4>Optimization Recommendations</h4>
              {recommendations.map((rec, index) => (
                <div key={index} className="recommendation">
                  <span className="rec-message">{rec.message}</span>
                  <button className="rec-action" onClick={rec.action}>
                    Apply
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {showConflictDetails && hasConflicts && (
        <div className="conflict-details">
          <div className="conflict-header">
            <h4>Synchronization Conflicts</h4>
            <div className="conflict-actions">
              <button
                className="resolve-button server"
                onClick={() => handleResolveAllConflicts("server_wins")}
              >
                Keep Server Version
              </button>
              <button
                className="resolve-button client"
                onClick={() => handleResolveAllConflicts("client_wins")}
              >
                Keep Local Version
              </button>
              <button
                className="resolve-button merge"
                onClick={() => handleResolveAllConflicts("merge")}
              >
                Merge Changes
              </button>
            </div>
          </div>

          <div className="conflict-list">
            {conflicts.map((conflict, index) => (
              <div key={index} className="conflict-item">
                <div className="conflict-field">
                  <strong>{conflict.field_name}</strong>
                  <span className="conflict-type">
                    ({conflict.conflict_type})
                  </span>
                </div>

                <div className="conflict-values">
                  <div className="value-comparison">
                    <div className="server-value">
                      <label>Server:</label>
                      <pre>
                        {JSON.stringify(conflict.server_value, null, 2)}
                      </pre>
                    </div>
                    <div className="client-value">
                      <label>Local:</label>
                      <pre>
                        {JSON.stringify(conflict.client_value, null, 2)}
                      </pre>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {showOptimizations && (
        <div className="optimization-panel">
          <h4>Sync Optimization</h4>

          <div className="optimization-controls">
            <div className="bandwidth-selector">
              <label>Bandwidth Profile:</label>
              <select
                value={bandwidthProfile}
                onChange={(e) => optimizeForBandwidth(e.target.value)}
              >
                <option value="high">High (WiFi/Ethernet)</option>
                <option value="medium">Medium (4G/LTE)</option>
                <option value="low">Low (3G/2G)</option>
              </select>
            </div>

            <div className="compression-toggle">
              <label>
                <input
                  type="checkbox"
                  checked={compressionEnabled}
                  onChange={(e) => {
                    // This would update compression settings
                    console.log("Compression toggled:", e.target.checked);
                  }}
                />
                Enable data compression
              </label>
            </div>
          </div>

          <div className="bandwidth-info">
            <p>
              Current profile: <strong>{bandwidthProfile}</strong>
            </p>
            <p>
              {bandwidthProfile === "low" &&
                "Optimized for slow connections with data compression and reduced precision."}
              {bandwidthProfile === "medium" &&
                "Balanced optimization for mobile networks."}
              {bandwidthProfile === "high" &&
                "Full quality sync for fast connections."}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default SyncStatus;
