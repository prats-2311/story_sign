/**
 * Authentication Error Handler
 * Specialized error handling for authentication operations
 */

import React from "react";
import {
  categorizeError,
  ERROR_TYPES,
  NetworkErrorHandler,
} from "./networkErrorHandler";

/**
 * Authentication-specific error types
 */
export const AUTH_ERROR_TYPES = {
  INVALID_CREDENTIALS: "invalid_credentials",
  SESSION_EXPIRED: "session_expired",
  TOKEN_INVALID: "token_invalid",
  ACCOUNT_LOCKED: "account_locked",
  ACCOUNT_DISABLED: "account_disabled",
  EMAIL_NOT_VERIFIED: "email_not_verified",
  PASSWORD_EXPIRED: "password_expired",
  MFA_REQUIRED: "mfa_required",
  RATE_LIMITED: "rate_limited",
  NETWORK_ERROR: "network_error",
  SERVER_ERROR: "server_error",
};

/**
 * Enhanced authentication error categorization
 */
export const categorizeAuthError = (error, response = null) => {
  const baseError = categorizeError(error, response);
  const errorMessage = error.message || error.toString();
  const status = response?.status || error.status;

  // Authentication-specific error patterns
  if (
    errorMessage.includes("Invalid credentials") ||
    errorMessage.includes("incorrect password") ||
    errorMessage.includes("wrong password") ||
    errorMessage.includes("invalid email") ||
    status === 401
  ) {
    return {
      ...baseError,
      authType: AUTH_ERROR_TYPES.INVALID_CREDENTIALS,
      userMessage:
        "Invalid email or password. Please check your credentials and try again.",
      retryable: false,
      suggestedActions: [
        "Double-check your email and password",
        'Try using the "Forgot Password" option',
        "Ensure Caps Lock is not enabled",
        "Contact support if you continue having issues",
      ],
    };
  }

  if (
    errorMessage.includes("session expired") ||
    errorMessage.includes("token expired") ||
    errorMessage.includes("authentication expired")
  ) {
    return {
      ...baseError,
      authType: AUTH_ERROR_TYPES.SESSION_EXPIRED,
      userMessage: "Your session has expired. Please sign in again.",
      retryable: false,
      suggestedActions: [
        "Sign in again",
        'Enable "Remember Me" for longer sessions',
        "Check if your system clock is correct",
      ],
    };
  }

  if (
    errorMessage.includes("invalid token") ||
    errorMessage.includes("malformed token") ||
    errorMessage.includes("token verification failed")
  ) {
    return {
      ...baseError,
      authType: AUTH_ERROR_TYPES.TOKEN_INVALID,
      userMessage: "Authentication token is invalid. Please sign in again.",
      retryable: false,
      suggestedActions: [
        "Sign in again",
        "Clear your browser cache",
        "Try using an incognito/private window",
      ],
    };
  }

  if (
    errorMessage.includes("account locked") ||
    errorMessage.includes("too many attempts") ||
    errorMessage.includes("temporarily locked")
  ) {
    return {
      ...baseError,
      authType: AUTH_ERROR_TYPES.ACCOUNT_LOCKED,
      userMessage:
        "Account temporarily locked due to multiple failed attempts.",
      retryable: false,
      suggestedActions: [
        "Wait 15-30 minutes before trying again",
        'Use the "Forgot Password" option',
        "Contact support if you need immediate access",
      ],
    };
  }

  if (
    errorMessage.includes("account disabled") ||
    errorMessage.includes("account suspended") ||
    errorMessage.includes("user inactive")
  ) {
    return {
      ...baseError,
      authType: AUTH_ERROR_TYPES.ACCOUNT_DISABLED,
      userMessage: "Your account has been disabled. Please contact support.",
      retryable: false,
      suggestedActions: [
        "Contact support for account reactivation",
        "Check your email for account status notifications",
      ],
    };
  }

  if (
    errorMessage.includes("email not verified") ||
    errorMessage.includes("verify your email") ||
    errorMessage.includes("email verification required")
  ) {
    return {
      ...baseError,
      authType: AUTH_ERROR_TYPES.EMAIL_NOT_VERIFIED,
      userMessage: "Please verify your email address before signing in.",
      retryable: false,
      suggestedActions: [
        "Check your email for verification link",
        "Check spam/junk folder",
        "Request a new verification email",
        "Contact support if you need help",
      ],
    };
  }

  if (
    errorMessage.includes("rate limit") ||
    errorMessage.includes("too many requests") ||
    status === 429
  ) {
    return {
      ...baseError,
      authType: AUTH_ERROR_TYPES.RATE_LIMITED,
      userMessage:
        "Too many login attempts. Please wait a moment and try again.",
      retryable: true,
      suggestedActions: [
        "Wait a few minutes before trying again",
        "Avoid rapid repeated attempts",
        "Contact support if the issue persists",
      ],
    };
  }

  // Return base error with auth context
  return {
    ...baseError,
    authType:
      baseError.type === ERROR_TYPES.NETWORK
        ? AUTH_ERROR_TYPES.NETWORK_ERROR
        : AUTH_ERROR_TYPES.SERVER_ERROR,
  };
};

/**
 * Authentication Error Handler class
 */
export class AuthErrorHandler extends NetworkErrorHandler {
  constructor(authContext, options = {}) {
    super({
      maxRetries: 2, // Lower retry count for auth operations
      retryDelay: 2000, // Longer delay for auth retries
      ...options,
    });

    this.authContext = authContext;
    this.loginAttempts = new Map(); // Track login attempts per email
    this.maxLoginAttempts = 5;
    this.lockoutDuration = 15 * 60 * 1000; // 15 minutes
  }

  /**
   * Handle login errors with attempt tracking
   */
  async handleLoginError(error, email, response = null) {
    const errorInfo = categorizeAuthError(error, response);

    // Track login attempts
    if (email) {
      this.trackLoginAttempt(email, errorInfo);
    }

    // Clear auth data on authentication errors
    if (errorInfo.type === ERROR_TYPES.AUTHENTICATION) {
      this.clearAuthData();
    }

    // Log error with context
    console.error("Login error:", {
      error: errorInfo,
      email: email ? email.substring(0, 3) + "***" : "unknown",
      attempts: this.getLoginAttempts(email),
    });

    return errorInfo;
  }

  /**
   * Handle registration errors
   */
  async handleRegistrationError(error, userData, response = null) {
    const errorInfo = categorizeAuthError(error, response);

    // Log error with context (without sensitive data)
    console.error("Registration error:", {
      error: errorInfo,
      email: userData?.email
        ? userData.email.substring(0, 3) + "***"
        : "unknown",
    });

    return errorInfo;
  }

  /**
   * Handle token refresh errors
   */
  async handleTokenRefreshError(error, response = null) {
    const errorInfo = categorizeAuthError(error, response);

    // Clear auth data and redirect to login on token refresh failure
    if (errorInfo.type === ERROR_TYPES.AUTHENTICATION) {
      this.clearAuthData();
      this.redirectToLogin();
    }

    console.error("Token refresh error:", errorInfo);
    return errorInfo;
  }

  /**
   * Track login attempts for rate limiting
   */
  trackLoginAttempt(email, errorInfo) {
    if (!email) return;

    const now = Date.now();
    const attempts = this.loginAttempts.get(email) || [];

    // Remove old attempts (outside lockout window)
    const recentAttempts = attempts.filter(
      attempt => now - attempt.timestamp < this.lockoutDuration
    );

    // Add current attempt if it's a failed login
    if (errorInfo.authType === AUTH_ERROR_TYPES.INVALID_CREDENTIALS) {
      recentAttempts.push({
        timestamp: now,
        error: errorInfo.authType,
      });
    }

    this.loginAttempts.set(email, recentAttempts);

    // Check if account should be temporarily locked
    if (recentAttempts.length >= this.maxLoginAttempts) {
      console.warn(
        `Account temporarily locked for ${email} due to multiple failed attempts`
      );
    }
  }

  /**
   * Get login attempt count for email
   */
  getLoginAttempts(email) {
    if (!email) return 0;

    const attempts = this.loginAttempts.get(email) || [];
    const now = Date.now();

    return attempts.filter(
      attempt => now - attempt.timestamp < this.lockoutDuration
    ).length;
  }

  /**
   * Check if email is temporarily locked
   */
  isEmailLocked(email) {
    return this.getLoginAttempts(email) >= this.maxLoginAttempts;
  }

  /**
   * Clear authentication data
   */
  clearAuthData() {
    try {
      // Clear localStorage
      localStorage.removeItem("auth_token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("user_data");

      // Clear sessionStorage
      sessionStorage.removeItem("auth_token");
      sessionStorage.removeItem("user_data");

      // Clear auth context if available
      if (this.authContext && this.authContext.clearError) {
        this.authContext.clearError();
      }
    } catch (error) {
      console.error("Error clearing auth data:", error);
    }
  }

  /**
   * Redirect to login page
   */
  redirectToLogin(returnUrl = null) {
    const currentPath = window.location.pathname;

    // Don't redirect if already on login/register pages
    if (currentPath === "/login" || currentPath === "/register") {
      return;
    }

    // Build login URL with return path
    let loginUrl = "/login";
    if (returnUrl || (currentPath !== "/" && currentPath !== "/login")) {
      const returnPath = returnUrl || currentPath;
      loginUrl += `?return=${encodeURIComponent(returnPath)}`;
    }

    window.location.href = loginUrl;
  }

  /**
   * Create enhanced login function with error handling
   */
  createEnhancedLogin(originalLogin) {
    return async (email, password, rememberMe = false) => {
      // Check if email is temporarily locked
      if (this.isEmailLocked(email)) {
        const error = new Error(
          "Account temporarily locked due to multiple failed attempts"
        );
        const errorInfo = await this.handleLoginError(error, email);
        throw Object.assign(error, { errorInfo });
      }

      try {
        const result = await originalLogin(email, password, rememberMe);

        // Clear login attempts on successful login
        if (email) {
          this.loginAttempts.delete(email);
        }

        return result;
      } catch (error) {
        const errorInfo = await this.handleLoginError(error, email);
        throw Object.assign(error, { errorInfo });
      }
    };
  }

  /**
   * Create enhanced register function with error handling
   */
  createEnhancedRegister(originalRegister) {
    return async userData => {
      try {
        return await originalRegister(userData);
      } catch (error) {
        const errorInfo = await this.handleRegistrationError(error, userData);
        throw Object.assign(error, { errorInfo });
      }
    };
  }

  /**
   * Create enhanced token refresh function
   */
  createEnhancedTokenRefresh(originalRefresh) {
    return async () => {
      try {
        return await originalRefresh();
      } catch (error) {
        const errorInfo = await this.handleTokenRefreshError(error);
        throw Object.assign(error, { errorInfo });
      }
    };
  }

  /**
   * Cleanup method
   */
  cleanup() {
    this.loginAttempts.clear();
  }
}

/**
 * Create auth error handler hook
 */
export const useAuthErrorHandler = authContext => {
  const [authErrorHandler] = React.useState(
    () => new AuthErrorHandler(authContext)
  );

  React.useEffect(() => {
    return () => authErrorHandler.cleanup();
  }, [authErrorHandler]);

  return authErrorHandler;
};

export default {
  AUTH_ERROR_TYPES,
  categorizeAuthError,
  AuthErrorHandler,
  useAuthErrorHandler,
};
