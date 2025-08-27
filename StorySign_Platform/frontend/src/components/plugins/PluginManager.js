import React, { useState, useEffect } from "react";
import { usePlatform } from "../shell/PlatformShell";
import InstalledPluginsTab from "./InstalledPluginsTab";
import PluginStoreTab from "./PluginStoreTab";
import SecurityMonitorTab from "./SecurityMonitorTab";
import PluginInstallModal from "./PluginInstallModal";
import PluginConfigModal from "./PluginConfigModal";
import SecurityReportModal from "./SecurityReportModal";
import "./PluginManager.css";

const PluginManager = () => {
  const { addNotification, notificationTypes } = usePlatform();

  // Plugin management state
  const [plugins, setPlugins] = useState([]);
  const [availablePlugins, setAvailablePlugins] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedPlugin, setSelectedPlugin] = useState(null);
  const [activeTab, setActiveTab] = useState("installed");
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");

  // Plugin installation state
  const [installationProgress, setInstallationProgress] = useState({});
  const [showInstallModal, setShowInstallModal] = useState(false);
  const [installSource, setInstallSource] = useState("store");

  // Plugin configuration state
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [configData, setConfigData] = useState({});

  // Security and monitoring state
  const [securityReports, setSecurityReports] = useState({});
  const [showSecurityModal, setShowSecurityModal] = useState(false);

  useEffect(() => {
    loadInstalledPlugins();
    loadAvailablePlugins();
    loadSecurityReports();
  }, []);

  const loadInstalledPlugins = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/v1/plugins/");
      const data = await response.json();

      if (data.status === "success") {
        setPlugins(data.plugins || []);
      } else {
        // Use mock data for development
        setPlugins([
          {
            id: "gesture-enhancer",
            name: "Gesture Enhancer",
            version: "1.0.0",
            description:
              "Enhances gesture recognition with additional algorithms",
            status: "active",
            author: "StorySign Team",
            installed_at: "2024-01-15T10:30:00Z",
            permissions: ["read:user_data", "access:video_stream"],
            error_message: null,
          },
          {
            id: "progress-tracker",
            name: "Advanced Progress Tracker",
            version: "2.1.0",
            description: "Provides detailed progress tracking and analytics",
            status: "active",
            author: "Analytics Inc",
            installed_at: "2024-01-10T14:20:00Z",
            permissions: ["read:user_data", "write:user_data", "database:read"],
            error_message: null,
          },
          {
            id: "social-features",
            name: "Social Learning Features",
            version: "1.5.0",
            description: "Adds social learning and collaboration features",
            status: "disabled",
            author: "Community Dev",
            installed_at: "2024-01-08T09:15:00Z",
            permissions: [
              "read:user_data",
              "write:user_data",
              "network:access",
            ],
            error_message: null,
          },
          {
            id: "broken-plugin",
            name: "Broken Plugin Example",
            version: "0.5.0",
            description: "A plugin with errors for testing",
            status: "error",
            author: "Test Dev",
            installed_at: "2024-01-05T16:45:00Z",
            permissions: ["read:user_data"],
            error_message: "Failed to initialize: Missing required dependency",
          },
        ]);
      }
    } catch (error) {
      console.error("Failed to load installed plugins:", error);
      addNotification(
        "Failed to load installed plugins",
        notificationTypes.ERROR
      );
    } finally {
      setLoading(false);
    }
  };

  const loadAvailablePlugins = async () => {
    try {
      // Mock available plugins from store
      setAvailablePlugins([
        {
          id: "accessibility-helper",
          name: "Accessibility Helper",
          version: "1.2.0",
          description: "Improves accessibility for users with disabilities",
          author: "Accessibility Team",
          category: "Accessibility",
          rating: 4.8,
          downloads: 1250,
          permissions: ["read:user_data", "modify:ui"],
          price: "free",
          screenshots: [],
          installed: false,
        },
        {
          id: "custom-themes",
          name: "Custom Themes",
          version: "1.0.0",
          description: "Allows users to create and share custom themes",
          author: "Design Studio",
          category: "Customization",
          rating: 4.5,
          downloads: 890,
          permissions: ["read:user_data", "write:user_data", "modify:ui"],
          price: "free",
          screenshots: [],
          installed: false,
        },
        {
          id: "ai-tutor",
          name: "AI Tutor Assistant",
          version: "2.0.0",
          description: "Advanced AI-powered tutoring and feedback system",
          author: "AI Learning Corp",
          category: "AI & Learning",
          rating: 4.9,
          downloads: 2100,
          permissions: [
            "read:user_data",
            "write:user_data",
            "access:ai_services",
            "network:access",
          ],
          price: "$9.99/month",
          screenshots: [],
          installed: false,
        },
      ]);
    } catch (error) {
      console.error("Failed to load available plugins:", error);
    }
  };

  const loadSecurityReports = async () => {
    try {
      const response = await fetch("/api/v1/plugins/security/reports");
      const data = await response.json();

      if (data.status === "success") {
        setSecurityReports(data.reports || {});
      } else {
        // Mock security reports
        setSecurityReports({
          "gesture-enhancer": {
            risk_level: "low",
            violations: [],
            resource_usage: { cpu: 15, memory: 45, network: 0 },
            last_scan: "2024-01-15T12:00:00Z",
          },
          "progress-tracker": {
            risk_level: "medium",
            violations: ["excessive_database_queries"],
            resource_usage: { cpu: 25, memory: 78, network: 12 },
            last_scan: "2024-01-15T11:30:00Z",
          },
          "social-features": {
            risk_level: "high",
            violations: [
              "unauthorized_network_access",
              "suspicious_data_collection",
            ],
            resource_usage: { cpu: 45, memory: 120, network: 89 },
            last_scan: "2024-01-15T10:15:00Z",
          },
        });
      }
    } catch (error) {
      console.error("Failed to load security reports:", error);
    }
  };

  const installPlugin = async (pluginId, source = "store") => {
    setInstallationProgress((prev) => ({ ...prev, [pluginId]: 0 }));

    try {
      // Simulate installation progress
      for (let progress = 0; progress <= 100; progress += 10) {
        setInstallationProgress((prev) => ({ ...prev, [pluginId]: progress }));
        await new Promise((resolve) => setTimeout(resolve, 200));
      }

      // Mock installation API call
      const installRequest = {
        manifest_data: availablePlugins.find((p) => p.id === pluginId),
      };

      const response = await fetch("/api/v1/plugins/install", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(installRequest),
      });

      if (response.ok) {
        addNotification(
          `Plugin ${pluginId} installed successfully`,
          notificationTypes.SUCCESS
        );
        await loadInstalledPlugins();
      } else {
        throw new Error("Installation failed");
      }
    } catch (error) {
      console.error("Plugin installation failed:", error);
      addNotification(
        `Failed to install plugin ${pluginId}`,
        notificationTypes.ERROR
      );
    } finally {
      setInstallationProgress((prev) => {
        const newProgress = { ...prev };
        delete newProgress[pluginId];
        return newProgress;
      });
    }
  };

  const uninstallPlugin = async (pluginId) => {
    if (!window.confirm("Are you sure you want to uninstall this plugin?")) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/plugins/${pluginId}`, {
        method: "DELETE",
      });

      if (response.ok) {
        addNotification(
          "Plugin uninstalled successfully",
          notificationTypes.SUCCESS
        );
        await loadInstalledPlugins();
      } else {
        throw new Error("Uninstallation failed");
      }
    } catch (error) {
      console.error("Plugin uninstallation failed:", error);
      addNotification("Failed to uninstall plugin", notificationTypes.ERROR);
    }
  };

  const togglePlugin = async (pluginId, currentStatus) => {
    const newStatus = currentStatus === "active" ? "disabled" : "active";

    try {
      // Mock toggle API call
      setPlugins((prev) =>
        prev.map((p) => (p.id === pluginId ? { ...p, status: newStatus } : p))
      );

      addNotification(
        `Plugin ${newStatus === "active" ? "enabled" : "disabled"}`,
        notificationTypes.SUCCESS
      );
    } catch (error) {
      console.error("Failed to toggle plugin:", error);
      addNotification("Failed to toggle plugin", notificationTypes.ERROR);
    }
  };

  const openPluginConfig = (plugin) => {
    setSelectedPlugin(plugin);
    setConfigData(plugin.config || {});
    setShowConfigModal(true);
  };

  const savePluginConfig = async () => {
    try {
      // Mock save config API call
      addNotification("Plugin configuration saved", notificationTypes.SUCCESS);
      setShowConfigModal(false);
    } catch (error) {
      console.error("Failed to save plugin config:", error);
      addNotification("Failed to save configuration", notificationTypes.ERROR);
    }
  };

  const openSecurityReport = (plugin) => {
    setSelectedPlugin(plugin);
    setShowSecurityModal(true);
  };

  const filteredPlugins = plugins.filter((plugin) => {
    const matchesSearch =
      plugin.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      plugin.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter =
      filterStatus === "all" || plugin.status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  const filteredAvailablePlugins = availablePlugins.filter(
    (plugin) =>
      plugin.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      plugin.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="plugin-manager">
      <div className="plugin-manager-header">
        <h2>Plugin Manager</h2>
        <div className="header-actions">
          <button
            className="btn btn-primary"
            onClick={() => setShowInstallModal(true)}
          >
            Install Plugin
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => loadInstalledPlugins()}
          >
            Refresh
          </button>
        </div>
      </div>

      <div className="plugin-manager-controls">
        <div className="tab-navigation">
          <button
            className={`tab ${activeTab === "installed" ? "active" : ""}`}
            onClick={() => setActiveTab("installed")}
          >
            Installed ({plugins.length})
          </button>
          <button
            className={`tab ${activeTab === "store" ? "active" : ""}`}
            onClick={() => setActiveTab("store")}
          >
            Plugin Store ({availablePlugins.length})
          </button>
          <button
            className={`tab ${activeTab === "security" ? "active" : ""}`}
            onClick={() => setActiveTab("security")}
          >
            Security Monitor
          </button>
        </div>

        <div className="search-and-filter">
          <input
            type="text"
            placeholder="Search plugins..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />

          {activeTab === "installed" && (
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="filter-select"
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="disabled">Disabled</option>
              <option value="error">Error</option>
            </select>
          )}
        </div>
      </div>

      <div className="plugin-manager-content">
        {loading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Loading plugins...</p>
          </div>
        ) : (
          <>
            {activeTab === "installed" && (
              <InstalledPluginsTab
                plugins={filteredPlugins}
                securityReports={securityReports}
                onToggle={togglePlugin}
                onUninstall={uninstallPlugin}
                onConfigure={openPluginConfig}
                onViewSecurity={openSecurityReport}
              />
            )}

            {activeTab === "store" && (
              <PluginStoreTab
                plugins={filteredAvailablePlugins}
                installationProgress={installationProgress}
                onInstall={installPlugin}
              />
            )}

            {activeTab === "security" && (
              <SecurityMonitorTab
                plugins={plugins}
                securityReports={securityReports}
                onViewDetails={openSecurityReport}
              />
            )}
          </>
        )}
      </div>

      {/* Plugin Installation Modal */}
      {showInstallModal && (
        <PluginInstallModal
          onClose={() => setShowInstallModal(false)}
          onInstall={installPlugin}
        />
      )}

      {/* Plugin Configuration Modal */}
      {showConfigModal && selectedPlugin && (
        <PluginConfigModal
          plugin={selectedPlugin}
          config={configData}
          onConfigChange={setConfigData}
          onSave={savePluginConfig}
          onClose={() => setShowConfigModal(false)}
        />
      )}

      {/* Security Report Modal */}
      {showSecurityModal && selectedPlugin && (
        <SecurityReportModal
          plugin={selectedPlugin}
          report={securityReports[selectedPlugin.id]}
          onClose={() => setShowSecurityModal(false)}
        />
      )}
    </div>
  );
};

export default PluginManager;
