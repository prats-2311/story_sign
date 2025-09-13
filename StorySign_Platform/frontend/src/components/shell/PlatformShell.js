import React, { createContext, useContext, useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { LogOut } from "lucide-react";
import { useAuth } from "../../contexts/AuthContext";
import { useResponsive } from "../../hooks/useResponsive";
import MobileNavigation from "../ui/MobileNavigation";
import "./PlatformShell.css";

// Platform Context for global state management
const PlatformContext = createContext();

// Custom hook to use platform context
export const usePlatform = () => {
  const context = useContext(PlatformContext);
  if (!context) {
    throw new Error("usePlatform must be used within a PlatformShell");
  }
  return context;
};

// Theme configuration
const THEMES = {
  light: {
    name: "Light",
    primary: "#2196F3",
    secondary: "#FFC107",
    background: "#ffffff",
    surface: "#f5f5f5",
    text: "#333333",
    textSecondary: "#666666",
  },
  dark: {
    name: "Dark",
    primary: "#64B5F6",
    secondary: "#FFD54F",
    background: "#121212",
    surface: "#1e1e1e",
    text: "#ffffff",
    textSecondary: "#cccccc",
  },
  highContrast: {
    name: "High Contrast",
    primary: "#000000",
    secondary: "#FFFF00",
    background: "#ffffff",
    surface: "#f0f0f0",
    text: "#000000",
    textSecondary: "#000000",
  },
};

// Module definitions for navigation
const MODULE_DEFINITIONS = [
  {
    id: "dashboard",
    name: "Dashboard",
    route: "/",
    icon: "🏠",
    permissions: ["read:own_data"],
    description: "Main dashboard and system controls",
  },
  {
    id: "asl-world",
    name: "ASL World",
    route: "/asl-world",
    icon: "🌍",
    permissions: ["read:own_data", "create:content"],
    description: "Interactive ASL learning environment",
  },
  {
    id: "plugins",
    name: "Plugins",
    route: "/plugins",
    icon: "🔌",
    permissions: ["install:plugins"],
    description: "Manage and configure plugins",
  },
  {
    id: "harmony",
    name: "Harmony",
    route: "/harmony",
    icon: "🎵",
    permissions: ["read:own_data"],
    description: "Collaborative learning sessions (Coming Soon)",
    disabled: false,
  },
  {
    id: "reconnect",
    name: "Reconnect",
    route: "/reconnect",
    icon: "🔗",
    permissions: ["read:own_data"],
    description: "Community challenges and social features (Coming Soon)",
    disabled: false,
  },
];

// Notification types
const NOTIFICATION_TYPES = {
  INFO: "info",
  SUCCESS: "success",
  WARNING: "warning",
  ERROR: "error",
};

const PlatformShell = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isMobile, shouldCollapseSidebar } = useResponsive();

  // Use AuthContext for authentication state
  const {
    user,
    isAuthenticated,
    isLoading: authLoading,
    logout: authLogout,
  } = useAuth();

  // Theme and accessibility state
  const [currentTheme, setCurrentTheme] = useState("light");
  const [accessibilitySettings, setAccessibilitySettings] = useState({
    fontSize: "medium",
    reducedMotion: false,
    highContrast: false,
    screenReader: false,
  });

  // Navigation state - responsive default
  const [sidebarOpen, setSidebarOpen] = useState(!shouldCollapseSidebar);
  const [currentModule, setCurrentModule] = useState("dashboard");

  // Notification system state
  const [notifications, setNotifications] = useState([]);
  const [notificationCounter, setNotificationCounter] = useState(0);

  // Plugin system state (placeholder)
  const [loadedPlugins] = useState([]);

  // Update current module based on route
  useEffect(() => {
    const currentPath = location.pathname;
    const module = MODULE_DEFINITIONS.find(
      mod =>
        mod.route === currentPath || currentPath.startsWith(mod.route + "/")
    );
    if (module) {
      setCurrentModule(module.id);
    }
  }, [location.pathname]);

  // Apply theme to CSS variables
  useEffect(() => {
    const theme = THEMES[currentTheme];
    const root = document.documentElement;

    Object.entries(theme).forEach(([key, value]) => {
      if (key !== "name") {
        root.style.setProperty(`--theme-${key}`, value);
      }
    });
  }, [currentTheme]);

  // Apply accessibility settings
  useEffect(() => {
    const root = document.documentElement;

    // Font size
    const fontSizeMap = {
      small: "14px",
      medium: "16px",
      large: "18px",
      xlarge: "20px",
    };
    root.style.setProperty(
      "--base-font-size",
      fontSizeMap[accessibilitySettings.fontSize]
    );

    // Reduced motion
    if (accessibilitySettings.reducedMotion) {
      root.style.setProperty("--animation-duration", "0s");
      root.style.setProperty("--transition-duration", "0s");
    } else {
      root.style.setProperty("--animation-duration", "0.3s");
      root.style.setProperty("--transition-duration", "0.2s");
    }

    // High contrast mode
    if (accessibilitySettings.highContrast && currentTheme !== "highContrast") {
      setCurrentTheme("highContrast");
    }
  }, [accessibilitySettings, currentTheme]);

  // Logout wrapper function to add notification
  const logout = async () => {
    try {
      await authLogout();
      addNotification("You have been logged out.", NOTIFICATION_TYPES.INFO);
    } catch (error) {
      addNotification("Logout failed.", NOTIFICATION_TYPES.ERROR);
      console.error("Logout error:", error);
    }
  };

  // Theme management
  const changeTheme = themeName => {
    if (THEMES[themeName]) {
      setCurrentTheme(themeName);
      addNotification(
        `Theme changed to ${THEMES[themeName].name}`,
        NOTIFICATION_TYPES.INFO
      );
    }
  };

  // Accessibility settings management
  const updateAccessibilitySettings = newSettings => {
    setAccessibilitySettings(prev => ({ ...prev, ...newSettings }));
    addNotification(
      "Accessibility settings updated",
      NOTIFICATION_TYPES.SUCCESS
    );
  };

  // Notification system
  const addNotification = (
    message,
    type = NOTIFICATION_TYPES.INFO,
    duration = 5000
  ) => {
    const id = notificationCounter + 1;
    setNotificationCounter(id);

    const notification = {
      id,
      message,
      type,
      timestamp: new Date().toISOString(),
      duration,
    };

    setNotifications(prev => [...prev, notification]);

    // Auto-remove notification after duration
    if (duration > 0) {
      setTimeout(() => {
        removeNotification(id);
      }, duration);
    }

    return id;
  };

  const removeNotification = id => {
    setNotifications(prev =>
      prev.filter(notification => notification.id !== id)
    );
  };

  const clearAllNotifications = () => {
    setNotifications([]);
  };

  // Navigation functions
  const navigateToModule = moduleId => {
    const module = MODULE_DEFINITIONS.find(mod => mod.id === moduleId);
    if (module && !module.disabled) {
      navigate(module.route);
    }
  };

  const toggleSidebar = () => {
    setSidebarOpen(prev => !prev);
  };

  // Plugin system functions (placeholders)
  const loadPlugin = async pluginId => {
    // TODO: Implement plugin loading
    console.log("Loading plugin:", pluginId);
    addNotification(`Plugin ${pluginId} loaded`, NOTIFICATION_TYPES.SUCCESS);
  };

  const unloadPlugin = async pluginId => {
    // TODO: Implement plugin unloading
    console.log("Unloading plugin:", pluginId);
    addNotification(`Plugin ${pluginId} unloaded`, NOTIFICATION_TYPES.INFO);
  };

  // Context value
  const contextValue = {
    // Authentication (from AuthContext)
    user,
    isAuthenticated,
    authLoading,
    logout,

    // Theme and accessibility
    currentTheme,
    availableThemes: Object.keys(THEMES),
    changeTheme,
    accessibilitySettings,
    updateAccessibilitySettings,

    // Navigation
    currentModule,
    modules: MODULE_DEFINITIONS,
    navigateToModule,
    sidebarOpen,
    toggleSidebar,

    // Notifications
    notifications,
    addNotification,
    removeNotification,
    clearAllNotifications,
    notificationTypes: NOTIFICATION_TYPES,

    // Plugins
    loadedPlugins,
    loadPlugin,
    unloadPlugin,
  };

  return (
    <PlatformContext.Provider value={contextValue}>
      <div
        className={`platform-shell theme-${currentTheme} ${
          isMobile ? "mobile" : ""
        }`}
      >
        <PlatformHeader />
        <div className="platform-body">
          <PlatformSidebar />
          <main className="platform-main">{children}</main>
        </div>
        <PlatformNotifications />
        {isMobile && <MobileNavigation />}
      </div>
    </PlatformContext.Provider>
  );
};

// Platform Header Component
const PlatformHeader = () => {
  const {
    user,
    isAuthenticated,
    logout,
    toggleSidebar,
    currentModule,
    modules,
    currentTheme,
    availableThemes,
    changeTheme,
  } = usePlatform();

  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showThemeMenu, setShowThemeMenu] = useState(false);

  const currentModuleInfo = modules.find(mod => mod.id === currentModule);

  return (
    <header className="platform-header">
      <div className="header-left">
        <button
          className="sidebar-toggle"
          onClick={toggleSidebar}
          aria-label="Toggle sidebar"
        >
          ☰
        </button>
        <div className="platform-logo">
          <h1>StorySign</h1>
        </div>
        {currentModuleInfo && (
          <div className="current-module">
            <span className="module-icon">{currentModuleInfo.icon}</span>
            <span className="module-name">{currentModuleInfo.name}</span>
          </div>
        )}
      </div>

      <div className="header-right">
        <div className="theme-selector">
          <button
            className="theme-toggle"
            onClick={() => setShowThemeMenu(!showThemeMenu)}
            aria-label="Change theme"
          >
            🎨
          </button>
          {showThemeMenu && (
            <div className="theme-menu">
              {availableThemes.map(theme => (
                <button
                  key={theme}
                  className={`theme-option ${
                    theme === currentTheme ? "active" : ""
                  }`}
                  onClick={() => {
                    changeTheme(theme);
                    setShowThemeMenu(false);
                  }}
                >
                  {THEMES[theme].name}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="user-menu">
          {isAuthenticated ? (
            <>
              <button
                className="user-avatar"
                onClick={() => setShowUserMenu(!showUserMenu)}
                aria-label="User menu"
              >
                {user?.firstName?.[0] || user?.email?.[0] || "?"}
              </button>
              {showUserMenu && (
                <div className="user-dropdown">
                  <div className="user-info">
                    <div className="user-name">
                      {user?.firstName} {user?.lastName}
                    </div>
                    <div className="user-email">{user?.email}</div>
                  </div>
                  <hr />
                  <button onClick={() => setShowUserMenu(false)}>
                    Profile
                  </button>
                  <button onClick={() => setShowUserMenu(false)}>
                    Settings
                  </button>
                  <hr />
                  <button
                    onClick={() => {
                      logout();
                      setShowUserMenu(false);
                    }}
                    className="logout-button"
                  >
                    <LogOut size={16} />
                    Logout
                  </button>
                </div>
              )}
            </>
          ) : (
            <button className="login-btn">Login</button>
          )}
        </div>
      </div>
    </header>
  );
};

// Platform Sidebar Component
const PlatformSidebar = () => {
  const { sidebarOpen, modules, currentModule, navigateToModule } =
    usePlatform();
  const { isMobile } = useResponsive();

  // Hide sidebar on mobile (use mobile navigation instead)
  if (!sidebarOpen || isMobile) return null;

  return (
    <aside className="platform-sidebar">
      <nav className="sidebar-nav">
        <ul className="nav-list">
          {modules.map(module => (
            <li key={module.id} className="nav-item">
              <button
                className={`nav-link ${
                  currentModule === module.id ? "active" : ""
                } ${module.disabled ? "disabled" : ""}`}
                onClick={() => navigateToModule(module.id)}
                disabled={module.disabled}
                title={module.description}
              >
                <span className="nav-icon">{module.icon}</span>
                <span className="nav-text">{module.name}</span>
                {module.disabled && <span className="nav-badge">Soon</span>}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      <div className="sidebar-footer">
        <div className="connection-status">
          <span className="status-indicator"></span>
          <span className="status-text">System Ready</span>
        </div>
      </div>
    </aside>
  );
};

// Platform Notifications Component
const PlatformNotifications = () => {
  const { notifications, removeNotification } = usePlatform();

  if (notifications.length === 0) return null;

  return (
    <div className="platform-notifications">
      {notifications.map(notification => (
        <div
          key={notification.id}
          className={`notification notification-${notification.type}`}
        >
          <div className="notification-content">
            <span className="notification-message">{notification.message}</span>
            <button
              className="notification-close"
              onClick={() => removeNotification(notification.id)}
              aria-label="Close notification"
            >
              ×
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default PlatformShell;
