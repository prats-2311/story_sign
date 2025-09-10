import React, { useState, useEffect } from "react";
import { performanceUtils } from "../../utils/performance";
import "./OptimizedLoadingScreen.css";

/**
 * Optimized loading screen with performance considerations
 * Provides responsive feedback and adapts to user preferences
 */
const OptimizedLoadingScreen = ({
  message = "Loading StorySign Platform...",
  showProgress = false,
  progress = 0,
  timeout = 10000,
  onTimeout,
  minimal = false,
}) => {
  const [showSpinner, setShowSpinner] = useState(true);
  const [hasTimedOut, setHasTimedOut] = useState(false);
  const [reducedMotion] = useState(() =>
    performanceUtils.prefersReducedMotion()
  );

  useEffect(() => {
    // Set timeout for loading
    const timeoutId = setTimeout(() => {
      setHasTimedOut(true);
      if (onTimeout) {
        onTimeout();
      }
    }, timeout);

    return () => clearTimeout(timeoutId);
  }, [timeout, onTimeout]);

  // Minimal loading for fast connections or reduced motion
  if (minimal || reducedMotion) {
    return (
      <div className="loading-screen minimal" role="status" aria-live="polite">
        <div className="loading-content">
          <div className="loading-text">{message}</div>
          {showProgress && (
            <div
              className="progress-bar"
              aria-label={`Loading progress: ${progress}%`}
            >
              <div
                className="progress-fill"
                style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
              />
            </div>
          )}
        </div>
      </div>
    );
  }

  if (hasTimedOut) {
    return (
      <div className="loading-screen timeout" role="alert">
        <div className="loading-content">
          <div className="timeout-icon" aria-hidden="true">
            ⚠️
          </div>
          <div className="timeout-message">
            <h2>Loading is taking longer than expected</h2>
            <p>Please check your connection and try refreshing the page.</p>
          </div>
          <button
            className="retry-button"
            onClick={() => window.location.reload()}
          >
            Refresh Page
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="loading-screen" role="status" aria-live="polite">
      <div className="loading-content">
        {showSpinner && (
          <div className="loading-spinner" aria-hidden="true">
            <div className="spinner-ring"></div>
            <div className="spinner-ring"></div>
            <div className="spinner-ring"></div>
          </div>
        )}

        <div className="loading-text">{message}</div>

        {showProgress && (
          <div className="progress-container">
            <div
              className="progress-bar"
              aria-label={`Loading progress: ${progress}%`}
            >
              <div
                className="progress-fill"
                style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
              />
            </div>
            <div className="progress-text">{Math.round(progress)}%</div>
          </div>
        )}

        <div className="loading-tips">
          <p>
            💡 Tip: Enable hardware acceleration in your browser for better
            performance
          </p>
        </div>
      </div>
    </div>
  );
};

/**
 * Route transition loading component
 * Optimized for smooth transitions between pages
 */
export const RouteTransitionLoader = ({
  isTransitioning,
  fromRoute,
  toRoute,
  duration = 300,
}) => {
  const [visible, setVisible] = useState(false);
  const [reducedMotion] = useState(() =>
    performanceUtils.prefersReducedMotion()
  );

  useEffect(() => {
    if (isTransitioning) {
      setVisible(true);
    } else {
      // Delay hiding to allow for smooth transition
      const hideTimeout = setTimeout(
        () => {
          setVisible(false);
        },
        reducedMotion ? 0 : 150
      );

      return () => clearTimeout(hideTimeout);
    }
  }, [isTransitioning, reducedMotion]);

  if (!visible) return null;

  return (
    <div
      className={`route-transition-loader ${
        reducedMotion ? "reduced-motion" : ""
      }`}
      style={{
        "--transition-duration": reducedMotion ? "0ms" : `${duration}ms`,
      }}
    >
      <div className="transition-bar" />
      {toRoute && (
        <div className="transition-info">
          <span>Loading {toRoute}...</span>
        </div>
      )}
    </div>
  );
};

/**
 * Component loading skeleton
 * Provides visual feedback while components are loading
 */
export const ComponentSkeleton = ({
  type = "default",
  lines = 3,
  showAvatar = false,
  className = "",
}) => {
  const [reducedMotion] = useState(() =>
    performanceUtils.prefersReducedMotion()
  );

  const renderSkeleton = () => {
    switch (type) {
      case "dashboard":
        return (
          <div className="skeleton-dashboard">
            <div className="skeleton-header">
              <div className="skeleton-line skeleton-title" />
              <div className="skeleton-line skeleton-subtitle" />
            </div>
            <div className="skeleton-grid">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="skeleton-card">
                  <div className="skeleton-line skeleton-card-title" />
                  <div className="skeleton-line skeleton-card-content" />
                  <div className="skeleton-line skeleton-card-content short" />
                </div>
              ))}
            </div>
          </div>
        );

      case "asl-world":
        return (
          <div className="skeleton-asl-world">
            <div className="skeleton-video-area">
              <div className="skeleton-video-placeholder" />
            </div>
            <div className="skeleton-controls">
              <div className="skeleton-line skeleton-button" />
              <div className="skeleton-line skeleton-button" />
            </div>
          </div>
        );

      default:
        return (
          <div className="skeleton-default">
            {showAvatar && <div className="skeleton-avatar" />}
            {[...Array(lines)].map((_, i) => (
              <div
                key={i}
                className={`skeleton-line ${i === lines - 1 ? "short" : ""}`}
              />
            ))}
          </div>
        );
    }
  };

  return (
    <div
      className={`component-skeleton ${
        reducedMotion ? "reduced-motion" : ""
      } ${className}`}
      role="status"
      aria-label="Loading content..."
    >
      {renderSkeleton()}
    </div>
  );
};

export default OptimizedLoadingScreen;
