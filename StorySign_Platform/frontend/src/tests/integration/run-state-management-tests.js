#!/usr/bin/env node

/**
 * Test runner for state management tests
 * Runs unit tests and integration tests for the video/camera state management fixes
 */

const { execSync } = require("child_process");
const path = require("path");

const testCategories = {
  unit: {
    name: "Unit Tests",
    patterns: [
      "src/pages/ASLWorldPage.test.js",
      "src/pages/HarmonyPage.test.js",
      "src/pages/ReconnectPage.test.js",
      "src/hooks/useWebcam.test.js",
      "src/hooks/useWebSocket.test.js",
    ],
  },
  integration: {
    name: "Integration Tests",
    patterns: ["src/tests/integration/StateManagement.integration.test.js"],
  },
};

function runTests(category, patterns) {
  console.log(`\n🧪 Running ${category}...`);
  console.log("=".repeat(50));

  try {
    const testPattern = patterns.join("|");
    const command = `npm test -- --testPathPattern="${testPattern}" --verbose --coverage`;

    console.log(`Executing: ${command}\n`);
    execSync(command, {
      stdio: "inherit",
      cwd: process.cwd(),
    });

    console.log(`\n✅ ${category} completed successfully!`);
    return true;
  } catch (error) {
    console.error(`\n❌ ${category} failed!`);
    console.error(error.message);
    return false;
  }
}

function runAllTests() {
  console.log("🚀 Starting State Management Test Suite");
  console.log("Testing video/camera state management fixes");
  console.log("=".repeat(60));

  const results = {};

  // Run each test category
  for (const [key, config] of Object.entries(testCategories)) {
    results[key] = runTests(config.name, config.patterns);
  }

  // Summary
  console.log("\n📊 Test Results Summary");
  console.log("=".repeat(30));

  let allPassed = true;
  for (const [key, passed] of Object.entries(results)) {
    const status = passed ? "✅ PASSED" : "❌ FAILED";
    console.log(`${testCategories[key].name}: ${status}`);
    if (!passed) allPassed = false;
  }

  console.log("\n" + "=".repeat(60));

  if (allPassed) {
    console.log("🎉 All state management tests passed!");
    console.log("✨ Video/camera state management fixes are working correctly");
    process.exit(0);
  } else {
    console.log("💥 Some tests failed!");
    console.log("🔧 Please review the failing tests and fix the issues");
    process.exit(1);
  }
}

// Run specific test category if provided
const category = process.argv[2];
if (category && testCategories[category]) {
  const config = testCategories[category];
  const success = runTests(config.name, config.patterns);
  process.exit(success ? 0 : 1);
} else if (category) {
  console.error(`❌ Unknown test category: ${category}`);
  console.log("Available categories:", Object.keys(testCategories).join(", "));
  process.exit(1);
} else {
  // Run all tests
  runAllTests();
}
