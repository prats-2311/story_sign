import React, { useState, useRef } from "react";
import "./App.css";
import WebcamCapture from "./WebcamCapture";
import VideoStreamingClient from "./VideoStreamingClient";

function App() {
  const [backendMessage, setBackendMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState("not_tested");
  const [webcamActive, setWebcamActive] = useState(false);
  const [webcamError, setWebcamError] = useState("");
  const [streamingActive, setStreamingActive] = useState(false);
  const [processedFrameData, setProcessedFrameData] = useState(null);

  const videoStreamingRef = useRef(null);

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
    // Send frame to WebSocket if streaming is active
    if (streamingActive && videoStreamingRef.current) {
      videoStreamingRef.current.sendFrame(frameData);
    }

    console.log("Frame captured:", {
      timestamp: frameData.timestamp,
      frameNumber: frameData.frameNumber,
      size: `${frameData.width}x${frameData.height}`,
    });
  };

  const handleStreamingConnectionChange = (status) => {
    console.log("Streaming connection status:", status);
  };

  const handleProcessedFrame = (message) => {
    setProcessedFrameData(message);
    console.log("Processed frame received:", {
      frameNumber: message.metadata?.frame_number,
      processingTime: message.metadata?.processing_time_ms,
      landmarks: message.metadata?.landmarks_detected,
    });
  };

  const handleStreamingError = (error) => {
    console.error("Streaming error:", error);
    setBackendMessage(`Streaming error: ${error}`);
    setConnectionStatus("error");
  };

  const handleWebcamError = (error) => {
    setWebcamError(error);
  };

  const toggleWebcam = () => {
    setWebcamActive(!webcamActive);
    if (webcamActive) {
      setWebcamError("");
      // Also stop streaming when stopping webcam
      setStreamingActive(false);
    }
  };

  const toggleStreaming = () => {
    if (!webcamActive) {
      setBackendMessage("Please start webcam first before enabling streaming");
      return;
    }
    setStreamingActive(!streamingActive);
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
              </div>
            )}
            <WebcamCapture
              isActive={webcamActive}
              onFrameCapture={handleFrameCapture}
              onError={handleWebcamError}
            />
          </div>

          <div className="streaming-area">
            <h3>Video Streaming</h3>
            <VideoStreamingClient
              ref={videoStreamingRef}
              isActive={streamingActive}
              onConnectionChange={handleStreamingConnectionChange}
              onProcessedFrame={handleProcessedFrame}
              onError={handleStreamingError}
            />
            {processedFrameData && (
              <div className="processed-frame-info">
                <h4>Latest Processed Frame</h4>
                <p>Frame #{processedFrameData.metadata?.frame_number}</p>
                <p>
                  Processing Time:{" "}
                  {processedFrameData.metadata?.processing_time_ms}ms
                </p>
                <p>
                  Landmarks:{" "}
                  {JSON.stringify(
                    processedFrameData.metadata?.landmarks_detected
                  )}
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
