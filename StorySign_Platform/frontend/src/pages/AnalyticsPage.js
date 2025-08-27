/**
 * Analytics Page Component
 * Main page for analytics dashboard and reporting
 */

import React, { useState, useEffect } from "react";
import AnalyticsDashboard from "../components/analytics/AnalyticsDashboard";
import { useAnalytics } from "../hooks/useAnalytics";
import "./AnalyticsPage.css";

const AnalyticsPage = () => {
  const [userRole, setUserRole] = useState("educator");
  const [hasAccess, setHasAccess] = useState(false);
  const [loading, setLoading] = useState(true);
  const analytics = useAnalytics("analytics");

  useEffect(() => {
    // Track page view
    analytics.trackPageView("Analytics Dashboard");

    // Check user permissions
    checkUserAccess();
  }, []);

  const checkUserAccess = async () => {
    try {
      // Get user info from token or API
      const token = localStorage.getItem("auth_token");
      if (!token) {
        setHasAccess(false);
        setLoading(false);
        return;
      }

      // For now, assume user has access if they have a token
      // In a real implementation, you'd verify the user's role
      setUserRole("educator"); // This would come from user data
      setHasAccess(true);
    } catch (error) {
      console.error("Error checking user access:", error);
      setHasAccess(false);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="analytics-page-loading">
        <div className="loading-spinner"></div>
        <p>Loading analytics dashboard...</p>
      </div>
    );
  }

  if (!hasAccess) {
    return (
      <div className="analytics-page-no-access">
        <div className="no-access-content">
          <h2>Access Restricted</h2>
          <p>
            You need educator or researcher permissions to access the analytics
            dashboard.
          </p>
          <p>Please contact your administrator to request access.</p>
          <button onClick={() => window.history.back()} className="back-button">
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="analytics-page">
      <div className="page-header">
        <div className="header-content">
          <h1>Analytics & Reporting</h1>
          <p className="page-description">
            Comprehensive analytics dashboard for tracking learning progress,
            system performance, and generating research insights.
          </p>
        </div>
        <div className="user-role-indicator">
          <span className="role-label">Access Level:</span>
          <span className={`role-badge ${userRole}`}>
            {userRole.charAt(0).toUpperCase() + userRole.slice(1)}
          </span>
        </div>
      </div>

      <div className="dashboard-container">
        <AnalyticsDashboard userRole={userRole} />
      </div>

      <div className="page-footer">
        <div className="footer-info">
          <p>
            <strong>Privacy Notice:</strong> All analytics data is collected and
            processed in accordance with our privacy policy and user consent
            preferences.
          </p>
          <p>
            <strong>Data Retention:</strong> Analytics data is retained
            according to institutional policies and regulatory requirements.
          </p>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;
