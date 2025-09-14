/**
 * API Configuration for StorySign Platform
 * Environment-aware backend connection for deployment
 */

// Get API base URL from environment or use proxy for production
const getApiBaseUrl = () => {
  // Always use environment variable if available (for production)
  if (process.env.REACT_APP_API_URL) {
    console.log(
      "🔧 Using API URL from environment:",
      process.env.REACT_APP_API_URL
    );
    return process.env.REACT_APP_API_URL;
  }

  // Development fallback
  console.log("🔧 Using development API URL: http://127.0.0.1:8000");
  return "http://127.0.0.1:8000";
};

const API_BASE_URL = getApiBaseUrl();

// Debug logging for production
if (process.env.REACT_APP_ENVIRONMENT === "production") {
  console.log("🚀 Production API Configuration:");
  console.log("- API_BASE_URL:", API_BASE_URL);
  console.log("- Environment:", process.env.REACT_APP_ENVIRONMENT);
  console.log("- Use Proxy:", process.env.REACT_APP_USE_PROXY);
}

// Export the base URL
export default API_BASE_URL;

// Export additional configuration
export const WS_BASE_URL =
  process.env.REACT_APP_WS_URL ||
  (API_BASE_URL ? API_BASE_URL.replace("http", "ws") : "ws://127.0.0.1:8000");

export const API_VERSION = process.env.REACT_APP_API_VERSION || "v1";

export const USE_PROXY = process.env.REACT_APP_USE_PROXY === "true";
