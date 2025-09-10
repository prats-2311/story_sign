/**
 * Network Error Handler Utility
 * Provides comprehensive error handling for network operations
 */

/**
 * Error types for categorization
 */
export const ERROR_TYPES = {
  NETWORK: "network",
  AUTHENTICATION: "authentication",
  AUTHORIZATION: "authorization",
  VALIDATION: "validation",
  SERVER: "server",
  CLIENT: "client",
  TIMEOUT: "timeout",
  CHUNK_LOAD: "chunk_load",
  UNKNOWN: "unknown",
};

/**
 * Error severity levels
 */
export const ERROR_SEVERITY = {
  LOW: "low",
  MEDIUM: "medium",
  HIGH: "high",
  CRITICAL: "critical",
};

/**
 * Categorize error based on error object and response
 */
export const categorizeError = (error, response = null) => {
  const errorMessage = error.message || error.toString();
  const status = response?.status || error.status;

  // Network connectivity errors
  if (
    error.name === "TypeError" ||
    errorMessage.includes("Failed to fetch") ||
    errorMessage.includes("Network request failed") ||
    errorMessage.includes("Unable to connect") ||
    errorMessage.includes("ERR_NETWORK") ||
    errorMessage.includes("ERR_INTERNET_DISCONNECTED") ||
    !navigator.onLine
  ) {
    return {
      type: ERROR_TYPES.NETWORK,
      severity: ERROR_SEVERITY.HIGH,
      retryable: true,
      userMessage:
        "Connection failed. Please check your internet connection and try again.",
      technicalMessage: errorMessage,
      suggestedActions: [
        "Check your internet connection",
        "Try again in a few moments",
        "Contact support if the problem persists",
      ],
    };
  }

  // Timeout errors
  if (
    errorMessage.includes("timeout") ||
    errorMessage.includes("Request timed out") ||
    error.name === "TimeoutError"
  ) {
    return {
      type: ERROR_TYPES.TIMEOUT,
      severity: ERROR_SEVERITY.MEDIUM,
      retryable: true,
      userMessage:
        "Request timed out. The server is taking too long to respond.",
      technicalMessage: errorMessage,
      suggestedActions: [
        "Try again in a moment",
        "Check your internet connection",
        "Contact support if timeouts persist",
      ],
    };
  }

  // Chunk loading errors (code splitting)
  if (
    error.name === "ChunkLoadError" ||
    errorMessage.includes("Loading chunk") ||
    errorMessage.includes("Loading CSS chunk")
  ) {
    return {
      type: ERROR_TYPES.CHUNK_LOAD,
      severity: ERROR_SEVERITY.MEDIUM,
      retryable: true,
      userMessage:
        "Failed to load application resources. Please refresh the page.",
      technicalMessage: errorMessage,
      suggestedActions: [
        "Refresh the page",
        "Clear your browser cache",
        "Try using a different browser",
      ],
    };
  }

  // HTTP status code based categorization
  if (status) {
    // Authentication errors (401)
    if (status === 401) {
      return {
        type: ERROR_TYPES.AUTHENTICATION,
        severity: ERROR_SEVERITY.HIGH,
        retryable: false,
        userMessage: "Your session has expired. Please sign in again.",
        technicalMessage: errorMessage,
        suggestedActions: [
          "Sign in again",
          "Clear your browser cache",
          "Contact support if you continue having issues",
        ],
      };
    }

    // Authorization errors (403)
    if (status === 403) {
      return {
        type: ERROR_TYPES.AUTHORIZATION,
        severity: ERROR_SEVERITY.HIGH,
        retryable: false,
        userMessage: "You don't have permission to access this resource.",
        technicalMessage: errorMessage,
        suggestedActions: [
          "Contact your administrator",
          "Check if you have the required permissions",
          "Try signing in with a different account",
        ],
      };
    }

    // Validation errors (400, 422)
    if (status === 400 || status === 422) {
      return {
        type: ERROR_TYPES.VALIDATION,
        severity: ERROR_SEVERITY.MEDIUM,
        retryable: false,
        userMessage: "Please check your input and try again.",
        technicalMessage: errorMessage,
        suggestedActions: [
          "Review the form for errors",
          "Check required fields",
          "Ensure data is in the correct format",
        ],
      };
    }

    // Client errors (4xx)
    if (status >= 400 && status < 500) {
      return {
        type: ERROR_TYPES.CLIENT,
        severity: ERROR_SEVERITY.MEDIUM,
        retryable: false,
        userMessage: "There was a problem with your request.",
        technicalMessage: errorMessage,
        suggestedActions: [
          "Check your input",
          "Try refreshing the page",
          "Contact support if the problem persists",
        ],
      };
    }

    // Server errors (5xx)
    if (status >= 500) {
      return {
        type: ERROR_TYPES.SERVER,
        severity: ERROR_SEVERITY.HIGH,
        retryable: true,
        userMessage: "Server error. Please try again in a moment.",
        technicalMessage: errorMessage,
        suggestedActions: [
          "Try again in a few minutes",
          "Refresh the page",
          "Contact support if the problem persists",
        ],
      };
    }
  }

  // Default unknown error
  return {
    type: ERROR_TYPES.UNKNOWN,
    severity: ERROR_SEVERITY.MEDIUM,
    retryable: true,
    userMessage: "An unexpected error occurred. Please try again.",
    technicalMessage: errorMessage,
    suggestedActions: [
      "Try again",
      "Refresh the page",
      "Contact support if the problem persists",
    ],
  };
};

/**
 * Enhanced error handler with retry logic
 */
export class NetworkErrorHandler {
  constructor(options = {}) {
    this.maxRetries = options.maxRetries || 3;
    this.retryDelay = options.retryDelay || 1000;
    this.retryMultiplier = options.retryMultiplier || 2;
    this.onError = options.onError || console.error;
    this.onRetry = options.onRetry || console.warn;
  }

  /**
   * Execute a network operation with error handling and retry logic
   */
  async executeWithRetry(operation, context = {}) {
    let lastError;
    let retryCount = 0;

    while (retryCount <= this.maxRetries) {
      try {
        const result = await operation();

        // Reset retry count on success
        if (retryCount > 0) {
          console.log(`Operation succeeded after ${retryCount} retries`);
        }

        return result;
      } catch (error) {
        lastError = error;
        const errorInfo = categorizeError(error);

        // Log the error
        this.onError(error, { ...context, retryCount, errorInfo });

        // Don't retry if error is not retryable or max retries reached
        if (!errorInfo.retryable || retryCount >= this.maxRetries) {
          break;
        }

        retryCount++;
        const delay =
          this.retryDelay * Math.pow(this.retryMultiplier, retryCount - 1);

        this.onRetry(
          `Retrying operation (${retryCount}/${this.maxRetries}) after ${delay}ms`,
          {
            error: errorInfo,
            context,
          }
        );

        // Wait before retry
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }

    // All retries failed, throw the last error with enhanced information
    const enhancedError = new Error(lastError.message);
    enhancedError.originalError = lastError;
    enhancedError.retryCount = retryCount;
    enhancedError.maxRetries = this.maxRetries;
    enhancedError.errorInfo = categorizeError(lastError);

    throw enhancedError;
  }

  /**
   * Handle authentication-specific errors
   */
  async handleAuthError(error, authContext = {}) {
    const errorInfo = categorizeError(error);

    // Special handling for authentication errors
    if (errorInfo.type === ERROR_TYPES.AUTHENTICATION) {
      // Clear auth data
      if (authContext.clearAuth) {
        authContext.clearAuth();
      }

      // Redirect to login if not already there
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }

    return errorInfo;
  }

  /**
   * Create a fetch wrapper with error handling
   */
  createFetchWrapper() {
    return async (url, options = {}) => {
      const operation = async () => {
        const response = await fetch(url, {
          ...options,
          headers: {
            "Content-Type": "application/json",
            ...options.headers,
          },
        });

        if (!response.ok) {
          const error = new Error(
            `HTTP ${response.status}: ${response.statusText}`
          );
          error.status = response.status;
          error.response = response;
          throw error;
        }

        return response;
      };

      return this.executeWithRetry(operation, {
        url,
        method: options.method || "GET",
      });
    };
  }
}

/**
 * Global error handler instance
 */
export const globalErrorHandler = new NetworkErrorHandler({
  maxRetries: 3,
  retryDelay: 1000,
  onError: (error, context) => {
    console.error("Network operation failed:", error, context);

    // Report to error tracking service if available
    if (window.errorTracker) {
      window.errorTracker.captureException(error, {
        tags: { type: "network_error" },
        extra: context,
      });
    }
  },
  onRetry: (message, context) => {
    console.warn("Retrying network operation:", message, context);
  },
});

/**
 * Enhanced fetch with automatic error handling
 */
export const enhancedFetch = globalErrorHandler.createFetchWrapper();

/**
 * Utility to check if error is recoverable
 */
export const isRecoverableError = error => {
  const errorInfo = categorizeError(error);
  return errorInfo.retryable;
};

/**
 * Utility to get user-friendly error message
 */
export const getUserErrorMessage = error => {
  const errorInfo = categorizeError(error);
  return errorInfo.userMessage;
};

/**
 * Utility to get error suggestions
 */
export const getErrorSuggestions = error => {
  const errorInfo = categorizeError(error);
  return errorInfo.suggestedActions;
};

/**
 * Network status monitor
 */
export class NetworkStatusMonitor {
  constructor(onStatusChange) {
    this.isOnline = navigator.onLine;
    this.onStatusChange = onStatusChange;
    this.setupEventListeners();
  }

  setupEventListeners() {
    window.addEventListener("online", this.handleOnline.bind(this));
    window.addEventListener("offline", this.handleOffline.bind(this));
  }

  handleOnline() {
    this.isOnline = true;
    if (this.onStatusChange) {
      this.onStatusChange(true);
    }
  }

  handleOffline() {
    this.isOnline = false;
    if (this.onStatusChange) {
      this.onStatusChange(false);
    }
  }

  cleanup() {
    window.removeEventListener("online", this.handleOnline.bind(this));
    window.removeEventListener("offline", this.handleOffline.bind(this));
  }
}

export default {
  ERROR_TYPES,
  ERROR_SEVERITY,
  categorizeError,
  NetworkErrorHandler,
  globalErrorHandler,
  enhancedFetch,
  isRecoverableError,
  getUserErrorMessage,
  getErrorSuggestions,
  NetworkStatusMonitor,
};
