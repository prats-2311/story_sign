import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import "./AuthPages.css";

const RegisterPage = () => {
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = useState({});
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState({
    score: 0,
    feedback: [],
  });

  const { register, isLoading, error, clearError } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // Focus on username field when component mounts
    const usernameInput = document.getElementById("username");
    if (usernameInput) {
      usernameInput.focus();
    }
  }, []);

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

  const calculatePasswordStrength = (password) => {
    let score = 0;
    const feedback = [];

    if (password.length >= 8) {
      score += 1;
    } else {
      feedback.push("Use at least 8 characters");
    }

    if (/[a-z]/.test(password)) {
      score += 1;
    } else {
      feedback.push("Include lowercase letters");
    }

    if (/[A-Z]/.test(password)) {
      score += 1;
    } else {
      feedback.push("Include uppercase letters");
    }

    if (/\d/.test(password)) {
      score += 1;
    } else {
      feedback.push("Include numbers");
    }

    if (/[^a-zA-Z\d]/.test(password)) {
      score += 1;
    } else {
      feedback.push("Include special characters");
    }

    return { score, feedback };
  };

  const validateForm = () => {
    const newErrors = {};

    // Username validation
    if (!formData.username.trim()) {
      newErrors.username = "Username is required";
    } else if (formData.username.length < 3) {
      newErrors.username = "Username must be at least 3 characters long";
    } else if (!/^[a-zA-Z0-9_-]+$/.test(formData.username)) {
      newErrors.username =
        "Username can only contain letters, numbers, hyphens, and underscores";
    }

    // Email validation
    if (!formData.email.trim()) {
      newErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "Please enter a valid email address";
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = "Password is required";
    } else if (formData.password.length < 8) {
      newErrors.password = "Password must be at least 8 characters long";
    } else if (passwordStrength.score < 3) {
      newErrors.password =
        "Password is too weak. Please follow the strength requirements.";
    }

    // Confirm password validation
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = "Please confirm your password";
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match";
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

    // Calculate password strength for password field
    if (name === "password") {
      const strength = calculatePasswordStrength(value);
      setPasswordStrength(strength);
    }

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
      const response = await register({
        username: formData.username,
        email: formData.email,
        password: formData.password,
      });

      console.log("Registration successful:", response);
      announceToScreenReader(
        "Registration successful. Redirecting to login..."
      );

      // Navigate to login page with success message
      navigate("/login", {
        state: {
          message:
            "Account created successfully! Please sign in with your new credentials.",
        },
      });
    } catch (error) {
      console.error("Registration error:", error);
      setErrors({
        submit: error.message || "Registration failed. Please try again.",
      });
      announceToScreenReader(
        `Registration failed: ${error.message || "Please try again."}`
      );
    } finally {
      // Loading state is managed by AuthContext
    }
  };

  const togglePasswordVisibility = (field) => {
    if (field === "password") {
      setShowPassword(!showPassword);
    } else if (field === "confirmPassword") {
      setShowConfirmPassword(!showConfirmPassword);
    }
  };

  const announceToScreenReader = (message) => {
    const announcement = document.getElementById("sr-announcement");
    if (announcement) {
      announcement.textContent = message;
    }
  };

  const getPasswordStrengthLabel = () => {
    const labels = ["Very Weak", "Weak", "Fair", "Good", "Strong"];
    return labels[passwordStrength.score] || "Very Weak";
  };

  const getPasswordStrengthClass = () => {
    const classes = ["very-weak", "weak", "fair", "good", "strong"];
    return classes[passwordStrength.score] || "very-weak";
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <header className="auth-header">
          <h1 className="auth-title">Create Your StorySign Account</h1>
          <p className="auth-subtitle">
            Join thousands of learners on their ASL journey. Create your free
            account to get started.
          </p>
        </header>

        <form onSubmit={handleSubmit} className="auth-form" noValidate>
          <div className="form-group">
            <label htmlFor="username" className="form-label">
              Username
              <span className="required-indicator" aria-label="required">
                *
              </span>
            </label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleInputChange}
              className={`form-input ${errors.username ? "error" : ""}`}
              placeholder="Choose a username"
              required
              autoComplete="username"
              aria-describedby={
                errors.username ? "username-error" : "username-help"
              }
              aria-invalid={errors.username ? "true" : "false"}
            />
            <div id="username-help" className="form-help">
              3+ characters, letters, numbers, hyphens, and underscores only
            </div>
            {errors.username && (
              <div id="username-error" className="error-message" role="alert">
                {errors.username}
              </div>
            )}
          </div>

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
                placeholder="Create a strong password"
                required
                autoComplete="new-password"
                aria-describedby="password-strength password-help"
                aria-invalid={errors.password ? "true" : "false"}
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => togglePasswordVisibility("password")}
                aria-label={showPassword ? "Hide password" : "Show password"}
                tabIndex="0"
              >
                {showPassword ? "👁️‍🗨️" : "👁️"}
              </button>
            </div>

            {formData.password && (
              <div id="password-strength" className="password-strength">
                <div className="strength-meter">
                  <div
                    className={`strength-bar ${getPasswordStrengthClass()}`}
                    style={{ width: `${(passwordStrength.score / 5) * 100}%` }}
                    aria-hidden="true"
                  ></div>
                </div>
                <div className="strength-label">
                  Strength:{" "}
                  <span className={getPasswordStrengthClass()}>
                    {getPasswordStrengthLabel()}
                  </span>
                </div>
                {passwordStrength.feedback.length > 0 && (
                  <ul className="strength-feedback">
                    {passwordStrength.feedback.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            <div id="password-help" className="form-help">
              Use at least 8 characters with a mix of letters, numbers, and
              symbols
            </div>
            {errors.password && (
              <div className="error-message" role="alert">
                {errors.password}
              </div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword" className="form-label">
              Confirm Password
              <span className="required-indicator" aria-label="required">
                *
              </span>
            </label>
            <div className="password-input-container">
              <input
                type={showConfirmPassword ? "text" : "password"}
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleInputChange}
                className={`form-input ${
                  errors.confirmPassword ? "error" : ""
                }`}
                placeholder="Confirm your password"
                required
                autoComplete="new-password"
                aria-describedby={
                  errors.confirmPassword ? "confirm-password-error" : undefined
                }
                aria-invalid={errors.confirmPassword ? "true" : "false"}
              />
              <button
                type="button"
                className="password-toggle"
                onClick={() => togglePasswordVisibility("confirmPassword")}
                aria-label={
                  showConfirmPassword
                    ? "Hide password confirmation"
                    : "Show password confirmation"
                }
                tabIndex="0"
              >
                {showConfirmPassword ? "👁️‍🗨️" : "👁️"}
              </button>
            </div>
            {errors.confirmPassword && (
              <div
                id="confirm-password-error"
                className="error-message"
                role="alert"
              >
                {errors.confirmPassword}
              </div>
            )}
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
            aria-describedby="register-button-description"
          >
            {isLoading ? (
              <>
                <span className="loading-spinner" aria-hidden="true"></span>
                Creating Account...
              </>
            ) : (
              "Create Account"
            )}
          </button>

          <div id="register-button-description" className="sr-only">
            Click to create your new StorySign account
          </div>
        </form>

        <footer className="auth-footer">
          <p className="auth-link-text">
            Already have an account?{" "}
            <Link to="/login" className="auth-link">
              Sign in here
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

export default RegisterPage;
