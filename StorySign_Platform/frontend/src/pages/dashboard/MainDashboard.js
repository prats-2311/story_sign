import React from "react";

const MainDashboard = ({ onNavigateToASLWorld }) => {
  return (
    <div className="control-panel">
      {/* ASL World Navigation Button - Direct access without backend connection requirement */}
      <div className="asl-world-toggle">
        <button className="asl-world-toggle-btn" onClick={onNavigateToASLWorld}>
          Enter ASL World
        </button>
        <p className="asl-world-description">
          Start your ASL learning journey! The backend will connect
          automatically when you begin practicing.
        </p>
      </div>

      {/* Platform Shell Demo Section */}
      <div className="platform-demo-section">
        <h3>Platform Shell Features</h3>
        <p>The new Platform Shell provides:</p>
        <ul>
          <li>✅ Global navigation with module switching</li>
          <li>✅ Theme management (Light, Dark, High Contrast)</li>
          <li>✅ Notification system for cross-module communication</li>
          <li>✅ Accessibility settings and controls</li>
          <li>✅ User authentication placeholders</li>
          <li>✅ Responsive sidebar with module status</li>
        </ul>
        <p>
          <strong>Navigation:</strong> Use the sidebar to switch between
          modules. ASL World is fully functional, while Harmony and Reconnect
          show "Coming Soon" status.
        </p>
        <p>
          <strong>Themes:</strong> Click the 🎨 icon in the header to switch
          themes.
        </p>
        <p>
          <strong>Notifications:</strong> The system will show notifications in
          the top-right corner.
        </p>
        <div style={{ marginTop: "15px" }}>
          <a
            href="/platform-demo"
            style={{
              color: "#1976D2",
              textDecoration: "none",
              fontWeight: "bold",
              padding: "8px 16px",
              border: "2px solid #1976D2",
              borderRadius: "4px",
              display: "inline-block",
              transition: "all 0.2s ease",
            }}
            onMouseOver={e => {
              e.target.style.backgroundColor = "#1976D2";
              e.target.style.color = "white";
            }}
            onMouseOut={e => {
              e.target.style.backgroundColor = "transparent";
              e.target.style.color = "#1976D2";
            }}
          >
            🧪 Test Platform Shell Features
          </a>
        </div>
      </div>
    </div>
  );
};

export default MainDashboard;
