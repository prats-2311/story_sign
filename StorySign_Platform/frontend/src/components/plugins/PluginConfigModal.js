import React, { useState, useEffect } from "react";

const PluginConfigModal = ({
  plugin,
  config,
  onConfigChange,
  onSave,
  onClose,
}) => {
  const [localConfig, setLocalConfig] = useState(config);
  const [configSchema, setConfigSchema] = useState(null);
  const [validationErrors, setValidationErrors] = useState({});
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    // Load plugin configuration schema
    loadConfigSchema();
  }, [plugin.id]);

  useEffect(() => {
    setLocalConfig(config);
    setHasChanges(false);
  }, [config]);

  const loadConfigSchema = async () => {
    try {
      // Mock configuration schema based on plugin type
      const mockSchemas = {
        "gesture-enhancer": {
          title: "Gesture Enhancer Configuration",
          description: "Configure gesture recognition enhancement settings",
          properties: {
            sensitivity: {
              type: "number",
              title: "Detection Sensitivity",
              description: "Adjust gesture detection sensitivity (0.1 - 1.0)",
              minimum: 0.1,
              maximum: 1.0,
              default: 0.7,
              step: 0.1,
            },
            enableAdvancedFiltering: {
              type: "boolean",
              title: "Advanced Filtering",
              description: "Enable advanced noise filtering algorithms",
              default: true,
            },
            filterStrength: {
              type: "number",
              title: "Filter Strength",
              description: "Strength of noise filtering (1-10)",
              minimum: 1,
              maximum: 10,
              default: 5,
              dependsOn: "enableAdvancedFiltering",
            },
            debugMode: {
              type: "boolean",
              title: "Debug Mode",
              description: "Enable debug logging and visualization",
              default: false,
            },
          },
        },
        "progress-tracker": {
          title: "Progress Tracker Configuration",
          description: "Configure advanced progress tracking settings",
          properties: {
            trackingInterval: {
              type: "number",
              title: "Tracking Interval (seconds)",
              description: "How often to save progress data",
              minimum: 1,
              maximum: 300,
              default: 30,
            },
            enableDetailedAnalytics: {
              type: "boolean",
              title: "Detailed Analytics",
              description: "Collect detailed performance analytics",
              default: true,
            },
            retentionDays: {
              type: "number",
              title: "Data Retention (days)",
              description: "How long to keep detailed analytics data",
              minimum: 7,
              maximum: 365,
              default: 90,
            },
            exportFormat: {
              type: "select",
              title: "Export Format",
              description: "Default format for data exports",
              options: [
                { value: "json", label: "JSON" },
                { value: "csv", label: "CSV" },
                { value: "xlsx", label: "Excel" },
              ],
              default: "json",
            },
            notifications: {
              type: "object",
              title: "Notification Settings",
              properties: {
                milestones: {
                  type: "boolean",
                  title: "Milestone Notifications",
                  default: true,
                },
                weeklyReports: {
                  type: "boolean",
                  title: "Weekly Progress Reports",
                  default: false,
                },
                achievements: {
                  type: "boolean",
                  title: "Achievement Notifications",
                  default: true,
                },
              },
            },
          },
        },
        "social-features": {
          title: "Social Features Configuration",
          description: "Configure social learning and collaboration settings",
          properties: {
            enablePublicProfile: {
              type: "boolean",
              title: "Public Profile",
              description: "Allow other users to view your profile",
              default: false,
            },
            shareProgress: {
              type: "boolean",
              title: "Share Progress",
              description: "Share learning progress with friends",
              default: false,
            },
            allowFriendRequests: {
              type: "boolean",
              title: "Friend Requests",
              description: "Allow other users to send friend requests",
              default: true,
            },
            privacyLevel: {
              type: "select",
              title: "Privacy Level",
              description: "Control what information is shared",
              options: [
                { value: "private", label: "Private (no sharing)" },
                { value: "friends", label: "Friends Only" },
                { value: "public", label: "Public" },
              ],
              default: "friends",
            },
          },
        },
      };

      setConfigSchema(
        mockSchemas[plugin.id] || {
          title: "Plugin Configuration",
          description: "Configure plugin settings",
          properties: {},
        }
      );
    } catch (error) {
      console.error("Failed to load config schema:", error);
    }
  };

  const handleConfigChange = (key, value) => {
    const newConfig = { ...localConfig, [key]: value };
    setLocalConfig(newConfig);
    onConfigChange(newConfig);
    setHasChanges(true);

    // Validate the change
    validateField(key, value);
  };

  const handleNestedConfigChange = (parentKey, childKey, value) => {
    const newConfig = {
      ...localConfig,
      [parentKey]: {
        ...localConfig[parentKey],
        [childKey]: value,
      },
    };
    setLocalConfig(newConfig);
    onConfigChange(newConfig);
    setHasChanges(true);
  };

  const validateField = (key, value) => {
    const property = configSchema?.properties?.[key];
    if (!property) return;

    const errors = { ...validationErrors };

    // Remove existing error for this field
    delete errors[key];

    // Validate based on type and constraints
    if (property.type === "number") {
      if (property.minimum !== undefined && value < property.minimum) {
        errors[key] = `Value must be at least ${property.minimum}`;
      } else if (property.maximum !== undefined && value > property.maximum) {
        errors[key] = `Value must be at most ${property.maximum}`;
      }
    }

    if (
      property.type === "string" &&
      property.minLength &&
      value.length < property.minLength
    ) {
      errors[key] = `Must be at least ${property.minLength} characters`;
    }

    setValidationErrors(errors);
  };

  const handleSave = async () => {
    // Validate all fields before saving
    const errors = {};

    if (configSchema?.properties) {
      Object.entries(configSchema.properties).forEach(([key, property]) => {
        const value = localConfig[key];

        if (property.required && (value === undefined || value === "")) {
          errors[key] = "This field is required";
        }
      });
    }

    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      return;
    }

    try {
      await onSave();
      setHasChanges(false);
    } catch (error) {
      console.error("Failed to save configuration:", error);
    }
  };

  const resetToDefaults = () => {
    if (!configSchema?.properties) return;

    const defaultConfig = {};
    Object.entries(configSchema.properties).forEach(([key, property]) => {
      if (property.default !== undefined) {
        defaultConfig[key] = property.default;
      }
    });

    setLocalConfig(defaultConfig);
    onConfigChange(defaultConfig);
    setHasChanges(true);
    setValidationErrors({});
  };

  const renderConfigField = (key, property) => {
    const value = localConfig[key] ?? property.default;
    const error = validationErrors[key];
    const isDisabled = property.dependsOn && !localConfig[property.dependsOn];

    switch (property.type) {
      case "boolean":
        return (
          <div key={key} className="config-field">
            <label className="config-label">
              <input
                type="checkbox"
                checked={value || false}
                onChange={(e) => handleConfigChange(key, e.target.checked)}
                disabled={isDisabled}
              />
              <span className="checkbox-label">{property.title}</span>
            </label>
            {property.description && (
              <p className="config-description">{property.description}</p>
            )}
            {error && <span className="config-error">{error}</span>}
          </div>
        );

      case "number":
        return (
          <div key={key} className="config-field">
            <label className="config-label">
              {property.title}
              <input
                type="number"
                value={value || ""}
                onChange={(e) =>
                  handleConfigChange(key, parseFloat(e.target.value) || 0)
                }
                min={property.minimum}
                max={property.maximum}
                step={property.step || 1}
                disabled={isDisabled}
                className={error ? "error" : ""}
              />
            </label>
            {property.description && (
              <p className="config-description">{property.description}</p>
            )}
            {error && <span className="config-error">{error}</span>}
          </div>
        );

      case "string":
        return (
          <div key={key} className="config-field">
            <label className="config-label">
              {property.title}
              <input
                type="text"
                value={value || ""}
                onChange={(e) => handleConfigChange(key, e.target.value)}
                disabled={isDisabled}
                className={error ? "error" : ""}
              />
            </label>
            {property.description && (
              <p className="config-description">{property.description}</p>
            )}
            {error && <span className="config-error">{error}</span>}
          </div>
        );

      case "select":
        return (
          <div key={key} className="config-field">
            <label className="config-label">
              {property.title}
              <select
                value={value || ""}
                onChange={(e) => handleConfigChange(key, e.target.value)}
                disabled={isDisabled}
                className={error ? "error" : ""}
              >
                <option value="">Select an option</option>
                {property.options?.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            {property.description && (
              <p className="config-description">{property.description}</p>
            )}
            {error && <span className="config-error">{error}</span>}
          </div>
        );

      case "object":
        return (
          <div key={key} className="config-field config-group">
            <h4 className="config-group-title">{property.title}</h4>
            {property.description && (
              <p className="config-description">{property.description}</p>
            )}
            <div className="config-group-fields">
              {Object.entries(property.properties || {}).map(
                ([childKey, childProperty]) => (
                  <div key={childKey} className="config-field">
                    <label className="config-label">
                      <input
                        type="checkbox"
                        checked={
                          (localConfig[key]?.[childKey] ??
                            childProperty.default) ||
                          false
                        }
                        onChange={(e) =>
                          handleNestedConfigChange(
                            key,
                            childKey,
                            e.target.checked
                          )
                        }
                        disabled={isDisabled}
                      />
                      <span className="checkbox-label">
                        {childProperty.title}
                      </span>
                    </label>
                  </div>
                )
              )}
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  if (!configSchema) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Loading configuration...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content plugin-config-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2>{configSchema.title}</h2>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="modal-body">
          <div className="plugin-info">
            <h3>{plugin.name} Configuration</h3>
            <p className="plugin-description">{plugin.description}</p>
            {configSchema.description && (
              <p className="config-description">{configSchema.description}</p>
            )}
          </div>

          <div className="config-form">
            {Object.entries(configSchema.properties || {}).map(
              ([key, property]) => renderConfigField(key, property)
            )}
          </div>

          {Object.keys(validationErrors).length > 0 && (
            <div className="validation-summary">
              <h4>⚠️ Please fix the following errors:</h4>
              <ul>
                {Object.entries(validationErrors).map(([key, error]) => (
                  <li key={key}>{error}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={resetToDefaults}>
            Reset to Defaults
          </button>
          <button className="btn btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button
            className="btn btn-primary"
            onClick={handleSave}
            disabled={!hasChanges || Object.keys(validationErrors).length > 0}
          >
            Save Configuration
          </button>
        </div>
      </div>
    </div>
  );
};

export default PluginConfigModal;
