import React, { useState, useEffect } from "react";
import "./PrivacyDashboard.css";

const PrivacyDashboard = () => {
  const [privacyData, setPrivacyData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    fetchPrivacyDashboard();
  }, []);

  const fetchPrivacyDashboard = async () => {
    try {
      setLoading(true);
      const response = await fetch("/api/v1/privacy/dashboard", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch privacy dashboard");
      }

      const data = await response.json();
      setPrivacyData(data.privacy_dashboard);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleConsentChange = async (consentType, action) => {
    try {
      const response = await fetch("/api/v1/privacy/consent", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          consent_type: consentType,
          action: action,
          consent_details: {
            timestamp: new Date().toISOString(),
            source: "privacy_dashboard",
          },
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to update consent");
      }

      // Refresh dashboard data
      await fetchPrivacyDashboard();
    } catch (err) {
      setError(err.message);
    }
  };

  const requestDataExport = async () => {
    try {
      const response = await fetch("/api/v1/privacy/export-request", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          export_format: "json",
          export_scope: {
            include_profile: true,
            include_progress: true,
            include_practice_sessions: true,
          },
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to request data export");
      }

      const data = await response.json();
      alert(
        `Data export requested successfully. Request ID: ${data.request_id}`
      );
    } catch (err) {
      setError(err.message);
    }
  };

  const requestDataDeletion = async () => {
    const confirmed = window.confirm(
      "Are you sure you want to request data deletion? This action cannot be undone."
    );

    if (!confirmed) return;

    try {
      const response = await fetch("/api/v1/privacy/delete-request", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          request_type: "full_deletion",
          deletion_scope: {
            include_all: true,
          },
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to request data deletion");
      }

      const data = await response.json();
      alert(
        `Data deletion requested successfully. You will receive a verification email. Request ID: ${data.request_id}`
      );
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) {
    return (
      <div className="privacy-dashboard loading">
        <div className="loading-spinner"></div>
        <p>Loading privacy dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="privacy-dashboard error">
        <h2>Error Loading Privacy Dashboard</h2>
        <p>{error}</p>
        <button onClick={fetchPrivacyDashboard}>Retry</button>
      </div>
    );
  }

  return (
    <div className="privacy-dashboard">
      <div className="privacy-header">
        <h1>Privacy & Data Control</h1>
        <p>Manage your privacy settings and data preferences</p>
      </div>

      <div className="privacy-tabs">
        <button
          className={activeTab === "overview" ? "active" : ""}
          onClick={() => setActiveTab("overview")}
        >
          Overview
        </button>
        <button
          className={activeTab === "consent" ? "active" : ""}
          onClick={() => setActiveTab("consent")}
        >
          Consent Management
        </button>
        <button
          className={activeTab === "rights" ? "active" : ""}
          onClick={() => setActiveTab("rights")}
        >
          Your Rights
        </button>
        <button
          className={activeTab === "settings" ? "active" : ""}
          onClick={() => setActiveTab("settings")}
        >
          Privacy Settings
        </button>
      </div>

      <div className="privacy-content">
        {activeTab === "overview" && (
          <div className="privacy-overview">
            <div className="privacy-card">
              <h3>Data Protection Status</h3>
              <div className="status-grid">
                <div className="status-item">
                  <span className="status-label">GDPR Compliance</span>
                  <span className="status-value enabled">✓ Enabled</span>
                </div>
                <div className="status-item">
                  <span className="status-label">Data Encryption</span>
                  <span className="status-value enabled">✓ Active</span>
                </div>
                <div className="status-item">
                  <span className="status-label">Privacy Dashboard</span>
                  <span className="status-value enabled">✓ Available</span>
                </div>
              </div>
            </div>

            <div className="privacy-card">
              <h3>Your GDPR Rights</h3>
              <div className="rights-list">
                <div className="right-item">
                  <strong>Right to Access:</strong> View all data we have about
                  you
                </div>
                <div className="right-item">
                  <strong>Right to Portability:</strong> Export your data in a
                  standard format
                </div>
                <div className="right-item">
                  <strong>Right to Erasure:</strong> Request deletion of your
                  personal data
                </div>
                <div className="right-item">
                  <strong>Right to Rectification:</strong> Correct inaccurate
                  personal data
                </div>
                <div className="right-item">
                  <strong>Right to Object:</strong> Object to processing of your
                  data
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "consent" && (
          <div className="consent-management">
            <div className="privacy-card">
              <h3>Consent Status</h3>
              <div className="consent-list">
                {privacyData?.consent_status &&
                  Object.entries(privacyData.consent_status).map(
                    ([type, granted]) => (
                      <div key={type} className="consent-item">
                        <div className="consent-info">
                          <h4>{formatConsentType(type)}</h4>
                          <p>{getConsentDescription(type)}</p>
                        </div>
                        <div className="consent-controls">
                          <span
                            className={`consent-status ${
                              granted ? "granted" : "denied"
                            }`}
                          >
                            {granted ? "Granted" : "Not Granted"}
                          </span>
                          <button
                            className={`consent-button ${
                              granted ? "withdraw" : "grant"
                            }`}
                            onClick={() =>
                              handleConsentChange(
                                type,
                                granted ? "withdraw" : "grant"
                              )
                            }
                          >
                            {granted ? "Withdraw" : "Grant"}
                          </button>
                        </div>
                      </div>
                    )
                  )}
              </div>
            </div>
          </div>
        )}

        {activeTab === "rights" && (
          <div className="gdpr-rights">
            <div className="privacy-card">
              <h3>Exercise Your Rights</h3>

              <div className="right-action">
                <h4>Data Export (Right to Portability)</h4>
                <p>
                  Download all your personal data in a machine-readable format.
                </p>
                <button
                  className="action-button export"
                  onClick={requestDataExport}
                >
                  Request Data Export
                </button>
              </div>

              <div className="right-action">
                <h4>Data Deletion (Right to Erasure)</h4>
                <p>
                  Request permanent deletion of your personal data. This action
                  cannot be undone.
                </p>
                <button
                  className="action-button delete"
                  onClick={requestDataDeletion}
                >
                  Request Data Deletion
                </button>
              </div>

              <div className="right-action">
                <h4>Data Correction (Right to Rectification)</h4>
                <p>
                  Update or correct your personal information in your profile
                  settings.
                </p>
                <button
                  className="action-button update"
                  onClick={() => (window.location.href = "/profile")}
                >
                  Update Profile
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === "settings" && (
          <div className="privacy-settings">
            <div className="privacy-card">
              <h3>Privacy Preferences</h3>
              {privacyData?.privacy_settings ? (
                <PrivacySettingsForm
                  settings={privacyData.privacy_settings}
                  onUpdate={fetchPrivacyDashboard}
                />
              ) : (
                <p>Loading privacy settings...</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const PrivacySettingsForm = ({ settings, onUpdate }) => {
  const [formData, setFormData] = useState(settings);
  const [saving, setSaving] = useState(false);

  const handleChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);

    try {
      const response = await fetch("/api/v1/privacy/settings", {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error("Failed to update privacy settings");
      }

      await onUpdate();
      alert("Privacy settings updated successfully");
    } catch (err) {
      alert(`Error updating settings: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="privacy-settings-form">
      <div className="setting-group">
        <h4>Data Collection</h4>

        <label className="setting-item">
          <input
            type="checkbox"
            checked={formData.allow_research_participation || false}
            onChange={(e) =>
              handleChange("allow_research_participation", e.target.checked)
            }
          />
          <span>Allow participation in research studies</span>
        </label>

        <label className="setting-item">
          <input
            type="checkbox"
            checked={formData.allow_analytics_tracking || false}
            onChange={(e) =>
              handleChange("allow_analytics_tracking", e.target.checked)
            }
          />
          <span>Allow analytics and usage tracking</span>
        </label>

        <label className="setting-item">
          <input
            type="checkbox"
            checked={formData.allow_performance_tracking || false}
            onChange={(e) =>
              handleChange("allow_performance_tracking", e.target.checked)
            }
          />
          <span>Allow performance and learning progress tracking</span>
        </label>
      </div>

      <div className="setting-group">
        <h4>Social Features</h4>

        <label className="setting-item">
          <input
            type="checkbox"
            checked={formData.allow_social_features || false}
            onChange={(e) =>
              handleChange("allow_social_features", e.target.checked)
            }
          />
          <span>Enable social learning features</span>
        </label>

        <label className="setting-item">
          <input
            type="checkbox"
            checked={formData.allow_third_party_sharing || false}
            onChange={(e) =>
              handleChange("allow_third_party_sharing", e.target.checked)
            }
          />
          <span>Allow sharing data with educational partners</span>
        </label>
      </div>

      <div className="setting-group">
        <h4>Communications</h4>

        <label className="setting-item">
          <input
            type="checkbox"
            checked={formData.allow_marketing_communications || false}
            onChange={(e) =>
              handleChange("allow_marketing_communications", e.target.checked)
            }
          />
          <span>Receive marketing communications</span>
        </label>

        <label className="setting-item">
          <input
            type="checkbox"
            checked={formData.privacy_notification_email || false}
            onChange={(e) =>
              handleChange("privacy_notification_email", e.target.checked)
            }
          />
          <span>Receive privacy-related notifications</span>
        </label>
      </div>

      <div className="setting-group">
        <h4>Data Retention</h4>

        <label className="setting-item">
          <span>Data retention preference:</span>
          <select
            value={formData.data_retention_preference || "one_year"}
            onChange={(e) =>
              handleChange("data_retention_preference", e.target.value)
            }
          >
            <option value="thirty_days">30 Days</option>
            <option value="one_year">1 Year</option>
            <option value="seven_years">7 Years</option>
          </select>
        </label>

        <label className="setting-item">
          <input
            type="checkbox"
            checked={formData.auto_delete_inactive_data || false}
            onChange={(e) =>
              handleChange("auto_delete_inactive_data", e.target.checked)
            }
          />
          <span>Automatically delete inactive data</span>
        </label>
      </div>

      <button type="submit" className="save-button" disabled={saving}>
        {saving ? "Saving..." : "Save Privacy Settings"}
      </button>
    </form>
  );
};

// Helper functions
const formatConsentType = (type) => {
  const formats = {
    research_participation: "Research Participation",
    data_analytics: "Data Analytics",
    marketing_communications: "Marketing Communications",
    third_party_sharing: "Third-Party Sharing",
    performance_tracking: "Performance Tracking",
    social_features: "Social Features",
  };
  return (
    formats[type] ||
    type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())
  );
};

const getConsentDescription = (type) => {
  const descriptions = {
    research_participation:
      "Allow your anonymized data to be used for ASL learning research",
    data_analytics:
      "Enable collection of usage analytics to improve the platform",
    marketing_communications: "Receive emails about new features and updates",
    third_party_sharing:
      "Share data with educational partners and integrations",
    performance_tracking:
      "Track your learning progress and performance metrics",
    social_features: "Enable social learning features and peer interactions",
  };
  return descriptions[type] || "Manage this data processing consent";
};

export default PrivacyDashboard;
