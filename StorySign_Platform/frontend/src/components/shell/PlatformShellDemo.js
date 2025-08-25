import React from "react";
import { usePlatform } from "./PlatformShell";

/**
 * Demo component to test Platform Shell functionality
 * This component demonstrates all the key features of the Platform Shell
 */
const PlatformShellDemo = () => {
  const {
    user,
    isAuthenticated,
    currentTheme,
    currentModule,
    notifications,
    addNotification,
    removeNotification,
    changeTheme,
    availableThemes,
    accessibilitySettings,
    updateAccessibilitySettings,
    navigateToModule,
    modules,
    sidebarOpen,
    toggleSidebar,
    notificationTypes,
  } = usePlatform();

  const handleTestNotification = (type) => {
    const messages = {
      [notificationTypes.INFO]: "This is an info notification",
      [notificationTypes.SUCCESS]: "Operation completed successfully!",
      [notificationTypes.WARNING]: "This is a warning message",
      [notificationTypes.ERROR]: "An error occurred during the operation",
    };

    addNotification(messages[type], type);
  };

  const handleAccessibilityChange = (setting, value) => {
    updateAccessibilitySettings({ [setting]: value });
  };

  return (
    <div style={{ padding: "2rem", maxWidth: "800px" }}>
      <h2>Platform Shell Demo & Testing</h2>

      {/* Authentication Status */}
      <section
        style={{
          marginBottom: "2rem",
          padding: "1rem",
          border: "1px solid #ccc",
          borderRadius: "8px",
        }}
      >
        <h3>Authentication Status</h3>
        <p>
          <strong>Authenticated:</strong> {isAuthenticated ? "Yes" : "No"}
        </p>
        {user && (
          <div>
            <p>
              <strong>User:</strong> {user.firstName} {user.lastName}
            </p>
            <p>
              <strong>Email:</strong> {user.email}
            </p>
            <p>
              <strong>Role:</strong> {user.role}
            </p>
          </div>
        )}
      </section>

      {/* Theme Management */}
      <section
        style={{
          marginBottom: "2rem",
          padding: "1rem",
          border: "1px solid #ccc",
          borderRadius: "8px",
        }}
      >
        <h3>Theme Management</h3>
        <p>
          <strong>Current Theme:</strong> {currentTheme}
        </p>
        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          {availableThemes.map((theme) => (
            <button
              key={theme}
              onClick={() => changeTheme(theme)}
              style={{
                padding: "0.5rem 1rem",
                backgroundColor: theme === currentTheme ? "#007bff" : "#f8f9fa",
                color: theme === currentTheme ? "white" : "black",
                border: "1px solid #ccc",
                borderRadius: "4px",
                cursor: "pointer",
              }}
            >
              {theme}
            </button>
          ))}
        </div>
      </section>

      {/* Navigation */}
      <section
        style={{
          marginBottom: "2rem",
          padding: "1rem",
          border: "1px solid #ccc",
          borderRadius: "8px",
        }}
      >
        <h3>Navigation</h3>
        <p>
          <strong>Current Module:</strong> {currentModule}
        </p>
        <p>
          <strong>Sidebar:</strong> {sidebarOpen ? "Open" : "Closed"}
        </p>
        <button
          onClick={toggleSidebar}
          style={{
            padding: "0.5rem 1rem",
            marginRight: "0.5rem",
            cursor: "pointer",
          }}
        >
          Toggle Sidebar
        </button>
        <div style={{ marginTop: "1rem" }}>
          <h4>Available Modules:</h4>
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            {modules.map((module) => (
              <button
                key={module.id}
                onClick={() => navigateToModule(module.id)}
                disabled={module.disabled}
                style={{
                  padding: "0.5rem 1rem",
                  backgroundColor:
                    module.id === currentModule ? "#28a745" : "#f8f9fa",
                  color: module.id === currentModule ? "white" : "black",
                  border: "1px solid #ccc",
                  borderRadius: "4px",
                  cursor: module.disabled ? "not-allowed" : "pointer",
                  opacity: module.disabled ? 0.5 : 1,
                }}
                title={module.description}
              >
                {module.icon} {module.name}
                {module.disabled && " (Soon)"}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Notifications */}
      <section
        style={{
          marginBottom: "2rem",
          padding: "1rem",
          border: "1px solid #ccc",
          borderRadius: "8px",
        }}
      >
        <h3>Notification System</h3>
        <p>
          <strong>Active Notifications:</strong> {notifications.length}
        </p>
        <div
          style={{
            display: "flex",
            gap: "0.5rem",
            flexWrap: "wrap",
            marginBottom: "1rem",
          }}
        >
          {Object.values(notificationTypes).map((type) => (
            <button
              key={type}
              onClick={() => handleTestNotification(type)}
              style={{
                padding: "0.5rem 1rem",
                backgroundColor: {
                  info: "#17a2b8",
                  success: "#28a745",
                  warning: "#ffc107",
                  error: "#dc3545",
                }[type],
                color: type === "warning" ? "black" : "white",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
              }}
            >
              Add {type.toUpperCase()}
            </button>
          ))}
        </div>
        {notifications.length > 0 && (
          <div>
            <h4>Current Notifications:</h4>
            {notifications.map((notification) => (
              <div
                key={notification.id}
                style={{
                  padding: "0.5rem",
                  margin: "0.25rem 0",
                  backgroundColor: "#f8f9fa",
                  border: "1px solid #ccc",
                  borderRadius: "4px",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <span>
                  <strong>[{notification.type.toUpperCase()}]</strong>{" "}
                  {notification.message}
                </span>
                <button
                  onClick={() => removeNotification(notification.id)}
                  style={{
                    background: "none",
                    border: "none",
                    cursor: "pointer",
                    fontSize: "1.2rem",
                  }}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Accessibility Settings */}
      <section
        style={{
          marginBottom: "2rem",
          padding: "1rem",
          border: "1px solid #ccc",
          borderRadius: "8px",
        }}
      >
        <h3>Accessibility Settings</h3>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "1rem",
          }}
        >
          <div>
            <label>
              <strong>Font Size:</strong>
              <select
                value={accessibilitySettings.fontSize}
                onChange={(e) =>
                  handleAccessibilityChange("fontSize", e.target.value)
                }
                style={{ marginLeft: "0.5rem", padding: "0.25rem" }}
              >
                <option value="small">Small</option>
                <option value="medium">Medium</option>
                <option value="large">Large</option>
                <option value="xlarge">Extra Large</option>
              </select>
            </label>
          </div>
          <div>
            <label>
              <input
                type="checkbox"
                checked={accessibilitySettings.reducedMotion}
                onChange={(e) =>
                  handleAccessibilityChange("reducedMotion", e.target.checked)
                }
                style={{ marginRight: "0.5rem" }}
              />
              <strong>Reduced Motion</strong>
            </label>
          </div>
          <div>
            <label>
              <input
                type="checkbox"
                checked={accessibilitySettings.highContrast}
                onChange={(e) =>
                  handleAccessibilityChange("highContrast", e.target.checked)
                }
                style={{ marginRight: "0.5rem" }}
              />
              <strong>High Contrast</strong>
            </label>
          </div>
          <div>
            <label>
              <input
                type="checkbox"
                checked={accessibilitySettings.screenReader}
                onChange={(e) =>
                  handleAccessibilityChange("screenReader", e.target.checked)
                }
                style={{ marginRight: "0.5rem" }}
              />
              <strong>Screen Reader Support</strong>
            </label>
          </div>
        </div>
      </section>

      {/* System Information */}
      <section
        style={{
          marginBottom: "2rem",
          padding: "1rem",
          border: "1px solid #ccc",
          borderRadius: "8px",
        }}
      >
        <h3>System Information</h3>
        <div style={{ fontFamily: "monospace", fontSize: "0.9rem" }}>
          <p>
            <strong>Current Module:</strong> {currentModule}
          </p>
          <p>
            <strong>Theme:</strong> {currentTheme}
          </p>
          <p>
            <strong>Sidebar Open:</strong> {sidebarOpen.toString()}
          </p>
          <p>
            <strong>Notifications:</strong> {notifications.length}
          </p>
          <p>
            <strong>Font Size:</strong> {accessibilitySettings.fontSize}
          </p>
          <p>
            <strong>Reduced Motion:</strong>{" "}
            {accessibilitySettings.reducedMotion.toString()}
          </p>
          <p>
            <strong>High Contrast:</strong>{" "}
            {accessibilitySettings.highContrast.toString()}
          </p>
        </div>
      </section>

      {/* Instructions */}
      <section
        style={{
          padding: "1rem",
          backgroundColor: "#e9ecef",
          borderRadius: "8px",
        }}
      >
        <h3>Testing Instructions</h3>
        <ol>
          <li>Test theme switching by clicking the theme buttons above</li>
          <li>Toggle the sidebar and observe the navigation changes</li>
          <li>
            Try navigating between modules (Dashboard and ASL World should work)
          </li>
          <li>Test notifications by clicking the notification type buttons</li>
          <li>Adjust accessibility settings and observe the changes</li>
          <li>
            Check that the header shows the current module and theme selector
          </li>
          <li>
            Verify that disabled modules (Harmony, Reconnect) show "Soon" badges
          </li>
        </ol>
      </section>
    </div>
  );
};

export default PlatformShellDemo;
