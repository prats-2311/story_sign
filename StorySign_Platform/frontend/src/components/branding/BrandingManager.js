import React, { useState, useEffect } from "react";
import "./BrandingManager.css";

const BrandingManager = () => {
  const [brandingConfig, setBrandingConfig] = useState(null);
  const [themes, setThemes] = useState([]);
  const [featureFlags, setFeatureFlags] = useState([]);
  const [customDomains, setCustomDomains] = useState([]);
  const [activeTab, setActiveTab] = useState("branding");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadBrandingData();
  }, []);

  const loadBrandingData = async () => {
    try {
      setLoading(true);

      // Get current domain's branding config
      const host = window.location.hostname;
      const brandingResponse = await fetch(`/api/v1/branding/domain/${host}`);

      if (brandingResponse.ok) {
        const branding = await brandingResponse.json();
        setBrandingConfig(branding);

        // Load related data
        await Promise.all([
          loadThemes(branding.id),
          loadFeatureFlags(branding.id),
          loadCustomDomains(branding.id),
        ]);
      }
    } catch (err) {
      setError("Failed to load branding configuration");
      console.error("Error loading branding data:", err);
    } finally {
      setLoading(false);
    }
  };

  const loadThemes = async (brandingId) => {
    try {
      const response = await fetch(`/api/v1/themes/branding/${brandingId}`);
      if (response.ok) {
        const themesData = await response.json();
        setThemes(themesData);
      }
    } catch (err) {
      console.error("Error loading themes:", err);
    }
  };

  const loadFeatureFlags = async (brandingId) => {
    try {
      const response = await fetch(
        `/api/v1/feature-flags/branding/${brandingId}`
      );
      if (response.ok) {
        const flagsData = await response.json();
        setFeatureFlags(flagsData);
      }
    } catch (err) {
      console.error("Error loading feature flags:", err);
    }
  };

  const loadCustomDomains = async (brandingId) => {
    try {
      const response = await fetch(
        `/api/v1/custom-domains/branding/${brandingId}`
      );
      if (response.ok) {
        const domainsData = await response.json();
        setCustomDomains(domainsData);
      }
    } catch (err) {
      console.error("Error loading custom domains:", err);
    }
  };

  const updateBrandingConfig = async (updates) => {
    try {
      const response = await fetch(`/api/v1/branding/${brandingConfig.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(updates),
      });

      if (response.ok) {
        setBrandingConfig({ ...brandingConfig, ...updates });
        // Apply changes to CSS variables
        applyBrandingToDOM(updates);
      } else {
        throw new Error("Failed to update branding configuration");
      }
    } catch (err) {
      setError("Failed to update branding configuration");
      console.error("Error updating branding:", err);
    }
  };

  const applyBrandingToDOM = (config) => {
    const root = document.documentElement;

    if (config.primary_color) {
      root.style.setProperty("--primary-color", config.primary_color);
    }
    if (config.secondary_color) {
      root.style.setProperty("--secondary-color", config.secondary_color);
    }
    if (config.accent_color) {
      root.style.setProperty("--accent-color", config.accent_color);
    }
    if (config.background_color) {
      root.style.setProperty("--background-color", config.background_color);
    }
    if (config.font_family) {
      root.style.setProperty("--font-family", config.font_family);
    }
    if (config.font_size_base) {
      root.style.setProperty("--font-size-base", `${config.font_size_base}px`);
    }
  };

  const toggleFeatureFlag = async (flagId) => {
    try {
      const response = await fetch(`/api/v1/feature-flags/${flagId}/toggle`, {
        method: "POST",
      });

      if (response.ok) {
        const updatedFlag = await response.json();
        setFeatureFlags((flags) =>
          flags.map((flag) =>
            flag.id === flagId
              ? { ...flag, is_enabled: updatedFlag.is_enabled }
              : flag
          )
        );
      }
    } catch (err) {
      console.error("Error toggling feature flag:", err);
    }
  };

  if (loading) {
    return (
      <div className="branding-manager loading">
        Loading branding configuration...
      </div>
    );
  }

  if (error) {
    return <div className="branding-manager error">{error}</div>;
  }

  return (
    <div className="branding-manager">
      <div className="branding-header">
        <h1>Branding & Customization</h1>
        <p>Customize your platform's appearance and features</p>
      </div>

      <div className="branding-tabs">
        <button
          className={`tab ${activeTab === "branding" ? "active" : ""}`}
          onClick={() => setActiveTab("branding")}
        >
          Branding
        </button>
        <button
          className={`tab ${activeTab === "themes" ? "active" : ""}`}
          onClick={() => setActiveTab("themes")}
        >
          Themes
        </button>
        <button
          className={`tab ${activeTab === "features" ? "active" : ""}`}
          onClick={() => setActiveTab("features")}
        >
          Features
        </button>
        <button
          className={`tab ${activeTab === "domains" ? "active" : ""}`}
          onClick={() => setActiveTab("domains")}
        >
          Domains
        </button>
      </div>

      <div className="branding-content">
        {activeTab === "branding" && (
          <BrandingConfigPanel
            config={brandingConfig}
            onUpdate={updateBrandingConfig}
          />
        )}

        {activeTab === "themes" && (
          <ThemeConfigPanel
            themes={themes}
            brandingId={brandingConfig?.id}
            onThemeUpdate={loadThemes}
          />
        )}

        {activeTab === "features" && (
          <FeatureFlagsPanel
            flags={featureFlags}
            onToggle={toggleFeatureFlag}
          />
        )}

        {activeTab === "domains" && (
          <CustomDomainsPanel
            domains={customDomains}
            brandingId={brandingConfig?.id}
            onDomainUpdate={loadCustomDomains}
          />
        )}
      </div>
    </div>
  );
};
const BrandingConfigPanel = ({ config, onUpdate }) => {
  const [formData, setFormData] = useState(config || {});

  const handleInputChange = (field, value) => {
    setFormData({ ...formData, [field]: value });
  };

  const handleSave = () => {
    onUpdate(formData);
  };

  return (
    <div className="branding-config-panel">
      <h2>Organization Branding</h2>

      <div className="form-grid">
        <div className="form-group">
          <label>Organization Name</label>
          <input
            type="text"
            value={formData.organization_name || ""}
            onChange={(e) =>
              handleInputChange("organization_name", e.target.value)
            }
          />
        </div>

        <div className="form-group">
          <label>Logo URL</label>
          <input
            type="url"
            value={formData.logo_url || ""}
            onChange={(e) => handleInputChange("logo_url", e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>Favicon URL</label>
          <input
            type="url"
            value={formData.favicon_url || ""}
            onChange={(e) => handleInputChange("favicon_url", e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>Primary Color</label>
          <input
            type="color"
            value={formData.primary_color || "#3B82F6"}
            onChange={(e) => handleInputChange("primary_color", e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>Secondary Color</label>
          <input
            type="color"
            value={formData.secondary_color || "#6B7280"}
            onChange={(e) =>
              handleInputChange("secondary_color", e.target.value)
            }
          />
        </div>

        <div className="form-group">
          <label>Accent Color</label>
          <input
            type="color"
            value={formData.accent_color || "#10B981"}
            onChange={(e) => handleInputChange("accent_color", e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>Font Family</label>
          <select
            value={formData.font_family || "Inter, sans-serif"}
            onChange={(e) => handleInputChange("font_family", e.target.value)}
          >
            <option value="Inter, sans-serif">Inter</option>
            <option value="Roboto, sans-serif">Roboto</option>
            <option value="Open Sans, sans-serif">Open Sans</option>
            <option value="Lato, sans-serif">Lato</option>
            <option value="Montserrat, sans-serif">Montserrat</option>
          </select>
        </div>

        <div className="form-group">
          <label>Base Font Size (px)</label>
          <input
            type="number"
            min="12"
            max="24"
            value={formData.font_size_base || 16}
            onChange={(e) =>
              handleInputChange("font_size_base", parseFloat(e.target.value))
            }
          />
        </div>
      </div>

      <div className="form-group full-width">
        <label>Custom CSS</label>
        <textarea
          rows="10"
          value={formData.custom_css || ""}
          onChange={(e) => handleInputChange("custom_css", e.target.value)}
          placeholder="/* Add custom CSS styles here */"
        />
      </div>

      <button className="save-button" onClick={handleSave}>
        Save Branding Configuration
      </button>
    </div>
  );
};

const ThemeConfigPanel = ({ themes, brandingId, onThemeUpdate }) => {
  return (
    <div className="theme-config-panel">
      <h2>Theme Configurations</h2>

      <div className="themes-grid">
        {themes.map((theme) => (
          <div key={theme.id} className="theme-card">
            <h3>{theme.theme_name}</h3>
            <div className="theme-details">
              <p>
                <strong>Layout:</strong> {theme.layout_type}
              </p>
              <p>
                <strong>Mode:</strong> {theme.theme_mode}
              </p>
              <p>
                <strong>Sidebar:</strong> {theme.sidebar_position}
              </p>
              {theme.is_default && (
                <span className="default-badge">Default</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const FeatureFlagsPanel = ({ flags, onToggle }) => {
  return (
    <div className="feature-flags-panel">
      <h2>Feature Flags</h2>

      <div className="flags-list">
        {flags.map((flag) => (
          <div key={flag.id} className="flag-item">
            <div className="flag-info">
              <h3>{flag.flag_name}</h3>
              <p>{flag.description}</p>
              <span className="flag-key">{flag.flag_key}</span>
            </div>
            <div className="flag-controls">
              <label className="toggle-switch">
                <input
                  type="checkbox"
                  checked={flag.is_enabled}
                  onChange={() => onToggle(flag.id)}
                />
                <span className="slider"></span>
              </label>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const CustomDomainsPanel = ({ domains, brandingId, onDomainUpdate }) => {
  return (
    <div className="custom-domains-panel">
      <h2>Custom Domains</h2>

      <div className="domains-list">
        {domains.map((domain) => (
          <div key={domain.id} className="domain-item">
            <div className="domain-info">
              <h3>{domain.domain_name}</h3>
              <p>
                <strong>Status:</strong> {domain.status}
              </p>
              <p>
                <strong>SSL Status:</strong> {domain.ssl_status}
              </p>
              {domain.cname_target && (
                <p>
                  <strong>CNAME Target:</strong> {domain.cname_target}
                </p>
              )}
            </div>
            <div className="domain-actions">
              <button className="verify-button">Verify DNS</button>
              <button className="ssl-button">Provision SSL</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default BrandingManager;
