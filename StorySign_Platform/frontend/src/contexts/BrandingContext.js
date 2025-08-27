import React, { createContext, useContext, useState, useEffect } from "react";

const BrandingContext = createContext();

export const useBranding = () => {
  const context = useContext(BrandingContext);
  if (!context) {
    throw new Error("useBranding must be used within a BrandingProvider");
  }
  return context;
};

export const BrandingProvider = ({ children }) => {
  const [brandingConfig, setBrandingConfig] = useState(null);
  const [currentTheme, setCurrentTheme] = useState(null);
  const [featureFlags, setFeatureFlags] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadBrandingConfiguration();
  }, []);

  const loadBrandingConfiguration = async () => {
    try {
      setLoading(true);

      // Get public branding configuration
      const response = await fetch("/api/v1/public/branding");
      if (response.ok) {
        const config = await response.json();
        setBrandingConfig(config);
        setFeatureFlags(config.features_enabled || {});

        // Apply branding to DOM
        applyBrandingToDOM(config);

        // Load default theme if available
        if (config.id) {
          await loadDefaultTheme(config.id);
        }
      }
    } catch (error) {
      console.error("Failed to load branding configuration:", error);
      // Use default branding
      const defaultConfig = getDefaultBrandingConfig();
      setBrandingConfig(defaultConfig);
      setFeatureFlags(defaultConfig.features_enabled);
      applyBrandingToDOM(defaultConfig);
    } finally {
      setLoading(false);
    }
  };

  const loadDefaultTheme = async (brandingId) => {
    try {
      const response = await fetch(`/api/v1/themes/branding/${brandingId}`);
      if (response.ok) {
        const themes = await response.json();
        const defaultTheme =
          themes.find((theme) => theme.is_default) || themes[0];
        if (defaultTheme) {
          setCurrentTheme(defaultTheme);
          applyThemeToDOM(defaultTheme);
        }
      }
    } catch (error) {
      console.error("Failed to load theme:", error);
    }
  };

  const applyBrandingToDOM = (config) => {
    const root = document.documentElement;

    // Apply CSS custom properties
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

    // Update document title and favicon
    if (config.organization_name) {
      document.title = `${config.organization_name} - ASL Learning Platform`;
    }

    if (config.favicon_url) {
      updateFavicon(config.favicon_url);
    }

    // Inject custom CSS
    if (config.custom_css) {
      injectCustomCSS(config.custom_css);
    }
  };

  const applyThemeToDOM = (theme) => {
    const root = document.documentElement;

    // Apply theme mode
    root.setAttribute("data-theme", theme.theme_mode);

    // Apply layout settings
    root.style.setProperty("--layout-type", theme.layout_type);
    root.style.setProperty("--sidebar-position", theme.sidebar_position);
    root.style.setProperty("--header-style", theme.header_style);

    // Apply component styles
    if (theme.button_style) {
      applyComponentStyles("button", theme.button_style);
    }
    if (theme.card_style) {
      applyComponentStyles("card", theme.card_style);
    }
    if (theme.navigation_style) {
      applyComponentStyles("navigation", theme.navigation_style);
    }
  };

  const applyComponentStyles = (component, styles) => {
    const root = document.documentElement;

    Object.entries(styles).forEach(([property, value]) => {
      if (typeof value === "object") {
        // Handle nested styles (like variants)
        Object.entries(value).forEach(([subProperty, subValue]) => {
          root.style.setProperty(
            `--${component}-${property}-${subProperty}`,
            subValue
          );
        });
      } else {
        root.style.setProperty(`--${component}-${property}`, value);
      }
    });
  };

  const updateFavicon = (faviconUrl) => {
    const link =
      document.querySelector("link[rel*='icon']") ||
      document.createElement("link");
    link.type = "image/x-icon";
    link.rel = "shortcut icon";
    link.href = faviconUrl;
    document.getElementsByTagName("head")[0].appendChild(link);
  };

  const injectCustomCSS = (css) => {
    // Remove existing custom CSS
    const existingStyle = document.getElementById("custom-branding-css");
    if (existingStyle) {
      existingStyle.remove();
    }

    // Inject new custom CSS
    const style = document.createElement("style");
    style.id = "custom-branding-css";
    style.textContent = css;
    document.head.appendChild(style);
  };

  const getDefaultBrandingConfig = () => {
    return {
      organization_name: "StorySign",
      primary_color: "#3B82F6",
      secondary_color: "#6B7280",
      accent_color: "#10B981",
      background_color: "#FFFFFF",
      font_family: "Inter, sans-serif",
      font_size_base: 16,
      features_enabled: {
        asl_world: true,
        harmony: false,
        reconnect: false,
        analytics: true,
        collaborative_sessions: true,
        plugin_system: false,
        research_participation: true,
        social_features: true,
        group_management: true,
        custom_themes: true,
        api_access: false,
        white_labeling: true,
      },
    };
  };

  const isFeatureEnabled = (featureKey) => {
    return featureFlags[featureKey] === true;
  };

  const getFeatureValue = (featureKey, defaultValue = null) => {
    return featureFlags[featureKey] !== undefined
      ? featureFlags[featureKey]
      : defaultValue;
  };

  const switchTheme = async (themeId) => {
    try {
      // In a real implementation, this would load the theme from the API
      // For now, we'll just update the current theme
      const response = await fetch(`/api/v1/themes/${themeId}`);
      if (response.ok) {
        const theme = await response.json();
        setCurrentTheme(theme);
        applyThemeToDOM(theme);
      }
    } catch (error) {
      console.error("Failed to switch theme:", error);
    }
  };

  const value = {
    brandingConfig,
    currentTheme,
    featureFlags,
    loading,
    isFeatureEnabled,
    getFeatureValue,
    switchTheme,
    refreshBranding: loadBrandingConfiguration,
  };

  return (
    <BrandingContext.Provider value={value}>
      {children}
    </BrandingContext.Provider>
  );
};

export default BrandingProvider;
