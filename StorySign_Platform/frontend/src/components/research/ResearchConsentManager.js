/**
 * Research Consent Manager Component
 * Handles user consent for research participation, data sharing, and privacy preferences
 */

import React, { useState, useEffect } from "react";
import "./ResearchConsentManager.css";

const ResearchConsentManager = ({
  userId,
  onConsentUpdate,
  initialConsents = [],
  researchStudies = [],
}) => {
  const [consents, setConsents] = useState(initialConsents);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showConsentModal, setShowConsentModal] = useState(false);
  const [selectedStudy, setSelectedStudy] = useState(null);

  // Available consent types
  const consentTypes = [
    {
      id: "general_research",
      name: "General Research",
      description:
        "Allow your anonymized learning data to be used for research to improve ASL education methods.",
      required: false,
    },
    {
      id: "learning_analytics",
      name: "Learning Analytics",
      description:
        "Share your practice session data and progress metrics for educational research.",
      required: false,
    },
    {
      id: "gesture_analysis",
      name: "Gesture Analysis",
      description:
        "Allow analysis of your sign language gestures to improve recognition algorithms.",
      required: false,
    },
    {
      id: "performance_tracking",
      name: "Performance Tracking",
      description:
        "Share your performance metrics and improvement patterns for longitudinal studies.",
      required: false,
    },
    {
      id: "demographic_data",
      name: "Demographic Data",
      description:
        "Include basic demographic information (age range, experience level) in research datasets.",
      required: false,
    },
    {
      id: "video_data",
      name: "Video Analysis Data",
      description:
        "Allow processed video analysis data (not actual video) to be used for research.",
      required: false,
    },
  ];

  // Anonymization levels
  const anonymizationLevels = [
    {
      id: "pseudonymized",
      name: "Pseudonymized",
      description:
        "Your data is linked to a research ID but cannot be traced back to you personally.",
    },
    {
      id: "anonymized",
      name: "Fully Anonymous",
      description: "All identifying information is removed from your data.",
    },
    {
      id: "aggregated",
      name: "Aggregated Only",
      description:
        "Only statistical summaries of your data are included in research.",
    },
  ];

  useEffect(() => {
    loadUserConsents();
  }, [userId]);

  const loadUserConsents = async () => {
    try {
      setLoading(true);
      // In a real implementation, this would fetch from the API
      // const response = await fetch(`/api/research/participants/me`);
      // const data = await response.json();
      // setConsents(data.consents || []);

      // Mock data for now
      setConsents(initialConsents);
    } catch (err) {
      setError("Failed to load consent preferences");
      console.error("Error loading consents:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleConsentChange = async (consentType, granted, studyId = null) => {
    try {
      setLoading(true);

      // In a real implementation, this would call the API
      // const response = await fetch('/api/research/participants/consent', {
      //   method: 'PUT',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({
      //     research_id: studyId || 'general',
      //     consent_type: consentType,
      //     consent_given: granted,
      //     consent_version: '1.0'
      //   })
      // });

      // Mock successful response
      const updatedConsents = consents.map((consent) =>
        consent.type === consentType && consent.studyId === studyId
          ? { ...consent, granted, updatedAt: new Date().toISOString() }
          : consent
      );

      // If consent doesn't exist, add it
      if (
        !updatedConsents.find(
          (c) => c.type === consentType && c.studyId === studyId
        )
      ) {
        updatedConsents.push({
          id: `${consentType}_${studyId || "general"}`,
          type: consentType,
          studyId: studyId || "general",
          granted,
          grantedAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          version: "1.0",
        });
      }

      setConsents(updatedConsents);

      if (onConsentUpdate) {
        onConsentUpdate(consentType, granted, studyId);
      }
    } catch (err) {
      setError("Failed to update consent preferences");
      console.error("Error updating consent:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleJoinStudy = async (studyId, consentData) => {
    try {
      setLoading(true);

      // In a real implementation, this would call the API
      // const response = await fetch('/api/research/participants/register', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({
      //     research_id: studyId,
      //     consent_version: '1.0',
      //     anonymization_level: consentData.anonymizationLevel,
      //     data_retention_years: consentData.retentionYears,
      //     allow_data_sharing: consentData.allowSharing
      //   })
      // });

      // Mock successful registration
      console.log("Joining study:", studyId, consentData);

      // Add consents for this study
      for (const consentType of consentData.consentTypes) {
        await handleConsentChange(consentType, true, studyId);
      }

      setShowConsentModal(false);
      setSelectedStudy(null);
    } catch (err) {
      setError("Failed to join research study");
      console.error("Error joining study:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleWithdrawFromStudy = async (studyId, reason = "") => {
    try {
      setLoading(true);

      // In a real implementation, this would call the API
      // const response = await fetch('/api/research/participants/withdraw', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({
      //     research_id: studyId,
      //     reason: reason
      //   })
      // });

      // Remove all consents for this study
      const updatedConsents = consents.filter(
        (consent) => consent.studyId !== studyId
      );
      setConsents(updatedConsents);

      console.log("Withdrew from study:", studyId, reason);
    } catch (err) {
      setError("Failed to withdraw from research study");
      console.error("Error withdrawing from study:", err);
    } finally {
      setLoading(false);
    }
  };

  const getConsentStatus = (consentType, studyId = "general") => {
    const consent = consents.find(
      (c) => c.type === consentType && c.studyId === studyId
    );
    return consent ? consent.granted : false;
  };

  const isParticipatingInStudy = (studyId) => {
    return consents.some(
      (consent) => consent.studyId === studyId && consent.granted
    );
  };

  if (loading && consents.length === 0) {
    return (
      <div className="research-consent-manager loading">
        <div className="loading-spinner"></div>
        <p>Loading consent preferences...</p>
      </div>
    );
  }

  return (
    <div className="research-consent-manager">
      <div className="consent-header">
        <h2>Research Participation & Privacy</h2>
        <p>
          Help improve ASL education by participating in research studies. You
          have full control over what data you share and how it's used.
        </p>
      </div>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          {error}
          <button onClick={() => setError(null)} className="error-close">
            ×
          </button>
        </div>
      )}

      {/* General Research Consents */}
      <div className="consent-section">
        <h3>General Research Participation</h3>
        <p>
          These settings apply to general research and platform improvement.
        </p>

        <div className="consent-grid">
          {consentTypes.map((consentType) => (
            <div key={consentType.id} className="consent-item">
              <div className="consent-header">
                <label className="consent-toggle">
                  <input
                    type="checkbox"
                    checked={getConsentStatus(consentType.id)}
                    onChange={(e) =>
                      handleConsentChange(consentType.id, e.target.checked)
                    }
                    disabled={loading}
                  />
                  <span className="toggle-slider"></span>
                  <span className="consent-name">{consentType.name}</span>
                </label>
              </div>
              <p className="consent-description">{consentType.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Research Studies */}
      <div className="consent-section">
        <h3>Research Studies</h3>
        <p>
          Join specific research studies to contribute to ASL education
          research.
        </p>

        {researchStudies.length === 0 ? (
          <div className="no-studies">
            <p>No research studies are currently available.</p>
          </div>
        ) : (
          <div className="studies-grid">
            {researchStudies.map((study) => (
              <div key={study.id} className="study-card">
                <div className="study-header">
                  <h4>{study.name}</h4>
                  <span
                    className={`study-status ${
                      isParticipatingInStudy(study.id)
                        ? "participating"
                        : "available"
                    }`}
                  >
                    {isParticipatingInStudy(study.id)
                      ? "Participating"
                      : "Available"}
                  </span>
                </div>
                <p className="study-description">{study.description}</p>
                <div className="study-details">
                  <span className="study-duration">
                    Duration: {study.duration}
                  </span>
                  <span className="study-participants">
                    Participants: {study.participantCount}
                  </span>
                </div>
                <div className="study-actions">
                  {isParticipatingInStudy(study.id) ? (
                    <button
                      onClick={() => handleWithdrawFromStudy(study.id)}
                      className="btn btn-secondary"
                      disabled={loading}
                    >
                      Withdraw
                    </button>
                  ) : (
                    <button
                      onClick={() => {
                        setSelectedStudy(study);
                        setShowConsentModal(true);
                      }}
                      className="btn btn-primary"
                      disabled={loading}
                    >
                      Join Study
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Data Export & Deletion */}
      <div className="consent-section">
        <h3>Data Rights</h3>
        <p>Manage your research data and exercise your privacy rights.</p>

        <div className="data-rights-actions">
          <button className="btn btn-outline">Export My Research Data</button>
          <button className="btn btn-outline">View Data Usage Report</button>
          <button className="btn btn-danger-outline">
            Delete All Research Data
          </button>
        </div>
      </div>

      {/* Study Consent Modal */}
      {showConsentModal && selectedStudy && (
        <StudyConsentModal
          study={selectedStudy}
          consentTypes={consentTypes}
          anonymizationLevels={anonymizationLevels}
          onJoin={handleJoinStudy}
          onCancel={() => {
            setShowConsentModal(false);
            setSelectedStudy(null);
          }}
        />
      )}
    </div>
  );
};

// Study Consent Modal Component
const StudyConsentModal = ({
  study,
  consentTypes,
  anonymizationLevels,
  onJoin,
  onCancel,
}) => {
  const [selectedConsents, setSelectedConsents] = useState([]);
  const [anonymizationLevel, setAnonymizationLevel] = useState("pseudonymized");
  const [retentionYears, setRetentionYears] = useState(5);
  const [allowSharing, setAllowSharing] = useState(false);
  const [hasReadTerms, setHasReadTerms] = useState(false);

  const handleConsentToggle = (consentId) => {
    setSelectedConsents((prev) =>
      prev.includes(consentId)
        ? prev.filter((id) => id !== consentId)
        : [...prev, consentId]
    );
  };

  const handleJoin = () => {
    if (!hasReadTerms || selectedConsents.length === 0) {
      return;
    }

    onJoin(study.id, {
      consentTypes: selectedConsents,
      anonymizationLevel,
      retentionYears,
      allowSharing,
    });
  };

  return (
    <div className="modal-overlay">
      <div className="study-consent-modal">
        <div className="modal-header">
          <h3>Join Research Study: {study.name}</h3>
          <button onClick={onCancel} className="modal-close">
            ×
          </button>
        </div>

        <div className="modal-content">
          <div className="study-info">
            <p>{study.description}</p>
            <div className="study-requirements">
              <h4>Study Requirements:</h4>
              <ul>
                {study.requirements?.map((req, index) => (
                  <li key={index}>{req}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="consent-selection">
            <h4>Data Sharing Permissions</h4>
            <p>
              Select what types of data you're willing to share for this study:
            </p>

            {consentTypes.map((consentType) => (
              <label key={consentType.id} className="consent-checkbox">
                <input
                  type="checkbox"
                  checked={selectedConsents.includes(consentType.id)}
                  onChange={() => handleConsentToggle(consentType.id)}
                />
                <span className="consent-name">{consentType.name}</span>
                <span className="consent-description">
                  {consentType.description}
                </span>
              </label>
            ))}
          </div>

          <div className="privacy-settings">
            <h4>Privacy Settings</h4>

            <div className="setting-group">
              <label>Data Anonymization Level:</label>
              <select
                value={anonymizationLevel}
                onChange={(e) => setAnonymizationLevel(e.target.value)}
              >
                {anonymizationLevels.map((level) => (
                  <option key={level.id} value={level.id}>
                    {level.name} - {level.description}
                  </option>
                ))}
              </select>
            </div>

            <div className="setting-group">
              <label>Data Retention Period:</label>
              <select
                value={retentionYears}
                onChange={(e) => setRetentionYears(parseInt(e.target.value))}
              >
                <option value={3}>3 years</option>
                <option value={5}>5 years</option>
                <option value={7}>7 years</option>
                <option value={10}>10 years</option>
              </select>
            </div>

            <label className="setting-checkbox">
              <input
                type="checkbox"
                checked={allowSharing}
                onChange={(e) => setAllowSharing(e.target.checked)}
              />
              Allow sharing anonymized data with other research institutions
            </label>
          </div>

          <div className="terms-agreement">
            <label className="terms-checkbox">
              <input
                type="checkbox"
                checked={hasReadTerms}
                onChange={(e) => setHasReadTerms(e.target.checked)}
              />
              I have read and agree to the research study terms and conditions
            </label>
          </div>
        </div>

        <div className="modal-actions">
          <button onClick={onCancel} className="btn btn-secondary">
            Cancel
          </button>
          <button
            onClick={handleJoin}
            className="btn btn-primary"
            disabled={!hasReadTerms || selectedConsents.length === 0}
          >
            Join Study
          </button>
        </div>
      </div>
    </div>
  );
};

export default ResearchConsentManager;
