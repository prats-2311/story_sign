import React from "react";
import "./SkipLinks.css";

/**
 * Skip Links component for keyboard navigation
 * Provides quick navigation to main content areas
 */
const SkipLinks = ({ links = [] }) => {
  const defaultLinks = [
    { id: "main-content", label: "Skip to main content" },
    { id: "main-navigation", label: "Skip to navigation" },
    { id: "page-footer", label: "Skip to footer" },
  ];

  const allLinks = [...defaultLinks, ...links];

  const handleSkipClick = (event, targetId) => {
    event.preventDefault();
    const target = document.getElementById(targetId);

    if (target) {
      // Make target focusable if it isn't already
      if (!target.hasAttribute("tabindex")) {
        target.setAttribute("tabindex", "-1");
      }

      target.focus();
      target.scrollIntoView({ behavior: "smooth", block: "start" });

      // Remove tabindex after focus to restore natural tab order
      setTimeout(() => {
        if (target.getAttribute("tabindex") === "-1") {
          target.removeAttribute("tabindex");
        }
      }, 100);
    }
  };

  if (allLinks.length === 0) {
    return null;
  }

  return (
    <nav className="skip-links" aria-label="Skip navigation">
      <ul className="skip-links-list">
        {allLinks.map((link) => (
          <li key={link.id} className="skip-links-item">
            <a
              href={`#${link.id}`}
              className="skip-link"
              onClick={(e) => handleSkipClick(e, link.id)}
            >
              {link.label}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  );
};

export default SkipLinks;
