import React, { Component } from "react";

/**
 * Enhanced error fallback component with different error types
 */
export const EnhancedErrorFallback = ({
  error,
  resetErrorBoundary,
  errorType = "general",
  componentName = "Component",
  showRetry = true,
  showReload = true,
  customActions = [],
}) => {
  const [showDetails, setShowDetails] = React.useState(false);
  const [retryCount, setRetryCount] = React.useState(0);

  const getErrorMessage = () => {
    switch (errorType) {
      case "network":
        return {
          title: "Connection Error",
          message:
            "Unable to connect to the server. Please check your internet connection.",
          icon: "🌐",
          suggestions: [
            "Check your internet connection",
            "Try refreshing the page",
            "Wait a moment and try again",
            "Contact support if the problem persists",
          ],
        };
      case "authentication":
        return {
          title: "Authentication Error",
          message:
            "There was a problem with your authentication. Please sign in again.",
          icon: "🔐",
          suggestions: [
            "Try signing in again",
            "Clear your browser cache",
            "Check if your session has expired",
            "Contact support if you continue having issues",
          ],
        };
      case "component":
        return {
          title: `Failed to Load ${componentName}`,
          message:
            "This component couldn't be loaded. This might be a temporary issue.",
          icon: "⚠️",
          suggestions: [
            "Try refreshing the page",
            "Clear your browser cache",
            "Check your internet connection",
            "Try again in a few minutes",
          ],
        };
      case "chunk":
        return {
          title: "Loading Error",
          message:
            "Failed to load application resources. This might be due to a network issue.",
          icon: "📦",
          suggestions: [
            "Refresh the page to reload resources",
            "Clear your browser cache",
            "Check your internet connection",
            "Try using a different browser",
          ],
        };
      default:
        return {
          title: "Something Went Wrong",
          message:
            "An unexpected error occurred. We're sorry for the inconvenience.",
          icon: "🚨",
          suggestions: [
            "Try refreshing the page",
            "Clear your browser cache",
            "Try again in a few minutes",
            "Contact support if the problem persists",
          ],
        };
    }
  };

  const errorInfo = getErrorMessage();

  const handleRetry = () => {
    setRetryCount(prev => prev + 1);
    resetErrorBoundary();
  };

  const handleReload = () => {
    window.location.reload();
  };

  return (
    <div
      className="error-boundary-fallback"
      role="alert"
      data-error-type={errorType}
    >
      <div className="error-content">
        <div className="error-header">
          <div className="error-icon" aria-hidden="true">
            {errorInfo.icon}
          </div>
          <h2 className="error-title">{errorInfo.title}</h2>
        </div>

        <p className="error-message">{errorInfo.message}</p>

        {retryCount > 0 && (
          <div className="retry-info">
            <p>Retry attempts: {retryCount}</p>
          </div>
        )}

        <div className="error-actions">
          {showRetry && (
            <button
              className="error-button primary"
              onClick={handleRetry}
              disabled={retryCount >= 3}
            >
              {retryCount >= 3 ? "Max Retries Reached" : "Try Again"}
            </button>
          )}

          {showReload && (
            <button className="error-button secondary" onClick={handleReload}>
              Reload Page
            </button>
          )}

          {customActions.map((action, index) => (
            <button
              key={index}
              className={`error-button ${action.type || "secondary"}`}
              onClick={action.onClick}
            >
              {action.label}
            </button>
          ))}

          <button
            className="error-button tertiary"
            onClick={() => setShowDetails(!showDetails)}
          >
            {showDetails ? "Hide" : "Show"} Details
          </button>
        </div>

        {showDetails && (
          <details className="error-details" open>
            <summary>Technical Details</summary>
            <div className="error-info">
              <div className="error-section">
                <h4>Error Message:</h4>
                <pre className="error-text">{error.message}</pre>
              </div>

              {error.stack && (
                <div className="error-section">
                  <h4>Stack Trace:</h4>
                  <pre className="error-stack">{error.stack}</pre>
                </div>
              )}

              <div className="error-section">
                <h4>Component:</h4>
                <p>{componentName}</p>
              </div>

              <div className="error-section">
                <h4>Timestamp:</h4>
                <p>{new Date().toISOString()}</p>
              </div>
            </div>
          </details>
        )}

        <div className="error-suggestions">
          <h3>Suggested Solutions:</h3>
          <ul>
            {errorInfo.suggestions.map((suggestion, index) => (
              <li key={index}>{suggestion}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

/**
 * Network-specific error boundary
 */
export class NetworkErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      retryCount: 0,
      isRetrying: false,
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Network Error Boundary caught an error:", error, errorInfo);

    // Report to error tracking service if available
    if (window.errorTracker) {
      window.errorTracker.captureException(error, {
        context: "NetworkErrorBoundary",
        extra: errorInfo,
      });
    }
  }

  handleRetry = async () => {
    if (this.state.retryCount >= 3) return;

    this.setState({ isRetrying: true });

    // Wait before retry with exponential backoff
    const delay = Math.pow(2, this.state.retryCount) * 1000;
    await new Promise(resolve => setTimeout(resolve, delay));

    this.setState(prevState => ({
      hasError: false,
      error: null,
      retryCount: prevState.retryCount + 1,
      isRetrying: false,
    }));
  };

  render() {
    if (this.state.hasError) {
      return (
        <EnhancedErrorFallback
          error={this.state.error}
          resetErrorBoundary={this.handleRetry}
          errorType="network"
          componentName={this.props.componentName || "Network Component"}
          showRetry={this.state.retryCount < 3 && !this.state.isRetrying}
          customActions={
            this.state.isRetrying
              ? [{ label: "Retrying...", type: "disabled", onClick: () => {} }]
              : []
          }
        />
      );
    }

    return this.props.children;
  }
}

/**
 * Authentication-specific error boundary
 */
export class AuthenticationErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Authentication Error:", error, errorInfo);

    // Notify parent component of auth error
    if (this.props.onAuthError) {
      this.props.onAuthError(error);
    }
  }

  handleReset = () => {
    // Clear any auth-related state
    if (window.localStorage) {
      window.localStorage.removeItem("auth_token");
      window.localStorage.removeItem("user_data");
    }

    // Reset error state
    this.setState({ hasError: false, error: null });

    // Redirect to login
    window.location.href = "/login";
  };

  render() {
    if (this.state.hasError) {
      return (
        <EnhancedErrorFallback
          error={this.state.error}
          resetErrorBoundary={this.handleReset}
          errorType="authentication"
          componentName="Authentication"
          customActions={[
            {
              label: "Sign In Again",
              type: "primary",
              onClick: this.handleReset,
            },
          ]}
        />
      );
    }

    return this.props.children;
  }
}

/**
 * Component loading error boundary with chunk error handling
 */
export class ComponentLoadingErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, retryCount: 0 };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error(
      `Component Loading Error in ${this.props.componentName}:`,
      error,
      errorInfo
    );

    // Special handling for chunk loading errors
    if (this.isChunkError(error)) {
      console.warn("Chunk loading error detected, may need page reload");
    }
  }

  isChunkError = error => {
    return (
      error.name === "ChunkLoadError" ||
      error.message.includes("Loading chunk") ||
      error.message.includes("Loading CSS chunk")
    );
  };

  handleReset = () => {
    const newRetryCount = this.state.retryCount + 1;

    // For chunk errors after multiple retries, force reload
    if (newRetryCount >= 2) {
      window.location.reload();
      return;
    }

    this.setState({
      hasError: false,
      error: null,
      retryCount: newRetryCount,
    });
  };

  render() {
    if (this.state.hasError) {
      // If a fallback component is provided, use it for certain error types
      if (this.props.fallbackComponent) {
        const FallbackComponent = this.props.fallbackComponent;
        return (
          <FallbackComponent
            error={this.state.error}
            resetErrorBoundary={this.handleReset}
          />
        );
      }

      return (
        <EnhancedErrorFallback
          error={this.state.error}
          resetErrorBoundary={this.handleReset}
          errorType={
            this.isChunkError(this.state.error) ? "chunk" : "component"
          }
          componentName={this.props.componentName}
          showRetry={this.state.retryCount < 3}
          customActions={
            this.state.retryCount >= 2
              ? [
                  {
                    label: "Reload Application",
                    type: "primary",
                    onClick: () => window.location.reload(),
                  },
                ]
              : []
          }
        />
      );
    }

    return this.props.children;
  }
}

/**
 * Route-specific error boundary with navigation fallbacks
 */
export class RouteErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error(`Route Error in ${this.props.routeName}:`, error, errorInfo);
  }

  navigateToFallback = () => {
    window.location.href = this.props.fallbackRoute || "/dashboard";
  };

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <EnhancedErrorFallback
          error={this.state.error}
          resetErrorBoundary={this.handleReset}
          errorType="component"
          componentName={`${this.props.routeName} Page`}
          customActions={[
            {
              label: "Go to Dashboard",
              type: "primary",
              onClick: this.navigateToFallback,
            },
          ]}
        />
      );
    }

    return this.props.children;
  }
}

export default {
  EnhancedErrorFallback,
  NetworkErrorBoundary,
  AuthenticationErrorBoundary,
  ComponentLoadingErrorBoundary,
  RouteErrorBoundary,
};
