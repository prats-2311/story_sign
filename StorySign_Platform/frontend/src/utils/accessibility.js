/**
 * Accessibility utility functions
 * Provides helper functions for WCAG compliance and accessibility features
 */

/**
 * Check if an element is focusable
 */
export const isFocusable = (element) => {
  if (!element || element.disabled) return false;

  const focusableSelectors = [
    "a[href]",
    "button:not([disabled])",
    "input:not([disabled])",
    "select:not([disabled])",
    "textarea:not([disabled])",
    '[tabindex]:not([tabindex="-1"])',
    '[contenteditable="true"]',
  ];

  return focusableSelectors.some((selector) => element.matches(selector));
};

/**
 * Get all focusable elements within a container
 */
export const getFocusableElements = (container) => {
  if (!container) return [];

  const focusableSelector = [
    "button:not([disabled])",
    "[href]",
    "input:not([disabled])",
    "select:not([disabled])",
    "textarea:not([disabled])",
    '[tabindex]:not([tabindex="-1"])',
    '[contenteditable="true"]',
  ].join(", ");

  return Array.from(container.querySelectorAll(focusableSelector));
};

/**
 * Trap focus within a container
 */
export const trapFocus = (container, event) => {
  const focusableElements = getFocusableElements(container);
  if (focusableElements.length === 0) return;

  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  if (event.key === "Tab") {
    if (event.shiftKey) {
      // Shift + Tab
      if (document.activeElement === firstElement) {
        event.preventDefault();
        lastElement.focus();
      }
    } else {
      // Tab
      if (document.activeElement === lastElement) {
        event.preventDefault();
        firstElement.focus();
      }
    }
  }
};

/**
 * Check color contrast ratio
 */
export const getContrastRatio = (foreground, background) => {
  const hexToRgb = (hex) => {
    // Remove # if present
    hex = hex.replace("#", "");

    // Handle 3-digit hex
    if (hex.length === 3) {
      hex = hex
        .split("")
        .map((char) => char + char)
        .join("");
    }

    if (hex.length !== 6) return null;

    const r = parseInt(hex.substr(0, 2), 16);
    const g = parseInt(hex.substr(2, 2), 16);
    const b = parseInt(hex.substr(4, 2), 16);

    return [r, g, b];
  };

  const parseColor = (color) => {
    if (typeof color !== "string") return null;

    // Handle hex colors
    if (color.startsWith("#")) {
      return hexToRgb(color);
    }

    // Handle rgb() colors
    const rgbMatch = color.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
    if (rgbMatch) {
      return [
        parseInt(rgbMatch[1]),
        parseInt(rgbMatch[2]),
        parseInt(rgbMatch[3]),
      ];
    }

    // Handle rgba() colors - check for transparency
    const rgbaMatch = color.match(
      /rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)/
    );
    if (rgbaMatch) {
      const alpha = parseFloat(rgbaMatch[4]);
      if (alpha === 0) return null; // Fully transparent
      return [
        parseInt(rgbaMatch[1]),
        parseInt(rgbaMatch[2]),
        parseInt(rgbaMatch[3]),
      ];
    }

    // Handle transparent keyword
    if (color === "transparent") {
      return null;
    }

    return null;
  };

  const getLuminance = (color) => {
    const rgb = parseColor(color);
    if (!rgb) return 0;

    const [r, g, b] = rgb.map((c) => {
      c = c / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });

    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };

  // Handle invalid colors first
  if (parseColor(foreground) === null || parseColor(background) === null) {
    return 1;
  }

  const l1 = getLuminance(foreground);
  const l2 = getLuminance(background);

  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);

  return (lighter + 0.05) / (darker + 0.05);
};

/**
 * Check if color contrast meets WCAG standards
 */
export const meetsContrastRequirement = (
  foreground,
  background,
  level = "AA",
  size = "normal"
) => {
  const ratio = getContrastRatio(foreground, background);

  if (level === "AAA") {
    return size === "large" ? ratio >= 4.5 : ratio >= 7;
  }

  // AA level (default)
  return size === "large" ? ratio >= 3 : ratio >= 4.5;
};

/**
 * Generate unique ID for accessibility attributes
 */
export const generateId = (prefix = "a11y") => {
  return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * Announce message to screen readers
 */
export const announceToScreenReader = (message, priority = "polite") => {
  const announcement = document.createElement("div");
  announcement.setAttribute("aria-live", priority);
  announcement.setAttribute("aria-atomic", "true");
  announcement.className = "sr-only";
  announcement.textContent = message;

  document.body.appendChild(announcement);

  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
};

/**
 * Check if user prefers reduced motion
 */
export const prefersReducedMotion = () => {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
};

/**
 * Check if user prefers high contrast
 */
export const prefersHighContrast = () => {
  return window.matchMedia("(prefers-contrast: high)").matches;
};

/**
 * Get appropriate ARIA role for element type
 */
export const getAriaRole = (elementType, context = {}) => {
  const roleMap = {
    button: "button",
    link: "link",
    heading: "heading",
    list: "list",
    listitem: "listitem",
    navigation: "navigation",
    main: "main",
    banner: "banner",
    contentinfo: "contentinfo",
    complementary: "complementary",
    search: "search",
    form: "form",
    dialog: "dialog",
    alertdialog: "alertdialog",
    alert: "alert",
    status: "status",
    progressbar: "progressbar",
    tab: "tab",
    tabpanel: "tabpanel",
    tablist: "tablist",
  };

  return roleMap[elementType] || null;
};

/**
 * Validate ARIA attributes
 */
export const validateAriaAttributes = (element) => {
  const warnings = [];

  // Check for required ARIA attributes
  const role = element.getAttribute("role");
  if (
    role === "button" &&
    !element.hasAttribute("aria-label") &&
    !element.textContent.trim()
  ) {
    warnings.push("Button elements should have accessible text or aria-label");
  }

  if (
    role === "dialog" &&
    !element.hasAttribute("aria-labelledby") &&
    !element.hasAttribute("aria-label")
  ) {
    warnings.push("Dialog elements should have aria-labelledby or aria-label");
  }

  // Check for invalid ARIA attribute combinations
  if (
    element.hasAttribute("aria-hidden") &&
    element.hasAttribute("tabindex") &&
    element.getAttribute("tabindex") !== "-1"
  ) {
    warnings.push('Elements with aria-hidden="true" should not be focusable');
  }

  return warnings;
};

/**
 * Create skip link for keyboard navigation
 */
export const createSkipLink = (targetId, text = "Skip to main content") => {
  const skipLink = document.createElement("a");
  skipLink.href = `#${targetId}`;
  skipLink.textContent = text;
  skipLink.className = "skip-link";
  skipLink.addEventListener("click", (e) => {
    e.preventDefault();
    const target = document.getElementById(targetId);
    if (target) {
      target.focus();
      target.scrollIntoView({ behavior: "smooth" });
    }
  });

  return skipLink;
};

/**
 * Manage focus for single page applications
 */
export const manageFocusForSPA = (newPageTitle) => {
  // Update page title
  document.title = newPageTitle;

  // Announce page change to screen readers
  announceToScreenReader(`Navigated to ${newPageTitle}`, "assertive");

  // Focus the main content area or first heading
  const mainContent = document.querySelector('main, [role="main"], h1');
  if (mainContent) {
    mainContent.setAttribute("tabindex", "-1");
    mainContent.focus();

    // Remove tabindex after focus to restore natural tab order
    setTimeout(() => {
      mainContent.removeAttribute("tabindex");
    }, 100);
  }
};

/**
 * Check if element is visible to screen readers
 */
export const isVisibleToScreenReader = (element) => {
  if (!element) return false;

  const style = window.getComputedStyle(element);

  // Check for common hiding techniques
  if (
    style.display === "none" ||
    style.visibility === "hidden" ||
    (element.hasAttribute("aria-hidden") &&
      element.getAttribute("aria-hidden") === "true") ||
    style.opacity === "0" ||
    element.hasAttribute("hidden")
  ) {
    return false;
  }

  return true;
};

/**
 * Format text for screen readers
 */
export const formatForScreenReader = (text, options = {}) => {
  const {
    expandAbbreviations = true,
    addPunctuation = true,
    removeExtraSpaces = true,
  } = options;

  let formatted = text;

  if (removeExtraSpaces) {
    formatted = formatted.replace(/\s+/g, " ").trim();
  }

  if (expandAbbreviations) {
    const abbreviations = {
      ASL: "American Sign Language",
      AI: "Artificial Intelligence",
      UI: "User Interface",
      UX: "User Experience",
    };

    Object.entries(abbreviations).forEach(([abbr, expansion]) => {
      const regex = new RegExp(`\\b${abbr}\\b`, "g");
      formatted = formatted.replace(regex, expansion);
    });
  }

  if (addPunctuation && !formatted.match(/[.!?]$/)) {
    formatted += ".";
  }

  return formatted;
};

export default {
  isFocusable,
  getFocusableElements,
  trapFocus,
  getContrastRatio,
  meetsContrastRequirement,
  generateId,
  announceToScreenReader,
  prefersReducedMotion,
  prefersHighContrast,
  getAriaRole,
  validateAriaAttributes,
  createSkipLink,
  manageFocusForSPA,
  isVisibleToScreenReader,
  formatForScreenReader,
};
