#!/usr/bin/env node
/**
 * Test script to verify API configuration
 */

// Set environment variables like in production
process.env.REACT_APP_API_URL = "https://story-sign.onrender.com";
process.env.REACT_APP_ENVIRONMENT = "production";
process.env.REACT_APP_USE_PROXY = "true";

// Import the API config
const API_BASE_URL = require("./src/config/api.js").default;

console.log("🔍 Testing API Configuration");
console.log("================================");
console.log("Environment Variables:");
console.log("- REACT_APP_API_URL:", process.env.REACT_APP_API_URL);
console.log("- REACT_APP_ENVIRONMENT:", process.env.REACT_APP_ENVIRONMENT);
console.log("- REACT_APP_USE_PROXY:", process.env.REACT_APP_USE_PROXY);
console.log("");
console.log("Resolved API_BASE_URL:", API_BASE_URL);
console.log("");

if (API_BASE_URL === "https://story-sign.onrender.com") {
  console.log("✅ API configuration is correct!");
  console.log(
    "Frontend will call: https://story-sign.onrender.com/api/v1/auth/login"
  );
} else {
  console.log("❌ API configuration is incorrect!");
  console.log("Expected: https://story-sign.onrender.com");
  console.log("Got:", API_BASE_URL);
}
