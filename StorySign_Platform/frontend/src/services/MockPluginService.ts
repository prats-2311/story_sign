/**
 * Mock Plugin Service
 *
 * Provides a mock implementation of the PluginService interface
 * for development and testing purposes.
 */

import {
  PluginService,
  PluginInfo,
  Plugin,
  HookHandler,
} from "../types/module";

export class MockPluginService implements PluginService {
  private availablePlugins: Map<string, PluginInfo> = new Map();
  private loadedPlugins: Map<string, Plugin> = new Map();
  private hooks: Map<string, HookHandler[]> = new Map();

  constructor() {
    this.initializeMockPlugins();
    console.log("MockPluginService: Initialized");
  }

  async getAvailablePlugins(): Promise<PluginInfo[]> {
    const plugins = Array.from(this.availablePlugins.values());
    console.log("MockPlugins: Available plugins:", plugins);
    return plugins;
  }

  async loadPlugin(pluginId: string): Promise<Plugin> {
    const pluginInfo = this.availablePlugins.get(pluginId);
    if (!pluginInfo) {
      throw new Error(`Plugin ${pluginId} not found`);
    }

    if (this.loadedPlugins.has(pluginId)) {
      console.log(`MockPlugins: Plugin ${pluginId} already loaded`);
      return this.loadedPlugins.get(pluginId)!;
    }

    console.log(`MockPlugins: Loading plugin ${pluginId}...`);

    // Simulate loading time
    await new Promise((resolve) => setTimeout(resolve, 500));

    // Create mock plugin
    const plugin: Plugin = {
      info: { ...pluginInfo, isLoaded: true },
      hooks: this.createMockHooks(pluginId),
      components: [], // Mock components would go here
      services: [], // Mock services would go here
    };

    this.loadedPlugins.set(pluginId, plugin);

    // Register plugin hooks
    plugin.hooks.forEach((hook) => {
      this.registerHook(hook.target, hook.handler);
    });

    console.log(`MockPlugins: Plugin ${pluginId} loaded successfully`);
    return plugin;
  }

  async unloadPlugin(pluginId: string): Promise<void> {
    const plugin = this.loadedPlugins.get(pluginId);
    if (!plugin) {
      console.log(`MockPlugins: Plugin ${pluginId} not loaded`);
      return;
    }

    console.log(`MockPlugins: Unloading plugin ${pluginId}...`);

    // Unregister hooks
    plugin.hooks.forEach((hook) => {
      this.unregisterHook(hook.target, hook.handler);
    });

    // Remove from loaded plugins
    this.loadedPlugins.delete(pluginId);

    // Update plugin info
    const pluginInfo = this.availablePlugins.get(pluginId);
    if (pluginInfo) {
      pluginInfo.isLoaded = false;
    }

    console.log(`MockPlugins: Plugin ${pluginId} unloaded successfully`);
  }

  async executeHook(hookName: string, context: any): Promise<any> {
    const handlers = this.hooks.get(hookName) || [];

    if (handlers.length === 0) {
      console.log(`MockPlugins: No handlers for hook ${hookName}`);
      return context;
    }

    console.log(
      `MockPlugins: Executing ${handlers.length} handlers for hook ${hookName}`
    );

    let result = context;

    for (const handler of handlers) {
      try {
        result = await handler(result);
      } catch (error) {
        console.error(
          `MockPlugins: Hook handler failed for ${hookName}:`,
          error
        );
      }
    }

    return result;
  }

  registerHook(hookName: string, handler: HookHandler): void {
    if (!this.hooks.has(hookName)) {
      this.hooks.set(hookName, []);
    }

    this.hooks.get(hookName)!.push(handler);
    console.log(`MockPlugins: Registered hook handler for ${hookName}`);
  }

  // Additional methods for testing and development
  public getAllLoadedPlugins(): Plugin[] {
    return Array.from(this.loadedPlugins.values());
  }

  public getLoadedPlugin(pluginId: string): Plugin | null {
    return this.loadedPlugins.get(pluginId) || null;
  }

  public getAllHooks(): Map<string, HookHandler[]> {
    return new Map(this.hooks);
  }

  public getHookHandlers(hookName: string): HookHandler[] {
    return this.hooks.get(hookName) || [];
  }

  public clearAllPlugins(): void {
    this.loadedPlugins.clear();
    this.hooks.clear();
    this.availablePlugins.forEach((plugin) => {
      plugin.isLoaded = false;
    });
    console.log("MockPlugins: All plugins cleared");
  }

  private unregisterHook(hookName: string, handler: HookHandler): void {
    const handlers = this.hooks.get(hookName);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
        console.log(`MockPlugins: Unregistered hook handler for ${hookName}`);
      }
    }
  }

  private initializeMockPlugins(): void {
    const mockPlugins: PluginInfo[] = [
      {
        id: "gesture-enhancer",
        name: "Gesture Enhancer",
        version: "1.0.0",
        description: "Enhances gesture recognition with additional algorithms",
        isLoaded: false,
        permissions: ["read:own_data", "view:analytics"],
      },
      {
        id: "progress-tracker",
        name: "Advanced Progress Tracker",
        version: "2.1.0",
        description: "Provides detailed progress tracking and analytics",
        isLoaded: false,
        permissions: ["read:own_data", "write:own_data", "view:analytics"],
      },
      {
        id: "social-features",
        name: "Social Learning Features",
        version: "1.5.0",
        description: "Adds social learning and collaboration features",
        isLoaded: false,
        permissions: ["read:own_data", "write:own_data", "create:content"],
      },
      {
        id: "accessibility-helper",
        name: "Accessibility Helper",
        version: "1.2.0",
        description: "Improves accessibility for users with disabilities",
        isLoaded: false,
        permissions: ["read:own_data"],
      },
      {
        id: "custom-themes",
        name: "Custom Themes",
        version: "1.0.0",
        description: "Allows users to create and share custom themes",
        isLoaded: false,
        permissions: ["read:own_data", "write:own_data"],
      },
    ];

    mockPlugins.forEach((plugin) => {
      this.availablePlugins.set(plugin.id, plugin);
    });

    console.log("MockPlugins: Initialized with mock plugins");
  }

  private createMockHooks(pluginId: string): any[] {
    // Create different hooks based on plugin type
    switch (pluginId) {
      case "gesture-enhancer":
        return [
          {
            type: "before",
            target: "asl-world.gesture.analyze",
            handler: async (context: any) => {
              console.log(
                `MockPlugin(${pluginId}): Enhancing gesture analysis`
              );
              return { ...context, enhanced: true };
            },
          },
        ];

      case "progress-tracker":
        return [
          {
            type: "after",
            target: "asl-world.sentence.completed",
            handler: async (context: any) => {
              console.log(
                `MockPlugin(${pluginId}): Tracking detailed progress`
              );
              return { ...context, detailedTracking: true };
            },
          },
        ];

      case "social-features":
        return [
          {
            type: "after",
            target: "asl-world.practice-session.completed",
            handler: async (context: any) => {
              console.log(
                `MockPlugin(${pluginId}): Adding social sharing options`
              );
              return { ...context, socialSharing: true };
            },
          },
        ];

      case "accessibility-helper":
        return [
          {
            type: "before",
            target: "platform.render",
            handler: async (context: any) => {
              console.log(
                `MockPlugin(${pluginId}): Applying accessibility enhancements`
              );
              return { ...context, accessibilityEnhanced: true };
            },
          },
        ];

      case "custom-themes":
        return [
          {
            type: "before",
            target: "platform.theme.apply",
            handler: async (context: any) => {
              console.log(
                `MockPlugin(${pluginId}): Applying custom theme modifications`
              );
              return { ...context, customTheme: true };
            },
          },
        ];

      default:
        return [];
    }
  }
}

export default MockPluginService;
