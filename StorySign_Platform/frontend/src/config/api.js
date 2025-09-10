/**
 * API Configuration for StorySign Platform
 * Handles environment-specific API URLs for cloud deployment compatibility
 */

// Default configuration for development
const DEFAULT_CONFIG = {
  API_BASE_URL: "http://localhost:8000",
  WS_BASE_URL: "ws://localhost:8000",
  API_VERSION: "v1",
};

/**
 * Get the current API configuration based on environment
 */
export const getApiConfig = () => {
  const config = {
    API_BASE_URL: process.env.REACT_APP_API_URL || DEFAULT_CONFIG.API_BASE_URL,
    WS_BASE_URL: process.env.REACT_APP_WS_URL || DEFAULT_CONFIG.WS_BASE_URL,
    API_VERSION:
      process.env.REACT_APP_API_VERSION || DEFAULT_CONFIG.API_VERSION,
  };

  // Ensure URLs don't have trailing slashes
  config.API_BASE_URL = config.API_BASE_URL.replace(/\/$/, "");
  config.WS_BASE_URL = config.WS_BASE_URL.replace(/\/$/, "");

  return config;
};

/**
 * Build API endpoint URL
 * @param {string} path - API endpoint path (e.g., '/auth/login')
 * @param {string} version - API version (optional, defaults to configured version)
 * @returns {string} Complete API URL
 */
export const buildApiUrl = (path, version = null) => {
  const config = getApiConfig();
  const apiVersion = version || config.API_VERSION;

  // Remove leading slash from path if present
  const cleanPath = path.replace(/^\//, "");

  // For Netlify deployment, use relative paths that will be proxied
  if (
    process.env.NODE_ENV === "production" &&
    process.env.REACT_APP_USE_PROXY === "true"
  ) {
    return `/api/${apiVersion}/${cleanPath}`;
  }

  return `${config.API_BASE_URL}/api/${apiVersion}/${cleanPath}`;
};

/**
 * Build WebSocket URL
 * @param {string} path - WebSocket endpoint path (e.g., '/ws/video')
 * @returns {string} Complete WebSocket URL
 */
export const buildWsUrl = (path) => {
  const config = getApiConfig();

  // Remove leading slash from path if present
  const cleanPath = path.replace(/^\//, "");

  // For production with proxy, use relative WebSocket URL
  if (
    process.env.NODE_ENV === "production" &&
    process.env.REACT_APP_USE_PROXY === "true"
  ) {
    // Convert HTTP(S) to WS(S) for proxy
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}/${cleanPath}`;
  }

  return `${config.WS_BASE_URL}/${cleanPath}`;
};

/**
 * Build health check URL (for backend connectivity testing)
 * @returns {string} Health check URL
 */
export const buildHealthCheckUrl = () => {
  const config = getApiConfig();

  // For production with proxy, use relative path
  if (
    process.env.NODE_ENV === "production" &&
    process.env.REACT_APP_USE_PROXY === "true"
  ) {
    return "/health";
  }

  return `${config.API_BASE_URL}/health`;
};

/**
 * Get environment information for debugging
 * @returns {object} Environment configuration details
 */
export const getEnvironmentInfo = () => {
  const config = getApiConfig();

  return {
    NODE_ENV: process.env.NODE_ENV,
    API_BASE_URL: config.API_BASE_URL,
    WS_BASE_URL: config.WS_BASE_URL,
    API_VERSION: config.API_VERSION,
    USE_PROXY: process.env.REACT_APP_USE_PROXY,
    REACT_APP_API_URL: process.env.REACT_APP_API_URL,
    REACT_APP_WS_URL: process.env.REACT_APP_WS_URL,
  };
};

// Export default configuration
export default getApiConfig();
