import React, { useState, useEffect } from "react";

const SecurityMonitorTab = ({ plugins, securityReports, onViewDetails }) => {
  const [sortBy, setSortBy] = useState("risk");
  const [filterRisk, setFilterRisk] = useState("all");
  const [systemStats, setSystemStats] = useState({
    totalPlugins: 0,
    activePlugins: 0,
    securityIssues: 0,
    resourceUsage: { cpu: 0, memory: 0, network: 0 },
  });

  useEffect(() => {
    calculateSystemStats();
  }, [plugins, securityReports]);

  const calculateSystemStats = () => {
    const activePlugins = plugins.filter((p) => p.status === "active");
    const totalIssues = Object.values(securityReports).reduce(
      (sum, report) => sum + (report?.violations?.length || 0),
      0
    );

    const totalResourceUsage = Object.values(securityReports).reduce(
      (acc, report) => {
        if (report?.resource_usage) {
          acc.cpu += report.resource_usage.cpu || 0;
          acc.memory += report.resource_usage.memory || 0;
          acc.network += report.resource_usage.network || 0;
        }
        return acc;
      },
      { cpu: 0, memory: 0, network: 0 }
    );

    setSystemStats({
      totalPlugins: plugins.length,
      activePlugins: activePlugins.length,
      securityIssues: totalIssues,
      resourceUsage: totalResourceUsage,
    });
  };

  const getPluginsWithSecurity = () => {
    return plugins
      .map((plugin) => ({
        ...plugin,
        securityReport: securityReports[plugin.id] || {
          risk_level: "unknown",
          violations: [],
          resource_usage: { cpu: 0, memory: 0, network: 0 },
          last_scan: null,
        },
      }))
      .filter((plugin) => {
        if (filterRisk === "all") return true;
        return plugin.securityReport.risk_level === filterRisk;
      })
      .sort((a, b) => {
        switch (sortBy) {
          case "risk":
            const riskOrder = { high: 3, medium: 2, low: 1, unknown: 0 };
            return (
              riskOrder[b.securityReport.risk_level] -
              riskOrder[a.securityReport.risk_level]
            );
          case "violations":
            return (
              b.securityReport.violations.length -
              a.securityReport.violations.length
            );
          case "cpu":
            return (
              (b.securityReport.resource_usage.cpu || 0) -
              (a.securityReport.resource_usage.cpu || 0)
            );
          case "memory":
            return (
              (b.securityReport.resource_usage.memory || 0) -
              (a.securityReport.resource_usage.memory || 0)
            );
          case "name":
            return a.name.localeCompare(b.name);
          default:
            return 0;
        }
      });
  };

  const getRiskLevelColor = (riskLevel) => {
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

  const getRiskLevelIcon = (riskLevel) => {
    switch (riskLevel) {
      case "high":
        return "🔴";
      case "medium":
        return "🟡";
      case "low":
        return "🟢";
      default:
        return "⚪";
    }
  };

  const getResourceUsageColor = (usage, type) => {
    const thresholds = {
      cpu: { high: 80, medium: 50 },
      memory: { high: 100, medium: 60 },
      network: { high: 70, medium: 40 },
    };

    const threshold = thresholds[type];
    if (usage >= threshold.high) return "usage-high";
    if (usage >= threshold.medium) return "usage-medium";
    return "usage-low";
  };

  const pluginsWithSecurity = getPluginsWithSecurity();

  return (
    <div className="security-monitor-tab">
      {/* System Overview */}
      <div className="security-overview">
        <h3>Security Overview</h3>
        <div className="overview-stats">
          <div className="stat-card">
            <div className="stat-icon">📦</div>
            <div className="stat-content">
              <div className="stat-number">{systemStats.totalPlugins}</div>
              <div className="stat-label">Total Plugins</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">✅</div>
            <div className="stat-content">
              <div className="stat-number">{systemStats.activePlugins}</div>
              <div className="stat-label">Active Plugins</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">⚠️</div>
            <div className="stat-content">
              <div className="stat-number">{systemStats.securityIssues}</div>
              <div className="stat-label">Security Issues</div>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">💻</div>
            <div className="stat-content">
              <div className="stat-number">
                {Math.round(systemStats.resourceUsage.cpu)}%
              </div>
              <div className="stat-label">Total CPU Usage</div>
            </div>
          </div>
        </div>

        {/* Resource Usage Chart */}
        <div className="resource-usage-chart">
          <h4>System Resource Usage</h4>
          <div className="usage-bars">
            <div className="usage-item">
              <span className="usage-label">CPU Usage</span>
              <div className="usage-bar">
                <div
                  className={`usage-fill ${getResourceUsageColor(
                    systemStats.resourceUsage.cpu,
                    "cpu"
                  )}`}
                  style={{
                    width: `${Math.min(systemStats.resourceUsage.cpu, 100)}%`,
                  }}
                ></div>
              </div>
              <span className="usage-value">
                {Math.round(systemStats.resourceUsage.cpu)}%
              </span>
            </div>

            <div className="usage-item">
              <span className="usage-label">Memory Usage</span>
              <div className="usage-bar">
                <div
                  className={`usage-fill ${getResourceUsageColor(
                    systemStats.resourceUsage.memory,
                    "memory"
                  )}`}
                  style={{
                    width: `${Math.min(
                      systemStats.resourceUsage.memory / 2,
                      100
                    )}%`,
                  }}
                ></div>
              </div>
              <span className="usage-value">
                {Math.round(systemStats.resourceUsage.memory)}MB
              </span>
            </div>

            <div className="usage-item">
              <span className="usage-label">Network Usage</span>
              <div className="usage-bar">
                <div
                  className={`usage-fill ${getResourceUsageColor(
                    systemStats.resourceUsage.network,
                    "network"
                  )}`}
                  style={{
                    width: `${Math.min(
                      systemStats.resourceUsage.network,
                      100
                    )}%`,
                  }}
                ></div>
              </div>
              <span className="usage-value">
                {Math.round(systemStats.resourceUsage.network)}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="security-controls">
        <div className="filter-controls">
          <div className="filter-group">
            <label htmlFor="risk-filter">Risk Level:</label>
            <select
              id="risk-filter"
              value={filterRisk}
              onChange={(e) => setFilterRisk(e.target.value)}
              className="filter-select"
            >
              <option value="all">All Levels</option>
              <option value="high">High Risk</option>
              <option value="medium">Medium Risk</option>
              <option value="low">Low Risk</option>
              <option value="unknown">Unknown</option>
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="sort-select">Sort by:</label>
            <select
              id="sort-select"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="filter-select"
            >
              <option value="risk">Risk Level</option>
              <option value="violations">Violations</option>
              <option value="cpu">CPU Usage</option>
              <option value="memory">Memory Usage</option>
              <option value="name">Name</option>
            </select>
          </div>
        </div>
      </div>

      {/* Plugin Security List */}
      <div className="security-plugins-list">
        {pluginsWithSecurity.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🔒</div>
            <h3>No plugins match the current filter</h3>
            <p>Try adjusting your filter settings to see more plugins.</p>
          </div>
        ) : (
          <div className="security-table">
            <div className="table-header">
              <div className="header-cell">Plugin</div>
              <div className="header-cell">Risk Level</div>
              <div className="header-cell">Violations</div>
              <div className="header-cell">CPU</div>
              <div className="header-cell">Memory</div>
              <div className="header-cell">Network</div>
              <div className="header-cell">Last Scan</div>
              <div className="header-cell">Actions</div>
            </div>

            {pluginsWithSecurity.map((plugin) => {
              const report = plugin.securityReport;

              return (
                <div key={plugin.id} className="table-row">
                  <div className="cell plugin-cell">
                    <div className="plugin-info">
                      <span className="plugin-name">{plugin.name}</span>
                      <span className="plugin-version">v{plugin.version}</span>
                      <span className={`plugin-status status-${plugin.status}`}>
                        {plugin.status}
                      </span>
                    </div>
                  </div>

                  <div className="cell risk-cell">
                    <div
                      className={`risk-indicator ${getRiskLevelColor(
                        report.risk_level
                      )}`}
                    >
                      <span className="risk-icon">
                        {getRiskLevelIcon(report.risk_level)}
                      </span>
                      <span className="risk-text">{report.risk_level}</span>
                    </div>
                  </div>

                  <div className="cell violations-cell">
                    {report.violations.length > 0 ? (
                      <div className="violations-indicator">
                        <span className="violations-count">
                          {report.violations.length}
                        </span>
                        <span className="violations-icon">⚠️</span>
                      </div>
                    ) : (
                      <span className="no-violations">✅</span>
                    )}
                  </div>

                  <div className="cell resource-cell">
                    <div className="resource-indicator">
                      <div
                        className={`resource-bar ${getResourceUsageColor(
                          report.resource_usage.cpu,
                          "cpu"
                        )}`}
                      >
                        <div
                          className="resource-fill"
                          style={{
                            width: `${Math.min(
                              report.resource_usage.cpu,
                              100
                            )}%`,
                          }}
                        ></div>
                      </div>
                      <span className="resource-value">
                        {report.resource_usage.cpu}%
                      </span>
                    </div>
                  </div>

                  <div className="cell resource-cell">
                    <div className="resource-indicator">
                      <div
                        className={`resource-bar ${getResourceUsageColor(
                          report.resource_usage.memory,
                          "memory"
                        )}`}
                      >
                        <div
                          className="resource-fill"
                          style={{
                            width: `${Math.min(
                              report.resource_usage.memory / 2,
                              100
                            )}%`,
                          }}
                        ></div>
                      </div>
                      <span className="resource-value">
                        {report.resource_usage.memory}MB
                      </span>
                    </div>
                  </div>

                  <div className="cell resource-cell">
                    <div className="resource-indicator">
                      <div
                        className={`resource-bar ${getResourceUsageColor(
                          report.resource_usage.network,
                          "network"
                        )}`}
                      >
                        <div
                          className="resource-fill"
                          style={{
                            width: `${Math.min(
                              report.resource_usage.network,
                              100
                            )}%`,
                          }}
                        ></div>
                      </div>
                      <span className="resource-value">
                        {report.resource_usage.network}%
                      </span>
                    </div>
                  </div>

                  <div className="cell scan-cell">
                    {report.last_scan ? (
                      <span className="scan-time">
                        {new Date(report.last_scan).toLocaleDateString()}
                      </span>
                    ) : (
                      <span className="no-scan">Never</span>
                    )}
                  </div>

                  <div className="cell actions-cell">
                    <button
                      className="btn btn-sm btn-info"
                      onClick={() => onViewDetails(plugin)}
                    >
                      Details
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default SecurityMonitorTab;
