import React, { forwardRef } from "react";
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
      loading = false,
      className = "",
      ...props
    },
    ref
  ) => {
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
        aria-disabled={disabled || loading}
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
      </button>
    );
  }
);

Button.displayName = "Button";

export default Button;
