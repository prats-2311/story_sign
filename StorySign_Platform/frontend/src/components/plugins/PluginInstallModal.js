import React, { useState } from "react";

const PluginInstallModal = ({ onClose, onInstall }) => {
  const [installMethod, setInstallMethod] = useState("url");
  const [manifestUrl, setManifestUrl] = useState("");
  const [manifestData, setManifestData] = useState("");
  const [pluginFile, setPluginFile] = useState(null);
  const [validationResult, setValidationResult] = useState(null);
  const [isValidating, setIsValidating] = useState(false);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    setPluginFile(file);

    if (file) {
      // Read file for validation
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          // If it's a JSON manifest file
          if (file.name.endsWith(".json")) {
            const manifest = JSON.parse(e.target.result);
            setManifestData(JSON.stringify(manifest, null, 2));
          }
        } catch (error) {
          console.error("Failed to read file:", error);
        }
      };
      reader.readAsText(file);
    }
  };

  const validateManifest = async () => {
    setIsValidating(true);
    setValidationResult(null);

    try {
      let manifest;

      if (installMethod === "manifest") {
        manifest = JSON.parse(manifestData);
      } else if (installMethod === "url") {
        // Simulate fetching manifest from URL
        await new Promise((resolve) => setTimeout(resolve, 1000));
        manifest = {
          id: "example-plugin",
          name: "Example Plugin",
          version: "1.0.0",
          description: "An example plugin for demonstration",
          author: "Plugin Developer",
          permissions: ["read:user_data"],
        };
      } else if (pluginFile) {
        manifest = JSON.parse(manifestData);
      }

      // Validate manifest structure
      const requiredFields = ["id", "name", "version", "description", "author"];
      const missingFields = requiredFields.filter((field) => !manifest[field]);

      if (missingFields.length > 0) {
        throw new Error(`Missing required fields: ${missingFields.join(", ")}`);
      }

      // Simulate security validation
      const response = await fetch("/api/v1/plugins/validate/manifest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(manifest),
      });

      let validationData;
      if (response.ok) {
        const data = await response.json();
        validationData = data.validation;
      } else {
        // Mock validation result
        validationData = {
          valid: true,
          issues: [],
          security_score: 85,
          risk_level: "low",
          permissions_analysis: {
            high_risk: [],
            medium_risk:
              manifest.permissions?.filter((p) =>
                ["database:write", "filesystem:write"].includes(p)
              ) || [],
            low_risk:
              manifest.permissions?.filter((p) =>
                ["read:user_data", "modify:ui"].includes(p)
              ) || [],
          },
        };
      }

      setValidationResult({
        manifest,
        validation: validationData,
        canInstall: validationData.valid && validationData.issues.length === 0,
      });
    } catch (error) {
      setValidationResult({
        error: error.message,
        canInstall: false,
      });
    } finally {
      setIsValidating(false);
    }
  };

  const handleInstall = async () => {
    if (!validationResult?.canInstall) return;

    try {
      await onInstall(validationResult.manifest.id, installMethod);
      onClose();
    } catch (error) {
      console.error("Installation failed:", error);
    }
  };

  const getRiskColor = (riskLevel) => {
    switch (riskLevel) {
      case "high":
        return "risk-high";
      case "medium":
        return "risk-medium";
      case "low":
        return "risk-low";
      default:
        return "risk-unknown";
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content plugin-install-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2>Install Plugin</h2>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="modal-body">
          <div className="install-method-selector">
            <h3>Installation Method</h3>
            <div className="method-options">
              <label className="method-option">
                <input
                  type="radio"
                  value="url"
                  checked={installMethod === "url"}
                  onChange={(e) => setInstallMethod(e.target.value)}
                />
                <span className="method-label">From URL</span>
                <span className="method-description">
                  Install from a manifest URL
                </span>
              </label>

              <label className="method-option">
                <input
                  type="radio"
                  value="file"
                  checked={installMethod === "file"}
                  onChange={(e) => setInstallMethod(e.target.value)}
                />
                <span className="method-label">Upload File</span>
                <span className="method-description">
                  Upload a plugin archive or manifest
                </span>
              </label>

              <label className="method-option">
                <input
                  type="radio"
                  value="manifest"
                  checked={installMethod === "manifest"}
                  onChange={(e) => setInstallMethod(e.target.value)}
                />
                <span className="method-label">Paste Manifest</span>
                <span className="method-description">
                  Paste plugin manifest JSON
                </span>
              </label>
            </div>
          </div>

          <div className="install-input-section">
            {installMethod === "url" && (
              <div className="input-group">
                <label htmlFor="manifest-url">Manifest URL:</label>
                <input
                  id="manifest-url"
                  type="url"
                  value={manifestUrl}
                  onChange={(e) => setManifestUrl(e.target.value)}
                  placeholder="https://example.com/plugin/manifest.json"
                  className="form-input"
                />
              </div>
            )}

            {installMethod === "file" && (
              <div className="input-group">
                <label htmlFor="plugin-file">Plugin File:</label>
                <input
                  id="plugin-file"
                  type="file"
                  accept=".json,.zip,.tar.gz"
                  onChange={handleFileChange}
                  className="form-input"
                />
                {pluginFile && (
                  <div className="file-info">
                    <span className="file-name">{pluginFile.name}</span>
                    <span className="file-size">
                      ({(pluginFile.size / 1024).toFixed(1)} KB)
                    </span>
                  </div>
                )}
              </div>
            )}

            {installMethod === "manifest" && (
              <div className="input-group">
                <label htmlFor="manifest-data">Plugin Manifest (JSON):</label>
                <textarea
                  id="manifest-data"
                  value={manifestData}
                  onChange={(e) => setManifestData(e.target.value)}
                  placeholder="Paste plugin manifest JSON here..."
                  className="form-textarea"
                  rows={10}
                />
              </div>
            )}
          </div>

          <div className="validation-section">
            <button
              className="btn btn-secondary"
              onClick={validateManifest}
              disabled={
                isValidating ||
                (installMethod === "url" && !manifestUrl) ||
                (installMethod === "file" && !pluginFile) ||
                (installMethod === "manifest" && !manifestData)
              }
            >
              {isValidating ? "Validating..." : "Validate Plugin"}
            </button>

            {validationResult && (
              <div className="validation-results">
                {validationResult.error ? (
                  <div className="validation-error">
                    <h4>❌ Validation Failed</h4>
                    <p>{validationResult.error}</p>
                  </div>
                ) : (
                  <div className="validation-success">
                    <h4>✅ Validation Results</h4>

                    <div className="plugin-info">
                      <h5>Plugin Information</h5>
                      <div className="info-grid">
                        <div className="info-item">
                          <span className="label">Name:</span>
                          <span className="value">
                            {validationResult.manifest.name}
                          </span>
                        </div>
                        <div className="info-item">
                          <span className="label">Version:</span>
                          <span className="value">
                            {validationResult.manifest.version}
                          </span>
                        </div>
                        <div className="info-item">
                          <span className="label">Author:</span>
                          <span className="value">
                            {validationResult.manifest.author}
                          </span>
                        </div>
                        <div className="info-item">
                          <span className="label">Description:</span>
                          <span className="value">
                            {validationResult.manifest.description}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="security-analysis">
                      <h5>Security Analysis</h5>
                      <div className="security-score">
                        <span className="score-label">Security Score:</span>
                        <span className="score-value">
                          {validationResult.validation.security_score}/100
                        </span>
                        <span
                          className={`risk-badge ${getRiskColor(
                            validationResult.validation.risk_level
                          )}`}
                        >
                          {validationResult.validation.risk_level} risk
                        </span>
                      </div>

                      {validationResult.validation.permissions_analysis && (
                        <div className="permissions-analysis">
                          <h6>Permissions Analysis</h6>

                          {validationResult.validation.permissions_analysis
                            .high_risk.length > 0 && (
                            <div className="permission-group risk-high">
                              <span className="group-label">
                                🔴 High Risk Permissions:
                              </span>
                              <div className="permission-list">
                                {validationResult.validation.permissions_analysis.high_risk.map(
                                  (perm) => (
                                    <span key={perm} className="permission-tag">
                                      {perm}
                                    </span>
                                  )
                                )}
                              </div>
                            </div>
                          )}

                          {validationResult.validation.permissions_analysis
                            .medium_risk.length > 0 && (
                            <div className="permission-group risk-medium">
                              <span className="group-label">
                                🟡 Medium Risk Permissions:
                              </span>
                              <div className="permission-list">
                                {validationResult.validation.permissions_analysis.medium_risk.map(
                                  (perm) => (
                                    <span key={perm} className="permission-tag">
                                      {perm}
                                    </span>
                                  )
                                )}
                              </div>
                            </div>
                          )}

                          {validationResult.validation.permissions_analysis
                            .low_risk.length > 0 && (
                            <div className="permission-group risk-low">
                              <span className="group-label">
                                🟢 Low Risk Permissions:
                              </span>
                              <div className="permission-list">
                                {validationResult.validation.permissions_analysis.low_risk.map(
                                  (perm) => (
                                    <span key={perm} className="permission-tag">
                                      {perm}
                                    </span>
                                  )
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {validationResult.validation.issues.length > 0 && (
                        <div className="validation-issues">
                          <h6>⚠️ Issues Found</h6>
                          <ul>
                            {validationResult.validation.issues.map(
                              (issue, index) => (
                                <li key={index}>{issue}</li>
                              )
                            )}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button
            className="btn btn-primary"
            onClick={handleInstall}
            disabled={!validationResult?.canInstall}
          >
            Install Plugin
          </button>
        </div>
      </div>
    </div>
  );
};

export default PluginInstallModal;
