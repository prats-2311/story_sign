/**
 * Jest Configuration for End-to-End Tests
 *
 * Specialized configuration for E2E testing with performance monitoring
 */

module.exports = {
  // Root directory
  rootDir: "../../..",

  // Test environment
  testEnvironment: "jsdom",

  // Test file patterns
  testMatch: ["<rootDir>/src/tests/e2e/**/*.test.js"],

  // Setup files
  setupFilesAfterEnv: [
    "<rootDir>/src/setupTests.js",
    "<rootDir>/src/tests/e2e/setup.js",
  ],

  // Module name mapping
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",
    "^@tests/(.*)$": "<rootDir>/src/tests/$1",
  },

  // Transform configuration
  transform: {
    "^.+\\.(js|jsx)$": "babel-jest",
  },

  // Module file extensions
  moduleFileExtensions: ["js", "jsx", "json"],

  // Coverage configuration
  collectCoverageFrom: [
    "src/**/*.{js,jsx}",
    "!src/tests/**",
    "!src/setupTests.js",
    "!src/index.js",
  ],

  coverageReporters: ["text", "lcov", "html", "json-summary"],

  coverageDirectory: "<rootDir>/coverage/e2e",

  // Test timeout for E2E tests (longer than unit tests)
  testTimeout: 30000,

  // Performance monitoring
  reporters: ["default"],

  // Global setup and teardown
  // globalSetup: "<rootDir>/src/tests/e2e/global-setup.js",
  // globalTeardown: "<rootDir>/src/tests/e2e/global-teardown.js",

  // Verbose output for debugging
  verbose: true,

  // Fail fast on first test failure (useful for CI)
  bail: false,

  // Clear mocks between tests
  clearMocks: true,

  // Restore mocks after each test
  restoreMocks: true,

  // Maximum number of concurrent workers
  maxWorkers: "50%",

  // Cache directory
  cacheDirectory: "<rootDir>/node_modules/.cache/jest-e2e",
};
