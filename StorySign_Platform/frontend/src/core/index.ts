/**
 * Core Module System Exports
 *
 * Central export point for all module system components, types, and utilities.
 */

// Core module system
export { BaseModule } from "./BaseModule";
export { ModuleManager } from "./ModuleManager";
export {
  ModuleContextProvider,
  useModuleSystem,
  useModuleContext,
  useModule,
  ModuleRegistrar,
  withModuleContext,
} from "./ModuleContextProvider";

// Type definitions
export type {
  ModuleInterface,
  ModuleMetadata,
  ModuleContext,
  ModuleConfig,
  ModuleHealthStatus,
  ModuleRegistration,
  ModuleManager as IModuleManager,
  User,
  UserProfile,
  DatabaseService,
  AnalyticsService,
  AnalyticsEvent,
  AnalyticsQuery,
  PluginService,
  PluginInfo,
  Plugin,
  PluginHook,
  HookHandler,
  HookContext,
  RealtimeService,
  MessageHandler,
  PlatformService,
  ContentQuery,
} from "../types/module";

export {
  ModuleState,
  Permission,
  UserRole,
  ConnectionStatus,
  NotificationType,
} from "../types/module";

// Service implementations
export { MockDatabaseService } from "../services/MockDatabaseService";
export { MockAnalyticsService } from "../services/MockAnalyticsService";
export { MockPluginService } from "../services/MockPluginService";
export { MockRealtimeService } from "../services/MockRealtimeService";
export { PlatformServiceImpl } from "../services/PlatformServiceImpl";

// Module implementations
export { ASLWorldModuleInterface } from "../modules/asl_world/ASLWorldModuleInterface";
export type {
  ASLWorldUserData,
  PracticeSession,
  SentenceAttempt,
  ASLWorldPreferences,
  LearningProgress,
  Achievement,
  ASLWorldModuleProps,
} from "../modules/asl_world/ASLWorldModuleInterface";
