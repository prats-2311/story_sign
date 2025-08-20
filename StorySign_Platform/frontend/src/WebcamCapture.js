import React, { useRef, useEffect, useState, useCallback } from "react";

const WebcamCapture = ({ onFrameCapture, onError, isActive = false }) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const animationFrameRef = useRef(null);

  const [webcamStatus, setWebcamStatus] = useState("inactive"); // inactive, initializing, active, error
  const [errorMessage, setErrorMessage] = useState("");
  const [frameCount, setFrameCount] = useState(0);

  // Initialize webcam access
  const initializeWebcam = useCallback(async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      const error = "getUserMedia is not supported in this browser";
      setErrorMessage(error);
      setWebcamStatus("error");
      onError?.(error);
      return;
    }

    setWebcamStatus("initializing");
    setErrorMessage("");

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          frameRate: { ideal: 30 },
        },
        audio: false,
      });

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current.play();
          setWebcamStatus("active");
        };
      }
    } catch (error) {
      let errorMsg = "Failed to access webcam";

      if (error.name === "NotAllowedError") {
        errorMsg =
          "Webcam access denied. Please allow camera permissions and try again.";
      } else if (error.name === "NotFoundError") {
        errorMsg =
          "No webcam device found. Please connect a camera and try again.";
      } else if (error.name === "NotReadableError") {
        errorMsg = "Webcam is already in use by another application.";
      } else if (error.name === "OverconstrainedError") {
        errorMsg = "Webcam does not support the requested video constraints.";
      } else {
        errorMsg = `Webcam error: ${error.message}`;
      }

      setErrorMessage(errorMsg);
      setWebcamStatus("error");
      onError?.(errorMsg);
    }
  }, [onError]);

  // Stop webcam stream
  const stopWebcam = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    setWebcamStatus("inactive");
    setFrameCount(0);
  }, []);

  // Capture frame from video and convert to base64 JPEG
  const captureFrame = useCallback(() => {
    if (!videoRef.current || !canvasRef.current || webcamStatus !== "active") {
      return null;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");

    // Reduce canvas dimensions for better WebSocket performance
    // Use smaller resolution for streaming while maintaining aspect ratio
    const maxWidth = 320;
    const maxHeight = 240;
    const videoWidth = video.videoWidth || 640;
    const videoHeight = video.videoHeight || 480;

    const aspectRatio = videoWidth / videoHeight;
    let canvasWidth = maxWidth;
    let canvasHeight = maxWidth / aspectRatio;

    if (canvasHeight > maxHeight) {
      canvasHeight = maxHeight;
      canvasWidth = maxHeight * aspectRatio;
    }

    canvas.width = canvasWidth;
    canvas.height = canvasHeight;

    // Draw current video frame to canvas with reduced size
    ctx.drawImage(video, 0, 0, canvasWidth, canvasHeight);

    try {
      // Convert canvas to base64 JPEG with lower quality for smaller size
      const base64Data = canvas.toDataURL("image/jpeg", 0.5);

      setFrameCount((prev) => prev + 1);

      return {
        frameData: base64Data,
        timestamp: new Date().toISOString(),
        frameNumber: frameCount + 1,
        width: canvas.width,
        height: canvas.height,
      };
    } catch (error) {
      console.error("Error capturing frame:", error);
      return null;
    }
  }, [webcamStatus, frameCount]);

  // Frame capture loop
  const startFrameCapture = useCallback(() => {
    if (!isActive || webcamStatus !== "active") {
      return;
    }

    const captureLoop = () => {
      const frameData = captureFrame();
      if (frameData && onFrameCapture) {
        onFrameCapture(frameData);
      }

      // Continue the loop
      animationFrameRef.current = requestAnimationFrame(captureLoop);
    };

    animationFrameRef.current = requestAnimationFrame(captureLoop);
  }, [isActive, webcamStatus, captureFrame, onFrameCapture]);

  // Stop frame capture loop
  const stopFrameCapture = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
  }, []);

  // Effect to handle webcam initialization/cleanup
  useEffect(() => {
    if (isActive && webcamStatus === "inactive") {
      initializeWebcam();
    } else if (!isActive && webcamStatus !== "inactive") {
      stopWebcam();
    }
  }, [isActive, webcamStatus, initializeWebcam, stopWebcam]);

  // Effect to handle frame capture loop
  useEffect(() => {
    if (isActive && webcamStatus === "active") {
      startFrameCapture();
    } else {
      stopFrameCapture();
    }

    return () => {
      stopFrameCapture();
    };
  }, [isActive, webcamStatus, startFrameCapture, stopFrameCapture]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopWebcam();
    };
  }, [stopWebcam]);

  const getStatusColor = () => {
    switch (webcamStatus) {
      case "active":
        return "#4CAF50";
      case "error":
        return "#f44336";
      case "initializing":
        return "#ff9800";
      default:
        return "#9e9e9e";
    }
  };

  const getStatusText = () => {
    switch (webcamStatus) {
      case "active":
        return `Active (${frameCount} frames)`;
      case "error":
        return "Error";
      case "initializing":
        return "Initializing...";
      default:
        return "Inactive";
    }
  };

  return (
    <div className="webcam-capture">
      <div className="webcam-status">
        <span
          className="status-dot"
          style={{ backgroundColor: getStatusColor() }}
        ></span>
        <span className="status-text">{getStatusText()}</span>
      </div>

      {errorMessage && (
        <div className="error-message">
          <p>{errorMessage}</p>
        </div>
      )}

      <div className="video-container">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          style={{
            width: "100%",
            maxWidth: "640px",
            height: "auto",
            display: webcamStatus === "active" ? "block" : "none",
          }}
        />

        {webcamStatus === "inactive" && (
          <div className="video-placeholder">
            <p>Webcam inactive</p>
          </div>
        )}

        {webcamStatus === "initializing" && (
          <div className="video-placeholder">
            <p>Initializing webcam...</p>
          </div>
        )}

        {webcamStatus === "error" && (
          <div className="video-placeholder error">
            <p>Webcam unavailable</p>
          </div>
        )}
      </div>

      {/* Hidden canvas for frame capture */}
      <canvas ref={canvasRef} style={{ display: "none" }} />
    </div>
  );
};

export default WebcamCapture;
