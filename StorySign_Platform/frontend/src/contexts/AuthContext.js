import React, { createContext, useContext, useReducer, useEffect } from "react";
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
};

// Initial state for authentication
const initialState = {
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
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
      };

    default:
      return state;
  }
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

  // Login function
  const login = async (email, password, rememberMe = false) => {
    dispatch({ type: AUTH_ACTIONS.LOGIN_START });

    try {
      const response = await authService.login(email, password, rememberMe);

      dispatch({
        type: AUTH_ACTIONS.LOGIN_SUCCESS,
        payload: {
          user: response.user,
          token: response.token,
        },
      });

      return response;
    } catch (error) {
      dispatch({
        type: AUTH_ACTIONS.LOGIN_FAILURE,
        payload: { error: error.message },
      });
      throw error;
    }
  };

  // Register function
  const register = async (userData) => {
    dispatch({ type: AUTH_ACTIONS.LOGIN_START });

    try {
      const response = await authService.register(userData);

      // Registration successful, but don't auto-login
      dispatch({
        type: AUTH_ACTIONS.SET_LOADING,
        payload: { isLoading: false },
      });

      return response;
    } catch (error) {
      dispatch({
        type: AUTH_ACTIONS.LOGIN_FAILURE,
        payload: { error: error.message },
      });
      throw error;
    }
  };

  // Logout function
  const logout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      dispatch({ type: AUTH_ACTIONS.LOGOUT });
    }
  };

  // Update user profile
  const updateProfile = async (profileData) => {
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
  const requestPasswordReset = async (email) => {
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
  const hasRole = (role) => {
    return state.user?.roles?.includes(role) || false;
  };

  const hasPermission = (permission) => {
    return state.user?.permissions?.includes(permission) || false;
  };

  // Context value
  const value = {
    // State
    user: state.user,
    token: state.token,
    isAuthenticated: state.isAuthenticated,
    isLoading: state.isLoading,
    error: state.error,

    // Actions
    login,
    register,
    logout,
    updateProfile,
    changePassword,
    requestPasswordReset,
    resetPassword,
    clearError,

    // Utilities
    hasRole,
    hasPermission,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;
