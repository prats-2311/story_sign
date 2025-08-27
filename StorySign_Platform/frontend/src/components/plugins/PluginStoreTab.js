import React, { useState } from "react";

const PluginStoreTab = ({ plugins, installationProgress, onInstall }) => {
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [sortBy, setSortBy] = useState("rating");

  const categories = ["all", ...new Set(plugins.map((p) => p.category))];

  const filteredAndSortedPlugins = plugins
    .filter(
      (plugin) =>
        selectedCategory === "all" || plugin.category === selectedCategory
    )
    .sort((a, b) => {
      switch (sortBy) {
        case "rating":
          return b.rating - a.rating;
        case "downloads":
          return b.downloads - a.downloads;
        case "name":
          return a.name.localeCompare(b.name);
        case "newest":
          return new Date(b.updated_at || 0) - new Date(a.updated_at || 0);
        default:
          return 0;
      }
    });

  const getRatingStars = (rating) => {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;
    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);

    return (
      <div className="rating-stars">
        {"★".repeat(fullStars)}
        {hasHalfStar && "☆"}
        {"☆".repeat(emptyStars)}
        <span className="rating-number">({rating})</span>
      </div>
    );
  };

  const getPermissionRiskLevel = (permissions) => {
    const highRiskPermissions = [
      "network:access",
      "filesystem:write",
      "database:write",
    ];
    const mediumRiskPermissions = [
      "filesystem:read",
      "database:read",
      "modify:ui",
    ];

    const hasHighRisk = permissions.some((p) =>
      highRiskPermissions.includes(p)
    );
    const hasMediumRisk = permissions.some((p) =>
      mediumRiskPermissions.includes(p)
    );

    if (hasHighRisk) return "high";
    if (hasMediumRisk) return "medium";
    return "low";
  };

  const getPermissionRiskColor = (riskLevel) => {
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

  if (plugins.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">🏪</div>
        <h3>Plugin Store Unavailable</h3>
        <p>
          The plugin store is currently unavailable. Please try again later.
        </p>
      </div>
    );
  }

  return (
    <div className="plugin-store-tab">
      <div className="store-controls">
        <div className="category-filter">
          <label htmlFor="category-select">Category:</label>
          <select
            id="category-select"
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="filter-select"
          >
            {categories.map((category) => (
              <option key={category} value={category}>
                {category === "all" ? "All Categories" : category}
              </option>
            ))}
          </select>
        </div>

        <div className="sort-filter">
          <label htmlFor="sort-select">Sort by:</label>
          <select
            id="sort-select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="filter-select"
          >
            <option value="rating">Rating</option>
            <option value="downloads">Downloads</option>
            <option value="name">Name</option>
            <option value="newest">Newest</option>
          </select>
        </div>
      </div>

      <div className="store-plugins-grid">
        {filteredAndSortedPlugins.map((plugin) => {
          const isInstalling = installationProgress[plugin.id] !== undefined;
          const installProgress = installationProgress[plugin.id] || 0;
          const permissionRisk = getPermissionRiskLevel(plugin.permissions);

          return (
            <div key={plugin.id} className="store-plugin-card">
              <div className="plugin-header">
                <div className="plugin-info">
                  <h3 className="plugin-name">{plugin.name}</h3>
                  <p className="plugin-version">v{plugin.version}</p>
                  <span className="plugin-category">{plugin.category}</span>
                </div>
                <div className="plugin-price">
                  {plugin.price === "free" ? (
                    <span className="price-free">FREE</span>
                  ) : (
                    <span className="price-paid">{plugin.price}</span>
                  )}
                </div>
              </div>

              <div className="plugin-body">
                <p className="plugin-description">{plugin.description}</p>

                <div className="plugin-stats">
                  <div className="stat-item">
                    {getRatingStars(plugin.rating)}
                  </div>
                  <div className="stat-item">
                    <span className="downloads-icon">⬇️</span>
                    <span className="downloads-count">
                      {plugin.downloads.toLocaleString()}
                    </span>
                  </div>
                </div>

                <div className="plugin-metadata">
                  <div className="metadata-item">
                    <span className="label">Author:</span>
                    <span className="value">{plugin.author}</span>
                  </div>
                </div>

                <div className="plugin-permissions">
                  <div className="permissions-header">
                    <span className="permissions-label">Permissions:</span>
                    <span
                      className={`risk-badge ${getPermissionRiskColor(
                        permissionRisk
                      )}`}
                    >
                      {permissionRisk} risk
                    </span>
                  </div>
                  <div className="permissions-list">
                    {plugin.permissions.slice(0, 3).map((permission) => (
                      <span key={permission} className="permission-tag">
                        {permission}
                      </span>
                    ))}
                    {plugin.permissions.length > 3 && (
                      <span className="permission-more">
                        +{plugin.permissions.length - 3} more
                      </span>
                    )}
                  </div>
                </div>

                {plugin.screenshots && plugin.screenshots.length > 0 && (
                  <div className="plugin-screenshots">
                    <div className="screenshots-grid">
                      {plugin.screenshots
                        .slice(0, 2)
                        .map((screenshot, index) => (
                          <img
                            key={index}
                            src={screenshot}
                            alt={`${plugin.name} screenshot ${index + 1}`}
                            className="screenshot-thumbnail"
                          />
                        ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="plugin-actions">
                {isInstalling ? (
                  <div className="installation-progress">
                    <div className="progress-bar">
                      <div
                        className="progress-fill"
                        style={{ width: `${installProgress}%` }}
                      ></div>
                    </div>
                    <span className="progress-text">
                      Installing... {installProgress}%
                    </span>
                  </div>
                ) : (
                  <>
                    <button
                      className="btn btn-primary btn-install"
                      onClick={() => onInstall(plugin.id)}
                      disabled={plugin.installed}
                    >
                      {plugin.installed ? "Installed" : "Install"}
                    </button>

                    <button className="btn btn-secondary btn-details">
                      View Details
                    </button>
                  </>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default PluginStoreTab;
