import React, { forwardRef, useId } from "react";
import { useAccessibility } from "../../hooks/useAccessibility";
import "./AccessibleForm.css";

/**
 * Accessible Form Field component with proper labeling and error handling
 */
export const FormField = forwardRef(
  (
    {
      id,
      label,
      type = "text",
      required = false,
      error,
      helpText,
      children,
      className = "",
      ...props
    },
    ref
  ) => {
    const generatedId = useId();
    const fieldId = id || generatedId;
    const errorId = useId();
    const helpId = useId();
    const { announce } = useAccessibility();

    const handleInvalid = (event) => {
      event.preventDefault();
      const message = error || event.target.validationMessage;
      announce(`Form error: ${message}`, "assertive");
    };

    const fieldClasses = ["form-field", error && "form-field-error", className]
      .filter(Boolean)
      .join(" ");

    const inputClasses = ["form-input", error && "form-input-error"]
      .filter(Boolean)
      .join(" ");

    const describedBy = [error && errorId, helpText && helpId]
      .filter(Boolean)
      .join(" ");

    return (
      <div className={fieldClasses}>
        <label htmlFor={fieldId} className="form-label">
          {label}
          {required && (
            <span className="required-indicator" aria-label="required">
              *
            </span>
          )}
        </label>

        {children || (
          <input
            ref={ref}
            id={fieldId}
            type={type}
            className={inputClasses}
            required={required}
            aria-invalid={error ? "true" : "false"}
            aria-describedby={describedBy || undefined}
            onInvalid={handleInvalid}
            {...props}
          />
        )}

        {helpText && (
          <div id={helpId} className="form-help">
            {helpText}
          </div>
        )}

        {error && (
          <div id={errorId} className="form-error" role="alert">
            {error}
          </div>
        )}
      </div>
    );
  }
);

/**
 * Accessible Select component
 */
export const AccessibleSelect = forwardRef(
  (
    {
      label,
      options = [],
      placeholder = "Select an option",
      required = false,
      error,
      helpText,
      className = "",
      ...props
    },
    ref
  ) => {
    const fieldId = useId();
    const errorId = useId();
    const helpId = useId();

    const describedBy = [error && errorId, helpText && helpId]
      .filter(Boolean)
      .join(" ");

    return (
      <div
        className={`form-field ${error ? "form-field-error" : ""} ${className}`}
      >
        <label htmlFor={fieldId} className="form-label">
          {label}
          {required && (
            <span className="required-indicator" aria-label="required">
              *
            </span>
          )}
        </label>

        <select
          ref={ref}
          id={fieldId}
          className={`form-select ${error ? "form-select-error" : ""}`}
          required={required}
          aria-invalid={error ? "true" : "false"}
          aria-describedby={describedBy || undefined}
          {...props}
        >
          <option value="" disabled>
            {placeholder}
          </option>
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        {helpText && (
          <div id={helpId} className="form-help">
            {helpText}
          </div>
        )}

        {error && (
          <div id={errorId} className="form-error" role="alert">
            {error}
          </div>
        )}
      </div>
    );
  }
);

/**
 * Accessible Textarea component
 */
export const AccessibleTextarea = forwardRef(
  (
    {
      label,
      required = false,
      error,
      helpText,
      rows = 4,
      className = "",
      ...props
    },
    ref
  ) => {
    const fieldId = useId();
    const errorId = useId();
    const helpId = useId();

    const describedBy = [error && errorId, helpText && helpId]
      .filter(Boolean)
      .join(" ");

    return (
      <div
        className={`form-field ${error ? "form-field-error" : ""} ${className}`}
      >
        <label htmlFor={fieldId} className="form-label">
          {label}
          {required && (
            <span className="required-indicator" aria-label="required">
              *
            </span>
          )}
        </label>

        <textarea
          ref={ref}
          id={fieldId}
          rows={rows}
          className={`form-textarea ${error ? "form-textarea-error" : ""}`}
          required={required}
          aria-invalid={error ? "true" : "false"}
          aria-describedby={describedBy || undefined}
          {...props}
        />

        {helpText && (
          <div id={helpId} className="form-help">
            {helpText}
          </div>
        )}

        {error && (
          <div id={errorId} className="form-error" role="alert">
            {error}
          </div>
        )}
      </div>
    );
  }
);

/**
 * Accessible Checkbox component
 */
export const AccessibleCheckbox = forwardRef(
  (
    { label, required = false, error, helpText, className = "", ...props },
    ref
  ) => {
    const fieldId = useId();
    const errorId = useId();
    const helpId = useId();

    const describedBy = [error && errorId, helpText && helpId]
      .filter(Boolean)
      .join(" ");

    return (
      <div
        className={`form-field form-field-checkbox ${
          error ? "form-field-error" : ""
        } ${className}`}
      >
        <div className="checkbox-wrapper">
          <input
            ref={ref}
            id={fieldId}
            type="checkbox"
            className={`form-checkbox ${error ? "form-checkbox-error" : ""}`}
            required={required}
            aria-invalid={error ? "true" : "false"}
            aria-describedby={describedBy || undefined}
            {...props}
          />
          <label htmlFor={fieldId} className="checkbox-label">
            {label}
            {required && (
              <span className="required-indicator" aria-label="required">
                *
              </span>
            )}
          </label>
        </div>

        {helpText && (
          <div id={helpId} className="form-help">
            {helpText}
          </div>
        )}

        {error && (
          <div id={errorId} className="form-error" role="alert">
            {error}
          </div>
        )}
      </div>
    );
  }
);

/**
 * Accessible Fieldset component for grouping related form controls
 */
export const AccessibleFieldset = ({
  legend,
  children,
  className = "",
  ...props
}) => {
  return (
    <fieldset className={`form-fieldset ${className}`} {...props}>
      <legend className="form-legend">{legend}</legend>
      {children}
    </fieldset>
  );
};

FormField.displayName = "FormField";
AccessibleSelect.displayName = "AccessibleSelect";
AccessibleTextarea.displayName = "AccessibleTextarea";
AccessibleCheckbox.displayName = "AccessibleCheckbox";
AccessibleFieldset.displayName = "AccessibleFieldset";

export default FormField;
