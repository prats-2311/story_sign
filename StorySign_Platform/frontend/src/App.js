import React, { useState, useRef, useEffect } from "react";
import {
  Routes,
  Route,
  Navigate,
  useNavigate,
  useLocation,
} from "react-router-dom";
import "./App.css";
import "./components/performance/PerformanceMonitor.css";
import "./styles/responsive.css";
import { MainDashboard, ASLWorldPage } from "./pages";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import PluginManagementPage from "./pages/PluginManagementPage";
import { PlatformShell } from "./components";
import PlatformShellDemo from "./components/shell/PlatformShellDemo";

import { ProtectedRoute, AuthGuard } from "./components/auth";
import AuthNavigation from "./components/navigation/AuthNavigation";
import SkipLinks from "./components/common/SkipLinks";
import { useAccessibility } from "./hooks/useAccessibility";
import { manageFocusForSPA } from "./utils/accessibility";
import pwaService from "./services/PWAService";
import { useResponsive } from "./hooks/useResponsive";
import { buildHealthCheckUrl } from "./config/api";

function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const { announce } = useAccessibility();
  const { isMobile, shouldUseVideoOptimizations, getVideoQuality } =
    useResponsive();

  const [backendMessage, setBackendMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState("not_tested");
  const [webcamActive, setWebcamActive] = useState(false);
  const [webcamError, setWebcamError] = useState("");
  const [streamingActive, setStreamingActive] = useState(false);
  const [processedFrameData, setProcessedFrameData] = useState(null);
  const [streamingError, setStreamingError] = useState("");
  const [streamingConnectionStatus, setStreamingConnectionStatus] =
    useState("disconnected");
  const [showTroubleshooting, setShowTroubleshooting] = useState(false);
  const [optimizationSettings, setOptimizationSettings] = useState({
    adaptiveQuality: true,
    targetFPS: isMobile ? 24 : 30,
    maxLatency: isMobile ? 150 : 100,
    qualityProfile: shouldUseVideoOptimizations ? "mobile" : "balanced",
  });

  const videoStreamingRef = useRef(null);

  // PWA and responsive setup
  useEffect(() => {
    // Initialize PWA service
    pwaService.init();

    // Update optimization settings based on device capabilities
    setOptimizationSettings(prev => ({
      ...prev,
      targetFPS: isMobile ? 24 : 30,
      maxLatency: isMobile ? 150 : 100,
      qualityProfile: shouldUseVideoOptimizations ? "mobile" : "balanced",
    }));

    // Cache important resources for offline use
    const importantResources = ["/", "/asl-world", "/plugins"];
    pwaService.cacheResources(importantResources);
  }, [isMobile, shouldUseVideoOptimizations]);

  // Handle route changes for accessibility
  useEffect(() => {
    const getPageTitle = pathname => {
      const titleMap = {
        "/": "StorySign - Dashboard",
        "/login": "StorySign - Sign In",
        "/register": "StorySign - Register",
        "/asl-world": "StorySign - ASL World",
        "/harmony": "StorySign - Harmony",
        "/reconnect": "StorySign - Reconnect",
        "/plugins": "StorySign - Plugin Management",
        "/platform-demo": "StorySign - Platform Demo",
      };
      return titleMap[pathname] || "StorySign Platform";
    };

    const pageTitle = getPageTitle(location.pathname);
    manageFocusForSPA(pageTitle);
  }, [location.pathname]);

  const testBackendConnection = async () => {
    setIsLoading(true);
    setConnectionStatus("testing");
    setShowTroubleshooting(false);

    try {
      const response = await fetch(buildHealthCheckUrl(), {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        timeout: 10000, // 10 second timeout
      });

      if (response.ok) {
        const data = await response.json();
        setBackendMessage(data.message || "Backend connected successfully!");
        setConnectionStatus("connected");
        setShowTroubleshooting(false);
      } else {
        let errorMessage = `Backend error: ${response.status} ${response.statusText}`;
        if (response.status === 404) {
          errorMessage =
            "Backend API endpoint not found. Please ensure the backend server is running correctly.";
        } else if (response.status >= 500) {
          errorMessage =
            "Backend server error. Please check the backend logs for more information.";
        }
        setBackendMessage(errorMessage);
        setConnectionStatus("error");
        setShowTroubleshooting(true);
      }
    } catch (error) {
      let errorMessage = "Connection failed: ";
      if (error.name === "TypeError" && error.message.includes("fetch")) {
        errorMessage +=
          "Cannot reach backend server. Please ensure the backend is running and accessible";
      } else if (error.name === "AbortError") {
        errorMessage +=
          "Connection timeout. The backend server may be overloaded or not responding.";
      } else {
        errorMessage += error.message;
      }
      setBackendMessage(errorMessage);
      setConnectionStatus("error");
      setShowTroubleshooting(true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFrameCapture = message => {
    // Send frame to WebSocket if streaming is active
    if (streamingActive && videoStreamingRef.current) {
      videoStreamingRef.current.sendFrame(message);
    }

    console.log("Frame captured:", {
      timestamp: message.timestamp,
      frameNumber: message.metadata?.frame_number,
      size: `${message.metadata?.width}x${message.metadata?.height}`,
      adaptiveFPS: message.metadata?.adaptive_fps,
      processingCapability: message.metadata?.processing_capability,
    });
  };

  const handleStreamingConnectionChange = status => {
    console.log("Streaming connection status:", status);
    setStreamingConnectionStatus(status);

    // Clear streaming error when connection is restored
    if (status === "connected") {
      setStreamingError("");
    }
  };

  const handleProcessedFrame = message => {
    // Handle different message types
    if (message.type === "processed_frame") {
      setProcessedFrameData(message);
      // Clear any previous streaming errors on successful frame processing
      setStreamingError("");

      console.log("Processed frame received:", {
        frameNumber: message.metadata?.frame_number,
        processingTime: message.metadata?.processing_time_ms,
        landmarks: message.metadata?.landmarks_detected,
      });
    } else {
      // Handle other message types as processed frames for backward compatibility
      setProcessedFrameData(message);
      setStreamingError("");
    }
  };

  const handleStreamingError = error => {
    console.error("Streaming error:", error);
    setStreamingError(error);

    // Don't override backend connection status if it's already connected
    if (connectionStatus !== "connected") {
      setBackendMessage(`Streaming error: ${error}`);
      setConnectionStatus("error");
    }
  };

  const handleOptimizationChange = newSettings => {
    setOptimizationSettings(newSettings);
    console.log("Optimization settings updated:", newSettings);

    // Send optimization settings to backend if needed
    // This could be implemented as a WebSocket message or REST API call
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

    if (connectionStatus !== "connected") {
      setBackendMessage(
        "Please test backend connection first before enabling streaming"
      );
      return;
    }

    // Clear previous streaming errors when starting
    if (!streamingActive) {
      setStreamingError("");
    }

    setStreamingActive(!streamingActive);
  };

  const retryWebcam = () => {
    setWebcamError("");
    setWebcamActive(false);
    // Small delay to ensure cleanup, then restart
    setTimeout(() => {
      setWebcamActive(true);
    }, 500);
  };

  const retryStreaming = () => {
    setStreamingError("");
    setStreamingActive(false);
    // Small delay to ensure cleanup, then restart
    setTimeout(() => {
      setStreamingActive(true);
    }, 500);
  };

  const handleNavigateToASLWorld = () => {
    navigate("/asl-world");
  };

  return (
    <>
      <SkipLinks />
      <AuthNavigation />
      <PlatformShell>
        <Routes>
          {/* Public Routes */}
          <Route
            path="/login"
            element={
              <AuthGuard>
                <LoginPage />
              </AuthGuard>
            }
          />
          <Route
            path="/register"
            element={
              <AuthGuard>
                <RegisterPage />
              </AuthGuard>
            }
          />

          {/* Protected Routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <MainDashboard
                  backendMessage={backendMessage}
                  isLoading={isLoading}
                  connectionStatus={connectionStatus}
                  webcamActive={webcamActive}
                  webcamError={webcamError}
                  streamingActive={streamingActive}
                  streamingError={streamingError}
                  showTroubleshooting={showTroubleshooting}
                  testBackendConnection={testBackendConnection}
                  toggleWebcam={toggleWebcam}
                  toggleStreaming={toggleStreaming}
                  retryWebcam={retryWebcam}
                  retryStreaming={retryStreaming}
                  onNavigateToASLWorld={handleNavigateToASLWorld}
                />
              </ProtectedRoute>
            }
          />
          <Route
            path="/asl-world"
            element={
              <ProtectedRoute>
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
                  onConnectionChange={handleStreamingConnectionChange}
                  onProcessedFrame={handleProcessedFrame}
                  onError={handleStreamingError}
                  onRetryConnection={retryStreaming}
                  toggleWebcam={toggleWebcam}
                  toggleStreaming={toggleStreaming}
                  testBackendConnection={testBackendConnection}
                />
              </ProtectedRoute>
            }
          />
          <Route
            path="/plugins"
            element={
              <ProtectedRoute>
                <PluginManagementPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/platform-demo"
            element={
              <ProtectedRoute>
                <PlatformShellDemo />
              </ProtectedRoute>
            }
          />

          {/* Placeholder routes for future modules */}
          <Route
            path="/harmony"
            element={
              <ProtectedRoute>
                <div style={{ padding: "2rem", textAlign: "center" }}>
                  <h1>Harmony Module</h1>
                  <p>Facial expression practice module coming soon!</p>
                </div>
              </ProtectedRoute>
            }
          />
          <Route
            path="/reconnect"
            element={
              <ProtectedRoute>
                <div style={{ padding: "2rem", textAlign: "center" }}>
                  <h1>Reconnect Module</h1>
                  <p>Therapeutic movement analysis module coming soon!</p>
                </div>
              </ProtectedRoute>
            }
          />

          {/* Default redirect to main dashboard */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </PlatformShell>
    </>
  );
}

export default App;
