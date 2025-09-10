import React from "react";
import "./AccessibleHeading.css";

/**
 * Accessible Heading component that ensures proper heading hierarchy
 * Automatically manages heading levels and provides screen reader context
 */
const AccessibleHeading = ({
  level = 1,
  children,
  className = "",
  id,
  visualLevel,
  srOnly = false,
  ...props
}) => {
  // Ensure level is between 1 and 6
  const headingLevel = Math.max(1, Math.min(6, level));
  const HeadingTag = `h${headingLevel}`;

  // Use visual level for styling if provided, otherwise use semantic level
  const styleLevel = visualLevel || headingLevel;

  const headingClasses = [
    "accessible-heading",
    `heading-level-${headingLevel}`,
    `heading-style-${styleLevel}`,
    srOnly && "sr-only",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <HeadingTag id={id} className={headingClasses} {...props}>
      {children}
    </HeadingTag>
  );
};

/**
 * Hook to manage heading hierarchy context
 */
export const useHeadingLevel = (parentLevel = 0) => {
  const currentLevel = parentLevel + 1;

  const getNextLevel = () => currentLevel + 1;

  return {
    currentLevel: Math.min(currentLevel, 6),
    getNextLevel,
  };
};

export default AccessibleHeading;
