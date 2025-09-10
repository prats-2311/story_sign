import React, { useEffect, useRef, useCallback } from "react";
import { createPortal } from "react-dom";
import Button from "./Button";
import "./Modal.css";

/**
 * Accessible Modal component with focus management and escape key handling
 * Follows WCAG 2.1 AA guidelines for dialog patterns
 */
const Modal = ({
  isOpen,
  onClose,
  title,
  children,
  size = "medium",
  closeOnOverlayClick = true,
  closeOnEscape = true,
  showCloseButton = true,
  className = "",
  ariaDescribedBy,
  initialFocusRef,
  finalFocusRef,
}) => {
  const modalRef = useRef(null);
  const overlayRef = useRef(null);
  const previousActiveElement = useRef(null);
  const titleId = useRef(
    `modal-title-${Math.random().toString(36).substr(2, 9)}`
  );

  // Store the previously focused element when modal opens
  useEffect(() => {
    if (isOpen) {
      previousActiveElement.current = document.activeElement;
    }
  }, [isOpen]);

  // Focus management
  const focusModal = useCallback(() => {
    if (initialFocusRef?.current) {
      initialFocusRef.current.focus();
    } else if (modalRef.current) {
      // Focus the first focusable element in the modal
      const focusableElements = modalRef.current.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      if (focusableElements.length > 0) {
        focusableElements[0].focus();
      } else {
        modalRef.current.focus();
      }
    }
  }, [initialFocusRef]);

  // Trap focus within modal
  const handleKeyDown = useCallback(
    (event) => {
      if (!modalRef.current) return;

      if (event.key === "Escape" && closeOnEscape) {
        event.preventDefault();
        onClose();
        return;
      }

      if (event.key === "Tab") {
        const focusableElements = modalRef.current.querySelectorAll(
          'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (event.shiftKey) {
          // Shift + Tab
          if (document.activeElement === firstElement) {
            event.preventDefault();
            lastElement?.focus();
          }
        } else {
          // Tab
          if (document.activeElement === lastElement) {
            event.preventDefault();
            firstElement?.focus();
          }
        }
      }
    },
    [closeOnEscape, onClose]
  );

  // Handle overlay click
  const handleOverlayClick = useCallback(
    (event) => {
      if (closeOnOverlayClick && event.target === overlayRef.current) {
        onClose();
      }
    },
    [closeOnOverlayClick, onClose]
  );

  // Effect for focus management and event listeners
  useEffect(() => {
    if (isOpen) {
      // Prevent body scroll
      document.body.style.overflow = "hidden";

      // Add event listeners
      document.addEventListener("keydown", handleKeyDown);

      // Focus the modal after a brief delay to ensure it's rendered
      const focusTimeout = setTimeout(focusModal, 100);

      return () => {
        document.removeEventListener("keydown", handleKeyDown);
        clearTimeout(focusTimeout);
      };
    } else {
      // Restore body scroll
      document.body.style.overflow = "";

      // Return focus to the previously focused element
      if (finalFocusRef?.current) {
        finalFocusRef.current.focus();
      } else if (previousActiveElement.current) {
        previousActiveElement.current.focus();
      }
    }
  }, [isOpen, handleKeyDown, focusModal, finalFocusRef]);

  if (!isOpen) {
    return null;
  }

  const modalClasses = ["modal-content", `modal-${size}`, className]
    .filter(Boolean)
    .join(" ");

  const modalElement = (
    <div
      className="modal-overlay"
      ref={overlayRef}
      onClick={handleOverlayClick}
      role="presentation"
    >
      <div
        ref={modalRef}
        className={modalClasses}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId.current}
        aria-describedby={ariaDescribedBy}
        tabIndex={-1}
      >
        <div className="modal-header">
          <h2 id={titleId.current} className="modal-title">
            {title}
          </h2>
          {showCloseButton && (
            <Button
              variant="secondary"
              size="small"
              onClick={onClose}
              ariaLabel="Close modal"
              className="modal-close-button"
            >
              ×
            </Button>
          )}
        </div>

        <div className="modal-body">{children}</div>
      </div>
    </div>
  );

  // Render modal in a portal to avoid z-index issues
  return createPortal(modalElement, document.body);
};

export default Modal;
