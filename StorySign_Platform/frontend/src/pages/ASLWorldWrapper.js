import React, { useState, useRef, useCallback } from "react";
import ASLWorldPage from "./ASLWorldPage";

const ASLWorldWrapper = () => {
  // Video streaming state - simplified without manual backend connection
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

  // Webcam controls - no backend dependency
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

  // Streaming toggle - automatic backend connection
  const toggleStreaming = useCallback(() => {
    if (webcamActive) {
      setStreamingActive(!streamingActive);
      setStreamingConnectionStatus(
        streamingActive ? "disconnected" : "connected"
      );
    }
  }, [webcamActive, streamingActive]);

  // Frame capture handler
  const handleFrameCapture = useCallback(frameData => {
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

  // Optimization change handler
  const handleOptimizationChange = useCallback(newSettings => {
    setOptimizationSettings(prev => ({ ...prev, ...newSettings }));
  }, []);

  return (
    <ASLWorldPage
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
      toggleWebcam={toggleWebcam}
      toggleStreaming={toggleStreaming}
    />
  );
};

export default ASLWorldWrapper;
