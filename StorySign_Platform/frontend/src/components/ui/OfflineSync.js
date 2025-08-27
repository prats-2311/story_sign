import React, { useState, useEffect } from "react";
import { useDeviceCapabilities } from "../../hooks/useResponsive";
import pwaService from "../../services/PWAService";
import "./OfflineSync.css";

const OfflineSync = () => {
  const { isOnline } = useDeviceCapabilities();
  const [syncStatus, setSyncStatus] = useState("idle");
  const [pendingData, setPendingData] = useState([]);
  const [lastSyncTime, setLastSyncTime] = useState(null);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    // Listen for PWA events
    const handleOnline = () => {
      console.log("Device back online, triggering sync...");
      triggerSync();
    };

    const handleOffline = () => {
      console.log("Device went offline");
      setSyncStatus("offline");
    };

    const handlePWAOnline = () => handleOnline();
    const handlePWAOffline = () => handleOffline();

    window.addEventListener("pwa-online", handlePWAOnline);
    window.addEventListener("pwa-offline", handlePWAOffline);

    // Check for pending data on mount
    checkPendingData();

    return () => {
      window.removeEventListener("pwa-online", handlePWAOnline);
      window.removeEventListener("pwa-offline", handlePWAOffline);
    };
  }, []);

  const checkPendingData = async () => {
    try {
      const practiceData =
        (await pwaService.getOfflineData("practice_sessions")) || [];
      const analyticsData =
        (await pwaService.getOfflineData("analytics_events")) || [];

      const allPendingData = [
        ...practiceData.map((item) => ({ ...item, type: "practice" })),
        ...analyticsData.map((item) => ({ ...item, type: "analytics" })),
      ];

      setPendingData(allPendingData);
    } catch (error) {
      console.error("Failed to check pending data:", error);
    }
  };

  const triggerSync = async () => {
    if (!isOnline || syncStatus === "syncing") return;

    setSyncStatus("syncing");

    try {
      // Trigger background sync through service worker
      await pwaService.triggerBackgroundSync();

      // Simulate sync process (in real implementation, this would be handled by service worker)
      await new Promise((resolve) => setTimeout(resolve, 2000));

      // Check if sync was successful
      await checkPendingData();

      setSyncStatus("success");
      setLastSyncTime(new Date());

      // Reset status after a delay
      setTimeout(() => {
        setSyncStatus("idle");
      }, 3000);
    } catch (error) {
      console.error("Sync failed:", error);
      setSyncStatus("error");

      setTimeout(() => {
        setSyncStatus("idle");
      }, 5000);
    }
  };

  const storePracticeData = async (sessionData) => {
    try {
      const existingData =
        (await pwaService.getOfflineData("practice_sessions")) || [];
      const newData = [
        ...existingData,
        {
          id: Date.now().toString(),
          ...sessionData,
          timestamp: new Date().toISOString(),
          synced: false,
        },
      ];

      await pwaService.storeOfflineData("practice_sessions", newData);
      await checkPendingData();

      console.log("Practice data stored for offline sync");
    } catch (error) {
      console.error("Failed to store practice data:", error);
    }
  };

  const storeAnalyticsData = async (eventData) => {
    try {
      const existingData =
        (await pwaService.getOfflineData("analytics_events")) || [];
      const newData = [
        ...existingData,
        {
          id: Date.now().toString(),
          ...eventData,
          timestamp: new Date().toISOString(),
          synced: false,
        },
      ];

      await pwaService.storeOfflineData("analytics_events", newData);
      await checkPendingData();

      console.log("Analytics data stored for offline sync");
    } catch (error) {
      console.error("Failed to store analytics data:", error);
    }
  };

  const clearSyncedData = async () => {
    try {
      await pwaService.storeOfflineData("practice_sessions", []);
      await pwaService.storeOfflineData("analytics_events", []);
      setPendingData([]);

      console.log("Synced data cleared");
    } catch (error) {
      console.error("Failed to clear synced data:", error);
    }
  };

  const getSyncStatusIcon = () => {
    switch (syncStatus) {
      case "syncing":
        return "🔄";
      case "success":
        return "✅";
      case "error":
        return "❌";
      case "offline":
        return "📡";
      default:
        return isOnline ? "🟢" : "🔴";
    }
  };

  const getSyncStatusText = () => {
    switch (syncStatus) {
      case "syncing":
        return "Syncing data...";
      case "success":
        return "Sync completed";
      case "error":
        return "Sync failed";
      case "offline":
        return "Offline mode";
      default:
        return isOnline ? "Online" : "Offline";
    }
  };

  // Expose methods for other components to use
  React.useImperativeHandle(
    React.forwardRef(() => null),
    () => ({
      storePracticeData,
      storeAnalyticsData,
      triggerSync,
    })
  );

  if (pendingData.length === 0 && isOnline && syncStatus === "idle") {
    return null; // Don't show component when everything is synced
  }

  return (
    <div className="offline-sync">
      <div
        className={`sync-indicator ${syncStatus}`}
        onClick={() => setShowDetails(!showDetails)}
      >
        <span className="sync-icon">{getSyncStatusIcon()}</span>
        <span className="sync-text">{getSyncStatusText()}</span>
        {pendingData.length > 0 && (
          <span className="pending-count">{pendingData.length}</span>
        )}
      </div>

      {showDetails && (
        <div className="sync-details">
          <div className="sync-header">
            <h4>Data Synchronization</h4>
            <button
              className="close-details"
              onClick={() => setShowDetails(false)}
            >
              ✕
            </button>
          </div>

          <div className="sync-info">
            <div className="status-row">
              <span>Status:</span>
              <span className={`status ${syncStatus}`}>
                {getSyncStatusText()}
              </span>
            </div>

            <div className="status-row">
              <span>Connection:</span>
              <span className={`status ${isOnline ? "online" : "offline"}`}>
                {isOnline ? "Online" : "Offline"}
              </span>
            </div>

            {lastSyncTime && (
              <div className="status-row">
                <span>Last sync:</span>
                <span>{lastSyncTime.toLocaleTimeString()}</span>
              </div>
            )}

            {pendingData.length > 0 && (
              <div className="status-row">
                <span>Pending items:</span>
                <span>{pendingData.length}</span>
              </div>
            )}
          </div>

          {pendingData.length > 0 && (
            <div className="pending-data">
              <h5>Pending Data:</h5>
              <ul>
                {pendingData.slice(0, 5).map((item, index) => (
                  <li key={index} className={`pending-item ${item.type}`}>
                    <span className="item-type">
                      {item.type === "practice" ? "📚" : "📊"}
                    </span>
                    <span className="item-description">
                      {item.type === "practice"
                        ? "Practice Session"
                        : "Analytics Event"}
                    </span>
                    <span className="item-time">
                      {new Date(item.timestamp).toLocaleTimeString()}
                    </span>
                  </li>
                ))}
                {pendingData.length > 5 && (
                  <li className="more-items">
                    +{pendingData.length - 5} more items
                  </li>
                )}
              </ul>
            </div>
          )}

          <div className="sync-actions">
            {isOnline && pendingData.length > 0 && (
              <button
                className="sync-button"
                onClick={triggerSync}
                disabled={syncStatus === "syncing"}
              >
                {syncStatus === "syncing" ? "Syncing..." : "Sync Now"}
              </button>
            )}

            {pendingData.length > 0 && (
              <button className="clear-button" onClick={clearSyncedData}>
                Clear Data
              </button>
            )}
          </div>

          {!isOnline && (
            <div className="offline-notice">
              <p>
                📡 You're currently offline. Data will be automatically synced
                when you reconnect to the internet.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default OfflineSync;
