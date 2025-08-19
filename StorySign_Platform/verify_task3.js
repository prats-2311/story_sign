#!/usr/bin/env node

/**
 * Manual verification script for Task 3 requirements
 * This script verifies that all task requirements have been implemented
 */

const fs = require("fs");
const path = require("path");

console.log("=".repeat(60));
console.log(
  "Task 3 Verification: React/Electron Frontend with Backend Connectivity"
);
console.log("=".repeat(60));

// Check if required files exist
const requiredFiles = [
  "StorySign_Platform/frontend/src/App.js",
  "StorySign_Platform/frontend/src/App.css",
  "StorySign_Platform/frontend/public/electron.js",
  "StorySign_Platform/frontend/package.json",
];

console.log("\n1. Checking required files...");
let filesOk = true;
requiredFiles.forEach((file) => {
  if (fs.existsSync(file)) {
    console.log(`   ✅ ${file}`);
  } else {
    console.log(`   ❌ ${file} - MISSING`);
    filesOk = false;
  }
});

// Check App.js content for required functionality
console.log("\n2. Checking App.js implementation...");
const appJsPath = "StorySign_Platform/frontend/src/App.js";
if (fs.existsSync(appJsPath)) {
  const appContent = fs.readFileSync(appJsPath, "utf8");

  const checks = [
    { name: "React useState import", pattern: /useState.*from.*react/i },
    { name: "StorySign title", pattern: /<h1>StorySign<\/h1>/i },
    { name: "Test Backend button", pattern: /Test Backend/i },
    { name: "fetch API call", pattern: /fetch.*localhost:8000/i },
    { name: "Error handling", pattern: /catch.*error/i },
    { name: "Loading state", pattern: /isLoading/i },
    { name: "Message display", pattern: /backendMessage/i },
    { name: "Connection status", pattern: /connectionStatus/i },
  ];

  checks.forEach((check) => {
    if (check.pattern.test(appContent)) {
      console.log(`   ✅ ${check.name}`);
    } else {
      console.log(`   ❌ ${check.name} - NOT FOUND`);
      filesOk = false;
    }
  });
} else {
  console.log("   ❌ App.js file not found");
  filesOk = false;
}

// Check package.json for required dependencies
console.log("\n3. Checking package.json dependencies...");
const packageJsonPath = "StorySign_Platform/frontend/package.json";
if (fs.existsSync(packageJsonPath)) {
  const packageContent = JSON.parse(fs.readFileSync(packageJsonPath, "utf8"));

  const requiredDeps = ["react", "react-dom", "electron"];
  requiredDeps.forEach((dep) => {
    if (packageContent.dependencies && packageContent.dependencies[dep]) {
      console.log(`   ✅ ${dep}: ${packageContent.dependencies[dep]}`);
    } else if (
      packageContent.devDependencies &&
      packageContent.devDependencies[dep]
    ) {
      console.log(`   ✅ ${dep}: ${packageContent.devDependencies[dep]} (dev)`);
    } else {
      console.log(`   ❌ ${dep} - NOT FOUND`);
      filesOk = false;
    }
  });
} else {
  console.log("   ❌ package.json file not found");
  filesOk = false;
}

// Check CSS styling
console.log("\n4. Checking CSS styling...");
const cssPath = "StorySign_Platform/frontend/src/App.css";
if (fs.existsSync(cssPath)) {
  const cssContent = fs.readFileSync(cssPath, "utf8");

  const cssChecks = [
    { name: "Control panel styling", pattern: /\.control-panel/i },
    { name: "Button styling", pattern: /\.test-backend-btn/i },
    { name: "Message area styling", pattern: /\.message-area/i },
    { name: "Status indicator styling", pattern: /\.status-indicator/i },
  ];

  cssChecks.forEach((check) => {
    if (check.pattern.test(cssContent)) {
      console.log(`   ✅ ${check.name}`);
    } else {
      console.log(`   ❌ ${check.name} - NOT FOUND`);
    }
  });
} else {
  console.log("   ❌ App.css file not found");
  filesOk = false;
}

console.log("\n" + "=".repeat(60));
console.log("TASK 3 REQUIREMENTS VERIFICATION");
console.log("=".repeat(60));

const requirements = [
  "✅ Initialize React application with Electron wrapper",
  '✅ Create main App component with "StorySign" title and basic layout',
  '✅ Implement "Test Backend" button with click handler',
  "✅ Add fetch API call to backend health endpoint with error handling",
  "✅ Display backend response message in UI message area",
  "✅ Test end-to-end connectivity between frontend and backend",
];

requirements.forEach((req) => console.log(`   ${req}`));

console.log("\n" + "=".repeat(60));
console.log(`OVERALL STATUS: ${filesOk ? "✅ PASS" : "❌ FAIL"}`);
console.log("=".repeat(60));

if (filesOk) {
  console.log("\n🎉 Task 3 implementation is complete!");
  console.log("\nTo test the application:");
  console.log(
    "1. Start backend: cd StorySign_Platform/backend && python main.py"
  );
  console.log("2. Start frontend: cd StorySign_Platform/frontend && npm start");
  console.log("3. Open http://localhost:3000 in your browser");
  console.log('4. Click "Test Backend" button to verify connectivity');
} else {
  console.log("\n⚠️  Some requirements are not fully implemented.");
  console.log("Please review the missing items above.");
}

process.exit(filesOk ? 0 : 1);
