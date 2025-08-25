/**
 * Module Manager
 *
 * Manages the lifecycle of all platform modules, including registration,
 * initialization, dependency resolution, and cleanup.
 */

import {
  ModuleManager as IModuleManager,
  ModuleInterface,
  ModuleRegistration,
  ModuleState,
  ModuleContext,
  DatabaseService,
  AnalyticsService,
  PluginService,
  RealtimeService,
  PlatformService,
} from "../types/module";

export class ModuleManager implements IModuleManager {
  private modules: Map<string, ModuleInterface> = new Map();
  private registrations: Map<string, ModuleRegistration> = new Map();
  private initializationOrder: string[] = [];
  private context: ModuleContext;

  constructor(
    database: DatabaseService,
    analytics: AnalyticsService,
    plugins: PluginService,
    realtime: RealtimeService,
    platform: PlatformService
  ) {
    this.context = {
      user: null, // Will be set when user logs in
      database,
      analytics,
      plugins,
      realtime,
      platform,
    };
  }

  // Update user context when authentication state changes
  public updateUserContext(user: any): void {
    this.context = { ...this.context, user };

    // Notify all initialized modules of user context change
    this.modules.forEach(async (module) => {
      if (module.state === ModuleState.READY) {
        try {
          // Re-initialize modules that depend on user context
          if (module.metadata.permissions.length > 0) {
            await module.cleanup();
            await module.initialize(this.context);
          }
        } catch (error) {
          console.error(
            `Failed to update user context for module ${module.metadata.id}:`,
            error
          );
        }
      }
    });
  }

  // Module registration
  async registerModule(registration: ModuleRegistration): Promise<void> {
    const moduleId = registration.module.metadata.id;

    if (this.modules.has(moduleId)) {
      throw new Error(`Module ${moduleId} is already registered`);
    }

    console.log(`Registering module: ${moduleId}`);

    // Validate module metadata
    this.validateModuleMetadata(registration.module);

    // Store registration and module
    this.registrations.set(moduleId, registration);
    this.modules.set(moduleId, registration.module);

    // Calculate initialization order based on dependencies
    this.calculateInitializationOrder();

    // Auto-start if configured
    if (registration.autoStart) {
      try {
        await this.initializeModule(moduleId);
      } catch (error) {
        console.error(`Failed to auto-start module ${moduleId}:`, error);
      }
    }

    console.log(`Module ${moduleId} registered successfully`);
  }

  async unregisterModule(moduleId: string): Promise<void> {
    const module = this.modules.get(moduleId);
    if (!module) {
      throw new Error(`Module ${moduleId} is not registered`);
    }

    console.log(`Unregistering module: ${moduleId}`);

    // Cleanup module if it's initialized
    if (module.state === ModuleState.READY) {
      await this.destroyModule(moduleId);
    }

    // Remove from collections
    this.modules.delete(moduleId);
    this.registrations.delete(moduleId);

    // Recalculate initialization order
    this.calculateInitializationOrder();

    console.log(`Module ${moduleId} unregistered successfully`);
  }

  // Module access
  getModule(moduleId: string): ModuleInterface | null {
    return this.modules.get(moduleId) || null;
  }

  getAllModules(): ModuleInterface[] {
    return Array.from(this.modules.values());
  }

  getModulesByState(state: ModuleState): ModuleInterface[] {
    return Array.from(this.modules.values()).filter(
      (module) => module.state === state
    );
  }

  // Module lifecycle management
  async initializeModule(moduleId: string): Promise<void> {
    const module = this.modules.get(moduleId);
    if (!module) {
      throw new Error(`Module ${moduleId} is not registered`);
    }

    if (module.state === ModuleState.READY) {
      console.log(`Module ${moduleId} is already initialized`);
      return;
    }

    console.log(`Initializing module: ${moduleId}`);

    try {
      // Initialize dependencies first
      await this.initializeDependencies(moduleId);

      // Initialize the module
      await module.initialize(this.context);

      console.log(`Module ${moduleId} initialized successfully`);

      // Track initialization
      this.context.analytics.trackEvent({
        type: "module_initialized",
        moduleName: moduleId,
        eventData: {
          version: module.metadata.version,
          dependencies: module.metadata.dependencies,
        },
        timestamp: new Date().toISOString(),
      });
    } catch (error) {
      console.error(`Failed to initialize module ${moduleId}:`, error);

      // Track initialization failure
      this.context.analytics.trackEvent({
        type: "module_initialization_failed",
        moduleName: moduleId,
        eventData: {
          error: error.message,
          version: module.metadata.version,
        },
        timestamp: new Date().toISOString(),
      });

      throw error;
    }
  }

  async destroyModule(moduleId: string): Promise<void> {
    const module = this.modules.get(moduleId);
    if (!module) {
      throw new Error(`Module ${moduleId} is not registered`);
    }

    if (module.state !== ModuleState.READY) {
      console.log(`Module ${moduleId} is not initialized`);
      return;
    }

    console.log(`Destroying module: ${moduleId}`);

    try {
      // Check for dependent modules and destroy them first
      await this.destroyDependentModules(moduleId);

      // Destroy the module
      await module.cleanup();

      console.log(`Module ${moduleId} destroyed successfully`);

      // Track destruction
      this.context.analytics.trackEvent({
        type: "module_destroyed",
        moduleName: moduleId,
        eventData: {
          version: module.metadata.version,
        },
        timestamp: new Date().toISOString(),
      });
    } catch (error) {
      console.error(`Failed to destroy module ${moduleId}:`, error);
      throw error;
    }
  }

  async reloadModule(moduleId: string): Promise<void> {
    console.log(`Reloading module: ${moduleId}`);

    const wasInitialized =
      this.getModule(moduleId)?.state === ModuleState.READY;

    if (wasInitialized) {
      await this.destroyModule(moduleId);
    }

    await this.initializeModule(moduleId);

    console.log(`Module ${moduleId} reloaded successfully`);
  }

  // Initialize all registered modules
  async initializeAllModules(): Promise<void> {
    console.log("Initializing all modules...");

    const errors: Array<{ moduleId: string; error: Error }> = [];

    for (const moduleId of this.initializationOrder) {
      try {
        await this.initializeModule(moduleId);
      } catch (error) {
        console.error(`Failed to initialize module ${moduleId}:`, error);
        errors.push({ moduleId, error });
      }
    }

    if (errors.length > 0) {
      console.warn(`${errors.length} modules failed to initialize:`, errors);
    }

    const initializedCount = this.getModulesByState(ModuleState.READY).length;
    console.log(
      `Module initialization complete: ${initializedCount}/${this.modules.size} modules ready`
    );
  }

  // Cleanup all modules
  async destroyAllModules(): Promise<void> {
    console.log("Destroying all modules...");

    const errors: Array<{ moduleId: string; error: Error }> = [];

    // Destroy in reverse order
    const destroyOrder = [...this.initializationOrder].reverse();

    for (const moduleId of destroyOrder) {
      try {
        await this.destroyModule(moduleId);
      } catch (error) {
        console.error(`Failed to destroy module ${moduleId}:`, error);
        errors.push({ moduleId, error });
      }
    }

    if (errors.length > 0) {
      console.warn(
        `${errors.length} modules failed to destroy cleanly:`,
        errors
      );
    }

    console.log("Module destruction complete");
  }

  // Health check for all modules
  async performHealthCheck(): Promise<Map<string, any>> {
    const results = new Map();

    for (const [moduleId, module] of this.modules) {
      if (module.state === ModuleState.READY) {
        try {
          const health = await module.healthCheck();
          results.set(moduleId, health);
        } catch (error) {
          results.set(moduleId, {
            healthy: false,
            issues: [`Health check failed: ${error.message}`],
            lastChecked: new Date().toISOString(),
            performance: { responseTime: 0, memoryUsage: 0, errorRate: 1 },
          });
        }
      } else {
        results.set(moduleId, {
          healthy: false,
          issues: [`Module state is ${module.state}, expected READY`],
          lastChecked: new Date().toISOString(),
          performance: { responseTime: 0, memoryUsage: 0, errorRate: 0 },
        });
      }
    }

    return results;
  }

  // Private helper methods
  private validateModuleMetadata(module: ModuleInterface): void {
    const metadata = module.metadata;

    if (!metadata.id || typeof metadata.id !== "string") {
      throw new Error("Module must have a valid string ID");
    }

    if (!metadata.name || typeof metadata.name !== "string") {
      throw new Error("Module must have a valid string name");
    }

    if (!metadata.version || typeof metadata.version !== "string") {
      throw new Error("Module must have a valid string version");
    }

    if (!Array.isArray(metadata.dependencies)) {
      throw new Error("Module dependencies must be an array");
    }

    if (!Array.isArray(metadata.permissions)) {
      throw new Error("Module permissions must be an array");
    }
  }

  private calculateInitializationOrder(): void {
    const visited = new Set<string>();
    const visiting = new Set<string>();
    const order: string[] = [];

    const visit = (moduleId: string) => {
      if (visiting.has(moduleId)) {
        throw new Error(
          `Circular dependency detected involving module: ${moduleId}`
        );
      }

      if (visited.has(moduleId)) {
        return;
      }

      visiting.add(moduleId);

      const module = this.modules.get(moduleId);
      if (module) {
        // Visit dependencies first
        for (const dependency of module.metadata.dependencies) {
          if (this.modules.has(dependency)) {
            visit(dependency);
          } else {
            console.warn(
              `Module ${moduleId} depends on ${dependency}, but it's not registered`
            );
          }
        }
      }

      visiting.delete(moduleId);
      visited.add(moduleId);
      order.push(moduleId);
    };

    // Visit all modules
    for (const moduleId of this.modules.keys()) {
      visit(moduleId);
    }

    this.initializationOrder = order;
    console.log("Module initialization order:", order);
  }

  private async initializeDependencies(moduleId: string): Promise<void> {
    const module = this.modules.get(moduleId);
    if (!module) return;

    for (const dependencyId of module.metadata.dependencies) {
      const dependency = this.modules.get(dependencyId);
      if (dependency && dependency.state !== ModuleState.READY) {
        await this.initializeModule(dependencyId);
      }
    }
  }

  private async destroyDependentModules(moduleId: string): Promise<void> {
    // Find modules that depend on this module
    const dependentModules: string[] = [];

    for (const [otherId, otherModule] of this.modules) {
      if (
        otherModule.metadata.dependencies.includes(moduleId) &&
        otherModule.state === ModuleState.READY
      ) {
        dependentModules.push(otherId);
      }
    }

    // Destroy dependent modules first
    for (const dependentId of dependentModules) {
      await this.destroyModule(dependentId);
    }
  }
}

export default ModuleManager;
