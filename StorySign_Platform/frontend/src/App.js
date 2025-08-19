import React, { useState } from "react";
import "./App.css";
import WebcamCapture from "./WebcamCapture";

function App() {
  const [backendMessage, setBackendMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState("not_tested");
  const [webcamActive, setWebcamActive] = useState(false);
  const [webcamError, setWebcamError] = useState("");

  const testBackendConnection = async () => {
    setIsLoading(true);
    setConnectionStatus("testing");

    try {
      const response = await fetch("http://localhost:8000/", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        const data = await response.json();
        setBackendMessage(data.message || "Backend connected successfully!");
        setConnectionStatus("connected");
      } else {
        setBackendMessage(
          `Backend error: ${response.status} ${response.statusText}`
        );
        setConnectionStatus("error");
      }
    } catch (error) {
      setBackendMessage(`Connection failed: ${error.message}`);
      setConnectionStatus("error");
    } finally {
      setIsLoading(false);
    }
  };

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

  const handleFrameCapture = (frameData) => {
    // This will be used in future tasks for sending frames to backend
    console.log("Frame captured:", {
      timestamp: frameData.timestamp,
      frameNumber: frameData.frameNumber,
      size: `${frameData.width}x${frameData.height}`,
    });
  };

  const handleWebcamError = (error) => {
    setWebcamError(error);
  };

  const toggleWebcam = () => {
    setWebcamActive(!webcamActive);
    if (webcamActive) {
      setWebcamError("");
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>StorySign</h1>
        <p>Real-time American Sign Language Recognition System</p>
      </header>
      <main className="App-main">
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
                <p className={`message ${connectionStatus}`}>
                  {backendMessage}
                </p>
              ) : (
                <p className="message placeholder">
                  Click "Test Backend" to verify connectivity
                </p>
              )}
            </div>
          </div>

          <div className="video-area">
            <h3>Video Feed</h3>
            <div className="video-controls">
              <button className="webcam-toggle-btn" onClick={toggleWebcam}>
                {webcamActive ? "Stop Webcam" : "Start Webcam"}
              </button>
            </div>
            {webcamError && (
              <div className="webcam-error">
                <p className="error-text">{webcamError}</p>
              </div>
            )}
            <WebcamCapture
              isActive={webcamActive}
              onFrameCapture={handleFrameCapture}
              onError={handleWebcamError}
            />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
