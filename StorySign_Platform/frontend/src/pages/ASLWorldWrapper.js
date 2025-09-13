import React, { useState, useRef, useCallback } from "react";
import { useBackend } from "../contexts/BackendContext";
import ASLWorldPage from "./ASLWorldPage";

const ASLWorldWrapper = () => {
  const { connectionStatus, testBackendConnection } = useBackend();

  // Video streaming state
  const [webcamActive, setWebcamActive] = useState(false);
  const [streamingActive, setStreamingActive] = useState(false);
  const [streamingConnectionStatus, setStreamingConnectionStatus] =
    useState("disconnected");
  const [processedFrameData, setProcessedFrameData] = useState(null);
  const [optimizationSettings, setOptimizationSettings] = useState({
    frameThrottleMs: 100,
    enableFrameDropping: true,
    maxQueueSize: 10,
  });

  const videoStreamingRef = useRef(null);

  // Webcam controls
  const toggleWebcam = useCallback(async () => {
    try {
      if (!webcamActive) {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: true,
        });
        setWebcamActive(true);
        window.currentWebcamStream = stream;
      } else {
        if (window.currentWebcamStream) {
          window.currentWebcamStream.getTracks().forEach(track => track.stop());
          window.currentWebcamStream = null;
        }
        setWebcamActive(false);
        setStreamingActive(false);
        setStreamingConnectionStatus("disconnected");
      }
    } catch (error) {
      console.error("Webcam error:", error);
      setWebcamActive(false);
    }
  }, [webcamActive]);

  const toggleStreaming = useCallback(() => {
    if (webcamActive && connectionStatus === "connected") {
      setStreamingActive(!streamingActive);
      setStreamingConnectionStatus(
        streamingActive ? "disconnected" : "connected"
      );
    }
  }, [webcamActive, connectionStatus, streamingActive]);

  // Frame capture handler
  const handleFrameCapture = useCallback(frameData => {
    // Placeholder for frame capture logic
    console.log("Frame captured:", frameData);
  }, []);

  // Connection change handler
  const handleConnectionChange = useCallback(status => {
    setStreamingConnectionStatus(status);
  }, []);

  // Processed frame handler
  const handleProcessedFrame = useCallback(frameData => {
    setProcessedFrameData(frameData);
  }, []);

  // Error handler
  const handleError = useCallback(error => {
    console.error("ASL World error:", error);
  }, []);

  // Retry connection handler
  const handleRetryConnection = useCallback(() => {
    testBackendConnection();
  }, [testBackendConnection]);

  // Optimization change handler
  const handleOptimizationChange = useCallback(newSettings => {
    setOptimizationSettings(prev => ({ ...prev, ...newSettings }));
  }, []);

  return (
    <ASLWorldPage
      connectionStatus={connectionStatus}
      webcamActive={webcamActive}
      streamingActive={streamingActive}
      onFrameCapture={handleFrameCapture}
      videoStreamingRef={videoStreamingRef}
      processedFrameData={processedFrameData}
      streamingConnectionStatus={streamingConnectionStatus}
      optimizationSettings={optimizationSettings}
      onOptimizationChange={handleOptimizationChange}
      onConnectionChange={handleConnectionChange}
      onProcessedFrame={handleProcessedFrame}
      onError={handleError}
      onRetryConnection={handleRetryConnection}
      toggleWebcam={toggleWebcam}
      toggleStreaming={toggleStreaming}
      testBackendConnection={testBackendConnection}
    />
  );
};

export default ASLWorldWrapper;
