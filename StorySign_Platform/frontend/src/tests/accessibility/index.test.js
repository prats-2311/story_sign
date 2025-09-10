/**
 * Accessibility Test Suite Entry Point
 * Runs comprehensive accessibility tests across the platform
 */

import "./setup";

// Import all accessibility test suites
import "./axe.test";
import "./keyboard-navigation.test";
import "./screen-reader.test";
import "./color-contrast.test";
import "./user-workflows.test";

describe("StorySign Platform Accessibility Test Suite", () => {
  test("accessibility test suite is properly configured", () => {
    // Verify that jest-axe is properly configured
    expect(expect.extend).toBeDefined();

    // Verify that accessibility utilities are available
    expect(global.accessibilityTestUtils).toBeDefined();
    expect(global.accessibilityTestUtils.mockReducedMotion).toBeDefined();
    expect(global.accessibilityTestUtils.mockHighContrast).toBeDefined();

    // Verify that required mocks are in place
    expect(window.matchMedia).toBeDefined();
    expect(navigator.mediaDevices).toBeDefined();
    expect(HTMLElement.prototype.focus).toBeDefined();
  });

  test("should have proper test environment setup", () => {
    // Check that DOM is clean
    expect(document.body.innerHTML).toBe("");

    // Check that focus is reset
    expect(document.activeElement).toBe(document.body);

    // Check that title is reset
    expect(document.title).toBe("Test");
  });
});

// Export test utilities for use in other test files
export { default as accessibilityTestUtils } from "./setup";
