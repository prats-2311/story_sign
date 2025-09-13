/**
 * Authentication Service
 * Handles all authentication-related API calls and token management
 */

import API_BASE_URL from "../config/api";

class AuthService {
  constructor() {
    this.tokenKey = "auth_token";
    this.userKey = "auth_user";
    this.refreshTokenKey = "refresh_token";
  }

  /**
   * Get the current authentication token
   * @returns {string|null} The JWT token or null if not authenticated
   */
  getToken() {
    return (
      localStorage.getItem(this.tokenKey) ||
      sessionStorage.getItem(this.tokenKey)
    );
  }

  /**
   * Get the current user data
   * @returns {Object|null} The user object or null if not authenticated
   */
  getCurrentUser() {
    const userStr =
      localStorage.getItem(this.userKey) ||
      sessionStorage.getItem(this.userKey);
    try {
      return userStr ? JSON.parse(userStr) : null;
    } catch (error) {
      console.error("Error parsing user data:", error);
      this.clearAuthData();
      return null;
    }
  }

  /**
   * Check if user is currently authenticated
   * @returns {boolean} True if authenticated, false otherwise
   */
  isAuthenticated() {
    const token = this.getToken();
    if (!token) return false;

    try {
      // Check if token is expired
      const payload = JSON.parse(atob(token.split(".")[1]));
      const currentTime = Date.now() / 1000;

      if (payload.exp < currentTime) {
        this.clearAuthData();
        return false;
      }

      return true;
    } catch (error) {
      console.error("Error validating token:", error);
      this.clearAuthData();
      return false;
    }
  }

  /**
   * Store authentication data
   * @param {string} token - JWT token
   * @param {Object} user - User object
   * @param {string} refreshToken - Refresh token (optional)
   * @param {boolean} rememberMe - Whether to persist in localStorage
   */
  storeAuthData(token, user, refreshToken = null, rememberMe = false) {
    const storage = rememberMe ? localStorage : sessionStorage;

    storage.setItem(this.tokenKey, token);
    storage.setItem(this.userKey, JSON.stringify(user));

    if (refreshToken) {
      storage.setItem(this.refreshTokenKey, refreshToken);
    }

    // Clear from the other storage to avoid conflicts
    const otherStorage = rememberMe ? sessionStorage : localStorage;
    otherStorage.removeItem(this.tokenKey);
    otherStorage.removeItem(this.userKey);
    otherStorage.removeItem(this.refreshTokenKey);
  }

  /**
   * Clear all authentication data
   */
  clearAuthData() {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.userKey);
    localStorage.removeItem(this.refreshTokenKey);
    sessionStorage.removeItem(this.tokenKey);
    sessionStorage.removeItem(this.userKey);
    sessionStorage.removeItem(this.refreshTokenKey);
  }

  /**
   * Make an authenticated API request
   * @param {string} endpoint - API endpoint (e.g., '/auth/me')
   * @param {Object} options - Fetch options
   * @returns {Promise<Response>} Fetch response
   */
  async makeAuthenticatedRequest(endpoint, options = {}) {
    const token = this.getToken();
    const url = `${API_BASE_URL}/api/v1${endpoint}`;

    const defaultOptions = {
      headers: {
        "Content-Type": "application/json",
        ...(token && { Authorization: `Bearer ${token}` }),
      },
    };

    const mergedOptions = {
      ...defaultOptions,
      ...options,
      headers: {
        ...defaultOptions.headers,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, mergedOptions);

      // Handle token expiration
      if (response.status === 401) {
        const refreshed = await this.refreshToken();
        if (refreshed) {
          // Retry the request with new token
          mergedOptions.headers.Authorization = `Bearer ${this.getToken()}`;
          return await fetch(url, mergedOptions);
        } else {
          // Refresh failed, clear auth data and throw error
          this.clearAuthData();
          throw new Error("Session expired. Please log in again.");
        }
      }

      return response;
    } catch (error) {
      if (error.name === "TypeError" && error.message.includes("fetch")) {
        throw new Error(
          "Unable to connect to server. Please check your internet connection."
        );
      }
      throw error;
    }
  }

  /**
   * Login user with email and password
   * @param {string} email - User email
   * @param {string} password - User password
   * @param {boolean} rememberMe - Whether to persist login
   * @returns {Promise<Object>} User data and token
   */
  async login(email, password, rememberMe = false) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          identifier: email.toLowerCase().trim(),
          password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        // Create more specific error messages based on status code
        let errorMessage = data.message || data.detail || "Login failed";

        if (response.status === 401) {
          errorMessage =
            "Invalid email or password. Please check your credentials and try again.";
        } else if (response.status === 429) {
          errorMessage =
            "Too many login attempts. Please wait a moment before trying again.";
        } else if (response.status >= 500) {
          errorMessage =
            "Server temporarily unavailable. Please try again in a moment.";
        } else if (response.status === 400) {
          errorMessage =
            data.message || "Invalid login request. Please check your input.";
        }

        const error = new Error(errorMessage);
        error.status = response.status;
        error.originalMessage = data.message || data.detail;
        throw error;
      }

      // Store authentication data
      this.storeAuthData(
        data.access_token,
        data.user,
        data.refresh_token,
        rememberMe
      );

      return {
        user: data.user,
        token: data.access_token,
      };
    } catch (error) {
      if (error.name === "TypeError" && error.message.includes("fetch")) {
        throw new Error(
          "Unable to connect to server. Please check your internet connection."
        );
      }
      throw error;
    }
  }

  /**
   * Register new user
   * @param {Object} userData - User registration data
   * @returns {Promise<Object>} Registration response
   */
  async register(userData) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: userData.username.trim(),
          email: userData.email.toLowerCase().trim(),
          password: userData.password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        // Create more specific error messages based on status code
        let errorMessage = data.message || data.detail || "Registration failed";

        if (response.status === 409) {
          errorMessage =
            "An account with this email already exists. Please use a different email or try logging in.";
        } else if (response.status === 400) {
          errorMessage =
            data.message ||
            "Invalid registration data. Please check your input.";
        } else if (response.status === 429) {
          errorMessage =
            "Too many registration attempts. Please wait a moment before trying again.";
        } else if (response.status >= 500) {
          errorMessage =
            "Server temporarily unavailable. Please try again in a moment.";
        }

        const error = new Error(errorMessage);
        error.status = response.status;
        error.originalMessage = data.message || data.detail;
        throw error;
      }

      return data;
    } catch (error) {
      if (error.name === "TypeError" && error.message.includes("fetch")) {
        throw new Error(
          "Unable to connect to server. Please check your internet connection."
        );
      }
      throw error;
    }
  }

  /**
   * Logout user
   * @returns {Promise<void>}
   */
  async logout() {
    try {
      // Attempt to notify server of logout
      const token = this.getToken();
      if (token) {
        await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });
      }
    } catch (error) {
      // Don't throw error for logout API call failure
      console.warn("Logout API call failed:", error.message);
    } finally {
      // Always clear local auth data
      this.clearAuthData();
    }
  }

  /**
   * Refresh authentication token
   * @returns {Promise<boolean>} True if refresh successful, false otherwise
   */
  async refreshToken() {
    const refreshToken =
      localStorage.getItem(this.refreshTokenKey) ||
      sessionStorage.getItem(this.refreshTokenKey);

    if (!refreshToken) {
      return false;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          refresh_token: refreshToken,
        }),
      });

      if (!response.ok) {
        return false;
      }

      const data = await response.json();

      // Update stored token
      const storage = localStorage.getItem(this.tokenKey)
        ? localStorage
        : sessionStorage;
      storage.setItem(this.tokenKey, data.access_token);

      if (data.user) {
        storage.setItem(this.userKey, JSON.stringify(data.user));
      }

      return true;
    } catch (error) {
      console.error("Token refresh failed:", error);
      return false;
    }
  }

  /**
   * Verify current token with server
   * @returns {Promise<Object|null>} User data if valid, null otherwise
   */
  async verifyToken() {
    if (!this.isAuthenticated()) {
      return null;
    }

    try {
      const response = await this.makeAuthenticatedRequest("/auth/me");

      if (!response.ok) {
        return null;
      }

      const userData = await response.json();

      // Update stored user data
      const storage = localStorage.getItem(this.userKey)
        ? localStorage
        : sessionStorage;
      storage.setItem(this.userKey, JSON.stringify(userData));

      return userData;
    } catch (error) {
      console.error("Token verification failed:", error);
      return null;
    }
  }

  /**
   * Request password reset
   * @param {string} email - User email
   * @returns {Promise<Object>} Reset response
   */
  async requestPasswordReset(email) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/auth/forgot-password`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email: email.toLowerCase().trim(),
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.message || data.detail || "Password reset request failed"
        );
      }

      return data;
    } catch (error) {
      if (error.name === "TypeError" && error.message.includes("fetch")) {
        throw new Error(
          "Unable to connect to server. Please check your internet connection."
        );
      }
      throw error;
    }
  }

  /**
   * Reset password with token
   * @param {string} token - Reset token
   * @param {string} newPassword - New password
   * @returns {Promise<Object>} Reset response
   */
  async resetPassword(token, newPassword) {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/auth/reset-password`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            token,
            new_password: newPassword,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || data.detail || "Password reset failed");
      }

      return data;
    } catch (error) {
      if (error.name === "TypeError" && error.message.includes("fetch")) {
        throw new Error(
          "Unable to connect to server. Please check your internet connection."
        );
      }
      throw error;
    }
  }

  /**
   * Update user profile
   * @param {Object} profileData - Profile update data
   * @returns {Promise<Object>} Updated user data
   */
  async updateProfile(profileData) {
    try {
      const response = await this.makeAuthenticatedRequest("/auth/profile", {
        method: "PUT",
        body: JSON.stringify(profileData),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || data.detail || "Profile update failed");
      }

      // Update stored user data
      const storage = localStorage.getItem(this.userKey)
        ? localStorage
        : sessionStorage;
      storage.setItem(this.userKey, JSON.stringify(data));

      return data;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Change user password
   * @param {string} currentPassword - Current password
   * @param {string} newPassword - New password
   * @returns {Promise<Object>} Change response
   */
  async changePassword(currentPassword, newPassword) {
    try {
      const response = await this.makeAuthenticatedRequest(
        "/auth/change-password",
        {
          method: "POST",
          body: JSON.stringify({
            current_password: currentPassword,
            new_password: newPassword,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.message || data.detail || "Password change failed"
        );
      }

      return data;
    } catch (error) {
      throw error;
    }
  }
}

// Create and export singleton instance
const authService = new AuthService();
export default authService;
