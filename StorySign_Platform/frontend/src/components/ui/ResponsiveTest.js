import React from "react";
import {
  useResponsive,
  useMediaQuery,
  useDeviceCapabilities,
} from "../../hooks/useResponsive";
import ResponsiveVideoPlayer from "../video/ResponsiveVideoPlayer";
import OfflineSync from "./OfflineSync";
import "./ResponsiveTest.css";

const ResponsiveTest = () => {
  const responsive = useResponsive();
  const isLargeScreen = useMediaQuery("(min-width: 1200px)");
  const isPrintMode = useMediaQuery("print");
  const capabilities = useDeviceCapabilities();

  const {
    windowSize,
    orientation,
    isTouchDevice,
    currentBreakpoint,
    isMobile,
    isTablet,
    isDesktop,
    deviceType,
    isCompactDevice,
    shouldCollapseSidebar,
    shouldUseVideoOptimizations,
    getVideoQuality,
  } = responsive;

  return (
    <div className="responsive-test">
      <div className="container">
        <h1>Responsive Design Test</h1>

        <div className="test-grid">
          {/* Window Information */}
          <div className="test-card">
            <h3>Window Information</h3>
            <div className="info-grid">
              <div className="info-item">
                <span className="label">Size:</span>
                <span className="value">
                  {windowSize.width} × {windowSize.height}
                </span>
              </div>
              <div className="info-item">
                <span className="label">Orientation:</span>
                <span className="value">{orientation}</span>
              </div>
              <div className="info-item">
                <span className="label">Breakpoint:</span>
                <span className="value">{currentBreakpoint}</span>
              </div>
              <div className="info-item">
                <span className="label">Touch Device:</span>
                <span className="value">{isTouchDevice ? "Yes" : "No"}</span>
              </div>
            </div>
          </div>

          {/* Device Type */}
          <div className="test-card">
            <h3>Device Detection</h3>
            <div className="info-grid">
              <div className="info-item">
                <span className="label">Type:</span>
                <span className="value">{deviceType}</span>
              </div>
              <div className="info-item">
                <span className="label">Mobile:</span>
                <span className="value">{isMobile ? "Yes" : "No"}</span>
              </div>
              <div className="info-item">
                <span className="label">Tablet:</span>
                <span className="value">{isTablet ? "Yes" : "No"}</span>
              </div>
              <div className="info-item">
                <span className="label">Desktop:</span>
                <span className="value">{isDesktop ? "Yes" : "No"}</span>
              </div>
              <div className="info-item">
                <span className="label">Compact:</span>
                <span className="value">{isCompactDevice ? "Yes" : "No"}</span>
              </div>
            </div>
          </div>

          {/* Media Queries */}
          <div className="test-card">
            <h3>Media Query Tests</h3>
            <div className="info-grid">
              <div className="info-item">
                <span className="label">Large Screen:</span>
                <span className="value">{isLargeScreen ? "Yes" : "No"}</span>
              </div>
              <div className="info-item">
                <span className="label">Print Mode:</span>
                <span className="value">{isPrintMode ? "Yes" : "No"}</span>
              </div>
            </div>
          </div>

          {/* Device Capabilities */}
          <div className="test-card">
            <h3>Device Capabilities</h3>
            <div className="info-grid">
              <div className="info-item">
                <span className="label">Camera:</span>
                <span className="value">
                  {capabilities.hasCamera ? "Yes" : "No"}
                </span>
              </div>
              <div className="info-item">
                <span className="label">Microphone:</span>
                <span className="value">
                  {capabilities.hasMicrophone ? "Yes" : "No"}
                </span>
              </div>
              <div className="info-item">
                <span className="label">Geolocation:</span>
                <span className="value">
                  {capabilities.hasGeolocation ? "Yes" : "No"}
                </span>
              </div>
              <div className="info-item">
                <span className="label">Orientation:</span>
                <span className="value">
                  {capabilities.hasOrientation ? "Yes" : "No"}
                </span>
              </div>
              <div className="info-item">
                <span className="label">Vibration:</span>
                <span className="value">
                  {capabilities.hasVibration ? "Yes" : "No"}
                </span>
              </div>
              <div className="info-item">
                <span className="label">Notifications:</span>
                <span className="value">
                  {capabilities.hasNotifications ? "Yes" : "No"}
                </span>
              </div>
              <div className="info-item">
                <span className="label">Online:</span>
                <span className="value">
                  {capabilities.isOnline ? "Yes" : "No"}
                </span>
              </div>
            </div>
          </div>

          {/* Responsive Utilities */}
          <div className="test-card">
            <h3>Responsive Utilities</h3>
            <div className="info-grid">
              <div className="info-item">
                <span className="label">Collapse Sidebar:</span>
                <span className="value">
                  {shouldCollapseSidebar ? "Yes" : "No"}
                </span>
              </div>
              <div className="info-item">
                <span className="label">Video Optimizations:</span>
                <span className="value">
                  {shouldUseVideoOptimizations ? "Yes" : "No"}
                </span>
              </div>
              <div className="info-item">
                <span className="label">Video Quality:</span>
                <span className="value">{getVideoQuality}</span>
              </div>
              <div className="info-item">
                <span className="label">Grid Columns:</span>
                <span className="value">{responsive.getGridColumns()}</span>
              </div>
              <div className="info-item">
                <span className="label">Spacing:</span>
                <span className="value">
                  {responsive.getResponsiveSpacing()}px
                </span>
              </div>
              <div className="info-item">
                <span className="label">Font Size:</span>
                <span className="value">
                  {responsive.getResponsiveFontSize()}px
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Responsive Grid Demo */}
        <div className="test-section">
          <h3>Responsive Grid Demo</h3>
          <div className="responsive-grid">
            {Array.from({ length: responsive.getGridColumns() * 2 }, (_, i) => (
              <div key={i} className="grid-item">
                Item {i + 1}
              </div>
            ))}
          </div>
        </div>

        {/* Video Player Demo */}
        <div className="test-section">
          <h3>Responsive Video Player Demo</h3>
          <div className="video-demo">
            <ResponsiveVideoPlayer
              src="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
              poster="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/images/BigBuckBunny.jpg"
              controls={true}
            />
          </div>
        </div>

        {/* Offline Sync Demo */}
        <div className="test-section">
          <h3>Offline Sync Demo</h3>
          <OfflineSync />
        </div>

        {/* Breakpoint Indicators */}
        <div className="test-section">
          <h3>Breakpoint Indicators</h3>
          <div className="breakpoint-indicators">
            <div className="indicator xs">XS (0-575px)</div>
            <div className="indicator sm">SM (576-767px)</div>
            <div className="indicator md">MD (768-991px)</div>
            <div className="indicator lg">LG (992-1199px)</div>
            <div className="indicator xl">XL (1200-1399px)</div>
            <div className="indicator xxl">XXL (1400px+)</div>
          </div>
        </div>

        {/* Touch Target Demo */}
        <div className="test-section">
          <h3>Touch Target Demo</h3>
          <div className="touch-demo">
            <button className="touch-target">Touch Target Button</button>
            <button className="regular-button">Regular Button</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResponsiveTest;
