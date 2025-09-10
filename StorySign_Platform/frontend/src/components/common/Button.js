import React, { forwardRef } from "react";
import { useReducedMotion } from "../../hooks/useAccessibility";
import "./Button.css";

/**
 * Accessible Button component with ARIA support and keyboard navigation
 * Follows WCAG 2.1 AA guidelines for interactive elements
 */
const Button = forwardRef(
  (
    {
      children,
      onClick,
      disabled = false,
      variant = "primary",
      size = "medium",
      type = "button",
      ariaLabel,
      ariaDescribedBy,
      ariaPressed,
      ariaExpanded,
      loading = false,
      className = "",
      tooltip,
      ...props
    },
    ref
  ) => {
    const prefersReducedMotion = useReducedMotion();

    const handleClick = (event) => {
      if (disabled || loading) {
        event.preventDefault();
        return;
      }
      if (onClick) {
        onClick(event);
      }
    };

    const handleKeyDown = (event) => {
      // Handle Enter and Space key activation
      if (
        (event.key === "Enter" || event.key === " ") &&
        !disabled &&
        !loading
      ) {
        event.preventDefault();
        if (onClick) {
          onClick(event);
        }
      }
    };

    const buttonClasses = [
      "accessible-button",
      `button-${variant}`,
      `button-${size}`,
      disabled && "button-disabled",
      loading && "button-loading",
      prefersReducedMotion && "reduced-motion",
      className,
    ]
      .filter(Boolean)
      .join(" ");

    return (
      <button
        ref={ref}
        type={type}
        className={buttonClasses}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        disabled={disabled || loading}
        aria-label={ariaLabel}
        aria-describedby={ariaDescribedBy}
        aria-pressed={ariaPressed}
        aria-expanded={ariaExpanded}
        aria-disabled={disabled || loading}
        title={tooltip}
        {...props}
      >
        {loading && (
          <span className="button-spinner" aria-hidden="true">
            <span className="spinner-icon"></span>
          </span>
        )}
        <span className={loading ? "button-content-loading" : "button-content"}>
          {children}
        </span>
        {loading && (
          <span className="sr-only">
            {ariaLabel ? `${ariaLabel} - Loading` : "Loading"}
          </span>
        )}
      </button>
    );
  }
);

Button.displayName = "Button";

export default Button;
