/**
 * Consent Manager Component
 * Handles user consent for analytics and privacy compliance (GDPR)
 */

import React, { useState, useEffect } from "react";
import { useAnalyticsConsent } from "../../hooks/useAnalytics";
import "./ConsentManager.css";

const ConsentManager = ({ onConsentChange, showModal = false, onClose }) => {
  const [consents, setConsents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showDetails, setShowDetails] = useState({});
  const [pendingChanges, setPendingChanges] = useState({});

  const {
    manageConsent,
    checkConsent,
    getConsentStatus,
    exportUserData,
    deleteUserData,
  } = useAnalyticsConsent();

  // Consent types and descriptions
  const consentTypes = [
    {
      type: "analytics",
      title: "Analytics & Performance",
      description:
        "Allow collection of usage data to improve the platform and your learning experience.",
      details: [
        "Track your learning progress and performance",
        "Analyze feature usage to improve the platform",
        "Monitor system performance and errors",
        "Generate anonymized usage statistics",
      ],
      required: false,
    },
    {
      type: "research",
      title: "Educational Research",
      description: "Contribute anonymized data to ASL education research.",
      details: [
        "Support research into ASL learning methods",
        "Help improve teaching techniques",
        "Contribute to academic studies (anonymized)",
        "Advance accessibility technology",
      ],
      required: false,
    },
    {
      type: "performance",
      title: "Performance Monitoring",
      description: "Allow monitoring of system performance for optimization.",
      details: [
        "Track video processing performance",
        "Monitor gesture detection accuracy",
        "Optimize real-time feedback systems",
        "Improve system responsiveness",
      ],
      required: false,
    },
    {
      type: "social",
      title: "Social Features",
      description:
        "Enable sharing progress and collaborative learning features.",
      details: [
        "Share progress with learning groups",
        "Enable collaborative practice sessions",
        "Allow peer feedback and interaction",
        "Participate in community features",
      ],
      required: false,
    },
  ];

  useEffect(() => {
    loadConsentStatus();
  }, []);

  const loadConsentStatus = async () => {
    try {
      setLoading(true);
      const status = await getConsentStatus();
      if (status) {
        setConsents(status);

        // Initialize pending changes with current status
        const currentStatus = {};
        status.forEach((consent) => {
          currentStatus[consent.consent_type] = consent.consent_given;
        });
        setPendingChanges(currentStatus);
      }
    } catch (error) {
      console.error("Error loading consent status:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleConsentChange = (consentType, granted) => {
    setPendingChanges((prev) => ({
      ...prev,
      [consentType]: granted,
    }));
  };

  const saveConsents = async () => {
    try {
      setSaving(true);

      // Save each changed consent
      for (const [consentType, granted] of Object.entries(pendingChanges)) {
        const currentConsent = consents.find(
          (c) => c.consent_type === consentType
        );
        const currentStatus = currentConsent
          ? currentConsent.consent_given
          : false;

        if (currentStatus !== granted) {
          await manageConsent(consentType, granted);
        }
      }

      // Reload consent status
      await loadConsentStatus();

      // Notify parent component
      if (onConsentChange) {
        onConsentChange(pendingChanges);
      }

      // Close modal if open
      if (onClose) {
        onClose();
      }
    } catch (error) {
      console.error("Error saving consents:", error);
      alert("Error saving consent preferences. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  const toggleDetails = (consentType) => {
    setShowDetails((prev) => ({
      ...prev,
      [consentType]: !prev[consentType],
    }));
  };

  const handleExportData = async () => {
    try {
      const data = await exportUserData();
      if (data) {
        // Create and download JSON file
        const blob = new Blob([JSON.stringify(data, null, 2)], {
          type: "application/json",
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `storysign-data-export-${
          new Date().toISOString().split("T")[0]
        }.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error("Error exporting data:", error);
      alert("Error exporting data. Please try again.");
    }
  };

  const handleDeleteData = async () => {
    const confirmed = window.confirm(
      "Are you sure you want to delete all your analytics data? This action cannot be undone."
    );

    if (confirmed) {
      try {
        const success = await deleteUserData();
        if (success) {
          alert(
            "Your data deletion request has been submitted. This process may take a few minutes."
          );
          await loadConsentStatus(); // Reload to reflect changes
        } else {
          alert("Error submitting data deletion request. Please try again.");
        }
      } catch (error) {
        console.error("Error deleting data:", error);
        alert("Error deleting data. Please try again.");
      }
    }
  };

  const getCurrentConsentStatus = (consentType) => {
    if (pendingChanges.hasOwnProperty(consentType)) {
      return pendingChanges[consentType];
    }

    const consent = consents.find((c) => c.consent_type === consentType);
    return consent ? consent.consent_given : false;
  };

  const hasChanges = () => {
    return Object.keys(pendingChanges).some((consentType) => {
      const currentConsent = consents.find(
        (c) => c.consent_type === consentType
      );
      const currentStatus = currentConsent
        ? currentConsent.consent_given
        : false;
      return pendingChanges[consentType] !== currentStatus;
    });
  };

  if (loading) {
    return (
      <div className="consent-manager loading">
        <div className="loading-spinner"></div>
        <p>Loading privacy preferences...</p>
      </div>
    );
  }

  const content = (
    <div className="consent-manager">
      <div className="consent-header">
        <h2>Privacy & Consent Settings</h2>
        <p>
          Control how your data is used to improve your learning experience and
          contribute to ASL education research. You can change these settings at
          any time.
        </p>
      </div>

      <div className="consent-types">
        {consentTypes.map((consentType) => (
          <div key={consentType.type} className="consent-item">
            <div className="consent-main">
              <div className="consent-info">
                <h3>{consentType.title}</h3>
                <p>{consentType.description}</p>
                {consentType.required && (
                  <span className="required-badge">Required</span>
                )}
              </div>

              <div className="consent-controls">
                <button
                  className="details-button"
                  onClick={() => toggleDetails(consentType.type)}
                  aria-expanded={showDetails[consentType.type]}
                >
                  {showDetails[consentType.type]
                    ? "Hide Details"
                    : "Show Details"}
                </button>

                <label className="consent-toggle">
                  <input
                    type="checkbox"
                    checked={getCurrentConsentStatus(consentType.type)}
                    onChange={(e) =>
                      handleConsentChange(consentType.type, e.target.checked)
                    }
                    disabled={consentType.required || saving}
                  />
                  <span className="toggle-slider"></span>
                  <span className="toggle-label">
                    {getCurrentConsentStatus(consentType.type)
                      ? "Enabled"
                      : "Disabled"}
                  </span>
                </label>
              </div>
            </div>

            {showDetails[consentType.type] && (
              <div className="consent-details">
                <h4>What this includes:</h4>
                <ul>
                  {consentType.details.map((detail, index) => (
                    <li key={index}>{detail}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="consent-actions">
        <div className="primary-actions">
          <button
            className="save-button"
            onClick={saveConsents}
            disabled={!hasChanges() || saving}
          >
            {saving ? "Saving..." : "Save Preferences"}
          </button>

          {onClose && (
            <button
              className="cancel-button"
              onClick={onClose}
              disabled={saving}
            >
              Cancel
            </button>
          )}
        </div>

        <div className="data-actions">
          <h3>Your Data Rights</h3>
          <p>
            Under GDPR and other privacy laws, you have the right to access and
            delete your data.
          </p>

          <div className="data-buttons">
            <button
              className="export-button"
              onClick={handleExportData}
              disabled={saving}
            >
              Export My Data
            </button>

            <button
              className="delete-button"
              onClick={handleDeleteData}
              disabled={saving}
            >
              Delete My Data
            </button>
          </div>
        </div>
      </div>

      <div className="consent-footer">
        <p>
          <strong>Privacy Notice:</strong> We are committed to protecting your
          privacy. All data collection is optional (except where required for
          core functionality) and you can withdraw consent at any time.
          <a href="/privacy-policy" target="_blank" rel="noopener noreferrer">
            Read our full Privacy Policy
          </a>
        </p>
      </div>
    </div>
  );

  if (showModal) {
    return (
      <div className="consent-modal-overlay">
        <div className="consent-modal">
          <button className="modal-close" onClick={onClose} aria-label="Close">
            ×
          </button>
          {content}
        </div>
      </div>
    );
  }

  return content;
};

export default ConsentManager;
