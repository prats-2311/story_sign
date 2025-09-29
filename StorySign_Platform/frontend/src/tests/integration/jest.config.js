module.exports = {
  displayName: "Integration Tests",
  testMatch: ["<rootDir>/src/tests/integration/**/*.test.js"],
  setupFilesAfterEnv: ["<rootDir>/src/setupTests.js"],
  testEnvironment: "jsdom",
  moduleNameMapping: {
    "^@/(.*)$": "<rootDir>/src/$1",
  },
  collectCoverageFrom: [
    "src/pages/**/*.{js,jsx}",
    "src/hooks/**/*.{js,jsx}",
    "src/components/**/*.{js,jsx}",
    "!src/**/*.test.{js,jsx}",
    "!src/tests/**",
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
  testTimeout: 10000,
};
