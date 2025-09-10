import React, { useState, useEffect } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import "./AuthPages.css";

const LoginPage = () => {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [errors, setErrors] = useState({});
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  const { login, isLoading, error, clearError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Get the intended destination from location state
  const from = location.state?.from?.pathname || "/";

  // Handle context errors
  useEffect(() => {
    if (error) {
      setErrors({ submit: error });
    }
  }, [error]);

  // Clear context error when component unmounts or form changes
  useEffect(() => {
    return () => {
      if (error) {
        clearError();
      }
    };
  }, [error, clearError]);

  useEffect(() => {
    // Focus on email field when component mounts
    const emailInput = document.getElementById("email");
    if (emailInput) {
      emailInput.focus();
    }
  }, []);

  const validateForm = () => {
    const newErrors = {};

    // Email validation
    if (!formData.email.trim()) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "Please enter a valid email address";
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = "Password is required";
    } else if (formData.password.length < 6) {
      newErrors.password = "Password must be at least 6 characters long";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));

    // Clear error for this field when user starts typing
    if (errors[name]) {
      setErrors((prev) => ({
        ...prev,
        [name]: "",
      }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      // Announce validation errors to screen readers
      const errorMessages = Object.values(errors).join(". ");
      const announcement = `Form has errors: ${errorMessages}`;
      announceToScreenReader(announcement);
      return;
    }

    setErrors({});

    try {
      const response = await login(
        formData.email,
        formData.password,
        rememberMe
      );

      console.log("Login successful:", response.user.email);
      announceToScreenReader("Login successful. Redirecting...");

      // Navigate to intended destination or home
      navigate(from, { replace: true });
    } catch (error) {
      console.error("Login error:", error);
      setErrors({
        submit:
          error.message ||
          "Login failed. Please check your credentials and try again.",
      });
      announceToScreenReader(
        `Login failed: ${
          error.message || "Please check your credentials and try again."
        }`
      );
    } finally {
      // Loading state is managed by AuthContext
    }
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  const announceToScreenReader = (message) => {
    const announcement = document.getElementById("sr-announcement");
    if (announcement) {
      announcement.textContent = message;
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <header className="auth-header">
          <h1 className="auth-title">Sign In to StorySign</h1>
          <p className="auth-subtitle">
            Welcome back! Please sign in to continue your ASL learning journey.
          </p>
        </header>

        <form onSubmit={handleSubmit} className="auth-form" noValidate>
          <div className="form-group">
            <label htmlFor="email" className="form-label">
              Email Address
              <span className="required-indicator" aria-label="required">
                *
              </span>
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              className={`form-input ${errors.email ? "error" : ""}`}
              placeholder="Enter your email address"
              required
              autoComplete="email"
              aria-describedby={errors.email ? "email-error" : undefined}
              aria-invalid={errors.email ? "true" : "false"}
            />
            {errors.email && (
              <div id="email-error" className="error-message" role="alert">
                {errors.email}
              </div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="password" className="form-label">
              Password
              <span className="required-indicator" aria-label="required">
                *
              </span>
            </label>
            <div className="password-input-container">
              <input
                type={showPassword ? "text" : "password"}
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                className={`form-input ${errors.password ? "error" : ""}`}
                placeholder="Enter your password"
                required
                autoComplete="current-password"
                aria-describedby={
                  errors.password ? "password-error" : undefined
                }
                aria-invalid={errors.password ? "true" : "false"}
              />
              <button
                type="button"
                className="password-toggle"
                onClick={togglePasswordVisibility}
                aria-label={showPassword ? "Hide password" : "Show password"}
                tabIndex="0"
              >
                {showPassword ? "👁️‍🗨️" : "👁️"}
              </button>
            </div>
            {errors.password && (
              <div id="password-error" className="error-message" role="alert">
                {errors.password}
              </div>
            )}
          </div>

          <div className="form-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="checkbox-input"
              />
              <span className="checkbox-text">Remember me</span>
            </label>
          </div>

          {errors.submit && (
            <div className="error-message submit-error" role="alert">
              {errors.submit}
            </div>
          )}

          <button
            type="submit"
            className="auth-button primary"
            disabled={isLoading}
            aria-describedby="login-button-description"
          >
            {isLoading ? (
              <>
                <span className="loading-spinner" aria-hidden="true"></span>
                Signing In...
              </>
            ) : (
              "Sign In"
            )}
          </button>

          <div id="login-button-description" className="sr-only">
            Click to sign in with your email and password
          </div>
        </form>

        <footer className="auth-footer">
          <p className="auth-link-text">
            Don't have an account?{" "}
            <Link to="/register" className="auth-link">
              Create one here
            </Link>
          </p>
          <p className="auth-link-text">
            <Link to="/forgot-password" className="auth-link">
              Forgot your password?
            </Link>
          </p>
        </footer>
      </div>

      {/* Screen reader announcements */}
      <div
        id="sr-announcement"
        className="sr-only"
        aria-live="polite"
        aria-atomic="true"
      ></div>
    </div>
  );
};

export default LoginPage;
