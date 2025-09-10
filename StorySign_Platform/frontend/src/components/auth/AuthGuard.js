import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import "./AuthComponents.css";

/**
 * AuthGuard component that redirects authenticated users away from auth pages
 * Useful for login/register pages that shouldn't be accessible when already logged in
 */
const AuthGuard = ({ children, redirectTo = "/" }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  // Show loading state while authentication is being determined
  if (isLoading) {
    return (
      <div className="auth-loading-container">
        <div className="auth-loading-spinner">
          <div className="spinner"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  // Redirect authenticated users away from auth pages
  if (isAuthenticated) {
    // Check if there's a redirect destination in location state
    const from = location.state?.from?.pathname || redirectTo;
    return <Navigate to={from} replace />;
  }

  // User is not authenticated, show the auth page
  return children;
};

export default AuthGuard;
