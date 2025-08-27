import React from "react";

const InstalledPluginsTab = ({
  plugins,
  securityReports,
  onToggle,
  onUninstall,
  onConfigure,
  onViewSecurity,
}) => {
  const getStatusIcon = (status) => {
    switch (status) {
      case "active":
        return "✅";
      case "disabled":
        return "⏸️";
      case "error":
        return "❌";
      default:
        return "❓";
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "active":
        return "status-active";
      case "disabled":
        return "status-disabled";
      case "error":
        return "status-error";
      default:
        return "status-unknown";
    }
  };

  const getRiskLevelColor = (riskLevel) => {
    switch (riskLevel) {
      case "low":
        return "risk-low";
      case "medium":
        return "risk-medium";
      case "high":
        return "risk-high";
      default:
        return "risk-unknown";
    }
  };

  if (plugins.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📦</div>
        <h3>No plugins installed</h3>
        <p>
          Install plugins from the Plugin Store to extend StorySign's
          functionality.
        </p>
      </div>
    );
  }

  return (
    <div className="installed-plugins-tab">
      <div className="plugins-grid">
        {plugins.map((plugin) => {
          const securityReport = securityReports[plugin.id];

          return (
            <div key={plugin.id} className="plugin-card">
              <div className="plugin-header">
                <div className="plugin-info">
                  <h3 className="plugin-name">{plugin.name}</h3>
                  <p className="plugin-version">v{plugin.version}</p>
                </div>
                <div
                  className={`plugin-status ${getStatusColor(plugin.status)}`}
                >
                  <span className="status-icon">
                    {getStatusIcon(plugin.status)}
                  </span>
                  <span className="status-text">{plugin.status}</span>
                </div>
              </div>

              <div className="plugin-body">
                <p className="plugin-description">{plugin.description}</p>

                <div className="plugin-metadata">
                  <div className="metadata-item">
                    <span className="label">Author:</span>
                    <span className="value">{plugin.author}</span>
                  </div>
                  <div className="metadata-item">
                    <span className="label">Installed:</span>
                    <span className="value">
                      {new Date(plugin.installed_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                {plugin.error_message && (
                  <div className="error-message">
                    <span className="error-icon">⚠️</span>
                    <span className="error-text">{plugin.error_message}</span>
                  </div>
                )}

                <div className="plugin-permissions">
                  <span className="permissions-label">Permissions:</span>
                  <div className="permissions-list">
                    {plugin.permissions.map((permission) => (
                      <span key={permission} className="permission-tag">
                        {permission}
                      </span>
                    ))}
                  </div>
                </div>

                {securityReport && (
                  <div className="security-summary">
                    <div
                      className={`risk-indicator ${getRiskLevelColor(
                        securityReport.risk_level
                      )}`}
                    >
                      <span className="risk-label">Security Risk:</span>
                      <span className="risk-value">
                        {securityReport.risk_level}
                      </span>
                    </div>

                    <div className="resource-usage">
                      <div className="usage-item">
                        <span className="usage-label">CPU:</span>
                        <div className="usage-bar">
                          <div
                            className="usage-fill"
                            style={{
                              width: `${securityReport.resource_usage.cpu}%`,
                            }}
                          ></div>
                        </div>
                        <span className="usage-value">
                          {securityReport.resource_usage.cpu}%
                        </span>
                      </div>

                      <div className="usage-item">
                        <span className="usage-label">Memory:</span>
                        <div className="usage-bar">
                          <div
                            className="usage-fill"
                            style={{
                              width: `${Math.min(
                                securityReport.resource_usage.memory,
                                100
                              )}%`,
                            }}
                          ></div>
                        </div>
                        <span className="usage-value">
                          {securityReport.resource_usage.memory}MB
                        </span>
                      </div>
                    </div>

                    {securityReport.violations.length > 0 && (
                      <div className="security-violations">
                        <span className="violations-count">
                          ⚠️ {securityReport.violations.length} security
                          issue(s)
                        </span>
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="plugin-actions">
                <button
                  className={`btn btn-sm ${
                    plugin.status === "active" ? "btn-warning" : "btn-success"
                  }`}
                  onClick={() => onToggle(plugin.id, plugin.status)}
                  disabled={plugin.status === "error"}
                >
                  {plugin.status === "active" ? "Disable" : "Enable"}
                </button>

                <button
                  className="btn btn-sm btn-secondary"
                  onClick={() => onConfigure(plugin)}
                >
                  Configure
                </button>

                {securityReport && (
                  <button
                    className="btn btn-sm btn-info"
                    onClick={() => onViewSecurity(plugin)}
                  >
                    Security
                  </button>
                )}

                <button
                  className="btn btn-sm btn-danger"
                  onClick={() => onUninstall(plugin.id)}
                >
                  Uninstall
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default InstalledPluginsTab;
