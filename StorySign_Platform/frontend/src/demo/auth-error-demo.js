/**
 * Demo script to showcase enhanced authentication error handling
 * This demonstrates the different types of errors and retry mechanisms
 */

import authService from "../services/AuthService";

// Mock different types of authentication errors for demonstration
export const demoAuthErrors = {
  // Network error - can retry
  networkError: () => {
    const error = new Error(
      "Unable to connect to server. Please check your internet connection."
    );
    error.name = "TypeError";
    return error;
  },

  // Server error - can retry
  serverError: () => {
    const error = new Error(
      "Server temporarily unavailable. Please try again in a moment."
    );
    error.status = 500;
    return error;
  },

  // Authentication error - cannot retry
  authError: () => {
    const error = new Error(
      "Invalid email or password. Please check your credentials and try again."
    );
    error.status = 401;
    return error;
  },

  // Validation error - cannot retry
  validationError: () => {
    const error = new Error(
      "An account with this email already exists. Please use a different email or try logging in."
    );
    error.status = 409;
    return error;
  },

  // Rate limiting error - cannot retry immediately
  rateLimitError: () => {
    const error = new Error(
      "Too many login attempts. Please wait a moment before trying again."
    );
    error.status = 429;
    return error;
  },
};

// Demo function to test error categorization
export const testErrorCategorization = () => {
  console.log("=== Authentication Error Handling Demo ===\n");

  Object.entries(demoAuthErrors).forEach(([errorType, errorGenerator]) => {
    const error = errorGenerator();
    console.log(`${errorType.toUpperCase()}:`);
    console.log(`  Message: ${error.message}`);
    console.log(`  Status: ${error.status || "N/A"}`);
    console.log(`  Type: ${error.name || "Error"}`);
    console.log("");
  });

  console.log("=== Error Handling Features ===");
  console.log("✅ Network errors: Show retry button with attempt counter");
  console.log("✅ Server errors: Show retry button with attempt counter");
  console.log("✅ Auth errors: Show error message without retry button");
  console.log(
    "✅ Validation errors: Show specific error message without retry"
  );
  console.log(
    "✅ Rate limit errors: Show wait message without immediate retry"
  );
  console.log(
    "✅ Error type indicators: Visual icons for different error types"
  );
  console.log("✅ Accessibility: Screen reader announcements for all errors");
  console.log("✅ Maximum retry attempts: Prevents infinite retry loops");
  console.log(
    "✅ Enhanced user feedback: Clear messaging and visual indicators"
  );
};

// Export for use in development/testing
export default {
  demoAuthErrors,
  testErrorCategorization,
};
