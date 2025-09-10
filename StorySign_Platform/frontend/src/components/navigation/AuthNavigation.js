import React, { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import "./AuthNavigation.css";

const AuthNavigation = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    try {
      await logout();
      setIsUserMenuOpen(false);
      navigate("/login");
    } catch (error) {
      console.error("Logout error:", error);
    }
  };

  const toggleUserMenu = () => {
    setIsUserMenuOpen(!isUserMenuOpen);
  };

  const closeUserMenu = () => {
    setIsUserMenuOpen(false);
  };

  // Don't render navigation on auth pages
  const authPages = [
    "/login",
    "/register",
    "/forgot-password",
    "/reset-password",
  ];
  if (authPages.includes(location.pathname)) {
    return null;
  }

  return (
    <nav
      className="auth-navigation"
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="nav-container">
        {/* Logo/Brand */}
        <div className="nav-brand">
          <Link to="/" className="brand-link">
            <span className="brand-text">StorySign</span>
          </Link>
        </div>

        {/* Main Navigation Links */}
        <div className="nav-links">
          {isAuthenticated ? (
            <>
              <Link
                to="/asl-world"
                className={`nav-link ${
                  location.pathname === "/asl-world" ? "active" : ""
                }`}
              >
                ASL World
              </Link>
              <Link
                to="/harmony"
                className={`nav-link ${
                  location.pathname === "/harmony" ? "active" : ""
                }`}
              >
                Harmony
              </Link>
              <Link
                to="/reconnect"
                className={`nav-link ${
                  location.pathname === "/reconnect" ? "active" : ""
                }`}
              >
                Reconnect
              </Link>
              <Link
                to="/plugins"
                className={`nav-link ${
                  location.pathname === "/plugins" ? "active" : ""
                }`}
              >
                Plugins
              </Link>
            </>
          ) : (
            <div className="nav-auth-links">
              <Link to="/login" className="nav-link">
                Sign In
              </Link>
              <Link to="/register" className="nav-link nav-link-primary">
                Get Started
              </Link>
            </div>
          )}
        </div>

        {/* User Menu */}
        {isAuthenticated && user && (
          <div className="user-menu-container">
            <button
              className="user-menu-trigger"
              onClick={toggleUserMenu}
              onBlur={(e) => {
                // Close menu if focus moves outside the menu container
                if (!e.currentTarget.parentNode.contains(e.relatedTarget)) {
                  closeUserMenu();
                }
              }}
              aria-expanded={isUserMenuOpen}
              aria-haspopup="true"
              aria-label={`User menu for ${user.username || user.email}`}
            >
              <div className="user-avatar">
                {user.avatar ? (
                  <img
                    src={user.avatar}
                    alt={`${user.username || user.email} avatar`}
                    className="avatar-image"
                  />
                ) : (
                  <span className="avatar-initials">
                    {(user.username || user.email).charAt(0).toUpperCase()}
                  </span>
                )}
              </div>
              <span className="user-name">
                {user.username || user.email.split("@")[0]}
              </span>
              <span className="menu-arrow" aria-hidden="true">
                {isUserMenuOpen ? "▲" : "▼"}
              </span>
            </button>

            {isUserMenuOpen && (
              <div
                className="user-menu-dropdown"
                role="menu"
                aria-label="User menu"
              >
                <div className="user-menu-header">
                  <div className="user-info">
                    <div className="user-display-name">
                      {user.username || user.email.split("@")[0]}
                    </div>
                    <div className="user-email">{user.email}</div>
                  </div>
                </div>

                <div className="user-menu-divider"></div>

                <Link
                  to="/profile"
                  className="user-menu-item"
                  role="menuitem"
                  onClick={closeUserMenu}
                >
                  <span className="menu-icon">👤</span>
                  Profile Settings
                </Link>

                <Link
                  to="/dashboard"
                  className="user-menu-item"
                  role="menuitem"
                  onClick={closeUserMenu}
                >
                  <span className="menu-icon">📊</span>
                  Dashboard
                </Link>

                <Link
                  to="/progress"
                  className="user-menu-item"
                  role="menuitem"
                  onClick={closeUserMenu}
                >
                  <span className="menu-icon">📈</span>
                  My Progress
                </Link>

                <div className="user-menu-divider"></div>

                <button
                  className="user-menu-item logout-item"
                  role="menuitem"
                  onClick={handleLogout}
                >
                  <span className="menu-icon">🚪</span>
                  Sign Out
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </nav>
  );
};

export default AuthNavigation;
