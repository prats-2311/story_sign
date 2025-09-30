/**
 * Module System Tests
 *
 * Basic tests for the module interface standard and module manager.
 */

import { ModuleManager } from "./ModuleManager";
import { ASLWorldModuleInterface } from "../modules/asl_world/ASLWorldModuleInterface";
import { MockDatabaseService } from "../services/MockDatabaseService";
import { MockAnalyticsService } from "../services/MockAnalyticsService";
import { MockPluginService } from "../services/MockPluginService";
import { MockRealtimeService } from "../services/MockRealtimeService";
import { PlatformServiceImpl } from "../services/PlatformServiceImpl";
import { ModuleState, Permission } from "../types/module";

describe("Module System", () => {
  let moduleManager;
  let aslWorldModule;
  let mockServices;

  beforeEach(() => {
    // Create mock services
    mockServices = {
      database: new MockDatabaseService(),
      analytics: new MockAnalyticsService(),
      plugins: new MockPluginService(),
      realtime: new MockRealtimeService(),
      platform: new PlatformServiceImpl(),
    };

    // Create module manager
    moduleManager = new ModuleManager(
      mockServices.database,
      mockServices.analytics,
      mockServices.plugins,
      mockServices.realtime,
      mockServices.platform
    );

    // Create ASL World module
    aslWorldModule = new ASLWorldModuleInterface();
  });

  afterEach(() => {
    // Cleanup
    jest.clearAllMocks();
  });

  describe("Module Interface", () => {
    test("should have valid metadata", () => {
      expect(aslWorldModule.metadata).toBeDefined();
      expect(aslWorldModule.metadata.id).toBe("asl-world");
      expect(aslWorldModule.metadata.name).toBe("ASL World");
      expect(aslWorldModule.metadata.version).toBe("1.0.0");
      expect(Array.isArray(aslWorldModule.metadata.dependencies)).toBe(true);
      expect(Array.isArray(aslWorldModule.metadata.permissions)).toBe(true);
    });

    test("should start in uninitialized state", () => {
      expect(aslWorldModule.state).toBe(ModuleState.UNINITIALIZED);
    });

    test("should have default configuration", () => {
      expect(aslWorldModule.config).toBeDefined();
      expect(aslWorldModule.config.enabled).toBe(true);
      expect(aslWorldModule.config.permissions).toContain(
        Permission.READ_OWN_DATA
      );
    });
  });

  describe("Module Manager", () => {
    test("should register a module successfully", async () => {
      const registration = {
        module: aslWorldModule,
        priority: 0,
        autoStart: false,
        dependencies: aslWorldModule.metadata.dependencies,
      };

      await moduleManager.registerModule(registration);

      const retrievedModule = moduleManager.getModule("asl-world");
      expect(retrievedModule).toBe(aslWorldModule);
    });

    test("should prevent duplicate module registration", async () => {
      const registration = {
        module: aslWorldModule,
        priority: 0,
        autoStart: false,
        dependencies: aslWorldModule.metadata.dependencies,
      };

      await moduleManager.registerModule(registration);

      await expect(moduleManager.registerModule(registration)).rejects.toThrow(
        "Module asl-world is already registered"
      );
    });

    test("should initialize a module", async () => {
      const registration = {
        module: aslWorldModule,
        priority: 0,
        autoStart: false,
        dependencies: aslWorldModule.metadata.dependencies,
      };

      await moduleManager.registerModule(registration);
      await moduleManager.initializeModule("asl-world");

      expect(aslWorldModule.state).toBe(ModuleState.READY);
    });

    test("should get modules by state", async () => {
      const registration = {
        module: aslWorldModule,
        priority: 0,
        autoStart: false,
        dependencies: aslWorldModule.metadata.dependencies,
      };

      await moduleManager.registerModule(registration);

      let uninitializedModules = moduleManager.getModulesByState(
        ModuleState.UNINITIALIZED
      );
      expect(uninitializedModules).toHaveLength(1);

      await moduleManager.initializeModule("asl-world");

      let readyModules = moduleManager.getModulesByState(ModuleState.READY);
      expect(readyModules).toHaveLength(1);

      uninitializedModules = moduleManager.getModulesByState(
        ModuleState.UNINITIALIZED
      );
      expect(uninitializedModules).toHaveLength(0);
    });
  });

  describe("Data Access", () => {
    beforeEach(async () => {
      const registration = {
        module: aslWorldModule,
        priority: 0,
        autoStart: false,
        dependencies: aslWorldModule.metadata.dependencies,
      };

      await moduleManager.registerModule(registration);
      await moduleManager.initializeModule("asl-world");
    });

    test("should save and retrieve user data", async () => {
      const testUserId = "test-user-123";
      const testData = {
        practiceHistory: [],
        preferences: { preferredDifficulty: "normal" },
        progress: { totalPracticeTime: 0 },
        achievements: [],
      };

      await aslWorldModule.saveUserData(testUserId, testData);
      const retrievedData = await aslWorldModule.getUserData(testUserId);

      expect(retrievedData).toBeDefined();
      expect(retrievedData.preferences.preferredDifficulty).toBe("normal");
    });

    test("should return default data for new users", async () => {
      const testUserId = "new-user-456";
      const userData = await aslWorldModule.getUserData(testUserId);

      expect(userData).toBeDefined();
      expect(userData.practiceHistory).toEqual([]);
      expect(userData.preferences).toBeDefined();
      expect(userData.progress).toBeDefined();
      expect(userData.achievements).toEqual([]);
    });
  });
});

describe("Mock Services", () => {
  describe("MockDatabaseService", () => {
    let database;

    beforeEach(() => {
      database = new MockDatabaseService();
    });

    test("should save and retrieve user data", async () => {
      const userId = "test-user";
      const dataType = "preferences";
      const data = { theme: "dark", language: "en" };

      await database.saveUserData(userId, dataType, data);
      const retrieved = await database.getUserData(userId, dataType);

      expect(retrieved).toMatchObject(data);
      expect(retrieved.lastUpdated).toBeDefined();
    });

    test("should create and retrieve sessions", async () => {
      const sessionData = {
        userId: "test-user",
        type: "practice",
        data: { story: "test" },
      };

      const sessionId = await database.createSession(sessionData);
      const retrieved = await database.getSession(sessionId);

      expect(retrieved).toMatchObject(sessionData);
      expect(retrieved.id).toBe(sessionId);
    });

    test("should search content", async () => {
      const results = await database.searchContent({
        type: "story",
        difficulty: "amateur",
      });

      expect(Array.isArray(results)).toBe(true);
      expect(results.length).toBeGreaterThan(0);
    });
  });

  describe("MockAnalyticsService", () => {
    let analytics;

    beforeEach(() => {
      analytics = new MockAnalyticsService();
    });

    test("should track events", () => {
      const event = {
        type: "test-event",
        moduleName: "test-module",
        eventData: { key: "value" },
        timestamp: new Date().toISOString(),
      };

      analytics.trackEvent(event);

      const allEvents = analytics.getAllEvents();
      expect(allEvents).toHaveLength(1);
      expect(allEvents[0]).toMatchObject(event);
    });

    test("should track user actions", () => {
      analytics.trackUserAction("button-click", { button: "submit" });

      const actions = analytics.getAllUserActions();
      expect(actions).toHaveLength(1);
      expect(actions[0].action).toBe("button-click");
    });

    test("should query analytics data", async () => {
      // Add some test events
      analytics.trackEvent({
        type: "test-event",
        moduleName: "test-module",
        eventData: { value: 10 },
        timestamp: new Date().toISOString(),
      });

      const result = await analytics.getAnalytics({
        eventType: "test-event",
        aggregation: "count",
      });

      expect(result.aggregation).toBe("count");
      expect(result.value).toBe(1);
    });
  });
});
