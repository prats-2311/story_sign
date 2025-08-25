/**
 * Module System Tests
 *
 * Tests for the module interface standard, module manager, and context provider.
 */

// Jest test setup - using built-in Jest functions
import { ModuleManager } from "./ModuleManager";
import { ASLWorldModuleInterface } from "../modules/asl_world/ASLWorldModuleInterface";
import { MockDatabaseService } from "../services/MockDatabaseService";
import { MockAnalyticsService } from "../services/MockAnalyticsService";
import { MockPluginService } from "../services/MockPluginService";
import { MockRealtimeService } from "../services/MockRealtimeService";
import { PlatformServiceImpl } from "../services/PlatformServiceImpl";
import { ModuleState, Permission } from "../types/module";

describe("Module System", () => {
  let moduleManager: ModuleManager;
  let aslWorldModule: ASLWorldModuleInterface;
  let mockServices: any;

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
    it("should have valid metadata", () => {
      expect(aslWorldModule.metadata).toBeDefined();
      expect(aslWorldModule.metadata.id).toBe("asl-world");
      expect(aslWorldModule.metadata.name).toBe("ASL World");
      expect(aslWorldModule.metadata.version).toBe("1.0.0");
      expect(Array.isArray(aslWorldModule.metadata.dependencies)).toBe(true);
      expect(Array.isArray(aslWorldModule.metadata.permissions)).toBe(true);
    });

    it("should start in uninitialized state", () => {
      expect(aslWorldModule.state).toBe(ModuleState.UNINITIALIZED);
    });

    it("should have default configuration", () => {
      expect(aslWorldModule.config).toBeDefined();
      expect(aslWorldModule.config.enabled).toBe(true);
      expect(aslWorldModule.config.permissions).toContain(
        Permission.READ_OWN_DATA
      );
    });
  });

  describe("Module Manager", () => {
    it("should register a module successfully", async () => {
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

    it("should prevent duplicate module registration", async () => {
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

    it("should initialize a module", async () => {
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

    it("should destroy a module", async () => {
      const registration = {
        module: aslWorldModule,
        priority: 0,
        autoStart: false,
        dependencies: aslWorldModule.metadata.dependencies,
      };

      await moduleManager.registerModule(registration);
      await moduleManager.initializeModule("asl-world");
      await moduleManager.destroyModule("asl-world");

      expect(aslWorldModule.state).toBe(ModuleState.DESTROYED);
    });

    it("should unregister a module", async () => {
      const registration = {
        module: aslWorldModule,
        priority: 0,
        autoStart: false,
        dependencies: aslWorldModule.metadata.dependencies,
      };

      await moduleManager.registerModule(registration);
      await moduleManager.unregisterModule("asl-world");

      const retrievedModule = moduleManager.getModule("asl-world");
      expect(retrievedModule).toBeNull();
    });

    it("should get modules by state", async () => {
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

  describe("Module Lifecycle", () => {
    beforeEach(async () => {
      const registration = {
        module: aslWorldModule,
        priority: 0,
        autoStart: false,
        dependencies: aslWorldModule.metadata.dependencies,
      };

      await moduleManager.registerModule(registration);
    });

    it("should initialize module with context", async () => {
      await moduleManager.initializeModule("asl-world");

      expect(aslWorldModule.state).toBe(ModuleState.READY);
      expect(aslWorldModule.context).toBeDefined();
      expect(aslWorldModule.context?.database).toBe(mockServices.database);
      expect(aslWorldModule.context?.analytics).toBe(mockServices.analytics);
    });

    it("should track analytics events during initialization", async () => {
      const trackEventSpy = vi.spyOn(mockServices.analytics, "trackEvent");

      await moduleManager.initializeModule("asl-world");

      expect(trackEventSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "module_initialized",
          moduleName: "asl-world",
        })
      );
    });

    it("should handle initialization errors", async () => {
      // Mock an initialization error
      const originalOnInitialize = aslWorldModule["onInitialize"];
      aslWorldModule["onInitialize"] = vi
        .fn()
        .mockRejectedValue(new Error("Test error"));

      await expect(moduleManager.initializeModule("asl-world")).rejects.toThrow(
        "Test error"
      );

      expect(aslWorldModule.state).toBe(ModuleState.ERROR);

      // Restore original method
      aslWorldModule["onInitialize"] = originalOnInitialize;
    });

    it("should perform health checks", async () => {
      await moduleManager.initializeModule("asl-world");

      const health = await aslWorldModule.healthCheck();

      expect(health).toBeDefined();
      expect(typeof health.healthy).toBe("boolean");
      expect(Array.isArray(health.issues)).toBe(true);
      expect(health.lastChecked).toBeDefined();
      expect(health.performance).toBeDefined();
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

    it("should save and retrieve user data", async () => {
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

    it("should return default data for new users", async () => {
      const testUserId = "new-user-456";
      const userData = await aslWorldModule.getUserData(testUserId);

      expect(userData).toBeDefined();
      expect(userData.practiceHistory).toEqual([]);
      expect(userData.preferences).toBeDefined();
      expect(userData.progress).toBeDefined();
      expect(userData.achievements).toEqual([]);
    });

    it("should track data access events", async () => {
      const trackEventSpy = vi.spyOn(mockServices.analytics, "trackEvent");
      const testUserId = "test-user-789";

      await aslWorldModule.getUserData(testUserId);

      expect(trackEventSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "user_data_accessed",
          moduleName: "asl-world",
          userId: testUserId,
        })
      );
    });
  });

  describe("Practice Session Management", () => {
    beforeEach(async () => {
      const registration = {
        module: aslWorldModule,
        priority: 0,
        autoStart: false,
        dependencies: aslWorldModule.metadata.dependencies,
      };

      await moduleManager.registerModule(registration);
      await moduleManager.initializeModule("asl-world");

      // Set up mock user
      moduleManager.updateUserContext({
        id: "test-user",
        email: "test@example.com",
        username: "testuser",
        role: "learner",
        preferences: {},
      });
    });

    it("should start a practice session", async () => {
      const storyData = {
        id: "test-story",
        title: "Test Story",
        difficulty: "normal",
        sentences: ["Hello", "World"],
      };

      const sessionId = await aslWorldModule.startPracticeSession(storyData);

      expect(sessionId).toBeDefined();
      expect(typeof sessionId).toBe("string");
    });

    it("should end a practice session", async () => {
      const storyData = {
        id: "test-story",
        title: "Test Story",
        difficulty: "normal",
        sentences: ["Hello", "World"],
      };

      const sessionId = await aslWorldModule.startPracticeSession(storyData);
      await aslWorldModule.endPracticeSession();

      // Session should be ended (no active session)
      expect(aslWorldModule["practiceSessionId"]).toBeNull();
    });

    it("should track session events", async () => {
      const trackEventSpy = vi.spyOn(mockServices.analytics, "trackEvent");
      const storyData = {
        id: "test-story",
        title: "Test Story",
        difficulty: "normal",
        sentences: ["Hello", "World"],
      };

      await aslWorldModule.startPracticeSession(storyData);

      expect(trackEventSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "practice_session_started",
          moduleName: "asl-world",
        })
      );
    });
  });

  describe("Component Rendering", () => {
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

    it("should render component with props", () => {
      const props = {
        connectionStatus: "connected",
        storyData: { title: "Test Story" },
      };

      const component = aslWorldModule.renderComponent(props);

      expect(component).toBeDefined();
      // Note: In a real test environment, you would use React Testing Library
      // to verify the component renders correctly
    });

    it("should update module props", () => {
      const newProps = {
        connectionStatus: "connected",
        isGeneratingStory: true,
      };

      aslWorldModule.updateProps(newProps);

      // Verify props were updated (this would be tested more thoroughly
      // in integration tests with actual component rendering)
      expect(aslWorldModule["moduleProps"]).toMatchObject(newProps);
    });
  });

  describe("Plugin Integration", () => {
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

    it("should register plugin hooks", () => {
      const hooks = [
        {
          type: "before" as const,
          target: "test-hook",
          handler: async (context: any) => context,
        },
      ];

      aslWorldModule.registerPluginHooks(hooks);

      // Verify hooks were registered with the plugin service
      const registeredHooks = mockServices.plugins.getHookHandlers("test-hook");
      expect(registeredHooks).toHaveLength(1);
    });

    it("should track plugin hook registration", () => {
      const trackEventSpy = vi.spyOn(mockServices.analytics, "trackEvent");
      const hooks = [
        {
          type: "before" as const,
          target: "test-hook",
          handler: async (context: any) => context,
        },
      ];

      aslWorldModule.registerPluginHooks(hooks);

      expect(trackEventSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "plugin_hooks_registered",
          moduleName: "asl-world",
          eventData: { hookCount: 1 },
        })
      );
    });
  });
});

describe("Mock Services", () => {
  describe("MockDatabaseService", () => {
    let database: MockDatabaseService;

    beforeEach(() => {
      database = new MockDatabaseService();
    });

    it("should save and retrieve user data", async () => {
      const userId = "test-user";
      const dataType = "preferences";
      const data = { theme: "dark", language: "en" };

      await database.saveUserData(userId, dataType, data);
      const retrieved = await database.getUserData(userId, dataType);

      expect(retrieved).toMatchObject(data);
      expect(retrieved.lastUpdated).toBeDefined();
    });

    it("should create and retrieve sessions", async () => {
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

    it("should search content", async () => {
      const results = await database.searchContent({
        type: "story",
        difficulty: "amateur",
      });

      expect(Array.isArray(results)).toBe(true);
      expect(results.length).toBeGreaterThan(0);
    });
  });

  describe("MockAnalyticsService", () => {
    let analytics: MockAnalyticsService;

    beforeEach(() => {
      analytics = new MockAnalyticsService();
    });

    it("should track events", () => {
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

    it("should track user actions", () => {
      analytics.trackUserAction("button-click", { button: "submit" });

      const actions = analytics.getAllUserActions();
      expect(actions).toHaveLength(1);
      expect(actions[0].action).toBe("button-click");
    });

    it("should query analytics data", async () => {
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
