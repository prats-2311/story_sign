import React, { useState, useEffect } from "react";

const SecurityReportModal = ({ plugin, report, onClose }) => {
  const [detailedReport, setDetailedReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    loadDetailedReport();
  }, [plugin.id]);

  const loadDetailedReport = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/plugins/${plugin.id}/security`);

      if (response.ok) {
        const data = await response.json();
        setDetailedReport(data.security_report);
      } else {
        // Mock detailed security report
        setDetailedReport({
          plugin_id: plugin.id,
          plugin_name: plugin.name,
          plugin_version: plugin.version,
          scan_timestamp: new Date().toISOString(),

          risk_assessment: {
            overall_risk: report?.risk_level || "medium",
            risk_score: 75,
            risk_factors: [
              {
                category: "Permissions",
                risk: "medium",
                description: "Plugin requests database write access",
                impact: "Could modify user data",
              },
              {
                category: "Network Access",
                risk: "low",
                description: "Plugin makes external API calls",
                impact: "Limited to approved endpoints",
              },
            ],
          },

          security_violations:
            report?.violations?.map((violation) => ({
              type: violation,
              severity: "medium",
              description: getViolationDescription(violation),
              timestamp: new Date(
                Date.now() - Math.random() * 86400000
              ).toISOString(),
              resolved: false,
            })) || [],

          resource_monitoring: {
            current_usage: report?.resource_usage || {
              cpu: 0,
              memory: 0,
              network: 0,
            },
            historical_usage: generateHistoricalUsage(),
            limits: {
              cpu: 50,
              memory: 100,
              network: 25,
              file_operations: 10,
            },
            violations: [],
          },

          code_analysis: {
            scanned_files: 5,
            lines_of_code: 1250,
            security_issues: [
              {
                type: "potential_data_leak",
                severity: "low",
                file: "main.py",
                line: 45,
                description: "Potential sensitive data in log output",
              },
            ],
            dependencies: [
              { name: "requests", version: "2.28.1", vulnerabilities: 0 },
              { name: "numpy", version: "1.21.0", vulnerabilities: 1 },
            ],
          },

          behavioral_analysis: {
            api_calls: {
              total: 1250,
              suspicious: 2,
              blocked: 0,
            },
            file_access: {
              reads: 45,
              writes: 12,
              unauthorized_attempts: 0,
            },
            network_activity: {
              requests: 89,
              data_sent: "2.5 MB",
              data_received: "1.8 MB",
              blocked_requests: 0,
            },
          },

          compliance_status: {
            privacy_compliant: true,
            security_standards: ["OWASP", "NIST"],
            audit_trail: true,
            data_encryption: true,
          },
        });
      }
    } catch (error) {
      console.error("Failed to load detailed security report:", error);
    } finally {
      setLoading(false);
    }
  };

  const getViolationDescription = (violation) => {
    const descriptions = {
      excessive_database_queries:
        "Plugin is making more database queries than expected",
      unauthorized_network_access:
        "Plugin attempted to access unauthorized network endpoints",
      suspicious_data_collection:
        "Plugin is collecting more user data than declared in permissions",
      resource_limit_exceeded: "Plugin exceeded allocated resource limits",
      malicious_pattern_detected:
        "Code patterns matching known malicious behavior detected",
    };
    return descriptions[violation] || "Unknown security violation";
  };

  const generateHistoricalUsage = () => {
    const hours = 24;
    const data = [];
    for (let i = hours; i >= 0; i--) {
      data.push({
        timestamp: new Date(Date.now() - i * 3600000).toISOString(),
        cpu: Math.random() * 30 + 10,
        memory: Math.random() * 50 + 20,
        network: Math.random() * 20 + 5,
      });
    }
    return data;
  };

  const getRiskColor = (risk) => {
    switch (risk) {
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

  const getSeverityColor = (severity) => {
    switch (severity) {
      case "critical":
        return "severity-critical";
      case "high":
        return "severity-high";
      case "medium":
        return "severity-medium";
      case "low":
        return "severity-low";
      default:
        return "severity-unknown";
    }
  };

  if (loading) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Loading security report...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content security-report-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2>Security Report: {plugin.name}</h2>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="modal-body">
          {/* Plugin Info */}
          <div className="plugin-security-header">
            <div className="plugin-info">
              <h3>
                {plugin.name} v{plugin.version}
              </h3>
              <p>{plugin.description}</p>
              <span className="scan-time">
                Last scanned:{" "}
                {new Date(detailedReport.scan_timestamp).toLocaleString()}
              </span>
            </div>

            <div className="overall-risk">
              <div
                className={`risk-indicator ${getRiskColor(
                  detailedReport.risk_assessment.overall_risk
                )}`}
              >
                <span className="risk-score">
                  {detailedReport.risk_assessment.risk_score}/100
                </span>
                <span className="risk-label">
                  {detailedReport.risk_assessment.overall_risk} risk
                </span>
              </div>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="security-tabs">
            <button
              className={`tab ${activeTab === "overview" ? "active" : ""}`}
              onClick={() => setActiveTab("overview")}
            >
              Overview
            </button>
            <button
              className={`tab ${activeTab === "violations" ? "active" : ""}`}
              onClick={() => setActiveTab("violations")}
            >
              Violations ({detailedReport.security_violations.length})
            </button>
            <button
              className={`tab ${activeTab === "resources" ? "active" : ""}`}
              onClick={() => setActiveTab("resources")}
            >
              Resources
            </button>
            <button
              className={`tab ${activeTab === "code" ? "active" : ""}`}
              onClick={() => setActiveTab("code")}
            >
              Code Analysis
            </button>
            <button
              className={`tab ${activeTab === "behavior" ? "active" : ""}`}
              onClick={() => setActiveTab("behavior")}
            >
              Behavior
            </button>
          </div>

          {/* Tab Content */}
          <div className="security-tab-content">
            {activeTab === "overview" && (
              <div className="overview-tab">
                <div className="risk-factors">
                  <h4>Risk Factors</h4>
                  {detailedReport.risk_assessment.risk_factors.map(
                    (factor, index) => (
                      <div key={index} className="risk-factor">
                        <div className="factor-header">
                          <span className="factor-category">
                            {factor.category}
                          </span>
                          <span
                            className={`factor-risk ${getRiskColor(
                              factor.risk
                            )}`}
                          >
                            {factor.risk}
                          </span>
                        </div>
                        <p className="factor-description">
                          {factor.description}
                        </p>
                        <p className="factor-impact">Impact: {factor.impact}</p>
                      </div>
                    )
                  )}
                </div>

                <div className="compliance-status">
                  <h4>Compliance Status</h4>
                  <div className="compliance-grid">
                    <div className="compliance-item">
                      <span className="compliance-label">
                        Privacy Compliant:
                      </span>
                      <span
                        className={`compliance-value ${
                          detailedReport.compliance_status.privacy_compliant
                            ? "compliant"
                            : "non-compliant"
                        }`}
                      >
                        {detailedReport.compliance_status.privacy_compliant
                          ? "✅ Yes"
                          : "❌ No"}
                      </span>
                    </div>
                    <div className="compliance-item">
                      <span className="compliance-label">
                        Security Standards:
                      </span>
                      <span className="compliance-value">
                        {detailedReport.compliance_status.security_standards.join(
                          ", "
                        )}
                      </span>
                    </div>
                    <div className="compliance-item">
                      <span className="compliance-label">Audit Trail:</span>
                      <span
                        className={`compliance-value ${
                          detailedReport.compliance_status.audit_trail
                            ? "compliant"
                            : "non-compliant"
                        }`}
                      >
                        {detailedReport.compliance_status.audit_trail
                          ? "✅ Enabled"
                          : "❌ Disabled"}
                      </span>
                    </div>
                    <div className="compliance-item">
                      <span className="compliance-label">Data Encryption:</span>
                      <span
                        className={`compliance-value ${
                          detailedReport.compliance_status.data_encryption
                            ? "compliant"
                            : "non-compliant"
                        }`}
                      >
                        {detailedReport.compliance_status.data_encryption
                          ? "✅ Enabled"
                          : "❌ Disabled"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "violations" && (
              <div className="violations-tab">
                {detailedReport.security_violations.length === 0 ? (
                  <div className="no-violations">
                    <div className="no-violations-icon">✅</div>
                    <h4>No Security Violations</h4>
                    <p>
                      This plugin has not triggered any security violations.
                    </p>
                  </div>
                ) : (
                  <div className="violations-list">
                    {detailedReport.security_violations.map(
                      (violation, index) => (
                        <div key={index} className="violation-item">
                          <div className="violation-header">
                            <span className="violation-type">
                              {violation.type.replace(/_/g, " ")}
                            </span>
                            <span
                              className={`violation-severity ${getSeverityColor(
                                violation.severity
                              )}`}
                            >
                              {violation.severity}
                            </span>
                            <span className="violation-time">
                              {new Date(violation.timestamp).toLocaleString()}
                            </span>
                          </div>
                          <p className="violation-description">
                            {violation.description}
                          </p>
                          <div className="violation-status">
                            {violation.resolved ? (
                              <span className="status-resolved">
                                ✅ Resolved
                              </span>
                            ) : (
                              <span className="status-active">⚠️ Active</span>
                            )}
                          </div>
                        </div>
                      )
                    )}
                  </div>
                )}
              </div>
            )}

            {activeTab === "resources" && (
              <div className="resources-tab">
                <div className="current-usage">
                  <h4>Current Resource Usage</h4>
                  <div className="usage-meters">
                    <div className="usage-meter">
                      <span className="meter-label">CPU Usage</span>
                      <div className="meter-bar">
                        <div
                          className="meter-fill"
                          style={{
                            width: `${
                              (detailedReport.resource_monitoring.current_usage
                                .cpu /
                                detailedReport.resource_monitoring.limits.cpu) *
                              100
                            }%`,
                          }}
                        ></div>
                      </div>
                      <span className="meter-value">
                        {detailedReport.resource_monitoring.current_usage.cpu}%
                        / {detailedReport.resource_monitoring.limits.cpu}%
                      </span>
                    </div>

                    <div className="usage-meter">
                      <span className="meter-label">Memory Usage</span>
                      <div className="meter-bar">
                        <div
                          className="meter-fill"
                          style={{
                            width: `${
                              (detailedReport.resource_monitoring.current_usage
                                .memory /
                                detailedReport.resource_monitoring.limits
                                  .memory) *
                              100
                            }%`,
                          }}
                        ></div>
                      </div>
                      <span className="meter-value">
                        {
                          detailedReport.resource_monitoring.current_usage
                            .memory
                        }
                        MB / {detailedReport.resource_monitoring.limits.memory}
                        MB
                      </span>
                    </div>

                    <div className="usage-meter">
                      <span className="meter-label">Network Usage</span>
                      <div className="meter-bar">
                        <div
                          className="meter-fill"
                          style={{
                            width: `${
                              (detailedReport.resource_monitoring.current_usage
                                .network /
                                detailedReport.resource_monitoring.limits
                                  .network) *
                              100
                            }%`,
                          }}
                        ></div>
                      </div>
                      <span className="meter-value">
                        {
                          detailedReport.resource_monitoring.current_usage
                            .network
                        }
                        % / {detailedReport.resource_monitoring.limits.network}%
                      </span>
                    </div>
                  </div>
                </div>

                <div className="usage-history">
                  <h4>24-Hour Usage History</h4>
                  <div className="usage-chart">
                    <div className="chart-placeholder">
                      <p>📊 Resource usage chart would be displayed here</p>
                      <p>
                        Showing CPU, Memory, and Network usage over the last 24
                        hours
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "code" && (
              <div className="code-tab">
                <div className="code-stats">
                  <h4>Code Analysis Summary</h4>
                  <div className="stats-grid">
                    <div className="stat-item">
                      <span className="stat-label">Files Scanned:</span>
                      <span className="stat-value">
                        {detailedReport.code_analysis.scanned_files}
                      </span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Lines of Code:</span>
                      <span className="stat-value">
                        {detailedReport.code_analysis.lines_of_code.toLocaleString()}
                      </span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Security Issues:</span>
                      <span className="stat-value">
                        {detailedReport.code_analysis.security_issues.length}
                      </span>
                    </div>
                  </div>
                </div>

                {detailedReport.code_analysis.security_issues.length > 0 && (
                  <div className="security-issues">
                    <h4>Security Issues</h4>
                    {detailedReport.code_analysis.security_issues.map(
                      (issue, index) => (
                        <div key={index} className="security-issue">
                          <div className="issue-header">
                            <span className="issue-type">
                              {issue.type.replace(/_/g, " ")}
                            </span>
                            <span
                              className={`issue-severity ${getSeverityColor(
                                issue.severity
                              )}`}
                            >
                              {issue.severity}
                            </span>
                          </div>
                          <div className="issue-location">
                            <span className="issue-file">{issue.file}</span>
                            <span className="issue-line">
                              Line {issue.line}
                            </span>
                          </div>
                          <p className="issue-description">
                            {issue.description}
                          </p>
                        </div>
                      )
                    )}
                  </div>
                )}

                <div className="dependencies">
                  <h4>Dependencies</h4>
                  <div className="dependencies-list">
                    {detailedReport.code_analysis.dependencies.map(
                      (dep, index) => (
                        <div key={index} className="dependency-item">
                          <span className="dep-name">{dep.name}</span>
                          <span className="dep-version">v{dep.version}</span>
                          <span
                            className={`dep-vulnerabilities ${
                              dep.vulnerabilities > 0
                                ? "has-vulnerabilities"
                                : "no-vulnerabilities"
                            }`}
                          >
                            {dep.vulnerabilities > 0
                              ? `⚠️ ${dep.vulnerabilities} vulnerabilities`
                              : "✅ No vulnerabilities"}
                          </span>
                        </div>
                      )
                    )}
                  </div>
                </div>
              </div>
            )}

            {activeTab === "behavior" && (
              <div className="behavior-tab">
                <div className="behavior-stats">
                  <h4>Behavioral Analysis</h4>

                  <div className="behavior-section">
                    <h5>API Calls</h5>
                    <div className="behavior-metrics">
                      <div className="metric-item">
                        <span className="metric-label">Total Calls:</span>
                        <span className="metric-value">
                          {detailedReport.behavioral_analysis.api_calls.total.toLocaleString()}
                        </span>
                      </div>
                      <div className="metric-item">
                        <span className="metric-label">Suspicious:</span>
                        <span
                          className={`metric-value ${
                            detailedReport.behavioral_analysis.api_calls
                              .suspicious > 0
                              ? "warning"
                              : "normal"
                          }`}
                        >
                          {
                            detailedReport.behavioral_analysis.api_calls
                              .suspicious
                          }
                        </span>
                      </div>
                      <div className="metric-item">
                        <span className="metric-label">Blocked:</span>
                        <span
                          className={`metric-value ${
                            detailedReport.behavioral_analysis.api_calls
                              .blocked > 0
                              ? "error"
                              : "normal"
                          }`}
                        >
                          {detailedReport.behavioral_analysis.api_calls.blocked}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="behavior-section">
                    <h5>File Access</h5>
                    <div className="behavior-metrics">
                      <div className="metric-item">
                        <span className="metric-label">Reads:</span>
                        <span className="metric-value">
                          {detailedReport.behavioral_analysis.file_access.reads}
                        </span>
                      </div>
                      <div className="metric-item">
                        <span className="metric-label">Writes:</span>
                        <span className="metric-value">
                          {
                            detailedReport.behavioral_analysis.file_access
                              .writes
                          }
                        </span>
                      </div>
                      <div className="metric-item">
                        <span className="metric-label">
                          Unauthorized Attempts:
                        </span>
                        <span
                          className={`metric-value ${
                            detailedReport.behavioral_analysis.file_access
                              .unauthorized_attempts > 0
                              ? "error"
                              : "normal"
                          }`}
                        >
                          {
                            detailedReport.behavioral_analysis.file_access
                              .unauthorized_attempts
                          }
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="behavior-section">
                    <h5>Network Activity</h5>
                    <div className="behavior-metrics">
                      <div className="metric-item">
                        <span className="metric-label">Requests:</span>
                        <span className="metric-value">
                          {
                            detailedReport.behavioral_analysis.network_activity
                              .requests
                          }
                        </span>
                      </div>
                      <div className="metric-item">
                        <span className="metric-label">Data Sent:</span>
                        <span className="metric-value">
                          {
                            detailedReport.behavioral_analysis.network_activity
                              .data_sent
                          }
                        </span>
                      </div>
                      <div className="metric-item">
                        <span className="metric-label">Data Received:</span>
                        <span className="metric-value">
                          {
                            detailedReport.behavioral_analysis.network_activity
                              .data_received
                          }
                        </span>
                      </div>
                      <div className="metric-item">
                        <span className="metric-label">Blocked Requests:</span>
                        <span
                          className={`metric-value ${
                            detailedReport.behavioral_analysis.network_activity
                              .blocked_requests > 0
                              ? "error"
                              : "normal"
                          }`}
                        >
                          {
                            detailedReport.behavioral_analysis.network_activity
                              .blocked_requests
                          }
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
          <button className="btn btn-primary">Export Report</button>
        </div>
      </div>
    </div>
  );
};

export default SecurityReportModal;
