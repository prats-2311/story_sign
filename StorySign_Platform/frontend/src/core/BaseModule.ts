/**
 * Base Module Implementation
 *
 * Provides common functionality and default implementations for all modules.
 * Modules can extend this class to inherit standard behavior.
 */

import { ReactNode } from "react";
import {
  ModuleInterface,
  ModuleMetadata,
  ModuleState,
  ModuleConfig,
  ModuleContext,
  ModuleHealthStatus,
  AnalyticsEvent,
  PluginHook,
  Permission,
} from "../types/module";

export abstract class BaseModule implements ModuleInterface {
  // Abstract properties that must be implemented by subclasses
  abstract readonly metadata: ModuleMetadata;

  // Module state management
  private _state: ModuleState = ModuleState.UNINITIALIZED;
  private _context: ModuleContext | null = null;
  private _config: ModuleConfig;
  private _pluginHooks: PluginHook[] = [];
  private _initializationTime: number = 0;
  private _lastHealthCheck: string = "";
  private _errorCount: number = 0;

  constructor(initialConfig?: Partial<ModuleConfig>) {
    this._config = {
      enabled: true,
      settings: {},
      permissions: [Permission.READ_OWN_DATA],
      dependencies: [],
      ...initialConfig,
    };
  }

  // Getters
  get state(): ModuleState {
    return this._state;
  }

  get config(): ModuleConfig {
    return { ...this._config };
  }

  set config(newConfig: ModuleConfig) {
    this._config = { ...newConfig };
    this.onConfigChange(newConfig);
  }

  get context(): ModuleContext | null {
    return this._context;
  }

  // Lifecycle methods
  async initialize(context: ModuleContext): Promise<void> {
    try {
      this._state = ModuleState.INITIALIZING;
      this._context = context;
      this._initializationTime = Date.now();

      // Validate dependencies
      await this.validateDependencies();

      // Validate permissions
      this.validatePermissions();

      // Call subclass initialization
      await this.onInitialize(context);

      // Register with analytics
      this.trackEvent({
        type: "module_initialized",
        moduleName: this.metadata.id,
        eventData: {
          version: this.metadata.version,
          initializationTime: Date.now() - this._initializationTime,
        },
        timestamp: new Date().toISOString(),
      });

      this._state = ModuleState.READY;
    } catch (error) {
      this._state = ModuleState.ERROR;
      this._errorCount++;

      console.error(`Failed to initialize module ${this.metadata.id}:`, error);

      if (this._context) {
        this._context.platform.showNotification(
          `Failed to initialize ${this.metadata.name}: ${error.message}`,
          "error"
        );
      }

      throw error;
    }
  }

  async cleanup(): Promise<void> {
    try {
      // Call subclass cleanup
      await this.onCleanup();

      // Track cleanup
      this.trackEvent({
        type: "module_destroyed",
        moduleName: this.metadata.id,
        eventData: {
          uptime: Date.now() - this._initializationTime,
          errorCount: this._errorCount,
        },
        timestamp: new Date().toISOString(),
      });

      this._state = ModuleState.DESTROYED;
      this._context = null;
    } catch (error) {
      console.error(`Failed to cleanup module ${this.metadata.id}:`, error);
      throw error;
    }
  }

  async onConfigChange(newConfig: ModuleConfig): Promise<void> {
    // Default implementation - can be overridden by subclasses
    console.log(`Config changed for module ${this.metadata.id}:`, newConfig);

    this.trackEvent({
      type: "module_config_changed",
      moduleName: this.metadata.id,
      eventData: { newConfig },
      timestamp: new Date().toISOString(),
    });
  }

  // Data access methods with error handling
  async getUserData(userId: string): Promise<any> {
    if (!this._context) {
      throw new Error("Module not initialized");
    }

    try {
      const data = await this._context.database.getUserData(
        userId,
        this.metadata.id
      );

      this.trackEvent({
        type: "user_data_accessed",
        moduleName: this.metadata.id,
        eventData: { userId, dataType: "read" },
        userId,
        timestamp: new Date().toISOString(),
      });

      return data;
    } catch (error) {
      this._errorCount++;
      console.error(
        `Failed to get user data for module ${this.metadata.id}:`,
        error
      );
      throw error;
    }
  }

  async saveUserData(userId: string, data: any): Promise<void> {
    if (!this._context) {
      throw new Error("Module not initialized");
    }

    try {
      await this._context.database.saveUserData(userId, this.metadata.id, data);

      this.trackEvent({
        type: "user_data_saved",
        moduleName: this.metadata.id,
        eventData: {
          userId,
          dataType: "write",
          dataSize: JSON.stringify(data).length,
        },
        userId,
        timestamp: new Date().toISOString(),
      });
    } catch (error) {
      this._errorCount++;
      console.error(
        `Failed to save user data for module ${this.metadata.id}:`,
        error
      );
      throw error;
    }
  }

  // Analytics integration
  trackEvent(event: AnalyticsEvent): void {
    if (!this._context) {
      console.warn(
        `Cannot track event - module ${this.metadata.id} not initialized`
      );
      return;
    }

    try {
      // Ensure event has module name
      const enrichedEvent = {
        ...event,
        moduleName: this.metadata.id,
      };

      this._context.analytics.trackEvent(enrichedEvent);
    } catch (error) {
      console.error(
        `Failed to track event for module ${this.metadata.id}:`,
        error
      );
    }
  }

  // Plugin integration
  registerPluginHooks(hooks: PluginHook[]): void {
    this._pluginHooks = [...this._pluginHooks, ...hooks];

    if (this._context) {
      hooks.forEach((hook) => {
        this._context!.plugins.registerHook(hook.target, hook.handler);
      });
    }

    this.trackEvent({
      type: "plugin_hooks_registered",
      moduleName: this.metadata.id,
      eventData: { hookCount: hooks.length },
      timestamp: new Date().toISOString(),
    });
  }

  // Health check implementation
  async healthCheck(): Promise<ModuleHealthStatus> {
    const startTime = Date.now();
    const issues: string[] = [];

    try {
      // Check module state
      if (this._state !== ModuleState.READY) {
        issues.push(`Module state is ${this._state}, expected READY`);
      }

      // Check context availability
      if (!this._context) {
        issues.push("Module context is not available");
      }

      // Check dependencies
      try {
        await this.validateDependencies();
      } catch (error) {
        issues.push(`Dependency validation failed: ${error.message}`);
      }

      // Call subclass health check
      const subclassIssues = await this.onHealthCheck();
      issues.push(...subclassIssues);

      const responseTime = Date.now() - startTime;
      this._lastHealthCheck = new Date().toISOString();

      const status: ModuleHealthStatus = {
        healthy: issues.length === 0,
        issues,
        lastChecked: this._lastHealthCheck,
        performance: {
          responseTime,
          memoryUsage: this.getMemoryUsage(),
          errorRate: this.calculateErrorRate(),
        },
      };

      // Track health check
      this.trackEvent({
        type: "health_check_completed",
        moduleName: this.metadata.id,
        eventData: {
          healthy: status.healthy,
          issueCount: issues.length,
          responseTime,
        },
        timestamp: new Date().toISOString(),
      });

      return status;
    } catch (error) {
      this._errorCount++;
      return {
        healthy: false,
        issues: [`Health check failed: ${error.message}`],
        lastChecked: new Date().toISOString(),
        performance: {
          responseTime: Date.now() - startTime,
          memoryUsage: 0,
          errorRate: 1,
        },
      };
    }
  }

  // Abstract methods that subclasses must implement
  abstract renderComponent(props: any): ReactNode;

  // Protected methods that subclasses can override
  protected async onInitialize(context: ModuleContext): Promise<void> {
    // Default implementation - can be overridden
  }

  protected async onCleanup(): Promise<void> {
    // Default implementation - can be overridden
  }

  protected async onHealthCheck(): Promise<string[]> {
    // Default implementation - can be overridden
    return [];
  }

  // Private helper methods
  private async validateDependencies(): Promise<void> {
    if (!this._context) {
      throw new Error("Module context not available for dependency validation");
    }

    const missingDependencies: string[] = [];

    for (const dependency of this.metadata.dependencies) {
      // Check if dependency module is available and ready
      // This would typically check with the module manager
      // For now, we'll just log the dependency check
      console.log(
        `Checking dependency: ${dependency} for module ${this.metadata.id}`
      );
    }

    if (missingDependencies.length > 0) {
      throw new Error(
        `Missing dependencies: ${missingDependencies.join(", ")}`
      );
    }
  }

  private validatePermissions(): void {
    // Validate that the module has the required permissions
    const requiredPermissions = this.metadata.permissions;
    const grantedPermissions = this._config.permissions;

    const missingPermissions = requiredPermissions.filter(
      (permission) => !grantedPermissions.includes(permission)
    );

    if (missingPermissions.length > 0) {
      throw new Error(`Missing permissions: ${missingPermissions.join(", ")}`);
    }
  }

  private getMemoryUsage(): number {
    // Estimate memory usage - in a real implementation this would be more sophisticated
    if (typeof performance !== "undefined" && performance.memory) {
      return performance.memory.usedJSHeapSize / 1024 / 1024; // MB
    }
    return 0;
  }

  private calculateErrorRate(): number {
    const uptime = Date.now() - this._initializationTime;
    if (uptime === 0) return 0;

    // Errors per minute
    return this._errorCount / (uptime / 60000);
  }
}

export default BaseModule;
