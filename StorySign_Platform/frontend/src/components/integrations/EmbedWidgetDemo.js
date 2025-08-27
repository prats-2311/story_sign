/**
 * Embeddable Widget Demo Component
 * Demonstrates how external sites can embed StorySign widgets
 */

import React, { useState, useEffect } from "react";
import "./EmbedWidgetDemo.css";

const EmbedWidgetDemo = () => {
  const [selectedWidget, setSelectedWidget] = useState("practice");
  const [embedCode, setEmbedCode] = useState("");
  const [previewUrl, setPreviewUrl] = useState("");
  const [widgetConfig, setWidgetConfig] = useState({
    domain: "example.com",
    userId: "",
    groupId: "",
    theme: "default",
    width: 800,
    height: 600,
  });

  // Generate embed code when configuration changes
  useEffect(() => {
    generateEmbedCode();
  }, [selectedWidget, widgetConfig]);

  const generateEmbedCode = () => {
    const baseUrl = window.location.origin;
    const params = new URLSearchParams({
      domain: widgetConfig.domain,
      ...(widgetConfig.userId && { user_id: widgetConfig.userId }),
      ...(widgetConfig.groupId && { group_id: widgetConfig.groupId }),
      ...(widgetConfig.theme && { theme: widgetConfig.theme }),
      ...(widgetConfig.width && { width: widgetConfig.width }),
      ...(widgetConfig.height && { height: widgetConfig.height }),
    });

    const iframeUrl = `${baseUrl}/api/v1/integrations/embed/widget/${selectedWidget}?${params}`;
    setPreviewUrl(iframeUrl);

    // Generate JavaScript embed code
    const jsEmbedCode = `
<!-- StorySign Widget Embed -->
<div id="storysign-widget-container"></div>
<script src="${baseUrl}/api/v1/integrations/embed/script/${selectedWidget}?domain=${widgetConfig.domain}"></script>
<script>
  StorySignWidget.init({
    containerId: 'storysign-widget-container',
    userId: '${widgetConfig.userId}',
    groupId: '${widgetConfig.groupId}',
    theme: '${widgetConfig.theme}',
    width: ${widgetConfig.width},
    height: ${widgetConfig.height}
  });
</script>

<!-- Alternative: Direct iframe embed -->
<iframe 
  src="${iframeUrl}"
  width="${widgetConfig.width}" 
  height="${widgetConfig.height}"
  frameborder="0"
  style="border: none;">
</iframe>`;

    setEmbedCode(jsEmbedCode);
  };

  const handleConfigChange = (key, value) => {
    setWidgetConfig((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(embedCode).then(() => {
      alert("Embed code copied to clipboard!");
    });
  };

  const widgetTypes = [
    {
      value: "practice",
      label: "Practice Widget",
      description: "Interactive ASL practice session",
    },
    {
      value: "progress",
      label: "Progress Widget",
      description: "User learning progress display",
    },
    {
      value: "leaderboard",
      label: "Leaderboard Widget",
      description: "Group leaderboard and rankings",
    },
  ];

  const themes = [
    { value: "default", label: "Default" },
    { value: "light", label: "Light" },
    { value: "dark", label: "Dark" },
    { value: "blue", label: "Blue" },
    { value: "green", label: "Green" },
  ];

  return (
    <div className="embed-widget-demo">
      <div className="demo-header">
        <h2>StorySign Embeddable Widgets</h2>
        <p>Integrate StorySign learning components into your website or LMS</p>
      </div>

      <div className="demo-content">
        <div className="configuration-panel">
          <h3>Widget Configuration</h3>

          <div className="config-section">
            <label>Widget Type:</label>
            <div className="widget-type-selector">
              {widgetTypes.map((type) => (
                <div
                  key={type.value}
                  className={`widget-type-option ${
                    selectedWidget === type.value ? "selected" : ""
                  }`}
                  onClick={() => setSelectedWidget(type.value)}
                >
                  <div className="widget-type-label">{type.label}</div>
                  <div className="widget-type-description">
                    {type.description}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="config-section">
            <label>Domain:</label>
            <input
              type="text"
              value={widgetConfig.domain}
              onChange={(e) => handleConfigChange("domain", e.target.value)}
              placeholder="example.com"
            />
          </div>

          <div className="config-section">
            <label>User ID (optional):</label>
            <input
              type="text"
              value={widgetConfig.userId}
              onChange={(e) => handleConfigChange("userId", e.target.value)}
              placeholder="user-123"
            />
          </div>

          <div className="config-section">
            <label>Group ID (optional):</label>
            <input
              type="text"
              value={widgetConfig.groupId}
              onChange={(e) => handleConfigChange("groupId", e.target.value)}
              placeholder="group-456"
            />
          </div>

          <div className="config-section">
            <label>Theme:</label>
            <select
              value={widgetConfig.theme}
              onChange={(e) => handleConfigChange("theme", e.target.value)}
            >
              {themes.map((theme) => (
                <option key={theme.value} value={theme.value}>
                  {theme.label}
                </option>
              ))}
            </select>
          </div>

          <div className="config-section">
            <label>Dimensions:</label>
            <div className="dimensions-inputs">
              <input
                type="number"
                value={widgetConfig.width}
                onChange={(e) =>
                  handleConfigChange("width", parseInt(e.target.value))
                }
                placeholder="Width"
              />
              <span>×</span>
              <input
                type="number"
                value={widgetConfig.height}
                onChange={(e) =>
                  handleConfigChange("height", parseInt(e.target.value))
                }
                placeholder="Height"
              />
            </div>
          </div>
        </div>

        <div className="preview-panel">
          <h3>Widget Preview</h3>
          <div className="widget-preview">
            <iframe
              src={previewUrl}
              width={Math.min(widgetConfig.width, 600)}
              height={Math.min(widgetConfig.height, 400)}
              frameBorder="0"
              title="Widget Preview"
            />
          </div>
        </div>
      </div>

      <div className="embed-code-section">
        <div className="embed-code-header">
          <h3>Embed Code</h3>
          <button onClick={copyToClipboard} className="copy-button">
            Copy to Clipboard
          </button>
        </div>
        <textarea
          className="embed-code-textarea"
          value={embedCode}
          readOnly
          rows={15}
        />
      </div>

      <div className="integration-info">
        <h3>Integration Information</h3>
        <div className="info-grid">
          <div className="info-card">
            <h4>OAuth2 Integration</h4>
            <p>Support for Google, Microsoft, and custom OAuth providers</p>
            <ul>
              <li>Automatic user creation and login</li>
              <li>Secure token-based authentication</li>
              <li>Configurable scopes and permissions</li>
            </ul>
          </div>

          <div className="info-card">
            <h4>SAML SSO</h4>
            <p>Enterprise single sign-on integration</p>
            <ul>
              <li>SAML 2.0 compliant</li>
              <li>Automatic user provisioning</li>
              <li>Metadata exchange support</li>
            </ul>
          </div>

          <div className="info-card">
            <h4>LTI Integration</h4>
            <p>Learning Management System integration</p>
            <ul>
              <li>LTI 1.1 and 2.0 support</li>
              <li>Grade passback capability</li>
              <li>Deep linking support</li>
            </ul>
          </div>

          <div className="info-card">
            <h4>Webhooks</h4>
            <p>Real-time event notifications</p>
            <ul>
              <li>Configurable event subscriptions</li>
              <li>Secure signature verification</li>
              <li>Automatic retry on failure</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="api-documentation">
        <h3>API Documentation</h3>
        <div className="api-endpoints">
          <div className="endpoint">
            <span className="method">GET</span>
            <span className="path">/api/v1/integrations/oauth/providers</span>
            <span className="description">List OAuth providers</span>
          </div>
          <div className="endpoint">
            <span className="method">POST</span>
            <span className="path">
              /api/v1/integrations/oauth/{provider}/callback
            </span>
            <span className="description">OAuth callback handler</span>
          </div>
          <div className="endpoint">
            <span className="method">GET</span>
            <span className="path">/api/v1/integrations/saml/metadata</span>
            <span className="description">SAML metadata XML</span>
          </div>
          <div className="endpoint">
            <span className="method">POST</span>
            <span className="path">/api/v1/integrations/lti/launch</span>
            <span className="description">LTI launch handler</span>
          </div>
          <div className="endpoint">
            <span className="method">POST</span>
            <span className="path">/api/v1/integrations/webhooks</span>
            <span className="description">Create webhook</span>
          </div>
          <div className="endpoint">
            <span className="method">GET</span>
            <span className="path">
              /api/v1/integrations/embed/widget/{type}
            </span>
            <span className="description">Embeddable widget</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmbedWidgetDemo;
