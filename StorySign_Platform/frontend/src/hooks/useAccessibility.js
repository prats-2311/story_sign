import { useEffect, useRef, useCallback, useState } from "react";

/**
 * Custom hook for accessibility features and utilities
 * Provides keyboard navigation, screen reader announcements, and focus management
 */
export const useAccessibility = () => {
  const announcementRef = useRef(null);
  const [announcements, setAnnouncements] = useState([]);
  const announcementId = useRef(0);

  // Create announcement element if it doesn't exist
  useEffect(() => {
    if (!announcementRef.current) {
      const element = document.createElement("div");
      element.setAttribute("aria-live", "polite");
      element.setAttribute("aria-atomic", "true");
      element.className = "sr-only";
      element.id = "accessibility-announcements";
      document.body.appendChild(element);
      announcementRef.current = element;
    }

    return () => {
      if (
        announcementRef.current &&
        document.body.contains(announcementRef.current)
      ) {
        document.body.removeChild(announcementRef.current);
      }
    };
  }, []);

  // Announce message to screen readers
  const announce = useCallback((message, priority = "polite") => {
    if (!message || typeof message !== "string") return;

    const id = ++announcementId.current;
    const announcement = { id, message, priority };

    setAnnouncements((prev) => [...prev, announcement]);

    // Update the live region
    if (announcementRef.current) {
      announcementRef.current.setAttribute("aria-live", priority);
      announcementRef.current.textContent = message;
    }

    // Clear announcement after it's been read
    setTimeout(
      () => {
        setAnnouncements((prev) => prev.filter((ann) => ann.id !== id));
        if (
          announcementRef.current &&
          announcementRef.current.textContent === message
        ) {
          announcementRef.current.textContent = "";
        }
      },
      priority === "assertive" ? 2000 : 1000
    );
  }, []);

  return {
    announce,
    announcements,
  };
};

/**
 * Hook for managing keyboard navigation
 */
export const useKeyboardNavigation = (containerRef, options = {}) => {
  const {
    focusableSelector = 'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
    trapFocus = false,
    autoFocus = false,
    onEscape,
  } = options;

  const getFocusableElements = useCallback(() => {
    if (!containerRef.current) return [];
    return Array.from(containerRef.current.querySelectorAll(focusableSelector));
  }, [containerRef, focusableSelector]);

  const focusFirst = useCallback(() => {
    const elements = getFocusableElements();
    if (elements.length > 0) {
      elements[0].focus();
    }
  }, [getFocusableElements]);

  const focusLast = useCallback(() => {
    const elements = getFocusableElements();
    if (elements.length > 0) {
      elements[elements.length - 1].focus();
    }
  }, [getFocusableElements]);

  const handleKeyDown = useCallback(
    (event) => {
      if (event.key === "Escape" && onEscape) {
        event.preventDefault();
        onEscape();
        return;
      }

      if (!trapFocus || event.key !== "Tab") return;

      const elements = getFocusableElements();
      if (elements.length === 0) return;

      const firstElement = elements[0];
      const lastElement = elements[elements.length - 1];

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
    },
    [trapFocus, onEscape, getFocusableElements]
  );

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    if (autoFocus) {
      focusFirst();
    }

    container.addEventListener("keydown", handleKeyDown);

    return () => {
      container.removeEventListener("keydown", handleKeyDown);
    };
  }, [containerRef, autoFocus, focusFirst, handleKeyDown]);

  return {
    focusFirst,
    focusLast,
    getFocusableElements,
  };
};

/**
 * Hook for managing focus restoration
 */
export const useFocusRestore = () => {
  const previousActiveElement = useRef(null);

  const saveFocus = useCallback(() => {
    previousActiveElement.current = document.activeElement;
  }, []);

  const restoreFocus = useCallback(() => {
    if (
      previousActiveElement.current &&
      typeof previousActiveElement.current.focus === "function"
    ) {
      previousActiveElement.current.focus();
    }
  }, []);

  return {
    saveFocus,
    restoreFocus,
  };
};

/**
 * Hook for managing skip links
 */
export const useSkipLinks = () => {
  const skipLinksRef = useRef([]);

  const addSkipLink = useCallback((id, label) => {
    const existingIndex = skipLinksRef.current.findIndex(
      (link) => link.id === id
    );
    const newLink = { id, label };

    if (existingIndex >= 0) {
      skipLinksRef.current[existingIndex] = newLink;
    } else {
      skipLinksRef.current.push(newLink);
    }
  }, []);

  const removeSkipLink = useCallback((id) => {
    skipLinksRef.current = skipLinksRef.current.filter(
      (link) => link.id !== id
    );
  }, []);

  const skipToContent = useCallback((targetId) => {
    const target = document.getElementById(targetId);
    if (target) {
      target.focus();
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, []);

  return {
    skipLinks: skipLinksRef.current,
    addSkipLink,
    removeSkipLink,
    skipToContent,
  };
};

/**
 * Hook for managing reduced motion preferences
 */
export const useReducedMotion = () => {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    // Check if matchMedia is available (not available in some test environments)
    if (typeof window !== "undefined" && window.matchMedia) {
      try {
        const mediaQuery = window.matchMedia(
          "(prefers-reduced-motion: reduce)"
        );
        if (mediaQuery && typeof mediaQuery.matches !== "undefined") {
          setPrefersReducedMotion(mediaQuery.matches);

          const handleChange = (event) => {
            setPrefersReducedMotion(event.matches);
          };

          if (mediaQuery.addEventListener) {
            mediaQuery.addEventListener("change", handleChange);
          }

          return () => {
            if (mediaQuery.removeEventListener) {
              mediaQuery.removeEventListener("change", handleChange);
            }
          };
        }
      } catch (error) {
        // Silently fail in test environments
        console.warn("matchMedia not available:", error);
      }
    }
  }, []);

  return prefersReducedMotion;
};

/**
 * Hook for managing high contrast preferences
 */
export const useHighContrast = () => {
  const [prefersHighContrast, setPrefersHighContrast] = useState(false);

  useEffect(() => {
    // Check if matchMedia is available (not available in some test environments)
    if (typeof window !== "undefined" && window.matchMedia) {
      try {
        const mediaQuery = window.matchMedia("(prefers-contrast: high)");
        if (mediaQuery && typeof mediaQuery.matches !== "undefined") {
          setPrefersHighContrast(mediaQuery.matches);

          const handleChange = (event) => {
            setPrefersHighContrast(event.matches);
          };

          if (mediaQuery.addEventListener) {
            mediaQuery.addEventListener("change", handleChange);
          }

          return () => {
            if (mediaQuery.removeEventListener) {
              mediaQuery.removeEventListener("change", handleChange);
            }
          };
        }
      } catch (error) {
        // Silently fail in test environments
        console.warn("matchMedia not available:", error);
      }
    }
  }, []);

  return prefersHighContrast;
};

export default useAccessibility;
