/**
 * Tests for SyncService
 */

import SyncService from "./SyncService";

// Mock fetch for testing
global.fetch = jest.fn();

// Mock WebSocket
global.WebSocket = jest.fn(() => ({
  addEventListener: jest.fn(),
  close: jest.fn(),
  send: jest.fn(),
}));

// Mock IndexedDB
global.indexedDB = {
  open: jest.fn(() => ({
    onsuccess: null,
    onerror: null,
    onupgradeneeded: null,
    result: {
      transaction: jest.fn(() => ({
        objectStore: jest.fn(() => ({
          add: jest.fn(),
          get: jest.fn(),
          getAll: jest.fn(() => ({ onsuccess: null })),
          clear: jest.fn(),
        })),
        oncomplete: null,
        onerror: null,
      })),
      objectStoreNames: {
        contains: jest.fn(() => false),
      },
      createObjectStore: jest.fn(),
    },
  })),
};

// Mock navigator
Object.defineProperty(navigator, "onLine", {
  writable: true,
  value: true,
});

Object.defineProperty(navigator, "userAgent", {
  writable: true,
  value: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
});

Object.defineProperty(navigator, "connection", {
  writable: true,
  value: {
    effectiveType: "4g",
    downlink: 10,
    rtt: 50,
  },
});

describe("SyncService", () => {
  let syncService;

  beforeEach(() => {
    // Create a new instance for each test
    syncService = new SyncService.constructor();

    // Reset mocks
    fetch.mockClear();

    // Mock successful API responses
    fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ success: true }),
    });
  });

  afterEach(() => {
    if (syncService) {
      syncService.destroy();
    }
  });

  describe("Device Detection", () => {
    test("should detect device information correctly", () => {
      const deviceInfo = syncService.detectDeviceInfo();

      expect(deviceInfo).toHaveProperty("platform");
      expect(deviceInfo).toHaveProperty("browser");
      expect(deviceInfo).toHaveProperty("user_agent");
      expect(deviceInfo).toHaveProperty("deviceId");
      expect(deviceInfo.deviceId).toHaveLength(16);
    });

    test("should detect platform correctly", () => {
      const platform = syncService.detectPlatform();
      expect(["web", "android", "ios", "mobile", "desktop"]).toContain(
        platform
      );
    });

    test("should detect browser correctly", () => {
      const browser = syncService.detectBrowser();
      expect(["chrome", "firefox", "safari", "edge", "unknown"]).toContain(
        browser
      );
    });

    test("should generate consistent device ID", () => {
      const deviceInfo = { platform: "web", browser: "chrome" };
      const id1 = syncService.generateDeviceId();
      const id2 = syncService.generateDeviceId();

      expect(id1).toBe(id2);
      expect(id1).toHaveLength(16);
    });
  });

  describe("Bandwidth Detection", () => {
    test("should detect high bandwidth for desktop", () => {
      navigator.connection.effectiveType = "4g";
      const profile = syncService.detectBandwidthProfile();
      expect(profile).toBe("high");
    });

    test("should detect low bandwidth for slow connections", () => {
      navigator.connection.effectiveType = "2g";
      const profile = syncService.detectBandwidthProfile();
      expect(profile).toBe("low");
    });

    test("should detect medium bandwidth for 3g", () => {
      navigator.connection.effectiveType = "3g";
      const profile = syncService.detectBandwidthProfile();
      expect(profile).toBe("medium");
    });
  });

  describe("Offline Queue Management", () => {
    test("should queue offline changes", async () => {
      const changeId = await syncService.queueOfflineChange("sync", {
        test: "data",
      });

      expect(changeId).toBeDefined();
      expect(syncService.offlineChanges).toHaveLength(1);
      expect(syncService.offlineChanges[0]).toMatchObject({
        id: changeId,
        type: "sync",
        data: { test: "data" },
      });
    });

    test("should queue sync operations", async () => {
      const operationId = await syncService.queueSyncOperation(
        "test_op",
        { data: "test" },
        1
      );

      expect(operationId).toBeDefined();
      expect(syncService.syncQueue).toHaveLength(1);
      expect(syncService.syncQueue[0]).toMatchObject({
        id: operationId,
        type: "test_op",
        data: { data: "test" },
        priority: 1,
      });
    });

    test("should sort operations by priority", async () => {
      await syncService.queueSyncOperation("low_priority", {}, 5);
      await syncService.queueSyncOperation("high_priority", {}, 1);
      await syncService.queueSyncOperation("medium_priority", {}, 3);

      expect(syncService.syncQueue).toHaveLength(3);
      expect(syncService.syncQueue[0].priority).toBe(1);
      expect(syncService.syncQueue[1].priority).toBe(3);
      expect(syncService.syncQueue[2].priority).toBe(5);
    });
  });

  describe("Data Optimization", () => {
    test("should optimize data for low bandwidth", async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            success: true,
            optimized_data: { compressed: true },
          }),
      });

      const data = { large: "data", with: "lots", of: "content" };
      const optimized = await syncService.optimizeDataForSync(data);

      expect(optimized).toEqual({ compressed: true });
    });

    test("should return original data for high bandwidth", async () => {
      syncService.bandwidthProfile = "high";
      const data = { test: "data" };
      const optimized = await syncService.optimizeDataForSync(data);

      expect(optimized).toEqual(data);
    });
  });

  describe("Checksum Calculation", () => {
    test("should calculate consistent checksums", () => {
      const data = { key: "value", number: 123 };
      const checksum1 = syncService.calculateChecksum(data);
      const checksum2 = syncService.calculateChecksum(data);

      expect(checksum1).toBe(checksum2);
      expect(typeof checksum1).toBe("string");
    });

    test("should generate different checksums for different data", () => {
      const data1 = { key: "value1" };
      const data2 = { key: "value2" };

      const checksum1 = syncService.calculateChecksum(data1);
      const checksum2 = syncService.calculateChecksum(data2);

      expect(checksum1).not.toBe(checksum2);
    });
  });

  describe("Status Management", () => {
    test("should return correct status", () => {
      const status = syncService.getStatus();

      expect(status).toHaveProperty("isOnline");
      expect(status).toHaveProperty("hasActiveSession");
      expect(status).toHaveProperty("syncInProgress");
      expect(status).toHaveProperty("offlineChangesCount");
      expect(status).toHaveProperty("queuedOperationsCount");
      expect(status).toHaveProperty("deviceInfo");
      expect(status).toHaveProperty("bandwidthProfile");
    });

    test("should track online/offline status", () => {
      expect(syncService.isOnline).toBe(true);

      // Simulate going offline
      syncService.isOnline = false;
      const status = syncService.getStatus();
      expect(status.isOnline).toBe(false);
    });
  });

  describe("Event Listeners", () => {
    test("should add and remove sync listeners", () => {
      const listener = jest.fn();

      syncService.addSyncListener(listener);
      expect(syncService.syncListeners.has(listener)).toBe(true);

      syncService.removeSyncListener(listener);
      expect(syncService.syncListeners.has(listener)).toBe(false);
    });

    test("should notify listeners of events", () => {
      const listener = jest.fn();
      syncService.addSyncListener(listener);

      syncService.notifyListeners("test_event", { data: "test" });

      expect(listener).toHaveBeenCalledWith("test_event", { data: "test" });
    });

    test("should handle listener errors gracefully", () => {
      const errorListener = jest.fn(() => {
        throw new Error("Listener error");
      });
      const goodListener = jest.fn();

      syncService.addSyncListener(errorListener);
      syncService.addSyncListener(goodListener);

      // Should not throw
      expect(() => {
        syncService.notifyListeners("test_event", {});
      }).not.toThrow();

      expect(goodListener).toHaveBeenCalled();
    });
  });

  describe("API Calls", () => {
    test("should make API calls with correct parameters", async () => {
      const mockResponse = { success: true, data: "test" };
      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await syncService.apiCall("/test", "POST", {
        test: "data",
      });

      expect(fetch).toHaveBeenCalledWith(
        expect.any(URL),
        expect.objectContaining({
          method: "POST",
          headers: expect.objectContaining({
            "Content-Type": "application/json",
          }),
          body: JSON.stringify({ test: "data" }),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    test("should handle API errors", async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: "Internal Server Error",
      });

      await expect(syncService.apiCall("/test")).rejects.toThrow(
        "API call failed: 500 Internal Server Error"
      );
    });

    test("should include auth token when available", async () => {
      localStorage.setItem("auth_token", "test-token");

      fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true }),
      });

      await syncService.apiCall("/test");

      expect(fetch).toHaveBeenCalledWith(
        expect.any(URL),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: "Bearer test-token",
          }),
        })
      );

      localStorage.removeItem("auth_token");
    });
  });

  describe("Utility Functions", () => {
    test("should generate unique IDs", () => {
      const id1 = syncService.generateId();
      const id2 = syncService.generateId();

      expect(id1).not.toBe(id2);
      expect(typeof id1).toBe("string");
      expect(id1.length).toBeGreaterThan(0);
    });

    test("should hash strings consistently", () => {
      const str = "test string";
      const hash1 = syncService.hashString(str);
      const hash2 = syncService.hashString(str);

      expect(hash1).toBe(hash2);
      expect(typeof hash1).toBe("string");
    });

    test("should identify network errors", () => {
      const networkError = new Error("fetch failed");
      const otherError = new Error("validation failed");

      expect(syncService.isNetworkError(networkError)).toBe(true);
      expect(syncService.isNetworkError(otherError)).toBe(false);
    });
  });
});

describe("SyncService Integration", () => {
  let syncService;

  beforeEach(() => {
    syncService = new SyncService.constructor();
  });

  afterEach(() => {
    if (syncService) {
      syncService.destroy();
    }
  });

  test("should handle complete sync workflow", async () => {
    // Mock successful session creation
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          success: true,
          session: {
            session_id: "test-session",
            sync_version: 1,
          },
        }),
    });

    // Create session
    const session = await syncService.createSession({ test: "data" });
    expect(session.session_id).toBe("test-session");

    // Mock successful sync
    fetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          success: true,
          sync_result: {
            status: "completed",
            sync_version: 2,
            conflicts: [],
          },
        }),
    });

    // Sync data
    const result = await syncService.syncData({ updated: "data" });
    expect(result.status).toBe("completed");
    expect(result.sync_version).toBe(2);
  });

  test("should handle offline mode gracefully", async () => {
    syncService.isOnline = false;

    // Should queue operation instead of making API call
    const changeId = await syncService.syncData({ offline: "data" });

    expect(changeId).toBeDefined();
    expect(syncService.offlineChanges).toHaveLength(1);
  });
});
