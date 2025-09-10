import React from "react";
import "./LoadingSpinner.css";

/**
 * Accessible LoadingSpinner component with screen reader support
 * Provides visual and auditory feedback for loading states
 */
const LoadingSpinner = ({
  size = "medium",
  variant = "primary",
  message = "Loading...",
  showMessage = true,
  className = "",
  ariaLabel,
  inline = false,
}) => {
  const spinnerClasses = [
    "loading-spinner",
    `spinner-${size}`,
    `spinner-${variant}`,
    inline && "spinner-inline",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const containerClasses = [
    "loading-spinner-container",
    inline && "container-inline",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={containerClasses}>
      <div
        className={spinnerClasses}
        role="status"
        aria-label={ariaLabel || message}
        aria-live="polite"
      >
        <div className="spinner-circle" aria-hidden="true">
          <div className="spinner-path"></div>
        </div>

        {showMessage && <span className="spinner-message">{message}</span>}

        {/* Screen reader only text */}
        <span className="sr-only">{ariaLabel || message}</span>
      </div>
    </div>
  );
};

/**
 * Inline spinner for use within buttons or other components
 */
export const InlineSpinner = ({
  size = "small",
  variant = "inherit",
  ariaLabel = "Loading",
}) => (
  <LoadingSpinner
    size={size}
    variant={variant}
    message=""
    showMessage={false}
    ariaLabel={ariaLabel}
    inline={true}
  />
);

/**
 * Full page loading overlay
 */
export const PageLoader = ({
  message = "Loading page...",
  variant = "primary",
}) => (
  <div className="page-loader-overlay">
    <LoadingSpinner
      size="large"
      variant={variant}
      message={message}
      showMessage={true}
    />
  </div>
);

/**
 * Content area loader
 */
export const ContentLoader = ({
  message = "Loading content...",
  variant = "primary",
}) => (
  <div className="content-loader-container">
    <LoadingSpinner
      size="medium"
      variant={variant}
      message={message}
      showMessage={true}
    />
  </div>
);

export default LoadingSpinner;
