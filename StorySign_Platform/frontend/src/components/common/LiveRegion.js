import React, { useEffect, useRef } from "react";

/**
 * Live Region component for screen reader announcements
 * Provides different politeness levels for various types of updates
 */
const LiveRegion = ({
  message,
  politeness = "polite",
  atomic = true,
  relevant = "additions text",
  className = "sr-only",
  clearDelay = 1000,
}) => {
  const regionRef = useRef(null);
  const timeoutRef = useRef(null);

  useEffect(() => {
    if (message && regionRef.current) {
      // Clear any existing timeout
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      // Set the message
      regionRef.current.textContent = message;

      // Clear the message after delay to allow for re-announcements
      if (clearDelay > 0) {
        timeoutRef.current = setTimeout(() => {
          if (regionRef.current) {
            regionRef.current.textContent = "";
          }
        }, clearDelay);
      }
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [message, clearDelay]);

  return (
    <div
      ref={regionRef}
      className={className}
      aria-live={politeness}
      aria-atomic={atomic}
      aria-relevant={relevant}
      role="status"
    />
  );
};

/**
 * Assertive Live Region for urgent announcements
 */
export const AssertiveLiveRegion = ({ message, ...props }) => (
  <LiveRegion
    message={message}
    politeness="assertive"
    clearDelay={2000}
    {...props}
  />
);

/**
 * Status Live Region for status updates
 */
export const StatusLiveRegion = ({ message, ...props }) => (
  <LiveRegion
    message={message}
    politeness="polite"
    clearDelay={1000}
    {...props}
  />
);

export default LiveRegion;
