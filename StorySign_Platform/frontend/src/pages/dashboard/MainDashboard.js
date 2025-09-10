import React from "react";

const MainDashboard = ({
  backendMessage,
  isLoading,
  connectionStatus,
  webcamActive,
  webcamError,
  streamingActive,
  streamingError,
  showTroubleshooting,
  testBackendConnection,
  toggleWebcam,
  toggleStreaming,
  retryWebcam,
  retryStreaming,
  onNavigateToASLWorld,
}) => {
  const getStatusColor = () => {
    switch (connectionStatus) {
      case "connected":
        return "#4CAF50";
      case "error":
        return "#f44336";
      case "testing":
        return "#ff9800";
      default:
        return "#9e9e9e";
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case "connected":
        return "Connected";
      case "error":
        return "Connection Failed";
      case "testing":
        return "Testing...";
      default:
        return "Not Tested";
    }
  };

  return (
    <div className="control-panel">
      <div className="connection-section">
        <h2>Backend Connectivity</h2>
        <div className="status-indicator">
          <span
            className="status-dot"
            style={{ backgroundColor: getStatusColor() }}
          ></span>
          <span className="status-text">{getStatusText()}</span>
        </div>
        <button
          className="test-backend-btn"
          onClick={testBackendConnection}
          disabled={isLoading}
        >
          {isLoading ? "Testing..." : "Test Backend"}
        </button>
      </div>

      <div className="message-area">
        <h3>System Messages</h3>
        <div className="message-display">
          {backendMessage ? (
            <p className={`message ${connectionStatus}`}>{backendMessage}</p>
          ) : (
            <p className="message placeholder">
              Click "Test Backend" to verify connectivity
            </p>
          )}
        </div>

        {showTroubleshooting && connectionStatus === "error" && (
          <div className="troubleshooting-panel">
            <h4>Troubleshooting Steps:</h4>
            <ul>
              <li>
                Ensure the backend server is running:{" "}
                <code>python main.py</code>
              </li>
              <li>Check that the backend is accessible and running</li>
              <li>Verify no firewall is blocking the connection</li>
              <li>Check the backend console for error messages</li>
              <li>Try restarting the backend server</li>
            </ul>
            <button
              className="retry-btn"
              onClick={testBackendConnection}
              disabled={isLoading}
            >
              Retry Connection
            </button>
          </div>
        )}
      </div>

      <div className="video-area">
        <h3>Video Feed</h3>
        <div className="video-controls">
          <button className="webcam-toggle-btn" onClick={toggleWebcam}>
            {webcamActive ? "Stop Webcam" : "Start Webcam"}
          </button>
          <button
            className="streaming-toggle-btn"
            onClick={toggleStreaming}
            disabled={!webcamActive}
          >
            {streamingActive ? "Stop Streaming" : "Start Streaming"}
          </button>
        </div>
        {webcamError && (
          <div className="webcam-error">
            <p className="error-text">{webcamError}</p>
            <div className="error-actions">
              <button className="retry-btn" onClick={retryWebcam}>
                Retry Webcam
              </button>
              <div className="error-help">
                <p>Common solutions:</p>
                <ul>
                  <li>Check camera permissions in browser settings</li>
                  <li>Close other applications using the camera</li>
                  <li>Try refreshing the page</li>
                  <li>Ensure camera is properly connected</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ASL World Navigation Button */}
      <div className="asl-world-toggle">
        <button
          className="asl-world-toggle-btn"
          onClick={onNavigateToASLWorld}
          disabled={connectionStatus !== "connected"}
        >
          Enter ASL World
        </button>
        {connectionStatus !== "connected" && (
          <p className="navigation-hint">
            Connect to backend first to access ASL World
          </p>
        )}
      </div>

      {/* Platform Shell Demo Section */}
      <div className="platform-demo-section">
        <h3>Platform Shell Features</h3>
        <p>The new Platform Shell provides:</p>
        <ul>
          <li>✅ Global navigation with module switching</li>
          <li>✅ Theme management (Light, Dark, High Contrast)</li>
          <li>✅ Notification system for cross-module communication</li>
          <li>✅ Accessibility settings and controls</li>
          <li>✅ User authentication placeholders</li>
          <li>✅ Responsive sidebar with module status</li>
        </ul>
        <p>
          <strong>Navigation:</strong> Use the sidebar to switch between
          modules. ASL World is fully functional, while Harmony and Reconnect
          show "Coming Soon" status.
        </p>
        <p>
          <strong>Themes:</strong> Click the 🎨 icon in the header to switch
          themes.
        </p>
        <p>
          <strong>Notifications:</strong> The system will show notifications in
          the top-right corner.
        </p>
        <div style={{ marginTop: "15px" }}>
          <a
            href="/platform-demo"
            style={{
              color: "#1976D2",
              textDecoration: "none",
              fontWeight: "bold",
              padding: "8px 16px",
              border: "2px solid #1976D2",
              borderRadius: "4px",
              display: "inline-block",
              transition: "all 0.2s ease",
            }}
            onMouseOver={(e) => {
              e.target.style.backgroundColor = "#1976D2";
              e.target.style.color = "white";
            }}
            onMouseOut={(e) => {
              e.target.style.backgroundColor = "transparent";
              e.target.style.color = "#1976D2";
            }}
          >
            🧪 Test Platform Shell Features
          </a>
        </div>
      </div>
    </div>
  );
};

export default MainDashboard;
