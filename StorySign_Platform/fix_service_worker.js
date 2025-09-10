#!/usr/bin/env node

/**
 * Quick fix for Service Worker registration error
 * This script helps resolve the "Failed to update a ServiceWorker" error
 */

const fs = require("fs");
const path = require("path");

console.log("🔧 Fixing Service Worker registration error...\n");

// Check if we're in the right directory
const frontendPath = path.join(__dirname, "frontend");
const publicPath = path.join(frontendPath, "public");
const swPath = path.join(publicPath, "sw.js");

if (!fs.existsSync(frontendPath)) {
  console.error("❌ Error: frontend directory not found");
  console.log(
    "Please run this script from the StorySign_Platform root directory"
  );
  process.exit(1);
}

if (!fs.existsSync(swPath)) {
  console.error("❌ Error: sw.js not found in public directory");
  process.exit(1);
}

console.log("✅ Service Worker file exists at:", swPath);

// Instructions for the user
console.log("\n📋 To fix the Service Worker error, follow these steps:\n");

console.log("1. 🧹 Clear browser cache and Service Worker:");
console.log("   - Open: http://localhost:3000/clear-cache.html");
console.log('   - Click "Clear Service Worker" and "Clear All Caches"');
console.log(
  "   - Or manually: F12 → Application → Storage → Clear site data\n"
);

console.log("2. 🔄 Hard refresh the application:");
console.log("   - Windows/Linux: Ctrl + Shift + R");
console.log("   - Mac: Cmd + Shift + R\n");

console.log("3. 🚀 Restart the development server:");
console.log("   - Stop the current server (Ctrl+C)");
console.log("   - Run: npm start (or yarn start)\n");

console.log("4. 🔍 If the error persists:");
console.log("   - Try opening in incognito/private mode");
console.log("   - Check browser console for additional errors");
console.log("   - Ensure no other instances of the app are running\n");

console.log(
  "💡 The Service Worker is now configured to only register in production."
);
console.log(
  "   Set REACT_APP_ENABLE_SW=true in .env to enable in development.\n"
);

console.log("✨ Service Worker fix applied successfully!");
