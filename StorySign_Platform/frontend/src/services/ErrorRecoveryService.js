/**
 * Error Recovery Service
 * Provides centralized error recovery mechanisms for the application
 */

import React from "react";
import {
  categorizeError,
  ERROR_TYPES,
  NetworkStatusMonitor,
} from "../utils/networkErrorHandler";
import {
  categorizeAuthError,
  AUTH_ERROR_TYPES,
} from "../utils/authErrorHandler";

/**
 * Recovery strategies for different error types
 */
export const RECOVERY_STRATEGIES = {
  RETRY: "retry",
  RELOAD: "reload",
  REDIRECT: "redirect",
  CLEAR_CACHE: "clear_cache",
  LOGOUT: "logout",
  MANUAL: "manual",
};

/**
 * Error Recovery Service class
 */
export class ErrorRecoveryService {
  constructor(options = {}) {
    this.maxRetries = options.maxRetries || 3;
    this.retryDelay = options.retryDelay || 1000;
    this.onRecoveryAttempt = options.onRecoveryAttempt || console.log;
    this.onRecoverySuccess = options.onRecoverySuccess || console.log;
    this.onRecoveryFailure = options.onRecoveryFailure || console.error;

    // Track recovery attempts
    this.recoveryAttempts = new Map();

    // Network status monitoring
    this.networkMonitor = new NetworkStatusMonitor(
      this.handleNetworkStatusChange.bind(this)
    );
    this.isOnline = navigator.onLine;

    // Queue for operations to retry when network comes back
    this.pendingOperations = [];
  }

  /**
   * Determine recovery strategy for an error
   */
  determineRecoveryStrategy(error, context = {}) {
    const errorInfo = categorizeError(error);
    const authErrorInfo = categorizeAuthError(error);

    // Network errors - retry when connection is restored
    if (errorInfo.type === ERROR_TYPES.NETWORK) {
      return {
        strategy: RECOVERY_STRATEGIES.RETRY,
        delay: this.retryDelay,
        maxAttempts: this.maxRetries,
        condition: () => this.isOnline,
        description: "Retry when network connection is restored",
      };
    }

    // Chunk loading errors - reload page
    if (errorInfo.type === ERROR_TYPES.CHUNK_LOAD) {
      return {
        strategy: RECOVERY_STRATEGIES.RELOAD,
        delay: 1000,
        maxAttempts: 1,
        description: "Reload page to fetch updated resources",
      };
    }

    // Authentication errors - logout and redirect
    if (errorInfo.type === ERROR_TYPES.AUTHENTICATION) {
      return {
        strategy: RECOVERY_STRATEGIES.LOGOUT,
        delay: 0,
        maxAttempts: 1,
        description: "Clear authentication and redirect to login",
      };
    }

    // Server errors - retry with exponential backoff
    if (errorInfo.type === ERROR_TYPES.SERVER) {
      return {
        strategy: RECOVERY_STRATEGIES.RETRY,
        delay: this.retryDelay,
        maxAttempts: this.maxRetries,
        exponentialBackoff: true,
        description: "Retry with exponential backoff",
      };
    }

    // Timeout errors - retry with longer delay
    if (errorInfo.type === ERROR_TYPES.TIMEOUT) {
      return {
        strategy: RECOVERY_STRATEGIES.RETRY,
        delay: this.retryDelay * 2,
        maxAttempts: 2,
        description: "Retry with longer timeout",
      };
    }

    // Default - manual recovery
    return {
      strategy: RECOVERY_STRATEGIES.MANUAL,
      delay: 0,
      maxAttempts: 0,
      description: "Manual intervention required",
    };
  }

  /**
   * Execute recovery strategy
   */
  async executeRecovery(error, operation, context = {}) {
    const recoveryPlan = this.determineRecoveryStrategy(error, context);
    const operationId = context.operationId || `op_${Date.now()}`;

    // Track recovery attempt
    const attempts = this.recoveryAttempts.get(operationId) || 0;
    this.recoveryAttempts.set(operationId, attempts + 1);

    this.onRecoveryAttempt({
      operationId,
      error,
      recoveryPlan,
      attempt: attempts + 1,
      context,
    });

    try {
      switch (recoveryPlan.strategy) {
        case RECOVERY_STRATEGIES.RETRY:
          return await this.executeRetryRecovery(
            error,
            operation,
            recoveryPlan,
            operationId
          );

        case RECOVERY_STRATEGIES.RELOAD:
          return await this.executeReloadRecovery(
            error,
            recoveryPlan,
            operationId
          );

        case RECOVERY_STRATEGIES.REDIRECT:
          return await this.executeRedirectRecovery(
            error,
            recoveryPlan,
            operationId,
            context
          );

        case RECOVERY_STRATEGIES.CLEAR_CACHE:
          return await this.executeClearCacheRecovery(
            error,
            operation,
            recoveryPlan,
            operationId
          );

        case RECOVERY_STRATEGIES.LOGOUT:
          return await this.executeLogoutRecovery(
            error,
            recoveryPlan,
            operationId,
            context
          );

        default:
          throw new Error(
            `Recovery strategy ${recoveryPlan.strategy} requires manual intervention`
          );
      }
    } catch (recoveryError) {
      this.onRecoveryFailure({
        operationId,
        originalError: error,
        recoveryError,
        recoveryPlan,
        attempt: attempts + 1,
      });
      throw recoveryError;
    }
  }

  /**
   * Execute retry recovery strategy
   */
  async executeRetryRecovery(error, operation, recoveryPlan, operationId) {
    const attempts = this.recoveryAttempts.get(operationId) || 0;

    if (attempts >= recoveryPlan.maxAttempts) {
      throw new Error(
        `Max recovery attempts (${recoveryPlan.maxAttempts}) reached for operation ${operationId}`
      );
    }

    // Check condition if specified
    if (recoveryPlan.condition && !recoveryPlan.condition()) {
      // Queue operation for later if condition not met
      this.queueOperation(operation, operationId, recoveryPlan);
      throw new Error("Recovery condition not met, operation queued");
    }

    // Calculate delay with exponential backoff if specified
    let delay = recoveryPlan.delay;
    if (recoveryPlan.exponentialBackoff) {
      delay = recoveryPlan.delay * Math.pow(2, attempts);
    }

    // Wait before retry
    if (delay > 0) {
      await new Promise(resolve => setTimeout(resolve, delay));
    }

    // Retry the operation
    try {
      const result = await operation();

      this.onRecoverySuccess({
        operationId,
        strategy: recoveryPlan.strategy,
        attempt: attempts + 1,
        result,
      });

      // Clear recovery attempts on success
      this.recoveryAttempts.delete(operationId);

      return result;
    } catch (retryError) {
      // Update attempt count and re-throw for potential further recovery
      this.recoveryAttempts.set(operationId, attempts + 1);
      throw retryError;
    }
  }

  /**
   * Execute reload recovery strategy
   */
  async executeReloadRecovery(error, recoveryPlan, operationId) {
    this.onRecoverySuccess({
      operationId,
      strategy: recoveryPlan.strategy,
      description: "Reloading page to recover from error",
    });

    // Add a small delay to allow logging
    setTimeout(() => {
      window.location.reload();
    }, recoveryPlan.delay);

    // Return a promise that never resolves since page will reload
    return new Promise(() => {});
  }

  /**
   * Execute redirect recovery strategy
   */
  async executeRedirectRecovery(error, recoveryPlan, operationId, context) {
    const redirectUrl = context.redirectUrl || "/";

    this.onRecoverySuccess({
      operationId,
      strategy: recoveryPlan.strategy,
      redirectUrl,
      description: `Redirecting to ${redirectUrl}`,
    });

    setTimeout(() => {
      window.location.href = redirectUrl;
    }, recoveryPlan.delay);

    return { redirected: true, url: redirectUrl };
  }

  /**
   * Execute clear cache recovery strategy
   */
  async executeClearCacheRecovery(error, operation, recoveryPlan, operationId) {
    try {
      // Clear various caches
      if ("caches" in window) {
        const cacheNames = await caches.keys();
        await Promise.all(cacheNames.map(name => caches.delete(name)));
      }

      // Clear localStorage (selectively)
      this.clearSelectiveStorage();

      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, recoveryPlan.delay));

      // Retry operation
      const result = await operation();

      this.onRecoverySuccess({
        operationId,
        strategy: recoveryPlan.strategy,
        description: "Cache cleared and operation retried successfully",
      });

      return result;
    } catch (clearError) {
      throw new Error(`Cache clear recovery failed: ${clearError.message}`);
    }
  }

  /**
   * Execute logout recovery strategy
   */
  async executeLogoutRecovery(error, recoveryPlan, operationId, context) {
    try {
      // Clear authentication data
      this.clearAuthData();

      // Redirect to login
      const returnUrl = context.returnUrl || window.location.pathname;
      const loginUrl = `/login${
        returnUrl !== "/login" ? `?return=${encodeURIComponent(returnUrl)}` : ""
      }`;

      this.onRecoverySuccess({
        operationId,
        strategy: recoveryPlan.strategy,
        description: "Logged out and redirecting to login",
      });

      setTimeout(() => {
        window.location.href = loginUrl;
      }, recoveryPlan.delay);

      return { loggedOut: true, redirectUrl: loginUrl };
    } catch (logoutError) {
      throw new Error(`Logout recovery failed: ${logoutError.message}`);
    }
  }

  /**
   * Queue operation for later execution
   */
  queueOperation(operation, operationId, recoveryPlan) {
    this.pendingOperations.push({
      operation,
      operationId,
      recoveryPlan,
      queuedAt: Date.now(),
    });
  }

  /**
   * Process queued operations
   */
  async processQueuedOperations() {
    const operations = [...this.pendingOperations];
    this.pendingOperations = [];

    for (const { operation, operationId, recoveryPlan } of operations) {
      try {
        await this.executeRetryRecovery(
          null,
          operation,
          recoveryPlan,
          operationId
        );
      } catch (error) {
        console.error(
          `Failed to process queued operation ${operationId}:`,
          error
        );
        // Re-queue if still retryable
        if (this.recoveryAttempts.get(operationId) < recoveryPlan.maxAttempts) {
          this.queueOperation(operation, operationId, recoveryPlan);
        }
      }
    }
  }

  /**
   * Handle network status changes
   */
  handleNetworkStatusChange(isOnline) {
    this.isOnline = isOnline;

    if (isOnline) {
      console.log("Network connection restored, processing queued operations");
      this.processQueuedOperations();
    } else {
      console.warn("Network connection lost");
    }
  }

  /**
   * Clear selective storage (preserve important data)
   */
  clearSelectiveStorage() {
    const preserveKeys = [
      "user_preferences",
      "theme_settings",
      "language_settings",
    ];

    try {
      // Clear localStorage except preserved keys
      const keysToRemove = [];
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && !preserveKeys.includes(key)) {
          keysToRemove.push(key);
        }
      }
      keysToRemove.forEach(key => localStorage.removeItem(key));

      // Clear all sessionStorage
      sessionStorage.clear();
    } catch (error) {
      console.error("Error clearing selective storage:", error);
    }
  }

  /**
   * Clear authentication data
   */
  clearAuthData() {
    const authKeys = [
      "auth_token",
      "refresh_token",
      "user_data",
      "session_data",
    ];

    try {
      authKeys.forEach(key => {
        localStorage.removeItem(key);
        sessionStorage.removeItem(key);
      });
    } catch (error) {
      console.error("Error clearing auth data:", error);
    }
  }

  /**
   * Get recovery statistics
   */
  getRecoveryStats() {
    return {
      totalAttempts: this.recoveryAttempts.size,
      pendingOperations: this.pendingOperations.length,
      isOnline: this.isOnline,
      attempts: Object.fromEntries(this.recoveryAttempts),
    };
  }

  /**
   * Cleanup method
   */
  cleanup() {
    this.networkMonitor.cleanup();
    this.recoveryAttempts.clear();
    this.pendingOperations = [];
  }
}

/**
 * Global error recovery service instance
 */
export const globalErrorRecovery = new ErrorRecoveryService({
  onRecoveryAttempt: info => {
    console.log("Recovery attempt:", info);
  },
  onRecoverySuccess: info => {
    console.log("Recovery successful:", info);
  },
  onRecoveryFailure: info => {
    console.error("Recovery failed:", info);
  },
});

/**
 * React hook for using error recovery service
 */
export const useErrorRecovery = () => {
  const [recoveryService] = React.useState(() => globalErrorRecovery);

  React.useEffect(() => {
    return () => {
      // Don't cleanup global service, just return empty cleanup
    };
  }, []);

  const recoverFromError = React.useCallback(
    async (error, operation, context = {}) => {
      return recoveryService.executeRecovery(error, operation, context);
    },
    [recoveryService]
  );

  const getRecoveryStats = React.useCallback(() => {
    return recoveryService.getRecoveryStats();
  }, [recoveryService]);

  return {
    recoverFromError,
    getRecoveryStats,
    isOnline: recoveryService.isOnline,
  };
};

export default {
  RECOVERY_STRATEGIES,
  ErrorRecoveryService,
  globalErrorRecovery,
  useErrorRecovery,
};
