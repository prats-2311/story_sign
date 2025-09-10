/**
 * Accessibility Testing Setup
 * Configures Jest and testing environment for accessibility tests
 */

import { configure } from "@testing-library/react";
import { toHaveNoViolations } from "jest-axe";

// Extend Jest matchers with jest-axe
expect.extend(toHaveNoViolations);

// Configure testing library for better accessibility testing
configure({
  // Increase timeout for accessibility tests
  asyncUtilTimeout: 5000,

  // Configure queries to be more inclusive
  defaultHidden: false,

  // Show suggestions for better queries
  showOriginalStackTrace: true,
});

// Mock IntersectionObserver for components that use it
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
};

// Mock ResizeObserver for responsive components
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
};

// Mock matchMedia for responsive and accessibility preference testing
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock getUserMedia for webcam components
Object.defineProperty(navigator, "mediaDevices", {
  writable: true,
  value: {
    getUserMedia: jest.fn().mockResolvedValue({
      getTracks: () => [{ stop: jest.fn() }],
    }),
  },
});

// Mock Web Speech API for voice features
Object.defineProperty(window, "speechSynthesis", {
  writable: true,
  value: {
    speak: jest.fn(),
    cancel: jest.fn(),
    pause: jest.fn(),
    resume: jest.fn(),
    getVoices: jest.fn().mockReturnValue([]),
  },
});

// Mock focus and blur methods for focus management testing
HTMLElement.prototype.focus = jest.fn();
HTMLElement.prototype.blur = jest.fn();
HTMLElement.prototype.scrollIntoView = jest.fn();

// Mock clipboard API for copy/paste functionality
Object.defineProperty(navigator, "clipboard", {
  writable: true,
  value: {
    writeText: jest.fn().mockResolvedValue(undefined),
    readText: jest.fn().mockResolvedValue(""),
  },
});

// Global test utilities for accessibility testing
global.accessibilityTestUtils = {
  // Helper to simulate reduced motion preference
  mockReducedMotion: (enabled = true) => {
    window.matchMedia.mockImplementation((query) => ({
      matches: query === "(prefers-reduced-motion: reduce)" ? enabled : false,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    }));
  },

  // Helper to simulate high contrast preference
  mockHighContrast: (enabled = true) => {
    window.matchMedia.mockImplementation((query) => ({
      matches: query === "(prefers-contrast: high)" ? enabled : false,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    }));
  },

  // Helper to simulate color scheme preference
  mockColorScheme: (scheme = "light") => {
    window.matchMedia.mockImplementation((query) => ({
      matches: query === `(prefers-color-scheme: ${scheme})`,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    }));
  },

  // Helper to test keyboard events
  createKeyboardEvent: (key, options = {}) => {
    return new KeyboardEvent("keydown", {
      key,
      code: key,
      bubbles: true,
      cancelable: true,
      ...options,
    });
  },

  // Helper to test focus events
  createFocusEvent: (type = "focus", options = {}) => {
    return new FocusEvent(type, {
      bubbles: true,
      cancelable: true,
      ...options,
    });
  },

  // Helper to wait for announcements
  waitForAnnouncement: async (container, timeout = 1000) => {
    return new Promise((resolve) => {
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (
            mutation.type === "childList" ||
            mutation.type === "characterData"
          ) {
            const liveRegions = container.querySelectorAll(
              '[aria-live], [role="status"], [role="alert"]'
            );
            liveRegions.forEach((region) => {
              if (region.textContent.trim()) {
                observer.disconnect();
                resolve(region.textContent);
              }
            });
          }
        });
      });

      observer.observe(container, {
        childList: true,
        subtree: true,
        characterData: true,
      });

      setTimeout(() => {
        observer.disconnect();
        resolve(null);
      }, timeout);
    });
  },
};

// Console warnings for accessibility issues during tests
const originalWarn = console.warn;
console.warn = (...args) => {
  const message = args.join(" ");

  // Highlight accessibility-related warnings
  if (
    message.includes("aria-") ||
    message.includes("role") ||
    message.includes("accessibility") ||
    message.includes("a11y")
  ) {
    originalWarn("\n🚨 ACCESSIBILITY WARNING:", ...args, "\n");
  } else {
    originalWarn(...args);
  }
};

// Setup for testing environment
beforeEach(() => {
  // Clear all mocks before each test
  jest.clearAllMocks();

  // Reset DOM
  document.body.innerHTML = "";
  document.head.innerHTML = "";

  // Reset document title
  document.title = "Test";

  // Reset focus
  if (document.activeElement && document.activeElement.blur) {
    document.activeElement.blur();
  }

  // Reset matchMedia to default state
  window.matchMedia.mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  }));
});

// Cleanup after each test
afterEach(() => {
  // Clean up any remaining timers safely
  try {
    if (jest.isMockFunction(setTimeout)) {
      jest.runOnlyPendingTimers();
      jest.useRealTimers();
    }
  } catch (error) {
    // Ignore timer cleanup errors
  }

  // Clean up any event listeners
  document.removeEventListener = jest.fn();
  window.removeEventListener = jest.fn();
});

// Global error handler for unhandled accessibility issues
window.addEventListener("error", (event) => {
  if (event.error && event.error.message.includes("accessibility")) {
    console.error("🚨 Accessibility Error:", event.error);
  }
});

// Export utilities for use in tests
export default global.accessibilityTestUtils;
