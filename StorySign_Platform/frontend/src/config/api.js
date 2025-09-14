/**
 * API Configuration for StorySign Platform
 * Environment-aware backend connection for deployment
 */

// Get API base URL from environment or use proxy for production
const getApiBaseUrl = () => {
  // In production (Netlify), use proxy path to avoid CORS
  if (process.env.REACT_APP_ENVIRONMENT === "production") {
    return ""; // Use relative paths that will be proxied by Netlify
  }

  // Use environment variable if available
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }

  // Development fallback
  return "http://127.0.0.1:8000";
};

const API_BASE_URL = getApiBaseUrl();

// Export the base URL
export default API_BASE_URL;

// Export additional configuration
export const WS_BASE_URL =
  process.env.REACT_APP_WS_URL ||
  (API_BASE_URL ? API_BASE_URL.replace("http", "ws") : "ws://127.0.0.1:8000");

export const API_VERSION = process.env.REACT_APP_API_VERSION || "v1";

export const USE_PROXY = process.env.REACT_APP_USE_PROXY === "true";
