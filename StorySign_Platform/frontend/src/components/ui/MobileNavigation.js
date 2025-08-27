import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { usePlatform } from "../shell/PlatformShell";
import "./MobileNavigation.css";

const MobileNavigation = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { modules } = usePlatform();

  // Filter out disabled modules and limit to main navigation items
  const mainModules = modules.filter((module) => !module.disabled).slice(0, 5);

  const handleNavigation = (route) => {
    navigate(route);
  };

  const isActive = (route) => {
    if (route === "/") {
      return location.pathname === "/";
    }
    return location.pathname.startsWith(route);
  };

  return (
    <nav className="mobile-nav" role="navigation" aria-label="Main navigation">
      <ul className="mobile-nav-list">
        {mainModules.map((module) => (
          <li key={module.id} className="mobile-nav-item">
            <button
              className={`mobile-nav-link ${
                isActive(module.route) ? "active" : ""
              }`}
              onClick={() => handleNavigation(module.route)}
              aria-label={`Navigate to ${module.name}`}
              aria-current={isActive(module.route) ? "page" : undefined}
            >
              <span className="mobile-nav-icon" aria-hidden="true">
                {module.icon}
              </span>
              <span className="mobile-nav-text">{module.name}</span>
            </button>
          </li>
        ))}
      </ul>
    </nav>
  );
};

export default MobileNavigation;
