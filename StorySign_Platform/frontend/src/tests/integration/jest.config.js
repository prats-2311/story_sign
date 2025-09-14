const path = require("path");

module.exports = {
  displayName: "Integration Tests",
  rootDir: path.resolve(__dirname, "../../../"),
  testMatch: ["<rootDir>/src/tests/integration/**/*.test.js"],
  setupFilesAfterEnv: [
    "<rootDir>/src/setupTests.js",
    "<rootDir>/src/tests/integration/setup.js",
  ],
  testEnvironment: "jsdom",
  collectCoverageFrom: [
    "src/**/*.{js,jsx}",
    "!src/tests/**",
    "!src/index.js",
    "!src/reportWebVitals.js",
  ],
  coverageDirectory: "coverage/integration",
  coverageReporters: ["text", "lcov", "html"],
  testTimeout: 30000,
  verbose: true,
  bail: false,
  maxWorkers: 1, // Run tests serially for integration tests
  transform: {
    "^.+\\.(js|jsx)$": "babel-jest",
  },
  transformIgnorePatterns: [
    "node_modules/(?!(react-router|react-router-dom|react-error-boundary)/)",
  ],
  moduleNameMapper: {
    "\\.(css|less|scss|sass)$": "identity-obj-proxy",
    "\\.(jpg|jpeg|png|gif|eot|otf|webp|svg|ttf|woff|woff2|mp4|webm|wav|mp3|m4a|aac|oga)$":
      "jest-transform-stub",
  },
};
