/**
 * Cross-platform synchronization service for StorySign frontend
 * Handles device-agnostic sessions, data sync, and offline changes
 */

import API_BASE_URL from "../config/api";

class SyncService {
  constructor() {
    this.currentSession = null;
    this.syncQueue = [];
    this.offlineChanges = [];
    this.isOnline = navigator.onLine;
    this.syncInProgress = false;
    this.conflictHandlers = new Map();
    this.syncListeners = new Set();

    // Device information
    this.deviceInfo = this.detectDeviceInfo();
    this.bandwidthProfile = this.detectBandwidthProfile();

    this.init();
  }

  async init() {
    try {
      // Set up event listeners
      this.setupEventListeners();

      // Initialize offline storage
      await this.initOfflineStorage();

      // Load offline changes
      await this.loadOfflineChanges();

      console.log("SyncService: Initialized successfully");
    } catch (error) {
      console.error("SyncService: Initialization failed:", error);
    }
  }

  setupEventListeners() {
    // Online/offline status
    window.addEventListener("online", () => {
      this.isOnline = true;
      console.log("SyncService: Back online");
      this.onOnline();
    });

    window.addEventListener("offline", () => {
      this.isOnline = false;
      console.log("SyncService: Gone offline");
      this.onOffline();
    });

    // Page visibility for sync triggers
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden && this.isOnline) {
        this.triggerSync();
      }
    });

    // Before unload - save pending changes
    window.addEventListener("beforeunload", () => {
      this.saveOfflineChanges();
    });
  }

  // Device-agnostic session management

  async createSession(sessionData = {}) {
    try {
      const response = await this.apiCall("/sync/sessions", "POST", {
        device_info: this.deviceInfo,
        session_data: sessionData,
      });

      if (response.success) {
        this.currentSession = response.session;

        // Set up WebSocket for real-time sync
        await this.setupSyncWebSocket();

        console.log(
          "SyncService: Session created:",
          this.currentSession.session_id
        );
        return this.currentSession;
      }

      throw new Error("Failed to create session");
    } catch (error) {
      console.error("SyncService: Session creation failed:", error);
      throw error;
    }
  }

  async getSessions() {
    try {
      const response = await this.apiCall("/sync/sessions", "GET");
      return response.success ? response.sessions : [];
    } catch (error) {
      console.error("SyncService: Failed to get sessions:", error);
      return [];
    }
  }

  async terminateSession(sessionId) {
    try {
      const response = await this.apiCall(
        `/sync/sessions/${sessionId}`,
        "DELETE"
      );

      if (sessionId === this.currentSession?.session_id) {
        this.currentSession = null;
        this.closeSyncWebSocket();
      }

      return response.success;
    } catch (error) {
      console.error("SyncService: Failed to terminate session:", error);
      return false;
    }
  }

  // Data synchronization

  async syncData(dataUpdates, options = {}) {
    if (!this.currentSession) {
      throw new Error("No active session for synchronization");
    }

    if (!this.isOnline) {
      // Queue for offline sync
      return this.queueOfflineChange("sync", dataUpdates, options);
    }

    try {
      this.syncInProgress = true;
      this.notifyListeners("sync_started", { dataUpdates });

      // Optimize data based on bandwidth
      const optimizedData = await this.optimizeDataForSync(dataUpdates);

      const response = await this.apiCall("/sync/sync", "POST", {
        session_id: this.currentSession.session_id,
        data_updates: optimizedData,
        client_version: this.currentSession.sync_version,
        checksum: this.calculateChecksum(optimizedData),
      });

      if (response.success) {
        const result = response.sync_result;

        // Update local session version
        this.currentSession.sync_version = result.sync_version;

        // Handle conflicts if any
        if (result.conflicts && result.conflicts.length > 0) {
          await this.handleConflicts(result.conflicts);
        }

        this.notifyListeners("sync_completed", result);
        return result;
      }

      throw new Error("Synchronization failed");
    } catch (error) {
      console.error("SyncService: Sync failed:", error);
      this.notifyListeners("sync_failed", { error });

      // Queue for retry if network error
      if (this.isNetworkError(error)) {
        this.queueOfflineChange("sync", dataUpdates, options);
      }

      throw error;
    } finally {
      this.syncInProgress = false;
    }
  }

  async queueSyncOperation(operationType, data, priority = 1) {
    if (this.isOnline) {
      try {
        const response = await this.apiCall(
          "/sync/queue-operation",
          "POST",
          null,
          {
            operation_type: operationType,
            data: data,
            priority: priority,
          }
        );

        return response.success ? response.operation_id : null;
      } catch (error) {
        console.error("SyncService: Failed to queue operation:", error);
      }
    }

    // Fallback to local queue
    const operation = {
      id: this.generateId(),
      type: operationType,
      data: data,
      priority: priority,
      timestamp: Date.now(),
    };

    this.syncQueue.push(operation);
    this.syncQueue.sort((a, b) => a.priority - b.priority);

    return operation.id;
  }

  // Offline change management

  async queueOfflineChange(changeType, data, options = {}) {
    const change = {
      id: this.generateId(),
      type: changeType,
      data: data,
      timestamp: Date.now(),
      deviceId: this.deviceInfo.deviceId,
      options: options,
    };

    this.offlineChanges.push(change);
    await this.saveOfflineChanges();

    console.log("SyncService: Queued offline change:", change.id);
    return change.id;
  }

  async processOfflineChanges() {
    if (!this.isOnline || this.offlineChanges.length === 0) {
      return { processed: 0, conflicts: 0, failed: 0 };
    }

    try {
      const response = await this.apiCall("/sync/offline-changes", "POST", {
        changes: this.offlineChanges,
      });

      if (response.success) {
        const result = response.processing_result;

        // Clear processed changes
        this.offlineChanges = [];
        await this.saveOfflineChanges();

        // Handle any conflicts
        if (result.conflict_details && result.conflict_details.length > 0) {
          await this.handleOfflineConflicts(result.conflict_details);
        }

        this.notifyListeners("offline_changes_processed", result);
        return result;
      }

      throw new Error("Failed to process offline changes");
    } catch (error) {
      console.error("SyncService: Failed to process offline changes:", error);
      throw error;
    }
  }

  // Conflict resolution

  async handleConflicts(conflicts) {
    for (const conflict of conflicts) {
      try {
        const resolution = await this.resolveConflict(conflict);

        if (resolution) {
          await this.apiCall("/sync/resolve-conflict", "POST", {
            conflict_id: conflict.id,
            resolution_strategy: resolution.strategy,
            resolved_value: resolution.value,
          });
        }
      } catch (error) {
        console.error("SyncService: Failed to resolve conflict:", error);
      }
    }
  }

  async resolveConflict(conflict) {
    // Check for custom conflict handler
    const handler = this.conflictHandlers.get(conflict.field_name);
    if (handler) {
      return await handler(conflict);
    }

    // Default resolution strategies
    switch (conflict.conflict_type) {
      case "value_conflict":
        // Latest wins by default
        return {
          strategy: "latest_wins",
          value: conflict.client_value,
        };

      case "object_merge":
        // Merge objects
        return {
          strategy: "merge",
          value: { ...conflict.server_value, ...conflict.client_value },
        };

      case "array_merge":
        // Merge arrays and remove duplicates
        const merged = [...conflict.server_value, ...conflict.client_value];
        return {
          strategy: "merge",
          value: [...new Set(merged)],
        };

      default:
        // Require user intervention
        return await this.requestUserResolution(conflict);
    }
  }

  registerConflictHandler(fieldName, handler) {
    this.conflictHandlers.set(fieldName, handler);
  }

  async requestUserResolution(conflict) {
    // This would typically show a UI dialog
    // For now, return a default resolution
    return {
      strategy: "user_choice",
      value: conflict.client_value,
    };
  }

  // Bandwidth optimization

  async optimizeDataForSync(data) {
    if (this.bandwidthProfile === "high") {
      return data;
    }

    try {
      const response = await this.apiCall("/sync/optimize-data", "POST", {
        data: data,
        bandwidth_profile: this.bandwidthProfile,
      });

      return response.success ? response.optimized_data : data;
    } catch (error) {
      console.error("SyncService: Data optimization failed:", error);
      return data;
    }
  }

  detectBandwidthProfile() {
    // Check connection information if available
    if (navigator.connection) {
      const connection = navigator.connection;

      if (
        connection.effectiveType === "slow-2g" ||
        connection.effectiveType === "2g"
      ) {
        return "low";
      } else if (connection.effectiveType === "3g") {
        return "medium";
      }
    }

    // Check if mobile device
    if (this.deviceInfo.platform === "mobile") {
      return "low";
    }

    return "high";
  }

  // Device detection

  detectDeviceInfo() {
    const userAgent = navigator.userAgent;
    const platform = this.detectPlatform();

    return {
      platform: platform,
      browser: this.detectBrowser(),
      version: this.detectVersion(),
      user_agent: userAgent,
      screen_resolution: `${screen.width}x${screen.height}`,
      connection: navigator.connection
        ? {
            effectiveType: navigator.connection.effectiveType,
            downlink: navigator.connection.downlink,
            rtt: navigator.connection.rtt,
          }
        : null,
      deviceId: this.generateDeviceId(),
    };
  }

  detectPlatform() {
    const userAgent = navigator.userAgent.toLowerCase();

    if (/android/.test(userAgent)) return "android";
    if (/iphone|ipad|ipod/.test(userAgent)) return "ios";
    if (/mobile/.test(userAgent)) return "mobile";
    if (window.electron) return "desktop";

    return "web";
  }

  detectBrowser() {
    const userAgent = navigator.userAgent;

    if (userAgent.includes("Chrome")) return "chrome";
    if (userAgent.includes("Firefox")) return "firefox";
    if (userAgent.includes("Safari")) return "safari";
    if (userAgent.includes("Edge")) return "edge";

    return "unknown";
  }

  detectVersion() {
    // Extract browser/app version
    const userAgent = navigator.userAgent;
    const match = userAgent.match(/(?:Chrome|Firefox|Safari|Edge)\/(\d+\.\d+)/);
    return match ? match[1] : "unknown";
  }

  generateDeviceId() {
    // Generate a consistent device ID based on device characteristics
    const characteristics = [
      navigator.userAgent,
      screen.width,
      screen.height,
      navigator.language,
      Intl.DateTimeFormat().resolvedOptions().timeZone,
    ].join("|");

    return this.hashString(characteristics).substring(0, 16);
  }

  // WebSocket for real-time sync

  async setupSyncWebSocket() {
    if (!this.currentSession) return;

    try {
      const wsUrl = `ws://127.0.0.1:8000/api/v1/sync/ws/sync/${this.currentSession.session_id}`;
      this.syncWebSocket = new WebSocket(wsUrl);

      this.syncWebSocket.onopen = () => {
        console.log("SyncService: WebSocket connected");
      };

      this.syncWebSocket.onmessage = event => {
        try {
          const message = JSON.parse(event.data);
          this.handleSyncMessage(message);
        } catch (error) {
          console.error(
            "SyncService: Failed to parse WebSocket message:",
            error
          );
        }
      };

      this.syncWebSocket.onclose = () => {
        console.log("SyncService: WebSocket disconnected");
        // Attempt to reconnect after delay
        setTimeout(() => this.setupSyncWebSocket(), 5000);
      };

      this.syncWebSocket.onerror = error => {
        console.error("SyncService: WebSocket error:", error);
      };
    } catch (error) {
      console.error("SyncService: Failed to setup WebSocket:", error);
    }
  }

  closeSyncWebSocket() {
    if (this.syncWebSocket) {
      this.syncWebSocket.close();
      this.syncWebSocket = null;
    }
  }

  handleSyncMessage(message) {
    switch (message.type) {
      case "sync_update":
        this.notifyListeners("remote_sync_update", message.data);
        break;
      case "conflict_detected":
        this.notifyListeners("conflict_detected", message.data);
        break;
      case "session_terminated":
        this.handleSessionTermination();
        break;
      default:
        console.log("SyncService: Unknown message type:", message.type);
    }
  }

  // Event handling

  onOnline() {
    this.notifyListeners("online");

    // Process offline changes
    if (this.offlineChanges.length > 0) {
      this.processOfflineChanges().catch(console.error);
    }

    // Trigger sync
    this.triggerSync();
  }

  onOffline() {
    this.notifyListeners("offline");
  }

  async triggerSync() {
    if (!this.isOnline || this.syncInProgress || !this.currentSession) {
      return;
    }

    // Process any queued operations
    if (this.syncQueue.length > 0) {
      const operations = this.syncQueue.splice(0);

      for (const operation of operations) {
        try {
          await this.syncData(operation.data, { type: operation.type });
        } catch (error) {
          console.error("SyncService: Failed to sync queued operation:", error);
        }
      }
    }
  }

  // Listener management

  addSyncListener(listener) {
    this.syncListeners.add(listener);
  }

  removeSyncListener(listener) {
    this.syncListeners.delete(listener);
  }

  notifyListeners(event, data) {
    this.syncListeners.forEach(listener => {
      try {
        listener(event, data);
      } catch (error) {
        console.error("SyncService: Listener error:", error);
      }
    });
  }

  // Offline storage

  async initOfflineStorage() {
    if ("indexedDB" in window) {
      return new Promise((resolve, reject) => {
        const request = indexedDB.open("StorySignSync", 1);

        request.onerror = () => reject(request.error);

        request.onsuccess = () => {
          this.db = request.result;
          resolve();
        };

        request.onupgradeneeded = () => {
          const db = request.result;

          if (!db.objectStoreNames.contains("offline_changes")) {
            db.createObjectStore("offline_changes", { keyPath: "id" });
          }

          if (!db.objectStoreNames.contains("sync_data")) {
            db.createObjectStore("sync_data", { keyPath: "key" });
          }
        };
      });
    }
  }

  async saveOfflineChanges() {
    if (!this.db) return;

    try {
      const transaction = this.db.transaction(["offline_changes"], "readwrite");
      const store = transaction.objectStore("offline_changes");

      // Clear existing changes
      await store.clear();

      // Save current changes
      for (const change of this.offlineChanges) {
        await store.add(change);
      }
    } catch (error) {
      console.error("SyncService: Failed to save offline changes:", error);
    }
  }

  async loadOfflineChanges() {
    if (!this.db) return;

    try {
      const transaction = this.db.transaction(["offline_changes"], "readonly");
      const store = transaction.objectStore("offline_changes");
      const request = store.getAll();

      request.onsuccess = () => {
        this.offlineChanges = request.result || [];
        console.log(
          `SyncService: Loaded ${this.offlineChanges.length} offline changes`
        );
      };
    } catch (error) {
      console.error("SyncService: Failed to load offline changes:", error);
    }
  }

  // Utility methods

  async apiCall(endpoint, method = "GET", body = null, params = null) {
    const url = new URL(`${API_BASE_URL}/api/v1${endpoint}`);

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        url.searchParams.append(key, value);
      });
    }

    const options = {
      method,
      headers: {
        "Content-Type": "application/json",
      },
    };

    // Add auth token if available
    const token = localStorage.getItem("auth_token");
    if (token) {
      options.headers.Authorization = `Bearer ${token}`;
    }

    if (body) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);

    if (!response.ok) {
      throw new Error(
        `API call failed: ${response.status} ${response.statusText}`
      );
    }

    return await response.json();
  }

  generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  calculateChecksum(data) {
    // Simple checksum calculation
    const str = JSON.stringify(data);
    let hash = 0;

    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash; // Convert to 32-bit integer
    }

    return hash.toString(16);
  }

  hashString(str) {
    let hash = 0;

    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash;
    }

    return Math.abs(hash).toString(16);
  }

  isNetworkError(error) {
    return (
      error.message.includes("fetch") ||
      error.message.includes("network") ||
      error.message.includes("connection")
    );
  }

  handleSessionTermination() {
    this.currentSession = null;
    this.closeSyncWebSocket();
    this.notifyListeners("session_terminated");
  }

  // Public API

  getStatus() {
    return {
      isOnline: this.isOnline,
      hasActiveSession: !!this.currentSession,
      syncInProgress: this.syncInProgress,
      offlineChangesCount: this.offlineChanges.length,
      queuedOperationsCount: this.syncQueue.length,
      deviceInfo: this.deviceInfo,
      bandwidthProfile: this.bandwidthProfile,
    };
  }

  async getSyncMetrics(days = 7) {
    try {
      const response = await this.apiCall("/sync/metrics", "GET", null, {
        days,
      });
      return response.success ? response.metrics : null;
    } catch (error) {
      console.error("SyncService: Failed to get metrics:", error);
      return null;
    }
  }

  destroy() {
    this.closeSyncWebSocket();
    this.syncListeners.clear();
    this.conflictHandlers.clear();

    if (this.db) {
      this.db.close();
    }
  }
}

// Create singleton instance
const syncService = new SyncService();

export default syncService;
