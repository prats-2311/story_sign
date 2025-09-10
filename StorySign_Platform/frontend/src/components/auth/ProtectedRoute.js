import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import "./AuthComponents.css";

/**
 * ProtectedRoute component that redirects unauthenticated users to login
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Child components to render if authenticated
 * @param {string[]} props.requiredRoles - Optional array of required roles
 * @param {string[]} props.requiredPermissions - Optional array of required permissions
 * @param {string} props.redirectTo - Optional custom redirect path (defaults to /login)
 * @param {React.ReactNode} props.fallback - Optional fallback component for loading state
 */
const ProtectedRoute = ({
  children,
  requiredRoles = [],
  requiredPermissions = [],
  redirectTo = "/login",
  fallback = null,
}) => {
  const { isAuthenticated, isLoading, user, hasRole, hasPermission } =
    useAuth();
  const location = useLocation();

  // Show loading state while authentication is being determined
  if (isLoading) {
    return (
      fallback || (
        <div className="auth-loading-container">
          <div className="auth-loading-spinner">
            <div className="spinner"></div>
            <p>Checking authentication...</p>
          </div>
        </div>
      )
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to={redirectTo} state={{ from: location }} replace />;
  }

  // Check role requirements
  if (requiredRoles.length > 0) {
    const hasRequiredRole = requiredRoles.some((role) => hasRole(role));
    if (!hasRequiredRole) {
      return (
        <div className="access-denied-container">
          <div className="access-denied-content">
            <h2>Access Denied</h2>
            <p>You don't have the required permissions to access this page.</p>
            <p>Required roles: {requiredRoles.join(", ")}</p>
            <button
              onClick={() => window.history.back()}
              className="back-button"
            >
              Go Back
            </button>
          </div>
        </div>
      );
    }
  }

  // Check permission requirements
  if (requiredPermissions.length > 0) {
    const hasRequiredPermission = requiredPermissions.some((permission) =>
      hasPermission(permission)
    );
    if (!hasRequiredPermission) {
      return (
        <div className="access-denied-container">
          <div className="access-denied-content">
            <h2>Access Denied</h2>
            <p>You don't have the required permissions to access this page.</p>
            <p>Required permissions: {requiredPermissions.join(", ")}</p>
            <button
              onClick={() => window.history.back()}
              className="back-button"
            >
              Go Back
            </button>
          </div>
        </div>
      );
    }
  }

  // User is authenticated and has required permissions
  return children;
};

export default ProtectedRoute;
