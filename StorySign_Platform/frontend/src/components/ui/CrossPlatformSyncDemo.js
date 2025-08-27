/**
 * Cross-Platform Synchronization Demo Component
 * Demonstrates the synchronization functionality across devices
 */

import React, { useState, useEffect } from "react";
import { useSync } from "../../hooks/useSync";
import SyncStatus from "./SyncStatus";
import "./CrossPlatformSyncDemo.css";

const CrossPlatformSyncDemo = () => {
  const {
    syncStatus,
    createSession,
    syncData,
    queueOperation,
    processOfflineChanges,
    isOnline,
    hasActiveSession,
    syncInProgress,
    hasOfflineChanges,
  } = useSync({
    autoSync: true,
    autoSyncInterval: 30000, // 30 seconds
    onRemoteUpdate: (data) => {
      console.log("Remote update received:", data);
      setRemoteUpdates((prev) => [...prev, { ...data, timestamp: new Date() }]);
    },
  });

  const [demoData, setDemoData] = useState({
    currentStory: "story-1",
    progress: {
      score: 85,
      completedSentences: 3,
      totalSentences: 5,
    },
    preferences: {
      difficulty: "medium",
      feedbackLevel: "detailed",
    },
  });

  const [syncLog, setSyncLog] = useState([]);
  const [remoteUpdates, setRemoteUpdates] = useState([]);
  const [simulatedDevices, setSimulatedDevices] = useState([
    { id: "web-1", name: "Desktop Browser", platform: "web", active: false },
    { id: "mobile-1", name: "Mobile App", platform: "android", active: false },
    { id: "tablet-1", name: "Tablet", platform: "ios", active: false },
  ]);

  const addToSyncLog = (message, type = "info") => {
    setSyncLog((prev) => [
      ...prev,
      {
        id: Date.now(),
        message,
        type,
        timestamp: new Date().toLocaleTimeString(),
      },
    ]);
  };

  const handleCreateSession = async () => {
    try {
      addToSyncLog("Creating device session...", "info");

      const session = await createSession({
        demo_mode: true,
        initial_data: demoData,
      });

      addToSyncLog(`Session created: ${session.session_id}`, "success");

      // Simulate activating current device
      setSimulatedDevices((prev) =>
        prev.map((device) =>
          device.id === "web-1" ? { ...device, active: true } : device
        )
      );
    } catch (error) {
      addToSyncLog(`Failed to create session: ${error.message}`, "error");
    }
  };

  const handleSyncData = async () => {
    try {
      addToSyncLog("Synchronizing data...", "info");

      const result = await syncData(demoData);

      if (result.conflicts && result.conflicts.length > 0) {
        addToSyncLog(
          `Sync completed with ${result.conflicts.length} conflicts`,
          "warning"
        );
      } else {
        addToSyncLog("Data synchronized successfully", "success");
      }
    } catch (error) {
      addToSyncLog(`Sync failed: ${error.message}`, "error");
    }
  };

  const handleQueueOperation = async (type, data) => {
    try {
      const operationId = await queueOperation(type, data, 1);
      addToSyncLog(`Queued ${type} operation: ${operationId}`, "info");
    } catch (error) {
      addToSyncLog(`Failed to queue operation: ${error.message}`, "error");
    }
  };

  const simulateOfflineChanges = () => {
    const offlineChanges = [
      {
        type: "progress_update",
        data: { score: 92, completedSentences: 4 },
        timestamp: new Date().toISOString(),
      },
      {
        type: "preference_change",
        data: { difficulty: "hard" },
        timestamp: new Date().toISOString(),
      },
    ];

    // Update local data to simulate offline changes
    setDemoData((prev) => ({
      ...prev,
      progress: { ...prev.progress, score: 92, completedSentences: 4 },
      preferences: { ...prev.preferences, difficulty: "hard" },
    }));

    addToSyncLog(`Simulated ${offlineChanges.length} offline changes`, "info");
  };

  const simulateDeviceActivity = (deviceId) => {
    setSimulatedDevices((prev) =>
      prev.map((device) =>
        device.id === deviceId ? { ...device, active: !device.active } : device
      )
    );

    const device = simulatedDevices.find((d) => d.id === deviceId);
    if (device) {
      addToSyncLog(
        `${device.name} ${device.active ? "disconnected" : "connected"}`,
        "info"
      );
    }
  };

  const simulateConflict = () => {
    // Simulate a conflict by updating data that might conflict with server
    const conflictingData = {
      ...demoData,
      currentStory: "story-2", // Different from what might be on server
      progress: { ...demoData.progress, score: 78 }, // Lower score that might conflict
    };

    setDemoData(conflictingData);
    addToSyncLog("Simulated conflicting data changes", "warning");
  };

  const updateDemoData = (field, value) => {
    setDemoData((prev) => ({
      ...prev,
      [field]: typeof value === "object" ? { ...prev[field], ...value } : value,
    }));
  };

  return (
    <div className="cross-platform-sync-demo">
      <div className="demo-header">
        <h2>Cross-Platform Synchronization Demo</h2>
        <p>
          This demo shows how data synchronizes across different devices and
          platforms, handles offline changes, and resolves conflicts.
        </p>
      </div>

      <div className="demo-content">
        {/* Sync Status */}
        <div className="demo-section">
          <h3>Synchronization Status</h3>
          <SyncStatus showDetails={true} showControls={true} />
        </div>

        {/* Demo Controls */}
        <div className="demo-section">
          <h3>Demo Controls</h3>
          <div className="demo-controls">
            <button
              onClick={handleCreateSession}
              disabled={hasActiveSession}
              className="demo-button primary"
            >
              Create Session
            </button>

            <button
              onClick={handleSyncData}
              disabled={!hasActiveSession || syncInProgress}
              className="demo-button secondary"
            >
              Sync Data
            </button>

            <button
              onClick={simulateOfflineChanges}
              className="demo-button warning"
            >
              Simulate Offline Changes
            </button>

            <button onClick={simulateConflict} className="demo-button danger">
              Simulate Conflict
            </button>
          </div>
        </div>

        {/* Current Data */}
        <div className="demo-section">
          <h3>Current Data</h3>
          <div className="data-editor">
            <div className="data-field">
              <label>Current Story:</label>
              <select
                value={demoData.currentStory}
                onChange={(e) => updateDemoData("currentStory", e.target.value)}
              >
                <option value="story-1">Story 1: Hello World</option>
                <option value="story-2">Story 2: My Family</option>
                <option value="story-3">Story 3: Daily Routine</option>
              </select>
            </div>

            <div className="data-field">
              <label>Score:</label>
              <input
                type="number"
                value={demoData.progress.score}
                onChange={(e) =>
                  updateDemoData("progress", {
                    score: parseInt(e.target.value),
                  })
                }
                min="0"
                max="100"
              />
            </div>

            <div className="data-field">
              <label>Completed Sentences:</label>
              <input
                type="number"
                value={demoData.progress.completedSentences}
                onChange={(e) =>
                  updateDemoData("progress", {
                    completedSentences: parseInt(e.target.value),
                  })
                }
                min="0"
                max="10"
              />
            </div>

            <div className="data-field">
              <label>Difficulty:</label>
              <select
                value={demoData.preferences.difficulty}
                onChange={(e) =>
                  updateDemoData("preferences", { difficulty: e.target.value })
                }
              >
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>
          </div>
        </div>

        {/* Simulated Devices */}
        <div className="demo-section">
          <h3>Simulated Devices</h3>
          <div className="devices-grid">
            {simulatedDevices.map((device) => (
              <div
                key={device.id}
                className={`device-card ${
                  device.active ? "active" : "inactive"
                }`}
                onClick={() => simulateDeviceActivity(device.id)}
              >
                <div className="device-icon">
                  {device.platform === "web" && "💻"}
                  {device.platform === "android" && "📱"}
                  {device.platform === "ios" && "📱"}
                </div>
                <div className="device-info">
                  <div className="device-name">{device.name}</div>
                  <div className="device-platform">{device.platform}</div>
                  <div
                    className={`device-status ${
                      device.active ? "online" : "offline"
                    }`}
                  >
                    {device.active ? "Online" : "Offline"}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Sync Operations */}
        <div className="demo-section">
          <h3>Queue Operations</h3>
          <div className="operation-controls">
            <button
              onClick={() =>
                handleQueueOperation("practice_session", {
                  sessionId: "demo-session",
                  score: demoData.progress.score,
                })
              }
              className="operation-button"
            >
              Queue Practice Session
            </button>

            <button
              onClick={() =>
                handleQueueOperation("progress_update", {
                  progress: demoData.progress,
                })
              }
              className="operation-button"
            >
              Queue Progress Update
            </button>

            <button
              onClick={() =>
                handleQueueOperation("preference_sync", {
                  preferences: demoData.preferences,
                })
              }
              className="operation-button"
            >
              Queue Preferences
            </button>
          </div>
        </div>

        {/* Sync Log */}
        <div className="demo-section">
          <h3>Synchronization Log</h3>
          <div className="sync-log">
            {syncLog.length === 0 ? (
              <div className="log-empty">No sync activities yet</div>
            ) : (
              syncLog.slice(-10).map((entry) => (
                <div key={entry.id} className={`log-entry ${entry.type}`}>
                  <span className="log-time">{entry.timestamp}</span>
                  <span className="log-message">{entry.message}</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Remote Updates */}
        {remoteUpdates.length > 0 && (
          <div className="demo-section">
            <h3>Remote Updates</h3>
            <div className="remote-updates">
              {remoteUpdates.slice(-5).map((update, index) => (
                <div key={index} className="update-entry">
                  <div className="update-time">
                    {update.timestamp.toLocaleTimeString()}
                  </div>
                  <div className="update-data">
                    <pre>{JSON.stringify(update, null, 2)}</pre>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CrossPlatformSyncDemo;
