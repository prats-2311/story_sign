import React, { createContext, useContext, useReducer, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import authService from "../services/AuthService";

// Action types for the auth reducer
const AUTH_ACTIONS = {
  LOGIN_START: "LOGIN_START",
  LOGIN_SUCCESS: "LOGIN_SUCCESS",
  LOGIN_FAILURE: "LOGIN_FAILURE",
  LOGOUT: "LOGOUT",
  REFRESH_TOKEN: "REFRESH_TOKEN",
  UPDATE_USER: "UPDATE_USER",
  SET_LOADING: "SET_LOADING",
  CLEAR_ERROR: "CLEAR_ERROR",
  SET_RETRY_COUNT: "SET_RETRY_COUNT",
  RESET_RETRY_COUNT: "RESET_RETRY_COUNT",
};

// Initial state for authentication
const initialState = {
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
  errorType: null, // 'network', 'validation', 'server', 'auth'
  retryCount: 0,
  maxRetries: 3,
  canRetry: false,
};

// Auth reducer to manage authentication state
const authReducer = (state, action) => {
  switch (action.type) {
    case AUTH_ACTIONS.LOGIN_START:
      return {
        ...state,
        isLoading: true,
        error: null,
      };

    case AUTH_ACTIONS.LOGIN_SUCCESS:
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      };

    case AUTH_ACTIONS.LOGIN_FAILURE:
      return {
        ...state,
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload.error,
        errorType: action.payload.errorType || "auth",
        canRetry: action.payload.canRetry || false,
      };

    case AUTH_ACTIONS.LOGOUT:
      return {
        ...state,
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      };

    case AUTH_ACTIONS.REFRESH_TOKEN:
      return {
        ...state,
        token: action.payload.token,
        user: action.payload.user || state.user,
      };

    case AUTH_ACTIONS.UPDATE_USER:
      return {
        ...state,
        user: { ...state.user, ...action.payload.user },
      };

    case AUTH_ACTIONS.SET_LOADING:
      return {
        ...state,
        isLoading: action.payload.isLoading,
      };

    case AUTH_ACTIONS.CLEAR_ERROR:
      return {
        ...state,
        error: null,
        errorType: null,
        canRetry: false,
      };

    case AUTH_ACTIONS.SET_RETRY_COUNT:
      return {
        ...state,
        retryCount: action.payload.retryCount,
      };

    case AUTH_ACTIONS.RESET_RETRY_COUNT:
      return {
        ...state,
        retryCount: 0,
      };

    default:
      return state;
  }
};

// Helper function to categorize errors and determine retry eligibility
const categorizeError = error => {
  const errorMessage = error.message || error.toString();

  // Network errors - can retry
  if (
    errorMessage.includes("Unable to connect") ||
    errorMessage.includes("network") ||
    errorMessage.includes("fetch") ||
    errorMessage.includes("NetworkError") ||
    error.name === "TypeError"
  ) {
    return {
      type: "network",
      canRetry: true,
      userMessage:
        "Connection failed. Please check your internet connection and try again.",
    };
  }

  // Server errors (5xx) - can retry
  if (
    errorMessage.includes("server error") ||
    errorMessage.includes("Server temporarily unavailable") ||
    errorMessage.includes("500") ||
    errorMessage.includes("502") ||
    errorMessage.includes("503") ||
    errorMessage.includes("504") ||
    (error.status && error.status >= 500)
  ) {
    return {
      type: "server",
      canRetry: true,
      userMessage:
        "Server temporarily unavailable. Please try again in a moment.",
    };
  }

  // Authentication errors - cannot retry without user action
  if (
    errorMessage.includes("Invalid credentials") ||
    errorMessage.includes("incorrect password") ||
    errorMessage.includes("user not found") ||
    errorMessage.includes("invalid email") ||
    errorMessage.includes("unauthorized")
  ) {
    return {
      type: "auth",
      canRetry: false,
      userMessage:
        "Invalid email or password. Please check your credentials and try again.",
    };
  }

  // Validation errors - cannot retry without user action
  if (
    errorMessage.includes("validation") ||
    errorMessage.includes("required") ||
    errorMessage.includes("invalid format") ||
    errorMessage.includes("already exists")
  ) {
    return {
      type: "validation",
      canRetry: false,
      userMessage: errorMessage, // Use the specific validation message
    };
  }

  // Default to auth error if we can't categorize
  return {
    type: "auth",
    canRetry: false,
    userMessage: errorMessage || "Authentication failed. Please try again.",
  };
};

// Create the AuthContext
const AuthContext = createContext();

// Custom hook to use the AuthContext
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

// AuthProvider component
export const AuthProvider = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);
  const navigate = useNavigate();

  // Initialize authentication state on app load
  useEffect(() => {
    const initializeAuth = async () => {
      dispatch({
        type: AUTH_ACTIONS.SET_LOADING,
        payload: { isLoading: true },
      });

      try {
        // Check if user is already authenticated
        if (authService.isAuthenticated()) {
          const user = authService.getCurrentUser();
          const token = authService.getToken();

          if (user && token) {
            // Verify token with server
            const verifiedUser = await authService.verifyToken();

            if (verifiedUser) {
              dispatch({
                type: AUTH_ACTIONS.LOGIN_SUCCESS,
                payload: {
                  user: verifiedUser,
                  token: token,
                },
              });
            } else {
              // Token verification failed, clear auth data
              authService.clearAuthData();
              dispatch({ type: AUTH_ACTIONS.LOGOUT });
            }
          } else {
            dispatch({ type: AUTH_ACTIONS.LOGOUT });
          }
        } else {
          dispatch({ type: AUTH_ACTIONS.LOGOUT });
        }
      } catch (error) {
        console.error("Auth initialization error:", error);
        authService.clearAuthData();
        dispatch({ type: AUTH_ACTIONS.LOGOUT });
      } finally {
        dispatch({
          type: AUTH_ACTIONS.SET_LOADING,
          payload: { isLoading: false },
        });
      }
    };

    initializeAuth();
  }, []);

  // Set up automatic token refresh
  useEffect(() => {
    let refreshInterval;

    if (state.isAuthenticated && state.token) {
      // Refresh token every 15 minutes
      refreshInterval = setInterval(async () => {
        try {
          const refreshed = await authService.refreshToken();
          if (refreshed) {
            const newToken = authService.getToken();
            const user = authService.getCurrentUser();

            dispatch({
              type: AUTH_ACTIONS.REFRESH_TOKEN,
              payload: {
                token: newToken,
                user: user,
              },
            });
          } else {
            // Refresh failed, logout user
            await logout();
          }
        } catch (error) {
          console.error("Token refresh error:", error);
          await logout();
        }
      }, 15 * 60 * 1000); // 15 minutes
    }

    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, [state.isAuthenticated, state.token]);

  // Login function with retry logic
  const login = async (
    email,
    password,
    rememberMe = false,
    isRetry = false
  ) => {
    dispatch({ type: AUTH_ACTIONS.LOGIN_START });

    try {
      const response = await authService.login(email, password, rememberMe);

      // Reset retry count on success
      dispatch({ type: AUTH_ACTIONS.RESET_RETRY_COUNT });

      dispatch({
        type: AUTH_ACTIONS.LOGIN_SUCCESS,
        payload: {
          user: response.user,
          token: response.token,
        },
      });

      return response;
    } catch (error) {
      const errorInfo = categorizeError(error);
      const currentRetryCount = isRetry ? state.retryCount + 1 : 1;

      // Update retry count
      dispatch({
        type: AUTH_ACTIONS.SET_RETRY_COUNT,
        payload: { retryCount: currentRetryCount },
      });

      const canRetry =
        errorInfo.canRetry && currentRetryCount < state.maxRetries;

      dispatch({
        type: AUTH_ACTIONS.LOGIN_FAILURE,
        payload: {
          error: errorInfo.userMessage,
          errorType: errorInfo.type,
          canRetry: canRetry,
        },
      });

      // Add retry count info to error for UI display
      const enhancedError = new Error(errorInfo.userMessage);
      enhancedError.type = errorInfo.type;
      enhancedError.canRetry = canRetry;
      enhancedError.retryCount = currentRetryCount;
      enhancedError.maxRetries = state.maxRetries;

      throw enhancedError;
    }
  };

  // Register function with retry logic
  const register = async (userData, isRetry = false) => {
    dispatch({ type: AUTH_ACTIONS.LOGIN_START });

    try {
      const response = await authService.register(userData);

      // Reset retry count on success
      dispatch({ type: AUTH_ACTIONS.RESET_RETRY_COUNT });

      // Registration successful, but don't auto-login
      dispatch({
        type: AUTH_ACTIONS.SET_LOADING,
        payload: { isLoading: false },
      });

      return response;
    } catch (error) {
      const errorInfo = categorizeError(error);
      const currentRetryCount = isRetry ? state.retryCount + 1 : 1;

      // Update retry count
      dispatch({
        type: AUTH_ACTIONS.SET_RETRY_COUNT,
        payload: { retryCount: currentRetryCount },
      });

      const canRetry =
        errorInfo.canRetry && currentRetryCount < state.maxRetries;

      dispatch({
        type: AUTH_ACTIONS.LOGIN_FAILURE,
        payload: {
          error: errorInfo.userMessage,
          errorType: errorInfo.type,
          canRetry: canRetry,
        },
      });

      // Add retry count info to error for UI display
      const enhancedError = new Error(errorInfo.userMessage);
      enhancedError.type = errorInfo.type;
      enhancedError.canRetry = canRetry;
      enhancedError.retryCount = currentRetryCount;
      enhancedError.maxRetries = state.maxRetries;

      throw enhancedError;
    }
  };

  // Logout function with localStorage cleanup and navigation
  const logout = async () => {
    try {
      // Call the auth service logout (which already handles server logout and localStorage cleanup)
      await authService.logout();
    } catch (error) {
      console.error("Logout error:", error);
      // Even if server logout fails, we still want to clear local data and navigate
      authService.clearAuthData();
    } finally {
      // Update authentication state
      dispatch({ type: AUTH_ACTIONS.LOGOUT });

      // Navigate to login page
      try {
        navigate("/login", { replace: true });
      } catch (navigationError) {
        console.error("Navigation error during logout:", navigationError);
        // Fallback navigation if React Router navigation fails
        window.location.href = "/login";
      }
    }
  };

  // Update user profile
  const updateProfile = async profileData => {
    try {
      const updatedUser = await authService.updateProfile(profileData);

      dispatch({
        type: AUTH_ACTIONS.UPDATE_USER,
        payload: { user: updatedUser },
      });

      return updatedUser;
    } catch (error) {
      console.error("Profile update error:", error);
      throw error;
    }
  };

  // Change password
  const changePassword = async (currentPassword, newPassword) => {
    try {
      const response = await authService.changePassword(
        currentPassword,
        newPassword
      );
      return response;
    } catch (error) {
      console.error("Password change error:", error);
      throw error;
    }
  };

  // Request password reset
  const requestPasswordReset = async email => {
    try {
      const response = await authService.requestPasswordReset(email);
      return response;
    } catch (error) {
      console.error("Password reset request error:", error);
      throw error;
    }
  };

  // Reset password with token
  const resetPassword = async (token, newPassword) => {
    try {
      const response = await authService.resetPassword(token, newPassword);
      return response;
    } catch (error) {
      console.error("Password reset error:", error);
      throw error;
    }
  };

  // Clear authentication error
  const clearError = () => {
    dispatch({ type: AUTH_ACTIONS.CLEAR_ERROR });
  };

  // Check if user has specific role or permission
  const hasRole = role => {
    return state.user?.roles?.includes(role) || false;
  };

  const hasPermission = permission => {
    return state.user?.permissions?.includes(permission) || false;
  };

  // Retry last failed authentication attempt
  const retryAuthentication = async lastAttemptData => {
    if (!state.canRetry || state.retryCount >= state.maxRetries) {
      throw new Error("Maximum retry attempts reached");
    }

    if (lastAttemptData.type === "login") {
      return await login(
        lastAttemptData.email,
        lastAttemptData.password,
        lastAttemptData.rememberMe,
        true // isRetry
      );
    } else if (lastAttemptData.type === "register") {
      return await register(lastAttemptData.userData, true); // isRetry
    }

    throw new Error("Invalid retry attempt type");
  };

  // Context value
  const value = {
    // State
    user: state.user,
    token: state.token,
    isAuthenticated: state.isAuthenticated,
    isLoading: state.isLoading,
    error: state.error,
    errorType: state.errorType,
    retryCount: state.retryCount,
    maxRetries: state.maxRetries,
    canRetry: state.canRetry,

    // Actions
    login,
    register,
    logout,
    updateProfile,
    changePassword,
    requestPasswordReset,
    resetPassword,
    clearError,
    retryAuthentication,

    // Utilities
    hasRole,
    hasPermission,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;
